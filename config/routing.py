from channels.routing import URLRouter
from django.urls import path

from infocore.consumers import KlineConsumer
from lib.middleware import TokenAuthMiddleware, RouteNotFoundMiddleware


websocket_urlpatterns = TokenAuthMiddleware(
    RouteNotFoundMiddleware(
        URLRouter(
            [
                path("kline/", KlineConsumer.as_asgi()),
            ]
        )
    )
)
