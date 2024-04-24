from rest_framework import routers

from tradecore.views import RepeatTradesViewSet

app_name = "tradecore:repeat-trades"

router = routers.DefaultRouter()
router.register(r"", RepeatTradesViewSet, basename="repeat-trades")

urlpatterns = router.urls
