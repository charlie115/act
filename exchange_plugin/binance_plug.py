import sys
import os
import datetime
import traceback
import pandas as pd
import numpy as np
import time
from binance.client import Client

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, info_dict=None, recvWindow=45000, logging_dir=None):
        self.my_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.info_dict = info_dict
        self.recvWindow = recvWindow
        self.binance_plug_logger = KimpBotLogger("binance_plug", logging_dir).logger
        self.binance_plug_logger.info(f"binance_plug_logger started.")

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_client.get_deposit_history(asset=asset))
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
        df = df.merge(spot_exchange_info_df[['symbol', 'base_asset', 'quote_asset']], on='symbol', how='inner')
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['atp24h'] = df['quoteVolume'] * df['lastPrice2']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)
        # if quote_asset is 'USDT', atp24h is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'atp24h'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        return df
    
    def spot_exchange_info(self):
        df = pd.DataFrame(self.pub_client.get_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        return df
    
    def usd_m_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def usd_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        if self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None:
            # TEST
            usd_m_exchange_info_df = self.usd_m_exchange_info()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None, Fetched from API")
        else:
            usd_m_exchange_info_df = self.info_dict.get('binance_usd_m_info_df')
        if self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None:
            # TEST
            binance_spot_ticker_df = self.spot_all_tickers()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None, Fetched from API")
        else:
            binance_spot_ticker_df = self.info_dict.get('binance_spot_ticker_df')
        df = df.merge(usd_m_exchange_info_df[['symbol', 'base_asset', 'quote_asset']], on='symbol', how='inner')
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = binance_spot_ticker_df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['atp24h'] = df['quoteVolume'] * df['lastPrice2']
        # if quote_asset is 'USDT', atp24h is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'atp24h'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)

        return df
    
    def coin_m_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_coin_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def coin_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_coin_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df['base_asset'] = df['symbol'].str.split('USD_').str[0]
        df['quote_asset'] = 'USD' # ?
        df['atp24h'] = df['volume'] * 100
        return df

    def get_fundingrate(self, futures_type="USD_M"):
        bi_client = self.pub_client
        if futures_type == "USD_M":
            if self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None:
                usd_m_exchange_info_df = self.usd_m_exchange_info()
                self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None, Fetched from API")
            else:
                usd_m_exchange_info_df = self.info_dict.get('binance_usd_m_info_df')
            binance_fund = pd.DataFrame(bi_client.futures_mark_price())
            binance_fund = binance_fund.merge(usd_m_exchange_info_df[['symbol','base_asset','quote_asset']], on='symbol', how='left')
            binance_fund = binance_fund.rename(columns={'lastFundingRate':'funding_rate', 'nextFundingTime':'funding_time'})
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # replace '' to None
            binance_fund.replace("", None, inplace=True)
            binance_fund.loc[:, 'funding_rate'] = binance_fund['funding_rate'].astype(float)
            binance_fund.drop(columns=['markPrice','indexPrice','estimatedSettlePrice','interestRate','time'], inplace=True)
            binance_fund['perpetual'] = binance_fund['symbol'].apply(lambda x: False if '_' in x else True)
            return binance_fund
        elif futures_type == "COIN_M":
            binance_fund = pd.DataFrame(bi_client.futures_coin_mark_price())
            binance_fund['base_asset'] = binance_fund['symbol'].str.split('USD_').str[0]
            binance_fund['quote_asset'] = 'USD'
            binance_fund = binance_fund.rename(columns={'lastFundingRate':'funding_rate', 'nextFundingTime':'funding_time'})
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # replace '' to None
            binance_fund.replace("", None, inplace=True)
            binance_fund.loc[:, 'funding_rate'] = binance_fund['funding_rate'].astype(float)
            binance_fund.drop(columns=['markPrice','indexPrice','estimatedSettlePrice','interestRate','pair','time'], inplace=True)
            binance_fund['perpetual'] = binance_fund['symbol'].apply(lambda x: True if '_PERP' in x else False)
            return binance_fund
        else:
            raise Exception(f"Invalid futures_type: {futures_type}")
        
    def wallet_status(self):
        binance_network_list = [x['networkList'] for x in self.my_client.get_all_coins_info()]
        binance_network_list = [item for sublist in binance_network_list for item in sublist]
        binance_wallet_status_df = pd.DataFrame(binance_network_list)
        binance_wallet_status_df = binance_wallet_status_df.rename(columns={"network": "network_type", "coin": "asset", "withdrawEnable": "withdraw", "depositEnable": "deposit"})
        return binance_wallet_status_df
        
