from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .network import run_command_on_switch
from .nlp_engine.intent import classify_intent
from .nlp_engine.ner import extract_entities
from .nlp_engine.map_command import map_to_cli
from .nlp_engine.safety import gate_command


class NetworkCommandAPIView(APIView):
    def get(self, request):
        return Response({"message": "GET request received. This endpoint is intended for POST requests with device_ip and query."}, status=status.HTTP_200_OK)

    def post(self, request):
        # ---- Debug instrumentation START (remove in production) ----
        try:
            print("[NetworkCommandAPIView] Incoming headers Content-Type=", request.headers.get('Content-Type'))
            print("[NetworkCommandAPIView] Raw body bytes:", len(getattr(request, 'body', b'')))
            if getattr(request, 'body', b''):
                preview = request.body[:200]
                print("[NetworkCommandAPIView] Body preview:", preview)
        except Exception as _e:
            print("[NetworkCommandAPIView] Logging error", _e)
        # ---- Debug instrumentation END ----

        # Robust extraction: DRF should parse JSON into request.data, but handle fallbacks
        device_ip = request.data.get("device_ip") if hasattr(request, "data") else None
        user_query = request.data.get("query") if hasattr(request, "data") else None
        confirm_sensitive = request.data.get("confirm_sensitive", False) if hasattr(request, "data") else False  # 👈 New flag from frontend

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

        # Query params fallback (for manual browser tests)
        if not device_ip and hasattr(request, 'query_params'):
            device_ip = request.query_params.get('device_ip')
        if not user_query and hasattr(request, 'query_params'):
            user_query = request.query_params.get('query')

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

        # 🔠 Step 1: NLP extraction
        intent_result = classify_intent(user_query)
        entities_result = extract_entities(user_query)

        # Determine a target entity for command
        command_target = None
        for ent in entities_result.get("entities", []):
            if ent["entity_group"].lower() in ["interface", "ip", "vlan"]:
                command_target = ent["word"]
                break

        # Allow proceeding even if no specific target was extracted for read-only/show style queries
        if not command_target:
            fallback_reason = "No specific entity extracted; proceeding with generic command mapping"
        else:
            fallback_reason = None

        # ⚙️ Step 2: Map to CLI
        mapping_result = map_to_cli(user_query)
        cli_command = mapping_result.get("command", "")

        # 🚨 Step 2.1: Safety check
        safety_info = gate_command(cli_command)

        # Fallback: if intent is show and command not allowed, try to normalize
        if not safety_info["allowed"] and intent_result.get("label") == "show":
            if not cli_command.lower().startswith("show"):
                cli_command = f"show {cli_command}".strip()
                safety_info = gate_command(cli_command)

        # If it's risky and not confirmed, return early
        if safety_info["needs_confirmation"] and not confirm_sensitive:
            return Response({
                "warning": "Sensitive command detected. Please confirm to proceed.",
                "intent": intent_result,
                "entities": entities_result,
                "cli_command": cli_command,
                "safety": safety_info,
                "requires_confirmation": True
            }, status=status.HTTP_200_OK)

        # If not allowed at all, block it
        if not safety_info["allowed"] and not safety_info["needs_confirmation"]:
            return Response(
                {"error": f"Command not allowed: {safety_info['reason']}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 🖧 Step 3: Run command
        try:
            output = run_command_on_switch(device_ip, cli_command)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "query": user_query,
            "intent": intent_result,
            "entities": entities_result,
            "cli_command": cli_command,
            "command_mapping": mapping_result,
            "safety": safety_info,
            "output": output,
            "note": fallback_reason
        }, status=status.HTTP_200_OK)
