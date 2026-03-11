from django.conf import settings
from rest_framework import exceptions

from platform_common.integrations.wallet import WalletServiceClient
from lib.permissions import ACWBasePermission
from lib.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from users.models import User, UserRole

class WalletMixin(object):
    def __init__(self):
        self.url = settings.WALLET_SERVICE_URL
        self.x_api_key = settings.WALLET_API_KEY

    def get_wallet_client(self):
        return WalletServiceClient(self.url, self.x_api_key)

    def hdwallet_service_list_api(self, endpoint, query_params=None):
        return self.get_wallet_client().list(endpoint, query_params=query_params)

    def hdwallet_service_retrieve_api(self, endpoint, path_param, query_params=None):
        return self.get_wallet_client().retrieve(
            endpoint,
            path_param,
            query_params=query_params,
        )

    def hdwallet_service_create_api(self, endpoint, data):
        return self.get_wallet_client().create(endpoint, data)

    def hdwallet_service_update_api(self, endpoint, path_param, data):
        return self.get_wallet_client().update(endpoint, path_param, data)

    def hdwallet_service_destroy_api(self, endpoint, path_param):
        return self.get_wallet_client().destroy(endpoint, path_param)

    def hdwallet_service_destroy_many_api(self, endpoint, query_params):
        return self.get_wallet_client().destroy_many(
            endpoint,
            query_params=query_params,
        )

    def handle_exception_from_api(self, api_response):
        try:
            detail = api_response.json()
        except Exception:
            detail = api_response.content

        if api_response.status_code == HTTP_400_BAD_REQUEST:
            raise exceptions.ParseError(detail)
        if api_response.status_code == HTTP_401_UNAUTHORIZED:
            raise exceptions.AuthenticationFailed
        if api_response.status_code == HTTP_403_FORBIDDEN:
            raise exceptions.PermissionDenied
        if api_response.status_code == HTTP_404_NOT_FOUND:
            raise exceptions.NotFound

        exception = exceptions.APIException(detail=detail)
        exception.status_code = api_response.status_code

        raise exception
