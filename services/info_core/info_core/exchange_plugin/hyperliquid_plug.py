"""
Hyperliquid Exchange Plugin

Hyperliquid is a decentralized perpetual futures exchange.
All perpetuals are USDC-settled.

API Documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api

Key differences from CEX:
- No API keys required for public data
- Single POST endpoint (https://api.hyperliquid.xyz/info) with 'type' parameter
- Symbols are just coin names (BTC, ETH) - need to append _USDC for system format
- Weight-based rate limiting (1200 weight/minute)
"""

import os
import sys
import datetime
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import time
import traceback
import requests
import _pickle as pickle

from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper


class Hyperliquid:
    """
    Low-level Hyperliquid API client for perpetual futures.

    API Documentation: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api
    Base URL: https://api.hyperliquid.xyz

    All requests are POST to /info endpoint with 'type' parameter.
    """

    def __init__(self, wallet_address=None):
        """
        Initialize Hyperliquid client.

        Args:
            wallet_address: Optional wallet address (0x...) for user-specific queries.
                           Not needed for public market data.
        """
        self.wallet_address = wallet_address
        self.base_url = "https://api.hyperliquid.xyz"
        self.headers = {
            "Content-Type": "application/json"
        }

    def _post_info(self, request_type: str, timeout=10, **kwargs) -> dict:
        """
        Make POST request to /info endpoint.

        Args:
            request_type: The 'type' parameter for the request
            timeout: Request timeout in seconds
            **kwargs: Additional parameters to include in request body

        Returns:
            Response JSON as dict or list
        """
        url = f"{self.base_url}/info"
        payload = {"type": request_type, **kwargs}

        try:
            response = requests.post(url, json=payload, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Hyperliquid API request failed: {e}")

    def get_meta(self) -> dict:
        """
        Get perpetuals metadata.

        Endpoint: POST /info {"type": "meta"}

        Returns metadata including universe (list of available assets).
        """
        return self._post_info("meta")

    def get_meta_and_asset_ctxs(self) -> list:
        """
        Get metadata and asset contexts (prices, funding, OI).

        Endpoint: POST /info {"type": "metaAndAssetCtxs"}

        Returns list of [meta, assetCtxs] where assetCtxs contains:
        - markPx: Mark price
        - oraclePx: Oracle/index price
        - funding: Current funding rate
        - openInterest: Open interest
        - dayNtlVlm: 24h notional volume
        - prevDayPx: Previous day close price
        """
        return self._post_info("metaAndAssetCtxs")

    def get_all_mids(self) -> dict:
        """
        Get mid prices for all coins.

        Endpoint: POST /info {"type": "allMids"}

        Returns dict mapping coin name to mid price string.
        """
        return self._post_info("allMids")

    def get_l2_book(self, coin: str) -> dict:
        """
        Get L2 order book for a coin.

        Endpoint: POST /info {"type": "l2Book", "coin": "BTC"}

        Args:
            coin: Coin name (e.g., "BTC", "ETH")

        Returns order book with bids and asks (max 20 levels each).
        """
        return self._post_info("l2Book", coin=coin)

    def get_predicted_fundings(self) -> list:
        """
        Get predicted funding rates for all assets.

        Endpoint: POST /info {"type": "predictedFundings"}

        Returns list of funding predictions with rate and next funding time.
        """
        return self._post_info("predictedFundings")

    def get_funding_history(self, coin: str, start_time: int, end_time: int = None) -> list:
        """
        Get historical funding rates.

        Args:
            coin: Coin name (e.g., "BTC")
            start_time: Start time in milliseconds
            end_time: End time in milliseconds (optional)

        Returns list of historical funding payments.
        """
        params = {"coin": coin, "startTime": start_time}
        if end_time:
            params["endTime"] = end_time
        return self._post_info("fundingHistory", **params)


class InitHyperliquidAdaptor:
    """
    High-level Hyperliquid adaptor matching the pattern of other exchange adaptors.

    Provides normalized DataFrame outputs compatible with the info_core system.

    Note: Hyperliquid uses USDC as quote currency for all perpetuals.
    Symbol format conversion: "BTC" -> "BTC_USDC"
    """

    def __init__(self, logging_dir=None):
        """
        Initialize Hyperliquid adaptor.

        No API keys needed for public data (DEX).
        """
        self.pub_client = Hyperliquid()
        self.local_redis = RedisHelper()
        self.hyperliquid_plug_logger = InfoCoreLogger("hyperliquid_plug", logging_dir).logger
        self.hyperliquid_plug_logger.info("hyperliquid_plug_logger started.")

    @staticmethod
    def _coin_to_symbol(coin: str) -> str:
        """Convert Hyperliquid coin name to system symbol format."""
        return f"{coin}_USDC"

    @staticmethod
    def _symbol_to_coin(symbol: str) -> str:
        """Convert system symbol format to Hyperliquid coin name."""
        return symbol.replace("_USDC", "").replace("_USDT", "")

    def usd_m_exchange_info(self) -> pd.DataFrame:
        """
        Get USDC-margined perpetuals exchange info.

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDC)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDC)
        - perpetual: Boolean (True for perpetual contracts)
        - max_leverage: Maximum leverage allowed
        """
        try:
            meta = self.pub_client.get_meta()

            if not meta or "universe" not in meta:
                self.hyperliquid_plug_logger.error("usd_m_exchange_info: No universe data in meta response")
                return pd.DataFrame()

            universe = meta["universe"]

            records = []
            for asset in universe:
                name = asset.get("name", "")
                if not name:
                    continue

                records.append({
                    "symbol": self._coin_to_symbol(name),
                    "base_asset": name,
                    "quote_asset": "USDC",
                    "perpetual": True,  # Hyperliquid only has perpetuals
                    "max_leverage": asset.get("maxLeverage", 50),
                    "sz_decimals": asset.get("szDecimals", 0),
                })

            df = pd.DataFrame(records)
            self.hyperliquid_plug_logger.info(f"usd_m_exchange_info: Found {len(df)} perpetual contracts")
            return df

        except Exception as e:
            self.hyperliquid_plug_logger.error(f"usd_m_exchange_info error: {e}, {traceback.format_exc()}")
            return pd.DataFrame()

    def usd_m_all_tickers(self) -> pd.DataFrame:
        """
        Get all USDC-margined perpetuals tickers with atp24h calculation.

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDC)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDC)
        - lastPrice: Last/mark price
        - atp24h: 24h trading volume in USDC (for ranking)
        - priceChangePercent: 24h price change percentage
        - markPrice: Mark price
        - indexPrice: Oracle/index price
        - funding_rate: Current funding rate
        - openInterest: Open interest
        """
        try:
            data = self.pub_client.get_meta_and_asset_ctxs()

            if not data or len(data) < 2:
                self.hyperliquid_plug_logger.error("usd_m_all_tickers: Invalid metaAndAssetCtxs response")
                return pd.DataFrame()

            meta = data[0]
            asset_ctxs = data[1]

            if "universe" not in meta:
                self.hyperliquid_plug_logger.error("usd_m_all_tickers: No universe in meta")
                return pd.DataFrame()

            universe = meta["universe"]

            if len(universe) != len(asset_ctxs):
                self.hyperliquid_plug_logger.warning(
                    f"usd_m_all_tickers: universe ({len(universe)}) and assetCtxs ({len(asset_ctxs)}) length mismatch"
                )

            records = []
            for i, asset in enumerate(universe):
                if i >= len(asset_ctxs):
                    break

                name = asset.get("name", "")
                if not name:
                    continue

                ctx = asset_ctxs[i]

                # Parse prices
                mark_px = float(ctx.get("markPx", 0))
                oracle_px = float(ctx.get("oraclePx", 0))
                prev_day_px = float(ctx.get("prevDayPx", 0))

                # Calculate price change percentage
                if prev_day_px > 0:
                    price_change_pct = ((mark_px - prev_day_px) / prev_day_px) * 100
                else:
                    price_change_pct = 0.0

                # 24h notional volume is in USDC
                day_ntl_vlm = float(ctx.get("dayNtlVlm", 0))

                records.append({
                    "symbol": self._coin_to_symbol(name),
                    "base_asset": name,
                    "quote_asset": "USDC",
                    "lastPrice": mark_px,
                    "markPrice": mark_px,
                    "indexPrice": oracle_px,
                    "priceChangePercent": price_change_pct,
                    "atp24h": day_ntl_vlm,
                    "funding_rate": float(ctx.get("funding", 0)),
                    "openInterest": float(ctx.get("openInterest", 0)),
                })

            df = pd.DataFrame(records)
            self.hyperliquid_plug_logger.debug(f"usd_m_all_tickers: Got {len(df)} tickers")
            return df

        except Exception as e:
            self.hyperliquid_plug_logger.error(f"usd_m_all_tickers error: {e}, {traceback.format_exc()}")
            return pd.DataFrame()

    def get_fundingrate(self, futures_type="USD_M") -> pd.DataFrame:
        """
        Get funding rate data for perpetual contracts.

        Args:
            futures_type: "USD_M" for USDC-margined futures

        Returns DataFrame with columns:
        - symbol: Contract name (BTC_USDC)
        - base_asset: Base currency (BTC)
        - quote_asset: Quote currency (USDC)
        - funding_rate: Current funding rate as float
        - funding_time: Next funding timestamp as datetime
        - perpetual: Boolean (True for perpetual contracts)

        Note: Hyperliquid has hourly funding (every hour on the hour).
        """
        if futures_type != "USD_M":
            return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

        try:
            # Get ticker data which includes funding rates
            ticker_df = self.usd_m_all_tickers()

            if ticker_df.empty:
                self.hyperliquid_plug_logger.warning("get_fundingrate: usd_m_all_tickers() returned empty DataFrame")
                return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

            # Select funding-related columns
            result_df = ticker_df[["symbol", "base_asset", "quote_asset"]].copy()

            # Add funding rate
            if "funding_rate" in ticker_df.columns:
                result_df["funding_rate"] = ticker_df["funding_rate"].astype(float)
            else:
                result_df["funding_rate"] = 0.0

            # Calculate next funding time (Hyperliquid has hourly funding)
            now = datetime.datetime.utcnow()
            # Next hour on the hour
            next_funding = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
            result_df["funding_time"] = next_funding

            # Hyperliquid has hourly funding (1 hour intervals)
            result_df["funding_interval_hours"] = 1

            # All Hyperliquid contracts are perpetual
            result_df["perpetual"] = True

            return result_df

        except Exception as e:
            self.hyperliquid_plug_logger.error(f"get_fundingrate error: {e}, {traceback.format_exc()}")
            return pd.DataFrame(columns=['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual'])

    def get_orderbook(self, symbol: str) -> dict:
        """
        Get order book for a symbol.

        Args:
            symbol: System format symbol (BTC_USDC)

        Returns dict with best bid/ask prices and quantities.
        """
        try:
            coin = self._symbol_to_coin(symbol)
            book = self.pub_client.get_l2_book(coin)

            if not book or "levels" not in book:
                return {"bid_price": 0, "ask_price": 0, "bid_qty": 0, "ask_qty": 0}

            levels = book["levels"]

            # levels[0] = bids (sorted desc by price)
            # levels[1] = asks (sorted asc by price)
            bids = levels[0] if len(levels) > 0 else []
            asks = levels[1] if len(levels) > 1 else []

            best_bid = bids[0] if bids else {"px": "0", "sz": "0"}
            best_ask = asks[0] if asks else {"px": "0", "sz": "0"}

            return {
                "bid_price": float(best_bid.get("px", 0)),
                "ask_price": float(best_ask.get("px", 0)),
                "bid_qty": float(best_bid.get("sz", 0)),
                "ask_qty": float(best_ask.get("sz", 0)),
            }

        except Exception as e:
            self.hyperliquid_plug_logger.error(f"get_orderbook error for {symbol}: {e}")
            return {"bid_price": 0, "ask_price": 0, "bid_qty": 0, "ask_qty": 0}

    def get_all_orderbooks(self, symbols: list = None) -> pd.DataFrame:
        """
        Get order books for multiple symbols via REST API.

        This is a fallback method - prefer WebSocket for real-time data.

        Args:
            symbols: List of system format symbols. If None, gets all from exchange info.

        Returns DataFrame with best bid/ask for each symbol.
        """
        try:
            if symbols is None:
                # Get from Redis cache or fetch
                fetched_info = self.local_redis.get_data("hyperliquid_usd_m_info_df")
                if fetched_info:
                    info_df = pickle.loads(fetched_info)
                    symbols = info_df["symbol"].tolist()
                else:
                    info_df = self.usd_m_exchange_info()
                    symbols = info_df["symbol"].tolist()

            records = []
            for symbol in symbols:
                book = self.get_orderbook(symbol)
                records.append({
                    "symbol": symbol,
                    "bp": book["bid_price"],
                    "ap": book["ask_price"],
                    "bq": book["bid_qty"],
                    "aq": book["ask_qty"],
                })
                time.sleep(0.05)  # Rate limiting

            return pd.DataFrame(records)

        except Exception as e:
            self.hyperliquid_plug_logger.error(f"get_all_orderbooks error: {e}, {traceback.format_exc()}")
            return pd.DataFrame()
