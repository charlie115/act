from collections import OrderedDict
from django.urls import include, path
from rest_framework import response
from urllib.parse import urljoin

from infocore.views import (
    KlineDataView,
    MarketCodesView,
)
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

                if name == "funding-rate":
                    for inner_url in url.url_patterns:
                        inner_endpoint = urljoin(endpoint, str(inner_url.pattern))
                        inner_name = inner_endpoint.strip("/")

                        if inner_name != "":
                            api_list.append(
                                (
                                    inner_name,
                                    request.build_absolute_uri(inner_endpoint),
                                )
                            )

        api_list = OrderedDict(api_list)

        return response.Response(api_list)


urlpatterns = [
    path("", InfoCoreAPIListView.as_view(), name="infocore api list"),
    path("assets/", include("infocore.urls.assets"), name="assets urls"),
    path(
        "funding-rate/",
        include("infocore.urls.funding_rate"),
        name="funding rate urls",
    ),
    path("kline/", KlineDataView.as_view(), name="kline data"),
    path("market-codes/", MarketCodesView.as_view(), name="market codes"),
]
