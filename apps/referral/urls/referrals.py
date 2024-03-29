from rest_framework import routers

from referral.views import ReferralViewSet

app_name = "referral:referrals"

router = routers.DefaultRouter()
router.register(r"", ReferralViewSet)

urlpatterns = router.urls
