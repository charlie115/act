import hashlib
import hmac
import time

from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialLogin
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.telegram.provider import TelegramProvider
from datetime import datetime, timedelta
from django.conf import settings
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
from rest_framework import exceptions, permissions, response
from rest_framework_simplejwt.views import TokenVerifyView

from lib.datetime import TZ_ASIA_SEOUL
from authentication.adapters import CustomGoogleOAuth2Adapter
from board.models import UserLevels
from socialaccounts.models import ProxySocialAccount
from users.models import User, UserRole, UserSocialApps, UserAuthLog
from users.serializers import UserSerializer


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
    http_method_names = ["post"]

    def process_login(self):
        super().process_login()

        # Log
        UserAuthLog.objects.create(user=self.user, endpoint="/login/")

        # Check if User has logged in today and add points to community_level
        today = datetime.now(tz=TZ_ASIA_SEOUL)
        today_start = today.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )
        today_end = today.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=timedelta.max.microseconds,
        )

        auth_logs_today = UserAuthLog.objects.filter(
            user=self.user,
            endpoint="/login/",
            date_logged__gte=today_start,
            date_logged__lte=today_end,
        )
        if len(auth_logs_today) == 1:  # first login
            UserLevels().update_level(user=self.user, points=UserLevels.LOGIN_POINTS)


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Link Telegram account",
        description="Login via Telegram",
    ),
)
class AuthTelegramLoginView(LoginView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ["post"]

    def post(self, request, *args, **kwargs):
        if "user" not in request.data:
            raise exceptions.ValidationError({"user": ["This field is required."]})

        # allauth/socialaccount/providers/telegram/views.py
        telegram_provider = providers.registry.by_id(TelegramProvider.id, request)

        data = dict(request.data.items())
        hash = data.pop("hash", None)
        uuid = data.pop("user", None)

        if not hash or not uuid:
            raise exceptions.ValidationError(
                {"detail": "hash and user fields are required."}
            )

        try:
            user = User.objects.get(uuid=uuid)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"user": ["User not found."]})

        payload = "\n".join(sorted(["{}={}".format(k, v) for k, v in data.items()]))

        # Get user's social app to get Telegram bot token
        try:
            user_telegram_socialapp = user.socialapps.get(
                socialapp__provider=telegram_provider.id
            )

        except UserSocialApps.DoesNotExist:
            raise exceptions.ValidationError(
                {"detail": "User has no telegram bot allocated yet."}
            )

        token = user_telegram_socialapp.socialapp.secret
        token_sha256 = hashlib.sha256(token.encode()).digest()
        expected_hash = hmac.new(
            token_sha256, payload.encode(), hashlib.sha256
        ).hexdigest()

        auth_date_raw = data.pop("auth_date", None)
        if auth_date_raw is None:
            raise exceptions.ValidationError(
                {"auth_date": ["This field is required."]}
            )

        try:
            auth_date = int(auth_date_raw)
        except (ValueError, TypeError):
            raise exceptions.ValidationError(
                {"auth_date": ["Must be a valid integer timestamp."]}
            )

        if not hmac.compare_digest(hash, expected_hash) or time.time() - auth_date > 30:
            raise exceptions.ValidationError({"detail": "Telegram data is not valid."})

        # allauth/socialaccount/providers/base/provider.py: sociallogin_from_response
        uid = telegram_provider.extract_uid(data)
        extra_data = telegram_provider.extract_extra_data(data)

        socialaccount = ProxySocialAccount(
            user=user,
            extra_data=extra_data,
            uid=uid,
            provider=telegram_provider.id,
        )
        sociallogin = SocialLogin(account=socialaccount, email_addresses=[])

        telegram_socialaccount = user.socialaccount_set.filter(
            provider=telegram_provider.id
        )
        if telegram_socialaccount:
            response_data = {"detail": "Telegram account already connected."}
        else:
            sociallogin.connect(request, user)
            user.telegram_chat_id = uid
            user.save()
            response_data = {"detail": "Telegram account successfully connected!"}

        return response.Response(response_data)

    def process_login(self):
        super().process_login()

        # Log
        UserAuthLog.objects.create(user=self.user, endpoint="/login/telegram/")


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Basic login",
        description="Login using `username` and `password`.<br>"
        "*(Only enabled in development mode for easier testing.)*",
    ),
)
class AuthBasicLoginView(LoginView):
    http_method_names = ["post"]

    def process_login(self):
        super().process_login()

        # Log
        UserAuthLog.objects.create(user=self.user, endpoint="/login/basic/")


@extend_schema(tags=["Auth"])
@extend_schema_view(
    get=extend_schema(exclude=True),
    post=extend_schema(
        operation_id="Logout",
        description="Logs out the logged in user.",
    ),
)
class AuthLogoutView(LogoutView):
    http_method_names = ["post"]


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Change password",
        description="Changes current `password`.",
    ),
)
class AuthPasswordChangeView(PasswordChangeView):
    http_method_names = ["post"]


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Reset password",
        description="Resets current `password`/unset `password` to nothing.",
    ),
)
class AuthPasswordResetView(PasswordResetView):
    http_method_names = ["post"]


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Confirm reset password",
        description="Confirms reset of `password`.",
    ),
)
class AuthPasswordResetConfirmView(PasswordResetConfirmView):
    http_method_names = ["post"]


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Refresh token",
        description="Refreshes the `access token`. "
        f"Expiration is also reset back to {settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']}.",
    ),
)
class AuthTokenRefreshView(get_refresh_view()):
    http_method_names = ["post"]


@extend_schema(tags=["Auth"])
@extend_schema_view(
    post=extend_schema(
        operation_id="Verify token",
        description="Verifies if `access token` is valid.",
    ),
)
class AuthTokenVerifyView(TokenVerifyView):
    http_method_names = ["post"]


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
    http_method_names = ["get", "put", "patch"]

    def partial_update(self, request, *args, **kwargs):
        telegram_bot = request.data.pop("telegram_bot", None)
        if telegram_bot:
            user_telegram_socialapps = self.request.user.socialapps.filter(
                socialapp__provider="telegram"
            )
            if len(user_telegram_socialapps) < 1:
                telegram_socialapps = UserSerializer()._get_telegram_bots()
                if len(telegram_socialapps) > 0:
                    UserSocialApps.objects.create(
                        socialapp=telegram_socialapps.first(),
                        user=self.request.user,
                    )
                else:
                    raise exceptions.ValidationError(
                        {"detail": "There is no telegram socialapp to allocate."}
                    )
            else:
                raise exceptions.ValidationError(
                    {"detail": "A telegram bot is already allocated to the user."}
                )

        return super().partial_update(request, *args, **kwargs)


@extend_schema(tags=["Auth"])
@extend_schema_view(
    patch=extend_schema(
        operation_id="Register the logged in user",
        description="Reigster the `logged in user`.<br>"
        "*User registration info is saved and the user's role finally becomes VISITOR → **USER**.*",
    ),
)
class AuthUserRegisterView(UserDetailsView):
    http_method_names = ["patch"]

    def perform_update(self, serializer):
        new_username = serializer.validated_data.get("username")

        if (
            new_username is not None
            and serializer.instance.username != new_username
            and not new_username.startswith("@")
            and new_username[0].isalpha()
        ):
            serializer.instance.role = UserRole.objects.get(name=UserRole.USER)

        serializer.save()
