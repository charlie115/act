from rest_framework import exceptions

from platform_common.integrations.tradecore import TradeCoreClient
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

    def get_trade_config_allocation(self, trade_config_uuid, detail=False):
        try:
            trade_config_allocation = TradeConfigAllocation.objects.get(
                trade_config_uuid=trade_config_uuid
            )
        except TradeConfigAllocation.DoesNotExist:
            if detail:
                raise exceptions.NotFound()
            else:
                raise exceptions.ValidationError(
                    {"trade_config_uuid": "Trade config not found."}
                )
        except Exception as err:
            raise exceptions.ParseError({"detail": err.messages})

        return trade_config_allocation

    def get_node(self, trade_config_uuid):
        trade_config_allocation = self.get_trade_config_allocation(
            trade_config_uuid=trade_config_uuid
        )
        return trade_config_allocation.node

    def get_tradecore_client(self, url):
        return TradeCoreClient(base_url=url)

    def tradecore_list_api(self, url, endpoint, query_params=None):
        return self.get_tradecore_client(url).list(endpoint, query_params=query_params)

    def tradecore_retrieve_api(self, url, endpoint, path_param, query_params=None):
        return self.get_tradecore_client(url).retrieve(
            endpoint,
            path_param,
            query_params=query_params,
        )

    def tradecore_create_api(self, url, endpoint, data):
        return self.get_tradecore_client(url).create(endpoint, data)

    def tradecore_update_api(self, url, endpoint, path_param, data):
        return self.get_tradecore_client(url).update(endpoint, path_param, data)

    def tradecore_destroy_api(self, url, endpoint, path_param):
        return self.get_tradecore_client(url).destroy(endpoint, path_param)

    def tradecore_destroy_many_api(self, url, endpoint, query_params):
        return self.get_tradecore_client(url).destroy_many(
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
