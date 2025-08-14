from django.urls import path, include

urlpatterns = [
    path("api/nlp/", include("chatbot.urls")),
]
