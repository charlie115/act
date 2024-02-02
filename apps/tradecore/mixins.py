import json
import requests

from django.core.serializers.json import DjangoJSONEncoder
from rest_framework import exceptions
from urllib.parse import urljoin

from tradecore.models import TradeConfigAllocation


class TradeCoreMixin(object):
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

        exception = exceptions.APIException(detail=detail)
        exception.status_code = api_response.status_code

        raise exception
