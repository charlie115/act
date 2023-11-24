from rest_framework import routers

from infocore.views import AssetViewSet

router = routers.DefaultRouter()
router.register(r"", AssetViewSet)

urlpatterns = router.urls
