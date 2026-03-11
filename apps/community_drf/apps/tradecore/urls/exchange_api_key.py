from rest_framework import routers

from tradecore.views import ExchangeApiKeyViewSet

app_name = "tradecore:exchange-api-key"

router = routers.DefaultRouter()
router.register(r"", ExchangeApiKeyViewSet, basename="exchange-api-key")

urlpatterns = router.urls
