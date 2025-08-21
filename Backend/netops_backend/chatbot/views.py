from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .network import run_command_on_switch
from .nlp_engine.intent import classify_intent
from .nlp_engine.ner import extract_entities
from .nlp_engine.map_command import map_to_cli
from .nlp_engine.safety import gate_command
from .nlp_engine.response_generator import generate_natural_response
from .nlp_engine.retrieval import log_interaction

from .auth import FirebaseAuthentication, IsAdminOrChatUser
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


@method_decorator(csrf_exempt, name="dispatch")
class NetworkCommandAPIView(APIView):
    # Auth removed conditionally via settings (DISABLE_AUTH). Override only if needed.

    def get(self, request):
        return Response(
            {"message": "GET request received. This endpoint is intended for POST requests with device_ip and query."},
            status=status.HTTP_200_OK
        )

    def post(self, request):
        # Debug: log incoming request
        try:
            print("[NetworkCommandAPIView] Incoming headers Content-Type=", request.headers.get('Content-Type'))
            print("[NetworkCommandAPIView] Raw body bytes:", len(getattr(request, 'body', b'')))
            if getattr(request, 'body', b''):
                preview = request.body[:200]
                print("[NetworkCommandAPIView] Body preview:", preview)
        except Exception as _e:
            print("[NetworkCommandAPIView] Logging error", _e)

        # Extract request data
        device_ip = request.data.get("device_ip") if hasattr(request, "data") else None
        user_query = request.data.get("query") if hasattr(request, "data") else None
        confirm_sensitive = request.data.get("confirm_sensitive", False) if hasattr(request, "data") else False

        # Try raw body JSON if parsing failed
        if (not device_ip or not user_query) and getattr(request, 'body', None):
            try:
                import json
                raw = json.loads(request.body.decode("utf-8"))
                device_ip = device_ip or raw.get("device_ip")
                user_query = user_query or raw.get("query")
                if 'confirm_sensitive' in raw:
                    confirm_sensitive = raw['confirm_sensitive']
            except Exception:
                pass

        # Query params fallback
        if not device_ip and hasattr(request, 'query_params'):
            device_ip = request.query_params.get('device_ip')
        if not user_query and hasattr(request, 'query_params'):
            user_query = request.query_params.get('query')

        # If still missing required fields
        if not device_ip or not user_query:
            return Response(
                {
                    "error": "Missing device_ip or query",
                    "received": {"device_ip": device_ip, "query": user_query},
                    "content_type": request.headers.get('Content-Type'),
                    "raw_body_len": len(getattr(request, 'body', b'')),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 1: NLP extraction
        intent_result = classify_intent(user_query)
        entities_result = extract_entities(user_query)

        # Detect target entity
        command_target = None
        for ent in entities_result.get("entities", []):
            if ent["entity_group"].lower() in ["interface", "ip", "vlan"]:
                command_target = ent["word"]
                break

        fallback_reason = None if command_target else "No specific entity extracted; proceeding with generic command mapping"

        # Step 2: Map to CLI
        mapping_result = map_to_cli(user_query)
        cli_command = mapping_result.get("command", "")

        # Step 2.1: Safety check
        safety_info = gate_command(cli_command)

        # Auto-add 'show' for safe read-only queries
        if not safety_info["allowed"] and intent_result.get("label") == "show":
            if not cli_command.lower().startswith("show"):
                cli_command = f"show {cli_command}".strip()
                safety_info = gate_command(cli_command)

        # Sensitive command check
        if safety_info["needs_confirmation"] and not confirm_sensitive:
            return Response({
                "warning": "Sensitive command detected. Please confirm to proceed.",
                "intent": intent_result,
                "entities": entities_result,
                "cli_command": cli_command,
                "safety": safety_info,
                "requires_confirmation": True
            }, status=status.HTTP_200_OK)

        # Block if unsafe
        if not safety_info["allowed"] and not safety_info["needs_confirmation"]:
            return Response(
                {"error": f"Command not allowed: {safety_info['reason']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Step 3: Run command
        try:
            output = run_command_on_switch(device_ip, cli_command)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Step 4: Natural language summarization
        output_natural = generate_natural_response(intent_result, entities_result, cli_command, output)

        # Step 4.1: Log interaction for future retrieval (best-effort)
        try:
            log_interaction(user_query, output)
        except Exception as e:
            print("[NetworkCommandAPIView] retrieval log error", e)

        # Step 5: Response
        return Response({
            "query": user_query,
            "intent": intent_result,
            "entities": entities_result,
            "cli_command": cli_command,
            "command_mapping": mapping_result,
            "safety": safety_info,
            "output_raw": output,
            "output_natural": output_natural,
            "output": output_natural,
            "note": fallback_reason
        }, status=status.HTTP_200_OK)


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
