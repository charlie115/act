import requests


class CoinMarketCapClient:
    def __init__(self, crypto_info_url, api_key):
        self.crypto_info_url = crypto_info_url
        self.api_key = api_key

    @property
    def headers(self):
        return {"X-CMC_PRO_API_KEY": self.api_key}

    def get_asset_info(self, symbol):
        return requests.get(
            url=self.crypto_info_url,
            headers=self.headers,
            params={"symbol": symbol},
            timeout=10,
        )

    def fetch_logo(self, logo_url):
        return requests.get(logo_url, stream=True, timeout=10)

