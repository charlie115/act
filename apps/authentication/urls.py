import os

from django.urls import include, path
from dj_rest_auth.urls import urlpatterns as dj_rest_auth_urls
from dj_rest_auth.views import LoginView
from rest_framework import response, routers

from authentication.views import GoogleLogin


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
    path("login/", GoogleLogin.as_view(), name="google login"),
    path("", include("dj_rest_auth.urls")),
]

if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
    urlpatterns += [
        path("login/basic/", LoginView.as_view(), name="basic login"),
    ]
