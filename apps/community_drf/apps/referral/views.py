from lib.views import BaseViewSet
from users.models import User, DepositHistory
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import viewsets, mixins, exceptions, response, status
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from lib.authentication import NodeIPAuthentication
from lib.permissions import IsAdmin, IsInternal
from django.db import models, transaction

from referral.constants import (
    PROFIT_TYPE_FEE,
)
from fee.models import FeeRate

from .models import AffiliateTier, Affiliate, ReferralCode, Referral, AffiliateRequest, CommissionHistory, CommissionBalance
from .serializers import (
    AffiliateTierSerializer,
    AffiliateSerializer,
    ReferralCodeSerializer,
    ReferralSerializer,
    ReferralCommissionQueryParamsSerializer,
    AffiliateRequestSerializer,
    CommissionBalanceSerializer,
    CommissionHistorySerializer,
    SubAffiliateSerializer,
)
from .utils import calculate_fee_and_commission_for_trade, get_all_affiliate_ids

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
class AffiliateTierViewSet(viewsets.ModelViewSet):
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
class AffiliateViewSet(viewsets.ModelViewSet):
    queryset = Affiliate.objects.select_related('user', 'tier', 'parent_affiliate')
    serializer_class = AffiliateSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["parent_affiliate_id", "tier"]
    ordering_fields = ["id", "created_at"]
    ordering = ["id"]
    # allow only get
    http_method_names = ["get"]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'affiliate'):
            # User is not an affiliate, return empty queryset
            return Affiliate.objects.none()
        related_affiliate_ids = get_all_affiliate_ids(user.affiliate)
        return Affiliate.objects.filter(id__in=related_affiliate_ids)
    
@extend_schema(tags=["SubAffiliate"])
@extend_schema_view(
    list=extend_schema(description="List all sub-affiliates with hidden fields"),
    retrieve=extend_schema(description="Retrieve a specific affiliate"),
    # create=extend_schema(description="Create a new affiliate"),
    # update=extend_schema(description="Update an affiliate"),
    # partial_update=extend_schema(description="Partially update an affiliate"),
    # destroy=extend_schema(description="Delete an affiliate"),
)
@extend_schema_view(
    get=extend_schema(
        operation_id="List Sub Affiliates",
        description="List all sub-affiliates of a parent affiliate without hidden fields.",
        responses={200: SubAffiliateSerializer(many=True)},
        tags=["SubAffiliate"]
    )
)
class SubAffiliateListView(ListAPIView):
    serializer_class = SubAffiliateSerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'affiliate'):
            # User is not an affiliate, return empty queryset
            return Affiliate.objects.none()
        
        affiliate = user.affiliate
        return Affiliate.objects.filter(parent_affiliate=affiliate)

@extend_schema(tags=["ReferralCode"])
@extend_schema_view(
    list=extend_schema(description="List all referral codes"),
    retrieve=extend_schema(description="Retrieve a specific referral code"),
    create=extend_schema(description="Create a new referral code"),
    # update=extend_schema(description="Update a referral code"),
    # partial_update=extend_schema(description="Partially update a referral code"),
    destroy=extend_schema(description="Delete a referral code"),
)
class ReferralCodeViewSet(viewsets.ModelViewSet):
    queryset = ReferralCode.objects.select_related('affiliate', 'affiliate__tier', 'affiliate__user')
    serializer_class = ReferralCodeSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["affiliate", "code", "created_at"]
    ordering_fields = ["id", "code"]
    ordering = ["id"]
    # allow only get, post, delete
    http_method_names = ["get", "post", "delete"]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'affiliate'):
            # User is not an affiliate, return empty queryset
            return ReferralCode.objects.none()
        return ReferralCode.objects.filter(affiliate=user.affiliate)
        
