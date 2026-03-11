from rest_framework import routers

from tradecore.views import OrderHistoryViewSet

app_name = "tradecore:order-history"

router = routers.DefaultRouter()
router.register(r"", OrderHistoryViewSet, basename="order-history")

urlpatterns = router.urls
