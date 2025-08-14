from django.urls import path
from .views import NetworkCommandAPIView

urlpatterns = [
    path("network-command/", NetworkCommandAPIView.as_view(), name="network-command"),
]
