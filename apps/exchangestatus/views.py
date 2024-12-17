from rest_framework.viewsets import ReadOnlyModelViewSet
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import ExchangeServerStatus
from .serializers import ExchangeServerStatusSerializer

@extend_schema_view(
    list=extend_schema(
        operation_id="List Exchange Server Statuses",
        description="Retrieve a list of all current exchange server status records.",
        responses={200: ExchangeServerStatusSerializer(many=True)},
        tags=["ExchangeServerStatus"]
    ),
    retrieve=extend_schema(
        operation_id="Retrieve Exchange Server Status",
        description="Retrieve the details of a specific exchange server status record by its ID.",
        responses={200: ExchangeServerStatusSerializer},
        tags=["ExchangeServerStatus"]
    )
)
class ExchangeServerStatusViewSet(ReadOnlyModelViewSet):
    queryset = ExchangeServerStatus.objects.select_related('market_code').all()
    serializer_class = ExchangeServerStatusSerializer
    permission_classes = [AllowAny]