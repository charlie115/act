from collections import OrderedDict
from django.urls import include, path
from rest_framework import response


from lib.views import BaseAPIListView
from tradecore.views import (
    CapitalView,
    SpotPositionView,
    FuturesPositionView,
    PboundaryView,
    DepositAddressView,
    ExitTradeView,
)


class TradeCoreAPIListView(BaseAPIListView):
    """
    Trade Core API endpoints
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


app_name = "tradecore"

urlpatterns = [
    path("", TradeCoreAPIListView.as_view(), name="tradecore-root"),
    path(
        "nodes/",
        include("tradecore.urls.nodes"),
        name="nodes",
    ),
    path(
        "trade-config/",
        include("tradecore.urls.trade_config"),
        name="trade-config",
    ),
    path(
        "trades/",
        include("tradecore.urls.trades"),
        name="trades",
    ),
    path(
        "repeat-trades/",
        include("tradecore.urls.repeat_trades"),
        name="repeat-trades",
    ),
    path(
        "trade-log/",
        include("tradecore.urls.trade_log"),
        name="trade-log",
    ),
    path(
        "exchange-api-key/",
        include("tradecore.urls.exchange_api_key"),
        name="funding-rate",
    ),
    path(
        "capital/",
        CapitalView.as_view(),
        name="capital-view",
    ),
    path(
        "spot-position/",
        SpotPositionView.as_view(),
        name="spot-position-view",
    ),
    path(
        "futures-position/",
        FuturesPositionView.as_view(),
        name="futures-position-view",
    ),
    path(
        "order-history/",
        include("tradecore.urls.order_history"),
        name="order-history",
    ),
    path(
        "trade-history/",
        include("tradecore.urls.trade_history"),
        name="trade-history",
    ),
    path(
        "pnl-history/",
        include("tradecore.urls.pnl_history"),
        name="pnl-history",
    ),
    path(
        "pboundary/",
        PboundaryView.as_view(),
        name="pboundary-view",
    ),
    path(
        "deposit-address/",
        DepositAddressView.as_view(),
        name="deposit-address-view",
    ),
    path(
        "exit-trade/",
        ExitTradeView.as_view(),
        name="exit-trade-view",
    ),
    path(
        "deposit-amount/",
        include("tradecore.urls.deposit_amount"),
        name="deposit-amount",
    ),
]
