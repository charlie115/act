from rest_framework import routers

from tradecore.views import TradeHistoryViewSet

app_name = "tradecore:trade-history"

router = routers.DefaultRouter()
router.register(r"", TradeHistoryViewSet, basename="trade-history")

urlpatterns = router.urls
