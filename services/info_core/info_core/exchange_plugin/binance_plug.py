import sys
import os
import datetime
import traceback
import pandas as pd
import numpy as np
import time
from binance.client import Client
import _pickle as pickle

from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, recvWindow=45000, logging_dir=None):
        self.my_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.recvWindow = recvWindow
        self.local_redis = RedisHelper()
        self.binance_plug_logger = InfoCoreLogger("binance_plug", logging_dir).logger
        self.binance_plug_logger.info(f"binance_plug_logger started.")
        
        self.spot_exchange_info_columns_to_convert = [
            "baseAssetPrecision",
            "quotePrecision",
            "quoteAssetPrecision",
        ]
        
        self.spot_all_tickers_columns_to_convert = [
            "priceChange",
            "priceChangePercent",
            "weightedAvgPrice",
            "prevClosePrice",
            "lastPrice",
            "bidPrice",
            "askPrice",
            "openPrice",
            "highPrice",
            "lowPrice",
            "volume",
            "quoteVolume",
        ]
        
        self.usd_m_exchange_info_columns_to_convert = [
            "maintMarginPercent",
            "requiredMarginPercent",
            "pricePrecision",
            "quantityPrecision",
            "baseAssetPrecision",
            "quotePrecision",
            "settlePlan",
            "triggerProtect",
        ]
        
        self.usd_m_all_tickers_columns_to_convert = [
            "priceChange",
            "priceChangePercent",
            "weightedAvgPrice",
            "lastPrice",
            "lastQty",
            "openPrice",
            "highPrice",
            "lowPrice",
            "volume",
            "quoteVolume",
        ]
        
        self.coin_m_exchange_info_columns_to_convert = [
            "liquidationFee",
            "marketTakeBound",
            "contractSize",
            "pricePrecision",
            "quantityPrecision",
            "baseAssetPrecision",
            "quotePrecision",
            "equalQtyPrecision",
            "triggerProtect",
            "maintMarginPercent",
            "requiredMarginPercent"
        ]
        
        self.coin_m_all_tickers_columns_to_convert = [
            "priceChange",
            "priceChangePercent",
            "weightedAvgPrice",
            "lastPrice",
            "lastQty",
            "openPrice",
            "highPrice",
            "lowPrice",
            "volume",
            "baseVolume",
            "openTime",
            "closeTime"
        ]

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_client.get_deposit_history(asset=asset))
        deposit.loc[:,'insertTime'] = deposit['insertTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        deposit.loc[:, 'amount'] = deposit['amount'].astype(float)
        return deposit
    
    def spot_all_tickers(self):
        df = pd.DataFrame(self.pub_client.get_ticker())
        df.loc[:, self.spot_all_tickers_columns_to_convert] = df.loc[:, self.spot_all_tickers_columns_to_convert].apply(pd.to_numeric, errors='coerce')
        # Load binance_spot_info_df
        fetched_binance_spot_info_df = self.local_redis.get_data('binance_spot_info_df')
        if fetched_binance_spot_info_df is None:
            spot_exchange_info_df = self.spot_exchange_info()
            self.binance_plug_logger.info(f"fetched_binance_spot_info_df is None, Fetched from API")
        else:
            spot_exchange_info_df = pickle.loads(fetched_binance_spot_info_df)
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
        df.loc[:, self.spot_exchange_info_columns_to_convert] = df.loc[:, self.spot_exchange_info_columns_to_convert].apply(pd.to_numeric, errors='coerce')
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        return df
    
    def usd_m_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_exchange_info()['symbols'])
        
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def usd_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_ticker())
        df.loc[:, self.usd_m_all_tickers_columns_to_convert] = df.loc[:, self.usd_m_all_tickers_columns_to_convert].apply(pd.to_numeric, errors='coerce')
        # Load binance_usd_m_info_df
        fetched_binance_usd_m_info_df = self.local_redis.get_data('binance_usd_m_info_df')
        if fetched_binance_usd_m_info_df is None:
            usd_m_exchange_info_df = self.usd_m_exchange_info()
            self.binance_plug_logger.info(f"fetched_binance_usd_m_info_df is None, Fetched from API")
        else:
            usd_m_exchange_info_df = pickle.loads(fetched_binance_usd_m_info_df)
        # Load binance_spot_ticker_df
        fetched_binance_spot_ticker_df = self.local_redis.get_data('binance_spot_ticker_df')
        if fetched_binance_spot_ticker_df is None:
            binance_spot_ticker_df = self.spot_all_tickers()
            self.binance_plug_logger.info(f"fetched_binance_spot_ticker_df is None, Fetched from API")
        else:
            binance_spot_ticker_df = pickle.loads(fetched_binance_spot_ticker_df)
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
        df.loc[:, self.coin_m_exchange_info_columns_to_convert] = df.loc[:, self.coin_m_exchange_info_columns_to_convert].apply(pd.to_numeric, errors='coerce')
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def coin_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_coin_ticker())
        df.loc[:, self.coin_m_all_tickers_columns_to_convert] = df.loc[:, self.coin_m_all_tickers_columns_to_convert].apply(pd.to_numeric, errors='coerce')
        df['base_asset'] = df['symbol'].str.split('USD_').str[0]
        df['quote_asset'] = 'USD' # ?
        df['atp24h'] = df['volume'] * 100
        return df

    def _get_funding_info(self):
        """
        Fetch funding rate info including interval hours from Binance API.

        Endpoint: GET /fapi/v1/fundingInfo
        Returns DataFrame with symbol and fundingIntervalHours.
        """
        try:
            import requests
            response = requests.get("https://fapi.binance.com/fapi/v1/fundingInfo", timeout=10)
            response.raise_for_status()
            data = response.json()
            df = pd.DataFrame(data)
            if 'symbol' in df.columns and 'fundingIntervalHours' in df.columns:
                return df[['symbol', 'fundingIntervalHours']]
            return pd.DataFrame(columns=['symbol', 'fundingIntervalHours'])
        except Exception as e:
            self.binance_plug_logger.error(f"Failed to fetch funding info: {e}")
            return pd.DataFrame(columns=['symbol', 'fundingIntervalHours'])

    def get_fundingrate(self, futures_type="USD_M"):
        bi_client = self.pub_client
        if futures_type == "USD_M":
            # Load binance_usd_m_info_df
            fetched_binance_usd_m_info_df = self.local_redis.get_data('binance_usd_m_info_df')
            if fetched_binance_usd_m_info_df is None:
                usd_m_exchange_info_df = self.usd_m_exchange_info()
                self.binance_plug_logger.info(f"fetched_binance_usd_m_info_df is None, Fetched from API")
            else:
                usd_m_exchange_info_df = pickle.loads(fetched_binance_usd_m_info_df)
            # Remove status != TRADING
            usd_m_exchange_info_df = usd_m_exchange_info_df[usd_m_exchange_info_df['status'] == 'TRADING']
            binance_fund = pd.DataFrame(bi_client.futures_mark_price())
            binance_fund = binance_fund.merge(usd_m_exchange_info_df[['symbol','base_asset','quote_asset']], on='symbol', how='inner')
            binance_fund = binance_fund.rename(columns={'lastFundingRate':'funding_rate', 'nextFundingTime':'funding_time'})
            # binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            # binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # Convert 'funding_time' from milliseconds to datetime with UTC timezone
            binance_fund['funding_time'] = pd.to_datetime(binance_fund['funding_time'], unit='ms', utc=True)
            # Remove timezone information if needed
            binance_fund['funding_time'] = binance_fund['funding_time'].dt.tz_localize(None)

            # Fetch and merge funding interval hours
            funding_info_df = self._get_funding_info()
            if not funding_info_df.empty:
                binance_fund = binance_fund.merge(funding_info_df, on='symbol', how='left')
                binance_fund['funding_interval_hours'] = pd.to_numeric(binance_fund['fundingIntervalHours'], errors='coerce')
                # Convert to nullable Int64 to preserve NaN as None
                binance_fund['funding_interval_hours'] = binance_fund['funding_interval_hours'].astype('Int64')
                binance_fund.drop(columns=['fundingIntervalHours'], inplace=True)
            else:
                binance_fund['funding_interval_hours'] = None

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
            # binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            # binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # Convert 'funding_time' from milliseconds to datetime with UTC timezone
            binance_fund['funding_time'] = pd.to_datetime(binance_fund['funding_time'], unit='ms', errors='coerce', utc=True)
            # Remove timezone information if needed
            binance_fund['funding_time'] = binance_fund['funding_time'].dt.tz_localize(None)
            # COIN-M perpetuals use 8 hour funding interval
            binance_fund['funding_interval_hours'] = 8
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
        
