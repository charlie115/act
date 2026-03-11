import os
import sys
import datetime
import pandas as pd
import time
import traceback
import requests

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger


class Coinone:
    """
    Low-level Coinone API client.
    Handles REST API calls to Coinone's public API v2.
    """
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.server_url = "https://api.coinone.co.kr"
        self.headers = {"accept": "application/json"}

    def _request(self, method, endpoint, params=None, timeout=10):
        """Make HTTP request to Coinone API."""
        url = f"{self.server_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
            else:
                response = requests.post(url, headers=self.headers, json=params, timeout=timeout)

            response.raise_for_status()
            data = response.json()

            if data.get('result') != 'success':
                raise Exception(f"Coinone API error: {data.get('error_code')} - {data}")

            return data
        except requests.exceptions.RequestException as e:
            raise Exception(f"Coinone request failed: {e}")

    def get_markets(self, quote_currency="KRW"):
        """
        Get all available trading pairs for a quote currency.
        GET /public/v2/markets/{quote_currency}
        """
        endpoint = f"/public/v2/markets/{quote_currency}"
        data = self._request("GET", endpoint)
        return data.get('markets', [])

    def get_tickers(self, quote_currency="KRW"):
        """
        Get ticker information for all markets.
        GET /public/v2/ticker_new/{quote_currency}
        """
        endpoint = f"/public/v2/ticker_new/{quote_currency}"
        data = self._request("GET", endpoint)
        return data.get('tickers', [])

    def get_currencies(self):
        """
        Get all available currencies with deposit/withdrawal status.
        GET /public/v2/currencies
        """
        endpoint = "/public/v2/currencies"
        data = self._request("GET", endpoint)
        return data.get('currencies', [])

    def get_orderbook(self, quote_currency, target_currency, size=15):
        """
        Get orderbook for a specific trading pair.
        GET /public/v2/orderbook/{quote_currency}/{target_currency}
        """
        endpoint = f"/public/v2/orderbook/{quote_currency}/{target_currency}"
        params = {"size": size}
        data = self._request("GET", endpoint, params=params)
        return data

    def spot_all_tickers(self, quote_currency="KRW"):
        """
        Get all tickers formatted as DataFrame.
        Normalizes field names to match other exchange adapters.
        """
        tickers = self.get_tickers(quote_currency)

        if not tickers:
            return pd.DataFrame()

        df = pd.DataFrame(tickers)

        # Normalize column names to match other exchanges
        # Coinone returns: quote_currency, target_currency, timestamp, high, low, first, last,
        #                  quote_volume, target_volume, best_asks, best_bids, id
        df['quote_currency'] = df['quote_currency'].str.upper()
        df['target_currency'] = df['target_currency'].str.upper()

        # Create symbol in format: BTC_KRW (matching Bithumb pattern)
        df['symbol'] = df['target_currency'] + '_' + df['quote_currency']
        df['base_asset'] = df['target_currency']
        df['quote_asset'] = df['quote_currency']

        # Rename price/volume fields
        df = df.rename(columns={
            'last': 'lastPrice',
            'quote_volume': 'atp24h',  # 24h volume in quote currency (KRW)
            'high': 'highPrice',
            'low': 'lowPrice',
            'first': 'openPrice',
            'target_volume': 'volume'
        })

        # Convert numeric columns
        numeric_columns = ['lastPrice', 'atp24h', 'highPrice', 'lowPrice', 'openPrice', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def spot_exchange_info(self, quote_currency="KRW"):
        """
        Get exchange info (markets) formatted as DataFrame.
        """
        markets = self.get_markets(quote_currency)

        if not markets:
            return pd.DataFrame()

        df = pd.DataFrame(markets)

        # Normalize to match other exchanges
        df['quote_currency'] = df['quote_currency'].str.upper()
        df['target_currency'] = df['target_currency'].str.upper()
        df['symbol'] = df['target_currency'] + '_' + df['quote_currency']
        df['base_asset'] = df['target_currency']
        df['quote_asset'] = df['quote_currency']

        return df

    def wallet_status(self):
        """
        Get wallet status (deposit/withdrawal availability) for all currencies.
        Returns DataFrame with columns: asset, network_type, deposit, withdraw
        """
        currencies = self.get_currencies()

        if not currencies:
            return pd.DataFrame()

        df = pd.DataFrame(currencies)

        # Normalize to match other exchanges
        df = df.rename(columns={
            'symbol': 'asset',
        })

        # Convert status strings to booleans
        # Coinone uses: "normal" = available, "suspended" = not available
        df['deposit'] = df['deposit_status'].apply(lambda x: x == 'normal')
        df['withdraw'] = df['withdraw_status'].apply(lambda x: x == 'normal')

        # Network type - Coinone doesn't provide this in the currencies endpoint
        # Default to asset name (can be enhanced later if needed)
        df['network_type'] = df['asset']

        return df[['asset', 'network_type', 'deposit', 'withdraw']]


class InitCoinoneAdaptor:
    """
    High-level Coinone adaptor following the same pattern as other exchange adaptors.
    Used by info_core.py for data fetching.
    """
    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        self.my_client = Coinone(my_access_key, my_secret_key)
        self.pub_client = Coinone()
        self.coinone_plug_logger = InfoCoreLogger("coinone_plug", logging_dir).logger
        self.coinone_plug_logger.info("coinone_plug_logger started.")

    def wallet_status(self):
        """Get wallet deposit/withdrawal status for all assets."""
        return self.pub_client.wallet_status()

    def spot_all_tickers(self):
        """Get all spot tickers with normalized field names."""
        return self.pub_client.spot_all_tickers()

    def spot_exchange_info(self):
        """Get exchange info (available trading pairs)."""
        return self.pub_client.spot_exchange_info()

    def get_all_market_symbols(self):
        """
        Get list of all available target currencies (base assets).
        Used for new listing detection.
        Returns: ['BTC', 'ETH', 'XRP', ...]
        """
        markets = self.pub_client.get_markets("KRW")
        return [m['target_currency'].upper() for m in markets]
