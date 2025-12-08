import os
import sys
import datetime
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import time
import traceback
import requests
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper


class Gate:
    """
    Low-level Gate.io API client for USDT-margined futures.

    API Documentation: https://www.gate.com/docs/developers/apiv4/
    Base URL: https://api.gateio.ws/api/v4
    """

    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = "https://api.gateio.ws/api/v4"
        self.futures_url = f"{self.base_url}/futures"

    def _request(self, method, endpoint, params=None, timeout=10):
        """Make HTTP request to Gate.io API."""
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=timeout)
            else:
                response = requests.request(method, url, params=params, headers=headers, timeout=timeout)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Gate.io API request failed: {e}")

    def usd_m_exchange_info(self):
        """
        Get all USDT-margined futures contracts.

        Endpoint: GET /futures/usdt/contracts

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDT)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDT)
        - perpetual: Boolean (True for perpetual contracts)
        - funding_next_apply: Unix timestamp (seconds) for next funding time
        - funding_interval: Funding interval in seconds (e.g., 28800 for 8 hours)
        - status: Trading status
        """
        data = self._request("GET", "/futures/usdt/contracts")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Rename 'name' to 'symbol' (e.g., BTC_USDT)
        df = df.rename(columns={"name": "symbol"})

        # Extract base_asset from symbol (BTC_USDT -> BTC)
        # Gate.io uses format: BASE_QUOTE (e.g., BTC_USDT, ETH_USDT)
        df["base_asset"] = df["symbol"].apply(lambda x: x.split("_")[0] if "_" in x else x)

        # Add quote_asset (all USDT-margined contracts use USDT)
        df["quote_asset"] = "USDT"

        # Convert type to perpetual boolean
        # Gate.io uses "direct" for perpetual, "inverse" for inverse perpetual
        if "type" in df.columns:
            df["perpetual"] = df["type"].apply(lambda x: x == "direct")
        else:
            df["perpetual"] = True  # Default to perpetual if type field missing

        # Convert funding_next_apply to numeric (Unix timestamp in seconds)
        if "funding_next_apply" in df.columns:
            df["funding_next_apply"] = pd.to_numeric(df["funding_next_apply"], errors='coerce')

        # Convert funding_interval to numeric
        if "funding_interval" in df.columns:
            df["funding_interval"] = pd.to_numeric(df["funding_interval"], errors='coerce')

        # Filter only trading contracts
        if "in_delisting" in df.columns:
            df = df[df["in_delisting"] == False]

        return df

    def all_tickers(self, settle="usdt"):
        """
        Get all futures tickers.

        Endpoint: GET /futures/{settle}/tickers

        Returns DataFrame with ticker data including last price, volume, funding rate.
        """
        data = self._request("GET", f"/futures/{settle}/tickers")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)

        # Rename columns to match internal format
        df = df.rename(columns={
            "contract": "symbol",           # BTC_USDT
            "last": "lastPrice",            # Last trade price
            "volume_24h_settle": "turnover24h",  # 24h volume in settle currency
            "volume_24h": "volume24h",      # 24h volume in contracts
            "high_24h": "highPrice",        # 24h high
            "low_24h": "lowPrice",          # 24h low
            "change_percentage": "priceChangePercent",  # 24h change %
        })

        # Convert string values to float
        numeric_columns = ["lastPrice", "turnover24h", "volume24h", "highPrice", "lowPrice",
                          "priceChangePercent", "index_price", "mark_price", "funding_rate"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def get_funding_rate(self, settle="usdt"):
        """
        Get funding rates from tickers (Gate.io includes funding rate in ticker data).

        Returns DataFrame with funding rate information.
        """
        return self.all_tickers(settle)


class InitGateAdaptor:
    """
    High-level Gate.io adaptor matching the pattern of other exchange adaptors.

    Provides normalized DataFrame outputs compatible with the info_core system.
    """

    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        self.my_client = Gate(my_access_key, my_secret_key)
        self.pub_client = Gate()  # Public client without authentication
        self.local_redis = RedisHelper()
        self.gate_plug_logger = InfoCoreLogger("gate_plug", logging_dir).logger
        self.gate_plug_logger.info("gate_plug_logger started.")

    def usd_m_exchange_info(self):
        """
        Get USDT-margined futures exchange info.

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDT)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDT)
        - perpetual: Boolean (True for perpetual contracts)
        """
        return self.pub_client.usd_m_exchange_info()

    def usd_m_all_tickers(self):
        """
        Get all USDT-margined futures tickers with atp24h calculation.

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDT)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDT)
        - lastPrice: Last trade price
        - atp24h: 24h trading volume in USDT (for ranking)
        """
        ticker_df = self.pub_client.all_tickers(settle="usdt")

        if ticker_df.empty:
            return ticker_df

        # Load gate_usd_m_info_df from Redis
        fetched_gate_usd_m_info_df = self.local_redis.get_data("gate_usd_m_info_df")
        if fetched_gate_usd_m_info_df is None:
            info_df = self.usd_m_exchange_info()
            self.gate_plug_logger.info("fetched_gate_usd_m_info_df is None, Fetched from API")
        else:
            info_df = pickle.loads(fetched_gate_usd_m_info_df)

        # Merge ticker with info to get base_asset and quote_asset
        merged_df = ticker_df.merge(
            info_df[["symbol", "base_asset", "quote_asset"]],
            on="symbol",
            how="inner"
        )

        if merged_df.empty:
            self.gate_plug_logger.warning(f"usd_m_all_tickers: merge resulted in empty DataFrame. ticker_df has {len(ticker_df)} rows, info_df has {len(info_df)} rows")
            # Log sample symbols for debugging
            if len(ticker_df) > 0 and len(info_df) > 0:
                ticker_symbols = ticker_df['symbol'].head(3).tolist() if 'symbol' in ticker_df.columns else []
                info_symbols = info_df['symbol'].head(3).tolist() if 'symbol' in info_df.columns else []
                self.gate_plug_logger.warning(f"Sample ticker symbols: {ticker_symbols}, Sample info symbols: {info_symbols}")

        # Calculate atp24h (24h trading volume in USDT)
        # For USDT-margined futures, turnover24h is already in USDT
        if "turnover24h" in merged_df.columns:
            merged_df["atp24h"] = merged_df["turnover24h"]
        else:
            # Fallback: calculate from volume and price
            merged_df["atp24h"] = merged_df["volume24h"] * merged_df["lastPrice"]

        return merged_df

    def get_fundingrate(self, futures_type="USD_M"):
        """
        Get funding rate data for futures contracts.

        Args:
            futures_type: "USD_M" for USDT-margined futures

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDT)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDT)
        - funding_rate: Current funding rate as float
        - funding_time: Next funding timestamp as datetime
        - perpetual: Boolean (True for perpetual contracts)

        Note: funding_rate comes from tickers API, but funding_next_apply comes
        from contracts API (similar to how Bybit embeds both in tickers).
        """
        if futures_type != "USD_M":
            # Gate.io only supports USDT-margined futures, return empty DataFrame for COIN_M
            # This matches the behavior of other exchanges that return empty data for unsupported types
            return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

        # Get ticker data (includes funding_rate but NOT funding_next_apply)
        ticker_df = self.usd_m_all_tickers()

        if ticker_df.empty:
            self.gate_plug_logger.warning("get_fundingrate: usd_m_all_tickers() returned empty DataFrame")
            return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

        # Load contracts info (includes funding_next_apply, perpetual flag)
        # This is critical: funding_next_apply is in contracts endpoint, not tickers
        fetched_gate_usd_m_info_df = self.local_redis.get_data("gate_usd_m_info_df")
        if fetched_gate_usd_m_info_df is None:
            info_df = self.usd_m_exchange_info()
            self.gate_plug_logger.info("fetched_gate_usd_m_info_df is None, Fetched from API")
        else:
            info_df = pickle.loads(fetched_gate_usd_m_info_df)

        # Merge ticker with contracts info to get perpetual and funding_next_apply
        # Columns from info_df: symbol, perpetual, funding_next_apply
        merge_columns = ["symbol", "perpetual"]
        if "funding_next_apply" in info_df.columns:
            merge_columns.append("funding_next_apply")

        funding_df = ticker_df.merge(
            info_df[merge_columns],
            on="symbol",
            how="inner"
        )

        if funding_df.empty:
            self.gate_plug_logger.warning(f"get_fundingrate: merge resulted in empty DataFrame. ticker_df has {len(ticker_df)} rows, info_df has {len(info_df)} rows")
            return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

        # Select and rename columns for funding rate output
        result_df = funding_df[["symbol", "base_asset", "quote_asset"]].copy()

        # Add funding rate (from ticker data)
        if "funding_rate" in funding_df.columns:
            result_df["funding_rate"] = funding_df["funding_rate"].astype(float)
        else:
            result_df["funding_rate"] = 0.0

        # Add funding time (from contracts data via merge)
        # funding_next_apply is Unix timestamp in seconds (not milliseconds like Binance/Bybit)
        if "funding_next_apply" in funding_df.columns:
            result_df["funding_time"] = pd.to_datetime(
                funding_df["funding_next_apply"],
                unit="s",
                utc=True
            ).dt.tz_localize(None)
        else:
            # Fallback: Default to next 8-hour interval (should not happen if API is working)
            self.gate_plug_logger.warning("funding_next_apply not found in contracts data, using fallback calculation")
            now = datetime.datetime.utcnow()
            # Gate.io has 8-hour funding intervals at 00:00, 08:00, 16:00 UTC
            hours_until_next = 8 - (now.hour % 8)
            if hours_until_next == 8:
                hours_until_next = 0
            next_funding = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=hours_until_next)
            result_df["funding_time"] = next_funding

        # Add perpetual flag (from contracts data via merge)
        result_df["perpetual"] = funding_df["perpetual"]

        return result_df
