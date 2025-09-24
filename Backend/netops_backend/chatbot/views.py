from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
import socket
import time
try:
    import paramiko  # type: ignore
except Exception:
    paramiko = None  # fallback if not available

from netops_backend.nlp_model import predict_cli
from .models import Conversation, Message
try:
    from Devices.device_resolver import resolve_device, find_device_by_host, get_devices  # Devices folder at project root
except ModuleNotFoundError:
    # Fallback if moved inside project package later
    from netops_backend.Devices.device_resolver import resolve_device, find_device_by_host, get_devices  # type: ignore

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

        # Always attempt resolution each request; use conversation only when no new hints
        resolved_device_dict = None

        def _has_any_hint(q: str) -> bool:
            ql = (q or "").lower()
            return any(k in ql for k in ["vijayawada", "india", "london", "uk", "building 1"]) or bool(hostname)

        dev_dict = None
        candidates = []
        err = None
        # Try explicit alias/hostname first
        if hostname:
            dev_dict, candidates, err = resolve_device(hostname)
        # If no explicit alias or not found, try the query text (location fuzzy matching inside resolver)
        if not dev_dict:
            q_to_use = query or ""
            dev_dict2, candidates2, err2 = resolve_device(q_to_use)
            if dev_dict2:
                dev_dict, candidates, err = dev_dict2, [], None
            elif candidates2:
                candidates, err = candidates2, err2

        # If the user intends the Vijayawada site (e.g., query includes it) and still no device resolved,
        # force-select INVIJB1SW1 if available.
        if not dev_dict and ("vijayawada" in (query or "").lower() or (hostname and str(hostname).upper() == "INVIJB1SW1")):
            dev_fallback, _, _ = resolve_device("INVIJB1SW1")
            if dev_fallback:
                dev_dict = dev_fallback

        if dev_dict:
            resolved_device_dict = dev_dict
            device_ip = dev_dict.get("host") or dev_dict.get("ip")
            hostname = dev_dict.get("alias") or hostname
        elif candidates:
            return Response({"error": "Multiple switches found, please specify one", "candidates": candidates, "session_id": session_id}, status=400)
        else:
            # No resolution → reuse conversation device if exists, but also restore full device dict
            if conversation and (conversation.device_host or conversation.device_alias):
                # Prefer finding by host to pull credentials/type
                alias_found, dev_by_host = (None, None)
                if conversation.device_host:
                    alias_found, dev_by_host = find_device_by_host(conversation.device_host)
                if dev_by_host:
                    resolved_device_dict = dev_by_host
                    device_ip = dev_by_host.get("host")
                    hostname = dev_by_host.get("alias") or alias_found or conversation.device_alias
                elif conversation.device_alias:
                    # Fallback: try resolving by stored alias (handles IP changes)
                    alias_dev, _, _ = resolve_device(conversation.device_alias)
                    if alias_dev:
                        resolved_device_dict = alias_dev
                        device_ip = alias_dev.get("host") or alias_dev.get("ip")
                        hostname = alias_dev.get("alias") or conversation.device_alias
                    else:
                        hostname = conversation.device_alias
                        device_ip = conversation.device_host

        # Fallback to DEFAULT_DEVICE_ALIAS or DEFAULT_DEVICE_IP from env if still not selected (UK default behavior)
        if not device_ip:
            default_alias = os.getenv("DEFAULT_DEVICE_ALIAS") or "UKLONB1SW2"
            default_ip = os.getenv("DEFAULT_DEVICE_IP")
            if default_alias:
                dev_dict, _, _ = resolve_device(default_alias)
                if dev_dict:
                    resolved_device_dict = dev_dict
                    device_ip = dev_dict.get("host") or dev_dict.get("ip")
                    hostname = dev_dict.get("alias") or default_alias
                    print(f"[NetworkCommandAPIView] default alias fallback -> {default_alias} {device_ip}")
            elif default_ip:
                device_ip = default_ip
                print(f"[NetworkCommandAPIView] default IP fallback -> {default_ip}")

        # If we have only an IP at this point (e.g., forced or provided) and no resolved dict, try to map it to a known device
        if device_ip and not resolved_device_dict:
            alias_found, dev_by_host = find_device_by_host(device_ip)
            if dev_by_host:
                resolved_device_dict = dev_by_host
                hostname = dev_by_host.get("alias") or alias_found or hostname

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


        print(f"[NetworkCommandAPIView] query={query!r} session={session_id} target={device_ip} alias_host={hostname}")

        if not device_ip:
            return Response({"error": "Failed to run command", "session_id": session_id}, status=400)

        cli_command = predict_cli(query)
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

        if net_connect is None:
            # Optional legacy SSH fallback for very old devices
            if os.getenv("ENABLE_LEGACY_SSH", "1") == "1" and paramiko is not None:
                try:
                    output = self._run_command_legacy_ssh(
                        device_ip,
                        (resolved_device_dict or {}).get("username") or req_username or env_username,
                        chosen_password,
                        cli_command,
                        port=22,
                        conn_timeout=conn_timeout,
                        auth_timeout=auth_timeout,
                    )
                    return Response({"output": output, "legacy": True}, status=200)
                except Exception as e:
                    print(f"[NetworkCommandAPIView] legacy ssh failed -> {e}")
            return Response({"error": "Unable to connect to device"}, status=502)

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
        return Response({"output": output, "device_alias": hostname, "device_host": device_ip, "session_id": session_id}, status=200)

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
