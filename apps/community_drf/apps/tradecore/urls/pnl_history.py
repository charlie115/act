from rest_framework import routers

from tradecore.views import PNLHistoryViewSet

app_name = "tradecore:pnl-history"

router = routers.DefaultRouter()
router.register(r"", PNLHistoryViewSet, basename="pnl-history")

urlpatterns = router.urls
