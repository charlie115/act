from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import ExchangeServerStatusViewSet

router = DefaultRouter()
router.register('server-status', ExchangeServerStatusViewSet, basename='server-status')

urlpatterns = [
    # ... other urls
    path('', include(router.urls)),
]