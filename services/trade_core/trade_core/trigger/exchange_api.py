import pandas as pd
import requests
import json
import time
import datetime
from loggers.logger import TradeCoreLogger
from exchange_plugin import binance_plug, bithumb_plug, bybit_plug, okx_plug, upbit_plug

class ExchangeApi:
    EXCHANGE_PLUGIN_MAP = {
        'UPBIT': upbit_plug.InitUpbitAdaptor,
        'BINANCE': binance_plug.InitBinanceAdaptor,
        'BITHUMB': bithumb_plug.InitBithumbAdaptor,
        'OKX': okx_plug.InitOkxAdaptor,
        'BYBIT': bybit_plug.InitBybitAdaptor,
    }

    def __init__(self, node, logging_dir=None):
        self.node = node
        self.exchange_api = None
        if logging_dir is not None:
            self.logger = TradeCoreLogger("exchange_api", logging_dir).logger
        else:
            self.logger = TradeCoreLogger("exchange_api").logger

    def set_exchange(self, exchange_name, access_key=None, secret_key=None, logging_dir=None):
        """Initialize the exchange API client for the given exchange."""
        exchange = exchange_name.upper()
        if exchange not in self.EXCHANGE_PLUGIN_MAP:
            raise Exception(f"Exchange {exchange} is not supported.")
        plugin_cls = self.EXCHANGE_PLUGIN_MAP[exchange]
        self.exchange_api = plugin_cls(access_key, secret_key, logging_dir=logging_dir)

    def _require_exchange_api(self):
        if self.exchange_api is None:
            raise RuntimeError("exchange_api not initialized. Call set_exchange() first.")

    def check_api_key(self, market_code, access_key, secret_key):
        exchange = market_code.split('_')[0]
        if exchange == 'UPBIT':
            pass
        elif exchange == 'BINANCE':
            pass
        elif exchange == 'BITHUMB':
            pass
        elif exchange == 'OKX':
            pass
        elif exchange == 'BYBIT':
            pass
        else:
            raise Exception(f"Market code:{market_code}, exchange:{exchange} is not supported.")


    def get_ticker(self, symbol):
        self._require_exchange_api()
        return self.exchange_api.get_ticker(symbol)

    def get_kline(self, symbol, interval, limit=1000):
        self._require_exchange_api()
        return self.exchange_api.get_kline(symbol, interval, limit)

    def get_orderbook(self, symbol, limit=100):
        self._require_exchange_api()
        return self.exchange_api.get_orderbook(symbol, limit)

    def get_account(self):
        self._require_exchange_api()
        return self.exchange_api.get_account()

    def get_order(self, symbol, order_id):
        self._require_exchange_api()
        return self.exchange_api.get_order(symbol, order_id)

    def get_open_orders(self, symbol):
        self._require_exchange_api()
        return self.exchange_api.get_open_orders(symbol)

    def get_all_orders(self, symbol):
        self._require_exchange_api()
        return self.exchange_api.get_all_orders(symbol)

    def create_order(self, symbol, side, type, quantity, price=None, stop_price=None, timeInForce=None):
        self._require_exchange_api()
        return self.exchange_api.create_order(symbol, side, type, quantity, price, stop_price, timeInForce)

    def cancel_order(self, symbol, order_id):
        self._require_exchange_api()
        return self.exchange_api.cancel_order(symbol, order_id)

    def get_order_status(self, symbol, order_id):
        self._require_exchange_api()
        return self.exchange_api.get_order_status(symbol, order_id)

    def get_order_trades(self, symbol, order):
        pass