import os
import sys
import datetime
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import time
import traceback
import requests
from pybit.unified_trading import HTTP

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import TradeCoreLogger

class Bybit:
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.server_url = "https://api.bybit.com"
        self.instrument_url = "/v5/market/instruments-info"
        self.ticker_url = "/v5/market/tickers"
        self.session = HTTP(testnet=False, api_key=api_key, api_secret=secret_key)

    def wallet_status(self):
        wallet_df = pd.DataFrame(self.session.get_coin_info()['result']['rows'])
        wallet_df_exploded = wallet_df.explode('chains')
        wallet_df = wallet_df_exploded.join(wallet_df_exploded['chains'].apply(pd.Series))
        wallet_df = wallet_df.drop(['name','chains'], axis=1).reset_index(drop=True).rename(columns={'coin':'asset', 'chainDeposit':'deposit', 'chainWithdraw':'withdraw', 'chain': 'network_type'})
        wallet_df.loc[:, 'deposit'] = wallet_df['deposit'].replace('1', True).replace('0', False)
        wallet_df.loc[:, 'withdraw'] = wallet_df['withdraw'].replace('1', True).replace('0', False)
        wallet_df = wallet_df.drop_duplicates().reset_index(drop=True)
        return wallet_df

    def spot_exchange_info(self):
        response = requests.get(self.server_url + self.instrument_url, params={"category":"spot"})
        response_json = response.json()
        info_df = pd.DataFrame(response_json['result']['list']).rename(columns={"baseCoin":"base_asset", "quoteCoin":"quote_asset"})
        info_df = info_df.join(info_df['lotSizeFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['priceFilter'].apply(pd.Series)).drop(columns=['lotSizeFilter', 'priceFilter'], axis=1)
        return info_df

    def all_tickers(self, category='spot'):
        response = requests.get(self.server_url + self.ticker_url, params={"category":category})
        response_json = response.json()
        ticker_df = pd.DataFrame(response_json['result']['list'])
        return ticker_df
    
    def usd_m_exchange_info(self):
        response = requests.get(self.server_url + self.instrument_url, params={"category":"linear"})
        response_json = response.json()
        info_df = pd.DataFrame(response_json['result']['list']).rename(columns={"baseCoin":"base_asset", "quoteCoin":"quote_asset", "contractType":"perpetual"})
        info_df = info_df.join(info_df['leverageFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['lotSizeFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['priceFilter'].apply(pd.Series)).drop(columns=['leverageFilter','lotSizeFilter', 'priceFilter'], axis=1)
        # result = info_df['perpetual'].replace({'LinearPerpetual': True, 'LinearFutures': False}).astype(bool)
        # info_df['perpetual'] = result
        info_df['perpetual'] = pd.Series(info_df['perpetual'].replace({'LinearPerpetual': True, 'LinearFutures': False}), dtype="boolean")
        return info_df
    
    def coin_m_exchange_info(self):
        response = requests.get(self.server_url + self.instrument_url, params={"category":"inverse"})
        response_json = response.json()
        info_df = pd.DataFrame(response_json['result']['list']).rename(columns={"baseCoin":"base_asset", "quoteCoin":"quote_asset", "contractType":"perpetual"})
        info_df = info_df.join(info_df['leverageFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['lotSizeFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['priceFilter'].apply(pd.Series)).drop(columns=['leverageFilter','lotSizeFilter', 'priceFilter'], axis=1)
        # result = info_df['perpetual'].replace('InversePerpetual', True)
        # result = result.replace('InverseFutures', False)
        # result = result.infer_objects(copy=False)
        # info_df.loc[:, 'perpetual'] = result
        info_df['perpetual'] = pd.Series(info_df['perpetual'].replace({'InversePerpetual': True, 'InverseFutures': False}), dtype="boolean")
        return info_df

class InitBybitAdaptor:
    def __init__(self, my_access_key=None, my_secret_key=None, info_dict={}, logging_dir=None):
        self.my_client = Bybit(my_access_key, my_secret_key)
        self.pub_client = Bybit()
        self.info_dict = info_dict
        self.bybit_plug_logger = TradeCoreLogger("bybit_plug", logging_dir).logger
        self.bybit_plug_logger.info(f"bybit_plug_logger started.")

    def wallet_status(self):
        return self.my_client.wallet_status()

    def spot_exchange_info(self):
        return self.pub_client.spot_exchange_info()
    
    def spot_all_tickers(self):
        ticker_df = self.pub_client.all_tickers(category='spot')        
        if self.info_dict is None or self.info_dict.get('bybit_spot_info_df') is None:
            info_df = self.spot_exchange_info()
            self.bybit_plug_logger.info(f"self.info_dict is None or self.info_dict.get('bybit_spot_info_df') is None, Fetched from API")
        else:
            info_df = self.info_dict.get('bybit_spot_info_df')
        merged_df = ticker_df.merge(info_df[['symbol','base_asset','quote_asset']], on='symbol', how='inner')
        merged_df = merged_df[merged_df['bid1Price'] != '']
        merged_df.loc[:, 'bid1Price':'usdIndexPrice'] = merged_df.loc[:, 'bid1Price':'usdIndexPrice'].astype(float)
        merged_df['quote_symbol'] = merged_df['quote_asset'] + 'USDT'
        temp_df = merged_df.copy()
        temp_df.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        merged_df = merged_df.merge(temp_df[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        merged_df['atp24h'] = merged_df['turnover24h'] * merged_df['lastPrice2']
        merged_df.drop(columns=['symbol2','quote_symbol','lastPrice2'], inplace=True)
        merged_df.loc[merged_df['quote_asset'] == 'USDT', 'atp24h'] = merged_df.loc[merged_df['quote_asset'] == 'USDT', 'turnover24h']
        return merged_df
    
    def usd_m_exchange_info(self):
        return self.pub_client.usd_m_exchange_info()
    
    def usd_m_all_tickers(self):
        ticker_df = self.pub_client.all_tickers(category='linear')
        if self.info_dict is None or self.info_dict.get('bybit_usd_m_info_df') is None:
            info_df = self.usd_m_exchange_info()
            self.bybit_plug_logger.info(f"self.info_dict is None or self.info_dict.get('bybit_usd_m_info_df') is None, Fetched from API")
        else:
            info_df = self.info_dict.get('bybit_usd_m_info_df')
        merged_df = ticker_df.merge(info_df[['symbol','base_asset','quote_asset']], on='symbol', how='inner')
        merged_df.loc[:, ['lastPrice','turnover24h','volume24h']] = merged_df.loc[:, ['lastPrice','turnover24h','volume24h']].astype(float)
        merged_df['quote_symbol'] = merged_df['quote_asset'] + 'USDT'
        temp_df = merged_df.copy()
        temp_df.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        merged_df = merged_df.merge(temp_df[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        merged_df['atp24h'] = merged_df['turnover24h'] * merged_df['lastPrice2']
        merged_df.drop(columns=['symbol2','quote_symbol','lastPrice2'], inplace=True)
        merged_df.loc[merged_df['quote_asset'] == 'USDT', 'atp24h'] = merged_df.loc[merged_df['quote_asset'] == 'USDT', 'turnover24h']
        return merged_df
    
    def coin_m_exchange_info(self):
        return self.pub_client.coin_m_exchange_info()
    
    def coin_m_all_tickers(self):
        ticker_df = self.pub_client.all_tickers(category='inverse')
        if self.info_dict is None or self.info_dict.get('bybit_coin_m_info_df') is None:
            info_df = self.coin_m_exchange_info()
            self.bybit_plug_logger.info(f"self.info_dict is None or self.info_dict.get('bybit_coin_m_info_df') is None, Fetched from API")
        else:
            info_df = self.info_dict.get('bybit_coin_m_info_df')
        merged_df = ticker_df.merge(info_df[['symbol','base_asset','quote_asset']], on='symbol', how='inner')
        merged_df.loc[:, ['lastPrice','turnover24h','volume24h']] = merged_df.loc[:, ['lastPrice','turnover24h','volume24h']].astype(float)
        merged_df['quote_symbol'] = merged_df['quote_asset'] + 'USDT'
        merged_df['atp24h'] = merged_df['volume24h']
        return merged_df
    
    def get_fundingrate(self, futures_type='USD_M'):
        if futures_type == "USD_M":
            ticker_df = self.usd_m_all_tickers()
        else:
            ticker_df = self.coin_m_all_tickers()
        funding_df = ticker_df.loc[:, ['symbol','base_asset','quote_asset','fundingRate','nextFundingTime']]
        funding_df['perpetual'] = funding_df.loc[:, 'fundingRate'].apply(lambda x: True if x != '' else False)
        funding_df.loc[:, ['fundingRate','nextFundingTime']] = funding_df.loc[:, ['fundingRate','nextFundingTime']].apply(pd.to_numeric, errors='coerce')
        funding_df.loc[:, 'nextFundingTime'] = funding_df.loc[:, 'nextFundingTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
        # Convert 'nextFundingTime' to datetime
        funding_df.loc[:, 'nextFundingTime'] = pd.to_datetime(funding_df['nextFundingTime']).dt.tz_localize(None)
        funding_df = funding_df.rename(columns={'fundingRate':"funding_rate", "nextFundingTime":"funding_time"})
        return funding_df