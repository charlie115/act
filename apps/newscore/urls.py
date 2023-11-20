from rest_framework import routers

from lib.views import BaseEndpointListView
from newscore.views import AnnouncementViewSet, NewsViewSet, PostViewSet


class NewsCoreAPIListView(BaseEndpointListView):
    """
    List of User APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = NewsCoreAPIListView


router = DocumentedRouter()
router.register(r"announcements", AnnouncementViewSet)
router.register(r"news", NewsViewSet)
router.register(r"posts", PostViewSet)

urlpatterns = router.urls
