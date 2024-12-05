from collections import OrderedDict
from django.urls import include, path
from rest_framework import response
from lib.views import BaseAPIListView
from wallet.views import (
    UserWalletAddressView,
    UserWalletBalanceView,
    UserWalletDepositView,
)


class WalletAPIListView(BaseAPIListView):
    """
    Wallet API endpoints
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


app_name = "wallet"

urlpatterns = [
    path("", WalletAPIListView.as_view(), name="wallet-root"),
    # path(
    #     "user-wallet/",
    #     include("wallet.urls.user_wallet"),
    #     name="user-wallet",
    # ),
    # path(
    #     "user-wallet-balance/",
    #     include("tradecore.urls.trade_config"),
    #     name="trade-config",
    # ),
    path(
        "user-wallet/<uuid:user>/",
        UserWalletAddressView.as_view(),
        name="user-wallet-view",
    ),
    path(
        "user-wallet-balance/<uuid:user>/",
        UserWalletBalanceView.as_view(),
        name="user-wallet-balance-view",
    ),
    path(
        "user-wallet-deposit/",
        UserWalletDepositView.as_view(),
        name="user-wallet-deposit-view",
    ),
]
