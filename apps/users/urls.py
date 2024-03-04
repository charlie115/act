from rest_framework import routers

from lib.views import BaseAPIListView
from users.views import (
    UserViewSet,
    UserBlocklistViewSet,
    UserFavoriteAssetsViewSet,
    UserProfileViewSet,
    DepositBalanceViewSet,
    DepositHistoryViewSet,
)


class UserAPIListView(BaseAPIListView):
    """
    List of User APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = UserAPIListView
    root_view_name = "users-root"


app_name = "users"

router = DocumentedRouter()
router.register(r"users", UserViewSet)
router.register(r"blocklist", UserBlocklistViewSet)
router.register(r"favorite-assets", UserFavoriteAssetsViewSet)
router.register(r"profiles", UserProfileViewSet)
router.register(r"deposit-balance", DepositBalanceViewSet)
router.register(r"deposit-history", DepositHistoryViewSet)

urlpatterns = router.urls
