import importlib
import os

from django.apps import apps
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework.response import Response

from lib.views import BaseAPIListView
from lib.url import mkpath

class APIListView(BaseAPIListView):
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
    path(mkpath(""), APIListView.as_view(), name="api-root"),
    path(mkpath("admin/"), admin.site.urls),
    path(mkpath("auth/"), include("authentication.urls")),
    path(mkpath("board/"), include("board.urls")),
    path(mkpath("chat/"), include("chat.urls")),
    path(mkpath("referral/"), include("referral.urls.urls")),
    path(mkpath("users/"), include("users.urls")),
    path(mkpath("infocore/"), include("infocore.urls.urls")),
    path(mkpath("messagecore/"), include("messagecore.urls")),
    path(mkpath("newscore/"), include("newscore.urls")),
    path(mkpath("tradecore/"), include("tradecore.urls.urls")),
    path(mkpath("wallet/"), include("wallet.urls.urls")),
    path(mkpath("coupon/"), include("coupon.urls")),
    path(mkpath("exchange-status/"), include("exchangestatus.urls")),
    # redis queue
    path(mkpath("django-rq/"), include("django_rq.urls")),
    # docs
    path(
        mkpath("docs/"),
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path(
        mkpath("schema/"),
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        mkpath("swagger/"),
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger",
    ),
]

if os.environ["DJANGO_SETTINGS_MODULE"] == "config.settings.dev":
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
