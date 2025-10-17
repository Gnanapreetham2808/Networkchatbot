from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .nlp_router import predict_cli


class NetworkCommandAPIView(APIView):
    """Simple API endpoint that maps natural language to a CLI command using the local T5 model.

    POST JSON: {"query": "show interfaces", "device_ip": "192.168.10.1"}
    Response: {"device_ip": ..., "query": ..., "cli_command": ...}
    """

    def post(self, request):
        data = getattr(request, 'data', {}) or {}
        query = data.get("query")
        device_ip = data.get("device_ip") or data.get("ip")

        print(f"[NetworkCommandAPIView] Incoming query={query!r} device_ip={device_ip}")

        if not query:
            return Response({"error": "Missing 'query'"}, status=status.HTTP_400_BAD_REQUEST)
        if not device_ip:
            return Response({"error": "Missing 'device_ip'"}, status=status.HTTP_400_BAD_REQUEST)

        cli_command = predict_cli(query)
        print(f"[NetworkCommandAPIView] Predicted command: {cli_command}")

        if cli_command.startswith("[Error]"):
            return Response({"error": cli_command}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({
            "device_ip": device_ip,
            "query": query,
            "cli_command": cli_command,
        }, status=status.HTTP_200_OK)

    def get(self, request):  # Optional simple health/info endpoint
        return Response({"detail": "POST a JSON body with 'query' and 'device_ip'"}, status=200)
