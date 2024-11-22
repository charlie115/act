import sys
import os
import datetime
import traceback
import pickle
import pandas as pd
from queue import Queue
import numpy as np
import time
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager # For MarginCallback
import asyncio # For MarginCallback
from psycopg2 import extras
from threading import Thread
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import TradeCoreLogger
from etc.acw_api import AcwApi
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from etc.redis_connector.redis_helper import RedisHelper
from etc.utils import get_trade_df
from api.utils import decrypt_data, MyException
from etc.redis_connector.redis_helper import RedisHelper

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, recvWindow=45000, logging_dir=None):
        self.my_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.recvWindow = recvWindow
        self.local_redis = RedisHelper()
        self.binance_plug_logger = TradeCoreLogger("binance_plug", logging_dir).logger
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
        # Load info_dict
        fetched_info_dict = self.local_redis.get_data('info_dict')
        if fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_spot_info_df') is None:
            # TEST
            spot_exchange_info_df = self.spot_exchange_info()
            self.binance_plug_logger.info(f"fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_spot_info_df') is None, Fetched from API")
        else:
            spot_exchange_info_df = pickle.loads(fetched_info_dict).get('binance_spot_info_df')
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
        # Load info_dict
        fetched_info_dict = self.local_redis.get_data('info_dict')
        if fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_usd_m_info_df') is None:
            # TEST
            usd_m_exchange_info_df = self.usd_m_exchange_info()
            self.binance_plug_logger.info(f"fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_usd_m_info_df') is None, Fetched from API")
        else:
            usd_m_exchange_info_df = pickle.loads(fetched_info_dict).get('binance_usd_m_info_df')
        if fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_spot_ticker_df') is None:
            # TEST
            binance_spot_ticker_df = self.spot_all_tickers()
            self.binance_plug_logger.info(f"fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_spot_ticker_df') is None, Fetched from API")
        else:
            binance_spot_ticker_df = pickle.loads(fetched_info_dict).get('binance_spot_ticker_df')
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

    def get_fundingrate(self, futures_type="USD_M"):
        bi_client = self.pub_client
        if futures_type == "USD_M":
            # Load info_dict
            fetched_info_dict = self.local_redis.get_data('info_dict')
            if fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_usd_m_info_df') is None:
                usd_m_exchange_info_df = self.usd_m_exchange_info()
                self.binance_plug_logger.info(f"fetched_info_dict is None or pickle.loads(fetched_info_dict).get('binance_usd_m_info_df') is None, Fetched from API")
            else:
                usd_m_exchange_info_df = pickle.loads(fetched_info_dict).get('binance_usd_m_info_df')
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

