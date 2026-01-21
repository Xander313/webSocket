from django.urls import path
from .consumers import IncidenteConsumer

websocket_urlpatterns = [
    path("ws/incidentes/", IncidenteConsumer.as_asgi()),
]
