from django.conf import settings

from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
    UserDetailsView,
)
from dj_rest_auth.jwt_auth import get_refresh_view
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework_simplejwt.views import TokenVerifyView

from authentication.adapters import CustomGoogleOAuth2Adapter


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Google login",
        description="Login via Google.",
    ),
)
class AuthGoogleLoginView(SocialLoginView):
    adapter_class = CustomGoogleOAuth2Adapter
    client_class = OAuth2Client


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Basic login",
        description="Login using `username` and `password`.<br>"
        "*(Only enabled in development mode for easier testing.)*",
    ),
)
class AuthBasicLoginView(LoginView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    get=extend_schema(exclude=True),
    post=extend_schema(
        operation_id="Logout",
        description="Logs out the logged in user.",
    ),
)
class AuthLogoutView(LogoutView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Change password",
        description="Changes current `password`.",
    ),
)
class AuthPasswordChangeView(PasswordChangeView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Reset password",
        description="Resets current `password`/unset `password` to nothing.",
    ),
)
class AuthPasswordResetView(PasswordResetView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Confirm reset password",
        description="Confirms reset of `password`.",
    ),
)
class AuthPasswordResetConfirmView(PasswordResetConfirmView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Refresh token",
        description="Refreshes the `access token`. "
        f"Expiration is also reset back to {settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']}.",
    ),
)
class AuthTokenRefreshView(get_refresh_view()):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Verify token",
        description="Verifies if `access token` is valid.",
    ),
)
class AuthTokenVerifyView(TokenVerifyView):
    pass


@extend_schema(tags=["Auth"])
@extend_schema_view(
    get=extend_schema(
        operation_id="Retrieve details of logged in user",
        description="Retrieves the details of the `logged in user`.",
    ),
    put=extend_schema(
        operation_id="Fully update details of logged in user",
        description="Fully updates all the details of the `logged in user`.<br>"
        "*All the previous details of the `logged in user` will be replaced with the new details provided. "
        "Any parameters not provided will be unset.*",
    ),
    patch=extend_schema(
        operation_id="Update some details of logged in user",
        description="Updates some details of the `logged in user`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
)
class AuthUserDetailsView(UserDetailsView):
    pass
