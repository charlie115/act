from collections import OrderedDict
from django.urls import path
from rest_framework import routers
from rest_framework.response import Response

from arbot.views import (
    ArbotNodeViewSet,
    ArbotUserConfigViewSet,
    ArbotHistoricalCoinDataView,
)
from lib.views import BaseEndpointListView


class ArbotAPIListView(BaseEndpointListView):
    """
    Arbot API endpoints
    """

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        api_list = OrderedDict(
            [
                ("coins", request.build_absolute_uri("coins/")),
            ]
        )
        api_list.update(response.data)

        return Response(api_list)


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = ArbotAPIListView


router = DocumentedRouter()
router.register(r"nodes", ArbotNodeViewSet)
router.register(r"user-configs", ArbotUserConfigViewSet)

urlpatterns = [
    path("coins/", ArbotHistoricalCoinDataView.as_view(), name="historical coin data"),
]

urlpatterns += router.urls
