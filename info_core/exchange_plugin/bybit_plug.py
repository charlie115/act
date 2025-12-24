import os
import sys
import datetime
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import time
import traceback
import requests
from pybit.unified_trading import HTTP
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper

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
        response = requests.get(self.server_url + self.instrument_url, params={"category":"spot", "limit": 1000})
        response_json = response.json()
        info_df = pd.DataFrame(response_json['result']['list']).rename(columns={"baseCoin":"base_asset", "quoteCoin":"quote_asset"})
        info_df = info_df.join(info_df['lotSizeFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['priceFilter'].apply(pd.Series)).drop(columns=['lotSizeFilter', 'priceFilter'], axis=1)
        info_df = info_df[info_df['status'] == 'Trading']
        return info_df

    def all_tickers(self, category='spot'):
        response = requests.get(self.server_url + self.ticker_url, params={"category":category})
        response_json = response.json()
        ticker_df = pd.DataFrame(response_json['result']['list'])
        return ticker_df
    
    def usd_m_exchange_info(self):
        response = requests.get(self.server_url + self.instrument_url, params={"category":"linear", "limit": 1000})
        response_json = response.json()
        info_df = pd.DataFrame(response_json['result']['list']).rename(columns={"baseCoin":"base_asset", "quoteCoin":"quote_asset", "contractType":"perpetual"})
        info_df = info_df.join(info_df['leverageFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['lotSizeFilter'].apply(pd.Series))
        info_df = info_df.join(info_df['priceFilter'].apply(pd.Series)).drop(columns=['leverageFilter','lotSizeFilter', 'priceFilter'], axis=1)
        # result = info_df['perpetual'].replace({'LinearPerpetual': True, 'LinearFutures': False}).astype(bool)
        # info_df['perpetual'] = result
        info_df['perpetual'] = pd.Series(info_df['perpetual'].replace({'LinearPerpetual': True, 'LinearFutures': False}), dtype="boolean")
        info_df = info_df[info_df['status'] == 'Trading']
        return info_df
    
    def coin_m_exchange_info(self):
        response = requests.get(self.server_url + self.instrument_url, params={"category":"inverse", "limit": 1000})
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
        info_df = info_df[info_df['status'] == 'Trading']
        return info_df

class InitBybitAdaptor:
    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        self.my_client = Bybit(my_access_key, my_secret_key)
        self.pub_client = Bybit()
        self.local_redis = RedisHelper()
        self.bybit_plug_logger = InfoCoreLogger("bybit_plug", logging_dir).logger
        self.bybit_plug_logger.info(f"bybit_plug_logger started.")

    def wallet_status(self):
        return self.my_client.wallet_status()

    def spot_exchange_info(self):
        return self.pub_client.spot_exchange_info()
    
    def spot_all_tickers(self):
        ticker_df = self.pub_client.all_tickers(category='spot')
        # Load bybit_spot_info_df
        fetched_bybit_spot_info_df = self.local_redis.get_data('bybit_spot_info_df')
        if fetched_bybit_spot_info_df is None:
            info_df = self.spot_exchange_info()
            self.bybit_plug_logger.info(f"fetched_bybit_spot_info_df is None, Fetched from API")
        else:
            info_df = pickle.loads(fetched_bybit_spot_info_df)
        merged_df = ticker_df.merge(info_df[['symbol','base_asset','quote_asset']], on='symbol', how='inner')
        merged_df = merged_df[(merged_df['bid1Price'] != '')&(merged_df['ask1Price'] != '')]
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
        # Load bybit_usd_m_info_df
        fetched_bybit_usd_m_info_df = self.local_redis.get_data('bybit_usd_m_info_df')
        if fetched_bybit_usd_m_info_df is None:
            info_df = self.usd_m_exchange_info()
            self.bybit_plug_logger.info(f"fetched_bybit_usd_m_info_df is None, Fetched from API")
        else:
            info_df = pickle.loads(fetched_bybit_usd_m_info_df)
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
        # Load bybit_coin_m_info_df
        fetched_bybit_coin_m_info_df = self.local_redis.get_data('bybit_coin_m_info_df')
        if fetched_bybit_coin_m_info_df is None:
            info_df = self.coin_m_exchange_info()
            self.bybit_plug_logger.info(f"fetched_bybit_coin_m_info_df is None, Fetched from API")
        else:
            info_df = pickle.loads(fetched_bybit_coin_m_info_df)
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

        # Include fundingIntervalHour if available in ticker data
        # Note: Bybit API uses 'fundingIntervalHour' (singular, already in hours)
        columns_to_select = ['symbol', 'base_asset', 'quote_asset', 'fundingRate', 'nextFundingTime']
        if 'fundingIntervalHour' in ticker_df.columns:
            columns_to_select.append('fundingIntervalHour')

        funding_df = ticker_df.loc[:, columns_to_select].copy()
        funding_df['perpetual'] = funding_df.loc[:, 'fundingRate'].apply(lambda x: True if x != '' else False)
        funding_df.loc[:, ['fundingRate', 'nextFundingTime']] = funding_df.loc[:, ['fundingRate', 'nextFundingTime']].apply(pd.to_numeric, errors='coerce')
        funding_df.loc[:, 'nextFundingTime'] = funding_df.loc[:, 'nextFundingTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
        # Convert 'nextFundingTime' to datetime
        funding_df.loc[:, 'nextFundingTime'] = pd.to_datetime(funding_df['nextFundingTime']).dt.tz_localize(None)
        funding_df = funding_df.rename(columns={'fundingRate': "funding_rate", "nextFundingTime": "funding_time"})

        # Add funding_interval_hours
        # Bybit fundingIntervalHour is already in hours (e.g., 8 for 8 hours)
        if 'fundingIntervalHour' in funding_df.columns:
            funding_df['funding_interval_hours'] = pd.to_numeric(funding_df['fundingIntervalHour'], errors='coerce')
            # Convert to nullable Int64 to preserve NaN as None
            funding_df['funding_interval_hours'] = funding_df['funding_interval_hours'].astype('Int64')
            funding_df.drop(columns=['fundingIntervalHour'], inplace=True)
        else:
            funding_df['funding_interval_hours'] = None

        return funding_df