@extend_schema(tags=["Referral"])
@extend_schema_view(
    list=extend_schema(description="List all referrals"),
    retrieve=extend_schema(description="Retrieve a specific referral"),
    create=extend_schema(description="Create a new referral"),
    # update=extend_schema(description="Update a referral"),
    # partial_update=extend_schema(description="Partially update a referral"),
    # destroy=extend_schema(description="Delete a referral"),
)
class ReferralViewSet(viewsets.ModelViewSet):
    queryset = Referral.objects.select_related('referral_code', 'referral_code__affiliate', 'referred_user')
    serializer_class = ReferralSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["referred_user", "referral_code"]
    ordering_fields = ["id", "created_at"]
    ordering = ["id"]
    # allow only get, post
    http_method_names = ["get", "post"]
    
    def get_queryset(self):
        user = self.request.user
        return Referral.objects.filter(referred_user=user)

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
    permission_classes = [IsAdmin | IsInternal]

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
        try:
            user_fee_rate = FeeRate.objects.get(level=user.fee_level.fee_level)
        except FeeRate.DoesNotExist:
            raise exceptions.ValidationError({"fee_rate": [f"No FeeRate configured for level {user.fee_level.fee_level}."]})
        user_fee = initial_profit * user_fee_rate.rate
        apply_to_deposit = validated.get("apply_to_deposit")
        trade_uuid = validated.get("trade_uuid")
        
        # Check if user has any remaining coupon credit
        coupon_credits = DepositHistory.objects.filter(
            user=user,
            type=DepositHistory.COUPON
        ).aggregate(total=models.Sum('change'))['total'] or 0
        
        # Get fee payments to calculate how much coupon credit has been used so far
        fee_payments = DepositHistory.objects.filter(
            user=user,
            type=DepositHistory.FEE
        ).aggregate(total=models.Sum('change'))['total'] or 0
                
        # Calculate remaining coupon credit (coupon credits minus fee payments)
        # Assuming coupons are used first for fees
        remaining_coupon_credit = coupon_credits + fee_payments # fee_payments are negative, so we add them
        
        # Get current user balance
        try:
            current_balance = user.deposit_balance.balance
        except User.deposit_balance.RelatedObjectDoesNotExist:
            current_balance = 0
        
        # Check both coupon credit and balance conditions
        using_coupon_funds = remaining_coupon_credit > 0
        has_negative_balance = current_balance < 0
        would_have_negative_balance = current_balance - user_fee < 0
        
        # Bypass commission if any of these conditions is true
        bypass_commission = using_coupon_funds or has_negative_balance or would_have_negative_balance
        
        if bypass_commission:
            # Determine reason for bypass
            reason = []
            if using_coupon_funds:
                reason.append(f"user has coupon credit (${float(remaining_coupon_credit)} remaining)")
            if has_negative_balance:
                reason.append(f"user has negative balance (${float(current_balance)})")
            elif would_have_negative_balance:
                reason.append(f"fee would cause negative balance (${float(current_balance)} - ${float(user_fee)})")
            
            reason_str = " and ".join(reason)
            
            # Skip commission calculation
            result = {
                "trade_uuid": trade_uuid,
                "records": [
                    {
                        "data_type": "deposit_history",
                        "user": user,
                        "change": user_fee * -1,
                        "type": PROFIT_TYPE_FEE,
                        "trade_uuid": trade_uuid,
                        "description": f"Fee paid with {reason_str} - no commission applied"
                    }
                ]
            }
        elif not referral:
            result = {
                "trade_uuid": trade_uuid,
                "records": [
                    {
                        "data_type": "deposit_history",
                        "user": user,
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
            # Guard against duplicate application for the same trade
            if trade_uuid and DepositHistory.objects.filter(trade_uuid=trade_uuid).exists():
                raise exceptions.ValidationError({
                    "error": "DUPLICATE_TRADE",
                    "message": f"Records for trade_uuid {trade_uuid} already exist."
                })

            with transaction.atomic():
                for record in result["records"]:
                    if record["data_type"] == "deposit_history":
                        DepositHistory.objects.create(
                            user=record["user"],
                            change=record["change"],
                            referral_discount=record.get("referral_discount", 0),
                            type=record["type"],
                            trade_uuid=trade_uuid,
                            description=record.get("description")
                        )
                    elif record["data_type"] == "commission_history":
                        CommissionHistory.objects.create(
                            affiliate=record["affiliate"],
                            child_affiliate=record["child_affiliate"],
                            user_who_paid=record["user_who_paid"],
                            service_type=record["service_type"],
                            type=record["type"],
                            trade_uuid=record["trade_uuid"],
                            change=record["change"],
                        )
                
        # change user model to user uuid
        for record in result["records"]:
            if record.get("user"):
                record["user"] = record["user"].uuid
            if record.get("affiliate"):
                record["affiliate"] = record["affiliate"].id
            if record.get("child_affiliate"):
                record["child_affiliate"] = record["child_affiliate"].id
            if record.get("user_who_paid"):
                record["user_who_paid"] = record["user_who_paid"].uuid
        
        return response.Response(result, status=status.HTTP_200_OK)
    
    def get_authenticators(self):
        authentication_classes = self.authentication_classes + [NodeIPAuthentication]
        return [auth() for auth in authentication_classes]

    def get_permissions(self):
        permission_classes = self.permission_classes

        if (
            hasattr(self.request, "_authenticator")
            and type(self.request._authenticator) is NodeIPAuthentication
        ):
            permission_classes = []

        return [permission() for permission in permission_classes]
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

@extend_schema_view(
    get=extend_schema(
        operation_id="List Commission History",
        description="List all commission history records for the user's affiliate and all its descendant affiliates.",
        responses={200: CommissionHistorySerializer(many=True)},
        tags=["CommissionHistory"]
    )
)
class CommissionHistoryListView(ListAPIView):
    serializer_class = CommissionHistorySerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'affiliate'):
            # User is not an affiliate, return empty queryset
            return CommissionHistory.objects.none()

        affiliate = user.affiliate
        affiliate_ids = get_all_affiliate_ids(affiliate)
        # Filter by these affiliate ids either as main affiliate or child affiliate
        # CommissionHistory can belong to affiliate and also has child_affiliate
        # We assume we want records where either affiliate_id or child_affiliate_id is in affiliate_ids
        return CommissionHistory.objects.filter(
            Q(affiliate_id__in=affiliate_ids)
        ).order_by('-created_at')
        
@extend_schema_view(
    get=extend_schema(
        operation_id="List Commission Balances",
        description="List commission balance records for the user's affiliate and all its descendant affiliates.",
        responses={200: CommissionBalanceSerializer(many=True)},
        tags=["CommissionBalance"]
    )
)
class CommissionBalanceListView(ListAPIView):
    serializer_class = CommissionBalanceSerializer

    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'affiliate'):
            return CommissionBalance.objects.none()

        affiliate = user.affiliate
        affiliate_ids = get_all_affiliate_ids(affiliate)
        return CommissionBalance.objects.filter(affiliate_id__in=affiliate_ids)