from rest_framework import routers

from users.views import UserViewSet, UserFavoriteSymbolsViewSet, UserProfileViewSet


class UserAPIListView(routers.APIRootView):
    """
    List of User APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = UserAPIListView


router = DocumentedRouter()
router.register(r"users", UserViewSet)
router.register(r"favorite-symbols", UserFavoriteSymbolsViewSet)
router.register(r"profiles", UserProfileViewSet)

urlpatterns = router.urls
