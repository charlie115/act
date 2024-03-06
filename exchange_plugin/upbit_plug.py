import os
import sys
import datetime
import pandas as pd
from queue import Queue
from upbit.client import Upbit
import time
from psycopg2 import extras
import traceback
from threading import Thread

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from etc.acw_api import AcwApi
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from api.utils import decrypt_data, MyException


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
        self.logger = KimpBotLogger("upbit_plug", logging_dir).logger
        self.logger.info(f"logger started.")

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

    
################################################################################################################################################
            
class UserUpbitAdaptor:
    def __init__(self, admin_telegram_id, node=None, db_dict=None, trade_df_dict=None, market_combi_code=None, logging_dir=None):
        self.user_client_dict = {}
        self.admin_telegram_id = admin_telegram_id
        self.node = node
        self.db_dict = db_dict
        self.trade_df_dict = trade_df_dict
        self.market_combi_code = market_combi_code
        self.trade_retry_term_sec = 0.2
        self.trade_retry_limit = 2
        self.order_info_retry_term_sec = 2
        self.order_info_retry_limit = 20
        self.acw_api = AcwApi()
        if db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**db_dict, 'database': 'trade_core'})
            self.user_api_key_df = self.load_user_api_keys()
        else:
            self.postgres_client = None
            self.user_api_key_df = None
        self.trade_df_dict = trade_df_dict
        self.market_combi_code = market_combi_code
        if market_combi_code is not None:
            self.market_code = [x for x in market_combi_code.split(':') if 'UPBIT' in x][0]
            self.market, self.quote_asset = self.market_code.split('/')
            self.exchange = self.market.split('_')[0]
            self.market_type = self.market.replace(self.exchange+'_','')
            self.counterpart_market_code = [x for x in market_combi_code.split(':') if 'UPBIT' not in x][0]
            self.counterpart_market, self.counterpart_quote_asset = self.counterpart_market_code.split('/')
            self.counterpart_exchange = self.counterpart_market.split('_')[0]
            self.counterpart_market_type = self.counterpart_market.replace(self.counterpart_exchange+'_','')
            # Check whether the market_type is supported
            if self.market_type not in ["SPOT"]:
                raise Exception(f"Invalid market_type: {self.market_type}")
            self.logger = KimpBotLogger(f"user_upbit_plug_{self.market_code}", logging_dir).logger
            self.logger.info(f"user_upbit_plug_{self.market_code} started.")
            self.load_user_api_keys_thread = Thread(target=self.loop_load_user_api_keys, args=(60,), daemon=True)
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
            self.logger = KimpBotLogger(f"user_upbit_plug", logging_dir).logger
            self.logger.info(f"user_upbit_plug started.")
        
    def load_user_client(self, access_key, secret_key):
        user_client = self.user_client_dict.get(access_key)
        if user_client is None:
            self.user_client_dict[access_key] = Upbit(access_key, secret_key)
            return self.user_client_dict[access_key]
        else:
            return user_client
        
    def load_user_api_keys(self):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        sql = "SELECT * FROM exchange_api_key WHERE exchange='UPBIT'"
        curr.execute(sql)
        user_api_key_df = pd.DataFrame(curr.fetchall())
        self.postgres_client.pool.putconn(conn)
        user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].applymap(lambda x: x.tobytes() if isinstance(x, memoryview) else x)
        user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].applymap(lambda x: decrypt_data(x).decode('utf-8') if x is not None else None)
        self.user_api_key_df = user_api_key_df
        return user_api_key_df
        
    def loop_load_user_api_keys(self, loop_interval_secs=60):
        self.logger.info(f"loop_load_user_api_keys started.")
        while True:
            try:
                self.user_api_key_df = self.load_user_api_keys()
            except Exception as e:
                self.logger.error(f"loop_load_user_api_keys|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_telegram_id, "loop_load_user_api_keys", self.node, "monitor", str(e))
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
        
    def get_spot_balance(self, access_key, secret_key, return_dict=None):
        upbit_client = self.load_user_client(access_key, secret_key)
        res = upbit_client.Account.Account_info()
        if res['response']['ok'] is False:
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
        upbit_client = self.load_user_client(access_key, secret_key)
        if market_type == 'SPOT':
            res = upbit_client.Account.Account_info()
            if res['response']['ok'] is False:
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['error_code'] = res['result']['error']['name']
                    return
                raise Exception(res['result']['error']['message'])
            position_df = pd.DataFrame(res['result'])
            symbol_df = position_df[position_df['currency']==symbol]['balance']
            if len(symbol_df) == 0:
                upbit_remaining_qty = 0
            else:
                upbit_remaining_qty = float(symbol_df.iloc[0])
                if return_dict is not None:
                    return_dict['res'] = upbit_remaining_qty
                    return_dict['error_code'] = None
            return upbit_remaining_qty
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
            res = client.Account.Account_info()
            if res['response']['ok'] is True:
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
                res = client.Order.Order_info(uuid=order_id)
            else:
                raise Exception(f"market_type: {market_type} is not supported yet.")
            if res['response']['ok']: # If it's not error -> return
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
                access_key, secret_key = self.get_api_key_tup(order_info_dict['trade_config_uuid'], (False if order_info_dict['market_type'] == "SPOT" else True))
                # API call
                fetched_order_info_res = self.fetch_order_info(access_key, secret_key, order_info_dict['order_id'], order_info_dict['market_type'])
                # process res and save data to db
                self.save_order_info_to_db(order_info_dict['trade_config_uuid'], order_info_dict['trade_uuid'], fetched_order_info_res, order_info_dict['market_type'])
            except Exception as e:
                self.logger.error(f"handle_order_info_queue_loop|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_telegram_id, "handle_order_info_queue_loop", self.node, "monitor", str(e))
                time.sleep(3)
            time.sleep(0.025)
        
    # Using limit order
    def market_long(self, access_key, secret_key, symbol, qty, price, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            res = client.Order.Order_new(
                market=symbol,
                side='bid',
                volume=str(qty),
                price=str(calculate_upbit_price(price*1.25)),
                ord_type='limit'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.trade_retry_limit, 'retry_term_sec': self.trade_retry_term_sec}
            if retry_count != 0:
                self.logger.info(f"market_long|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}")
            if res['response']['ok']: # If it's not error -> return
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
    
    # Using limit order
    def market_short(self, access_key, secret_key, symbol, qty, price, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        retry_count = 0

        while retry_count <= self.trade_retry_limit:
            res = client.Order.Order_new(
                market=symbol,
                side='ask',
                volume=str(qty),
                price=str(calculate_upbit_price(price*0.75)),
                ord_type='limit'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.trade_retry_limit, 'retry_term_sec': self.trade_retry_term_sec}
            if retry_count != 0:
                self.logger.info(f"market_short|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}")
            if res['response']['ok']: # If it's not error -> return
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
    