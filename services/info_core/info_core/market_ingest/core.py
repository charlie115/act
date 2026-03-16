import os
import pandas as pd
# from price_websocket import dict_convert, update_dollar, price_websocket
from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_plugin.bithumb_plug import InitBithumbAdaptor
from exchange_plugin.bybit_plug import InitBybitAdaptor
from exchange_plugin.gate_plug import InitGateAdaptor
from exchange_plugin.coinone_plug import InitCoinoneAdaptor
from exchange_plugin.hyperliquid_plug import InitHyperliquidAdaptor
from exchange_websocket.binance_websocket import BinanceWebsocket, BinanceUSDMWebsocket, BinanceCOINMWebsocket
from exchange_websocket.upbit_websocket import UpbitWebsocket
from exchange_websocket.okx_websocket import OkxWebsocket, OkxUSDMWebsocket, OkxCOINMWebsocket
from exchange_websocket.bithumb_websocket import BithumbWebsocket
from exchange_websocket.bybit_websocket import BybitWebsocket, BybitUSDMWebsocket, BybitCOINMWebsocket
from exchange_websocket.gate_websocket import GateWebsocket, GateUSDMWebsocket
from exchange_websocket.coinone_websocket import CoinoneWebsocket
from exchange_websocket.hyperliquid_websocket import HyperliquidWebsocket, HyperliquidUSDMWebsocket
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from etc.db_handler.mongodb_client import InitDBClient
import _pickle as pickle
from threading import Lock, Thread
import time
import datetime
import os
import traceback
from functools import partial
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.price_df_generator import get_price_df
from standalone_func.premium_data_generator import (
    build_premium_cache_metadata,
    get_premium_df,
    get_premium_df_from_market_snapshots,
    store_premium_df,
)
from standalone_func.funding_wallet_common import store_latest_funding_snapshot
from standalone_func.store_exchange_status import fetch_market_servercheck
import requests

current_file_dir = os.path.realpath(__file__)
current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
logging_dir = f"{current_folder_dir}/loggers/logs/"
MARKET_STATE_VERSION_PREFIX = "MARKET_STATE_VERSION"
CONVERT_RATE_VERSION_PREFIX = "CONVERT_RATE_VERSION"

