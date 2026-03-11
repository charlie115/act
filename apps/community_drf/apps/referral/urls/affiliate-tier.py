from rest_framework import routers

from referral.views import AffiliateTierViewSet

app_name = "referral:affiliate-tier"

router = routers.DefaultRouter()
router.register(r"", AffiliateTierViewSet)

urlpatterns = router.urls
