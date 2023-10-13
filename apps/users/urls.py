from rest_framework import routers

from lib.views import BaseEndpointListView
from users.views import (
    UserViewSet,
    UserBlocklistViewSet,
    UserFavoriteAssetsViewSet,
    UserProfileViewSet,
)


class UserAPIListView(BaseEndpointListView):
    """
    List of User APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = UserAPIListView


router = DocumentedRouter()
router.register(r"users", UserViewSet)
router.register(r"blocklist", UserBlocklistViewSet)
router.register(r"favorite-assets", UserFavoriteAssetsViewSet)
router.register(r"profiles", UserProfileViewSet)

urlpatterns = router.urls
