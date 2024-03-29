from rest_framework import routers

from referral.views import ReferralCodeViewSet

app_name = "referral:referral-code"

router = routers.DefaultRouter()
router.register(r"", ReferralCodeViewSet)

urlpatterns = router.urls
