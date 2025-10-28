from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
import re
from django.views.decorators.csrf import csrf_exempt
import os
import logging
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
import socket
import time

logger = logging.getLogger(__name__)
try:
    import paramiko  # type: ignore
except Exception:
    paramiko = None  # fallback if not available

from netops_backend.nlp_router import predict_cli, predict_cli_provider
from .models import Conversation, Message
from .models import DeviceHealth, HealthAlert
import subprocess
from functools import lru_cache
from datetime import datetime, timedelta, timezone
try:
    from Devices.device_resolver import resolve_device, find_device_by_host, get_devices  # Devices folder at project root
except ModuleNotFoundError:
    # Fallback if moved inside project package later
    from netops_backend.Devices.device_resolver import resolve_device, find_device_by_host, get_devices  # type: ignore


# ------------------------------- Device Status Helpers ---------------------------------
PING_TIMEOUT = float(os.getenv("DEVICE_STATUS_PING_TIMEOUT", "0.8"))  # seconds
PING_CACHE_TTL = float(os.getenv("DEVICE_STATUS_CACHE_TTL", "15"))  # seconds

@lru_cache(maxsize=256)
def _cached_ping(host: str) -> tuple[str, float, float]:
    """Ping host returning (status, latency_ms, cached_at_epoch).

    Uses platform ping command with one echo request. Falls back to socket connect (22) if ping fails.
    Cached via lru_cache; manual TTL enforcement in caller.
    """
    start = time.time()
    latency_ms = -1.0
    status_val = "down"
    # Windows vs *nix command
    if os.name == 'nt':
        cmd = ["ping", "-n", "1", "-w", str(int(PING_TIMEOUT*1000)), host]
    else:
        cmd = ["ping", "-c", "1", "-W", str(int(PING_TIMEOUT)), host]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=PING_TIMEOUT+0.5)
        output = proc.stdout.lower()
        if proc.returncode == 0:
            # Attempt latency parse
            # common patterns: time=12.3 ms or time<1ms
            import re
            m = re.search(r"time[=<]\s*([0-9]+\.?[0-9]*)\s*ms", output)
            if m:
                try:
                    latency_ms = float(m.group(1))
                except Exception:
                    latency_ms = (time.time() - start)*1000
            else:
                latency_ms = (time.time() - start)*1000
            status_val = "up"
        else:
            # fallback: TCP connect quick test
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(PING_TIMEOUT)
                t0 = time.time()
                sock.connect((host, 22))
                latency_ms = (time.time() - t0) * 1000
                status_val = "up"
            except Exception:
                pass
            finally:
                try:
                    sock.close()
                except Exception:
                    pass
    except Exception:
        pass
    return status_val, latency_ms, time.time()

def ping_host(host: str) -> dict:
    # Enforce TTL manually because lru_cache has no time expiration.
    key = (host,)
    # Access internal cache (not public API but acceptable here for lightweight solution)
    try:
        cache = _cached_ping.cache  # type: ignore[attr-defined]
    except Exception:
        cache = None
    status_val: str
    latency_ms: float
    ts: float
    if cache is not None:
        # rebuild key how lru_cache would (host,) since single arg
        # Python's internal key building is different; just always call function and rely on TTL enforcement after.
        pass
    status_val, latency_ms, ts = _cached_ping(host)
    # If stale, bust and recompute
    if (time.time() - ts) > PING_CACHE_TTL:
        try:
            _cached_ping.cache_clear()  # type: ignore[attr-defined]
        except Exception:
            pass
        status_val, latency_ms, ts = _cached_ping(host)
    return {
        "status": status_val,
        "latency_ms": None if latency_ms < 0 else round(latency_ms, 2),
        "checked_at": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
    }

class DeviceStatusAPIView(APIView):
    """GET /device-status/ -> list of devices with reachability and latency.

    Optional query params:
      alias=ALIAS1,ALIAS2  (filter subset)
    """
    def get(self, request):  # type: ignore[override]
        devices = get_devices() or {}
        alias_filter = request.GET.get("alias")
        subset = None
        if alias_filter:
            wanted = {a.strip().upper() for a in alias_filter.split(",") if a.strip()}
            subset = {k:v for k,v in devices.items() if k.upper() in wanted}
        devs = subset if subset is not None else devices
        results = []
        for alias, info in devs.items():
            host = info.get("host") or info.get("ip")
            if not host:
                results.append({
                    "alias": alias,
                    "name": info.get("name") or alias,
                    "host": None,
                    "status": "unknown",
                    "latency_ms": None,
                    "checked_at": None
                })
                continue
            ping_data = ping_host(str(host))
            results.append({
                "alias": alias,
                "name": info.get("name") or alias,
                "host": host,
                **ping_data
            })
        return Response({
            "count": len(results),
            "devices": results,
            "cache_ttl_seconds": PING_CACHE_TTL,
        }, status=200)

# Simple command safety allowlist (read-only)
SAFE_PREFIXES = (
    'show ', 'dir', 'display '
)
BLOCKED_SUBSTRINGS = (
    ' delete', ' erase', ' write ', ' format', ' reload', ' shutdown', ' no shutdown', 'copy ', ' tftp', ' ftp ', 'scp '
)


