from rest_framework import routers

from lib.views import BaseEndpointListView
from news.views import NewsViewSet


class NewsCoreAPIListView(BaseEndpointListView):
    """
    List of User APIs
    """

    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = NewsCoreAPIListView


router = DocumentedRouter()
router.register(r"news", NewsViewSet)

urlpatterns = router.urls
