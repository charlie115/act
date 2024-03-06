import os
import sys
import datetime
import pandas as pd
import time
import traceback
from psycopg2 import extras
from functools import partial
from threading import Thread
from queue import Queue
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from exchange_plugin.upbit_plug import UserUpbitAdaptor
from exchange_plugin.binance_plug import UserBinanceAdaptor
from etc.redis_connector.redis_connector import InitRedis
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from etc.acw_api import AcwApi
from api.utils import MyException

class UserExchangeAdaptor:
    def __init__(self, admin_telegram_id, node=None, db_dict=None, trade_df_dict=None, market_combi_code=None, logging_dir=None):
        self.exchange_adaptor_dict = {}
        self.admin_telegram_id = admin_telegram_id
        self.node = node
        self.db_dict = db_dict
        if db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**db_dict, 'database': 'trade_core'})
        else:
            self.postgres_client = None
        # redis connection to read info_dict
        self.local_redis_client = InitRedis(host='localhost', port=6379, db=0, passwd=None)
        self.trade_df_dict = trade_df_dict
        self.market_combi_code = market_combi_code.upper()
        self.acw_api = AcwApi()
        self.available_exchange_adaptor_dict = {
            "UPBIT": UserUpbitAdaptor,
            "BINANCE": UserBinanceAdaptor
        }
        # self.initialize_calculate_enter_qty = None
        self.target_symbol_converter = None
        self.origin_symbol_converter = None
        self.available_market_combi_code_list = ["UPBIT_SPOT/KRW:BINANCE_USD_M/USDT"]
        if self.market_combi_code is None: # If market_combi_code is not given, initialize all exchange adaptors since it will be used for curd.py in api
            self.logger = KimpBotLogger("integrated_plug", logging_dir=logging_dir).logger
            self.logger.info('integrated_plug_logger init')
            self.exchange_adaptor_dict = {}
            for exchange in self.available_exchange_adaptor_dict.keys():
                self.exchange_adaptor_dict[exchange] = self.available_exchange_adaptor_dict[exchange](admin_telegram_id=admin_telegram_id, logging_dir=logging_dir)
            self.target_market_code = None
            self.origin_market_code = None
            self.target_market = None
            self.target_quote_asset = None
            self.target_exchange = None
            self.target_market_type = None
            self.origin_market = None
            self.origin_quote_asset = None
            self.origin_exchange = None
            self.origin_market_type = None
            self.target_exchange_adaptor = None
            self.origin_exchange_adaptor = None
        else:
            self.logger = KimpBotLogger(f"integrated_plug_{self.market_combi_code}", logging_dir=logging_dir).logger
            self.logger.info(f'integrated_plug_{self.market_combi_code}_logger init')
            self.target_market_code, self.origin_market_code = self.market_combi_code.split(':')
            self.target_market, self.target_quote_asset = self.target_market_code.split('/')
            self.target_exchange = self.target_market.split('_')[0]
            self.target_market_type = self.target_market.replace(self.target_exchange+'_', '')
            self.origin_market, self.origin_quote_asset = self.origin_market_code.split('/')
            self.origin_exchange = self.origin_market.split('_')[0]
            self.origin_market_type = self.origin_market.replace(self.origin_exchange+'_', '')
            target_exchange_adaptor_func = self.available_exchange_adaptor_dict.get(self.target_exchange)
            if target_exchange_adaptor_func is None:
                raise Exception(f'exchange {self.target_exchange} not supported')
            else:
                self.exchange_adaptor_dict[self.target_exchange] = target_exchange_adaptor_func(admin_telegram_id=admin_telegram_id, logging_dir=logging_dir)
                self.target_exchange_adaptor = self.exchange_adaptor_dict[self.target_exchange]
            origin_exchange_adaptor_func = self.available_exchange_adaptor_dict.get(self.origin_exchange)
            if origin_exchange_adaptor_func is None:
                raise Exception(f'exchange {self.origin_exchange} not supported')
            else:
                self.exchange_adaptor_dict[self.origin_exchange] = origin_exchange_adaptor_func(admin_telegram_id=admin_telegram_id, logging_dir=logging_dir)
                self.origin_exchange_adaptor = self.exchange_adaptor_dict[self.origin_exchange]
            # Initialize functions
            self.initialize_tools(self, self.market_combi_code)
            # Start reading the order history from the database
            self.order_history_df = None
            self.order_history_df_thread = Thread(target=self.load_order_history_loop, daemon=True)
            self.order_history_df_thread.start()
            # Start reading the trade history from the database
            self.trade_history_df = None
            self.trade_history_df_thread = Thread(target=self.load_trade_history_loop, daemon=True)
            self.trade_history_df_thread.start()
            while self.order_history_df is None or self.trade_history_df is None:
                time.sleep(1)
            # queue for handling handling trade info and pnl
            self.trade_info_dict_queue = Queue()
            self.trade_info_dict_queue_thread = Thread(target=self.handle_trade_info_queue_loop, daemon=True)
            self.trade_info_dict_queue_thread.start()
        
    def initialize_tools(self, market_combi_code):
        if market_combi_code not in self.available_market_combi_code_list:
            raise Exception(f'market_combi_code {market_combi_code} not supported yet.')
        if market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            # self.calculate_enter_qty = partial(self.target_exchange_adaptor.calculate_enter_qty, market_type=self.target_market_type, capital_currency='KRW')
            self.target_symbol_converter = lambda x: x+'USDT'
            self.origin_symbol_converter = lambda x: 'KRW-'+x
        else:
            raise Exception(f'market_combi_code {market_combi_code} not supported yet.')
        
    def load_order_history(self, table_name='order_history'):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            # Check whether it's empty
            if self.postgres_client.is_table_empty(table_name):
                self.order_history_df = pd.DataFrame(columns=self.postgres_client.get_column_names(table_name))
                self.postgres_client.pool.putconn(conn)
            else:
                sql = f"""SELECT * FROM {table_name}"""
                curr.execute(sql)
                self.order_history_df = pd.DataFrame(curr.fetchall())
                self.postgres_client.pool.putconn(conn)
        except Exception as e:
            self.postgres_client.pool.putconn(conn)
            self.logger.error(f"load_order_{table_name}|{e}")
            self.logger.error(traceback.format_exc())
            raise e
        
    def load_order_history_loop(self):
        self.logger.info(f"load_order_history_loop started.")
        while True:
            try:
                self.load_order_history()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"load_order_history_loop|{e}")
                self.logger.error(traceback.format_exc())
                time.sleep(3)
                
    def load_trade_history(self, table_name='trade_history'):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            # Chekc whether it's empty
            if self.postgres_client.is_table_empty(table_name):
                self.trade_history_df = pd.DataFrame(columns=self.postgres_client.get_column_names(table_name))
                self.postgres_client.pool.putconn(conn)
            else:
                sql = f"""SELECT * FROM {table_name}"""
                curr.execute(sql)
                self.trade_history_df = pd.DataFrame(curr.fetchall())
                self.postgres_client.pool.putconn(conn)
        except Exception as e:
            self.postgres_client.pool.putconn(conn)
            self.logger.error(f"load_{table_name}|{e}")
            self.logger.error(traceback.format_exc())
            raise e
        
    def load_trade_history_loop(self):
        self.logger.info(f"load_trade_history_loop started.")
        while True:
            try:                    
                self.load_trade_history()
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"load_trade_history_loop|{e}")
                self.logger.error(traceback.format_exc())
                time.sleep(3)

    def check_api_key(self, exchange, access_key, secret_key, passphrase=None, futures=False):
        """FUTURES includes USD_M, COIN_M"""
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        if exchange == "OKX":
            return self.exchange_adaptor_dict[exchange].check_api_key(access_key, secret_key, passphrase, futures)
        else:
            return self.exchange_adaptor_dict[exchange].check_api_key(access_key, secret_key, futures)
    
    def get_position(self, exchange, access_key, secret_key, market_type, passphrase=None):
        """SPOT position columns: ['asset', 'free', 'locked']
        USD_M position columns: ["symbol", "base_asset", "qty", "margin_type", "entry_price", "liquidation_price", "leverage"]
        """
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            position_df = exchange_adaptor.all_position_information(access_key, secret_key, market_type)
        elif exchange == "BINANCE":
            position_df = exchange_adaptor.all_position_information(access_key, secret_key, market_type)
            info_df = pickle.loads(self.local_redis_client.get_data(f'TRADE_CORE|{exchange.lower()}_{market_type.lower()}_info_df'))
            position_df = position_df.merge(info_df[['symbol','base_asset']], how='left', on='symbol')
            position_df = position_df.rename(columns={"positionAmt":"qty", "marginType":"margin_type", "entryPrice":"entry_price", "liquidationPrice":"liquidation_price"})
            position_df["ROI"] = position_df.apply(lambda x: (x['entry_price']-x['markPrice'])/x['markPrice']*x['leverage']*100 if x['qty']<0 else 
                                                   (x['markPrice']-x['entry_price'])/x['entry_price']*['leverage']*100, axis=1)
        else:
            raise Exception(f'exchange {exchange} not supported')
        return position_df
    
    def get_capital(self, exchange, access_key, secret_key, market_type, passphrase=None):
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            currency = 'KRW'
            position_df = exchange_adaptor.get_balance(access_key, secret_key, market_type)
            ticker_df = pickle.loads(self.local_redis_client.get_data(f"TRADE_CORE|{exchange.lower()}_{market_type.lower()}_ticker_df"))
            position_df['symbol'] = position_df['unit_currency']+'-'+position_df['asset']
            merged_df = position_df.merge(ticker_df[['symbol','lastPrice']], how='left', on='symbol')
            merged_df.loc[merged_df['asset']==currency, 'lastPrice'] = 1
            merged_df['entered'] = merged_df['avg_buy_price'] * merged_df['free']
            merged_df['locked'] = merged_df['avg_buy_price'] * merged_df['locked']
            free = round(merged_df.loc[merged_df['asset']==currency, 'free'].values[0])
            locked = round(merged_df['entered'].sum() + merged_df['locked'].sum())
            before_pnl = round(free + locked)
            after_pnl = round((((merged_df['free'] + merged_df['locked']) * merged_df['lastPrice'])).sum())
            pnl = round(after_pnl - before_pnl)
        elif exchange == "BINANCE":
            currency = 'USDT'
            balance_df = self.exchange_adaptor_dict[exchange].get_balance(access_key, secret_key, market_type)
            currency_df = balance_df[balance_df['asset']==currency]
            free = round(currency_df['availableBalance'].values[0],1)
            locked = round(currency_df['walletBalance'].values[0] - free,1)
            before_pnl = round(currency_df['walletBalance'].values[0],1)
            pnl = round(currency_df['unrealizedProfit'].values[0],1)
            after_pnl = round(currency_df['walletBalance'].values[0] + pnl,1)
        else:
            raise Exception(f'exchange {exchange} not supported')

        capital_series = pd.Series({'free':free, 'locked':locked, 'before_pnl': before_pnl, 'pnl':pnl, 'after_pnl':after_pnl, 'currency': currency})
        return capital_series
    
    def target_margin_call_callback(self):
        print(f"target_margin_call_callback called")

    def target_liquidation_callback(self):
        print(f"target_liquidation_callback called")

    def origin_margin_call_callback(self):
        print(f"origin_margin_call_callback called")

    def origin_liquidation_callback(self):
        print(f"origin_liquidation_callback called")
    
    def start_user_socket_stream(self, market_combi_code):
        if self.market_combi_code not in self.available_market_combi_code_list:
            raise Exception(f'market_combi_code {market_combi_code} not supported yet.')
        if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            self.target_exchange_adaptor.start_user_socket_stream(self.target_market_type)
            self.origin_exchange_adaptor.start_user_socket_stream(self.origin_market_type, self.target_margin_call_callback, self.target_liquidation_callback)

    def long_short_trade(self, merged_row):
        if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            # first calculate the qty based on the KRW capital
            qty = self.origin_exchange_adaptor.calculate_enter_qty(merged_row['base_asset'], merged_row['dollar'], merged_row['bp'], merged_row['LS_premium'], merged_row['SL_premium'], merged_row['trade_capital'], self.origin_market_type)
            if qty == 0:
                body = f"투입금액이 {merged_row['base_asset']}USDT 1개의 가격보다 낮습니다. \n주문을 취소합니다."
                # self.acw_api.create_message(merged_row['telegram_id'], "주문취소", self.node, 'warning', body)
                raise Exception(body)
            modified_input_usd = qty * merged_row['bp']/merged_row['dollar'] # Binance USD_M bid price in USDT
            modified_input_krw = qty * merged_row['ap'] # UPBIT KRW ask price in KRW

            # Get Binance API keys
            origin_access_key, origin_secret_key = self.origin_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.origin_market_type else True)
            # Binance USD_M Short
            origin_return_dict = {}
            origin_trade_thread = Thread(target=self.origin_exchange_adaptor.market_short, args=(origin_access_key, origin_secret_key,
                self.origin_symbol_converter(merged_row['base_asset']), qty, self.origin_market_type, origin_return_dict))
            origin_trade_thread.start()

            # Get Upbit API keys
            target_access_key, target_secret_key = self.target_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.target_market_type else True)
            # Upbit trade + response validation
            target_trade_error = False
            try:
                target_res = self.target_exchange_adaptor.market_long(target_access_key, target_secret_key, merged_row['base_asset'], qty, merged_row['ap'])
                origin_trade_thread.join()
                title = "업비트 LONG 성공"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 업비트 {self.target_symbol_converter(merged_row['base_asset'])} LONG거래가 정상적으로 진행되었습니다."
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'info', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                target_order_id = target_res['result']['uuid']
            except Exception as e:
                target_trade_error = True
                origin_trade_thread.join()
                title = "업비트 LONG 실패"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 업비트 {self.target_symbol_converter(merged_row['base_asset'])} LONG거래가 실패하였습니다. {e}"
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'error', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                error_log = f"{title}|trade uuid:{merged_row['uuid']}\error:{e}\n{body}"
                self.logger.error(error_log)
                # Monitoring purpose
                self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'error', error_log, send_times=1, send_term=1)

            # Binance response validation
            origin_trade_error = False
            if origin_return_dict['error_code'] is None:
                title = "바이낸스 SHORT 성공"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 바이낸스 {self.origin_symbol_converter(merged_row['base_asset'])} SHORT거래가 정상적으로 진행되었습니다."
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'info', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                origin_res = origin_return_dict['res']
                origin_order_id = origin_res['orderId']
            else:
                origin_trade_error = True
                title = "바이낸스 SHORT 실패"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 바이낸스 {self.origin_symbol_converter(merged_row['base_asset'])} SHORT거래가 실패하였습니다. {origin_return_dict['error_code']}"
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'error', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                error_log = f"{title}|trade uuid:{merged_row['uuid']}\nres:{origin_return_dict['res']}\n{body}"
                self.logger.error(error_log)
                # Monitoring purpose
                self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'error', error_log, send_times=1, send_term=1)
            
            # raise exception according to the result of the trade
            if origin_trade_error and target_trade_error:
                raise MyException(f"업비트 LONG과 바이낸스 SHORT 모두 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=4)
            elif origin_trade_error:
                raise MyException(f"바이낸스 SHORT 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=2)
            elif target_trade_error:
                raise MyException(f"업비트 LONG 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=3)
            
            # put order info to the queue
            target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.target_symbol_converter(merged_row['base_asset']), "order_id": target_order_id, "market_type": self.target_market_type}
            origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.origin_symbol_converter(merged_row['base_asset']), "order_id": origin_order_id, "market_type": self.origin_market_type}
            
            self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
            self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)

            # generate trade info dict
            trade_info_dict = {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "base_asset": merged_row['base_asset'],
                               "target_order_id": target_order_id, "origin_order_id": origin_order_id, "target_premium_value": merged_row['high'], "dollar": merged_row['dollar'], "trade_side": "ENTER",
                               "modified_input_usd": modified_input_usd, "modified_input_krw": modified_input_krw, "last_trade_history_uuid": merged_row['last_trade_history_uuid'],
                               "telegram_id": merged_row['telegram_id'], "send_times": merged_row['send_times'], "send_term": merged_row['send_term']}
            # put trade info to the queue
            self.trade_info_dict_queue.put(trade_info_dict)
            return trade_info_dict

        else:
            raise Exception(f'market_combi_code {self.market_combi_code} not supported yet.')
        
    def short_long_trade(self, merged_row):
        if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            # first read the last_trade_history_uuid from the merged_row
            last_trade_history_uuid = merged_row['last_trade_history_uuid']
            if last_trade_history_uuid is None:
                raise Exception(f"trade_uuid: {merged_row['uuid']}, last_trade_history_uuid is None. It's impossible to do short_long_trade.")
            # Check whether the trade_side of last_trade_history is "ENTER"
            last_trade_history_series = self.trade_history_df[self.trade_history_df['uuid']==last_trade_history_uuid]
            if len(last_trade_history_series) == 0:
                raise Exception(f"trade_uuid: {merged_row['uuid']}, last_trade_history_uuid: {last_trade_history_uuid} does not exist in the trade_history. It's impossible to do short_long_trade.")
            if last_trade_history_series['trade_side'].values[0] != "ENTER":
                raise Exception(f"trade_uuid: {merged_row['uuid']}, last_trade_history_uuid's trade_side is not 'ENTER'. It's impossible to do short_long_trade.")
            # Passed validation for trade_history
            target_order_id = last_trade_history_series['target_order_id'].values[0]
            origin_order_id = last_trade_history_series['origin_order_id'].values[0]
            # Get order_history_series
            target_order_history_series = self.order_history_df[self.order_history_df['order_id']==target_order_id]
            origin_order_history_series = self.order_history_df[self.order_history_df['order_id']==origin_order_id]
            # Get entered qty and symbol
            target_symbol = target_order_history_series['symbol'].values[0]
            target_qty = target_order_history_series['qty'].values[0]
            origin_symbol = origin_order_history_series['symbol'].values[0]
            origin_qty = origin_order_history_series['qty'].values[0]

            # Get Binance API keys
            origin_access_key, origin_secret_key = self.origin_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.origin_market_type else True)
            
            # # Get remaining position
            # origin_return_dict = {}
            # origin_position_thread = Thread(target=self.origin_exchange_adaptor.position_information, args=(origin_access_key, origin_secret_key, self.origin_market_type, origin_symbol, origin_return_dict), daemon=True)
            # origin_position_thread.start()
            # target_remaining_qty = self.target_exchange_adaptor.position_information(target_access_key, target_secret_key, self.target_market_type, target_symbol)
            
            # Binance USD_M Long
            origin_return_dict = {}
            origin_trade_thread = Thread(target=self.origin_exchange_adaptor.market_long, args=(origin_access_key, origin_secret_key,
                origin_symbol, origin_qty, self.origin_market_type, origin_return_dict))
            origin_trade_thread.start()

            # Get Upbit API keys
            target_access_key, target_secret_key = self.target_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.target_market_type else True)
            # Upbit trade + response validation
            target_trade_error = False
            try:
                target_res = self.target_exchange_adaptor.market_short(target_access_key, target_secret_key, target_symbol, target_qty, merged_row['ap'])
                origin_trade_thread.join()
                title = "업비트 SHORT 성공"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 업비트 {target_symbol} SHORT거래가 정상적으로 진행되었습니다."
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'info', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                target_order_id = target_res['result']['uuid']
            except Exception as e:
                target_trade_error = True
                origin_trade_thread.join()
                title = "업비트 SHORT 실패"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 업비트 {target_symbol} SHORT거래가 실패하였습니다. {e}"
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'error', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                error_log = f"{title}|trade uuid:{merged_row['uuid']}\error:{e}\n{body}"
                self.logger.error(error_log)
                # Monitoring purpose
                self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'error', error_log, send_times=1, send_term=1)

            # Binance response validation
            origin_trade_error = False
            if origin_return_dict['error_code'] is None:
                title = "바이낸스 LONG 성공"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 바이낸스 {origin_symbol} LONG거래가 정상적으로 진행되었습니다."
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'info', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                origin_res = origin_return_dict['res']
                origin_order_id = origin_res['orderId']
            else:
                origin_trade_error = True
                title = "바이낸스 LONG 실패"
                body = f"<b>거래UUID: {merged_row['uuid']}</b>의 바이낸스 {origin_symbol} SHORT거래가 실패하였습니다. {origin_return_dict['error_code']}"
                self.acw_api.create_message_thread(merged_row['telegram_id'], title, self.node, 'error', body, send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                error_log = f"{title}|trade uuid:{merged_row['uuid']}\nres:{origin_return_dict['res']}\n{body}"
                self.logger.error(error_log)
                # Monitoring purpose
                self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'error', error_log, send_times=1, send_term=1)
            
            # raise exception according to the result of the trade
            if origin_trade_error and target_trade_error:
                raise MyException(f"업비트 SHORT과 바이낸스 LONG 모두 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=4)
            elif origin_trade_error:
                raise MyException(f"바이낸스 LONG 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=2)
            elif target_trade_error:
                raise MyException(f"업비트 SHORT 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=3)
            
            # put order info to the queue
            target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.target_symbol_converter(merged_row['base_asset']), "order_id": target_order_id, "market_type": self.target_market_type}
            origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.origin_symbol_converter(merged_row['base_asset']), "order_id": origin_order_id, "market_type": self.origin_market_type}
            
            self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
            self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)

            # generate trade info dict
            trade_info_dict = {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "base_asset": merged_row['base_asset'],
                               "target_order_id": target_order_id, "origin_order_id": origin_order_id, "target_premium_value": merged_row['high'], "dollar": merged_row['dollar'], "trade_side": "EXIT",
                               "modified_input_usd": None, "modified_input_krw": None, "last_trade_history_uuid": merged_row['last_trade_history_uuid'],
                               "telegram_id": merged_row['telegram_id'], "send_times": merged_row['send_times'], "send_term": merged_row['send_term']}
            # put trade info to the queue
            self.trade_info_dict_queue.put(trade_info_dict)
            return trade_info_dict

        else:
            raise Exception(f'market_combi_code {self.market_combi_code} not supported yet.')
        
    def handle_trade_info(self):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        # initialize
        target_order_history = None
        origin_order_history = None
        try:
            # if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            trade_info_dict = self.trade_info_dict_queue.get()

            while target_order_history is None or origin_order_history is None:
                # Check whether the target order history exists in the database
                curr.execute(f"SELECT * FROM order_history WHERE order_id='{trade_info_dict['target_order_id']}'")
                target_order_history = curr.fetchone()
                # Check whether the origin order history exists in the database
                curr.execute(f"SELECT * FROM order_history WHERE order_id='{trade_info_dict['origin_order_id']}'")
                origin_order_history = curr.fetchone()
                if target_order_history is not None and origin_order_history is not None:
                    break
                time.sleep(1)

            # Now both are not None
            # id SERIAL PRIMARY KEY,
            # trade_config_uuid, trade_uuid, registered_datetime, trade_side, base_asset, target_order_id, origin_order_id, dollar, remark,
            trade_info_dict['registered_datetime'] = datetime.datetime.utcnow()
            trade_info_dict['remark'] = None
            # Need to calculate the executed_premium_value and slippage_p
            target_executed_price = target_order_history['executed_price']
            origin_executed_price = origin_order_history['executed_price']
            # Calculate the executed_premium_value
            if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                trade_info_dict['executed_premium_value'] = (target_executed_price - origin_executed_price) / origin_executed_price * 100
                # check whether it used usdt_conversion
                if trade_info_dict['target_premium_value'] >= 800:
                    trade_info_dict['executed_premium_value'] = (1+trade_info_dict['executed_premium_value'])/100 * trade_info_dict['dollar']
            # Calculate the slippage_p which means the percentage of the slippage between target_premium_value and executed_premium_value
            trade_info_dict['slippage_p'] = abs((trade_info_dict['executed_premium_value'] - trade_info_dict['target_premium_value']) / trade_info_dict['target_premium_value'] * 100)

            # Insert trade info to the database and return the generated uuid
            sql = """INSERT INTO trade_history (trade_config_uuid, trade_uuid, registered_datetime, trade_side, base_asset, target_order_id, origin_order_id, 
            target_premium_value, executed_premium_value, slippage_p, dollar, remark) 
            VALUES (%(trade_config_uuid)s, %(trade_uuid)s, %(registered_datetime)s, %(trade_side)s, %(base_asset)s, 
            %(target_order_id)s, %(origin_order_id)s, %(target_premium_value)s, %(executed_premium_value)s, %(slippage_p)s, %(dollar)s, %(remark)s) RETURNING uuid"""
            curr.execute(sql, trade_info_dict)
            generated_uuid = curr.fetchone()[0]            
            # UPDATE the last_trade_history_uuid to 'trade' table
            curr.execute(f"UPDATE trade SET last_trade_history_uuid='{generated_uuid}' WHERE uuid='{trade_info_dict['trade_uuid']}'")
            conn.commit()
            # else:
            #     raise Exception(f'market_combi_code {self.market_combi_code} not supported yet.')
            self.postgres_client.pool.putconn(conn)

            # Send message to the user
            if trade_info_dict['trade_side'] == 'ENTER':
                title = "진입거래 성공"
                body = f"<b>거래UUID: {trade_info_dict['trade_uuid']}</b>의 거래가 정상적으로 진행되었습니다."
                full_body = title + '\n' + body
            else:
                title = "탈출거래 성공"
                body = f"<b>거래UUID: {trade_info_dict['trade_uuid']}</b>의 거래가 정상적으로 진행되었습니다."
                full_body = title + '\n' + body
            self.acw_api.create_message_thread(trade_info_dict['telegram_id'], title, self.node, 'info', full_body, send_times=trade_info_dict['send_times'], send_term=trade_info_dict['send_term'])
            
            # Generate PnL hisrory if it's exit trade
            if trade_info_dict['trade_side'] == 'EXIT':
                self.generate_pnl_history(trade_info_dict)
        except Exception as e:
            self.postgres_client.pool.putconn(conn)
            self.logger.error(f"handle_trade_info|{e}")
            self.logger.error(traceback.format_exc())
            raise e

    def handle_trade_info_queue_loop(self):
        self.logger.info(f"handle_trade_info_queue_loop started.")
        while True:
            try:
                self.handle_trade_info()
            except Exception as e:
                self.logger.error(f"handle_trade_info_queue_loop|{e}")
                self.logger.error(traceback.format_exc())
                time.sleep(3)
        
    def generate_pnl_history(self, trade_info_dict):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        try:
            # Fisrt check the last_trade_history_uuid to match ENTER trade and EXIT trade
            last_trade_history_series = self.trade_history_df[self.trade_history_df['uuid']==trade_info_dict['last_trade_history_uuid']]
            # Check whether it exists
            if len(last_trade_history_series) == 0:
                raise Exception(f"trade_uuid: {trade_info_dict['trade_uuid']}, last_trade_history_uuid: {trade_info_dict['last_trade_history_uuid']} does not exist in the trade_history. It's impossible to do generate_pnl_history.")
            # Check whether the last trade history's trade_side is "ENTER"
            last_trade_history_series_trade_side = last_trade_history_series['trade_side'].values[0]
            if last_trade_history_series_trade_side != "ENTER":
                raise Exception(f"trade_uuid: {trade_info_dict['trade_uuid']}, last_trade_history_uuid's trade_side is not 'ENTER'. trade_side:{last_trade_history_series_trade_side} It's impossible to do generate_pnl_history.")
            # Passed validation for fetching the last trade_history
            
            # Fetch the ENTER trade_history
            enter_trade_history_series = last_trade_history_series
            enter_target_order_id = enter_trade_history_series['target_order_id'].values[0]
            enter_origin_order_id = enter_trade_history_series['origin_order_id'].values[0]
            
            # Fetch the ENTER target_order_history and origin_order_history
            enter_target_order_history_series = self.order_history_df[self.order_history_df['order_id']==enter_target_order_id]
            enter_origin_order_history_series = self.order_history_df[self.order_history_df['order_id']==enter_origin_order_id]
            
            # Fetch the EXIT target_order_history and origin_order_history
            exit_target_order_history_series = self.order_history_df[self.order_history_df['order_id']==trade_info_dict['target_order_id']]
            exit_origin_order_history_series = self.order_history_df[self.order_history_df['order_id']==trade_info_dict['origin_order_id']]
            
            # Calculate the pnl
            target_total_fee = enter_target_order_history_series['fee'].values[0] + exit_target_order_history_series['fee'].values[0]
            origin_total_fee = enter_origin_order_history_series['fee'].values[0] + exit_origin_order_history_series['fee'].values[0]
            
            
            if self.market_combi_code == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                # Calculate realized_premium_gap_p
                enter_trade_executed_premium_value = enter_trade_history_series['executed_premium_value'].values[0]
                exit_trade_executed_premium_value = trade_info_dict['executed_premium_value']
                realized_premium_gap_p = exit_trade_executed_premium_value - enter_trade_executed_premium_value
                # Check whether it used usdt_conversion value
                if enter_trade_history_series['target_premium_value'].values[0] >= 800:
                    realized_premium_gap_p = (exit_trade_executed_premium_value - enter_trade_executed_premium_value)/enter_trade_executed_premium_value*100
            
            # Insert pnl history to the database
            
            # send message to the user


            else:
                raise Exception(f'market_combi_code {self.market_combi_code} not supported yet.')
            self.postgres_client.pool.putconn(conn)
        except Exception as e:
            self.postgres_client.pool.putconn(conn)
            self.logger.error(f"generate_pnl_history|{e}")
            self.logger.error(traceback.format_exc())
            raise e

          


