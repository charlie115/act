from django.core.cache import cache
from django.shortcuts import render
from rest_framework import views, response
from wallet.mixins import WalletMixin
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import exceptions, mixins, response, views, viewsets
from rest_framework.decorators import action
from lib.permissions import IsAdmin, IsInternal, IsManager, IsUser
from lib.status import HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from wallet.serializers import UserWalletQueryParamsSerializer, UserWalletBalanceQueryParmasSerializer, UserWalletDepositBodyParamsSerializer

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
    tradecore_api_endpoint = "user_wallet/"

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
            endpoint=self.tradecore_api_endpoint,
            path_param=validated_data.get("user_id"),
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)
        
class UserWalletBalanceView(WalletMixin, views.APIView):
    http_method_names = ["get"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "user_wallet_balance/"

    def get(self, request, user):
        query_params = (UserWalletBalanceQueryParmasSerializer(
            context={"view": self, "request": request},
            data={"user": user}, # user uuid
        ))
        query_params.is_valid(raise_exception=True)
        validated_data = query_params.validated_data

        data = self.get_data(validated_data)

        return response.Response(data)

    def get_data(self, validated_data):
        api_response = self.hdwallet_service_retrieve_api(
            endpoint=self.tradecore_api_endpoint,
            path_param=validated_data.get("user_id"),
        )

        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj

        self.handle_exception_from_api(api_response)
        
class UserWalletDepositView(WalletMixin, views.APIView):
    http_method_names = ["post"]
    permission_classes = [IsAdmin | IsInternal | IsManager | IsUser]
    tradecore_api_endpoint = "user_wallet_deposit/"

    def post(self, request):
        body_params = UserWalletDepositBodyParamsSerializer(
            context={"view": self, "request": request},
            data=request.data,
        )
        body_params.is_valid(raise_exception=True)
        validated_data = body_params.validated_data
        
        # Get the transaction data of incoming TRX or USDT: list
        data = self.get_data(validated_data)
        
        return response.Response(data)
    
    def get_data(self, validated_data):
        api_response = self.hdwallet_service_retrieve_api(
            endpoint=self.tradecore_api_endpoint,
            path_param=validated_data.pop("user_id", ""),
            query_params=validated_data,
        )
        
        if api_response.status_code == HTTP_200_OK:
            obj = api_response.json()
            return obj
        
        self.handle_exception_from_api(api_response)