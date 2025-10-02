from django.urls import path
from .views import NetworkCommandAPIView, MeAPIView, DeviceLocationAPIView, DeviceStatusAPIView

urlpatterns = [
    path("network-command/", NetworkCommandAPIView.as_view(), name="network-command"),
    path("auth/me/", MeAPIView.as_view(), name="me"),
    path("device-locations/", DeviceLocationAPIView.as_view(), name="device-locations"),
    path("device-status/", DeviceStatusAPIView.as_view(), name="device-status"),
]
