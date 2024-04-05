from rest_framework import routers

from tradecore.views import TradeConfigViewSet

app_name = "tradecore:trade-config"

router = routers.DefaultRouter()
router.register(r"", TradeConfigViewSet, basename="trade-config")

urlpatterns = router.urls
