from rest_framework import routers

from referral.views import AffiliateRequestViewSet

app_name = "referral:affiliate-request"

router = routers.DefaultRouter()
router.register(r"", AffiliateRequestViewSet)

urlpatterns = router.urls
