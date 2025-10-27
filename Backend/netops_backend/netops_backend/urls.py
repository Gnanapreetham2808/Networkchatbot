from django.urls import path, include
from rest_framework.routers import DefaultRouter

from netops_backend.vlan_agent.views import VLANIntentViewSet

router = DefaultRouter()
router.register(r"vlan-intents", VLANIntentViewSet, basename="vlan-intent")

urlpatterns = [
    # Primary API namespace
    path("api/nlp/", include("chatbot.urls")),
    path("api/", include(router.urls)),
    # Convenience shortcut for local testing
    path("", include("chatbot.urls")),
]
