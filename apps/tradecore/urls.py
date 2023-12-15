from rest_framework import routers

from tradecore.views import NodeViewSet, UserConfigViewSet
from lib.views import BaseEndpointListView


class TradeCoreAPIListView(BaseEndpointListView):
    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = TradeCoreAPIListView


router = DocumentedRouter()
router.register(r"nodes", NodeViewSet)
router.register(r"user-configs", UserConfigViewSet)

urlpatterns = router.urls
