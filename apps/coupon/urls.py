from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CouponViewSet, CouponRedemptionViewSet

router = DefaultRouter()
router.register('coupons', CouponViewSet, basename='coupon')
router.register('coupon-redemption', CouponRedemptionViewSet, basename='coupon-redemption')

urlpatterns = [
    # ... other urls
    path('', include(router.urls)),
]