@method_decorator(csrf_exempt, name="dispatch")
class NetworkCommandAPIView(APIView):
    """Endpoint: NL query -> generated CLI -> execute via Netmiko -> raw output.

    POST JSON: {"query": "show interfaces", "device_ip": "192.168.1.10"}
    Success: {"output": "...raw device output..."}
    Errors:
      {"error": "Unable to connect to device"}
      {"error": "Failed to run command"}
    """

    def get(self, request):
        return Response({"detail": "POST JSON with 'device_ip' and 'query'"}, status=200)

    def post(self, request):
        data = getattr(request, 'data', {}) or {}
        query = data.get("query") or (request.query_params.get("query") if hasattr(request, "query_params") else None)
        device_ip = data.get("device_ip") or data.get("ip") or (request.query_params.get("device_ip") if hasattr(request, "query_params") else None)
        # Optional direct alias override
        device_alias_param = data.get("device_alias") or data.get("alias")
        hostname = device_alias_param or data.get("hostname") or data.get("device_hostname") or (request.query_params.get("hostname") if hasattr(request, "query_params") else None)
        session_id = data.get("session_id") or request.headers.get("X-Session-ID")

        conversation = None
        if session_id:
            try:
                conversation = Conversation.objects.filter(id=session_id).first()
            except Exception:
                conversation = None
        if conversation is None and session_id:
            # Create new conversation with provided UUID if format matches else generate
            try:
                # Let UUIDField validate by creating then updating id (simpler: create blank and rely on auto UUID when not provided)
                conversation = Conversation.objects.create(id=session_id)  # type: ignore[arg-type]
            except Exception:
                conversation = Conversation.objects.create()
                session_id = str(conversation.id)
        if conversation is None:
            conversation = Conversation.objects.create()
            session_id = str(conversation.id)

        if not query:
            return Response({"error": "Failed to run command"}, status=400)

        # Optional force/blocks via env or request
        force_alias = os.getenv("FORCE_DEVICE_ALIAS") or data.get("force_device_alias")
        force_ip = os.getenv("FORCE_DEVICE_IP") or data.get("force_device_ip")
        blocked_ips = {s.strip() for s in (os.getenv("BLOCKED_DEVICE_IPS", "").split(",")) if s.strip()}
        blocked_aliases = {s.strip().upper() for s in (os.getenv("BLOCKED_DEVICE_ALIASES", "").split(",")) if s.strip()}

        # Apply forced target first, if configured
        if force_alias:
            dev_dict, _, _ = resolve_device(force_alias)
            if dev_dict:
                resolved_device_dict = dev_dict
                device_ip = dev_dict.get("host") or dev_dict.get("ip")
                hostname = force_alias
        elif force_ip:
            device_ip = force_ip
        # Resolution Phase ----------------------------------------------------
        # Always attempt resolution each request; use conversation only when no new hints
        resolved_device_dict = None
        resolution_method = None  # direct_alias | phrase | fuzzy | keyword | explicit_fallback | intent_override | conversation_fallback | default | ip_match

        dev_dict = None
        candidates: list[str] = []
        err = None
        # 1. Explicit alias/hostname
        if hostname:
            dev_dict, candidates, err = resolve_device(hostname)
            if dev_dict:
                resolution_method = "direct_alias"
        # 2. Query-based (phrase/fuzzy/keyword)
        if not dev_dict:
            q_to_use = query or ""
            dev_dict2, candidates2, err2 = resolve_device(q_to_use)
            if dev_dict2:
                lowered = q_to_use.lower()
                if any(k in lowered for k in ["vijayawada", "vij ", " vij", "vijay", "vijaya", "india", "london", "uk", "building 1"]):
                    resolution_method = resolution_method or "fuzzy"
                else:
                    resolution_method = resolution_method or "phrase"
                dev_dict, candidates, err = dev_dict2, [], None
            elif candidates2:
                candidates, err = candidates2, err2

        # 3. Explicit Vijayawada fallback if intent present but still unresolved
        if not dev_dict and ("vijayawada" in (query or "").lower() or (hostname and str(hostname).upper() == "INVIJB1C01")):
            dev_fallback, _, _ = resolve_device("INVIJB1C01")
            if dev_fallback:
                dev_dict = dev_fallback
                resolution_method = resolution_method or "explicit_fallback"

        # 4. Apply resolved or candidate handling
        if dev_dict:
            resolved_device_dict = dev_dict
            device_ip = dev_dict.get("host") or dev_dict.get("ip")
            hostname = dev_dict.get("alias") or hostname
        elif candidates:
            return Response({"error": "Multiple switches found, please specify one", "candidates": candidates, "session_id": session_id}, status=400)
        else:
            # 5. Conversation fallback
            if conversation and (conversation.device_host or conversation.device_alias):
                alias_found, dev_by_host = (None, None)
                if conversation.device_host:
                    alias_found, dev_by_host = find_device_by_host(conversation.device_host)
                if dev_by_host:
                    resolved_device_dict = dev_by_host
                    device_ip = dev_by_host.get("host")
                    hostname = dev_by_host.get("alias") or alias_found or conversation.device_alias
                    resolution_method = resolution_method or "conversation_fallback"
                elif conversation.device_alias:
                    alias_dev, _, _ = resolve_device(conversation.device_alias)
                    if alias_dev:
                        resolved_device_dict = alias_dev
                        device_ip = alias_dev.get("host") or alias_dev.get("ip")
                        hostname = alias_dev.get("alias") or conversation.device_alias
                        resolution_method = resolution_method or "conversation_fallback"
                    else:
                        hostname = conversation.device_alias
                        device_ip = conversation.device_host

        # 6. Default alias fallback
        if not device_ip:
            default_alias = os.getenv("DEFAULT_DEVICE_ALIAS") or "UKLONB10C01"
            default_ip = os.getenv("DEFAULT_DEVICE_IP")
            if default_alias:
                dev_dict, _, _ = resolve_device(default_alias)
                if dev_dict:
                    resolved_device_dict = dev_dict
                    device_ip = dev_dict.get("host") or dev_dict.get("ip")
                    hostname = dev_dict.get("alias") or default_alias
                    resolution_method = resolution_method or "default"
                    logger.info("Default alias fallback applied", extra={
                        'alias': default_alias,
                        'host': device_ip,
                        'resolution_method': resolution_method
                    })
            elif default_ip:
                device_ip = default_ip
                logger.info("Default IP fallback applied", extra={'host': default_ip})

        # 7. Reverse lookup by IP if needed
        if device_ip and not resolved_device_dict:
            alias_found, dev_by_host = find_device_by_host(device_ip)
            if dev_by_host:
                resolved_device_dict = dev_by_host
                hostname = dev_by_host.get("alias") or alias_found or hostname
                resolution_method = resolution_method or "ip_match"

        # 8. Late Vijayawada intent override (UK -> IN swap)
        if resolved_device_dict and query:
            ql = query.lower()
            vij_intent = any(k in ql for k in ["vijayawada", "vij ", " vij", "vijay ", " vijay", "vijaya ", " vijaya", "india"])
            alias_now = (resolved_device_dict.get("alias") or "").upper()
            if vij_intent and alias_now.startswith("UK"):
                alt_dev, _, _ = resolve_device("INVIJB1C01")
                if alt_dev:
                    logger.info("Intent override applied - switching to Vijayawada", extra={
                        'from_alias': alias_now,
                        'to_alias': 'INVIJB1C01',
                        'intent': 'vijayawada_reference'
                    })
                    resolved_device_dict = alt_dev
                    device_ip = alt_dev.get("host") or alt_dev.get("ip") or device_ip
                    hostname = alt_dev.get("alias") or hostname
                    resolution_method = "intent_override"

        # Enforce blocks: if resolved to a blocked IP or alias, reroute to default/forced alias or error
        if device_ip and device_ip in blocked_ips:
            # Prefer force/default alias if available
            reroute_alias = force_alias or os.getenv("DEFAULT_DEVICE_ALIAS")
            if reroute_alias:
                dev_dict, _, _ = resolve_device(reroute_alias)
                if dev_dict:
                    resolved_device_dict = dev_dict
                    device_ip = dev_dict.get("host") or dev_dict.get("ip")
                    hostname = dev_dict.get("alias") or reroute_alias
            else:
                return Response({"error": "Target device is blocked"}, status=400)


        logger.info("Network command request", extra={
            'query': query,
            'session_id': session_id,
            'alias': hostname,
            'host': device_ip,
            'resolution_method': resolution_method
        })

        # Determine connection strategy:
        #  direct (default) | jump_first (try jump then direct fallback) | jump_only (only via jump host)
        strategy = (resolved_device_dict or {}).get("connection_strategy", "direct") if resolved_device_dict else "direct"
        alias_upper = hostname.upper() if hostname else None
        # Remove previous forced jump logic for Vijayawada; allow direct connect (host now points to site IP)
        # If future need arises, reintroduce conditional enforcement here.
        # Environment overrides:
        #  ALWAYS_JUMP_ALIASES = comma list of aliases to force jump_only
        #  FORCE_JUMP_FOR_ALL=1 -> treat any device with jump_via as jump_only
        always_jump_aliases = {a.strip().upper() for a in os.getenv("ALWAYS_JUMP_ALIASES", "").split(',') if a.strip()}
        if alias_upper and alias_upper in always_jump_aliases:
            strategy = "jump_only"
        if os.getenv("FORCE_JUMP_FOR_ALL", "0") == "1" and resolved_device_dict and resolved_device_dict.get("jump_via"):
            strategy = "jump_only"
        logger.debug("Connection strategy determined", extra={
            'strategy': strategy,
            'alias': alias_upper,
            'jump_via': resolved_device_dict.get("jump_via") if resolved_device_dict else None
        })

        if not device_ip:
            return Response({"error": "Failed to run command", "session_id": session_id}, status=400)

        # Jump-first strategy: if device defines jump_via and connection_strategy == jump_first, attempt multi-hop immediately
        jump_first_attempted = False
        if resolved_device_dict and resolved_device_dict.get("jump_via") and strategy in ("jump_first", "jump_only"):
            jump_alias = str(resolved_device_dict.get("jump_via")).upper()
            jd, _, _ = resolve_device(jump_alias)
            if jd:
                try:
                    log_label = "jump_only" if strategy == "jump_only" else "jump_first"
                    logger.info(f"Attempting jump host connection ({log_label})", extra={
                        'strategy': strategy,
                        'jump_alias': jump_alias,
                        'target_alias': hostname,
                        'target_host': device_ip,
                        'no_direct_fallback': strategy == 'jump_only'
                    })
                    output = self._run_via_jump(
                        jump_device=jd,
                        target_device=resolved_device_dict,
                        cli_command=predict_cli(query),  # re-run to ensure same CLI used below if fallback
                        primary_ip=device_ip,
                        username=(resolved_device_dict or {}).get("username") or os.getenv("DEVICE_USERNAME", "admin"),
                        password=(resolved_device_dict or {}).get("password") or os.getenv("DEVICE_PASSWORD", "admin"),
                        enable_secret=(resolved_device_dict or {}).get("secret") or os.getenv("DEVICE_SECRET", ""),
                        conn_timeout=float(os.getenv("DEVICE_CONN_TIMEOUT", "8")),
                    )
                    # Persist conversation and return early
                    cli_command = predict_cli(query)
                    if conversation:
                        updated = False
                        if hostname and (conversation.device_alias != hostname or conversation.device_host != (resolved_device_dict.get("host") or device_ip)):
                            conversation.device_alias = hostname
                            conversation.device_host = resolved_device_dict.get("host") or device_ip
                            updated = True
                        conversation.last_command = cli_command
                        if updated:
                            conversation.save(update_fields=["device_alias", "device_host", "last_command", "updated_at"])
                        else:
                            conversation.save(update_fields=["last_command", "updated_at"])
                        Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content=query)
                        Message.objects.create(conversation=conversation, role=Message.ROLE_ASSISTANT, content=cli_command, meta="CLI_OUTPUT")
                    return Response({
                        "output": output,
                        "device_alias": hostname,
                        "device_host": resolved_device_dict.get("host") or device_ip,  # Use primary host only (loopback disabled)
                        "session_id": session_id,
                        "jump_via": jump_alias,
                        "cleaned": True,
                        "strategy": "jump_first",
                        "connection_method": "jump"
                    }, status=200)
                except Exception as e:
                    logger.warning("Jump host connection failed", extra={
                        'strategy': strategy,
                        'jump_alias': jump_alias,
                        'target_alias': hostname,
                        'error': str(e)
                    }, exc_info=True)
                    jump_first_attempted = True
                    if strategy == "jump_only":
                        # Do not attempt direct connection for jump_only strategy
                        return Response({"error": "Unable to connect to device via jump host"}, status=502)

        # Vendor-aware CLI prediction: Cisco -> local T5/LoRA, Aruba -> Gemini API
        vendor = (resolved_device_dict or {}).get("vendor") or (resolved_device_dict or {}).get("device_type") or ""
        vendor_l = str(vendor).lower()
        # Environment overrides (optional)
        # Aruba uses Gemini API (free tier: 1500 requests/day)
        aruba_provider = os.getenv("ARUBA_LLM_PROVIDER", "gemini")
        aruba_model = os.getenv("ARUBA_LLM_MODEL", "gemini-1.5-flash")
        cisco_provider = os.getenv("CISCO_LLM_PROVIDER", "local")

        if "aruba" in vendor_l or "hp" in vendor_l or "hewlett" in vendor_l:
            # Strip location words for Gemini so it focuses on the intent, not site names
            loc_pattern = re.compile(r"\b(uk|london|gb|india|in|vijayawada|hyderabad|hyderabaad|hyd|lab|aruba)\b", re.I)
            sanitized_query = loc_pattern.sub("", query).strip()
            # Default Aruba prompt if not provided in env
            aruba_system = os.getenv(
                "ARUBA_SYSTEM_PROMPT",
                "You are a precise network CLI assistant. Given a natural language request, output exactly one Aruba AOS-CX show command that best answers it. Ignore any location words (like city or site). Return ONLY the command text."
            )
            cli_command = predict_cli_provider(
                sanitized_query or query,
                provider=aruba_provider,
                model=aruba_model,
                system_prompt=aruba_system,
            )
            # No fallback for Aruba - Gemini API is required for AOS-CX commands
            if (not cli_command) or cli_command.startswith("[Error]"):
                error_msg = "Gemini API required for Aruba devices. Please check your API key."
                if cli_command and "GEMINI_API_KEY" in cli_command:
                    error_msg = "Gemini API key not set. Get free key at https://makersuite.google.com/app/apikey"
                logger.error(error_msg, extra={'vendor': vendor, 'error': cli_command})
                return Response({
                    "error": error_msg,
                    "details": "Aruba AOS-CX requires Gemini API. T5 model only supports Cisco IOS.",
                    "session_id": session_id
                }, status=503)
        else:
            # default Cisco/local
            cli_command = predict_cli_provider(
                query,
                provider=cisco_provider,
                model=os.getenv("CISCO_LLM_MODEL"),
                system_prompt=os.getenv("CISCO_SYSTEM_PROMPT")
            )
            # Cisco fallback: if local or configured provider fails, try OpenAI with Cisco prompt
            if (not cli_command) or cli_command.startswith("[Error]"):
                # sanitize for OpenAI
                loc_pattern = re.compile(r"\b(uk|london|gb|india|in|vijayawada|hyderabad|hyderabaad|hyd|lab|aruba)\b", re.I)
                sanitized_query = loc_pattern.sub("", query).strip()
                cisco_fallback_provider = os.getenv("CISCO_FALLBACK_PROVIDER", "openai")
                cisco_fallback_model = os.getenv("CISCO_FALLBACK_MODEL", os.getenv("CLI_LLM_MODEL", "gpt-4o-mini"))
                cisco_system = os.getenv(
                    "CISCO_SYSTEM_PROMPT",
                    "You are a precise network CLI assistant. Given a natural language request, output exactly one Cisco IOS show command that best answers it. Return ONLY the command text, with no quotes or explanations."
                )
                cli_command = predict_cli_provider(
                    sanitized_query or query,
                    provider=cisco_fallback_provider,
                    model=cisco_fallback_model,
                    system_prompt=cisco_system,
                )
        print(f"[NetworkCommandAPIView] predicted_cli={cli_command}")
        if not cli_command or cli_command.startswith("[Error]"):
            return Response({"error": "Failed to run command", "session_id": session_id}, status=500)

        lc = cli_command.strip().lower()
        # Enforce read-only by default
        if not any(lc.startswith(p) for p in SAFE_PREFIXES):
            return Response({"error": "Command not allowed", "command": cli_command, "session_id": session_id}, status=400)
        if any(b in lc for b in BLOCKED_SUBSTRINGS):
            return Response({"error": "Command blocked for safety", "command": cli_command, "session_id": session_id}, status=400)

        # Allow overrides via request (optional) else fall back to env
        req_username = data.get("username")
        req_password = data.get("password")
        req_secret = data.get("secret")
        req_type = data.get("device_type")
        req_port = data.get("port")

        env_username = os.getenv("DEVICE_USERNAME", "admin")
        env_password = os.getenv("DEVICE_PASSWORD", "admin")
        env_secret = os.getenv("DEVICE_SECRET", "")
        env_type = os.getenv("DEVICE_TYPE", "cisco_ios")
        env_port = os.getenv("DEVICE_PORT")
        conn_timeout = float(os.getenv("DEVICE_CONN_TIMEOUT", "8"))
        auth_timeout = float(os.getenv("DEVICE_AUTH_TIMEOUT", "10"))
        banner_timeout = float(os.getenv("DEVICE_BANNER_TIMEOUT", "15"))
        force_telnet = os.getenv("FORCE_TELNET", "0") == "1"
        prefer_telnet = force_telnet or (os.getenv("PREFER_TELNET", "0") == "1")
        disable_telnet = os.getenv("DISABLE_TELNET", "0") == "1"

        # Allow per-request override of telnet preferences
        def _truthy(val):
            if val is None:
                return False
            if isinstance(val, bool):
                return val
            return str(val).strip().lower() in {"1", "true", "yes", "on"}

        if "force_telnet" in data:
            force_telnet = _truthy(data.get("force_telnet"))
        if "prefer_telnet" in data:
            prefer_telnet = force_telnet or _truthy(data.get("prefer_telnet"))
        # Per-request SSH-only enforcement
        ssh_only = _truthy(data.get("ssh_only")) if "ssh_only" in data else False
        telnet_permitted = (not disable_telnet) and (not ssh_only)
        if not telnet_permitted and force_telnet:
            print("[NetworkCommandAPIView] telnet disabled (env/request) -> ignoring force_telnet")
            force_telnet = False
            prefer_telnet = False

        # Derive alias (uppercase) for env password lookup if available
        resolved_alias_upper = None
        if resolved_device_dict:
            # attempt alias from dict key if present, else from hostname var
            # devices.json currently omits explicit alias field, so infer from query resolution
            resolved_alias_upper = hostname.upper() if hostname else None
        env_alias_password = None
        if resolved_alias_upper:
            env_alias_password = os.getenv(f"DEVICE_{resolved_alias_upper}_PASSWORD")

        password_source = "env-global"
        chosen_password = (resolved_device_dict or {}).get("password")
        if chosen_password:
            password_source = "devices.json"
        elif req_password:
            password_source = "request"
            chosen_password = req_password
        elif env_alias_password:
            password_source = f"env-alias:{resolved_alias_upper}"
            chosen_password = env_alias_password
        else:
            chosen_password = env_password

        print(f"[NetworkCommandAPIView] password source -> {password_source}")

        ssh_device = {
            "device_type": (resolved_device_dict or {}).get("device_type", "cisco_ios"),
            "host": device_ip,
            "username": (resolved_device_dict or {}).get("username") or req_username or env_username,
            "password": chosen_password,
            "secret": (resolved_device_dict or {}).get("secret") or (req_secret if req_secret is not None else env_secret),
            "fast_cli": True,
            "timeout": conn_timeout,
            "conn_timeout": conn_timeout,
            "auth_timeout": auth_timeout,
            "banner_timeout": banner_timeout,
            "allow_agent": False,
            "use_keys": False,
            "port": 22,
        }
        telnet_device = {
            **ssh_device,
            "device_type": "cisco_ios_telnet",
            "port": 23,
        }

        # Build ordered candidate list - LOOPBACKS DISABLED (only use primary host)
        ordered_candidates: list[str] = []
        if resolved_device_dict:
            # COMMENTED OUT: Loopback fallback disabled - connect directly to host IP only
            # loopbacks_any = []
            # try:
            #     if isinstance(resolved_device_dict.get('loopbacks'), list):
            #         loopbacks_any = [lb for lb in resolved_device_dict.get('loopbacks') if lb]
            #     elif resolved_device_dict.get('loopback'):
            #         # legacy single loopback value
            #         lv = resolved_device_dict.get('loopback')
            #         if isinstance(lv, str):
            #             loopbacks_any = [lv]
            # except Exception:
            #     pass
            
            primary_host_initial = device_ip
            alt_hosts_any = []
            try:
                alt_hosts_any = [h for h in (resolved_device_dict.get('alt_hosts') or []) if h]
            except Exception:
                alt_hosts_any = []
            
            # Compose order: PRIMARY HOST ONLY (loopbacks disabled, alt_hosts as backup)
            # REMOVED: for h in loopbacks_any:
            #     if h and h not in ordered_candidates:
            #         ordered_candidates.append(h)
            if primary_host_initial and primary_host_initial not in ordered_candidates:
                ordered_candidates.append(primary_host_initial)
            for h in alt_hosts_any:
                if h and h not in ordered_candidates:
                    ordered_candidates.append(h)
            if ordered_candidates:
                device_ip = ordered_candidates[0]
                ssh_device['host'] = device_ip
                telnet_device['host'] = device_ip
                print(f"[NetworkCommandAPIView] connection candidates (primary-host-only)={ordered_candidates}")

        net_connect = None
        last_err = None
        if prefer_telnet and telnet_permitted:
            print("[NetworkCommandAPIView] telnet preferred -> attempting port 23")
            try:
                net_connect = ConnectHandler(**telnet_device)
            except Exception as e:
                last_err = e
                print(f"[NetworkCommandAPIView] telnet connect failed -> {e}")
            if net_connect is None and not force_telnet:
                print(f"[NetworkCommandAPIView] ssh fallback attempt 22")
                try:
                    net_connect = ConnectHandler(**ssh_device)
                except Exception as e:
                    last_err = e
                    print(f"[NetworkCommandAPIView] ssh connect failed -> {e}")
        elif prefer_telnet and not telnet_permitted:
            print("[NetworkCommandAPIView] telnet preferred but disabled -> SSH only")
            try:
                net_connect = ConnectHandler(**ssh_device)
            except Exception as e:
                last_err = e
                print(f"[NetworkCommandAPIView] ssh connect failed -> {e}")
        else:
            print(f"[NetworkCommandAPIView] ssh connect attempt 22")
            try:
                net_connect = ConnectHandler(**ssh_device)
            except Exception as e:
                last_err = e
                print(f"[NetworkCommandAPIView] ssh connect failed -> {e}")
            if net_connect is None and telnet_permitted:
                print("[NetworkCommandAPIView] telnet fallback attempt 23")
                try:
                    net_connect = ConnectHandler(**telnet_device)
                except Exception as e:
                    last_err = e
                    print(f"[NetworkCommandAPIView] telnet connect failed -> {e}")
            elif net_connect is None and not telnet_permitted:
                print("[NetworkCommandAPIView] telnet disabled -> no telnet fallback")

        if net_connect is None and ordered_candidates:
            # Iterate remaining candidates after the first one
            for cand_host in ordered_candidates[1:]:
                if not cand_host or cand_host == device_ip:
                    continue
                print(f"[NetworkCommandAPIView] trying next candidate host {cand_host}")
                ssh_device['host'] = cand_host
                telnet_device['host'] = cand_host
                try:
                    net_connect = ConnectHandler(**ssh_device)
                    if net_connect:
                        device_ip = cand_host
                        break
                except Exception as e:
                    last_err = e
                    print(f"[NetworkCommandAPIView] candidate host ssh failed -> {e}")
            if net_connect is None:
                # restore to first candidate for consistency
                ssh_device['host'] = ordered_candidates[0]
                telnet_device['host'] = ordered_candidates[0]

        if net_connect is None:
            # If strategy jump_only and we already attempted jump path earlier, do not proceed to legacy direct attempts.
            if strategy == "jump_only" and jump_first_attempted:
                return Response({"error": "Unable to connect to device via jump host"}, status=502)
            # Optional legacy SSH fallback for very old devices (try original then alts)
            legacy_hosts = [device_ip] + [h for h in (resolved_device_dict.get("alt_hosts") if resolved_device_dict else []) if h != device_ip]
            if os.getenv("ENABLE_LEGACY_SSH", "1") == "1" and paramiko is not None:
                for lh in legacy_hosts:
                    try:
                        print(f"[NetworkCommandAPIView] legacy ssh attempt host={lh}")
                        output = self._run_command_legacy_ssh(
                            lh,
                            (resolved_device_dict or {}).get("username") or req_username or env_username,
                            chosen_password,
                            cli_command,
                            port=22,
                            conn_timeout=conn_timeout,
                            auth_timeout=auth_timeout,
                        )
                        device_ip = lh
                        return Response({"output": output, "legacy": True}, status=200)
                    except Exception as e:
                        print(f"[NetworkCommandAPIView] legacy ssh failed host={lh} -> {e}")
            # Before final failure, attempt jump host (multi-hop) if defined on target
            jump_used = False
            jump_alias = None
            if resolved_device_dict and resolved_device_dict.get("jump_via"):
                jump_alias = str(resolved_device_dict.get("jump_via")).upper()
                jd, _, _ = resolve_device(jump_alias)
                if jd:
                    print(f"[NetworkCommandAPIView] attempting jump via {jump_alias}")
                    try:
                        output = self._run_via_jump(
                            jump_device=jd,
                            target_device=resolved_device_dict,
                            cli_command=cli_command,
                            primary_ip=device_ip,
                            username=(resolved_device_dict or {}).get("username") or req_username or env_username,
                            password=chosen_password,
                            enable_secret=(resolved_device_dict or {}).get("secret") or (req_secret if req_secret is not None else env_secret),
                            conn_timeout=conn_timeout,
                        )
                        # conversation persistence happens below; override device_ip to target host
                        jump_used = True
                        device_ip = resolved_device_dict.get("host") or device_ip
                        if conversation:
                            updated = False
                            if hostname and (conversation.device_alias != hostname or conversation.device_host != device_ip):
                                conversation.device_alias = hostname
                                conversation.device_host = device_ip
                                updated = True
                            conversation.last_command = cli_command
                            if updated:
                                conversation.save(update_fields=["device_alias", "device_host", "last_command", "updated_at"])
                            else:
                                conversation.save(update_fields=["last_command", "updated_at"])
                            Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content=query)
                            Message.objects.create(conversation=conversation, role=Message.ROLE_ASSISTANT, content=cli_command, meta="CLI_OUTPUT")
                        resp_payload = {
                            "output": output,
                            "device_alias": hostname,
                            "device_host": (resolved_device_dict.get("host") if resolved_device_dict else None) or device_ip,  # Use primary host only
                            "session_id": session_id,
                            "jump_via": jump_alias,
                            "cleaned": True,
                            "connection_method": "jump"
                        }
                        return Response(resp_payload, status=200)
                    except Exception as e:
                        print(f"[NetworkCommandAPIView] jump via {jump_alias} failed -> {e}")
            # Return generic error by default; optionally expose details for troubleshooting
            debug_expose = os.getenv("EXPOSE_CONN_ERROR", "0") == "1"
            try:
                # Reuse _truthy helper if present in scope (defined earlier in method)
                if 'data' in locals() and isinstance(data, dict) and 'debug' in data:
                    # mypy: ignore dynamic function reference
                    debug_expose = debug_expose or (locals().get('_truthy')(data.get('debug')) if callable(locals().get('_truthy')) else False)  # type: ignore
            except Exception:
                pass
            resp_err = {"error": "Unable to connect to device"}
            if debug_expose and last_err is not None:
                # Include a concise string form of the last exception
                resp_err["error_detail"] = str(last_err)[:600]
                # Mark that sensitive details may have been truncated
                resp_err["truncated"] = len(str(last_err)) > 600
            return Response(resp_err, status=502)

        try:
            if (req_secret or env_secret):
                try:
                    net_connect.enable()
                except Exception as ee:
                    print(f"[NetworkCommandAPIView] enable failed (continuing): {ee}")
            output = net_connect.send_command(cli_command, expect_string=None, use_textfsm=False)
        except Exception as e:
            print(f"[NetworkCommandAPIView] command exec failure: {e}")
            try:
                net_connect.disconnect()
            except Exception:
                pass
            return Response({"error": "Failed to run command"}, status=500)
        finally:
            try:
                net_connect.disconnect()
            except Exception:
                pass

        # Persist conversation state
        if conversation:
            updated = False
            if hostname and (conversation.device_alias != hostname or conversation.device_host != device_ip):
                conversation.device_alias = hostname
                conversation.device_host = device_ip
                updated = True
            conversation.last_command = cli_command
            if updated:
                conversation.save(update_fields=["device_alias", "device_host", "last_command", "updated_at"])
            else:
                conversation.save(update_fields=["last_command", "updated_at"])
            Message.objects.create(conversation=conversation, role=Message.ROLE_USER, content=query)
            Message.objects.create(conversation=conversation, role=Message.ROLE_ASSISTANT, content=cli_command, meta="CLI_OUTPUT")

        # Flexible response modes
        # Default: minimal JSON with raw output only (legacy behavior the user requested)
        # ?structured=1 or body {"structured": true} => full structured payload
        # ?text=1 or body {"text": true} => plain text (text/plain) raw output only
        qp = getattr(request, "query_params", {})
        want_structured = False
        want_text = False
        try:
            if "structured" in data or (hasattr(qp, 'get') and qp.get("structured") is not None):
                want_structured = _truthy(data.get("structured") if "structured" in data else qp.get("structured"))
            if "full" in data or (hasattr(qp, 'get') and qp.get("full") is not None):
                # alias for structured
                want_structured = want_structured or _truthy(data.get("full") if "full" in data else qp.get("full"))
            if "text" in data or (hasattr(qp, 'get') and qp.get("text") is not None):
                want_text = _truthy(data.get("text") if "text" in data else qp.get("text"))
        except Exception:
            pass

        if want_text and not want_structured:
            # Return plain text response
            from django.http import HttpResponse
            return HttpResponse(output, content_type="text/plain; charset=utf-8", status=200)

        if want_structured:
            return Response({
                "session_id": session_id,
                "device_alias": hostname,
                "device_host": device_ip,
                "cli_command": cli_command,
                "raw_output": output,
            }, status=200)

        # Minimal JSON (raw output only)
        base_resp = {"output": output, "device_alias": hostname, "device_host": device_ip, "session_id": session_id, "resolved_device_alias": hostname, "resolution_method": resolution_method}
        if resolved_device_dict and resolved_device_dict.get("jump_via"):
            base_resp["jump_via"] = resolved_device_dict.get("jump_via")
            # Heuristic: output already cleaned in jump path; mark flag
            base_resp["cleaned"] = True
        return Response(base_resp, status=200)

    def _run_command_legacy_ssh(self, host: str, username: str, password: str, command: str, port: int = 22,
                                 conn_timeout: float = 8.0, auth_timeout: float = 10.0) -> str:
        """Minimal SSH exec using Paramiko Transport with legacy algorithms.

        Matches options similar to:
        -oKexAlgorithms=+diffie-hellman-group1-sha1
        -oHostKeyAlgorithms=+ssh-rsa
        -oCiphers=+aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc
        -oMACs=+hmac-sha1,hmac-sha1-96,hmac-md5,hmac-md5-96
        """
        ciphers = [s.strip() for s in os.getenv("SSH_LEGACY_CIPHERS", "aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc").split(",") if s.strip()]
        kex = [s.strip() for s in os.getenv("SSH_LEGACY_KEX", "diffie-hellman-group1-sha1").split(",") if s.strip()]
        macs = [s.strip() for s in os.getenv("SSH_LEGACY_MACS", "hmac-sha1,hmac-sha1-96,hmac-md5,hmac-md5-96").split(",") if s.strip()]
        key_types = [s.strip() for s in os.getenv("SSH_LEGACY_KEY_TYPES", "ssh-rsa").split(",") if s.strip()]

        s = socket.create_connection((host, port), timeout=conn_timeout)
        t = paramiko.Transport(s)
        so = t.get_security_options()
        # Older Paramiko builds (or stripped versions) may lack some attributes (e.g. macs)
        def _safe_set(attr: str, values):
            if not values:
                return
            if hasattr(so, attr):
                try:
                    setattr(so, attr, tuple(values))
                except Exception as e:  # pragma: no cover
                    print(f"[legacy ssh] failed setting {attr}: {e}")
            else:  # pragma: no cover
                print(f"[legacy ssh] skipping unsupported security option: {attr}")

        _safe_set("ciphers", ciphers)
        _safe_set("kex", kex)
        _safe_set("macs", macs)
        _safe_set("key_types", key_types)

        t.start_client(timeout=auth_timeout)
        t.auth_password(username=username, password=password)
        chan = t.open_session(timeout=conn_timeout)
        chan.settimeout(conn_timeout)
        chan.invoke_shell()
        # Reduce paging and run command
        try:
            chan.send("terminal length 0\n")
            time.sleep(0.2)
            if chan.recv_ready():
                _ = chan.recv(65535)
        except Exception:
            pass
        chan.send(command + "\n")

        output_chunks = []
        end_time = time.time() + max(conn_timeout, 5)
        while time.time() < end_time:
            time.sleep(0.2)
            if chan.recv_ready():
                output_chunks.append(chan.recv(65535).decode(errors="ignore"))
            if chan.exit_status_ready():
                break
        try:
            chan.close()
        finally:
            t.close()
        return "".join(output_chunks).strip()

    def _run_via_jump(self, jump_device: dict, target_device: dict, cli_command: str, primary_ip: str,
                       username: str, password: str, enable_secret: str | None, conn_timeout: float = 8.0) -> str:
        """Interactive nested SSH (jump -> target) capturing only target command output.

        Process:
          1. Connect to jump (Netmiko)
          2. ssh to target loopback/host (prefers loopback)
          3. Handle fingerprint (yes/no) and password prompts
          4. Disable paging on target (terminal length 0)
          5. Execute cli_command
          6. Read until target prompt reappears
          7. Sanitize output (remove echoes, prompts, noise)
        """
        jump_host = jump_device.get("host")
        if not jump_host:
            raise RuntimeError("jump device missing host")
        target_host = target_device.get("host") or primary_ip  # Use primary host only (loopback disabled)
        if not target_host:
            raise RuntimeError("target device missing host")
        target_alias = (target_device.get("alias") or target_device.get("ALIAS") or target_device.get("name") or "").strip() or None
        jd = {
            "device_type": jump_device.get("device_type", "cisco_ios"),
            "host": jump_host,
            "username": jump_device.get("username") or username,
            "password": jump_device.get("password") or password,
            "secret": jump_device.get("secret"),
            "fast_cli": False,
            "timeout": conn_timeout,
            "conn_timeout": conn_timeout,
            "auth_timeout": conn_timeout,
            "banner_timeout": 20,
            "allow_agent": False,
            "use_keys": False,
            "port": 22,
        }
        net_jump = None
        try:
            net_jump = ConnectHandler(**jd)
            try:
                if jd.get("secret"):
                    net_jump.enable()
            except Exception:
                pass
            def _sleep(s=0.35):
                time.sleep(s)
            def _read_all(window=0.4):
                end = time.time() + window
                buf = []
                while time.time() < end:
                    try:
                        chunk = net_jump.read_channel()
                    except Exception:
                        break
                    if chunk:
                        buf.append(chunk)
                        time.sleep(0.05)
                    else:
                        time.sleep(0.05)
                return "".join(buf)
            jump_prompt = None
            try:
                jump_prompt = net_jump.find_prompt().strip()
            except Exception:
                pass
            # ------------------- Enhanced multi-host attempt + identity verification -------------------
            # Build ordered candidate hosts: PRIMARY HOST ONLY (loopback disabled) -> alt_hosts
            candidate_hosts: list[str] = []
            # COMMENTED OUT: Loopback disabled
            # if target_device.get("loopback") and target_device.get("loopback") != target_device.get("host"):
            #     candidate_hosts.append(target_device.get("loopback"))  # type: ignore[arg-type]
            if target_device.get("host"):
                candidate_hosts.append(target_device.get("host"))  # type: ignore[arg-type]
            try:
                for ah in (target_device.get("alt_hosts") or []):
                    if ah and ah not in candidate_hosts:
                        candidate_hosts.append(ah)
            except Exception:
                pass
            if not candidate_hosts:
                candidate_hosts.append(target_host)

            expected_sub = (target_device.get('prompt_contains') or target_alias or '').strip() or None
            strict_check = os.getenv('DISABLE_TARGET_PROMPT_ALIAS_CHECK', '0') != '1'
            identity_verify_enabled = os.getenv('IDENTITY_VERIFY_ON_PROMPT_MISS', '1') == '1'
            verify_cmd_env = os.getenv('VERIFY_IDENTITY_COMMAND')
            verify_cmds = [c for c in [verify_cmd_env, 'show hostname', 'show running-config | include hostname'] if c]
            allow_generic_env = os.getenv('ALLOW_GENERIC_TARGET_PROMPT', '1') == '1'
            strict_mode = os.getenv('STRICT_JUMP_PROMPT', '0') == '1'
            # Device-specific relax flag (devices.json can set "relax_prompt": true)
            if target_device.get('relax_prompt'):
                strict_check = False
                print(f"[jump] relax_prompt flag active for device; disabling strict alias enforcement")
            # Per-alias environment relaxation list (comma separated aliases)
            relax_aliases_env = {a.strip().upper() for a in os.getenv('RELAX_PROMPT_ALIASES', '').split(',') if a.strip()}
            if target_alias and target_alias.upper() in relax_aliases_env:
                strict_check = False
                print(f"[jump] alias {target_alias} in RELAX_PROMPT_ALIASES; disabling strict alias enforcement")
            # Device-specific strict flag (devices.json can set "strict_prompt": true) to force alias match
            if target_device.get('strict_prompt'):
                strict_check = True
                strict_mode = True
                print(f"[jump] strict_prompt flag active for device; enforcing alias substring and disabling generic fallback")
            # ALWAYS_STRICT_ALIASES env to force alias-based success only
            always_strict_aliases = {a.strip().upper() for a in os.getenv('ALWAYS_STRICT_ALIASES', '').split(',') if a.strip()}
            if target_alias and target_alias.upper() in always_strict_aliases:
                strict_check = True
                strict_mode = True  # treat as strict mode for fallback gating
                print(f"[jump] alias {target_alias} in ALWAYS_STRICT_ALIASES; disabling generic fallback")
            # Device-driven identity verification enhancements:
            # identity_verify_commands: list override of commands to run to detect alias/identity
            # identity_accept_substrings: list of substrings (case-insensitive) ANY of which validate identity
            id_verify_cmds_cfg = target_device.get('identity_verify_commands') or []
            if isinstance(id_verify_cmds_cfg, list) and id_verify_cmds_cfg:
                verify_cmds = id_verify_cmds_cfg
            id_accept_subs = []
            cfg_accept = target_device.get('identity_accept_substrings') or []
            if isinstance(cfg_accept, list):
                id_accept_subs = [s for s in cfg_accept if isinstance(s, str) and s.strip()]

            executed_ssh_cmds: set[str] = set()
            final_prompt = None
            final_host = None
            alias_verified = False
            last_attempt_error: Exception | None = None
            generic_candidate: dict | None = None  # store {'prompt': str, 'host': str} if we see a usable generic prompt

            for attempt, cand_host in enumerate(candidate_hosts, start=1):
                try:
                    leg_kex = os.getenv("SSH_LEGACY_KEX", "diffie-hellman-group1-sha1")
                    leg_hostkeys = os.getenv("SSH_LEGACY_KEY_TYPES", "ssh-rsa")
                    leg_ciphers = os.getenv("SSH_LEGACY_CIPHERS", "aes128-cbc,3des-cbc,aes192-cbc,aes256-cbc")
                    leg_macs = os.getenv("SSH_LEGACY_MACS", "hmac-sha1,hmac-sha1-96,hmac-md5,hmac-md5-96")
                    ssh_cmd_full = (
                        f"ssh -o KexAlgorithms=+{leg_kex} -o HostKeyAlgorithms=+{leg_hostkeys} "
                        f"-o Ciphers=+{leg_ciphers} -o MACs=+{leg_macs} "
                        f"-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout={int(conn_timeout)} {username}@{cand_host}"
                    )
                    print(f"[jump-try] candidate={cand_host} attempt={attempt}/{len(candidate_hosts)}")
                    executed_ssh_cmds.add(ssh_cmd_full)
                    net_jump.write_channel(ssh_cmd_full + "\n")
                    _sleep(0.6)
                    buf = _read_all(0.9)
                    if "Are you sure you want to continue" in buf:
                        net_jump.write_channel("yes\n")
                        _sleep(0.6)
                        buf += _read_all(0.9)
                    pass_tries = 0
                    while "assword" in buf and pass_tries < 3 and "denied" not in buf.lower():
                        net_jump.write_channel(password + "\n")
                        pass_tries += 1
                        _sleep(0.9)
                        buf += _read_all(1.2)
                        if any(l.strip().endswith('#') for l in buf.splitlines()):
                            break
                    # Extract prompt
                    target_prompt = None
                    for line in buf.splitlines()[::-1]:
                        l = line.strip()
                        if l.endswith('#') and (not jump_prompt or l != jump_prompt):
                            target_prompt = l
                            break
                    if not target_prompt:
                        net_jump.write_channel("\n")
                        _sleep(0.5)
                        extra = _read_all(0.6)
                        for line in extra.splitlines()[::-1]:
                            l = line.strip()
                            if l.endswith('#') and (not jump_prompt or l != jump_prompt):
                                target_prompt = l
                                break
                    if not target_prompt:
                        # simplified retry
                        simple_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null {username}@{cand_host}"
                        executed_ssh_cmds.add(simple_cmd)
                        net_jump.write_channel(simple_cmd + "\n")
                        _sleep(0.8)
                        buf2 = _read_all(1.0)
                        if "Are you sure you want to continue" in buf2:
                            net_jump.write_channel("yes\n")
                            _sleep(0.6)
                            buf2 += _read_all(0.8)
                        pass_tries2 = 0
                        while "assword" in buf2 and pass_tries2 < 2 and "denied" not in buf2.lower():
                            net_jump.write_channel(password + "\n")
                            pass_tries2 += 1
                            _sleep(0.9)
                            buf2 += _read_all(1.2)
                        for line in buf2.splitlines()[::-1]:
                            l = line.strip()
                            if l.endswith('#') and (not jump_prompt or l != jump_prompt):
                                target_prompt = l
                                break
                    if not target_prompt:
                        target_prompt = '#'

                    alias_ok = False
                    if expected_sub and target_prompt:
                        alias_ok = expected_sub.upper() in target_prompt.upper()
                    # Identity verification sequence if alias not in prompt
                    if strict_check and expected_sub and not alias_ok and identity_verify_enabled:
                        try:
                            for vcmd in verify_cmds:
                                net_jump.write_channel(vcmd + "\n")
                                _sleep(0.7)
                                ident_out = _read_all(1.0)
                                ident_upper = ident_out.upper()
                                expected_upper = expected_sub.upper()
                                match_expected = expected_upper in ident_upper
                                match_alt = any(sub.upper() in ident_upper for sub in id_accept_subs)
                                if match_expected or match_alt:
                                    alias_ok = True
                                    alias_verified = True
                                    print(f"[jump-identity] identity matched via '{vcmd}' (expected={match_expected} alt={match_alt})")
                                    break
                        except Exception as ide:
                            print(f"[jump-identity] verification error: {ide}")

                    if strict_check and expected_sub and not alias_ok:
                        # Host/IP-based acceptance fallback (if device sets allow_host_identity_fallback=true)
                        host_id_fallback = bool(target_device.get('allow_host_identity_fallback'))
                        cand_is_known = cand_host in {target_device.get('loopback'), target_device.get('host')} or cand_host in set(target_device.get('alt_hosts') or [])
                        if host_id_fallback and cand_is_known:
                            print(f"[jump-try] candidate={cand_host} alias missing but host matches configured device and host identity fallback enabled -> accepting")
                            final_prompt = target_prompt
                            final_host = cand_host
                            break
                        print(f"[jump-try] candidate={cand_host} failed alias/prompt check -> trying next")
                        if generic_candidate is None and target_prompt and target_prompt.strip().endswith('#'):
                            generic_candidate = {"prompt": target_prompt, "host": cand_host}
                        continue

                    # Accept generic prompt if relaxed
                    if not strict_check or not expected_sub:
                        final_prompt = target_prompt
                        final_host = cand_host
                        break
                    if expected_sub and alias_ok:
                        final_prompt = target_prompt
                        final_host = cand_host
                        break
                except Exception as e:
                    last_attempt_error = e
                    print(f"[jump-try] candidate={cand_host} exception -> {e}")
                    continue

            if final_prompt is None:
                # If strict_mode (incl. strict_prompt) active -> fail hard
                if strict_mode:
                    raise RuntimeError(f"Unable to positively identify target device (strict); hosts tried={candidate_hosts}")
                # Else allow relaxed generic fallback
                fallback_generic_allowed = allow_generic_env
                if generic_candidate and fallback_generic_allowed:
                    print(f"[jump] falling back to generic prompt from host {generic_candidate['host']} (alias verification failed, relaxed mode)")
                    final_prompt = generic_candidate['prompt']
                    final_host = generic_candidate['host']
                else:
                    raise RuntimeError(f"Unable to reach target device via any candidate host {candidate_hosts}; last_error={last_attempt_error}")
            if strict_check and expected_sub and expected_sub.upper() not in final_prompt.upper():
                # If we accepted via host identity fallback earlier, alias_verified flag would be True; check that first.
                if alias_verified:
                    print(f"[jump] alias substring absent but identity verified via command output / host fallback")
                else:
                    # If strict but device permits host identity fallback and final_host is a configured address, allow.
                    host_id_fallback = bool(target_device.get('allow_host_identity_fallback'))
                    if strict_mode and host_id_fallback and final_host in {target_device.get('loopback'), target_device.get('host')} | set(target_device.get('alt_hosts') or []):
                        print(f"[jump] strict alias missing; permitting due to allow_host_identity_fallback on known host {final_host}")
                    elif strict_mode:
                        raise RuntimeError(f"Did not reach target prompt containing alias {expected_sub}; last prompt {final_prompt}")
                    elif allow_generic_env:
                        print(f"[jump] proceeding with generic prompt final={final_prompt} without alias (non-strict relaxed)")
                    else:
                        raise RuntimeError(f"Did not reach target prompt containing alias {expected_sub}; last prompt {final_prompt}")
            target_prompt = final_prompt
            target_host = final_host or target_host
            # Disable paging
            net_jump.write_channel("terminal length 0\n")
            _sleep(0.4)
            _ = _read_all(0.5)
            # Run command
            net_jump.write_channel(cli_command + "\n")
            _sleep(0.5)
            collected = []
            end_time = time.time() + max(conn_timeout, 6)
            while time.time() < end_time:
                ch = _read_all(0.5)
                if ch:
                    collected.append(ch)
                    # Only treat as end if prompt resembles target (endswith # and not jump prompt)
                    if any(ln.strip().endswith('#') and (not jump_prompt or ln.strip() != jump_prompt) for ln in ch.splitlines()):
                        break
                else:
                    time.sleep(0.2)
            try:
                net_jump.write_channel("exit\n")
            except Exception:
                pass
            raw_segment = "".join(collected)
            lines = raw_segment.splitlines()
            output_lines = []
            seen_echo = False
            for ln in lines:
                s = ln.rstrip()
                if not s:
                    continue
                if not seen_echo and cli_command in s:
                    seen_echo = True
                    continue
                if s.strip().endswith('#') and len(s.strip()) <= len(target_prompt) + 4:
                    # end
                    break
                if s.strip().startswith('% Invalid input'):
                    continue
                if s.strip() in executed_ssh_cmds:
                    continue
                if jump_prompt and s.strip() == jump_prompt:
                    continue
                # Filter timestamp only lines like '01:40 AM'
                ts = s.replace('AM','').replace('PM','').strip()
                if ts.count(':') == 1 and ts.replace(':','').replace(' ','').isdigit() and len(ts) <= 8:
                    continue
                output_lines.append(s)
            return "\n".join(output_lines).strip()
        finally:
            if net_jump:
                try:
                    net_jump.disconnect()
                except Exception:
                    pass


