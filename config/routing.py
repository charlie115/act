from django.urls import path

from arbot.consumers import CoinConsumer

websocket_urlpatterns = [
    path("ws/coins/", CoinConsumer.as_asgi()),
]
