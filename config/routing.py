from channels.routing import URLRouter
from django.urls import path

from arbot.consumers import CoinConsumer
from lib.middleware import TokenAuthMiddleware


websocket_urlpatterns = TokenAuthMiddleware(
    URLRouter(
        [
            path("ws/coins/", CoinConsumer.as_asgi()),
        ]
    )
)
