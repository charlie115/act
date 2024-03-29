from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, response, views
from rest_framework.filters import OrderingFilter
from rest_framework.pagination import PageNumberPagination


from lib.views import BaseViewSet
from referral.constants import (
    SERVICE_FEE_RATE,
    PROFIT_TYPE_TRADE,
    PROFIT_TYPE_COMMISSION,
)
from referral.models import Referral, ReferralCode
from referral.serializers import (
    ReferralSerializer,
    ReferralCodeSerializer,
    ReferralCommissionQueryParamsSerializer,
)
from users.models import User


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


@extend_schema_view(
    get=extend_schema(
        operation_id="Calculate profit and commissions in a trade",
        description="Returns the user's profit from their trade, as well as all the commissions from the referrals",
        parameters=[ReferralCommissionQueryParamsSerializer],
        tags=["ReferralCommission"],
    ),
)
class ReferralCommissionView(views.APIView):
    http_method_names = ["get"]
    permission_classes = []

    def get(self, request):
        query_params = ReferralCommissionQueryParamsSerializer(
            data=request.query_params
        )
        query_params.is_valid(raise_exception=True)
        query = query_params.validated_data

        self.target_market_code = query.get("target_market_code")
        self.origin_market_code = query.get("origin_market_code")

        data = {
            "trade_uuid": query.get("trade_uuid"),
            "profit": self.get_profit_data(
                user=query.get("user"),
                initial_profit=query.get("initial_profit"),
            ),
        }

        return response.Response(data)

    def get_profit_data(self, user, initial_profit):
        try:
            user = User.objects.get(uuid=user)
        except User.DoesNotExist:
            raise exceptions.ValidationError({"user": ["User not found."]})

        # User
        user_profit = initial_profit * SERVICE_FEE_RATE
        company_profit = initial_profit - user_profit

        user_profit_data = {
            "user": user.uuid,
            "profit": user_profit,
            "type": PROFIT_TYPE_TRADE,
        }
        data = [user_profit_data]

        try:
            used_referral = user.used_referrals.get(
                referral_code__target_market_code=self.target_market_code,
                referral_code__origin_market_code=self.origin_market_code,
            )
            used_referral_code = used_referral.referral_code

            referrer_profit_data = self.compute_commission(
                referred_user=user,
                referral_code=used_referral_code,
                profit=(
                    company_profit * used_referral_code.referral_group.commission_rate
                ),  # User's direct referrer
            )
            data.extend(referrer_profit_data)

        except Referral.DoesNotExist:
            pass

        return data

    def compute_commission(self, referred_user, referral_code, profit, depth=1):
        data = []

        user_profit_data = {
            "user": referral_code.user.uuid,
            "profit": profit,
            "type": PROFIT_TYPE_COMMISSION,
            "commission_from": referred_user.uuid,
        }
        try:
            used_referral = referral_code.user.used_referrals.get(
                referral_code__target_market_code=self.target_market_code,
                referral_code__origin_market_code=self.origin_market_code,
            )
        except Referral.DoesNotExist:
            used_referral = None

        if used_referral and referral_code.referral_group.upper_share_rate != 0:
            # Users who are not direct referrer can't get any profit
            # And we pass the potention profit instead to the upper referrer in case max_depth > 1
            if depth > 1 and referral_code.max_depth == 1:
                user_profit_data["profit"] = 0
                upper_referrer_profit = profit
            else:
                upper_referrer_profit = (
                    profit * referral_code.referral_group.upper_share_rate
                )
                user_profit_data["profit"] = profit - upper_referrer_profit

            data.append(user_profit_data)

            # Repeat steps to compute for (upper) referrer profit
            referrer_profit_data = self.compute_commission(
                referred_user=referral_code.user,
                referral_code=used_referral.referral_code,
                profit=upper_referrer_profit,
                depth=depth + 1,
            )
            data.extend(referrer_profit_data)
        else:
            data.append(user_profit_data)

        return data
