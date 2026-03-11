import json

import requests
from django.core.serializers.json import DjangoJSONEncoder
from urllib.parse import urljoin


class JsonApiClient:
    def __init__(self, base_url, default_headers=None):
        self.base_url = base_url
        self.default_headers = default_headers or {}

    def build_api_url(self, endpoint, path_param=None):
        api_url = urljoin(self.base_url, endpoint)
        if path_param:
            api_url = urljoin(api_url, str(path_param))
        return api_url

    def request(self, method, endpoint, path_param=None, query_params=None, data=None, headers=None):
        request_headers = {**self.default_headers, **(headers or {})}
        request_data = (
            json.dumps(data, cls=DjangoJSONEncoder)
            if data is not None
            else None
        )
        return requests.request(
            method=method,
            url=self.build_api_url(endpoint, path_param),
            params=query_params,
            data=request_data,
            headers=request_headers,
        )

