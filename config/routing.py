from channels.routing import URLRouter
from django.urls import path

from infocore.consumers import KlineConsumer
from lib.middleware import TokenAuthMiddleware


websocket_urlpatterns = TokenAuthMiddleware(
    URLRouter(
        [
            path("kline/", KlineConsumer.as_asgi()),
        ]
    )
)
