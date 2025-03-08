from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from lib.views import UserOwnedViewSet
from fee.models import UserFeeLevel
from fee.serializers import UserFeeLevelSerializer


@extend_schema(tags=["Fee"])
@extend_schema_view(
    list=extend_schema(
        operation_id="List user fee levels",
        description="Returns a list of all `user fee levels`.",
    ),
    retrieve=extend_schema(
        operation_id="Retrieve a user fee level",
        description="Retrieves the details of the authenticated user's `fee level`.",
    ),
)
class UserFeeLevelViewSet(UserOwnedViewSet):
    queryset = UserFeeLevel.objects.all()
    lookup_field = "id"
    serializer_class = UserFeeLevelSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    ordering_fields = [
        "fee_level",
        "total_paid_fee",
        "last_updated_datetime",
    ]
    ordering = ["fee_level"]
    http_method_names = ["get"]  # Read-only endpoint
