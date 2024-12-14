from lib.views import BaseViewSet
from users.models import User, DepositHistory
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins, exceptions, response, status
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView

from referral.constants import (
    PROFIT_TYPE_FEE,
    PROFIT_TYPE_COMMISSION,
)
from fee.models import FeeRate

from .models import AffiliateTier, Affiliate, ReferralCode, Referral, AffiliateRequest
from .serializers import (
    AffiliateTierSerializer,
    AffiliateSerializer,
    ReferralCodeSerializer,
    ReferralSerializer,
    ReferralCommissionQueryParamsSerializer,
    AffiliateRequestSerializer,
)
from .utils import calculate_fee_and_commission_for_trade

### ViewSets ###

@extend_schema(tags=["AffiliateTier"])
@extend_schema_view(
    list=extend_schema(description="List all affiliate tiers"),
    retrieve=extend_schema(description="Retrieve a specific affiliate tier"),
    # create=extend_schema(description="Create a new affiliate tier"),
    # update=extend_schema(description="Update an affiliate tier"),
    # partial_update=extend_schema(description="Partially update an affiliate tier"),
    # destroy=extend_schema(description="Delete an affiliate tier"),
)
class AffiliateTierViewSet(BaseViewSet):
    queryset = AffiliateTier.objects.all()
    serializer_class = AffiliateTierSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["name"]
    ordering_fields = ["id", "name"]
    ordering = ["id"]
    # Allow only get
    http_method_names = ["get"]
@extend_schema(tags=["Affiliate"])
@extend_schema_view(
    list=extend_schema(description="List all affiliates"),
    retrieve=extend_schema(description="Retrieve a specific affiliate"),
    # create=extend_schema(description="Create a new affiliate"),
    # update=extend_schema(description="Update an affiliate"),
    # partial_update=extend_schema(description="Partially update an affiliate"),
    # destroy=extend_schema(description="Delete an affiliate"),
)
# class AffiliateViewSet(BaseViewSet):
class AffiliateViewSet(viewsets.ModelViewSet):
    queryset = Affiliate.objects.select_related('user', 'tier', 'parent_affiliate')
    serializer_class = AffiliateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["parent_affiliate_id", "tier"]
    ordering_fields = ["id", "created_at"]
    ordering = ["id"]
    # allow only get
    http_method_names = ["get"]

@extend_schema(tags=["ReferralCode"])
@extend_schema_view(
    list=extend_schema(description="List all referral codes"),
    retrieve=extend_schema(description="Retrieve a specific referral code"),
    create=extend_schema(description="Create a new referral code"),
    # update=extend_schema(description="Update a referral code"),
    # partial_update=extend_schema(description="Partially update a referral code"),
    destroy=extend_schema(description="Delete a referral code"),
)
class ReferralCodeViewSet(BaseViewSet):
    queryset = ReferralCode.objects.select_related('affiliate', 'affiliate__tier', 'affiliate__user')
    serializer_class = ReferralCodeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["affiliate", "code", "created_at"]
    ordering_fields = ["id", "code"]
    ordering = ["id"]
    # allow only get, post, delete
    http_method_names = ["get", "post", "delete"]

@extend_schema(tags=["Referral"])
@extend_schema_view(
    list=extend_schema(description="List all referrals"),
    retrieve=extend_schema(description="Retrieve a specific referral"),
    create=extend_schema(description="Create a new referral"),
    # update=extend_schema(description="Update a referral"),
    # partial_update=extend_schema(description="Partially update a referral"),
    # destroy=extend_schema(description="Delete a referral"),
)
class ReferralViewSet(BaseViewSet):
    queryset = Referral.objects.select_related('referral_code', 'referral_code__affiliate', 'referred_user')
    serializer_class = ReferralSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["referred_user", "referral_code"]
    ordering_fields = ["id", "created_at"]
    ordering = ["id"]
    # allow only get, post
    http_method_names = ["get", "post"]

### Commission Calculation View ###

@extend_schema_view(
    get=extend_schema(
        operation_id="Calculate profit and commissions in a trade",
        description="Returns the user's profit from their trade and all commissions earned by affiliates. Query parameters should include necessary info.",
        parameters=[ReferralCommissionQueryParamsSerializer],
        tags=["ReferralCommission"]
    ),
)
class ReferralCommissionView(APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        query_params = ReferralCommissionQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        validated = query_params.validated_data

        user_uuid = validated.get("user")
        try:
            user = User.objects.get(uuid=user_uuid)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"user": ["User not found."]})
        # Check whether the user has a referral
        try:
            referral = user.referral
        except Referral.DoesNotExist:
            referral = None
        initial_profit = validated.get("initial_profit")  # assuming initial_profit is the profit from user
        if initial_profit < 0:
            raise exceptions.ValidationError({"initial_profit": ["Profit cannot be negative."]})
        # Calculate the user fee from from the profit using user's fee rate
        user_fee_rate = FeeRate.objects.get(level=user.fee_level.fee_level)
        print(f"user_fee_rate: {user_fee_rate}")
        user_fee = initial_profit * user_fee_rate.rate
        apply_to_deposit = validated.get("apply_to_deposit")
        trade_uuid = validated.get("trade_uuid")
        
        if not referral:
            result = {
                "trade_uuid": trade_uuid,
                "records": [
                    {
                        "user": user,
                        "commission_from": None,
                        "change": user_fee * -1,
                        "type": PROFIT_TYPE_FEE,
                        "trade_uuid": trade_uuid,
                    }
                ]
            }

        else:
            result = calculate_fee_and_commission_for_trade(user, user_fee, referral, trade_uuid)

        # If apply_to_deposit is True, record the payouts in DepositHistory.
        # For simplicity, you can integrate that logic in utils or here.
        # Example:
        if apply_to_deposit:
            for record in result["records"]:
                DepositHistory.objects.create(
                    user=record["user"],
                    commission_from=record["commission_from"],
                    change=record["change"],
                    type=record["type"],
                    trade_uuid=trade_uuid,
                    description=record.get("description")
                )
                
        # change user model to user uuid
        for record in result["records"]:
            record["user"] = record["user"].uuid
            if record["commission_from"]:
                record["commission_from"] = record["commission_from"].uuid
        
        return response.Response(result, status=status.HTTP_200_OK)
@extend_schema(tags=["AffiliateRequest"])
@extend_schema_view(
    list=extend_schema(
        description="List all AffiliateRequests.",
    ),
    retrieve=extend_schema(
        description="Retrieve a specific AffiliateRequest.",
    ),
    create=extend_schema(
        description="Create a new AffiliateRequest.",
    ),
)    
class AffiliateRequestViewSet(BaseViewSet):
    """
    A viewset for authenticated users to:
    - Create a new AffiliateRequest (status will be PENDING by default).
    - List their own requests (if not admin, they only see their own).
    - Retrieve details of a single request.

    Admins or users with special permissions (as defined in BaseViewSet) can see all requests or manage them.
    """
    queryset = AffiliateRequest.objects.all()
    serializer_class = AffiliateRequestSerializer
    # allow get, post
    http_method_names = ["get", "post"]

    def get_queryset(self):
        # BaseViewSet logic applies ownership filtering. 
        # If Admin/Internal/Manager, may return more than just user's own requests.
        queryset = super().get_queryset()
        return queryset