import os
import sys
import datetime
import pandas as pd
from upbit.client import Upbit
import time
import traceback

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

def calculate_upbit_price(price):
    if price >= 2000000:
        price = int(price/1000)*1000
    elif price >= 1000000:
        price = int(price/500)*500
    elif price >= 500000:
        price = int(price/100)*100
    elif price >= 100000:
        price = int(price/50)*50
    elif price >= 10000:
        price = int(price/10)*10
    elif price >= 1000:
        price = int(price/5)*5
    elif price >= 100:
        price = int(price)
    elif price >= 10:
        price = int(price*10)/10
    elif price >= 1:
        price = int(price*100)/100
    elif price >= 0.1:
        price = int(price*1000)/1000
    elif 0.1 > price:
        price = int(price*10000)/10000

    return price

class InitUpbitAdaptor:
    def __init__(self, my_upbit_access_key=None, my_upbit_secret_key=None, info_dict=None, logging_dir=None):
        self.my_client = Upbit(my_upbit_access_key, my_upbit_secret_key)
        self.pub_client = Upbit()
        self.info_dict = info_dict
        self.upbit_plug_logger = KimpBotLogger("upbit_plug", logging_dir).logger
        self.upbit_plug_logger.info(f"upbit_plug_logger started.")

    # Private API
    def wallet_status(self):
        wallet_status = pd.DataFrame(self.my_client.Account.Account_wallet()['result'])
        wallet_status = wallet_status.rename(columns={"currency": "asset", "net_type": "network_type"})
        wallet_status['deposit'] = wallet_status['wallet_state'].apply(lambda x: True if x in ["working", "deposit_only"] else False)
        wallet_status['withdraw'] = wallet_status['wallet_state'].apply(lambda x: True if x in ["working", "withdraw_only"] else False)
        return wallet_status
    
    def spot_exchange_info(self):
        info_df = pd.DataFrame(self.pub_client.Market.Market_info_all(isDetails=True)['result'])
        info_df['base_asset'] = info_df['market'].apply(lambda x: x.split('-')[1])
        info_df['quote_asset'] = info_df['market'].apply(lambda x: x.split('-')[0])
        info_df.loc[:, 'market_warning'] = info_df['market_warning'].apply(lambda x: False if x == "NONE" else True)
        info_df.rename(columns={"market": "symbol"}, inplace=True)
        return info_df

    def spot_all_tickers(self, return_dict=None):
        upbit_client = self.pub_client
        upbit_symbols_df = pd.DataFrame(upbit_client.Market.Market_info_all()['result'])
        upbit_symbols = upbit_symbols_df['market'].to_list()
        upbit_all_ticker_df = pd.DataFrame(upbit_client.Trade.Trade_ticker(markets=','.join(upbit_symbols))['result'])
        upbit_all_ticker_df = upbit_all_ticker_df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        def convert_to_krw(x):
            if x['market'].startswith('KRW-'):
                return x['acc_trade_price_24h']
            else:
                try:
                    output = x['acc_trade_price_24h'] * upbit_all_ticker_df[upbit_all_ticker_df['market']==f"KRW-{x['market'].split('-')[0]}"]['trade_price'].iloc[0]
                except:
                    output = None
                return output
        upbit_all_ticker_df['base_asset'] = upbit_all_ticker_df['market'].apply(lambda x: x.split('-')[1])
        upbit_all_ticker_df['quote_asset'] = upbit_all_ticker_df['market'].apply(lambda x: x.split('-')[0])
        upbit_all_ticker_df['acc_trade_price_24h_krw'] = upbit_all_ticker_df.apply(convert_to_krw, axis=1)
        upbit_all_ticker_df.rename(columns={"market": "symbol", "trade_price": "lastPrice", "acc_trade_price_24h_krw": "atp24h"}, inplace=True)
        if return_dict is None:
            res = upbit_all_ticker_df
            return res
        else:
            return_dict['res'] = upbit_all_ticker_df

    
