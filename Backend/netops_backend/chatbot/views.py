from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .network import run_command_on_switch

class NetworkCommandAPIView(APIView):
    def post(self, request):
        query = request.data.get("query")
        device_ip = request.data.get("device_ip")

        # For now, just run a static command
        output = run_command_on_switch(device_ip, "show ip interface brief")
        return Response({"output": output}, status=status.HTTP_200_OK)
