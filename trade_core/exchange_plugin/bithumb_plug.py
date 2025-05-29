import os
import sys
import datetime
import pandas as pd
import time
import traceback
import requests
import uuid
import hashlib
import jwt   # pip install pyjwt
from urllib.parse import urlencode
import json
from threading import Thread
from multiprocessing import Queue
from psycopg2 import extras

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import TradeCoreLogger
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from api.utils import decrypt_data, MyException


def calculate_bithumb_price(price):
    if price >= 1000000:  # 1,000,000원 이상
        price = int(price/1000)*1000
    elif price >= 500000:  # 500,000원 이상 1,000,000원 미만
        price = int(price/500)*500
    elif price >= 100000:  # 100,000원 이상 500,000원 미만
        price = int(price/100)*100
    elif price >= 50000:  # 50,000원 이상 100,000원 미만
        price = int(price/50)*50
    elif price >= 10000:  # 10,000원 이상 50,000원 미만
        price = int(price/10)*10
    elif price >= 5000:  # 5,000원 이상 10,000원 미만
        price = int(price/5)*5
    elif price >= 100:  # 100원 이상 5,000원 미만
        price = int(price)  # 1원 단위
    elif price >= 10:  # 10원 이상 100원 미만
        price = int(price*100)/100  # 0.01원 단위
    elif price >= 1:  # 1원 이상 10원 미만
        price = int(price*1000)/1000  # 0.001원 단위
    elif price > 0:  # 1원 미만
        price = int(price*10000)/10000  # 0.0001원 단위

    return price
