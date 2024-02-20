import os

from django.urls import path
from dj_rest_auth.urls import urlpatterns as dj_rest_auth_urls
from rest_framework import response

from authentication.views import (
    AuthGoogleLoginView,
    AuthTelegramLoginView,
    AuthBasicLoginView,
    AuthLogoutView,
    AuthPasswordChangeView,
    AuthPasswordResetConfirmView,
    AuthPasswordResetView,
    AuthTokenRefreshView,
    AuthTokenVerifyView,
    AuthUserDetailsView,
    AuthUserRegisterView,
)
from lib.views import BaseAPIListView


class AuthAPIListView(BaseAPIListView):
    """
    Authentication API endpoints
    """

    def get(self, request, *args, **kwargs):
        api_list = {
            str(url.pattern).strip("/"): request.build_absolute_uri(url.pattern)
            for url in dj_rest_auth_urls
        }
        api_list["login/telegram"] = request.build_absolute_uri("login/telegram/")

        if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
            api_list["login/basic"] = request.build_absolute_uri("login/basic/")

        api_list = dict(sorted(api_list.items()))

        return response.Response(api_list)


app_name = "authentication"

urlpatterns = [
    path("", AuthAPIListView.as_view(), name="auth-root"),
    path("login/", AuthGoogleLoginView.as_view(), name="login-view"),
    path(
        "login/telegram/",
        AuthTelegramLoginView.as_view(),
        name="login-telegram-view",
    ),
    path("logout/", AuthLogoutView.as_view(), name="logout-view"),
    path(
        "password/change/",
        AuthPasswordChangeView.as_view(),
        name="password-change-view",
    ),
    path(
        "password/reset/",
        AuthPasswordResetView.as_view(),
        name="password-reset-view",
    ),
    path(
        "password/reset/confirm/",
        AuthPasswordResetConfirmView.as_view(),
        name="password-reset-confirm-view",
    ),
    path("token/refresh/", AuthTokenRefreshView.as_view(), name="token-refresh-view"),
    path("token/verify/", AuthTokenVerifyView.as_view(), name="token-verify-view"),
    path("user/", AuthUserDetailsView.as_view(), name="user-view"),
    path("user/register/", AuthUserRegisterView.as_view(), name="user-register-view"),
]

if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
    urlpatterns += [
        path("login/basic/", AuthBasicLoginView.as_view(), name="login-basic-view"),
    ]