class MarketIngestRuntime:
    def __init__(self,
                 logging_dir,
                 authoritative_reference_publisher,
                 proc_n,
                 node,
                 admin_id,
                 acw_api,
                 exchange_api_key_dict,
                 enabled_market_klines,
                 mongodb_dict,
                 redis_dict):
        # Inital value setting
        self.logger = InfoCoreLogger("info_core", logging_dir).logger
        self.price_websocket_logger = InfoCoreLogger("price_websocket", logging_dir).logger
        self.update_dollar_logger = InfoCoreLogger("update_dollar", logging_dir).logger
        self.logging_dir = logging_dir
        self.node = node
        self.admin_id = admin_id
        self.proc_n = proc_n
        self.authoritative_reference_publisher = authoritative_reference_publisher
        self.monitor_websocket_switch = True
        self.exclude_outliers = True
        self.acw_api = acw_api
        self.exchange_api_key_dict = exchange_api_key_dict
        self.enabled_market_klines = enabled_market_klines
        self.enabled_websocket_list = self.generate_enabled_websocket_list()
        self.enabled_markets_dict = self.generate_enabled_market_code_dict()
        self.mongodb_dict = mongodb_dict
        self.upbit_symbols_to_exclude = []
        self.binance_usd_m_symbols_to_exclude = []
        # For redis connesction
        self.redis_dict = redis_dict
        self.remote_redis = RedisHelper(**self.redis_dict)
        self.local_redis = RedisHelper()
        self.local_redis.fallback_redis_client = self.remote_redis
        self.logger.info(f"MarketIngestRuntime|initiated with proc_n={proc_n}")

        self.update_dollar_return_dict = {}
        self.update_dollar_thread = Thread(target=self.fetch_dollar_loop, args=(self.update_dollar_logger,), daemon=True)
        self.update_dollar_thread.start()

        self.info_thread_dict = {}
        self.premium_cache_thread_dict = {}
        self.latest_funding_thread_dict = {}
        self.market_price_df_cache = {}
        self.market_price_df_cache_lock = Lock()
        self.premium_cache_signature_dict = {}

        self.okx_adaptor = InitOkxAdaptor(self.exchange_api_key_dict['okx_read_only']['api_key'], self.exchange_api_key_dict['okx_read_only']['secret_key'], self.exchange_api_key_dict['okx_read_only']['passphrase'], logging_dir=self.logging_dir)
        self.upbit_adaptor = InitUpbitAdaptor(self.exchange_api_key_dict['upbit_read_only']['api_key'], self.exchange_api_key_dict['upbit_read_only']['secret_key'], self.logging_dir)
        self.binance_adaptor = InitBinanceAdaptor(self.exchange_api_key_dict['binance_read_only']['api_key'], self.exchange_api_key_dict['binance_read_only']['secret_key'], logging_dir=self.logging_dir)
        self.bithumb_adaptor = InitBithumbAdaptor(logging_dir=self.logging_dir)
        self.bybit_adaptor = InitBybitAdaptor(self.exchange_api_key_dict['bybit_read_only']['api_key'], self.exchange_api_key_dict['bybit_read_only']['secret_key'], self.logging_dir)
        self.gate_adaptor = InitGateAdaptor(
            self.exchange_api_key_dict.get('gate_read_only', {}).get('api_key'),
            self.exchange_api_key_dict.get('gate_read_only', {}).get('secret_key'),
            self.logging_dir
        )
        self.coinone_adaptor = InitCoinoneAdaptor(
            self.exchange_api_key_dict.get('coinone_read_only', {}).get('api_key'),
            self.exchange_api_key_dict.get('coinone_read_only', {}).get('secret_key'),
            self.logging_dir
        )
        # Hyperliquid (DEX) - no API keys required for public data
        self.hyperliquid_adaptor = InitHyperliquidAdaptor(
            self.logging_dir
        )

        # Initiate Fetching USDT from Bithumb
        self.update_usdt_thread = Thread(target=self.fetch_usdt_loop, daemon=True)
        self.update_usdt_thread.start()

        # UPBIT SPOT (KRW, BTC Market)
        # UPBIT wallet status
        # BINANCE SPOT, USD-M Futures, COIN-M Futures
        self.total_data_name_list = [
            "upbit_spot_info_df",
            "upbit_spot_ticker_df",
            "binance_spot_ticker_df",
            "binance_spot_info_df",
            "binance_usd_m_ticker_df",
            "binance_usd_m_info_df",
            "binance_coin_m_ticker_df",
            "binance_coin_m_info_df",
            "okx_spot_ticker_df",
            "okx_spot_info_df",
            "okx_usd_m_ticker_df",
            "okx_usd_m_info_df",
            "okx_coin_m_ticker_df",
            "okx_coin_m_info_df",
            "bithumb_spot_info_df",
            "bithumb_spot_ticker_df",
            "bybit_spot_info_df",
            "bybit_spot_ticker_df",
            "bybit_usd_m_info_df",
            "bybit_usd_m_ticker_df",
            "bybit_coin_m_info_df",
            "bybit_coin_m_ticker_df",
            "gate_usd_m_info_df",
            "gate_usd_m_ticker_df",
            "coinone_spot_info_df",
            "coinone_spot_ticker_df",
            "hyperliquid_usd_m_info_df",
            "hyperliquid_usd_m_ticker_df"
        ]
        
        # Remove all info data from the local redis
        for data_name in self.total_data_name_list:
            self.local_redis.delete_key(data_name)

        self.enabled_data_name_list = self.get_enabled_data_name_list()

        for data_name in self.enabled_data_name_list:
            if 'okx' in data_name:
                self.info_thread_dict[f"update_{data_name}"] = Thread(target=self.update_exchange_info_as_df, args=(data_name, 3), daemon=True)
            else:
                self.info_thread_dict[f"update_{data_name}"] = Thread(target=self.update_exchange_info_as_df, args=(data_name,), daemon=True)
            self.info_thread_dict[f"update_{data_name}"].start()
            self.logger.info(f"InitCore|update_{data_name} thread has started.")

        # Wait until all info df has been updated
        while True:
            all_data_exists = True
            for data_name in self.enabled_data_name_list:
                if self.local_redis.get_data(data_name) is None:
                    all_data_exists = False
                    break
            
            if all_data_exists:
                self.logger.info(f"InitCore|All info df has been updated.")
                break
            else:
                self.logger.info(f"InitCore|Waiting for all info to be updated.")
                # log the missing data
                for data_name in self.enabled_data_name_list:
                    if self.local_redis.get_data(data_name) is None:
                        self.logger.info(f"InitCore|{data_name} is not updated.")
                time.sleep(2)

        self.exchange_websocket_dict = {}
        for enabled_websocket_name in self.enabled_websocket_list:
            if enabled_websocket_name == "UPBIT_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = UpbitWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, self.logging_dir)
            elif enabled_websocket_name == "BITHUMB_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = BithumbWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, self.logging_dir)
            elif enabled_websocket_name == "BINANCE_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = BinanceWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "SPOT", logging_dir)
            elif enabled_websocket_name == "BINANCE_USD_M":
                self.exchange_websocket_dict[enabled_websocket_name] = BinanceUSDMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "USD_M", logging_dir)
            elif enabled_websocket_name == "BINANCE_COIN_M":
                self.exchange_websocket_dict[enabled_websocket_name] = BinanceCOINMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "COIN_M", logging_dir)
            elif enabled_websocket_name == "OKX_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = OkxWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "SPOT", logging_dir)
            elif enabled_websocket_name == "OKX_USD_M":
                self.exchange_websocket_dict[enabled_websocket_name] = OkxUSDMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "USD_M", logging_dir)
            elif enabled_websocket_name == "OKX_COIN_M":
                self.exchange_websocket_dict[enabled_websocket_name] = OkxCOINMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "COIN_M", logging_dir)
            elif enabled_websocket_name == "BYBIT_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = BybitWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "SPOT", logging_dir)
            elif enabled_websocket_name == "BYBIT_USD_M":
                self.exchange_websocket_dict[enabled_websocket_name] = BybitUSDMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "USD_M", logging_dir)
            elif enabled_websocket_name == "BYBIT_COIN_M":
                self.exchange_websocket_dict[enabled_websocket_name] = BybitCOINMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "COIN_M", logging_dir)
            elif enabled_websocket_name == "GATE_USD_M":
                self.exchange_websocket_dict[enabled_websocket_name] = GateUSDMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, "USD_M", logging_dir)
            elif enabled_websocket_name == "COINONE_SPOT":
                self.exchange_websocket_dict[enabled_websocket_name] = CoinoneWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, logging_dir)
            elif enabled_websocket_name == "HYPERLIQUID_USD_M":
                self.exchange_websocket_dict[enabled_websocket_name] = HyperliquidUSDMWebsocket(self.admin_id, self.node, self.proc_n, partial(self.get_symbol_list, enabled_websocket_name), self.acw_api, logging_dir)
            else:
                self.logger.error(f"InitCore|{enabled_websocket_name} is not valid.")
                self.acw_api.create_message_thread(self.admin_id, f"InitCore|{enabled_websocket_name} is not valid.", f"InitCore|{enabled_websocket_name} is not valid.")
                break

        self.logger.info(f"MarketIngestRuntime|exchange_websocket_dict, {self.exchange_websocket_dict.keys()} has been initiated.")
        time.sleep(10)

        # Loading convert rate
        self.convert_rate_initialized = False
        self.update_convert_rate_dict_thread = Thread(target=self.update_convert_rate_dict, daemon=True)
        self.update_convert_rate_dict_thread.start()
        while self.convert_rate_initialized is False:
            time.sleep(0.2)
        self.start_premium_cache_workers()
        self.start_latest_funding_workers()

    def generate_enabled_websocket_list(self):
        market_list = []
        for each_market_combi in self.enabled_market_klines:
            market_code1, market_code2 = each_market_combi.split(':')
            market_list.append(market_code1.split('/')[0])
            market_list.append(market_code2.split('/')[0])
        market_list = list(set(market_list))
        return market_list
    
    def generate_enabled_market_code_dict(self):
        organized_markets = {}

        def add_market_product(market, product_type, product):
            if market not in organized_markets:
                organized_markets[market] = {"SPOT": [], "USD_M": {"PERPETUAL": [], "FUTURES": []}, "COIN_M": {"PERPETUAL": [], "FUTURES": []}}
            
            if product_type == "SPOT":
                if product not in organized_markets[market]["SPOT"]:
                    organized_markets[market]["SPOT"].append(product)
            elif product_type in ["USD_M", "COIN_M"]:
                if product not in organized_markets[market][product_type]["PERPETUAL"]:
                    organized_markets[market][product_type]["PERPETUAL"].append(product)

        # Process each entry in the enabled_market_klines
        for entry in self.enabled_market_klines:
            pairs = entry.split(":")
            for pair in pairs:
                market, quote_asset = pair.split("/")
                # Handle different market types
                if "USD_M" in market:
                    market_name = market.replace("_USD_M", "")
                    market_type = "USD_M"
                elif "COIN_M" in market:
                    market_name = market.replace("_COIN_M", "")
                    market_type = "COIN_M"
                else:
                    market_name, market_type = market.split("_")
                add_market_product(market_name, market_type, quote_asset)
        return organized_markets
    
    def get_enabled_data_name_list(self):
        enabled_data_name_list = []
        for each_market in self.enabled_websocket_list:
            for each_data_name in self.total_data_name_list:
                if each_market.lower() in each_data_name:
                    enabled_data_name_list.append(each_data_name)

        for each_market_combi in self.enabled_market_klines:
            target_market_code, origin_market_code = each_market_combi.split(":")
            for market_code in (target_market_code, origin_market_code):
                exchange_name, market_type, _ = self._parse_market_code(market_code)
                if market_type == "SPOT":
                    continue
                if not self._market_combination_requires_spot_reference(
                    target_market_code,
                    origin_market_code,
                    exchange_name,
                ):
                    continue
                spot_info = f"{exchange_name.lower()}_spot_info_df"
                spot_ticker = f"{exchange_name.lower()}_spot_ticker_df"
                if spot_info not in enabled_data_name_list and spot_info in self.total_data_name_list:
                    enabled_data_name_list.append(spot_info)
                if spot_ticker not in enabled_data_name_list and spot_ticker in self.total_data_name_list:
                    enabled_data_name_list.append(spot_ticker)
        return list(set(enabled_data_name_list))

    def _parse_market_code(self, market_code):
        market_name, quote_asset = market_code.split("/")
        normalized_quote_asset = "USDT" if quote_asset == "USD" else quote_asset
        if "USD_M" in market_name:
            exchange_name = market_name.replace("_USD_M", "")
            market_type = "USD_M"
        elif "COIN_M" in market_name:
            exchange_name = market_name.replace("_COIN_M", "")
            market_type = "COIN_M"
        else:
            exchange_name, market_type = market_name.split("_", 1)
        return exchange_name, market_type, normalized_quote_asset

    def _quotes_need_spot_reference(self, quote_asset_one, quote_asset_two):
        if quote_asset_one == quote_asset_two:
            return False
        if {quote_asset_one, quote_asset_two} == {"KRW", "USDT"}:
            return False
        return True

    def _market_combination_requires_spot_reference(
        self,
        target_market_code,
        origin_market_code,
        exchange_name,
    ):
        target_exchange, target_market_type, target_quote_asset = self._parse_market_code(target_market_code)
        origin_exchange, origin_market_type, origin_quote_asset = self._parse_market_code(origin_market_code)
        if not self._quotes_need_spot_reference(origin_quote_asset, target_quote_asset):
            return False
        if target_exchange == exchange_name and target_market_type != "SPOT":
            return True
        if origin_exchange == exchange_name and origin_market_type != "SPOT":
            return True
        return False

    def get_enabled_futures_market_codes(self):
        enabled_futures_markets = set()
        for market_code_combination in self.enabled_market_klines:
            for market_code in market_code_combination.split(":"):
                market_name = market_code.split("/")[0]
                if "SPOT" not in market_name:
                    enabled_futures_markets.add(market_code)
        return sorted(enabled_futures_markets)

    def _get_funding_adaptor(self, exchange_name):
        adaptor_map = {
            "BINANCE": self.binance_adaptor,
            "OKX": self.okx_adaptor,
            "BYBIT": self.bybit_adaptor,
            "GATE": self.gate_adaptor,
            "HYPERLIQUID": self.hyperliquid_adaptor,
        }
        return adaptor_map.get(exchange_name)

    def _fetch_latest_funding_df(self, market_code):
        market_name, quote_asset = market_code.split("/")
        exchange_name = market_name.split("_")[0]
        futures_type = "_".join(market_name.split("_")[1:])
        adaptor = self._get_funding_adaptor(exchange_name)
        if adaptor is None:
            return pd.DataFrame()

        funding_df = adaptor.get_fundingrate(futures_type)
        if funding_df.empty:
            return funding_df

        if "quote_asset" in funding_df.columns:
            funding_df = funding_df[funding_df["quote_asset"] == quote_asset]
        if "perpetual" in funding_df.columns:
            funding_df = funding_df[funding_df["perpetual"] == True]
        if funding_df.empty:
            return funding_df

        funding_df = funding_df.copy()
        funding_df["datetime_now"] = datetime.datetime.utcnow()
        return funding_df
    
    def store_info_dict_to_redis(self, data_name, fetched_df):
        # Save the data to the local redis
        self.local_redis.set_data(data_name, pickle.dumps(fetched_df))
        if data_name.endswith("_info_df") or data_name.endswith("_ticker_df"):
            market_code = data_name.replace("_info_df", "").replace("_ticker_df", "").upper()
            self.local_redis.set_data(
                f"{MARKET_STATE_VERSION_PREFIX}|{market_code}",
                str(int(time.time() * 1_000_000)),
            )

    def update_exchange_info_as_df(self, data_name, error_count_limit=1, loop_time_secs=30):
        error_count = 0
        while True:
            try:
                # Check whether the market is in maintenance or not
                server_check = False
                market_name = data_name.replace('_info_df', '').replace('_ticker_df', '').upper()
                possible_market_codes = [f"{market_name}/{quote_asset}" for quote_asset in ['BTC', 'USDT', 'KRW', 'USD']]
                for market_code in possible_market_codes:
                    server_check = fetch_market_servercheck(market_code)
                    if server_check:
                        break
                if server_check is True:
                    self.logger.info(f"update_exchange_info_as_df|name:{data_name} has been skipped due to server check.")
                    time.sleep(loop_time_secs)
                    continue
                start_time = time.time()
                if data_name == "upbit_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.upbit_adaptor.spot_exchange_info())
                elif data_name == "upbit_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.upbit_adaptor.spot_all_tickers())
                elif data_name == "upbit_wallet_status_df":
                    self.store_info_dict_to_redis(data_name, self.upbit_adaptor.wallet_status())
                elif data_name == "binance_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.binance_adaptor.spot_all_tickers())
                elif data_name == "binance_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.binance_adaptor.spot_exchange_info())
                elif data_name == "binance_usd_m_ticker_df":
                    self.store_info_dict_to_redis(
                        data_name,
                        self.binance_adaptor.usd_m_all_tickers(),
                    )
                elif data_name == "binance_usd_m_info_df":
                    self.store_info_dict_to_redis(
                        data_name,
                        self.binance_adaptor.usd_m_exchange_info(),
                    )
                elif data_name == "binance_coin_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.binance_adaptor.coin_m_all_tickers())
                elif data_name == "binance_coin_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.binance_adaptor.coin_m_exchange_info())
                elif data_name == "okx_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.spot_all_tickers())
                elif data_name == "okx_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.spot_exchange_info())
                elif data_name == "okx_usd_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.usd_m_all_tickers())
                elif data_name == "okx_usd_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.usd_m_exchange_info())
                elif data_name == "okx_coin_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.coin_m_all_tickers())
                elif data_name == "okx_coin_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.okx_adaptor.coin_m_exchange_info())
                elif data_name == "bithumb_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.bithumb_adaptor.spot_exchange_info())
                elif data_name == "bithumb_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.bithumb_adaptor.spot_all_tickers())
                elif data_name == "bithumb_wallet_status_df":
                    self.store_info_dict_to_redis(data_name, self.bithumb_adaptor.wallet_status())
                elif data_name == "bybit_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.spot_exchange_info())
                elif data_name == "bybit_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.spot_all_tickers())
                elif data_name == "bybit_usd_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.usd_m_exchange_info())
                elif data_name == "bybit_usd_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.usd_m_all_tickers())
                elif data_name == "bybit_coin_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.coin_m_exchange_info())
                elif data_name == "bybit_coin_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.bybit_adaptor.coin_m_all_tickers())
                elif data_name == "gate_usd_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.gate_adaptor.usd_m_exchange_info())
                elif data_name == "gate_usd_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.gate_adaptor.usd_m_all_tickers())
                elif data_name == "coinone_spot_info_df":
                    self.store_info_dict_to_redis(data_name, self.coinone_adaptor.spot_exchange_info())
                elif data_name == "coinone_spot_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.coinone_adaptor.spot_all_tickers())
                elif data_name == "hyperliquid_usd_m_info_df":
                    self.store_info_dict_to_redis(data_name, self.hyperliquid_adaptor.usd_m_exchange_info())
                elif data_name == "hyperliquid_usd_m_ticker_df":
                    self.store_info_dict_to_redis(data_name, self.hyperliquid_adaptor.usd_m_all_tickers())
                else:
                    self.logger.error(f"update_exchange_info_as_df|name:{data_name} is not valid.")
                    self.acw_api.create_message_thread(self.admin_id, f"update_exchange_info_as_df|name:{data_name} is not valid.", f"update_exchange_info_as_df|name:{data_name} is not valid.")
                    break
                end_time = time.time() - start_time
                self.logger.info(f"update_exchange_info_as_df|name:{data_name} has been updated. ({end_time:.2f} secs), error_count:{error_count}")
                error_count = 0
                time.sleep(loop_time_secs)
            except Exception as e:
                error_count += 1
                if error_count >= error_count_limit:
                    self.logger.error(f"update_exchange_info_as_df|name:{data_name}, {traceback.format_exc()}")
                    self.acw_api.create_message_thread(self.admin_id, f"update_exchange_info_as_df|name:{data_name} failed.", f"update_exchange_info_as_df|name:{data_name} failed.")
                time.sleep(loop_time_secs)

    def _get_enabled_quote_assets(self, exchange_name, market_type):
        market_dict = self.enabled_markets_dict.get(exchange_name, {})
        if market_type == "SPOT":
            return sorted(set(market_dict.get("SPOT", [])))
        futures_dict = market_dict.get(market_type, {})
        quote_assets = []
        for contract_type in futures_dict:
            quote_assets.extend(futures_dict.get(contract_type, []))
        return sorted(set(quote_assets))
    
    def dollar_update_thread_status(self):
        dollar_update_alive_flag = self.update_dollar_thread.is_alive()
        if dollar_update_alive_flag is True:
            dollar_update_status_str = "dollar_update_thread is alive"
            integrity_flag = True
        else:
            dollar_update_status_str = "dollar_update_thread is dead"
            integrity_flag = False
        return integrity_flag, dollar_update_status_str

    def _load_redis_df(self, key):
        """Load a pickled DataFrame from Redis, returning None if missing."""
        data = self.local_redis.get_data(key)
        if data is None:
            return None
        return pickle.loads(data)

    def get_symbol_list(self, target_market): # E.g) UPBIT_SPOT, BINANCE_SPOT, BINANCE_USD_M, BINANCE_COIN_M
        target_exchange = target_market.split('_')[0]
        target_market_type = '_'.join(target_market.split('_')[1:])

        comparing_exchanges = self.enabled_markets_dict.keys()
        comparison_list = []
        for exchange in comparing_exchanges:
            for market_type in self.enabled_markets_dict[exchange]:
                if market_type == "SPOT":
                    for quote_asset in self.enabled_markets_dict[exchange][market_type]:
                        comparison_list.append({"exchange": exchange, "market_type": market_type, "contract_type":None, "quote_asset": quote_asset})
                else:
                    for contract_type in self.enabled_markets_dict[exchange][market_type]:
                        for quote_asset in self.enabled_markets_dict[exchange][market_type][contract_type]:
                            comparison_list.append({"exchange": exchange, "market_type": market_type, "contract_type":contract_type, "quote_asset": quote_asset})

        for i, comparison_dict in enumerate(comparison_list):
            if comparison_dict['exchange'] == target_exchange and comparison_dict['market_type'] == target_market_type:
                target_market_dict = comparison_list.pop(i)
                break

        # Start compare and concat
        target_market_symbols = []
        target_market_ticker_df = self._load_redis_df(f"{target_market_dict['exchange'].lower()}_{target_market_dict['market_type'].lower()}_ticker_df")
        if target_market_ticker_df is None:
            return []
        # check if it's spot or not
        if target_market_dict['market_type'] != "SPOT":
            info_df = self._load_redis_df(f"{target_market_dict['exchange'].lower()}_{target_market_dict['market_type'].lower()}_info_df")
            if info_df is None:
                return []
            target_market_info_df = info_df[['symbol','perpetual']]
            target_market_ticker_df = target_market_ticker_df.merge(target_market_info_df, on='symbol', how='inner')
            if target_market_dict['contract_type'] == "PERPETUAL":
                target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['perpetual'] == True]
            else: # FUTURES
                target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['perpetual'] == False]
        target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['quote_asset']==target_market_dict['quote_asset']][['symbol','lastPrice','atp24h','base_asset','quote_asset']]
        merged_dfs = []
        for each_comparison_dict in comparison_list:
            each_market_info_df = self._load_redis_df(f"{each_comparison_dict['exchange'].lower()}_{each_comparison_dict['market_type'].lower()}_info_df")
            if each_market_info_df is None:
                continue
            if each_comparison_dict['contract_type'] is None:
                each_market_info_df = each_market_info_df[each_market_info_df['quote_asset']==each_comparison_dict['quote_asset']]
            else: # contract_type is PERPETUAL or FUTURES
                if each_comparison_dict['contract_type'] == "PERPETUAL":
                    each_market_info_df = each_market_info_df[(each_market_info_df['quote_asset']==each_comparison_dict['quote_asset'])&(each_market_info_df['perpetual'] == True)]
                else: # FUTURES
                    each_market_info_df = each_market_info_df[(each_market_info_df['quote_asset']==each_comparison_dict['quote_asset'])&(each_market_info_df['perpetual'] == False)]
            comparison_market_code = f"{each_comparison_dict['exchange'].lower()}_{each_comparison_dict['market_type'].lower()}"
            new_symbol = f"symbol_{comparison_market_code}"
            new_quote_asset = f"quote_asset_{comparison_market_code}"
            each_market_info_df = each_market_info_df.rename(columns={"symbol":new_symbol, "quote_asset": new_quote_asset})
            merged_df = target_market_ticker_df.merge(each_market_info_df[[new_symbol, "base_asset", new_quote_asset]], on='base_asset', how='inner')
            if (each_comparison_dict['exchange'] == target_market_dict['exchange'] and
                each_comparison_dict['market_type'] == target_market_dict['market_type']):
                target_market_symbols += merged_df[new_symbol].to_list()
            merged_dfs.append(merged_df)
            target_market_symbols += merged_df['symbol'].to_list()

        target_market_symbols = list(set(target_market_symbols))
        total_target_market_ticker_df = self._load_redis_df(f"{target_market_dict['exchange'].lower()}_{target_market_dict['market_type'].lower()}_ticker_df")
        if total_target_market_ticker_df is None:
            return []
        total_target_market_df = total_target_market_ticker_df[total_target_market_ticker_df['symbol'].isin(target_market_symbols)]
        final_symbol_list = total_target_market_df.sort_values('atp24h', ascending=False)['symbol'].to_list()

        # DEV_MAX_SYMBOLS: limit symbols in dev to reduce CPU/memory load
        dev_max = int(os.getenv("DEV_MAX_SYMBOLS", 0))
        if dev_max > 0:
            final_symbol_list = final_symbol_list[:dev_max]

        return final_symbol_list
    
    def check_status(self, print_result=False, include_text=False):
        exchange_proc_status_tup_list = [x.check_status(include_text=True) for x in self.exchange_websocket_dict.values()]
        proc_status = all([x[0] for x in exchange_proc_status_tup_list])
        print_text = ""
        for each_result in [x[1] for x in exchange_proc_status_tup_list]:
            print_text += f"{each_result}\n"
        if print_result:
            self.logger.info(print_text.rstrip())
        if include_text:
            return proc_status, print_text
        return proc_status

    def shutdown(self):
        for exchange_websocket in self.exchange_websocket_dict.values():
            if hasattr(exchange_websocket, "terminate_websocket"):
                try:
                    exchange_websocket.terminate_websocket()
                except Exception:
                    self.logger.error(f"MarketIngestRuntime|shutdown|{traceback.format_exc()}")
    
    def convert_asset_rate(self, origin_market, origin_quote_asset, target_market, target_quote_asset, _depth=0):
        if _depth > 3:
            return None

        if origin_quote_asset == "USD":
            origin_quote_asset = "USDT"
        if target_quote_asset == "USD":
            target_quote_asset = "USDT"
        if origin_quote_asset == target_quote_asset:
            return 1

        # Try to load spot ticker data, fall back to Binance if not available
        origin_exchange = origin_market.lower().split('_')[0]
        spot_data = self.local_redis.get_data(f"{origin_exchange}_spot_ticker_df")
        if spot_data is None:
            # Exchange doesn't have spot data (e.g., Gate.io), use Binance spot instead
            spot_data = self.local_redis.get_data("binance_spot_ticker_df")
        origin_market_spot_info_df = pickle.loads(spot_data) if spot_data else None
        # First try to find the rate from the origin_market_spot_info_df

        def convert_between_coins(spot_info_df, origin_quote_asset, target_quote_asset):
            if spot_info_df is None:
                return None
            df = spot_info_df[(spot_info_df['base_asset']==origin_quote_asset)&(spot_info_df['quote_asset']==target_quote_asset)]
            reverse_df = spot_info_df[(spot_info_df['quote_asset']==origin_quote_asset)&(spot_info_df['base_asset']==target_quote_asset)]
            if len(df) == 1:
                convert_rate = df['lastPrice'].values[0]
            elif len(reverse_df) == 1:
                price = reverse_df['lastPrice'].values[0]
                convert_rate = 1 / price if price != 0 else None
            else:
                convert_rate = None
            return convert_rate
        convert_rate = convert_between_coins(origin_market_spot_info_df, origin_quote_asset, target_quote_asset)
        if convert_rate is None: # not between coins
            dollar_price = get_dollar_dict(self.local_redis).get('price')
            if target_quote_asset == "KRW" and origin_quote_asset == "USDT":
                convert_rate = dollar_price
            elif target_quote_asset == "USDT" and origin_quote_asset == "KRW":
                convert_rate = 1 / dollar_price if dollar_price else None
            elif target_quote_asset == "KRW":
                usdt_rate = convert_between_coins(origin_market_spot_info_df, origin_quote_asset, "USDT")
                convert_rate = usdt_rate * dollar_price if usdt_rate and dollar_price else None
            elif origin_quote_asset == "KRW":
                temp_convert_rate = self.convert_asset_rate(target_market, target_quote_asset, origin_market, origin_quote_asset, _depth + 1)
                if temp_convert_rate is not None:
                    convert_rate = 1 / temp_convert_rate
                else:
                    title = f"target_market: {target_market}, target_quote_asset: {target_quote_asset}, origin_market:{origin_market}, origin_quote_asset: {origin_quote_asset}"
                    raise Exception(f"Cannot find the convert rate for {title}")
            else:
                temp_convert_rate = self.convert_asset_rate(target_market, target_quote_asset, origin_market, origin_quote_asset, _depth + 1)
                if temp_convert_rate is not None:
                    convert_rate = 1 / temp_convert_rate
                    return convert_rate
                else:
                    pass
                title = f"target_market: {target_market}, target_quote_asset: {target_quote_asset}, origin_market:{origin_market}, origin_quote_asset: {origin_quote_asset}"
                raise Exception(f"Cannot find the convert rate for {title}")
        return convert_rate

    def update_convert_rate_dict(self, loop_time_secs=30):
        while True:
            try:
                for each_market_combi in self.enabled_market_klines:
                    target_market_code, origin_market_code = each_market_combi.split(':')
                    target_market, target_quote_asset = target_market_code.split('/')
                    origin_market, origin_quote_asset = origin_market_code.split('/')
                    new_convert_rate = self.convert_asset_rate(
                        origin_market,
                        origin_quote_asset,
                        target_market,
                        target_quote_asset,
                    )
                    previous_convert_rate = self.local_redis.hget_value('convert_rate_dict', each_market_combi)
                    self.local_redis.hset_value('convert_rate_dict', each_market_combi, new_convert_rate)
                    if previous_convert_rate is None or float(previous_convert_rate) != float(new_convert_rate):
                        self.local_redis.set_data(
                            f"{CONVERT_RATE_VERSION_PREFIX}|{each_market_combi}",
                            str(int(time.time() * 1_000_000)),
                        )
                if self.convert_rate_initialized is False:
                    self.convert_rate_initialized = True
            except Exception as e:
                self.logger.error(f"update_convert_rate_dict|Exception occured! Error: {e}, traceback: {traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, f"update_convert_rate_dict|Exception occured! Error: {e}", f"update_convert_rate_dict|Exception occured! Error: {e}")
            time.sleep(loop_time_secs)

    def _decode_redis_value(self, raw_value):
        if raw_value is None:
            return None
        if isinstance(raw_value, bytes):
            return raw_value.decode("utf-8")
        return str(raw_value)

    def _get_market_state_version(self, market_code):
        return self._decode_redis_value(
            self.local_redis.get_data(f"{MARKET_STATE_VERSION_PREFIX}|{market_code}")
        )

    def _get_convert_rate_version(self, market_code_combination):
        return self._decode_redis_value(
            self.local_redis.get_data(f"{CONVERT_RATE_VERSION_PREFIX}|{market_code_combination}")
        )

    def _get_convert_rate_value(self, market_code_combination):
        raw_value = self.local_redis.hget_value("convert_rate_dict", market_code_combination)
        if raw_value is None:
            return None
        if isinstance(raw_value, bytes):
            raw_value = raw_value.decode("utf-8")
        return float(raw_value)

    def _get_market_price_df_snapshot(self, market_code):
        market_state_version = self._get_market_state_version(market_code)
        if market_state_version is None:
            return None, None

        with self.market_price_df_cache_lock:
            cached_entry = self.market_price_df_cache.get(market_code)
            if (
                cached_entry is not None
                and cached_entry["market_state_version"] == market_state_version
            ):
                return cached_entry["price_df"], market_state_version

        price_df = get_price_df(self.local_redis, market_code)
        with self.market_price_df_cache_lock:
            self.market_price_df_cache[market_code] = {
                "market_state_version": market_state_version,
                "price_df": price_df,
            }
        return price_df, market_state_version

    def start_premium_cache_workers(self, loop_time_secs=0.05):
        for market_code_combination in self.enabled_market_klines:
            worker = Thread(
                target=self.update_premium_cache_loop,
                args=(market_code_combination, loop_time_secs),
                daemon=True,
            )
            worker.start()
            self.premium_cache_thread_dict[market_code_combination] = worker

    def start_latest_funding_workers(self, loop_time_secs=5):
        for market_code in self.get_enabled_futures_market_codes():
            worker = Thread(
                target=self.update_latest_funding_loop,
                args=(market_code, loop_time_secs),
                daemon=True,
            )
            worker.start()
            self.latest_funding_thread_dict[market_code] = worker

    def update_premium_cache_loop(self, market_code_combination, loop_time_secs=0.05):
        target_market_code, origin_market_code = market_code_combination.split(":")
        target_quote_asset = target_market_code.split("/")[1]
        origin_quote_asset = origin_market_code.split("/")[1]

        while True:
            try:
                if fetch_market_servercheck(target_market_code) or fetch_market_servercheck(origin_market_code):
                    time.sleep(1)
                    continue

                target_market_df, target_market_version = self._get_market_price_df_snapshot(
                    target_market_code.split("/")[0]
                )
                origin_market_df, origin_market_version = self._get_market_price_df_snapshot(
                    origin_market_code.split("/")[0]
                )
                convert_rate_version = self._get_convert_rate_version(market_code_combination)
                convert_rate = self._get_convert_rate_value(market_code_combination)

                if (
                    target_market_df is None
                    or origin_market_df is None
                    or convert_rate_version is None
                    or convert_rate is None
                ):
                    time.sleep(1)
                    continue

                current_signature = (
                    target_market_version,
                    origin_market_version,
                    convert_rate_version,
                )
                if self.premium_cache_signature_dict.get(market_code_combination) == current_signature:
                    time.sleep(loop_time_secs)
                    continue

                dollar_price = get_dollar_dict(self.local_redis)["price"]
                premium_df = get_premium_df_from_market_snapshots(
                    origin_market_df=origin_market_df,
                    target_market_df=target_market_df,
                    quote_asset_one=origin_quote_asset,
                    quote_asset_two=target_quote_asset,
                    convert_rate=convert_rate,
                    dollar_price=dollar_price,
                    logger=self.logger,
                    target_market_code=target_market_code,
                    origin_market_code=origin_market_code,
                    sort_by_atp24h=False,
                )
                if not premium_df.empty:
                    metadata = build_premium_cache_metadata(
                        self.local_redis,
                        market_code_combination,
                        target_market_code,
                        origin_market_code,
                    )
                    store_premium_df(
                        self.local_redis,
                        market_code_combination,
                        premium_df,
                        metadata=metadata,
                        ex=5,
                    )
                    self.premium_cache_signature_dict[market_code_combination] = current_signature
            except Exception as e:
                self.logger.error(
                    f"update_premium_cache_loop|{market_code_combination}|{e}\n{traceback.format_exc()}"
                )

            time.sleep(loop_time_secs)

    def update_latest_funding_loop(self, market_code, loop_time_secs=5):
        while True:
            try:
                if fetch_market_servercheck(market_code):
                    time.sleep(1)
                    continue

                funding_df = self._fetch_latest_funding_df(market_code)
                if not funding_df.empty:
                    store_latest_funding_snapshot(self.local_redis, market_code, funding_df)
                    self.remote_redis.set_data(
                        f"INFO_CORE|FUNDING_LATEST|{market_code}",
                        self.local_redis.get_data(f"INFO_CORE|FUNDING_LATEST|{market_code}"),
                        ex=120,
                    )
            except Exception as e:
                self.logger.error(
                    f"update_latest_funding_loop|{market_code}|{e}\n{traceback.format_exc()}"
                )

            time.sleep(loop_time_secs)
        
        
    def fetch_dollar(self, update_dollar_logger, url='https://m.search.naver.com/p/csearch/content/qapirender.nhn?key=calculator&pkid=141&q=환율&where=m&u1=keb&u6=standardUnit&u7=0&u3=USD&u4=KRW&u8=down&u2=1', timeout=10):
        current_time_utc = datetime.datetime.utcnow()

        # Calculate KST time
        kst_tz = datetime.timezone(datetime.timedelta(hours=9))
        current_kst_time = current_time_utc.replace(tzinfo=datetime.timezone.utc).astimezone(kst_tz)
        current_kst_time_only = current_kst_time.time()

        # Define restricted time window (8:20 AM to 9:00 AM KST)
        start_time_kst = datetime.time(8, 20)
        end_time_kst = datetime.time(9, 00)
        is_restricted_time = start_time_kst <= current_kst_time_only < end_time_kst
        
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            response_dict = resp.json()

            # Basic validation of response structure
            countries = response_dict.get('country')
            if not isinstance(countries, list) or len(countries) < 2:
                update_dollar_logger.error(f"Unexpected response format from Naver API. 'country' list invalid or too short. response_dict: {response_dict}")
                self.acw_api.create_message_thread(self.admin_id, "Naver 환율 API 응답 형식 오류", f"Naver 환율 API에서 예상치 못한 응답 형식을 받았습니다. response_dict: {response_dict}")
                return self.update_dollar_return_dict # Return previous state or handle error appropriately

            fetched_value_str = countries[1].get('value')
            if not fetched_value_str:
                update_dollar_logger.warning(f'환율 정보를 가져오지 못했습니다 (value missing). url: {url}, response_dict: {response_dict}')
                self.acw_api.create_message_thread(self.admin_id, f"환율 정보를 가져오지 못했습니다 (value missing).", f"환율 정보를 가져오지 못했습니다., url: {url}, response_dict: {response_dict}")
                return self.update_dollar_return_dict

            fetched_dollar = float(fetched_value_str.replace(',', ''))
            
            if is_restricted_time:
                # Only log during restricted time, do not update redis or internal state
                update_dollar_logger.info(f"fetch_dollar|Time restriction ({start_time_kst}-{end_time_kst} KST). Fetched dollar: {fetched_dollar:.2f}. Not updating Redis.")
            else:
                # --- Update logic only runs outside restricted time ---
                redis_key = 'INFO_CORE|dollar'
                existing_dollar_data = self.local_redis.get_dict(redis_key)
                
                price_to_store = fetched_dollar
                difference_count_to_store = 0
                last_updated_time_to_store = current_time_utc # Use the fetched UTC time
                update_occurred = True # Flag to indicate if price/timestamp should be updated

                if existing_dollar_data is not None:                
                    existing_price = existing_dollar_data['price']
                    existing_diff_count = existing_dollar_data.get('difference_count', 0)
                    existing_time_str = existing_dollar_data.get('last_updated_time')

                    # Check whether the newly updated dollar price is too different
                    if abs(fetched_dollar - existing_price) / existing_price > 0.005:
                        update_dollar_logger.warning(f"fetch_dollar|Large price difference detected. (existing: {existing_price}, new: {fetched_dollar})")
                        difference_count_to_store = existing_diff_count + 1
                        
                        # Accept the new price if count is >= 2
                        if difference_count_to_store >= 2:
                            update_dollar_logger.warning(f"fetch_dollar|Accepting new price {fetched_dollar} due to sustained difference (count: {difference_count_to_store}).")
                            price_to_store = fetched_dollar
                            last_updated_time_to_store = current_time_utc
                            update_occurred = True
                        else:
                             # Keep existing price and time if difference is large but count < 2
                            price_to_store = existing_price
                            # Use existing time string directly or parsed datetime
                            try:
                                # Use existing time string directly or parsed datetime if available
                                if existing_time_str:
                                    last_updated_time_to_store = datetime.datetime.strptime(existing_time_str, "%Y-%m-%d %H:%M:%S")
                                else: # Fallback if time string is missing for some reason
                                    last_updated_time_to_store = current_time_utc 
                            except (ValueError, TypeError): # Handle potential parsing errors
                                 update_dollar_logger.warning(f"fetch_dollar|Could not parse existing timestamp '{existing_time_str}'. Using current time as fallback.")
                                 last_updated_time_to_store = current_time_utc
                            update_occurred = False # Only count was updated
                    else:
                        # Difference is small, accept new price and reset count
                        price_to_store = fetched_dollar
                        difference_count_to_store = 0 
                        last_updated_time_to_store = current_time_utc
                        update_occurred = True

                else:
                    # No existing data, use fetched values
                    update_dollar_logger.info("fetch_dollar|No existing dollar data found in Redis. Initializing.")
                    # Variables price_to_store, difference_count_to_store, last_updated_time_to_store, update_occurred are already initialized correctly above

                # Update the class member dictionary
                self.update_dollar_return_dict['price'] = price_to_store
                self.update_dollar_return_dict['difference_count'] = difference_count_to_store
                # Store datetime object in the class member for internal use
                self.update_dollar_return_dict['last_updated_time'] = last_updated_time_to_store 
                
                # Prepare data for Redis (store time as string)
                dict_for_redis = {
                    "price": price_to_store,
                    "difference_count": difference_count_to_store,
                    # Ensure we store the correct timestamp string (which might be the old one if update_occurred is False)
                    "last_updated_time": last_updated_time_to_store.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.local_redis.set_dict(redis_key, dict_for_redis)
                if self.authoritative_reference_publisher:
                    self.remote_redis.set_dict(redis_key, dict_for_redis)
                
                # Generate log once every 10 times (only if an actual price update occurred or it's the first time)
                self.update_dollar_return_dict['log_counter'] = self.update_dollar_return_dict.get('log_counter', 0) + 1
                if self.update_dollar_return_dict['log_counter'] % 10 == 1: # Log on the 1st, 11th, 21st... call
                    if update_occurred:
                        update_dollar_logger.info(f"fetch_dollar|Dollar price updated to {price_to_store:.2f} KRW. Diff count: {difference_count_to_store}.")
                    else: # Log when price is kept due to large diff but low count
                        update_dollar_logger.info(f"fetch_dollar|Dollar price check. Price kept at {price_to_store:.2f} KRW. Diff count incremented to {difference_count_to_store}.")
            # --- End of update logic block ---

        except requests.exceptions.Timeout:
            update_dollar_logger.error(f"fetch_dollar|Request timed out after {timeout} seconds for URL: {url}")
            self.acw_api.create_message_thread(self.admin_id, f"fetch_dollar|Request Timeout", f"fetch_dollar|Request timed out for URL: {url}")
        except requests.exceptions.RequestException as e:
            update_dollar_logger.error(f"fetch_dollar|Request failed: {e}")
            self.acw_api.create_message_thread(self.admin_id, f"fetch_dollar|Request Exception", f"fetch_dollar|Request failed: {e}")
        except (ValueError, TypeError) as e:
            # Ensure fetched_value_str is defined for the error message
            fetched_value_str_for_error = 'N/A'
            try:
                # Try to access it if it was assigned
                fetched_value_str_for_error = fetched_value_str
            except NameError:
                pass # It wasn't assigned, keep 'N/A'
            update_dollar_logger.error(f"fetch_dollar|Error processing fetched value: {e}. Value string: '{fetched_value_str_for_error}'")
            self.acw_api.create_message_thread(self.admin_id, f"fetch_dollar|Value Processing Error", f"fetch_dollar|Error processing value: {e}. String: '{fetched_value_str_for_error}'")
        except Exception as e:
            update_dollar_logger.exception(f"fetch_dollar|An unexpected error occurred: {e}") # Use logger.exception to include traceback
            self.acw_api.create_message_thread(self.admin_id, f"fetch_dollar|Unexpected Exception", f"fetch_dollar|An unexpected error occurred: {e}")
            
        # Always return the current state of the class member dict (which won't be updated during restricted time)
        return self.update_dollar_return_dict

    def fetch_dollar_loop(self, update_dollar_logger, loop_time=30):
        self.logger.info(f"fetch_dollar_loop|Dollar update thread has started.")
        while True:
            try:
                self.fetch_dollar(update_dollar_logger)
            except Exception as e:
                self.logger.error(f"fetch_dollar_loop|Exception occured! Error: {e}, {traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, f"fetch_dollar_loop|Exception occured! Error: {e}", f"fetch_dollar_loop|Exception occured! Error: {e}")
            time.sleep(loop_time)
            
    def fetch_usdt(self):
        try:
            # Check whether BITHUMB_SPOT/KRW is in maintenance or not
            server_check = fetch_market_servercheck("BITHUMB_SPOT/KRW")
            if server_check:
                self.logger.info(f"fetch_usdt|BITHUMB_SPOT/KRW has been skipped due to server check.")
                return
            # Fetch usdt price from Bithumb
            ticker_df = self.bithumb_adaptor.spot_all_tickers()
            usdt_df = ticker_df[ticker_df['base_asset']=='USDT']
            usdt_price = usdt_df['lastPrice'].iloc[0]
            change = usdt_df['fluctate_24H'].iloc[0]
            # UTC time in '%Y-%m-%d %H:%M:%S'
            last_update_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

            dict_for_redis = {
                'price': float(usdt_price),
                'change': float(change),
                'last_update_time': last_update_time
            }
            self.local_redis.set_dict('INFO_CORE|usdt', dict_for_redis)
            if self.authoritative_reference_publisher:
                self.remote_redis.set_dict('INFO_CORE|usdt', dict_for_redis)
        except Exception as e:
            self.logger.error(f"fetch_usdt|Exception occured! Error: {e}, {traceback.format_exc()}")
            self.acw_api.create_message_thread(self.admin_id, f"fetch_usdt|Exception occured! Error: {e}", f"fetch_usdt|Exception occured! Error: {e}")
            
    def fetch_usdt_loop(self, loop_time=30):
        self.logger.info(f"fetch_usdt_loop|USDT update thread has started.")
        while True:
            try:
                self.fetch_usdt()
            except Exception as e:
                self.logger.error(f"fetch_usdt_loop|Exception occured! Error: {e}, {traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, f"fetch_usdt_loop|Exception occured! Error: {e}", f"fetch_usdt_loop|Exception occured! Error: {e}")
            time.sleep(loop_time)

    def add_symbol_to_exclude(self, market, base_asset):
        if market == "UPBIT_SPOT":
            self.upbit_symbols_to_exclude.append(base_asset)
        elif market == "BINANCE_USD_M":
            self.binance_usd_m_symbols_to_exclude.append(base_asset)
        else:
            raise Exception(f"market: {market} is not supported.")
    def remove_symbol_to_exclude(self, market, base_asset):
        if market == "UPBIT_SPOT":
            self.upbit_symbols_to_exclude.remove(base_asset)
        elif market == "BINANCE_USD_M":
            self.binance_usd_m_symbols_to_exclude.remove(base_asset)
        else:
            raise Exception(f"market: {market} is not supported.")
