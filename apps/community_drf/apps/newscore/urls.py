from rest_framework import routers

from lib.views import BaseAPIListView
from newscore.views import AnnouncementViewSet, NewsViewSet, PostViewSet


class NewsCoreAPIListView(BaseAPIListView):
    """
    List of NewsCore APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = NewsCoreAPIListView
    root_view_name = "newscore-root"


app_name = "newscore"

router = DocumentedRouter()
router.register(r"announcements", AnnouncementViewSet)
router.register(r"news", NewsViewSet)
router.register(r"posts", PostViewSet)

urlpatterns = router.urls
