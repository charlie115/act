import pandas as pd
import requests
import json
import time
import datetime
from loggers.logger import TradeCoreLogger
from exchange_plugin import binance_plug, bithumb_plug, bybit_plug, okx_plug, upbit_plug

class ExchangeApi:
    def __init__(self, node, logging_dir=None):
        self.node = node
        if logging_dir is not None:
            self.logger = TradeCoreLogger("exchange_api", logging_dir).logger
        else:
            self.logger = TradeCoreLogger("exchange_api").logger

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
        return self.exchange_api.get_ticker(symbol)

    def get_kline(self, symbol, interval, limit=1000):
        return self.exchange_api.get_kline(symbol, interval, limit)

    def get_orderbook(self, symbol, limit=100):
        return self.exchange_api.get_orderbook(symbol, limit)

    def get_account(self):
        return self.exchange_api.get_account()

    def get_order(self, symbol, order_id):
        return self.exchange_api.get_order(symbol, order_id)

    def get_open_orders(self, symbol):
        return self.exchange_api.get_open_orders(symbol)

    def get_all_orders(self, symbol):
        return self.exchange_api.get_all_orders(symbol)

    def create_order(self, symbol, side, type, quantity, price=None, stop_price=None, timeInForce=None):
        return self.exchange_api.create_order(symbol, side, type, quantity, price, stop_price, timeInForce)

    def cancel_order(self, symbol, order_id):
        return self.exchange_api.cancel_order(symbol, order_id)

    def get_order_status(self, symbol, order_id):
        return self.exchange_api.get_order_status(symbol, order_id)

    def get_order_trades(self, symbol, order):
        pass