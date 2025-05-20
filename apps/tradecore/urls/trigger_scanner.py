from django.urls import path
from rest_framework.routers import DefaultRouter

from tradecore.views import TriggerScannerViewSet

app_name = "tradecore:trigger-scanner"
router = DefaultRouter()
router.register("", TriggerScannerViewSet, basename="trigger-scanner")

urlpatterns = router.urls 