from channels.routing import URLRouter
from django.urls import path

from infocore.consumers import CoinConsumer
from lib.middleware import TokenAuthMiddleware


websocket_urlpatterns = TokenAuthMiddleware(
    URLRouter(
        [
            path("coins/", CoinConsumer.as_asgi()),
        ]
    )
)
