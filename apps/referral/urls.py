from rest_framework import routers

from lib.views import BaseAPIListView
from referral.views import ReferralViewSet, ReferralCodeViewSet


class ReferralAPIListView(BaseAPIListView):
    """
    List of Referral APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = ReferralAPIListView
    root_view_name = "referral-root"


app_name = "referral"

router = DocumentedRouter()
router.register(r"referrals", ReferralViewSet)
router.register(r"referral-code", ReferralCodeViewSet)

urlpatterns = router.urls