################################################################################################################################################
class UserBinanceAdaptor:
    def __init__(self, admin_id, acw_api, postgres_db_dict=None, market_code_combination=None, margin_liquidation_call_trade_queue=None, recvWindow=45000, logging_dir=None):
        self.admin_id = admin_id
        self.local_redis_client = RedisHelper(host='localhost', port=6379, db=0, passwd=None)
        self.user_client_dict = {}
        self.user_stream_monitoring_list = []
        self.recvWindow = recvWindow
        self.trade_retry_term_sec = 0.2
        self.trade_retry_limit = 2
        self.order_info_retry_term_sec = 3
        self.order_info_retry_limit = 20
        self.acw_api = acw_api
        self.margin_liquidation_call_trade_queue = margin_liquidation_call_trade_queue
        if postgres_db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
            self.user_api_key_df = self.load_user_api_keys()
        else:
            self.postgres_client = None
            self.user_api_key_df = None
        self.market_code_combination = market_code_combination
        if market_code_combination is not None:
            self.market_code = [x for x in market_code_combination.split(':') if 'BINANCE' in x][0]
            self.market, self.quote_asset = self.market_code.split('/')
            self.exchange = self.market.split('_')[0]
            self.market_type = self.market.replace(self.exchange+'_','')
            self.counterpart_market_code = [x for x in market_code_combination.split(':') if 'BINANCE' not in x][0]
            self.counterpart_market, self.counterpart_quote_asset = self.counterpart_market_code.split('/')
            self.counterpart_exchange = self.counterpart_market.split('_')[0]
            self.counterpart_market_type = self.counterpart_market.replace(self.counterpart_exchange+'_','')
            # Check whether the market_type is supported
            if self.market_type not in ["USD_M"]:
                raise Exception(f"Invalid market_type: {self.market_type}")
            logger_name = self.market_code.replace('/', '__')
            self.logger = TradeCoreLogger(f"user_binance_plug_{logger_name}", logging_dir).logger
            self.logger.info(f"user_binance_plug_{self.market_code} started.")
            self.load_user_api_keys_thread = Thread(target=self.loop_load_user_api_keys, args=(5,), daemon=True)
            self.load_user_api_keys_thread.start()
            # queue for handling order info
            self.order_info_dict_queue = Queue()
            # thread for handling order info
            self.handle_order_info_queue_thread = Thread(target=self.handle_order_info_queue_loop, daemon=True)
            self.handle_order_info_queue_thread.start()
            if self.margin_liquidation_call_trade_queue is not None:
                # thread for monitoring margin call and liquidation call
                self.start_user_socket_stream(market_type=self.market_type)
        else:
            self.market_code = None
            self.market = None
            self.quote_asset = None
            self.exchange = None
            self.market_type = None
            self.counterpart_market_code = None
            self.counterpart_market = None
            self.counterpart_quote_asset = None
            self.counterpart_exchange = None
            self.counterpart_market_type = None
            self.logger = TradeCoreLogger(f"user_binance_plug", logging_dir).logger
            self.logger.info(f"user_binance_plug started.")
        
    def load_user_api_keys(self, table_name='exchange_api_key'):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        sql = f"SELECT * FROM {table_name} WHERE exchange='BINANCE'"
        curr.execute(sql)
        user_api_key_df = pd.DataFrame(curr.fetchall())
        self.postgres_client.pool.putconn(conn)
        # Check whether returned dataframe is empty or not
        if len(user_api_key_df) == 0:
            # Get the names of the columns and create an empty dataframe
            column_names = self.postgres_client.get_column_names(table_name)
            self.user_api_key_df = pd.DataFrame(columns=column_names)
            return self.user_api_key_df
        else:
            user_api_key_df[['access_key', 'secret_key']] = user_api_key_df[['access_key', 'secret_key']].map(lambda x: x.tobytes() if isinstance(x, memoryview) else x)
            user_api_key_df[['access_key', 'secret_key']] = user_api_key_df[['access_key', 'secret_key']].map(lambda x: decrypt_data(x).decode('utf-8') if x is not None else None)
            self.user_api_key_df = user_api_key_df
            return user_api_key_df

    def loop_load_user_api_keys(self, loop_interval_secs=5):
        self.logger.info(f"loop_load_user_api_keys started.")
        while True:
            try:
                self.user_api_key_df = self.load_user_api_keys()
            except Exception as e:
                self.logger.error(f"loop_load_user_api_keys|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, "loop_load_user_api_keys", str(e))
            time.sleep(loop_interval_secs)

    def get_api_key_tup(self, trade_config_uuid, futures, raise_error=True):
        # Pick one randomly using .sample among the same trade_config_uuid and futures flag
        try:
            api_key_df = self.user_api_key_df[(self.user_api_key_df['trade_config_uuid']==trade_config_uuid) & (self.user_api_key_df['futures']==futures)].sample(1)
            return (api_key_df['access_key'].values[0], api_key_df['secret_key'].values[0])
        except ValueError:
            if raise_error:
                raise MyException(f"No API Key found for trade_config_uuid: {trade_config_uuid}, futures: {futures}", error_code=1)
            else:
                return (None, None)

    def load_user_client(self, access_key, secret_key):
        user_client = self.user_client_dict.get(access_key)
        if user_client is None:
            self.user_client_dict[access_key] = Client(access_key, secret_key)
            return self.user_client_dict[access_key]
        else:
            return user_client

    def check_api_key(self, access_key, secret_key, futures=False):
        self.user_client_dict.pop(access_key, None)
        try:
            if futures is False:
                self.get_spot_balance(access_key, secret_key)
            else:
                self.get_usdm_balance(access_key, secret_key)
            return (True, 'OK')
        except Exception as e:
            self.user_client_dict.pop(access_key, None)
            return (False, str(e))

    def get_deposit_address(self, access_key, secret_key, asset='USDT', network='TRX'):
        client = self.load_user_client(access_key, secret_key)
        deposit_address = client.get_deposit_address(coin=asset, network=network)
        if deposit_address.get('tag') == '':
            deposit_address['tag'] = None
        output_dict = {
            "asset": deposit_address['coin'],
            "address": deposit_address['address'],
            "tag": deposit_address['tag']
        }
        return output_dict

    def get_deposit_amount(self, access_key, secret_key, txid, asset='USDT'):
        client = self.load_user_client(access_key, secret_key)
        deposit_df = pd.DataFrame(client.get_deposit_history(asset=asset))
        deposit_df = deposit_df[deposit_df['coin']==asset]
        deposit_df = deposit_df[deposit_df['txId']==txid]
        if len(deposit_df) == 0:
            output_dict = {
                "status": f"{txid}에 대한 입금 내역이 존재하지 않습니다. 잠시 후 다시 조회해 주세요.",
                "deposited": False,
                "amount": 0
            }
            return output_dict
        deposit_df.loc[:,'insertTime'] = deposit_df['insertTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        deposit_df.loc[:, 'amount'] = deposit_df['amount'].astype(float)
        fetched_status = deposit_df['status'].values[0]
        fetched_amount = deposit_df['amount'].values[0]
        output_dict = {
            "status": f"{asset} {fetched_amount}개에 대한 입금이 확인되었습니다." if fetched_status == 1 else "거래소 입금반영중입니다. 잠시 후 다시 조회해 주세요.",
            "deposited": True if fetched_status == 1 else False,
            "amount": fetched_amount
        }
        return output_dict

    def get_spot_balance(self, access_key, secret_key):
        client = self.load_user_client(access_key, secret_key)
        spot_balance = pd.DataFrame(client.get_account()['balances'])
        spot_balance.loc[:,['free','locked']] = spot_balance[['free','locked']].astype(float)
        spot_balance_df = spot_balance[spot_balance['free']>0].reset_index(drop=True)
        return spot_balance_df

    def get_usdm_balance(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        usdm_balance_df = pd.DataFrame(client.futures_account()['assets'])
        usdm_balance_df.loc[:, ['walletBalance', 'unrealizedProfit', 'availableBalance']] = usdm_balance_df[['walletBalance', 'unrealizedProfit', 'availableBalance']].astype(float)
        if return_dict is None:
            return usdm_balance_df
        else:
            return_dict['res'] = usdm_balance_df

    def get_balance(self, access_key, secret_key, market_type='SPOT'):
        if market_type == "SPOT":
            return self.get_spot_balance(access_key, secret_key)
        elif market_type == "USD_M":
            return self.get_usdm_balance(access_key, secret_key)
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
        
    def get_market_maxqty(self, market_type, symbol):
        if market_type == "SPOT":
            # Not available yet. raise error
            raise Exception(f"market_type: {market_type} is not supported yet.")
        elif market_type == "USD_M":
            info_df = pickle.loads(self.local_redis_client.get_data('TRADE_CORE|binance_usd_m_info_df'))
            market_maxqty = info_df[info_df['symbol']==symbol]['MarketMaxQty'].values[0]
            return market_maxqty
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")

    def change_margin_type(self, access_key, secret_key, market_type, symbol, margin_type='ISOLATED'):
        client = self.load_user_client(access_key, secret_key)
        try:
            if market_type == "USD_M":
                res = client.futures_change_margin_type(
                    symbol=symbol,
                    marginType=margin_type
                )
            else:
                raise Exception(f"market_type: {market_type} is not supported yet.")
        except Exception as e:
            error_code = e.code
            if error_code == -4046:
                res = {'code': 200, 'msg': e.message}
            else:
                self.logger.error(f"change_margin_type|{traceback.format_exc()}")
                raise Exception(e)
        return res

    def change_leverage(self, access_key, secret_key, market_type, symbol, leverage):
        client = self.load_user_client(access_key, secret_key)
        if market_type == "USD_M":
            res = client.futures_change_leverage(symbol=symbol, leverage=leverage)
        else:
            raise Exception(f"market_type: {market_type} is not supported yet.")
        return res

    def fetch_order_info(self, access_key, secret_key, symbol, order_id, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0
        try:
            while retry_count <= self.order_info_retry_limit:
                try:
                    if market_type == "USD_M":
                        res = client.futures_get_order(symbol=symbol, orderId=order_id, recvWindow=self.recvWindow)
                    else:
                        raise Exception(f"market_type: {market_type} is not supported yet.")
                    if return_dict is not None:
                        return_dict['res'] = res
                        return_dict['error_code'] = None
                    return res
                except Exception as e:
                    if e.code in [-2013, -1000, -1001, -1008]: # Binance -Order not exist, -Unknown error, -Internal error, -SERVER BUSY
                        time.sleep(self.order_info_retry_term_sec)
                        retry_count += 1
                        if retry_count == self.order_info_retry_limit:
                            raise e
                    else:
                        raise e
        except Exception as e:
            self.logger.error(f"fetch_order_info|order_id:{order_id}\nerror:{e}\n{traceback.format_exc()}")
            if return_dict is None:
                raise e
            else:
                return_dict['res'] = e
                return_dict['error_code'] = e.code

    def save_order_info_to_db(self, trade_config_uuid, trade_uuid, res, market_type):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            if market_type == "USD_M":
                order_id = str(res['orderId'])
                executed_price = float(res['avgPrice'])
                executed_qty = float(res['executedQty'])
                side = res['side']
                order_type = res['type']
                symbol = res['symbol']
                fee = executed_price * executed_qty * 0.0005 # TEMP
                sql = """INSERT INTO order_history(order_id, trade_config_uuid, trade_uuid, registered_datetime, order_type, market_code, symbol, quote_asset, side, price, qty, fee, remark)
                        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                val = (order_id, trade_config_uuid, trade_uuid, datetime.datetime.utcnow(), order_type, self.market_code, symbol, self.quote_asset, side, executed_price, executed_qty, fee, None)
                curr.execute(sql, val)
                conn.commit()
            else:
                raise Exception(f"market_type: {market_type} is not supported yet.")
            self.postgres_client.pool.putconn(conn)
        except Exception as e:
            self.logger.error(f"save_order_info_to_db|{traceback.format_exc()}")
            self.postgres_client.pool.putconn(conn)
            raise e

    def handle_order_info_queue_loop(self):
        self.logger.info(f"handle_order_info_queue_loop started.")
        while True:
            try:
                order_info_dict = self.order_info_dict_queue.get()
                access_key, secret_key = self.get_api_key_tup(order_info_dict['trade_config_uuid'], (False if order_info_dict['market_type'] == "SPOT" else True))
                # API call
                fetched_order_info_res = self.fetch_order_info(access_key, secret_key, order_info_dict['symbol'], order_info_dict['order_id'], order_info_dict['market_type'])
                # process res and save data to db
                self.save_order_info_to_db(order_info_dict['trade_config_uuid'], order_info_dict['trade_uuid'], fetched_order_info_res, order_info_dict['market_type'])
            except Exception as e:
                self.logger.error(f"handle_order_info_queue_loop|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, "handle_order_info_queue_loop", str(e))
                time.sleep(3)
            time.sleep(0.05)

    def market_long(self, access_key, secret_key, symbol, qty, market_type, reduce_only=False, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            if retry_count >= 1:
                self.logger.info(f"market_enter|retry_count: {retry_count}, retry_term_sec: {self.trade_retry_term_sec}, retry_count_limit: {self.trade_retry_limit}") # For TESTING
            try:
                if market_type == "USD_M":
                    res = client.futures_create_order(
                        symbol=symbol,
                        side='BUY',
                        type='MARKET',
                        quantity=qty,
                        recvWindow=self.recvWindow,
                        reduceOnly='true' if reduce_only else 'false'
                    )
                    if return_dict is not None:
                        return_dict['res'] = res
                        return_dict['error_code'] = None
                    return res
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if e.code not in [-1000, -1001, -1008] or retry_count >= self.trade_retry_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = e.code
                        return
            retry_count += 1

    def market_short(self, access_key, secret_key, symbol, qty, market_type, reduce_only=False, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            if retry_count >= 1:
                self.logger.info(f"market_short|retry_count: {retry_count}, retry_term_sec: {self.trade_retry_term_sec}, retry_count_limit: {self.trade_retry_limit}") # For TESTING
            try:
                if market_type == "USD_M":
                    res = client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=qty,
                    recvWindow=self.recvWindow,
                    reduceOnly='true' if reduce_only else 'false'
                    )
                    if return_dict is not None:
                        return_dict['res'] = res
                        return_dict['error_code'] = None
                    return res
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if e.code not in [-1000, -1001, -1008] or retry_count >= self.trade_retry_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = e.code
                        return
            retry_count += 1

    def position_information(self, access_key, secret_key, market_type, symbol, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0
        while retry_count <= self.trade_retry_limit:
            try:
                if market_type == "USD_M":
                    res = client.futures_position_information()
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
                position_df = pd.DataFrame(res)
                symbol_df = position_df[position_df['symbol']==symbol]
                if len(symbol_df) == 0:
                    position_qty = 0
                    liquidation_price = None
                else:
                    position_qty = abs(float(symbol_df['positionAmt'].iloc[0]))
                    liquidation_price = float(symbol_df['liquidationPrice'].iloc[0])
                if return_dict is not None:
                    return_dict['res'] = (position_qty, liquidation_price)
                    return_dict['error_code'] = None
                return (position_qty, liquidation_price)
            except Exception as e:
                if e.code not in [-1000, -1001, -1008] or retry_count >= self.trade_retry_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = e.code
                        return
            retry_count += 1

    def all_position_information(self, access_key, secret_key, market_type='USD_M', return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        if market_type == "USD_M":
            res = client.futures_position_information()
            position_df = pd.DataFrame(res)
            if position_df.empty:
                return position_df
            columns_to_convert = [
                "positionAmt",
                "entryPrice",
                "breakEvenPrice",
                "markPrice",
                "unRealizedProfit",
                "liquidationPrice",
                "isolatedMargin",
                "notional",
                "isolatedWallet",
                "initialMargin",
                "maintMargin",
                "positionInitialMargin",
                "openOrderInitialMargin",
                "adl",
            ]
            # Convert columns to numeric, coercing errors to NaN
            position_df[columns_to_convert] = position_df[columns_to_convert].apply(pd.to_numeric, errors='coerce')

            # Perform the leverage calculation
            position_df['leverage'] = (
                abs(position_df['notional'] / position_df['positionInitialMargin'])
            ).round(0).astype(int)
            position_df = position_df[position_df['positionAmt']!=0].reset_index(drop=True)
            
            # Add marginType info
            position_df['marginType'] = position_df['isolatedMargin'].apply(lambda x: 'crossed' if x == 0 else 'isolated')
        elif market_type == "COIN_M":
            # raise error for not supported yet
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
        if return_dict is None:
            return position_df
        else:
            try:
                return_dict['res'] = position_df
                return_dict['error_code'] = None
            except Exception as e:
                self.logger.error(f"all_position_information|{traceback.format_exc()}")
                return_dict['res'] = e
                return_dict['error_code'] = e.code

    def get_futures_account(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        if return_dict is None:
            res = client.futures_account()
            res_df = pd.DataFrame(res['assets'])
            res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
            return res_df
        else:
            try:
                res = client.futures_account()
                res_df = pd.DataFrame(res['assets'])
                res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
                return_dict['res'] = res_df
                return_dict['state'] = 'OK'
            except Exception as e:
                self.logger.error(f"get_futures_account|{traceback.format_exc()}")
                return_dict['res'] = e
                return_dict['state'] = 'ERROR'

    # Functions for monitoring binance margin call
    def usd_m_margin_call_callback(self, res, trade_config_uuid, margin_call_mode, telegram_id):
        try:
            # margin_call_mode == None -> Do nothing,
            # margin_call_mode == 1 -> Only warning message, 
            # margin_call_mode == 2 -> message & auto exit
            if margin_call_mode == None:
                return
            elif margin_call_mode == 1 or margin_call_mode == 2:
                margin_type = res['p'][0]['mt'] # CROSSED or ISOLATED
                base_asset = res['p'][0]['s'].replace('USDT', '')
                position_side = res['p'][0]['ps']
                mark_price = float(res['p'][0]['mp'])
                position_amount = float(res['p'][0]['pa'])
                unrealized_pnl = float(res['p'][0]['up'])
                # Send margin call message
                title = f"마진콜 경고! 바이낸스 {base_asset}USDT 의 미실현손익이 위험수위에 도달했습니다.\n"
                body = f"바이낸스 포지션: {position_side}, 마진타입: {margin_type}\n"
                body += f"미실현손익: {unrealized_pnl}USDT, 포지션수량: {position_amount}\n"
                body += f"{base_asset}USDT 현재 Mark가격: {mark_price}USDT"
                msg_full = f"{title}\n{body}"
                self.acw_api.create_message_thread(telegram_id, title, msg_full, 'WARNING', send_times=5, send_term=5)

                # If margin_call_mode == 2, execute auto exit
                if margin_call_mode == 2:
                    body = f"마진콜 모니터링 설정에 따라, 자동거래에 진입되어 있는 {self.exchange}와 {self.counterpart_exchange}의 포지션을 자동정리합니다."
                    self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리", body, 'INFO')

                    trade_df = get_trade_df(self.market_code_combination, trade_support=True)
                    waiting_df = trade_df[(trade_df['trade_config_uuid']==trade_config_uuid)&(trade_df['base_asset']==base_asset)&(trade_df['trade_switch']==-1)]
                    self.logger.info(f"청산자동정리 실행|trade_config_uuid: {trade_config_uuid}, symbol: {base_asset}, symbol: {base_asset}") # test
                    if len(waiting_df) == 0:
                        body = f"{base_asset}USDT는 차익거래에 진입되어있는 상태가 아닙니다.\n"
                        body += f"포지션 자동정리를 취소합니다."
                        self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리 취소", body, 'INFO')
                        return                    

                    # 여기부터
                    # There's waiting trade
                    for row_tup in waiting_df.iterrows():
                        # load api keys
                        # access_key, secret_key = self.get_api_key_tup(trade_config_uuid, futures=True)
                        row = row_tup[1]
                        trade_uuid = row['uuid']
                        base_asset = row['base_asset']
                        last_trade_history_uuid = row['last_trade_history_uuid']
                        
                        # Order record validation
                        if last_trade_history_uuid is None:
                            body = f"거래 UUID:{trade_uuid}({base_asset})에 대한 거래 체결기록이 조회되지 않습니다.\n"
                            body += f"포지션 자동정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리 취소", body, 'INFO')
                            continue
                        # UPDATE database
                        try:
                            conn = self.postgres_client.pool.getconn()
                            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                            curr.execute("""UPDATE trade SET last_updated_datetime=%s, trade_switch=%s WHERE uuid=%s""", (datetime.datetime.utcnow(), 1, trade_uuid))
                            conn.commit()
                            self.postgres_client.pool.putconn(conn)
                        except Exception as e:
                            self.postgres_client.pool.putconn(conn)
                            self.logger.error(f"usd_m_margin_call_callback|{traceback.format_exc()}")
                            self.acw_api.create_message_thread(self.admin_id, "usd_m_margin_call_callback", str(e), 'ERROR')
                            continue
                        
                        # Fetch trade history from database
                        try:
                            conn = self.postgres_client.pool.getconn()
                            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                            curr.execute("""SELECT * FROM trade_history WHERE uuid=%s""", (last_trade_history_uuid,))
                            trade_history_df = pd.DataFrame(curr.fetchall())
                            self.postgres_client.pool.putconn(conn)
                        except Exception as e:
                            self.postgres_client.pool.putconn(conn)
                            self.logger.error(f"usd_m_margin_call_callback|{traceback.format_exc()}")
                            self.acw_api.create_message_thread(self.admin_id, "usd_m_margin_call_callback", str(e), 'ERROR')
                            continue
                        
                        trade_side = trade_history_df['trade_side'].values[0]
                        if trade_side == "EXIT":
                            body = f"거래 UUID:{trade_uuid}({base_asset})에 대한 EXIT 거래가 이미 실행되었으므로 포지션 정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리 취소", body, 'INFO')
                            continue
                        trade_base_asset = trade_history_df['base_asset'].values[0]
                        if trade_base_asset != base_asset:
                            body = f"거래기록 UUID:{last_trade_history_uuid}의 거래자산({trade_base_asset})과 청산경고자산({base_asset})이 서로 일치하지 않습니다.\n"
                            body += f"포지션 자동정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리 취소", body, 'INFO')
                            continue
                        target_order_id = trade_history_df['target_order_id'].values[0]
                        origin_order_id = trade_history_df['origin_order_id'].values[0]
                        
                        # Fetch order history from database
                        try:
                            conn = self.postgres_client.pool.getconn()
                            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                            curr.execute("""SELECT * FROM order_history WHERE order_id=%s""", (target_order_id,))
                            target_order_history_df = pd.DataFrame(curr.fetchall())
                            curr.execute("""SELECT * FROM order_history WHERE order_id=%s""", (origin_order_id,))
                            origin_order_history_df = pd.DataFrame(curr.fetchall())
                            self.postgres_client.pool.putconn(conn)
                        except Exception as e:
                            self.postgres_client.pool.putconn(conn)
                            self.logger.error(f"usd_m_margin_call_callback|{traceback.format_exc()}")
                            self.acw_api.create_message_thread(self.admin_id, "usd_m_margin_call_callback", str(e), 'ERROR')
                            continue
                        
                        target_order_executed_qty = target_order_history_df['qty'].values[0]
                        origin_order_executed_qty = origin_order_history_df['qty'].values[0]
                        
                        margin_liquidation_call_trade_dict = {
                            "trade_type": "short_long_trade",
                            "trade_df": row.to_frame().T,
                            "order_type": "margin_call"
                        }
                        
                        self.margin_liquidation_call_trade_queue.put(margin_liquidation_call_trade_dict)
            else:
                return
        except Exception as e:
            self.logger.error(f"usd_m_margin_call_callback|{traceback.format_exc()}")
            title = "usd_m_margin_call_callback 에서 에러 발생!"
            body = f"{title}\n"
            body += f"trade_uuid: {trade_uuid}, trade_config_uuid: {trade_config_uuid}, margin_call_mode: {margin_call_mode}({type(margin_call_mode)}), error: {e}"
            full_content = f"{title}\n{body}"
            self.acw_api.create_message_thread(self.admin_id, title, full_content, send_times=1, send_term=1)
            return
        
    def usd_m_liquidation_callback(self, res, trade_config_uuid, margin_call_mode, telegram_id):
        try:
            # margin_call_mode == None -> Do nothing,
            # margin_call_mode == 1 -> Only warning message, 
            # margin_call_mode == 2 -> message & auto exit
            if margin_call_mode == None:
                return
            elif margin_call_mode == 1 or margin_call_mode == 2:
                symbol = res['o']['s'] # EX: BTCUSDT
                symbol = symbol.replace('USDT', '')
                side = res['o']['S'] # BUY or SELL
                qty = res['o']['q']
                # Send Liquidation message
                body = f"청산 알람! 바이낸스 {symbol}USDT {qty}개가 강제청산되었습니다.\n"
                self.acw_api.create_message_thread(telegram_id, "청산 알람", body, 'WARNING',  send_times=5, send_term=5)
                # If margin_call_mode == 2, execute auto exit
                if margin_call_mode == 2:
                    body = f"마진콜 모니터링 설정에 따라, 자동거래에 진입되어 있는 {self.counterpart_exchange}의 포지션을 자동정리합니다."
                    self.acw_api.create_message_thread(telegram_id, "청산 자동정리", body, 'INFO')
                    trade_df = get_trade_df(self.market_code_combination, trade_support=True)
                    waiting_df = trade_df[(trade_df['trade_config_uuid']==trade_config_uuid)&(trade_df['base_asset']==symbol)&(trade_df['trade_switch']==-1)]
                    self.logger.info(f"청산자동정리 실행|trade_config_uuid: {trade_config_uuid}, symbol: {symbol}, symbol: {symbol}") # test
                    if len(waiting_df) == 0:
                        body = f"{symbol}USDT는 차익거래에 진입되어있는 상태가 아닙니다.\n"
                        body += f"포지션 자동정리를 취소합니다."
                        self.acw_api.create_message_thread(telegram_id, "청산 자동정리 취소", body, 'INFO')
                        return
                    
                    for row_tup in waiting_df.iterrows():
                        row = row_tup[1]
                        trade_uuid = row['uuid']
                        base_asset = row['base_asset']
                        last_trade_history_uuid = row['last_trade_history_uuid']
                        # Order record validation
                        if last_trade_history_uuid is None:
                            body = f"거래 UUID:{trade_uuid}({base_asset})에 대한 거래 체결기록이 조회되지 않습니다.\n"
                            body += f"포지션 자동정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "청산 자동정리 취소", body, 'INFO')
                            continue
                        # UPDATE database
                        try:
                            conn = self.postgres_client.pool.getconn()
                            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                            curr.execute("""UPDATE trade SET last_updated_datetime=%s, trade_switch=%s WHERE uuid=%s""", (datetime.datetime.utcnow(), 2, trade_uuid))
                            conn.commit()
                            self.postgres_client.pool.putconn(conn)
                        except Exception as e:
                            self.postgres_client.pool.putconn(conn)
                            self.logger.error(f"usd_m_liquidation_callback|{traceback.format_exc()}")
                            self.acw_api.create_message_thread(self.admin_id, "usd_m_liquidation_callback", str(e), 'ERROR')
                            continue
                        # Fetch trade history from database
                        try:
                            conn = self.postgres_client.pool.getconn()
                            curr = conn.cursor(cursor_factory=extras.RealDictCursor)
                            curr.execute("""SELECT * FROM trade_history WHERE uuid=%s""", (last_trade_history_uuid,))
                            trade_history_df = pd.DataFrame(curr.fetchall())
                            self.postgres_client.pool.putconn(conn)
                        except Exception as e:
                            self.postgres_client.pool.putconn(conn)
                            self.logger.error(f"usd_m_liquidation_callback|{traceback.format_exc()}")
                            self.acw_api.create_message_thread(self.admin_id, "usd_m_liquidation_callback", str(e), 'ERROR')
                            continue
                        trade_side = trade_history_df['trade_side'].values[0]
                        if trade_side == "EXIT":
                            body = f"거래 UUID:{trade_uuid}({base_asset})에 대한 EXIT 거래가 이미 실행되었으므로 포지션 정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "청산 자동정리 취소", body, 'INFO')
                            continue
                        trade_base_asset = trade_history_df['base_asset'].values[0]
                        if trade_base_asset != base_asset:
                            body = f"거래기록 UUID:{last_trade_history_uuid}의 거래자산({trade_base_asset})과 청산경고자산({base_asset})이 서로 일치하지 않습니다.\n"
                            body += f"포지션 자동정리를 취소합니다."
                            self.acw_api.create_message_thread(telegram_id, "청산 자동정리 취소", body, 'INFO')
                            continue
                        target_order_id = trade_history_df['target_order_id'].values[0]
                        origin_order_id = trade_history_df['origin_order_id'].values[0]
                        
                        margin_liquidation_call_trade_dict = {
                            "trade_type": "short_long_trade",
                            "trade_df": row.to_frame().T,
                            "order_type": "liquidation"
                        }
                        
                        self.margin_liquidation_call_trade_queue.put(margin_liquidation_call_trade_dict)
            else:
                return
        except Exception as e:
            self.logger.error(f"usd_m_liquidation_callback|{traceback.format_exc()}")
            title = "usd_m_liquidation_callback 에서 에러 발생!"
            body = f"{title}\n"
            body += f"trade_config_uuid: {trade_config_uuid}, margin_call_mode: {margin_call_mode}({type(margin_call_mode)}), error: {e}"
            full_content = f"{title}\n{body}"
            self.acw_api.create_message_thread(self.admin_id, title, full_content, send_times=1, send_term=1)
            return

    async def user_usd_m_socket(self, access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id):
        client = await AsyncClient.create(access_key, secret_key)
        bm = BinanceSocketManager(client)
        # start any sockets here, i.e a trade socket
        ts = bm.futures_socket()
        # then start receiving messages
        async with ts as tscm:
            while True:
                try:
                    res = await tscm.recv()
                    self.logger.info(f"user_usd_m_socket stream|trade_config_uuid:{trade_config_uuid}\nres: {res}\n") # test
                    if res['e'] == "MARGIN_CALL":
                        self.usd_m_margin_call_callback(res, trade_config_uuid, margin_call_mode, telegram_id)
                    if res['e'] == "ACCOUNT_UPDATE":
                        # self.reflect_binance_account_update(user_id, res)
                        pass
                    if res['e'] == "ORDER_TRADE_UPDATE" and res['o']['o'] == 'LIQUIDATION':
                        self.usd_m_liquidation_callback(res, trade_config_uuid, margin_call_mode, telegram_id)
                except Exception as e:
                    title = "user_usd_m_socket 에서 에러 발생!"
                    body = f"{title}]n"
                    body += f"error: {e}"
                    msg_full = f"{title}\n{body}"
                    self.acw_api.create_message_thread(self.admin_id, title, msg_full, 'ERROR', send_times=1, send_term=1)
                time.sleep(0.3)

    def user_usd_m_socket_async(self, access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id):
        asyncio.run(self.user_usd_m_socket(access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id))

    def start_user_socket_stream(self, market_type, loop_secs=3, monitor_loop_secs=2.5):
        # A user should have at least one trade_df setting to start user socket stream.
        self.logger.info(f"start_socket_stream|start_socket_stream started.")
        def monitor_user_stream_loop():
            input_type = 'monitor'
            title = 'monitor_user_stream stopped! restarting monitor_user_stream thread..'
            def monitor_user_stream():
                try:
                    while True:
                        time.sleep(loop_secs)
                        # Add monitoring thread if there isn't one
                        trade_df = get_trade_df(self.market_code_combination, trade_support=True)
                        if trade_df is None or len(trade_df) == 0:
                            continue
                        # Make a copy to avoid SettingWithCopyWarning
                        unique_trade_df = trade_df.drop_duplicates(subset=['trade_config_uuid']).copy()

                        # Temporary DataFrame
                        unique_trade_df['api_keys'] = unique_trade_df['trade_config_uuid'].apply(
                            lambda x: self.get_api_key_tup(
                                x,
                                futures=(False if market_type.upper() == 'SPOT' else True),
                                raise_error=False
                            )
                        )

                        unique_trade_df[['access_key', 'secret_key']] = pd.DataFrame(
                            unique_trade_df['api_keys'].tolist(),
                            index=unique_trade_df.index
                        )
                        # delete temporary df
                        unique_trade_df.drop(columns=['api_keys'], inplace=True)
                        # Drop if there's no api key
                        unique_trade_df = unique_trade_df.dropna(subset=['access_key', 'secret_key'])

                        for row_tup in unique_trade_df.iterrows():
                            row = row_tup[1]
                            if 'BINANCE' in self.market_code_combination.split(':')[0]:
                                margin_call_mode = row['target_market_margin_call']
                            else:
                                margin_call_mode = row['origin_market_margin_call']
                            if self.user_stream_monitoring_list == []:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_socket_async, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id']), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"trade_config_uuid: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            elif row['trade_config_uuid'] not in [x[0] for x in self.user_stream_monitoring_list]:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_socket_async, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id']), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"user_id: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            time.sleep(0.25)
                        # Remove dead thread or unauthorized thread from the list
                        for i,each_tup in enumerate(self.user_stream_monitoring_list):
                            trade_config_uuid = self.user_stream_monitoring_list[i][0]
                            status_flag = True
                            if each_tup[1].is_alive() is False:
                                status_flag = False
                                self.logger.error(f"trade_config_uuid: {trade_config_uuid}'s user_stream monitoring thread has died!")
                                title = f"trade_config_uuid: {trade_config_uuid}'s binance user_stream monitoring thread has died!"
                                self.acw_api.create_message_thread(self.admin_id, title, title, send_times=1, send_term=1)
                            if trade_config_uuid not in unique_trade_df['trade_config_uuid'].values:
                                title = f"trade_config_uuid: {trade_config_uuid}'s not in the unique_trade_df! status_flag = False.."
                                self.logger.info(title)
                                status_flag = False
                            if status_flag is False:
                                title = f"trade_config_uuid: {trade_config_uuid}'s user_stream monitoring thread has been removed!"
                                self.logger.info(title)
                                self.user_stream_monitoring_list.pop(i)
                except Exception:
                    self.logger.error(f"monitor_user_stream|{traceback.format_exc()}")

            monitor_user_stream_thread = Thread(target=monitor_user_stream, daemon=True)
            monitor_user_stream_thread.start()
            while True:
                if not monitor_user_stream_thread.is_alive():
                    self.logger.error(f"monitor_user_stream|monitor_user_stream stopped! restarting monitor_user_stream thread..")
                    title = 'monitor_user_stream stopped! restarting monitor_user_stream thread..'
                    self.acw_api.create_message_thread(self.admin_id, title, title, send_times=1, send_term=1)
                    monitor_user_stream_thread = Thread(target=monitor_user_stream, daemon=True)
                    monitor_user_stream_thread.start()
                time.sleep(monitor_loop_secs)
        self.start_socket_stream_thread = Thread(target=monitor_user_stream_loop, daemon=True)
        self.start_socket_stream_thread.start()

    def calculate_enter_qty(self, base_asset, dollar, bp, LS_premium, SL_premium, trade_capital, market_type, capital_currency='KRW'):
        if capital_currency not in ["KRW"]:
            raise Exception(f"Invalid currency: {capital_currency}")
        if market_type not in ["USD_M"]:
            raise Exception(f"Invalid market_type: {market_type}")
        usdt_converted_dollar = (100+(LS_premium+SL_premium)/2)/100 * dollar
        value_usd = trade_capital/(usdt_converted_dollar*1.005) # 0.5% margin for the enter amount of KRW
        
        bp_usd = bp / usdt_converted_dollar

        # BTC, ETH, BCH, LTC -> 0.001 까지 가능
        if base_asset in ['BTC','ETH','BCH','LTC']:
            enter_quantity = round(value_usd / bp_usd, 3)
            if enter_quantity*bp_usd > value_usd:
                enter_quantity = round((enter_quantity - 0.001), 3)

        # ETC, NEO, LINK -> 0.01 까지 가능
        elif base_asset in ['ETC','NEO', 'LINK']:
            enter_quantity = round(value_usd / bp_usd, 2)
            if enter_quantity*bp_usd > value_usd:
                enter_quantity = round((enter_quantity - 0.01), 2)
        else:
            enter_quantity = value_usd // bp_usd
                        
        return enter_quantity