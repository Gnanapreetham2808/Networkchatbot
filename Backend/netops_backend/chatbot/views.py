from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import os
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException

from netops_backend.nlp_model import predict_cli
try:
    from Devices.device_resolver import resolve_device  # Devices folder at project root
except ModuleNotFoundError:
    # Fallback if moved inside project package later
    from netops_backend.Devices.device_resolver import resolve_device  # type: ignore


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

        print(f"[NetworkCommandAPIView] query={query!r} target={device_ip} alias_host={hostname}")

        if not device_ip:
            return Response({"error": "Failed to run command"}, status=400)

        cli_command = predict_cli(query)
        print(f"[NetworkCommandAPIView] predicted_cli={cli_command}")
        if not cli_command or cli_command.startswith("[Error]"):
            return Response({"error": "Failed to run command"}, status=500)

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
        # Telnet-only attempt
        device = {
            "device_type": (resolved_device_dict or {}).get("device_type", "cisco_ios_telnet" if True else "cisco_ios"),
            "host": device_ip,
            "username": (resolved_device_dict or {}).get("username") or req_username or env_username,
            "password": (resolved_device_dict or {}).get("password") or req_password or env_password,
            "secret": (resolved_device_dict or {}).get("secret") or (req_secret if req_secret is not None else env_secret),
            "fast_cli": True,
            "timeout": conn_timeout,
            "conn_timeout": conn_timeout,
            "auth_timeout": auth_timeout,
            "banner_timeout": banner_timeout,
            "port": 23,
        }
        print("[NetworkCommandAPIView] telnet connect attempt 23")
        try:
            net_connect = ConnectHandler(**device)
        except (NetmikoTimeoutException, NetmikoAuthenticationException, OSError) as e:
            print(f"[NetworkCommandAPIView] telnet connect failed -> {e}")
            return Response({"error": "Unable to connect to device"}, status=502)
        except Exception as e:
            print(f"[NetworkCommandAPIView] unexpected telnet error -> {e}")
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
