from django.db import IntegrityError, transaction
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiTypes,
    OpenApiExample
)
from lib.views import BaseViewSet
from users.models import DepositHistory

from .models import Coupon, CouponRedemption
from .serializers import CouponSerializer, RedeemCouponSerializer, CouponRedemptionSerializer

@extend_schema_view(
    list=extend_schema(
        operation_id="List Coupons",
        description="Retrieve a list of all active coupons.",
        responses={200: CouponSerializer(many=True)},
        tags=["Coupon"]
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a single coupon",
        description="Retrieve details of a single coupon by its ID.",
        responses={200: CouponSerializer},
        tags=["Coupon"]
    ),
)
class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Show the list of available coupons.
    """
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    http_method_names = ['get']
    
    def get_queryset(self):
        # filter only is_active true
        return self.queryset.filter(is_active=True)

@extend_schema_view(
    redeem=extend_schema(
        operation_id="Redeem a Coupon",
        description="Redeem a coupon by providing its name.",
        request=RedeemCouponSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT
        },
        examples=[
            OpenApiExample(
                name="Redeem Welcome Coupon",
                value={"name": "Welcome Coupon"},
                summary="An example showing how to redeem a coupon by its name."
            )
        ],
        tags=["CouponRedemption"]
    )
)
class CouponRedemptionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A viewset for users to redeem a coupon.
    """
    queryset = CouponRedemption.objects.all()
    serializer_class = CouponRedemptionSerializer
    
    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='redeem')
    def redeem(self, request):
        serializer = RedeemCouponSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        coupon = serializer.validated_data['coupon']
        user = request.user

        try:
            with transaction.atomic():
                # Lock the coupon row to prevent concurrent redemptions
                coupon = Coupon.objects.select_for_update().get(pk=coupon.pk)

                # Re-check validity inside the lock to prevent TOCTOU race
                if not coupon.is_active:
                    return Response({
                        "error": "COUPON_INACTIVE",
                        "message": "This coupon is no longer active.",
                    }, status=status.HTTP_400_BAD_REQUEST)
                if coupon.is_expired():
                    return Response({
                        "error": "COUPON_EXPIRED",
                        "message": "This coupon has expired.",
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Create a redemption record (unique_together constraint prevents duplicates)
                CouponRedemption.objects.create(user=user, coupon=coupon)

                # Here we record a deposit indicating the user received credit from the coupon.
                DepositHistory.objects.create(
                    user=user,
                    change=coupon.amount,
                    type=DepositHistory.COUPON,
                    coupon=coupon,
                )
        except IntegrityError:
            return Response({
                "error": "COUPON_ALREADY_REDEEMED",
                "message": "You have already redeemed this coupon.",
            }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": "Coupon redeemed successfully.",
            "amount": str(coupon.amount),
        }, status=status.HTTP_200_OK)