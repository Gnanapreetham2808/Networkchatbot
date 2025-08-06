from django.urls import path
from .views import NetworkCommandAPIView

urlpatterns = [
    path("run-command/", NetworkCommandAPIView.as_view()),
]
