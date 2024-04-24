from rest_framework import routers

from tradecore.views import TradesViewSet

app_name = "tradecore:trades"

router = routers.DefaultRouter()
router.register(r"", TradesViewSet, basename="trades")

urlpatterns = router.urls
