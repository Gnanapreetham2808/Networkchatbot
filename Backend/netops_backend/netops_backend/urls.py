from django.urls import path, include

urlpatterns = [
    # Primary API namespace
    path("api/nlp/", include("chatbot.urls")),
    # Convenience shortcut for local testing
    path("", include("chatbot.urls")),
]
