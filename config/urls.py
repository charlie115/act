import importlib
import os

from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import routers
from rest_framework.response import Response

from lib.permissions import IsDjangoAdmin, IsACWAdmin


class EndpointListView(routers.APIRootView):
    """
    List of all endpoints
    """

    http_method_names = ["get"]
    permission_classes = [IsDjangoAdmin or IsACWAdmin]

    def get(self, request, *args, **kwargs):
        api_list = {
            "admin": request.build_absolute_uri("admin/"),
            "docs": request.build_absolute_uri("docs/"),
        }

        for name, app in apps.app_configs.items():
            if name in settings.LOCAL_APPS:
                if importlib.util.find_spec(f"apps.{name}.urls"):
                    name = "auth" if name == "authentication" else name
                    api_list[name] = request.build_absolute_uri(os.path.join(name, ""))

        return Response(api_list)


urlpatterns = [
    path("", EndpointListView.as_view(), name="endpoint list"),
    path("admin/", admin.site.urls),
    path("auth/", include("authentication.urls"), name="authentication urls"),
    path("arbot/", include("arbot.urls"), name="arbot urls"),
    path("docs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
    path("users/", include("users.urls"), name="users urls"),
]
