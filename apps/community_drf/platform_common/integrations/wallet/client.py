from platform_common.integrations.http import JsonApiClient


class WalletServiceClient(JsonApiClient):
    def __init__(self, base_url, api_key):
        super().__init__(base_url=base_url, default_headers={"x-api-key": api_key})

    def list(self, endpoint, query_params=None):
        return self.request("get", endpoint, query_params=query_params)

    def retrieve(self, endpoint, path_param, query_params=None):
        return self.request(
            "get",
            endpoint,
            path_param=path_param,
            query_params=query_params,
        )

    def create(self, endpoint, data):
        return self.request("post", endpoint, data=data)

    def update(self, endpoint, path_param, data):
        return self.request("put", endpoint, path_param=path_param, data=data)

    def destroy(self, endpoint, path_param):
        return self.request("delete", endpoint, path_param=path_param)

    def destroy_many(self, endpoint, query_params=None):
        return self.request("delete", endpoint, query_params=query_params)

