import json
import requests
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import exceptions
from urllib.parse import urljoin

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
        
        # TEST
        self.url = "http://localhost:8003"
        self.x_api_key = "test"
        # TEST

    def build_api_url(self, endpoint, path_param=None):
        api_url = urljoin(self.url, endpoint)        
        if path_param:
            api_url = urljoin(api_url, str(path_param))
        return api_url

    def hdwallet_service_list_api(self, endpoint, query_params=None):
        api_url = self.build_api_url(endpoint)
        api_response = requests.get(
            url=api_url,
            headers={"x-api-key": self.x_api_key},
            params=query_params
        )
        return api_response

    def hdwallet_service_retrieve_api(self, endpoint, path_param, query_params=None):
        api_url = self.build_api_url(endpoint, path_param)
        api_response = requests.get(
            url=api_url,
            headers={"x-api-key": self.x_api_key},
            params=query_params
        )
        return api_response

    def hdwallet_service_create_api(self, endpoint, data):
        api_url = self.build_api_url(endpoint)
        api_data = json.dumps(data, cls=DjangoJSONEncoder)
        api_response = requests.post(
            url=api_url,
            headers={"x-api-key": self.x_api_key},
            data=api_data
        )
        return api_response

    def hdwallet_service_update_api(self, endpoint, path_param, data):
        api_url = self.build_api_url(endpoint, path_param)
        api_data = json.dumps(data, cls=DjangoJSONEncoder)
        api_response = requests.put(
            url=api_url,
            headers={"x-api-key": self.x_api_key},
            data=api_data
        )
        return api_response

    def hdwallet_service_destroy_api(self, endpoint, path_param):
        api_url = self.build_api_url(endpoint, path_param)
        api_response = requests.delete(
            url=api_url,
            headers={"x-api-key": self.x_api_key}
        )
        return api_response

    def hdwallet_service_destroy_many_api(self, endpoint, query_params):
        api_url = self.build_api_url(endpoint)
        api_response = requests.delete(
            url=api_url,
            headers={"x-api-key": self.x_api_key},
            params=query_params
        )
        return api_response

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
