import os
import sys
import datetime
import pandas as pd
import time
import traceback
import numpy as np
from psycopg2 import extras
from functools import partial
from threading import Thread
from queue import Queue
from decimal import Decimal
import _pickle as pickle

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import TradeCoreLogger
from exchange_plugin.upbit_plug import UserUpbitAdaptor
from exchange_plugin.binance_plug import UserBinanceAdaptor
from etc.redis_connector.redis_helper import RedisHelper
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from etc.utils import get_trade_df
from standalone_func.uuid_converter import display_id_to_trade_uuid, trade_uuid_to_display_id
from api.utils import MyException
from standalone_func.premium_data_generator import get_premium_df

class UserExchangeAdaptor:
    def __init__(self,
                 admin_id,
                 acw_api,
                 redis_db_dict,
                 postgres_db_dict=None,
                 market_code_combination=None,
                 api_server=False,
                 logging_dir=None):
        self.exchange_adaptor_dict = {}
        self.admin_id = admin_id
        self.postgres_db_dict = postgres_db_dict
        if postgres_db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
        else:
            self.postgres_client = None
        # redis connection to read info_dict
        if api_server:
            self.redis = RedisHelper(**redis_db_dict)
        else:
            self.redis = RedisHelper()
        self.market_code_combination = market_code_combination
        self.acw_api = acw_api
        self.available_exchange_adaptor_dict = {
            "UPBIT": UserUpbitAdaptor,
            "BINANCE": UserBinanceAdaptor
        }
        if self.market_code_combination is None: # If market_code_combination is not given, initialize all exchange adaptors since it will be used for crud.py in api
            self.logger = TradeCoreLogger("integrated_plug", logging_dir=logging_dir).logger
            self.logger.info('integrated_plug_logger init')
            self.exchange_adaptor_dict = {}
            for exchange in self.available_exchange_adaptor_dict.keys():
                self.exchange_adaptor_dict[exchange] = self.available_exchange_adaptor_dict[exchange](admin_id=admin_id, acw_api=acw_api, logging_dir=logging_dir)
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
            logger_name = self.market_code_combination.replace('/', '__').replace(':','-')
            self.logger = TradeCoreLogger(f"integrated_plug_{logger_name}", logging_dir=logging_dir).logger
            self.logger.info(f'integrated_plug_{self.market_code_combination}_logger init')
            self.target_market_code, self.origin_market_code = self.market_code_combination.split(':')
            self.target_market, self.target_quote_asset = self.target_market_code.split('/')
            self.target_exchange = self.target_market.split('_')[0]
            self.target_market_type = self.target_market.replace(self.target_exchange+'_', '')
            self.origin_market, self.origin_quote_asset = self.origin_market_code.split('/')
            self.origin_exchange = self.origin_market.split('_')[0]
            self.origin_market_type = self.origin_market.replace(self.origin_exchange+'_', '')
            target_exchange_adaptor_func = self.available_exchange_adaptor_dict.get(self.target_exchange)
            # queue for handling handling trade info and pnl
            self.trade_info_dict_queue = Queue()
            self.trade_info_dict_queue_thread = Thread(target=self.handle_trade_info_queue_loop, daemon=True)
            self.trade_info_dict_queue_thread.start()
            if not api_server:
                # queue for handling margin call trades of short_long and long_short
                self.margin_liquidation_call_trade_queue = Queue()
                self.margin_liquidation_call_trade_queue_thread = Thread(target=self.handle_margin_liquidation_call_trade_queue_loop, daemon=True)
                self.margin_liquidation_call_trade_queue_thread.start()
            if target_exchange_adaptor_func is None:
                raise Exception(f'exchange {self.target_exchange} not supported')
            else:
                self.exchange_adaptor_dict[self.target_exchange] = target_exchange_adaptor_func(admin_id=admin_id,
                                                                                                acw_api=self.acw_api,
                                                                                                postgres_db_dict=self.postgres_db_dict,
                                                                                                market_code_combination=self.market_code_combination,
                                                                                                margin_liquidation_call_trade_queue=self.margin_liquidation_call_trade_queue if not api_server else None,
                                                                                                logging_dir=logging_dir)
                self.target_exchange_adaptor = self.exchange_adaptor_dict[self.target_exchange]
            origin_exchange_adaptor_func = self.available_exchange_adaptor_dict.get(self.origin_exchange)
            if origin_exchange_adaptor_func is None:
                raise Exception(f'exchange {self.origin_exchange} not supported')
            else:
                self.exchange_adaptor_dict[self.origin_exchange] = origin_exchange_adaptor_func(admin_id=admin_id,
                                                                                                acw_api=self.acw_api,
                                                                                                postgres_db_dict=self.postgres_db_dict,
                                                                                                market_code_combination=self.market_code_combination,
                                                                                                margin_liquidation_call_trade_queue=self.margin_liquidation_call_trade_queue if not api_server else None,
                                                                                                logging_dir=logging_dir)
                self.origin_exchange_adaptor = self.exchange_adaptor_dict[self.origin_exchange]
            # # Initialize functions
            # self.initialize_tools(self.market_code_combination)
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
        
    def symbol_converter(self, market_code, base_asset):
        if market_code == "UPBIT_SPOT/KRW":
            return 'KRW-'+base_asset
        elif market_code == "BINANCE_USD_M/USDT":
            return base_asset+'USDT'
        elif market_code == "BINANCE_SPOT/USDT":
            return base_asset+'USDT'
        else:
            raise Exception(f'market_code {market_code} not supported yet.')
        
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
        
    def get_deposit_address(self, exchange, access_key, secret_key, passphrase, asset='USDT', network='TRX'):
        exchange = exchange.upper()
        if exchange == "BINANCE":
            return self.exchange_adaptor_dict[exchange].get_deposit_address(access_key, secret_key, asset, network)
        else:
            raise Exception(f'exchange {exchange} not supported')
        
    def get_deposit_amount(self, exchange, access_key, secret_key, passphrase, txid, asset='USDT'):
        exchange = exchange.upper()
        if exchange == "BINANCE":
            return self.exchange_adaptor_dict[exchange].get_deposit_amount(access_key, secret_key, txid, asset)
        else:
            raise Exception(f'exchange {exchange} not supported')
        
    def get_position(self, exchange, access_key, secret_key, market_type, passphrase=None):
        """SPOT position columns: ['asset', 'free', 'locked']
        USD_M position columns: ["symbol", "base_asset", "qty", "margin_type", "entry_price", "liquidation_price", "leverage"]
        """
        # Load info_dict
        fetched_info_dict = self.redis.get_data('info_dict')
        if fetched_info_dict is None:
            raise Exception("info_dict is not loaded.")
        fetched_info_dict = pickle.loads(fetched_info_dict)
        
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            position_df = exchange_adaptor.all_position_information(access_key, secret_key, market_type)
        elif exchange == "BINANCE":
            position_df = exchange_adaptor.all_position_information(access_key, secret_key, market_type)
            if position_df.empty:
                return position_df
            info_df = fetched_info_dict[f'{exchange.lower()}_{market_type.lower()}_info_df']
            position_df = position_df.merge(info_df[['symbol','base_asset']], how='left', on='symbol')
            position_df = position_df.rename(columns={"positionAmt":"qty", "marginType":"margin_type", "entryPrice":"entry_price", "liquidationPrice":"liquidation_price"})
            if len(position_df) == 0:
                position_df["ROI"] = None
            else:
                position_df["ROI"] = position_df.apply(lambda x: (x['entry_price']-x['markPrice'])/x['markPrice']*x['leverage']*100 if x['qty']<0 else 
                                                   (x['markPrice']-x['entry_price'])/x['entry_price']*x['leverage']*100, axis=1)
        else:
            raise Exception(f'exchange {exchange} not supported')
        return position_df
    
    def get_capital(self, exchange, access_key, secret_key, market_type, passphrase=None):
        # Load info_dict
        fetched_info_dict = self.redis.get_data('info_dict')
        if fetched_info_dict is None:
            raise Exception("info_dict is not loaded.")
        fetched_info_dict = pickle.loads(fetched_info_dict)
        
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        exchange_adaptor = self.exchange_adaptor_dict[exchange]
        if exchange == "UPBIT":
            currency = 'KRW'
            position_df = exchange_adaptor.get_balance(access_key, secret_key, market_type)
            ticker_df = fetched_info_dict[f"{exchange.lower()}_{market_type.lower()}_ticker_df"]
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
    
    def get_market_maxqty(self, exchange, market_type, symbol):
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        if exchange == "BINANCE":
            self.exchange_adaptor_dict[exchange].get_market_maxqty(market_type, symbol)
        else:
            # temporary
            return None
        
    def change_margin_type(self, exchange, access_key, secret_key, market_type, margin_type_cross, symbol=None, passphrase=None):
        if market_type == 'SPOT':
            raise Exception(f"market_type {market_type} does not support margin_type change.")
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        if exchange == "BINANCE":
            if margin_type_cross:
                margin_type = 'CROSSED'
            else:
                margin_type = 'ISOLATED'
            self.exchange_adaptor_dict[exchange].change_margin_type(access_key, secret_key, market_type, symbol, margin_type)
        else:
            # not supported yet
            raise Exception(f'exchange {exchange} not supported')
        
    def change_leverage(self, exchange, access_key, secret_key, market_type, leverage, symbol=None, passphrase=None):
        if market_type == 'SPOT':
            raise Exception(f"market_type {market_type} does not support leverage change.")
        exchange = exchange.upper()
        if exchange not in self.exchange_adaptor_dict:
            raise Exception(f'exchange {exchange} not supported')
        if exchange == "BINANCE":
            self.exchange_adaptor_dict[exchange].change_leverage(access_key, secret_key, market_type, symbol, leverage)
        else:
            # not supported yet
            raise Exception(f'exchange {exchange} not supported')

    def long_short_trade(self, merged_row, liquidation_call=False):
        try:
            if self.market_code_combination == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                trade_side = "ENTER"
                # Check whether the trade_switch is 0 // trade_switch 0: 진입대기, -1: 탈출대기, -2: 진입에러, 1:탈출완료, 2:탈출에러, 3: 거래 진행 중
                if merged_row['trade_switch'] != 0:
                    return
                # first calculate the qty based on the KRW capital
                qty = self.origin_exchange_adaptor.calculate_enter_qty(merged_row['base_asset'], merged_row['dollar'], merged_row['bp'], merged_row['LS_premium'], merged_row['SL_premium'], merged_row['trade_capital'], self.origin_market_type)
                if qty == 0:
                    body = f"투입금액이 {merged_row['base_asset']}USDT 1개의 가격보다 낮습니다. \n주문을 취소합니다."
                    # self.acw_api.create_message(merged_row['telegram_id'], "주문취소", self.node, 'WARNING', body)
                    raise Exception(body)
                modified_input_usd = qty * merged_row['bp']/merged_row['dollar'] # Binance USD_M bid price in USDT
                modified_input_krw = qty * merged_row['ap'] # UPBIT KRW ask price in KRW

                # Get Binance API keys
                origin_access_key, origin_secret_key = self.origin_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.origin_market_type else True)
                # Binance USD_M Short
                origin_return_dict = {}
                origin_trade_thread = Thread(target=self.origin_exchange_adaptor.market_short, args=(origin_access_key, origin_secret_key,
                    self.symbol_converter(self.origin_market_code, merged_row['base_asset']), qty, self.origin_market_type, False, origin_return_dict))
                origin_trade_thread.start()

                # Get Upbit API keys
                target_access_key, target_secret_key = self.target_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.target_market_type else True)
                # Upbit trade + response validation
                target_trade_error = False
                try:
                    target_res = self.target_exchange_adaptor.market_long(target_access_key, target_secret_key, self.symbol_converter(self.target_market_code, merged_row['base_asset']), qty, merged_row['ap'])
                    origin_trade_thread.join()
                    title = "업비트 매수 성공"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 매수거래({float(qty)}개, {round(merged_row['trade_capital'])}원)가 정상적으로 진행되었습니다."
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    target_order_id = target_res['result']['uuid']
                    
                    # put order info to the queue
                    target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                               "trade_uuid": merged_row['uuid'],
                                               "symbol": self.symbol_converter(self.target_market_code, merged_row['base_asset']),
                                               "order_id": target_order_id, "market_type": self.target_market_type}
                    self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
                except Exception as e:
                    target_trade_error = True
                    origin_trade_thread.join()
                    title = "업비트 매수 실패"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}({merged_row['uuid']})의 업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 매수거래({float(qty)}개, {round(merged_row['trade_capital'])}원)가 실패하였습니다. {e}"
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    error_log = f"{title}|trade uuid:{merged_row['uuid']}\error:{e}\n{body}"
                    self.logger.error(error_log)
                    # Monitoring purpose
                    self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)

                # Binance response validation
                origin_trade_error = False
                if origin_return_dict['error_code'] is None:
                    title = "바이낸스 SHORT 성공"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} SHORT거래({float(qty)}개, {round(merged_row['trade_capital'])}원)가 정상적으로 진행되었습니다."
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    origin_res = origin_return_dict['res']
                    origin_order_id = str(origin_res['orderId'])
                    
                    # put order info to the queue
                    origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                               "trade_uuid": merged_row['uuid'],
                                               "symbol": self.symbol_converter(self.origin_market_code, merged_row['base_asset']),
                                               "order_id": origin_order_id,
                                               "market_type": self.origin_market_type}
                    self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)
                else:
                    origin_trade_error = True
                    title = "바이낸스 SHORT 실패"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}({merged_row['uuid']})의 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} SHORT거래({float(qty)}개, {round(merged_row['trade_capital'])}원)가 실패하였습니다."
                    body += f"\n바이낸스 에러내용: {origin_return_dict['res']}, 에러코드: {origin_return_dict['error_code']}"
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    error_log = f"{title}|trade uuid:{merged_row['uuid']}\n{body}"
                    self.logger.error(error_log)
                    # Monitoring purpose
                    self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)
                
                # raise exception according to the result of the trade
                if origin_trade_error and target_trade_error:
                    raise MyException(f"업비트 매수와 바이낸스 SHORT 모두 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=4)
                elif origin_trade_error:
                    # Check whether the trade_config's safe_reverse is set to True, if True, do the reverse trade for the target market
                    if merged_row['safe_reverse']:
                        target_ordered_qty = float(target_res['result']['volume'])
                        title = "바이낸스 SHORT 실패로 인한 업비트 역매매(매도) 거래"
                        body = ""
                        body += f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)} 의 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} SHORT 거래가 실패하여"
                        body += f"\n업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 역매매(매도, {target_ordered_qty}개) 거래를 진행합니다."
                        self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                        try:
                            target_reverse_res = self.target_exchange_adaptor.market_short(target_access_key, target_secret_key, self.symbol_converter(self.target_market_code, merged_row['base_asset']), target_ordered_qty, merged_row['ap'])
                            target_reverse_order_id = target_reverse_res['result']['uuid']
                            title = "업비트 역매매(매도) 성공"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 역매매(매도, {target_ordered_qty}개) 거래가 정상적으로 진행되었습니다."""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                            
                            # put order info to the queue
                            target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                                       "trade_uuid": merged_row['uuid'],
                                                       "symbol": self.symbol_converter(self.target_market_code, merged_row['base_asset']),
                                                       "order_id": target_reverse_order_id, "market_type": self.target_market_type}
                            self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
                        except Exception as e:
                            title = "업비트 역매매(매도) 거래 실패"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 
                            업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 역매매(매도, {target_ordered_qty}개) 거래가 실패하였습니다. {e}"""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR')
                            error_log = f"{title}|trade uuid:{merged_row['uuid']}\n{body}\n{traceback.format_exc()}"
                            self.logger.error(error_log)
                            # Monitoring purpose
                            self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)
                    raise MyException(f"바이낸스 SHORT 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=2)
                elif target_trade_error:
                    # Check whether the trade_config's safe_reverse is set to True, if True, do the reverse trade for the origin market
                    if merged_row['safe_reverse']:
                        title = "업비트 매수 실패로 인한 바이낸스 역매매(LONG) 거래"
                        body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {self.symbol_converter(self.target_market_code, merged_row['base_asset'])} 매수 거래가 실패하여 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} 역매매(LONG, {float(qty)}개) 거래를 진행합니다."""
                        self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                        try:
                            origin_reverse_res = self.origin_exchange_adaptor.market_long(origin_access_key, origin_secret_key, self.symbol_converter(self.origin_market_code, merged_row['base_asset']), qty, self.origin_market_type, True)
                            origin_reverse_order_id = str(origin_reverse_res['orderId'])
                            title = "바이낸스 역매매(LONG) 성공"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} 역매매(LONG, {float(qty)}개) 거래가 정상적으로 진행되었습니다."""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                            
                            # put order info to the queue
                            origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                                        "trade_uuid": merged_row['uuid'],
                                                        "symbol": self.symbol_converter(self.origin_market_code, merged_row['base_asset']),
                                                        "order_id": origin_reverse_order_id,
                                                        "market_type": self.origin_market_type}
                            self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)
                        except Exception as e:
                            title = "바이낸스 역매매(LONG) 거래 실패"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {self.symbol_converter(self.origin_market_code, merged_row['base_asset'])} 역매매(LONG, {float(qty)}개) 거래가 실패하였습니다. {e}"""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR')
                            error_log = f"{title}|trade uuid:{merged_row['uuid']}\n{body}\n{traceback.format_exc()}"
                            self.logger.error(error_log)
                            # Monitoring purpose
                            self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)
                    raise MyException(f"업비트 매수 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=3)

                # generate trade info dict
                trade_info_dict = {"user": merged_row['user'], "trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "base_asset": merged_row['base_asset'],
                                "target_order_id": target_order_id, "origin_order_id": origin_order_id, "target_premium_value": merged_row['low'], "dollar": merged_row['dollar'], "trade_side": trade_side,
                                "modified_input_usd": modified_input_usd, "modified_input_krw": modified_input_krw, "last_trade_history_uuid": merged_row['last_trade_history_uuid'],
                                "telegram_id": merged_row['telegram_id'], "send_times": merged_row['send_times'], "send_term": merged_row['send_term'], "usdt_conversion": merged_row['usdt_conversion'],
                                "trade_capital": merged_row['trade_capital']}
                # put trade info to the queue
                self.trade_info_dict_queue.put(trade_info_dict)
                return trade_info_dict

            else:
                raise Exception(f'market_code_combination {self.market_code_combination} not supported yet.')
        except Exception as e:
                # reflect the error to the trade to db
                conn = self.postgres_client.pool.getconn()
                curr = conn.cursor()
                sql = f"""UPDATE trade SET trade_switch = %s WHERE uuid = %s"""
                val = (-2 if trade_side == "ENTER" else 2, merged_row['uuid'])
                curr.execute(sql, val)
                conn.commit()
                self.postgres_client.pool.putconn(conn)
                raise e
            
    def short_long_trade(self, merged_row, liquidation_call=False):
        try:
            if self.market_code_combination == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                trade_side = "EXIT"
                # Check whether the trade_switch is -1 // trade_switch 0: 진입대기, -1: 탈출대기, -2: 진입에러, 1:탈출완료, 2:탈출에러, 3: 거래 진행 중
                if merged_row['trade_switch'] != -1:
                    return     
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
                
                if liquidation_call is False:
                    # Binance USD_M Long
                    origin_return_dict = {}
                    origin_trade_thread = Thread(target=self.origin_exchange_adaptor.market_long, args=(origin_access_key, origin_secret_key,
                        origin_symbol, origin_qty, self.origin_market_type, True, origin_return_dict))
                    origin_trade_thread.start()

                # Get Upbit API keys
                target_access_key, target_secret_key = self.target_exchange_adaptor.get_api_key_tup(merged_row['trade_config_uuid'], futures=False if 'SPOT' in self.target_market_type else True)
                # Upbit trade + response validation
                target_trade_error = False
                try:
                    target_res = self.target_exchange_adaptor.market_short(target_access_key, target_secret_key, target_symbol, target_qty, merged_row['ap'])
                    if liquidation_call is False:
                        origin_trade_thread.join()
                    title = "업비트 매도 성공"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {target_symbol} 매도거래({float(target_qty)}개, {round(merged_row['trade_capital'])}원)가 정상적으로 진행되었습니다."
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    target_order_id = target_res['result']['uuid']
                    
                    # put order info to the queue
                    target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.symbol_converter(self.target_market_code, merged_row['base_asset']), "order_id": target_order_id, "market_type": self.target_market_type}
                    self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
                except Exception as e:
                    target_trade_error = True
                    origin_trade_thread.join()
                    title = "업비트 매도 실패"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}({merged_row['uuid']})의 업비트 {target_symbol} 매도거래({float(target_qty)}개, {round(merged_row['trade_capital'])}원)가 실패하였습니다. {e}"
                    self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                    error_log = f"{title}|trade uuid:{merged_row['uuid']}\error:{e}\n{body}"
                    self.logger.error(error_log)
                    # Monitoring purpose
                    self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)

                if liquidation_call is False:
                    # Binance response validation
                    origin_trade_error = False
                    if origin_return_dict['error_code'] is None:
                        title = "바이낸스 LONG 성공"
                        body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {origin_symbol} LONG거래({float(origin_qty)}개, {round(merged_row['trade_capital'])}원)가 정상적으로 진행되었습니다."
                        self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                        origin_res = origin_return_dict['res']
                        origin_order_id = str(origin_res['orderId'])
                        
                        origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "symbol": self.symbol_converter(self.origin_market_code, merged_row['base_asset']), "order_id": origin_order_id, "market_type": self.origin_market_type}                
                        self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)
                    else:
                        origin_trade_error = True
                        title = "바이낸스 LONG 실패"
                        body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}({merged_row['uuid']})의 바이낸스 {origin_symbol} LONG거래({float(origin_qty)}개, {round(merged_row['trade_capital'])}원)가 실패하였습니다."
                        body += f"\n바이낸스 에러내용: {origin_return_dict['res']}, 에러코드: {origin_return_dict['error_code']}"
                        self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR', send_times=merged_row['send_times'], send_term=merged_row['send_term'])
                        error_log = f"{title}|trade uuid:{merged_row['uuid']}\nres:{origin_return_dict['res']}\n{body}"
                        self.logger.error(error_log)
                        # Monitoring purpose
                        self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)
                    
                    # raise exception according to the result of the trade
                    if origin_trade_error and target_trade_error:
                        raise MyException(f"업비트 매도와 바이낸스 LONG 모두 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=4)
                    elif origin_trade_error:
                        # Check whether the trade_config's safe_reverse is set to True, if True, do the reverse trade for the target market
                        if merged_row['safe_reverse']:
                            target_ordered_qty = float(target_res['result']['volume'])
                            title = "바이낸스 LONG 실패로 인한 업비트 역매매(매수) 거래"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {origin_symbol} LONG 거래가 실패하여 업비트 {target_symbol} 역매매 (매수, {target_ordered_qty}개) 거래를 진행합니다."""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                            try:
                                target_reverse_res = self.target_exchange_adaptor.market_long(target_access_key, target_secret_key, target_symbol, target_ordered_qty, merged_row['ap'])
                                target_reverse_order_id = target_reverse_res['result']['uuid']
                                title = "업비트 역매매(매수) 성공"
                                body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {target_symbol} 역매매(매수, {target_ordered_qty}개) 거래가 정상적으로 진행되었습니다."""
                                self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                                
                                # put order info to the queue
                                target_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                                           "trade_uuid": merged_row['uuid'],
                                                           "symbol": self.symbol_converter(self.target_market_code, merged_row['base_asset']),
                                                           "order_id": target_reverse_order_id,
                                                           "market_type": self.target_market_type}
                                self.target_exchange_adaptor.order_info_dict_queue.put(target_order_info_dict)
                            except Exception as e:
                                title = "업비트 역매매(매수) 거래 실패"
                                body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {target_symbol} 역매매 (매수, {target_ordered_qty}개) 거래가 실패하였습니다. {e}"""
                                error_log = f"{title}|trade uuid:{merged_row['uuid']}\n{body}\n{traceback.format_exc()}"
                                self.logger.error(error_log)
                                # Monitoring purpose
                                self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'MONITOR')
                        raise MyException(f"바이낸스 LONG 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=2)
                    elif target_trade_error:
                        # Check whether the trade_config's safe_reverse is set to True, if True, do the reverse trade for the origin market
                        if merged_row['safe_reverse']:
                            title = "업비트 매도 실패로 인한 바이낸스 역매매(SHORT) 거래"
                            body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 업비트 {target_symbol} 매도 거래가 실패하여 바이낸스 {origin_symbol} 역매매(SHORT, {float(origin_qty)}개) 거래를 진행합니다."""
                            self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                            try:
                                origin_reverse_res = self.origin_exchange_adaptor.market_short(origin_access_key, origin_secret_key, origin_symbol, origin_qty, self.origin_market_type, False)
                                origin_reverse_order_id = str(origin_reverse_res['orderId'])
                                title = "바이낸스 역매매(SHORT) 성공"
                                body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {origin_symbol} 역매매(SHORT, {float(origin_qty)}개) 거래가 정상적으로 진행되었습니다."""
                                self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'INFO')
                                
                                # put order info to the queue
                                origin_order_info_dict =  {"trade_config_uuid": merged_row['trade_config_uuid'],
                                                           "trade_uuid": merged_row['uuid'],
                                                           "symbol": self.symbol_converter(self.origin_market_code, merged_row['base_asset']),
                                                           "order_id": origin_reverse_order_id,
                                                           "market_type": self.origin_market_type}
                                self.origin_exchange_adaptor.order_info_dict_queue.put(origin_order_info_dict)
                            except Exception as e:
                                title = "바이낸스 역매매(SHORT) 거래 실패"
                                body = f"""거래ID: {trade_uuid_to_display_id(self.market_code_combination, merged_row['uuid'], self.logger)}의 바이낸스 {origin_symbol} 역매매(SHORT, {float(origin_qty)}) 거래가 실패하였습니다. {e}"""
                                self.acw_api.create_message_thread(merged_row['telegram_id'], title, body, 'ERROR')
                                error_log = f"{title}|trade uuid:{merged_row['uuid']}\n{body}\n{traceback.format_exc()}"
                                self.logger.error(error_log)
                                # Monitoring purpose
                                self.acw_api.create_message_thread(self.admin_id, title, error_log, 'MONITOR', send_times=1, send_term=1)
                        raise MyException(f"업비트 매도 거래가 실패하였습니다. 에러내용을 확인하시기 바랍니다.", error_code=3)
                
                
                if liquidation_call is False:
                    # generate trade info dict
                    trade_info_dict = {"user": merged_row['user'], "trade_config_uuid": merged_row['trade_config_uuid'], "trade_uuid": merged_row['uuid'], "base_asset": merged_row['base_asset'],
                                    "target_order_id": target_order_id, "origin_order_id": origin_order_id, "target_premium_value": merged_row['high'], "dollar": merged_row['dollar'], "trade_side": trade_side,
                                    "modified_input_usd": None, "modified_input_krw": None, "last_trade_history_uuid": merged_row['last_trade_history_uuid'],
                                    "telegram_id": merged_row['telegram_id'], "send_times": merged_row['send_times'], "send_term": merged_row['send_term'], "usdt_conversion": merged_row['usdt_conversion'],
                                    "trade_capital": merged_row['trade_capital']}
                    # put trade info to the queue
                    self.trade_info_dict_queue.put(trade_info_dict)
                    return trade_info_dict

            else:
                raise Exception(f'market_code_combination {self.market_code_combination} not supported yet.')
        except Exception as e:
            # reflect the error to the trade to db
            conn = self.postgres_client.pool.getconn()
            curr = conn.cursor()
            sql = f"""UPDATE trade SET trade_switch = %s WHERE uuid = %s"""
            val = (-2 if trade_side == "ENTER" else 2, merged_row['uuid'])
            curr.execute(sql, val)
            conn.commit()
            self.postgres_client.pool.putconn(conn)
            raise e
        
    def handle_trade_info(self):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        # initialize
        target_order_history = None
        origin_order_history = None
        try:
            # if self.market_code_combination == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
            trade_info_dict = self.trade_info_dict_queue.get()
            # clean numpy type. Convert it to python native type
            trade_info_dict = {k: v.item() if isinstance(v, np.generic) else v for k, v in trade_info_dict.items()}

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
            target_executed_price = target_order_history['price']
            origin_executed_price = origin_order_history['price']
            # Check whether it used usdt_conversion
            if trade_info_dict['usdt_conversion']:
                usdt_conversion = True
            else:
                usdt_conversion = False
            # Calculate the executed_premium_value
            if self.market_code_combination == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                trade_info_dict['executed_premium_value'] = (target_executed_price - origin_executed_price*Decimal(str(trade_info_dict['dollar']))) / (origin_executed_price*Decimal(str(trade_info_dict['dollar']))) * 100
                # check whether it used usdt_conversion
                if usdt_conversion:
                    trade_info_dict['executed_premium_value'] = (1+trade_info_dict['executed_premium_value']/100) * Decimal(str(trade_info_dict['dollar']))
            # Calculate the slippage_p which means the percentage of the slippage between target_premium_value and executed_premium_value
            if trade_info_dict['trade_side'] == 'ENTER':
                if not usdt_conversion:
                    trade_info_dict['slippage_p'] = round((trade_info_dict['target_premium_value'] - trade_info_dict['executed_premium_value']),2)
                else:
                    trade_info_dict['slippage_p'] = round((trade_info_dict['target_premium_value'] - trade_info_dict['executed_premium_value']) / trade_info_dict['executed_premium_value'] * 100, 2)
                # Reflect slippage to high value
                if trade_info_dict['target_premium_value'] < trade_info_dict['executed_premium_value']: # Original
                    slippage_to_add = round(trade_info_dict['executed_premium_value'] - trade_info_dict['target_premium_value'], 3) # Original
                    trade_df = get_trade_df(self.market_code_combination, trade_support=True)
                    original_high = trade_df[trade_df['uuid']==trade_info_dict['trade_uuid']]['high'].values[0]
                    new_high_to_apply = original_high + Decimal(str(slippage_to_add))
                    # Send a message to notify the change
                    title = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)} 탈출프리미엄 조정"
                    body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}의 설정된 진입프리미엄값과 실제 체결된 진입프리미엄 값이 {slippage_to_add}만큼 차이나므로, 탈출프리미엄이 {new_high_to_apply}로 변경되었습니다."
                    full_body = title + '\n' + body
                    self.acw_api.create_message_thread(trade_info_dict['telegram_id'], title, full_body, 'INFO', send_times=trade_info_dict['send_times'], send_term=trade_info_dict['send_term'])
                    # Update the high value
                    curr.execute(f"UPDATE trade SET high={new_high_to_apply} WHERE uuid='{trade_info_dict['trade_uuid']}'")
                    conn.commit()                    
            else:
                if not usdt_conversion:
                    trade_info_dict['slippage_p'] = (trade_info_dict['executed_premium_value'] - trade_info_dict['target_premium_value'])
                else:
                    trade_info_dict['slippage_p'] = (trade_info_dict['executed_premium_value'] - trade_info_dict['target_premium_value']) / trade_info_dict['target_premium_value'] * 100
                
            if trade_info_dict['slippage_p'] < 0:
                slippage_str = f"슬리피지: {(round(trade_info_dict['slippage_p'], 3))}%p"
            else:
                slippage_str = f"슬리피지 없음"

            # Insert trade info to the database and return the generated uuid
            sql = """INSERT INTO trade_history (trade_config_uuid, trade_uuid, registered_datetime, trade_side, base_asset, target_order_id, origin_order_id, 
            target_premium_value, executed_premium_value, slippage_p, dollar, remark) 
            VALUES (%(trade_config_uuid)s, %(trade_uuid)s, %(registered_datetime)s, %(trade_side)s, %(base_asset)s, 
            %(target_order_id)s, %(origin_order_id)s, %(target_premium_value)s, %(executed_premium_value)s, %(slippage_p)s, %(dollar)s, %(remark)s) RETURNING uuid"""
            curr.execute(sql, trade_info_dict)
            generated_uuid = curr.fetchone()['uuid']
            trade_info_dict['uuid'] = generated_uuid
            # UPDATE the trade_switch and last_trade_history_uuid to 'trade' table
            # trade_switch 0: 진입대기, -1: 탈출대기, -2: 진입에러, 1:탈출완료, 2:탈출에러, 3: 거래 진행 중
            curr.execute(f"UPDATE trade SET trade_switch={-1 if trade_info_dict['trade_side']=='ENTER' else 1}, last_trade_history_uuid='{generated_uuid}' WHERE uuid='{trade_info_dict['trade_uuid']}'")
            conn.commit()
            # else:
            #     raise Exception(f'market_code_combination {self.market_code_combination} not supported yet.')
            

            if usdt_conversion:
                premium_unit = "KRW"
                # point_str = ''
            else:
                premium_unit = "%"
                # point_str = 'p'

            # Send message to the user
            if trade_info_dict['trade_side'] == 'ENTER':
                title = "진입거래 성공"
                body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}의 거래({round(trade_info_dict['trade_capital'])}원)가 정상적으로 진행되었습니다."
                body += f"\n진입프리미엄: {round(trade_info_dict['target_premium_value'],2)}{premium_unit}\n실제진입프리미엄: {round(trade_info_dict['executed_premium_value'],2)}{premium_unit}\n{slippage_str}"
                full_body = title + '\n' + body
            else:
                # Add 1 if the trade has the repeat_trade configuration connected
                trade_uuid = trade_info_dict['trade_uuid']
                # fetch repeat_trade whose trade_uuid is trade_uuid
                curr.execute(f"SELECT * FROM repeat_trade WHERE trade_uuid='{trade_uuid}'")
                repeat_trade_series = curr.fetchone()
                if repeat_trade_series is not None:
                    # Add 1 to the auto_repeat_num
                    auto_repeat_num = repeat_trade_series['auto_repeat_num'] + 1
                    # Update the auto_repeat_num
                    curr.execute(f"UPDATE repeat_trade SET auto_repeat_num={auto_repeat_num} WHERE trade_uuid='{trade_uuid}'")
                    conn.commit()
                
                title = "탈출거래 성공"
                body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}의 거래({round(trade_info_dict['trade_capital'])}원)가 정상적으로 진행되었습니다."
                body += f"\n탈출프리미엄: {round(trade_info_dict['target_premium_value'],2)}{premium_unit}\n실제탈출프리미엄: {round(trade_info_dict['executed_premium_value'],2)}{premium_unit}\n{slippage_str}"
                full_body = title + '\n' + body
            self.acw_api.create_message_thread(trade_info_dict['telegram_id'], title, full_body, 'INFO', send_times=trade_info_dict['send_times'], send_term=trade_info_dict['send_term'])
            self.postgres_client.pool.putconn(conn)
            
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
                
    def handle_margin_liquidation_call_trade(self):
        try:
            # Load info_dict
            fetched_info_dict = self.redis.get_data("info_dict")
            if fetched_info_dict is None:
                raise Exception("info_dict is None.")
            fetched_info_dict = pickle.loads(fetched_info_dict)
            
            # Load convert_rate_dict
            fetched_convert_rate_dict = self.redis.hgetall_dict("convert_rate_dict")
            # Convert all the values to float
            fetched_convert_rate_dict = {k.decode('utf-8'): float(v) for k, v in fetched_convert_rate_dict.items()}
    
            margin_liquidation_call_trade_dict = self.margin_liquidation_call_trade_queue.get()
            trade_type = margin_liquidation_call_trade_dict.get('trade_type')
            trade_df = margin_liquidation_call_trade_dict.get('trade_df')
            order_type = margin_liquidation_call_trade_dict.get('order_type')
                        
            target_market_code, origin_market_code = self.market_code_combination.split(':')
            premium_df = get_premium_df(self.redis, fetched_info_dict, fetched_convert_rate_dict, target_market_code, origin_market_code, self.logger)
            merged_df = trade_df.merge(premium_df, on='base_asset')
            merged_df['SL_premium_value'] = merged_df.apply(lambda x: x['SL_premium'] if x['usdt_conversion'] == False else (1+x['SL_premium']/100)*x['dollar'], axis=1)
            merged_df['LS_premium_value'] = merged_df.apply(lambda x: x['LS_premium'] if x['usdt_conversion'] == False else (1+x['LS_premium']/100)*x['dollar'], axis=1)
            
            trade_row = merged_df.iloc[0]
            
            if trade_type == "short_long_trade":
                self.short_long_trade(trade_row, liquidation_call=True if order_type=='liquidation' else False)
            elif trade_type == "long_short_trade":
                self.long_short_trade(trade_row, liquidation_call=True if order_type=='liquidation' else False)
            else:
                raise Exception(f"trade_type {trade_type} not supported.")
        except Exception as e:
            self.logger.error(f"handle_margin_liquidation_call_trade|{e}")
            self.logger.error(traceback.format_exc())
                
    def handle_margin_liquidation_call_trade_queue_loop(self):
        self.logger.info(f"handle_margin_liquidation_call_trade_queue_loop started.")
        while True:
            try:
                self.handle_margin_liquidation_call_trade()
            except Exception as e:
                self.logger.error(f"handle_margin_liquidation_call_trade_queue_loop|{e}")
                self.logger.error(traceback.format_exc())
                time.sleep(3)
        
    def generate_pnl_history(self, trade_info_dict):
        self.load_order_history()
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
            
            # Check the qty between the ENTER and EXIT for target market with error rate of 0.5%
            enter_target_order_qty = enter_target_order_history_series['qty'].values[0]
            exit_target_order_qty = exit_target_order_history_series['qty'].values[0]
            target_pnl_qty_error = False
            if abs(enter_target_order_qty - exit_target_order_qty) > enter_target_order_qty * Decimal(str(0.005)):
                target_pnl_qty_error = True
                # log
                title = "수량오류"
                body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}({trade_info_dict['trade_uuid']})의 {self.target_market_code}의 진입수량과 탈출수량의 차이가 0.5% 이상입니다. 진입수량: {enter_target_order_qty}, 탈출수량: {exit_target_order_qty}"
                full_body = title + '\n' + body
                self.logger.error(f"generate_pnl_history|{full_body}")
                # send monitor message to the admin
                self.acw_api.create_message_thread(self.admin_id, title, full_body, send_times=1, send_term=1)
            enter_origin_order_qty = enter_origin_order_history_series['qty'].values[0]
            exit_origin_order_qty = exit_origin_order_history_series['qty'].values[0]
            origin_pnl_qty_error = False
            if abs(enter_origin_order_qty - exit_origin_order_qty) > enter_origin_order_qty * Decimal(str(0.005)):
                origin_pnl_qty_error = True
                # log
                title = "수량오류"
                body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}({trade_info_dict['trade_uuid']})의 {self.origin_market_code}의 진입수량과 탈출수량의 차이가 0.5% 이상입니다. 진입수량: {enter_origin_order_qty}, 탈출수량: {exit_origin_order_qty}"
                full_body = title + '\n' + body
                self.logger.error(f"generate_pnl_history|{full_body}")
                # send monitor message to the admin
                self.acw_api.create_message_thread(self.admin_id, title, full_body, send_times=1, send_term=1)
            
            # Calculate the pnl
            target_total_fee = enter_target_order_history_series['fee'].values[0] + exit_target_order_history_series['fee'].values[0]
            origin_total_fee = enter_origin_order_history_series['fee'].values[0] + exit_origin_order_history_series['fee'].values[0]
            
            if target_pnl_qty_error or origin_pnl_qty_error:
                # Insert pnl history to the database
                pnl_history = {}
                pnl_history['enter_trade_history_uuid'] = enter_trade_history_series['uuid'].values[0]
                pnl_history['exit_trade_history_uuid'] = trade_info_dict['uuid']
                pnl_history['realized_premium_gap_p'] = 0
                pnl_history['target_currency'] = enter_target_order_history_series['quote_asset'].values[0]
                pnl_history['target_pnl'] = 0
                pnl_history['target_total_fee'] = target_total_fee
                pnl_history['target_pnl_after_fee'] = 0
                pnl_history['origin_currency'] = enter_origin_order_history_series['quote_asset'].values[0]
                pnl_history['origin_pnl'] = 0
                pnl_history['origin_total_fee'] = origin_total_fee
                pnl_history['origin_pnl_after_fee'] = 0
                pnl_history['total_currency'] = 0
                pnl_history['total_pnl'] = 0
                pnl_history['total_pnl_after_fee'] = 0
                pnl_history['remark'] = "진입탈출 수량 불일치"
                # Insert pnl history to the database
                sql = """INSERT INTO pnl_history (enter_trade_history_uuid, exit_trade_history_uuid, realized_premium_gap_p, target_currency, target_pnl, target_total_fee, target_pnl_after_fee, origin_currency, origin_pnl, origin_total_fee, origin_pnl_after_fee, total_currency, total_pnl, total_pnl_after_fee, remark) 
                VALUES (%(enter_trade_history_uuid)s, %(exit_trade_history_uuid)s, %(realized_premium_gap_p)s, %(target_currency)s, %(target_pnl)s, %(target_total_fee)s, %(target_pnl_after_fee)s, %(origin_currency)s, %(origin_pnl)s, %(origin_total_fee)s, %(origin_pnl_after_fee)s, %(total_currency)s, %(total_pnl)s, %(total_pnl_after_fee)s, %(remark)s)"""
                curr.execute(sql, pnl_history)
                conn.commit()
                # send message to the user
                title = "수량오류"
                body = f"거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)}({trade_info_dict['trade_uuid']})의 진입수량과 탈출수량의 차이가 0.5% 이상입니다. 수량오류로 인해 PnL계산이 불가합니다. 관리자에게 문의하시기 바랍니다."
                full_body = title + '\n' + body
                self.acw_api.create_message_thread(enter_trade_history_series['telegram_id'].values[0], title, full_body, 'ERROR', send_times=enter_trade_history_series['send_times'].values[0], send_term=enter_trade_history_series['send_term'].values[0])
            else:
                # BUY or SELL
                enter_target_order_history_side = enter_target_order_history_series['side'].values[0]
                if enter_target_order_history_side == "BUY":
                    target_pnl = ((exit_target_order_history_series['price'].values[0] - enter_target_order_history_series['price'].values[0]) 
                                * enter_target_order_history_series['qty'].values[0])
                else:
                    target_pnl = ((enter_target_order_history_series['price'].values[0] - exit_target_order_history_series['price'].values[0]) 
                                * enter_target_order_history_series['qty'].values[0])
                    
                enter_origin_order_history_side = enter_origin_order_history_series['side'].values[0]
                if enter_origin_order_history_side == "BUY":
                    origin_pnl = ((exit_origin_order_history_series['price'].values[0] - enter_origin_order_history_series['price'].values[0]) 
                                * enter_origin_order_history_series['qty'].values[0])
                else:
                    origin_pnl = ((enter_origin_order_history_series['price'].values[0] - exit_origin_order_history_series['price'].values[0]) 
                                * enter_origin_order_history_series['qty'].values[0])
                
                if self.market_code_combination == "UPBIT_SPOT/KRW:BINANCE_USD_M/USDT":
                    # Calculate realized_premium_gap_p
                    enter_trade_executed_premium_value = enter_trade_history_series['executed_premium_value'].values[0]
                    exit_trade_executed_premium_value = trade_info_dict['executed_premium_value']
                    realized_premium_gap_p = exit_trade_executed_premium_value - enter_trade_executed_premium_value
                    # Check whether it used usdt_conversion value
                    if enter_trade_history_series['target_premium_value'].values[0] >= 800:
                        realized_premium_gap_p = (exit_trade_executed_premium_value - enter_trade_executed_premium_value)/enter_trade_executed_premium_value*100
                    
                    total_currency = 'USDT'
                    # total_pnl = target_pnl + origin_pnl * Decimal(str(trade_info_dict['dollar']))
                    total_pnl = target_pnl/Decimal(str(trade_info_dict['dollar'])) + origin_pnl
                    # total_fee = target_total_fee + origin_total_fee * Decimal(str(trade_info_dict['dollar']))
                    total_fee = target_total_fee/Decimal(str(trade_info_dict['dollar'])) + origin_total_fee
                    total_pnl_after_fee = total_pnl - total_fee
                else:
                    raise Exception(f'market_code_combination {self.market_code_combination} not supported yet.')
                
                pnl_history = {}
                target_currency = enter_target_order_history_series['quote_asset'].values[0]
                origin_currency = enter_origin_order_history_series['quote_asset'].values[0]
                
                pnl_history['trade_config_uuid'] = enter_trade_history_series['trade_config_uuid'].values[0]
                pnl_history['trade_uuid'] = trade_info_dict['trade_uuid']
                pnl_history['registered_datetime'] = datetime.datetime.utcnow()
                pnl_history['market_code_combination'] = self.market_code_combination
                pnl_history['enter_trade_history_uuid'] = enter_trade_history_series['uuid'].values[0]
                pnl_history['exit_trade_history_uuid'] = trade_info_dict['uuid']
                pnl_history['realized_premium_gap_p'] = realized_premium_gap_p
                pnl_history['target_currency'] = target_currency
                pnl_history['target_pnl'] = target_pnl
                pnl_history['target_total_fee'] = target_total_fee
                pnl_history['target_pnl_after_fee'] = target_pnl - target_total_fee
                pnl_history['origin_currency'] = origin_currency
                pnl_history['origin_pnl'] = origin_pnl
                pnl_history['origin_total_fee'] = origin_total_fee
                pnl_history['origin_pnl_after_fee'] = origin_pnl - origin_total_fee
                pnl_history['total_currency'] = total_currency
                pnl_history['total_pnl'] = total_pnl
                pnl_history['total_pnl_after_fee'] = total_pnl_after_fee
                pnl_history['total_pnl_after_fee_kimp'] = None # build later
                pnl_history['remark'] = None
                
                # Insert pnl history to the database
                sql = """INSERT INTO pnl_history (trade_config_uuid, trade_uuid, registered_datetime, market_code_combination, enter_trade_history_uuid, exit_trade_history_uuid, realized_premium_gap_p, target_currency, 
                target_pnl, target_total_fee, target_pnl_after_fee, origin_currency, origin_pnl, origin_total_fee, 
                origin_pnl_after_fee, total_currency, total_pnl, total_pnl_after_fee, total_pnl_after_fee_kimp, remark)
                VALUES (%(trade_config_uuid)s, %(trade_uuid)s, %(registered_datetime)s, %(market_code_combination)s, %(enter_trade_history_uuid)s, %(exit_trade_history_uuid)s, %(realized_premium_gap_p)s, %(target_currency)s, %(target_pnl)s, 
                %(target_total_fee)s, %(target_pnl_after_fee)s, %(origin_currency)s, %(origin_pnl)s, %(origin_total_fee)s, %(origin_pnl_after_fee)s, %(total_currency)s, %(total_pnl)s, %(total_pnl_after_fee)s, %(total_pnl_after_fee_kimp)s, %(remark)s)"""
                curr.execute(sql, pnl_history)
                conn.commit()
                
                # send message to the user
                if target_currency == "KRW":
                    target_round_n = 0
                else:
                    target_round_n = 1
                if origin_currency == "KRW":
                    origin_round_n = 0
                else:
                    origin_round_n = 1
                if total_currency == "KRW":
                    total_round_n = 0
                else:
                    total_round_n = 1
                title = f"{self.market_code_combination}\n거래ID: {trade_uuid_to_display_id(self.market_code_combination, trade_info_dict['trade_uuid'], self.logger)} 탈출 손익"
                body = f"{self.target_market_code} 진입탈출 수수료: {round(target_total_fee, target_round_n)}{target_currency}"
                body += f"\n{self.origin_market_code} 진입탈출 수수료: {round(origin_total_fee, origin_round_n)}{origin_currency}"
                body += f"\n양측 총 수수료: {round(total_fee, total_round_n)}{total_currency}"
                body += f"\n합산 손익: {round(total_pnl, total_round_n)}{total_currency}"
                body += f"\n수수료 적용 후 합산 손익: {round(total_pnl_after_fee, total_round_n)}{total_currency}"
                body += f"\n수수료, 김프 적용 후 합산 손익: {round(total_pnl_after_fee, total_round_n)}{total_currency}"
                full_body = title + '\n' + body
                self.acw_api.create_message_thread(trade_info_dict['telegram_id'], title, full_body, 'INFO', send_times=trade_info_dict['send_times'], send_term=trade_info_dict['send_term'])
                # apply to the user deposit if a user had profit
                if total_pnl_after_fee > 0:
                    self.acw_api.get_referral_commission(trade_info_dict['user'], trade_info_dict['trade_config_uuid'], round(total_pnl_after_fee, total_round_n), self.target_market_code, self.origin_market_code, apply_to_deposit=True)
            self.postgres_client.pool.putconn(conn)
        except Exception as e:
            self.postgres_client.pool.putconn(conn)
            self.logger.error(f"generate_pnl_history|{e}")
            self.logger.error(traceback.format_exc())
            title = "PnL 계산 오류"
            body = f"거래UUID: {trade_info_dict['trade_uuid']}의 PnL 계산 중 오류가 발생하였습니다. 관리자에게 문의하시기 바랍니다."
            full_body = title + '\n' + body
            self.acw_api.create_message_thread(trade_info_dict['telegram_id'], title, full_body, 'ERROR', send_times=1, send_term=1)
            # send message to the admin
            self.acw_api.create_message_thread(self.admin_id, title, full_body, 'MONITOR', send_times=1, send_term=1)
            raise e