from rest_framework import routers

from arbot.views import ArbotNodeViewSet, ArbotUserConfigViewSet


class ArbotAPIListView(routers.APIRootView):
    """
    Arbot API endpoints
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = ArbotAPIListView


router = DocumentedRouter()
router.register(r"nodes", ArbotNodeViewSet)
router.register(r"user-configs", ArbotUserConfigViewSet)

urlpatterns = router.urls
