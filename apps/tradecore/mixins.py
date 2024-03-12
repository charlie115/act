import json
import requests

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
from tradecore.models import TradeConfigAllocation
from users.models import User, UserRole


class TradeCoreMixin(object):
    def finalize_queryset(self, queryset):
        query_field = ""
        query = {}

        if queryset.model is User:
            query_field = "id__in"
            query = {query_field: [self.request.user.uuid]}

        elif hasattr(queryset.model, "user"):
            query_field = "user_id__in"
            query = {query_field: [self.request.user.id]}

        if self.request.user.role.name == UserRole.ADMIN:
            return queryset

        if (
            self.request.user.role.name == UserRole.INTERNAL_USER
            and ACWBasePermission().has_api_permission(self.request)
        ):
            return queryset

        if (
            self.request.user.role.name == UserRole.MANAGER
            and ACWBasePermission().has_api_permission(self.request)
        ):
            managed_user_uuids = self.request.user.managed_users.values_list(
                "managed_user__uuid",
                flat=True,
            )

            try:
                query[query_field] += managed_user_uuids
            except KeyError:
                pass

        return queryset.filter(**query)

    def get_trade_config_allocation(
        self,
        trade_config_uuid,
        exception_to_raise=exceptions.NotFound(),
    ):
        try:
            trade_config_allocation = TradeConfigAllocation.objects.get(
                trade_config_uuid=trade_config_uuid
            )
        except TradeConfigAllocation.DoesNotExist:
            raise exception_to_raise

        return trade_config_allocation

    def get_node(self, trade_config_uuid):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=trade_config_uuid,
            exception_to_raise=exceptions.ValidationError(
                {"trade_config_uuid": "Trade config not found."}
            ),
        )
        return trade_config_allocation.node

    def build_api_url(self, url, endpoint, path_param=None):
        api_url = urljoin(url, endpoint)
        if path_param:
            api_url = urljoin(api_url, str(path_param))
        return api_url

    def tradecore_list_api(self, url, endpoint, query_params=None):
        api_url = self.build_api_url(url, endpoint)
        api_response = requests.get(url=api_url, params=query_params)
        return api_response

    def tradecore_retrieve_api(self, url, endpoint, path_param):
        api_url = self.build_api_url(url, endpoint, path_param)
        api_response = requests.get(url=api_url)
        return api_response

    def tradecore_create_api(self, url, endpoint, data):
        api_url = self.build_api_url(url, endpoint)
        api_data = json.dumps(data, cls=DjangoJSONEncoder)
        api_response = requests.post(url=api_url, data=api_data)
        return api_response

    def tradecore_update_api(self, url, endpoint, path_param, data):
        api_url = self.build_api_url(url, endpoint, path_param)
        api_data = json.dumps(data, cls=DjangoJSONEncoder)
        api_response = requests.put(url=api_url, data=api_data)
        return api_response

    def tradecore_destroy_api(self, url, endpoint, path_param):
        api_url = self.build_api_url(url, endpoint, path_param)
        api_response = requests.delete(url=api_url)
        return api_response

    def tradecore_destroy_many_api(self, url, endpoint, query_params):
        api_url = self.build_api_url(url, endpoint)
        api_response = requests.delete(url=api_url, params=query_params)
        return api_response

    def handle_exception_from_api(self, api_response):
        try:
            detail = api_response.json()
        except Exception:
            detail = api_response.content

        if api_response.status_code == HTTP_400_BAD_REQUEST:
            raise exceptions.ParseError
        if api_response.status_code == HTTP_401_UNAUTHORIZED:
            raise exceptions.AuthenticationFailed
        if api_response.status_code == HTTP_403_FORBIDDEN:
            raise exceptions.PermissionDenied
        if api_response.status_code == HTTP_404_NOT_FOUND:
            raise exceptions.NotFound

        exception = exceptions.APIException(detail=detail)
        exception.status_code = api_response.status_code

        raise exception
