from rest_framework import routers

from tradecore.views import NodeViewSet

app_name = "tradecore:nodes"

router = routers.DefaultRouter()
router.register(r"", NodeViewSet)

urlpatterns = router.urls
