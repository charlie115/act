from rest_framework import routers

from lib.views import BaseAPIListView
from messagecore.views import MessageViewSet


class MessageCoreAPIListView(BaseAPIListView):
    """
    List of MessageCore APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = MessageCoreAPIListView
    root_view_name = "messagecore-root"


app_name = "messagecore"

router = DocumentedRouter()
router.register(r"messages", MessageViewSet)

urlpatterns = router.urls
