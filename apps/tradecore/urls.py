from rest_framework import routers

from tradecore.views import (
    NodeViewSet,
    TradeConfigViewSet,
    TradesViewSet,
)
from lib.views import BaseEndpointListView


class TradeCoreAPIListView(BaseEndpointListView):
    """
    Trade Core API endpoints
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = TradeCoreAPIListView


router = DocumentedRouter()
router.register(r"nodes", NodeViewSet)
router.register(r"trade-config", TradeConfigViewSet, basename="trade-config")
router.register(r"trades", TradesViewSet, basename="trades")

urlpatterns = router.urls
