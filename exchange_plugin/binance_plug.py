import sys
import os
import datetime
import traceback
import pandas as pd
import time
from binance.client import Client

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, info_dict=None, recvWindow=45000, logging_dir=None):
        self.my_bi_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.info_dict = info_dict
        self.recvWindow = recvWindow
        self.binance_plug_logger = KimpBotLogger("binance_plug", logging_dir).logger
        self.binance_plug_logger.info(f"binance_plug_logger started.")

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_bi_client.get_deposit_history(asset=asset))
        deposit.loc[:,'insertTime'] = deposit['insertTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        deposit.loc[:, 'amount'] = deposit['amount'].astype(float)
        return deposit
    
    def spot_all_tickers(self):
        df = pd.DataFrame(self.pub_client.get_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        if self.info_dict is None or self.info_dict.get('binance_spot_info_df') is None:
            # TEST
            spot_exchange_info_df = self.spot_exchange_info()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_info_df') is None, Fetched from API")
        else:
            spot_exchange_info_df = self.info_dict.get('binance_spot_info_df')
        df = df.merge(spot_exchange_info_df[['symbol', 'baseAsset', 'quoteAsset']], on='symbol', how='inner')
        df.rename(columns={'baseAsset': 'base_asset', 'quoteAsset': 'quote_asset'}, inplace=True)
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['volume_usdt'] = df['quoteVolume'] * df['lastPrice2']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)
        # if quote_asset is 'USDT', volume_usdt is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'volume_usdt'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        return df
    
    def spot_exchange_info(self):
        df = pd.DataFrame(self.pub_client.get_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def usdm_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def usdm_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        if self.info_dict is None or self.info_dict.get('binance_usdm_info_df') is None:
            # TEST
            usdm_exchange_info_df = self.usdm_exchange_info()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_info_df') is None, Fetched from API")
        else:
            usdm_exchange_info_df = self.info_dict.get('binance_usdm_info_df')
        if self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None:
            # TEST
            binance_spot_ticker_df = self.spot_all_tickers()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None, Fetched from API")
        else:
            binance_spot_ticker_df = self.info_dict.get('binance_spot_ticker_df')
        df = df.merge(usdm_exchange_info_df[['symbol', 'baseAsset', 'quoteAsset']], on='symbol', how='inner')
        df.rename(columns={'baseAsset': 'base_asset', 'quoteAsset': 'quote_asset'}, inplace=True)
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = binance_spot_ticker_df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['volume_usdt'] = df['quoteVolume'] * df['lastPrice2']
        # if quote_asset is 'USDT', volume_usdt is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'volume_usdt'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)

        return df
    
    def coinm_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_coin_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def coinm_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_coin_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df['base_asset'] = df['symbol'].str.split('USD_').str[0]
        df['quote_asset'] = 'USDT' # ?
        df['volume_usdt'] = df['volume'] * 100
        return df

    def usdm_fundingrate(self):
        bi_client = self.pub_client
        binance_fund = pd.DataFrame(bi_client.futures_mark_price())
        binance_fund = binance_fund.rename(columns={'symbol':'binance', 'lastFundingRate':'binance_fundingrate', 'nextFundingTime':'fundingtime'})
        binance_fund.loc[:,['nextFundingTime', 'time']] = binance_fund.loc[:,['nextFundingTime', 'time']].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        binance_fund['symbol'] = binance_fund['binance'].apply(lambda x: x.replace('USDT',''))
        return binance_fund
