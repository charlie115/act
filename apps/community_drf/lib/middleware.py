from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


jwt_auth = JWTAuthentication()


@database_sync_to_async
def get_user_from_jwt(token_key):
    try:
        validated_token = jwt_auth.get_validated_token(token_key)
        user = jwt_auth.get_user(validated_token)
    except InvalidToken:
        user = AnonymousUser()
    return user


class RouteNotFoundMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            return await self.app(scope, receive, send)
        except ValueError as err:
            if "No route found for path" in str(err) and scope["type"] == "websocket":
                await send({"type": "websocket.close"})
                # TODO: Log error
            else:
                raise err


class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])

        scope["user"] = AnonymousUser()
        if b"authorization" in headers:
            token_name, token_key = headers[b"authorization"].decode().split()
            if token_name == "Bearer":
                scope["user"] = await get_user_from_jwt(token_key)

        return await self.app(scope, receive, send)


def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))