class Bithumb:
    def __init__(self, access_key=None, secret_key=None):
        """
        Bithumb client for both public and private endpoints.
        
        :param api_key: (str) Your Bithumb API key
        :param secret_key: (str) Your Bithumb Secret key
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.server_url = "https://api.bithumb.com/v1"
        self.headers = {"accept": "application/json"}

    ############################################################################
    # Public endpoints
    ############################################################################
    def spot_all_tickers(self, market=None):
        """
        Retrieves ticker information for all available markets, or a specific market.
        By default, fetches for ["KRW", "BTC"] markets.
        """
        
        market_url = "/market/all?isDetails=false"
        res = requests.get(self.server_url + market_url, headers=self.headers)
        res.raise_for_status()
        all_market_code_list = pd.DataFrame(res.json())['market'].to_list()
        
        # Filter for KRW markets
        krw_markets = [x for x in all_market_code_list if 'KRW-' in x]
        
        # Split into chunks of 300 to avoid 413 Entity Too Large error
        chunk_size = 300
        ticker_data_list = []
        
        for i in range(0, len(krw_markets), chunk_size):
            chunk = krw_markets[i:i + chunk_size]
            
            ticker_url = "/ticker"
            query_params = {
                "markets": ",".join(chunk)
            }
            res = requests.get(self.server_url + ticker_url, headers=self.headers, params=query_params)
            res.raise_for_status()
            
            # Collect the ticker data from this chunk
            chunk_data = res.json()
            ticker_data_list.extend(chunk_data)
        
        # Combine all ticker data into a single DataFrame
        total_ticker_df = pd.DataFrame(ticker_data_list)
        
        
        # Rename columns and clean up
        total_ticker_df = total_ticker_df.rename(
            columns={
                'market': 'symbol',
                'acc_trade_price_24h': 'atp24h',
                'trade_price': 'lastPrice',
            }
        )
        # Convert numeric columns
        numeric_cols = ['opening_price','high_price','low_price','lastPrice',
                        'prev_closing_price','change_price','change_rate',
                        'signed_change_price','signed_change_rate','trade_volume',
                        'acc_trade_price', 'atp24h', 'acc_trade_volume',
                        'acc_trade_volume_24h', 'highest_52_week_price',
                        'lowest_52_week_price', 'timestamp']
        for col in numeric_cols:
            if col in total_ticker_df.columns:
                total_ticker_df[col] = total_ticker_df[col].astype(float)
        total_ticker_df['base_asset'] = total_ticker_df['symbol'].apply(lambda x: x.split('-')[1])
        total_ticker_df['quote_asset'] = total_ticker_df['symbol'].apply(lambda x: x.split('-')[0])
        return total_ticker_df
    
    def spot_exchange_info(self):
        """
        Wrapper to get exchange info (in this example, the same as 'spot_all_tickers').
        """
        return self.spot_all_tickers()

    ############################################################################
    # Private endpoints
    ############################################################################
    def _generate_output(self, response):
        """
        Helper function to check the response status and return the JSON data.
        """
        # Check whether the status code is either 200 or 201
        if response.status_code not in [200, 201]:
            new_response = {}
            new_response['ok'] = False
            new_response['result'] = response.json()
        else:
            new_response = {}
            new_response['ok'] = True
            new_response['result'] = response.json()
        return new_response
    
    def _generate_auth_headers(self, endpoint_path, request_body=None, method="POST"):
        """
        
        Create the JWT-based authorization header for private endpoints.
        Bithumb requires a hash of the query/body, plus a nonce/timestamp.

        :param endpoint_path: e.g. '/v1/orders'
        :param request_body: dict of your payload (for query in GET or data in POST)
        :param method: "GET" or "POST"
        :return: Dictionary with required authorization headers
        """
        if not self.access_key or not self.secret_key:
            raise ValueError("API Key and Secret Key must be provided for private endpoints.")
        
        if request_body is None:
            request_body = {}
        
        # 1) Build the query string for hashing
        if method == "GET":
            # For GET, the request body would be used as query parameters
            query_string = urlencode(request_body)
        else:
            # For POST, also in official sample, they do the same for the body
            query_string = urlencode(request_body)
        
        query_hash = hashlib.sha512(query_string.encode()).hexdigest()
        
        # 2) Build JWT payload
        payload = {
            'access_key': self.access_key,
            'nonce': str(uuid.uuid4()),
            'timestamp': int(round(time.time() * 1000)),
            'query_hash': query_hash,
            'query_hash_alg': 'SHA512'
        }
        
        # 3) Encode JWT
        jwt_token = jwt.encode(payload, self.secret_key)
        authorization_token = f'Bearer {jwt_token}'
        
        # 4) Headers
        headers = {
            'Authorization': authorization_token,
            'Content-Type': 'application/json'
        }
        
        return headers
    
    def wallet_status(self):
        endpoint_path = '/status/wallet'
        url = self.server_url + endpoint_path
        headers = self._generate_auth_headers(endpoint_path, method="GET")
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # Check the status code
        if response.status_code != 200:
            raise Exception(f"Error getting wallet status: {response.json()}")
        wallet_status_df = pd.DataFrame(response.json())
        wallet_status_df = wallet_status_df.rename(
            columns={'currency': 'asset',
                    'net_type': 'network_type'
                    }
        )
        wallet_status_df.loc[:, 'network_type'] = wallet_status_df['network_type'].apply(lambda x: x.split('_')[0])
        # Possible wallet_state
        # 1. working
        # 2. withdraw_only
        # 3. deposit_only
        # 4. paused
        wallet_status_df['deposit'] = wallet_status_df['wallet_state'].apply(lambda x: True if x in ['working', 'deposit_only'] else False)
        wallet_status_df['withdraw'] = wallet_status_df['wallet_state'].apply(lambda x: True if x in ['working', 'withdraw_only'] else False)
        return wallet_status_df

    def spot_place_order(self, market: str, side: str, volume: float, price: float, ord_type: str):
        """
        Places an order on Bithumb. 
        This method replicates the official sample for placing an order.

        :param market: e.g. 'KRW-BTC'
        :param side: 'bid' for buy, 'ask' for sell
        :param volume: amount of coin to buy/sell
        :param price: price per coin (if ord_type='limit')
        :param ord_type: 'limit', 'market' etc.
        :return: (dict) API response
        """
        endpoint_path = '/orders'
        url = self.server_url + endpoint_path

        request_body = {
            # 'market': str(market),
            'market': market,
            # 'side': str(side),
            'side': side,
            # 'ord_type': str(ord_type),
            'ord_type': ord_type,
        }
        if volume:
            # request_body['volume'] = str(volume)
            request_body['volume'] = volume
        if price:
            # request_body['price'] = str(price)
            request_body['price'] = price
        
        # Build auth headers
        headers = self._generate_auth_headers(endpoint_path, request_body=request_body, method="POST")
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(request_body))
            # response.raise_for_status()
            return self._generate_output(response)
        except Exception as err:
            # Log or re-raise the exception as needed
            raise Exception(f"Error placing order: {err}")

    def spot_cancel_order(self, order_id: str):
        """
        Cancel an order on Bithumb.
        """
        endpoint_path = f'/order'
        url = self.server_url + endpoint_path

        request_body = {
            'uuid': order_id
        }
        
        # Build auth headers
        headers = self._generate_auth_headers(endpoint_path, request_body=request_body, method="GET")
        
        try:
            response = requests.delete(url, headers=headers, params=request_body)
            # response.raise_for_status()
            return self._generate_output(response)
        except Exception as err:
            # Log or re-raise the exception as needed
            raise Exception(f"Error cancelling order: {err}")
        
    def spot_order_info(self, order_id: str):
        """
        Get information on a specific order.
        """
        endpoint_path = f'/order'
        url = self.server_url + endpoint_path

        request_body = {
            'uuid': order_id
        }
        
        # Build auth headers
        headers = self._generate_auth_headers(endpoint_path, request_body=request_body, method="GET")
        
        try:
            response = requests.get(url, headers=headers, params=request_body)
            # response.raise_for_status()
            return self._generate_output(response)
        except Exception as err:
            # Log or re-raise the exception as needed
            raise Exception(f"Error getting order info: {err}")
        
    def get_account_info(self):
        """
        Get account information.
        """
        endpoint_path = f'/accounts'
        url = self.server_url + endpoint_path

        # Build auth headers
        headers = self._generate_auth_headers(endpoint_path, method="GET")
        
        try:
            response = requests.get(url, headers=headers)
            # response.raise_for_status()
            return self._generate_output(response)
        except Exception as err:
            # Log or re-raise the exception as needed
            raise Exception(f"Error getting account info: {err}")

class InitBithumbAdaptor:
    """
    A higher-level adaptor class that could be used as a single interface.
    """
    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        # Private client (for trading, etc.)
        self.my_client = Bithumb(my_access_key, my_secret_key)
        # Public client (if you want to do public calls without credentials)
        self.pub_client = Bithumb()
        
        self.bithumb_plug_logger = TradeCoreLogger("bithumb_plug", logging_dir).logger
        self.bithumb_plug_logger.info("bithumb_plug_logger started.")

    # -------------------- Public wrappers --------------------
    def spot_all_tickers(self):
        return self.pub_client.spot_all_tickers()

    def spot_exchange_info(self):
        return self.pub_client.spot_exchange_info()
    
    # -------------------- Private wrappers -------------------
    def wallet_status(self):
        return self.my_client.wallet_status()

class UserBithumbAdaptor:
    def __init__(self, admin_id, acw_api, postgres_db_dict=None, market_code_combination=None, margin_liquidation_call_trade_queue=None, logging_dir=None):
        self.user_client_dict = {}
        self.admin_id = admin_id
        self.postgres_db_dict = postgres_db_dict
        self.market_code_combination = market_code_combination
        self.margin_liquidation_call_trade_queue = None
        self.trade_retry_term_sec = 0.2
        self.trade_retry_limit = 2
        self.order_info_retry_term_sec = 2
        self.order_info_retry_limit = 20
        self.acw_api = acw_api
        if postgres_db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
            self.user_api_key_df = self.load_user_api_keys()
        else:
            self.postgres_client = None
            self.user_api_key_df = None
        self.market_code_combination = market_code_combination
        if market_code_combination is not None:
            self.market_code = [x for x in market_code_combination.split(':') if 'BITHUMB' in x][0]
            self.market, self.quote_asset = self.market_code.split('/')
            self.exchange = self.market.split('_')[0]
            self.market_type = self.market.replace(self.exchange+'_','')
            self.counterpart_market_code = [x for x in market_code_combination.split(':') if 'BITHUMB' not in x][0]
            self.counterpart_market, self.counterpart_quote_asset = self.counterpart_market_code.split('/')
            self.counterpart_exchange = self.counterpart_market.split('_')[0]
            self.counterpart_market_type = self.counterpart_market.replace(self.counterpart_exchange+'_','')
            # Check whether the market_type is supported
            if self.market_type not in ["SPOT"]:
                raise Exception(f"Invalid market_type: {self.market_type}")
            logger_name = self.market_code.replace('/', '__')
            self.logger = TradeCoreLogger(f"user_bithumb_plug_{logger_name}", logging_dir).logger
            self.logger.info(f"user_bithumb_plug_{self.market_code} started.")
            self.load_user_api_keys_thread = Thread(target=self.loop_load_user_api_keys, args=(5,), daemon=True)
            self.load_user_api_keys_thread.start()
            # queue for handling order info
            self.order_info_dict_queue = Queue()
            # thread for handling order info
            self.handle_order_info_queue_thread = Thread(target=self.handle_order_info_queue_loop, daemon=True)
            self.handle_order_info_queue_thread.start()
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
            self.logger = TradeCoreLogger(f"user_bithumb_plug", logging_dir).logger
            self.logger.info(f"user_bithumb_plug started.")
        
    def load_user_client(self, access_key, secret_key):
        user_client = self.user_client_dict.get(access_key)
        if user_client is None:
            self.user_client_dict[access_key] = Bithumb(access_key, secret_key)
            return self.user_client_dict[access_key]
        else:
            return user_client
        
    def load_user_api_keys(self, table_name='exchange_api_key'):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        sql = f"SELECT * FROM {table_name} WHERE exchange='BITHUMB'"
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
            user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].map(lambda x: x.tobytes() if isinstance(x, memoryview) else x)
            user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].map(lambda x: decrypt_data(x).decode('utf-8') if x is not None else None)
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
        
    def get_spot_balance(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        res = client.get_account_info()
        if res['ok'] is False:
            if return_dict is not None:
                return_dict['res'] = res
                return_dict['error_code'] = res['result']['error']['name']
                return
            raise Exception(res['result']['error']['message'])
        result_df = pd.DataFrame(res['result'])
        result_df.loc[:, ['balance','locked','avg_buy_price']] = result_df[['balance','locked','avg_buy_price']].astype(float)
        result_df = result_df.rename(columns={'currency':'asset', 'balance':'free'})
        if return_dict is None:
            return result_df
        else:
            return_dict['res'] = result_df
            return_dict['error_code'] = None

    def position_information(self, access_key, secret_key, market_type, symbol, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        if market_type == 'SPOT':
            res = client.get_account_info()
            if res['ok'] is False:
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = res['result']['error']['name']
                    return
                raise Exception(res['result']['error']['message'])
            position_df = pd.DataFrame(res['result'])
            symbol_df = position_df[position_df['currency']==symbol]['balance']
            if len(symbol_df) == 0:
                remaining_qty = 0
            else:
                remaining_qty = float(symbol_df.iloc[0])
                if return_dict is not None:
                    return_dict['res'] = remaining_qty
                    return_dict['error_code'] = None
            return remaining_qty
        else:
            raise Exception(f"market_type: {market_type} is not supported yet.")

    def all_position_information(self, access_key, secret_key, market_type='SPOT', return_dict=None):
        if market_type == "SPOT":
            return self.get_spot_balance(access_key, secret_key, return_dict=return_dict)
        elif market_type == "USD_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
        
    def get_balance(self, access_key, secret_key, market_type='SPOT', return_dict=None):
        if market_type == "SPOT":
            return self.get_spot_balance(access_key, secret_key, return_dict=return_dict)
        elif market_type == "USD_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
    
    def check_api_key(self, access_key, secret_key, futures=False):
        self.user_client_dict.pop(access_key, None)
        client = self.load_user_client(access_key, secret_key)
        if futures:
            raise Exception(f"futures market is not supported yet.")
        try:
            res = client.get_account_info()
            if res['ok'] is True:
                return (True, 'OK')
            else:
                self.user_client_dict.pop(access_key, None)
                return (False, res['result']['error']['message'])
        except Exception as e:
            self.user_client_dict.pop(access_key, None)
            return (False, str(e))
        
    def fetch_order_info(self, access_key, secret_key, order_id, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0
        while retry_count <= self.order_info_retry_limit:
            if market_type == "SPOT":
                res = client.spot_order_info(order_id=order_id)
            else:
                raise Exception(f"market_type: {market_type} is not supported yet.")
            if res['ok']: # If it's not error -> return
                # Even though it looks fine it might return the wrong data. So, we need to check the content of the response.
                if float(res['result']['executed_volume']) == 0:
                    if retry_count == self.order_info_retry_limit:
                        self.logger.error(f"order_id: {order_id} NO_EXECUTED_VOLUME")
                        if return_dict is not None:
                            return_dict['res'] = res
                            return_dict['error_code'] = "NO_EXECUTED_VOLUME"
                            return
                        raise Exception(f"order_id: {order_id}, NO_EXECUTED_VOLUME")
                    else:
                        retry_count += 1
                        time.sleep(self.order_info_retry_term_sec)
                        continue
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = None
                return res
            else:
                # Check error messages
                if '알수없는' in res['result']['error']['message'] or '일시적인 거래량 급증' in res['result']['error']['message']:
                    if retry_count == self.order_info_retry_limit:
                        pass
                    else:
                        retry_count += 1
                        time.sleep(self.order_info_retry_term_sec)
                        continue
                self.logger.error(f"order_id: {order_id}\n{res}")
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = res['result']['error']['name']
                    return
                raise Exception(f"order_id: {order_id}, {res['result']['error']['message']}")
        
    def save_order_info_to_db(self, trade_config_uuid, trade_uuid, res, market_type):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            if market_type == "SPOT":
                order_id = res['result']['uuid']
                executed_price = round(sum([float(x['funds']) for x in res['result']['trades']]) 
                                    / sum([float(x['volume']) for x in res['result']['trades']]), 2)
                executed_qty = sum([float(x['volume']) for x in res['result']['trades']])
                side = 'BUY' if res['result']['side'] == 'bid' else 'SELL'
                order_type = 'LIMIT' if res['result']['ord_type'] == 'limit' else 'MARKET'
                symbol = res['result']['market']
                fee = float(res['result']['paid_fee'])
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
                key_uuid, access_key, secret_key = self.get_api_key_tup(order_info_dict['trade_config_uuid'], (False if order_info_dict['market_type'] == "SPOT" else True))
                # API call
                fetched_order_info_res = self.fetch_order_info(access_key, secret_key, order_info_dict['order_id'], order_info_dict['market_type'])
                # process res and save data to db
                self.save_order_info_to_db(order_info_dict['trade_config_uuid'], order_info_dict['trade_uuid'], fetched_order_info_res, order_info_dict['market_type'])
            except Exception as e:
                self.logger.error(f"handle_order_info_queue_loop|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_id, "handle_order_info_queue_loop", str(e))
                time.sleep(3)
            time.sleep(0.025)
        
    # Using limit order
    def market_long(self, access_key, secret_key, symbol, qty, price, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            res = client.spot_place_order(
                market=symbol,
                side='bid',
                volume=str(qty),
                price=str(calculate_bithumb_price(price*1.25)),
                ord_type='limit'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.trade_retry_limit, 'retry_term_sec': self.trade_retry_term_sec}
            if retry_count != 0:
                self.logger.info(f"market_long|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}")
            if res['ok']: # If it's not error -> return
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = None
                    return
                return res
            retry_error_case = False
            if '알수없는' in res['result']['error']['message']:
                retry_error_case = True
            if '일시적인 거래량 급증' in res['result']['error']['message']:
                retry_error_case = True
            if retry_error_case is False or retry_count >= self.trade_retry_limit: # If it's normal error -> return
                self.logger.info(f"market_long|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}") # TEST
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_core'] = res['result']['error']['name']
                    return
                raise Exception(res['result']['error']['message'])
            retry_count += 1
            time.sleep(self.trade_retry_term_sec)
        return res
    
    # Using market order
    def market_short(self, access_key, secret_key, symbol, qty, price, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            res = client.spot_place_order(
                market=symbol,
                side='ask',
                volume=str(qty),
                price=None,
                ord_type='market'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.trade_retry_limit, 'retry_term_sec': self.trade_retry_term_sec}
            if retry_count != 0:
                self.logger.info(f"market_short|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}")
            if res['ok']: # If it's not error -> return
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = None
                    return
                return res
            retry_error_case = False
            if '알수없는' in res['result']['error']['message']:
                retry_error_case = True
            if '일시적인 거래량 급증' in res['result']['error']['message']:
                retry_error_case = True
            if retry_error_case is False or retry_count >= self.trade_retry_limit: # If it's normal error -> return
                self.logger.info(f"market_short|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}") # TEST
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_core'] = res['result']['error']['name']
                    return
                raise Exception(res['result']['error']['message'])
            retry_count += 1
            time.sleep(self.trade_retry_term_sec)
        return res
