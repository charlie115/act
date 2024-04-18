from rest_framework import routers

from tradecore.views import TradeLogViewSet

app_name = "tradecore:trade-log"

router = routers.DefaultRouter()
router.register(r"", TradeLogViewSet, basename="trade-log")

urlpatterns = router.urls
