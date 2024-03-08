from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination


from lib.views import BaseViewSet
from referral.models import Referral, ReferralCode
from referral.serializers import ReferralSerializer, ReferralCodeSerializer


@extend_schema(tags=["Referral"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List referrals",
        description="Returns a list of all `referrals`.",
    ),
    create=extend_schema(
        operation_id="Create a referral",
        description="Creates a new `referral`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a referral",
        description="Retrieves the details of an existing `referral`.",
    ),
    update=extend_schema(
        operation_id="Fully update a referral",
        description="Fully updates an existing `referral`.<br>"
        "*All the previous values of the `referral` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a referral",
        description="Updates an existing `referral`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a referral",
        description="Deletes an existing `referral`.",
    ),
)
class ReferralViewSet(BaseViewSet):
    queryset = Referral.objects.all()
    serializer_class = ReferralSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "referred_user",
        "referral_code",
        "registered_datetime",
    )
    ordering_fields = ["id", "referral_code", "registered_datetime"]
    ordering = ["id"]
    http_method_names = ["get", "post", "put", "patch", "delete"]
    pagination_class = PageNumberPagination


@extend_schema(tags=["ReferralCode"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List referral codes",
        description="Returns a list of all `referral codes`.",
    ),
    create=extend_schema(
        operation_id="Create a referral code",
        description="Creates a new `referral code`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a referral code",
        description="Retrieves the details of an existing `referral code`.",
    ),
    update=extend_schema(
        operation_id="Fully update a referral code",
        description="Fully updates an existing `referral code`.<br>"
        "*All the previous values of the `referral code` will be replaced with the new values provided. "
        "Any parameters not provided will be unset.*",
    ),
    partial_update=extend_schema(
        operation_id="Update a referral code",
        description="Updates an existing `referral code`.<br>"
        "*Only the parameters specified will be updated while the rest will be left unchanged.*",
    ),
    destroy=extend_schema(
        operation_id="Delete a referral code",
        description="Deletes an existing `referral code`.",
    ),
)
class ReferralCodeViewSet(BaseViewSet):
    queryset = ReferralCode.objects.all()
    serializer_class = ReferralCodeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = (
        "user",
        "referral_group",
        "code",
        "target_market_code",
        "origin_market_code",
        "max_depth",
        "contact",
    )
    ordering_fields = ["id", "code"]
    ordering = ["id"]
    http_method_names = ["get"]
    pagination_class = PageNumberPagination
