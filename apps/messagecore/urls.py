from rest_framework import routers

from lib.views import BaseEndpointListView
from messagecore.views import MessageViewSet


class MessageCoreAPIListView(BaseEndpointListView):
    """
    List of MessageCore APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = MessageCoreAPIListView


router = DocumentedRouter()
router.register(r"messages", MessageViewSet)

urlpatterns = router.urls