@method_decorator(csrf_exempt, name="dispatch")
class MeAPIView(APIView):
    # Auth removed conditionally via settings (DISABLE_AUTH). Override only if needed.

    def get(self, request):
        user = getattr(request, 'user', None)
        if not user or not getattr(user, 'is_authenticated', False):
            return Response({"authenticated": False}, status=401)
        return Response({
            "authenticated": True,
            "uid": getattr(user, 'uid', None),
            "email": getattr(user, 'email', None),
            "is_admin": getattr(user, 'is_admin', False),
        })


@method_decorator(csrf_exempt, name="dispatch")
class DeviceLocationAPIView(APIView):
    """Return simplified location markers (UK + India) for the globe.

    Optional query param: sites=uk,in  (comma separated)
    Response: {"locations": [{alias, site, lat, lng, label}]}  (lat/lng may be null if unknown)
    """

    FALLBACK_COORDS = {
        "UKLONB10C01": {"lat": 51.5072, "lng": -0.1276, "label": "UK - London"},
        "INVIJB1C01": {"lat": 16.5062, "lng": 80.6480, "label": "India - Vijayawada (Cisco)"},
        "INVIJB10A01": {"lat": 16.5062, "lng": 80.6480, "label": "India - Vijayawada (Aruba)"},
    }

    SITE_ALIAS_PREF = {
        "uk": ["UKLONB10C01"],
        "london": ["UKLONB10C01"],
        # India - both devices in Vijayawada
        "in": ["INVIJB1C01", "INVIJB10A01"],
        "india": ["INVIJB1C01", "INVIJB10A01"],
        "vijayawada": ["INVIJB1C01", "INVIJB10A01"],
        "vij": ["INVIJB1C01", "INVIJB10A01"],
        "lab": ["INVIJB10A01"],
        "aruba": ["INVIJB10A01"],
    }

    def get(self, request):
        devices_map = get_devices()
        sites_param = getattr(request, 'query_params', {}).get('sites', 'uk,in') if hasattr(request, 'query_params') else 'uk,in'
        requested_sites = [s.strip().lower() for s in sites_param.split(',') if s.strip()]
        chosen = []
        used_aliases = set()
        for site in requested_sites:
            prefs = self.SITE_ALIAS_PREF.get(site, [])
            # collect all valid candidates for this site
            valid_aliases = [cand for cand in prefs if cand in devices_map]
            # fallback if none matched explicitly
            if not valid_aliases:
                if site in ("uk", "london"):
                    alias = next((a for a in devices_map.keys() if a.startswith("UKLONB")), None) or next((a for a in devices_map.keys() if a.startswith("UK")), None)
                    if alias:
                        valid_aliases.append(alias)
                elif site in ("in", "india", "vijayawada"):
                    vij = next((a for a in devices_map.keys() if a.startswith("INVIJB1SW")), None)
                    hyd = next((a for a in devices_map.keys() if a.startswith("INHYDB3SW")), None)
                    for a in [vij, hyd, next((a for a in devices_map.keys() if a.startswith("IN")), None)]:
                        if a and a not in valid_aliases:
                            valid_aliases.append(a)
                elif site in ("hyd", "hyderabad", "hyderabaad", "lab", "aruba"):
                    alias = next((a for a in devices_map.keys() if a.startswith("INHYDB3SW")), None)
                    if alias:
                        valid_aliases.append(alias)
            for alias in valid_aliases:
                if not alias or alias in used_aliases:
                    continue
                used_aliases.add(alias)
                dev = devices_map.get(alias, {})
                lat = dev.get("lat") or dev.get("latitude")
                lng = dev.get("lng") or dev.get("longitude")
                fb = self.FALLBACK_COORDS.get(alias)
                if (lat is None or lng is None) and fb:
                    lat = fb["lat"]
                    lng = fb["lng"]
                label = (fb and fb.get("label")) or alias
                chosen.append({
                    "alias": alias,
                    "site": site,
                    "lat": lat,
                    "lng": lng,
                    "label": label,
                })
        return Response({"locations": chosen}, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class DeviceHealthAPIView(APIView):
    """Return recent CPU samples and latest alerts per device."""

    def get(self, request):
        try:
            limit = int(getattr(request, 'query_params', {}).get('limit', '50'))
        except Exception:
            limit = 50
        include_cleared = str(getattr(request, 'query_params', {}).get('include_cleared', '0')).lower() in ('1','true','yes')
        # Fetch recent samples
        samples = list(DeviceHealth.objects.order_by('-created_at', '-id')[:limit].values('alias', 'cpu_pct', 'created_at'))
        # Latest alert per alias/category
        latest_alerts = {}
        base_qs = HealthAlert.objects.order_by('-created_at')
        if not include_cleared:
            base_qs = base_qs.filter(cleared_at__isnull=True)
        for a in base_qs[:200]:
            key = (a.alias, a.category)
            if key not in latest_alerts:
                latest_alerts[key] = {
                    'alias': a.alias,
                    'category': a.category,
                    'severity': a.severity,
                    'message': a.message,
                    'created_at': a.created_at,
                    'cleared_at': a.cleared_at,
                }
        alerts = list(latest_alerts.values())
        return Response({
            'samples': samples,
            'alerts': alerts,
        }, status=200)


@method_decorator(csrf_exempt, name="dispatch")
class HealthzAPIView(APIView):
    """Lightweight health summary for dashboards and probes.

    GET /healthz?window_minutes=60 returns:
      - last_sample_per_device
      - active_alerts_count by category
    """

    def get(self, request):
        try:
            window_min = int(getattr(request, 'query_params', {}).get('window_minutes', '60'))
        except Exception:
            window_min = 60
        since = datetime.utcnow() - timedelta(minutes=window_min)
        # last sample per alias
        last_by_alias = {}
        for row in DeviceHealth.objects.filter(created_at__gte=since).order_by('alias', '-created_at', '-id').values('alias','cpu_pct','created_at'):
            a = row['alias']
            if a not in last_by_alias:
                last_by_alias[a] = row
        # active alerts count by category
        active = HealthAlert.objects.filter(cleared_at__isnull=True)
        cat_counts = {}
        for a in active.values('category'):
            c = a['category']
            cat_counts[c] = cat_counts.get(c, 0) + 1
        return Response({
            'window_minutes': window_min,
            'last_samples': last_by_alias,
            'active_alerts_by_category': cat_counts,
        }, status=200)
