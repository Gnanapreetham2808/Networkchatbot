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
try:
    from Devices.device_resolver import resolve_device  # Devices folder at project root
except ModuleNotFoundError:
    # Fallback if moved inside project package later
    from netops_backend.Devices.device_resolver import resolve_device  # type: ignore

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
        hostname = data.get("hostname") or data.get("device_hostname") or (request.query_params.get("hostname") if hasattr(request, "query_params") else None)

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

        # Resolve device alias from natural language query if explicit device not provided
        resolved_device_dict = None
        ambiguity_candidates = []
        if not device_ip and not hostname:
            dev_dict, candidates, err = resolve_device(query)
            if dev_dict:
                resolved_device_dict = dev_dict
                device_ip = dev_dict.get("host") or dev_dict.get("ip")
                hostname = dev_dict.get("alias") or None
            elif candidates:
                return Response({"error": "Multiple switches found, please specify one", "candidates": candidates}, status=400)
            else:
                # fallback remains: we proceed but connection will likely fail
                pass
        else:
            # If alias specified directly, attempt resolution too for credentials
            alias_candidate = hostname or device_ip
            dev_dict, candidates, err = resolve_device(alias_candidate)
            if dev_dict:
                resolved_device_dict = dev_dict
                device_ip = dev_dict.get("host") or dev_dict.get("ip") or device_ip
            elif candidates:
                return Response({"error": "Multiple switches found, please specify one", "candidates": candidates}, status=400)

        # Fallback to DEFAULT_DEVICE_ALIAS or DEFAULT_DEVICE_IP from env if still not selected
        if not device_ip:
            default_alias = os.getenv("DEFAULT_DEVICE_ALIAS")
            default_ip = os.getenv("DEFAULT_DEVICE_IP")
            if default_alias:
                dev_dict, _, _ = resolve_device(default_alias)
                if dev_dict:
                    resolved_device_dict = dev_dict
                    device_ip = dev_dict.get("host") or dev_dict.get("ip")
                    hostname = dev_dict.get("alias") or default_alias
            elif default_ip:
                device_ip = default_ip

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


        print(f"[NetworkCommandAPIView] query={query!r} target={device_ip} alias_host={hostname}")

        if not device_ip:
            return Response({"error": "Failed to run command"}, status=400)

        cli_command = predict_cli(query)
        print(f"[NetworkCommandAPIView] predicted_cli={cli_command}")
        if not cli_command or cli_command.startswith("[Error]"):
            return Response({"error": "Failed to run command"}, status=500)

        lc = cli_command.strip().lower()
        # Enforce read-only by default
        if not any(lc.startswith(p) for p in SAFE_PREFIXES):
            return Response({"error": "Command not allowed", "command": cli_command}, status=400)
        if any(b in lc for b in BLOCKED_SUBSTRINGS):
            return Response({"error": "Command blocked for safety", "command": cli_command}, status=400)

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

        ssh_device = {
            "device_type": (resolved_device_dict or {}).get("device_type", "cisco_ios"),
            "host": device_ip,
            "username": (resolved_device_dict or {}).get("username") or req_username or env_username,
            "password": (resolved_device_dict or {}).get("password") or req_password or env_password,
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
                        (resolved_device_dict or {}).get("password") or req_password or env_password,
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

        return Response({"output": output}, status=200)

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
        if ciphers:
            so.ciphers = tuple(ciphers)
        if kex:
            so.kex = tuple(kex)
        if macs:
            so.macs = tuple(macs)
        if key_types:
            so.key_types = tuple(key_types)

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
