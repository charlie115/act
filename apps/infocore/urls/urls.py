from collections import OrderedDict
from django.urls import include, path
from rest_framework import response, routers
from urllib.parse import urljoin

from infocore.views import (
    DollarView,
    USDTView,
    MarketCodesView,
    KlineDataView,
    KlineVolatilityView,
    WalletStatusView,
    RankIndicatorView,
    AiRankRecommendationView,
    VolatilityNotificationConfigViewSet,
)
from lib.views import BaseAPIListView


# Router for ViewSets
router = routers.DefaultRouter()
router.register(
    r"volatility-notifications",
    VolatilityNotificationConfigViewSet,
    basename="volatility-notifications",
)


class InfoCoreAPIListView(BaseAPIListView):
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


app_name = "infocore"

urlpatterns = [
    path("", InfoCoreAPIListView.as_view(), name="infocore-root"),
    path("assets/", include("infocore.urls.assets"), name="assets"),
    path("dollar/", DollarView.as_view(), name="dollar-view"),
    path("usdt/", USDTView.as_view(), name="usdt-view"),
    path(
        "funding-rate/",
        include("infocore.urls.funding_rate"),
        name="funding-rate",
    ),
    path("kline/", KlineDataView.as_view(), name="kline-view"),
    path(
        "kline-volatility/", KlineVolatilityView.as_view(), name="kline-volatility-view"
    ),
    path("market-codes/", MarketCodesView.as_view(), name="market-codes-view"),
    path("wallet-status/", WalletStatusView.as_view(), name="wallet-status-view"),
    path(
        "rank-indicator/",
        RankIndicatorView.as_view(),
        name="rank-indicator",
    ),
    path(
        "ai-rank-recommendation/",
        AiRankRecommendationView.as_view(),
        name="ai-rank-recommendation",
    ),
    # Volatility notification configs (ViewSet with router)
    path("", include(router.urls)),
]
