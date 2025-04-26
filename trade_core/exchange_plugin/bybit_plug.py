import os
import sys
import datetime
import pandas as pd
pd.set_option('future.no_silent_downcasting', True)
import time
import traceback
import requests
import _pickle as pickle
from pybit.unified_trading import HTTP, WebSocket
import json
from psycopg2 import extras
from threading import Thread
from queue import Queue
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import TradeCoreLogger
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from etc.redis_connector.redis_helper import RedisHelper
from etc.utils import get_trade_df
from api.utils import decrypt_data, MyException

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
        self.bybit_plug_logger = TradeCoreLogger("bybit_plug", logging_dir).logger
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
        funding_df = ticker_df.loc[:, ['symbol','base_asset','quote_asset','fundingRate','nextFundingTime']]
        funding_df['perpetual'] = funding_df.loc[:, 'fundingRate'].apply(lambda x: True if x != '' else False)
        funding_df.loc[:, ['fundingRate','nextFundingTime']] = funding_df.loc[:, ['fundingRate','nextFundingTime']].apply(pd.to_numeric, errors='coerce')
        funding_df.loc[:, 'nextFundingTime'] = funding_df.loc[:, 'nextFundingTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
        # Convert 'nextFundingTime' to datetime
        funding_df.loc[:, 'nextFundingTime'] = pd.to_datetime(funding_df['nextFundingTime']).dt.tz_localize(None)
        funding_df = funding_df.rename(columns={'fundingRate':"funding_rate", "nextFundingTime":"funding_time"})
        return funding_df
    
class UserBybitAdaptor:
    def __init__(self, admin_id, acw_api, postgres_db_dict=None, market_code_combination=None, margin_liquidation_call_trade_queue=None, logging_dir=None):
        self.admin_id = admin_id
        self.local_redis_client = RedisHelper(host='localhost', port=6379, db=0, passwd=None)
        self.user_client_dict = {}
        self.user_stream_monitoring_list = []
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
            self.market_code = [x for x in market_code_combination.split(':') if 'BYBIT' in x][0]
            self.market, self.quote_asset = self.market_code.split('/')
            self.exchange = self.market.split('_')[0]
            self.market_type = self.market.replace(self.exchange+'_','')
            self.counterpart_market_code = [x for x in market_code_combination.split(':') if 'BYBIT' not in x][0]
            self.counterpart_market, self.counterpart_quote_asset = self.counterpart_market_code.split('/')
            self.counterpart_exchange = self.counterpart_market.split('_')[0]
            self.counterpart_market_type = self.counterpart_market.replace(self.counterpart_exchange+'_','')
            # Check whether the market_type is supported
            if self.market_type not in ["USD_M"]:
                raise Exception(f"Invalid market_type: {self.market_type}")
            logger_name = self.market_code.replace('/', '__')
            self.logger = TradeCoreLogger(f"user_bybit_plug_{logger_name}", logging_dir).logger
            self.logger.info(f"user_bybit_plug_{self.market_code} started.")
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
            self.logger = TradeCoreLogger(f"user_bybit_plug", logging_dir).logger
            self.logger.info(f"user_bybit_plug started.")
        
    def load_user_api_keys(self, table_name='exchange_api_key'):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        sql = f"SELECT * FROM {table_name} WHERE exchange='BYBIT'"
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
            return (api_key_df['uuid'].values[0], api_key_df['access_key'].values[0], api_key_df['secret_key'].values[0])
        except ValueError:
            if raise_error:
                raise MyException(f"No API Key found for trade_config_uuid: {trade_config_uuid}, futures: {futures}", error_code=1)
            else:
                return (None, None, None)
            
    def delete_user_api_key(self, uuid, table_name='exchange_api_key'):
        """
        Deletes a user's API key from the specified table using the unique uuid.

        Parameters
        ----------
        uuid : str
            The UUID of the API key entry that should be deleted.
        table_name : str, optional
            The name of the table storing user API keys (default is 'exchange_api_key').

        Returns
        -------
        bool
            True if the deletion was successful (at least one row affected), False otherwise.
        """
        # Obtain a connection from the pool
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor()

        try:
            # Execute the DELETE statement
            sql = f"DELETE FROM {table_name} WHERE uuid = %s"
            curr.execute(sql, (uuid,))
            rows_deleted = curr.rowcount
            conn.commit()

            # Return True if at least one row was deleted, otherwise False
            return rows_deleted > 0

        except Exception as e:
            # In case of any error, rollback changes
            conn.rollback()
            raise e

        finally:
            # Return the connection to the pool
            self.postgres_client.pool.putconn(conn)

    def load_user_client(self, access_key, secret_key):
        user_client = self.user_client_dict.get(access_key)
        if user_client is None:
            self.user_client_dict[access_key] = HTTP(testnet=False, api_key=access_key, api_secret=secret_key)
            return self.user_client_dict[access_key]
        else:
            return user_client
    
    def check_api_key(self, access_key, secret_key, futures=False):
        self.user_client_dict.pop(access_key, None)
        try:
            # Check API key by getting wallet balance
            client = self.load_user_client(access_key, secret_key)
            client.get_wallet_balance(accountType="UNIFIED")
            return (True, 'OK')
        except Exception as e:
            self.user_client_dict.pop(access_key, None)
            return (False, str(e))
        
    def get_spot_balance(self, access_key, secret_key):
        client = self.load_user_client(access_key, secret_key)
        balance_info = client.get_wallet_balance(accountType="UNIFIED")
        asset_list = balance_info['result']['list'][0]['coin']
    
        if not asset_list:
            return pd.DataFrame(columns=['asset', 'free', 'locked'])
            
        all_balances = []
        for asset in asset_list:
            all_balances.append({
                'asset': asset['coin'], 
                'free': (float(asset.get('walletBalance', 0)) 
                        - float(asset.get('totalPositionIM', 0)) 
                        - float(asset.get('totalOrderIM', 0))
                        - float(asset.get('locked', 0))), 
                'locked': (float(asset['locked'])
                            + float(asset.get('totalPositionIM', 0))
                            + float(asset.get('totalOrderIM', 0))),
            })
                    
        balance_df = pd.DataFrame(all_balances)
        return balance_df

    def get_usdm_balance(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        balance_info = client.get_wallet_balance(accountType="UNIFIED")
        asset_list = balance_info['result']['list'][0]['coin']

        if not asset_list:
            return pd.DataFrame(columns=['asset', 'free', 'locked', 'before_pnl', 'pnl', 'after_pnl'])
            
        all_balances = []
        for asset in asset_list:
            all_balances.append({
                'asset': asset['coin'], 
                'free': (float(asset.get('walletBalance', 0)) 
                        - float(asset.get('totalPositionIM', 0)) 
                        - float(asset.get('totalOrderIM', 0))
                        - float(asset.get('locked', 0))), 
                'locked': (float(asset['locked'])
                            + float(asset.get('totalPositionIM', 0))
                            + float(asset.get('totalOrderIM', 0))),
                'before_pnl': float(asset.get('walletBalance', 0)),
                'pnl': float(asset.get('unrealisedPnl', 0)),
                'after_pnl': float(asset.get('walletBalance', 0)) + float(asset.get('unrealisedPnl', 0)),
            })
                    
        balance_df = pd.DataFrame(all_balances)
        if return_dict is None:
            return balance_df
        else:
            return_dict['res'] = balance_df
    
    def get_balance(self, access_key, secret_key, market_type='SPOT'):
        if market_type == "SPOT":
            return self.get_spot_balance(access_key, secret_key)
        elif market_type == "USD_M":
            return self.get_usdm_balance(access_key, secret_key)
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
    
    def change_margin_type(self, access_key, secret_key, market_type, margin_type='ISOLATED'):
        client = self.load_user_client(access_key, secret_key)
        if market_type == "USD_M":
            # Bybit uses REGULAR_MARGIN for cross margin and ISOLATED_MARGIN for isolated margin
            res = client.set_margin_mode(
                setMarginMode="ISOLATED_MARGIN" if margin_type == 'ISOLATED' else "REGULAR_MARGIN",
            )
            if res['retCode'] != 0:
                raise Exception(f"market_type: {market_type}, margin_type: {margin_type}, error: {res}")
            # if it's successful retCode: 0, retMsg: "Request accepted"
        else:
            raise Exception(f"market_type: {market_type} is not supported yet.")
    
    def change_leverage(self, access_key, secret_key, market_type, symbol, leverage):
        client = self.load_user_client(access_key, secret_key)
        if market_type == "USD_M":
            try:
                res = client.set_leverage(
                    category="linear",
                    symbol=symbol,
                    buyLeverage=str(leverage),
                    sellLeverage=str(leverage)
                )
            except Exception as e:
                if e.status_code == 110043:
                    # 110043: "leverage not modified" which means the leverage is already set
                    return
                else:
                    raise e
            # if it's successful retCode: 0, retMsg: "OK"
        else:
            raise Exception(f"market_type: {market_type} is not supported yet.")
        return res

    def handle_order_info_queue_loop(self):
        self.logger.info(f"handle_order_info_queue_loop started.")
        while True:
            try:
                order_info_dict = self.order_info_dict_queue.get()
                key_uuid, access_key, secret_key = self.get_api_key_tup(order_info_dict['trade_config_uuid'], (False if order_info_dict['market_type'] == "SPOT" else True))
                # API call
                fetched_order_info_res = self.fetch_order_info(access_key, secret_key, order_info_dict['symbol'], order_info_dict['order_id'], order_info_dict['market_type'])
                # process res and save data to db
                self.save_order_info_to_db(order_info_dict['trade_config_uuid'], order_info_dict['trade_uuid'], fetched_order_info_res, order_info_dict['market_type'])
            except Exception as e:
                self.logger.error(f"handle_order_info_queue_loop|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, "handle_order_info_queue_loop", str(e))
                time.sleep(3)
            time.sleep(0.05)
            
    def fetch_order_info(self, access_key, secret_key, symbol, order_id, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0
        try:
            while retry_count <= self.order_info_retry_limit:
                try:
                    if market_type == "USD_M":
                        res = client.get_order_history(
                            category="linear",
                            orderId=order_id
                        )
                        print(res)
                        if res['retCode'] == 0 and res['result']['list']:
                            order_info = res['result']['list'][0]
                            print(order_info)
                            print(return_dict)
                            if return_dict is not None:
                                return_dict['res'] = order_info
                                return_dict['error_code'] = None
                            return order_info
                        else:
                            time.sleep(self.order_info_retry_term_sec)
                            retry_count += 1
                    else:
                        raise Exception(f"market_type: {market_type} is not supported yet.")
                except Exception as e:
                    time.sleep(self.order_info_retry_term_sec)
                    retry_count += 1
                    if retry_count == self.order_info_retry_limit:
                        raise e
            raise Exception(f"Failed to fetch order info after multiple retries, traceback:{traceback.format_exc()}")
        except Exception as e:
            self.logger.error(f"fetch_order_info|order_id:{order_id}\nerror:{e}\n{traceback.format_exc()}")
            if return_dict is None:
                raise e
            else:
                return_dict['res'] = e
                return_dict['error_code'] = getattr(e, 'code', None)
    
    def save_order_info_to_db(self, trade_config_uuid, trade_uuid, res, market_type):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            if market_type == "USD_M":
                order_id = str(res['orderId'])
                executed_price = float(res['avgPrice'])
                executed_qty = float(res['qty'])
                side = res['side'].upper()
                order_type = res['orderType'].upper()
                symbol = res['symbol']
                fee = float(res.get('cumExecFee', 0))  # Bybit provides fee directly
                
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
    
    def market_long(self, access_key, secret_key, symbol, qty, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        
        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            if retry_count >= 1:
                self.logger.info(f"market_long|retry_count: {retry_count}, retry_term_sec: {self.trade_retry_term_sec}, retry_count_limit: {self.trade_retry_limit}")
            try:
                if market_type == "USD_M":
                    res = client.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Buy",
                        orderType="Market",
                        qty=str(qty),
                    )
                    
                    if res['retCode'] == 0:  # Success
                        if return_dict is not None:
                            return_dict['res'] = res['result']
                            return_dict['error_code'] = None
                        return res['result']
                    else:
                        raise Exception(f"Error code: {res['retCode']}, message: {res['retMsg']}")
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if retry_count >= self.trade_retry_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = getattr(e, 'code', -1)
                        # return
                        print(e)
                time.sleep(self.trade_retry_term_sec)
                retry_count += 1
    
    def market_short(self, access_key, secret_key, symbol, qty, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        
        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            if retry_count >= 1:
                self.logger.info(f"market_long|retry_count: {retry_count}, retry_term_sec: {self.trade_retry_term_sec}, retry_count_limit: {self.trade_retry_limit}")
            try:
                if market_type == "USD_M":
                    res = client.place_order(
                        category="linear",
                        symbol=symbol,
                        side="Sell",
                        orderType="Market",
                        qty=str(qty),
                    )
                    
                    if res['retCode'] == 0:  # Success
                        if return_dict is not None:
                            return_dict['res'] = res['result']
                            return_dict['error_code'] = None
                        return res['result']
                    else:
                        raise Exception(f"Error code: {res['retCode']}, message: {res['retMsg']}")
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if retry_count >= self.trade_retry_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = getattr(e, 'code', -1)
                        # return
                        print(e)
                time.sleep(self.trade_retry_term_sec)
                retry_count += 1
                
    def all_position_information(self, access_key, secret_key, market_type='USD_M', return_dict=None):
        client = self.load_user_client(access_key, secret_key)                
        if market_type == "USD_M":
            res = client.get_positions(
                category="linear",
                settleCoin="USDT"
            )
            
            if res['retCode'] == 0:
                positions = res['result']['list']
                
                if not positions:
                    empty_df = pd.DataFrame()
                    if return_dict is None:
                        return empty_df
                    else:
                        return_dict['res'] = empty_df
                        return_dict['error_code'] = None
                    return empty_df
                
                position_data = []
                for pos in positions:
                    if float(pos['size']) != 0:  # Only include active positions
                        position_data.append({
                            'symbol': pos['symbol'],
                            'size': float(pos['size']),
                            'avgPrice': float(pos['avgPrice']),
                            'markPrice': float(pos['markPrice']),
                            'unrealisedPnl': float(pos['unrealisedPnl']),
                            'liqPrice': float(pos['liqPrice']) if pos['liqPrice'] != "0" else None,
                            'leverage': float(pos['leverage']),
                            'marginType': None, # It's not used in UTA2.0
                            'positionIM': float(pos['positionIM']),
                            'positionMM': float(pos['positionMM']),
                            'side': 'LONG' if pos['side'] == 'Buy' else 'SHORT'
                        })
                
                position_df = pd.DataFrame(position_data)
                
                if return_dict is None:
                    return position_df
                else:
                    return_dict['res'] = position_df
                    return_dict['error_code'] = None
                return position_df
            else:
                raise Exception(f"Error code: {res['retCode']}, message: {res['retMsg']}")

        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
                
    def calculate_enter_qty(self, base_asset, dollar, bp, LS_premium, SL_premium, trade_capital, market_type, capital_currency='KRW'):
        if capital_currency not in ["KRW"]:
            raise Exception(f"Invalid currency: {capital_currency}")
        if market_type not in ["USD_M"]:
            raise Exception(f"Invalid market_type: {market_type}")
        usdt_converted_dollar = (100+(LS_premium+SL_premium)/2)/100 * dollar
        value_usd = trade_capital/(usdt_converted_dollar*1.005) # 0.5% margin for the enter amount of KRW
        
        bp_usd = bp / usdt_converted_dollar

        # BTC, ETH, BCH, LTC -> 0.001 precision
        if base_asset in ['BTC','ETH','BCH','LTC']:
            enter_quantity = round(value_usd / bp_usd, 3)
            if enter_quantity*bp_usd > value_usd:
                enter_quantity = round((enter_quantity - 0.001), 3)

        # ETC, NEO, LINK -> 0.01 precision
        elif base_asset in ['ETC','NEO', 'LINK']:
            enter_quantity = round(value_usd / bp_usd, 2)
            if enter_quantity*bp_usd > value_usd:
                enter_quantity = round((enter_quantity - 0.01), 2)
        else:
            enter_quantity = value_usd // bp_usd
                        
        return enter_quantity 

    def start_user_socket_stream(self, market_type, loop_secs=3, monitor_loop_secs=2.5):
        # A user should have at least one trade_df setting to start user socket stream.
        self.logger.info(f"start_socket_stream|start_socket_stream started.")
        # Add a dictionary to track API key error counts
        self.api_key_error_counts = {}
        
        def monitor_user_stream_loop():
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

                        unique_trade_df[['key_uuid', 'access_key', 'secret_key']] = pd.DataFrame(
                            unique_trade_df['api_keys'].tolist(),
                            index=unique_trade_df.index
                        )
                        # delete temporary df
                        unique_trade_df.drop(columns=['api_keys'], inplace=True)
                        # Drop if there's no api key
                        unique_trade_df = unique_trade_df.dropna(subset=['access_key', 'secret_key'])

                        for row_tup in unique_trade_df.iterrows():
                            row = row_tup[1]
                            # First check if the user has a valid api key
                            _, error_str = self.check_api_key(row['access_key'], row['secret_key'], futures=True)
                            
                            if 'error' in error_str.lower():
                                # Track consecutive errors for this access key
                                access_key = row['access_key']
                                if access_key not in self.api_key_error_counts:
                                    self.api_key_error_counts[access_key] = 0
                                
                                self.api_key_error_counts[access_key] += 1
                                error_count = self.api_key_error_counts[access_key]
                                
                                access_key_hidden = access_key[:5] + '****' + access_key[-5:]
                                self.logger.warning(f"API key validation error for {access_key_hidden}. Error count: {error_count}/10")
                                
                                # Only delete the API key if error count reaches 10
                                if error_count >= 10:
                                    title = f"API key invalid"
                                    body = f"access_key: {access_key_hidden} 가 유효하지 않아 API키가 자동 삭제됩니다. IP 및 권한설정이 제대로 되었는지 확인하시고 다시 등록하십시오."
                                    self.acw_api.create_message_thread(row['telegram_id'], title, body, 'ERROR', send_times=1, send_term=1)
                                    # Delete the user's api key from the database
                                    self.delete_user_api_key(row['key_uuid'])
                                    # Reset error count after deletion
                                    self.api_key_error_counts[access_key] = 0
                                    self.logger.info(f"API key {access_key_hidden} deleted after 10 consecutive errors")
                            else:
                                # Reset error count if the API key is valid
                                if row['access_key'] in self.api_key_error_counts:
                                    self.api_key_error_counts[row['access_key']] = 0
                            
                            if 'BYBIT' in self.market_code_combination.split(':')[0]:
                                margin_call_mode = row['target_market_margin_call']
                            else:
                                margin_call_mode = row['origin_market_margin_call']
                            if self.user_stream_monitoring_list == []:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_websocket, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id']), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"trade_config_uuid: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            elif row['trade_config_uuid'] not in [x[0] for x in self.user_stream_monitoring_list]:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_websocket, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id']), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"trade_config_uuid: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            time.sleep(0.25)
                        # Remove dead thread or unauthorized thread from the list
                        for i,each_tup in enumerate(self.user_stream_monitoring_list):
                            trade_config_uuid = self.user_stream_monitoring_list[i][0]
                            status_flag = True
                            if each_tup[1].is_alive() is False:
                                status_flag = False
                                self.logger.error(f"trade_config_uuid: {trade_config_uuid}'s user_stream monitoring thread has died!")
                                title = f"trade_config_uuid: {trade_config_uuid}'s bybit user_stream monitoring thread has died!"
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
    
    def handle_message(self, message, trade_config_uuid, margin_call_mode, telegram_id):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            self.logger.info(f"user_usd_m_socket stream|trade_config_uuid:{trade_config_uuid}\nres: {data}\n") # test
            
            # Handle different message types
            if 'topic' in data:
                if data['topic'] == 'execution':
                    # Process execution updates (for margin call detection)
                    if 'data' in data and data['data']:
                        for execution in data['data']:
                            # Check for Liquidation
                            if execution['execType'] == 'BustTrade':
                                self.usd_m_liquidation_callback(execution, trade_config_uuid, margin_call_mode, telegram_id)
        
        except Exception as e:
            self.logger.error(f"WebSocket handle_message error: {str(e)}\n{traceback.format_exc()}")
    
    def user_usd_m_websocket(self, access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id):
        """Create and maintain a WebSocket connection to Bybit for monitoring positions"""
        self.logger.info(f"Starting WebSocket for trade_config_uuid: {trade_config_uuid}")
        
        # Create a callback function that includes the required parameters
        def callback_with_params(message):
            self.handle_message(message, trade_config_uuid, margin_call_mode, telegram_id)
        
        ws = WebSocket(
            testnet=False,
            channel_type='private',
            api_key=access_key,
            api_secret=secret_key
        )
        ws.position_stream(callback=callback_with_params)
        while True:
            time.sleep(1)
    
    def usd_m_liquidation_callback(self, execution_data, trade_config_uuid, margin_call_mode, telegram_id):
        """Handle liquidation events from execution updates"""
        try:
            # margin_call_mode == None -> Do nothing,
            # margin_call_mode == 1 -> Only warning message, 
            # margin_call_mode == 2 -> message & auto exit
            if margin_call_mode == None:
                return
            elif margin_call_mode == 1 or margin_call_mode == 2:
                symbol = execution_data['symbol']
                base_asset = symbol.replace('USDT', '')
                side = execution_data['side']  # Buy or Sell
                open_position_side = 'LONG' if side == 'Sell' else 'SHORT'
                qty = execution_data['execQty']
                exec_price = execution_data['execPrice']
                exec_fee = execution_data['execFee']
                
                # Send Liquidation message
                body = f"청산 알람! 바이비트 {base_asset}USDT {open_position_side} {qty}개가 {exec_price}에 강제청산되었습니다.\n"
                self.acw_api.create_message_thread(telegram_id, "청산 알람", body, 'WARNING', send_times=5, send_term=5)
                
                # If margin_call_mode == 2, execute auto exit
                if margin_call_mode == 2:
                    body = f"청산 모니터링 설정에 따라, 자동거래에 진입되어 있는 {self.counterpart_exchange}의 포지션을 자동정리합니다."
                    self.acw_api.create_message_thread(telegram_id, "청산 자동정리", body, 'INFO')
                    
                    trade_df = get_trade_df(self.market_code_combination, trade_support=True)
                    waiting_df = trade_df[(trade_df['trade_config_uuid']==trade_config_uuid)&(trade_df['base_asset']==base_asset)&(trade_df['trade_switch']==-1)]
                    self.logger.info(f"청산자동정리 실행|trade_config_uuid: {trade_config_uuid}, symbol: {base_asset}")
                    
                    if len(waiting_df) == 0:
                        body = f"{base_asset}USDT는 차익거래에 진입되어있는 상태가 아닙니다.\n"
                        body += f"포지션 자동정리를 취소합니다."
                        self.acw_api.create_message_thread(telegram_id, "청산 자동정리 취소", body, 'INFO')
                        return
                    
                    for row_tup in waiting_df.iterrows():
                        row = row_tup[1]
                        trade_uuid = row['uuid']
                        
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
                        
                        # Process the trade for liquidation handling
                        margin_liquidation_call_trade_dict = {
                            "open_position_side": open_position_side,
                            "market_code": self.market_code,
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