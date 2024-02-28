import os
import sys
import datetime
import pandas as pd
import time
import traceback
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from exchange_plugin.upbit_plug import UserUpbitAdaptor
from exchange_plugin.binance_plug import UserBinanceAdaptor
from etc.redis_connector.redis_connector import InitRedis

class UserExchangeAdaptor:
    def __init__(self, logging_dir=None):
        self.logger = KimpBotLogger("integrated_plug", logging_dir=logging_dir).logger
        self.logger.info('integrated_plug_logger init')
        self.exchange_adaptor_dict = {}
        self.exchange_adaptor_dict["UPBIT"] = UserUpbitAdaptor(logging_dir=logging_dir)
        self.exchange_adaptor_dict["BINANCE"] = UserBinanceAdaptor(logging_dir=logging_dir)
        # redis connection to read info_dict
        self.local_redis_client = InitRedis(host='localhost', port=6379, db=0, passwd=None)

    def check_api_key(self, exchange, access_key, secret_key, passphrase=None, futures=False):
        """FUTURES includes USD_M, COIN_M"""
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        if exchange == "OKX":
            return self.exchange_adaptor_dict[exchange].check_api_key(access_key, secret_key, passphrase, futures)
        else:
            return self.exchange_adaptor_dict[exchange].check_api_key(access_key, secret_key, futures)
    
    def get_position(self, exchange, access_key, secret_key, market_type, passphrase=None):
        """SPOT position columns: ['asset', 'free', 'locked']
        USD_M position columns: ["symbol", "base_asset", "qty", "margin_type", "entry_price", "liquidation_price", "leverage"]
        """
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            position_df = exchange_adaptor.get_balance(access_key, secret_key, market_type)
        elif exchange == "BINANCE":
            position_df = exchange_adaptor.all_position_information(access_key, secret_key, market_type)
            info_df = pickle.loads(self.local_redis_client.get_data(f'TRADE_CORE|{exchange.lower()}_{market_type.lower()}_info_df'))
            position_df = position_df.merge(info_df[['symbol','base_asset']], how='left', on='symbol')
            position_df = position_df.rename(columns={"positionAmt":"qty", "marginType":"margin_type", "entryPrice":"entry_price", "liquidationPrice":"liquidation_price"})
            position_df["ROI"] = position_df.apply(lambda x: (x['entry_price']-x['markPrice'])/x['markPrice']*x['leverage']*100 if x['qty']<0 else 
                                                   (x['markPrice']-x['entry_price'])/x['entry_price']*['leverage']*100, axis=1)
        else:
            raise Exception(f'exchange {exchange} not supported')
        return position_df
    
    def get_capital(self, exchange, access_key, secret_key, market_type, passphrase=None):
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            currency = 'KRW'
            position_df = exchange_adaptor.get_balance(access_key, secret_key, market_type)
            ticker_df = pickle.loads(self.local_redis_client.get_data(f"TRADE_CORE|{exchange.lower()}_{market_type.lower()}_ticker_df"))
            position_df['symbol'] = position_df['unit_currency']+'-'+position_df['asset']
            merged_df = position_df.merge(ticker_df[['symbol','lastPrice']], how='left', on='symbol')
            merged_df.loc[merged_df['asset']==currency, 'lastPrice'] = 1
            merged_df['entered'] = merged_df['avg_buy_price'] * merged_df['free']
            merged_df['locked'] = merged_df['avg_buy_price'] * merged_df['locked']
            free = round(merged_df.loc[merged_df['asset']==currency, 'free'].values[0])
            locked = round(merged_df['entered'].sum() + merged_df['locked'].sum())
            before_pnl = round(free + locked)
            after_pnl = round((((merged_df['free'] + merged_df['locked']) * merged_df['lastPrice'])).sum())
            pnl = round(after_pnl - before_pnl)
        elif exchange == "BINANCE":
            currency = 'USDT'
            balance_df = self.exchange_adaptor_dict[exchange].get_balance(access_key, secret_key, market_type)
            currency_df = balance_df[balance_df['asset']==currency]
            free = round(currency_df['availableBalance'].values[0],1)
            locked = round(currency_df['walletBalance'].values[0] - free,1)
            before_pnl = round(currency_df['walletBalance'].values[0],1)
            pnl = round(currency_df['unrealizedProfit'].values[0],1)
            after_pnl = round(currency_df['walletBalance'].values[0] + pnl,1)
        else:
            raise Exception(f'exchange {exchange} not supported')

        capital_series = pd.Series({'free':free, 'locked':locked, 'before_pnl': before_pnl, 'pnl':pnl, 'after_pnl':after_pnl, 'currency': currency})
        return capital_series