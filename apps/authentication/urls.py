import os

from django.urls import path
from dj_rest_auth.urls import urlpatterns as dj_rest_auth_urls
from rest_framework import response, routers

from authentication.views import (
    AuthGoogleLoginView,
    AuthBasicLoginView,
    AuthLogoutView,
    AuthPasswordChangeView,
    AuthPasswordResetConfirmView,
    AuthPasswordResetView,
    AuthTokenRefreshView,
    AuthTokenVerifyView,
    AuthUserDetailsView,
)


class AuthAPIListView(routers.APIRootView):
    """
    Authentication API endpoints
    """

    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        api_list = {
            str(url.pattern).strip("/"): request.build_absolute_uri(url.pattern)
            for url in dj_rest_auth_urls
        }
        if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
            api_list["login/basic"] = request.build_absolute_uri("login/basic/")

        api_list = dict(sorted(api_list.items()))

        return response.Response(api_list)


urlpatterns = [
    path("", AuthAPIListView.as_view(), name="auth api list"),
    path("login/", AuthGoogleLoginView.as_view(), name="google login"),
    path("logout/", AuthLogoutView.as_view(), name="logout"),
    path("password/change/", AuthPasswordChangeView.as_view(), name="password change"),
    path("password/reset/", AuthPasswordResetView.as_view(), name="password reset"),
    path(
        "password/reset/confirm/",
        AuthPasswordResetConfirmView.as_view(),
        name="password reset confirm",
    ),
    path("token/refresh/", AuthTokenRefreshView.as_view(), name="token refresh"),
    path("token/verify/", AuthTokenVerifyView.as_view(), name="token verify"),
    path("user/", AuthUserDetailsView.as_view(), name="logged in user"),
]

if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
    urlpatterns += [
        path("login/basic/", AuthBasicLoginView.as_view(), name="basic login"),
    ]
