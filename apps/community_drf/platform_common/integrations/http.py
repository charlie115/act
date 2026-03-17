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
        if path_param is not None:
            api_url = urljoin(api_url, str(path_param))
        return api_url

    def request(self, method, endpoint, path_param=None, query_params=None, data=None, headers=None):
        request_headers = {**self.default_headers, **(headers or {})}
        kwargs = {
            "method": method,
            "url": self.build_api_url(endpoint, path_param),
            "params": query_params,
            "headers": request_headers,
            "timeout": 30,
        }
        if data is not None:
            # Use DjangoJSONEncoder to handle Decimal, UUID, datetime, etc.
            # and set Content-Type explicitly so the server parses it as JSON.
            request_headers.setdefault("Content-Type", "application/json")
            kwargs["data"] = json.dumps(data, cls=DjangoJSONEncoder)
        return requests.request(**kwargs)

