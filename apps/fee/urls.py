from rest_framework import routers

from lib.views import BaseAPIListView
from fee.views import UserFeeLevelViewSet


class FeeAPIListView(BaseAPIListView):
    """
    List of Fee APIs
    """
    pass


class DocumentedRouter(routers.DefaultRouter):
    APIRootView = FeeAPIListView
    root_view_name = "fee-root"


app_name = "fee"

router = DocumentedRouter()
router.register(r"user-feelevel", UserFeeLevelViewSet)

urlpatterns = router.urls