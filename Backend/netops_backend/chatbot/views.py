from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .network import run_command_on_switch
from .nlp_engine import extract_intent_and_entities, map_to_cli_command

class NetworkCommandAPIView(APIView):
    def post(self, request):
        device_ip = request.data.get("device_ip")
        user_query = request.data.get("query")

        if not device_ip or not user_query:
            return Response({"error": "Missing device_ip or query"}, status=400)

        # 🔠 Step 1: NLP extraction
        intent, entities = extract_intent_and_entities(user_query)

        # ⚙️ Step 2: Map intent/entities to CLI
        command = map_to_cli_command(intent, user_query, entities)

        # 🖧 Step 3: Run on switch
        output = run_command_on_switch(device_ip, command)

        return Response({
            "query": user_query,
            "intent": intent,
            "entities": entities,
            "cli_command": command,
            "output": output
        }, status=status.HTTP_200_OK)
