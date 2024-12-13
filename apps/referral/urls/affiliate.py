from rest_framework import routers

from referral.views import AffiliateViewSet

app_name = "referral:affiliate"

router = routers.DefaultRouter()
router.register(r"", AffiliateViewSet)

urlpatterns = router.urls
