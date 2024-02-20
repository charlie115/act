from rest_framework import routers

from infocore.views import AssetViewSet

app_name = "infocore:assets"

router = routers.DefaultRouter()
router.register(r"", AssetViewSet)

urlpatterns = router.urls
