from collections import OrderedDict
from django.urls import path
from rest_framework import response

from infocore.views import InfoCoreHistoricalCoinDataView
from lib.views import BaseEndpointListView


class InfoCoreAPIListView(BaseEndpointListView):
    """
    Info Core API endpoints
    """

    def get(self, request, *args, **kwargs):
        api_list = []

        for url in urlpatterns:
            endpoint = str(url.pattern)
            name = endpoint.strip("/")
            if name != "":
                api_list.append(
                    (
                        name,
                        request.build_absolute_uri(endpoint),
                    )
                )

        api_list = OrderedDict(api_list)

        return response.Response(api_list)


urlpatterns = [
    path("", InfoCoreAPIListView.as_view(), name="infocore api list"),
    path(
        "coins/", InfoCoreHistoricalCoinDataView.as_view(), name="historical coin data"
    ),
]
