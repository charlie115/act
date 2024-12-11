from django.core.cache import cache
from django.shortcuts import render
from rest_framework import views, response
from wallet.mixins import WalletMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, response, views, viewsets
from rest_framework.decorators import action
from lib.permissions import IsAdmin, IsInternal, IsManager, IsUser
from lib.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from wallet.serializers import UserWalletQueryParamsSerializer, UserWalletBalanceQueryParmasSerializer, UserWalletTransactionBodyParamsSerializer
from users.models import DepositHistory, User
from decimal import Decimal, ROUND_HALF_UP

@extend_schema_view(
    get=extend_schema(
        operation_id="Get user hd wallet address",
        description="Retrieves `user hd wallet` information.",
        tags=["UserWalletAddress"],
    ),
)
class UserWalletAddressView(WalletMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    hdwallet_api_endpoint = "user_wallet/"

    def get(self, request, user):
        query_params = (UserWalletQueryParamsSerializer(
            context={"view": self, "request": request},
            data={"user": user}, # user uuid
        ))
        query_params.is_valid(raise_exception=True)
        validated_data = query_params.validated_data

        data = self.get_data(validated_data)

        return response.Response(data)

    def get_data(self, validated_data):
        api_response = self.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_api_endpoint,
            path_param=validated_data.get("user_id"),
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)
        
@extend_schema_view(
    get=extend_schema(
        operation_id="Get user hd wallet balance",
        description="Retrieves `user hd wallet balance` information.",
        tags=["UserWalletBalance"],
    ),
)
class UserWalletBalanceView(WalletMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    hdwallet_api_endpoint = "user_wallet/balance/"

    def get(self, request, user):
        asset = request.query_params.get("asset")
        query_params = (UserWalletBalanceQueryParmasSerializer(
            context={"view": self, "request": request},
            data={
                    "user": user,
                    "asset": asset
                },
        ))
        query_params.is_valid(raise_exception=True)
        validated_data = query_params.validated_data

        data = self.get_data(validated_data)

        return response.Response(data)

    def get_data(self, validated_data):
        query_params = {}
        query_params["asset"] = validated_data.get("asset")
        api_response = self.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_api_endpoint,
            path_param=validated_data.get("user_id"),
            query_params=query_params,
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)

@extend_schema_view(
    post=extend_schema(
        operation_id="process user wallet transaction to the deposit history",
        description="Fetch user wallet transaction and process information to the deposit history.",
        tags=["UserWalletDeposit"],
    ),
)        
class UserWalletTransactionView(WalletMixin, views.APIView):
    http_method_names = ["post"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    hdwallet_api_endpoint = "user_wallet/transactions/"

    def post(self, request):
        body_params = UserWalletTransactionBodyParamsSerializer(
            context={"view": self, "request": request},
            data=request.data,
        )
        body_params.is_valid(raise_exception=True)
        validated_data = body_params.validated_data
        
        # Get the transaction data of incoming TRX or USDT: list
        data = self.get_data(validated_data)
        total_withdraw_amount = 0
        total_deposit_amount = 0
            
        for transaction in data:
            # Filter out TRX transactions
            if transaction.get("asset") == "TRX":
                continue
            txid = transaction.get('txid')
            # Check whether the transaction is already processed (same txid)
            if DepositHistory.objects.filter(txid=txid).exists():
                continue
            # Check whether it's incoming transaction(deposit)
            if transaction.get("owner_address") == transaction.get("to_address"):
                change = Decimal(transaction.get('amount')).quantize(
                            Decimal('0.01'), 
                            rounding=ROUND_HALF_UP
                        )
                type = DepositHistory.DEPOSIT
                total_deposit_amount += change
            # Check whether it's outgoing transaction(withdraw) -> 회사로 돈 뺄때는 어떻게 처리? -> 처리하지 말자. 이건 나중에 유저 withdrawl 에서 처리하기로.
            else:
                # change = (Decimal(transaction.get('amount')) * Decimal('-1')).quantize(
                #             Decimal('0.01'),
                #             rounding=ROUND_HALF_UP
                #         )
                # type = DepositHistory.WITHDRAW
                # total_withdraw_amount += change * Decimal('-1')
                continue
                
            # Save the transaction to the deposit history
            DepositHistory.objects.create(
                user=User.objects.get(uuid=validated_data.get("user")),
                change=change,
                txid=txid,
                type=type,
                pending=False,
            )
        
        processed_data = {
            "message": "User wallet transaction processed successfully",
            "result": {
                "total_deposit_amount": total_deposit_amount,
                "total_withdraw_amount": total_withdraw_amount,
            }
        }
        if total_deposit_amount == 0 and total_withdraw_amount == 0:
            processed_data["message"] = "No new transaction data for USDT found, No Deposit, No Withdraw processed"
            return response.Response(processed_data, status=HTTP_200_OK)
        return response.Response(processed_data, status=HTTP_201_CREATED)
    
    def get_data(self, validated_data):
        api_response = self.hdwallet_service_retrieve_api(
            endpoint=self.hdwallet_api_endpoint,
            path_param=validated_data.pop("user_id", ""),
            query_params=validated_data,
        )
        
        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj
        
        self.handle_exception_from_api(api_response)