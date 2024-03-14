from rest_framework import routers

from lib.views import BaseAPIListView
from tradecore.views import (
    NodeViewSet,
    TradeConfigViewSet,
    TradesViewSet,
    ExchangeApiKeyViewSet,
)


class TradeCoreAPIListView(BaseAPIListView):
    """
    Trade Core API endpoints
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = TradeCoreAPIListView
    root_view_name = "tradecore-root"


app_name = "tradecore"

router = DocumentedRouter()
router.register(r"nodes", NodeViewSet)
router.register(r"trade-config", TradeConfigViewSet, basename="trade-config")
router.register(r"trades", TradesViewSet, basename="trades")
router.register(r"exchange-api-key", ExchangeApiKeyViewSet, basename="exchange-api-key")

urlpatterns = router.urls
