from channels.routing import URLRouter
from django.urls import path

from chat.consumers import ChatConsumer
from infocore.consumers import KlineConsumer
from lib.middleware import TokenAuthMiddleware, RouteNotFoundMiddleware
from lib.url import mkpath


websocket_urlpatterns = TokenAuthMiddleware(
    RouteNotFoundMiddleware(
        URLRouter(
            [
                path(mkpath("kline/"), KlineConsumer.as_asgi()),
                path(mkpath("chat/"), ChatConsumer.as_asgi()),
            ]
        )
    )
)
