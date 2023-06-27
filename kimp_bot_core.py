import pandas as pd
from price_websocket import dict_convert, update_dollar, price_websocket
from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from loggers.logger import KimpBotLogger
from etc.register_msg import register
from etc.redis_connector.redis_connector import InitRedis
from etc.db_handler.create_schema_tables import InitDBClient
import _pickle as pickle
from threading import Thread
import time
import os
import traceback

current_file_dir = os.path.realpath(__file__)
current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
logging_dir = f"{current_folder_dir}/loggers/logs/"

class InitKimpCore:
    if not os.path.exists(logging_dir):
        os.mkdir(logging_dir)
    kimp_bot_core_logger = KimpBotLogger("kimp_bot_core", logging_dir).logger
    price_websocket_logger = KimpBotLogger("price_websocket", logging_dir).logger
    update_dollar_logger = KimpBotLogger("update_dollar", logging_dir).logger

    def __init__(self, proc_n, node, admin_id, okx_demo_trading='0'):
        # Inital value setting
        self.origin = node
        self.admin_id = admin_id
        self.proc_n = proc_n
        self.monitor_websocket_switch = True
        self.exclude_outliers = True
        self.monitor_bot_token = None
        self.monitor_api_url = None
        # For redis connection
        self.redis_client = InitRedis()

        self.kimp_bot_core_logger.info(f"InitKimpCore|InitKimpCore initiated with proc_n={proc_n}")

        self.okx_adaptor = InitOkxAdaptor(demo_trading=okx_demo_trading)
        self.upbit_adaptor = InitUpbitAdaptor()

        self.shared_listed_symbol_dict = self.fetch_both_listed_symbol_dict()
        self.both_listed_okx_symbols = self.shared_listed_symbol_dict['both_listed_okx_symbols']
        self.both_listed_upbit_symbols = self.shared_listed_symbol_dict['both_listed_upbit_symbols']

        self.price_websocket_thread = Thread(target=price_websocket.okx_upbit_websocket,
                                                args=(self.both_listed_okx_symbols,
                                                        self.both_listed_upbit_symbols,
                                                        self.proc_n,
                                                        self.price_websocket_logger), daemon=True)
        self.price_websocket_thread.start()

        self.update_dollar_return_dict = {}
        self.update_dollar_thread = Thread(target=update_dollar.fetch_dollar_loop, args=(self.update_dollar_return_dict, self.update_dollar_logger), daemon=True)
        self.update_dollar_thread.start()

        time.sleep(2)

        self.OKX_BOOKTICKER_PROC_LIST = price_websocket.OKX_TICKER_PROC_LIST
        self.UPBIT_TICKER_PROC_LIST = price_websocket.UPBIT_TICKER_PROC_LIST
        self.UPBIT_ORDERBOOK_PROC_LIST = price_websocket.UPBIT_ORDERBOOK_PROC_LIST

        self.OKX_BOOKTICKER_DICT = price_websocket.OKX_TICKER_DICT
        self.UPBIT_TICKER_DICT = price_websocket.UPBIT_TICKER_DICT
        self.UPBIT_ORDERBOOK_DICT = price_websocket.UPBIT_ORDERBOOK_DICT

    def fetch_both_listed_symbol_dict(self):
        okx_all_tickers = pd.DataFrame(self.okx_adaptor.pub_okx_client.MarketAPI.get_tickers('SWAP')['data'])
        okx_all_tickers = okx_all_tickers[okx_all_tickers['instId'].str.endswith('-USDT-SWAP')]
        okx_all_tickers.loc[:, ['last', 'volCcy24h', 'vol24h']] = okx_all_tickers.loc[:, ['last', 'volCcy24h', 'vol24h']].astype(float)
        okx_all_tickers['24h_turnover'] = okx_all_tickers['volCcy24h'] * okx_all_tickers['last']
        okx_all_tickers = okx_all_tickers.sort_values('24h_turnover', ascending=False).reset_index(drop=True)[['instId','last','24h_turnover']]
        okx_all_tickers['symbol'] = okx_all_tickers['instId'].apply(lambda x: x.split('-')[0])
        upbit_ticker_df = self.upbit_adaptor.upbit_all_ticker(None, None)
        upbit_ticker_df['symbol'] = upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
        both_listed_symbol_df = pd.merge(okx_all_tickers, upbit_ticker_df, on='symbol', how='inner')
        both_listed_okx_symbols = both_listed_symbol_df.sort_values('24h_turnover', ascending=False)['instId'].tolist()
        both_listed_upbit_symbols = both_listed_symbol_df.sort_values('acc_trade_price_24h', ascending=False)['market'].tolist()
        return {'both_listed_okx_symbols': both_listed_okx_symbols, 'both_listed_upbit_symbols': both_listed_upbit_symbols}

    def get_dollar_dict(self):
        return self.update_dollar_return_dict

    def get_both_listed_okx_symbols(self):
        return self.both_listed_okx_symbols
    
    def get_both_listed_upbit_symbols(self):
        return self.both_listed_upbit_symbols

    def set_monitor_bot_token(self, bot_token):
        self.monitor_bot_token = bot_token

    def set_monitor_api_url(self, api_url):
        self.monitor_api_url = api_url

    def start_monitor_update_to_redis(self):
        if self.monitor_bot_token is None or self.monitor_api_url is None:
            self.kimp_bot_core_logger.error(f"start_monitor_update_to_redis|monitor setting hasn't configured.")
            status_body = f"self.monitor_bot_token: {self.monitor_bot_token}, self.monitor_api_url: {self.monitor_api_url}"
            self.kimp_bot_core_logger.error(status_body)
        else:
            self.start_monitor_update_kimp_to_redis()
            self.start_monitor_update_wa_kimp_to_redis()
            self.start_monitor_update_dollar_to_redis()

    # def set_local_db_client(self, host, port, user, passwd, database, master_node=True):
    #     self.kimp_bot_core_logger.info("set_local_db_client|self.local_db_client has been set.")
    #     self.local_db_client = InitDBClient(host, port, user, passwd, database, self.create_schema_tables_logger)
    #     self.local_db_client.create_all_table(master_node=master_node)

    # def set_remote_db_client(self, host, port, user, passwd, database):
    #     self.kimp_bot_core_logger.info("set_remote_db_client|self.remote_db_client has been set.")
    #     self.remote_db_client = InitDBClient(host, port, user, passwd, database, self.create_schema_tables_logger)

    def get_kimp_df(self):
        return dict_convert.get_kimp_df(
            self.OKX_BOOKTICKER_DICT,
            self.UPBIT_TICKER_DICT,
            self.UPBIT_ORDERBOOK_DICT,
            float(self.update_dollar_return_dict['price']))

    def get_wa_kimp_dict(self, exclude_outliers=True, kimp_side='last'):
        if exclude_outliers == True:
            kimp_df = self.get_kimp_df().sort_values('tp_kimp').iloc[1:-1,:]
        else:
            kimp_df = self.get_kimp_df()
        if kimp_side == 'last':
            wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['tp_kimp']).sum()
            wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['tp_usdt']).sum()
            wa_kimp_dict = {
                "wa_kimp": wa_kimp,
                "wa_usdt": wa_usdt
            }
        elif kimp_side == 'enter':
            wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['enter_kimp']).sum()
            wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['enter_usdt']).sum()
            wa_kimp_dict = {
                "wa_kimp": wa_kimp,
                "wa_usdt": wa_usdt
            }
        else:
            wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['exit_kimp']).sum()
            wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['exit_usdt']).sum()
            wa_kimp_dict = {
                "wa_kimp": wa_kimp,
                "wa_usdt": wa_usdt
            }
        return wa_kimp_dict

    def websocket_proc_status(self, print_status=None):
        integrity_flag, whole_status_str = price_websocket.check_proc_status(
            self.OKX_BOOKTICKER_PROC_LIST,
            self.UPBIT_TICKER_PROC_LIST,
            self.UPBIT_ORDERBOOK_PROC_LIST,
            self.price_websocket_logger,
            print_status=print_status
        )
        return integrity_flag, whole_status_str
    
    def dollar_update_thread_status(self):
        dollar_update_alive_flag = self.update_dollar_thread.is_alive()
        if dollar_update_alive_flag is True:
            dollar_update_status_str = "dollar_update_thread is alive"
            integrity_flag = True
        else:
            dollar_update_status_str = "dollar_update_thread is dead"
            integrity_flag = False
        return integrity_flag, dollar_update_status_str
    
    def reinitiate_dollar_update_thread(self):
        before_reinitiate = "Before reinit:  " + self.dollar_update_thread_status()[1]
        self.update_dollar_thread = Thread(target=update_dollar.fetch_dollar_loop, args=(self.update_dollar_return_dict, self.update_dollar_logger), daemon=True)
        self.update_dollar_thread.start()
        time.sleep(1)
        after_reinitiate = "After reinit: " + self.dollar_update_thread_status()[1]
        self.kimp_bot_core_logger.info(f"reinitiate_dollar_update_thread|{before_reinitiate} -> {after_reinitiate}")
        self.kimp_bot_core_logger.info("reinitiate_dollar_update_thread|dollar_update_thread has been reinitiated.")
        return before_reinitiate + "\n" + after_reinitiate

    def terminate_websocket_procs(self):
        price_websocket.terminate_websocket_proc(
            self.OKX_BOOKTICKER_PROC_LIST,
            self.UPBIT_TICKER_PROC_LIST,
            self.UPBIT_ORDERBOOK_PROC_LIST,
            self.price_websocket_logger
            )

    def monitor_websocket(self, loop_secs=2.5):
        if self.monitor_bot_token is None or self.monitor_api_url is None:
            self.kimp_bot_core_logger.error(f"monitor_websocket|monitor setting hasn't configured.")
            return
        self.kimp_bot_core_logger.info(f"monitor_websocket|monitor_websocket_procs started.")
        def monitor_loop(monitor_bot_token=self.monitor_bot_token, monitor_api_url=self.monitor_api_url):
            input_type = "monitor"
            title1 = "websocket process stopped!"
            title2 = "websocket status after restart"
            while self.monitor_websocket_switch:
                try:
                    integrity_flag, whole_status_str = self.websocket_proc_status(print_status=False)
                    if integrity_flag == False:
                        self.kimp_bot_core_logger.error(f"websocket integrity has broken. proc_stats: {whole_status_str}")
                        register(monitor_bot_token, monitor_api_url, self.admin_id, self.origin, input_type, title1, content=whole_status_str, code=None, sent_switch=0, send_counts=1, remark=None)
                        # print(f"Before re_init by monitor_loop")
                        self.terminate_websocket_procs()
                        self.__init__(self.proc_n, self.origin, self.admin_id)
                        # print(f"After re_init by monitor_loop")
                        integrity_flag, whole_status_str = self.websocket_proc_status(print_status=False)
                        status_after_restart = f"monitor_websocket|After re_init by monitor_loop. proc_stats: {whole_status_str}"
                        self.kimp_bot_core_logger.info(status_after_restart)
                        register(monitor_bot_token, monitor_api_url, self.admin_id, self.origin, input_type, title2, content=status_after_restart, code=None, sent_switch=0, send_counts=1, remark=None)
                except Exception as e:
                        self.kimp_bot_core_logger.critical(f"monitor_websocket|monitor_websocket_procs 에러!|{traceback.format_exc()}")
                        register(self.monitor_bot_token, self.monitor_api_url, self.admin_id, self.origin, input_type, 'monitor_websocket_procs 에러!', content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(loop_secs)
        self.monitor_websocket_thread = Thread(target=monitor_loop, daemon=True)
        self.monitor_websocket_thread.start()

    def stop_monitor_websocket(self):
        self.monitor_websocket_switch = False
        # print(f"monitor_websocket_switch has been set to False.")
        self.kimp_bot_core_logger.info(f"stop_monitor_websocket|monitor_websocket_switch has been set to False.")
        time.sleep(3)
        # print(f"self.monitor_websocket_thread.is_alive: {self.monitor_websocket_thread.is_alive()}")
        self.kimp_bot_core_logger.info(f"stop_monitor_websocket|self.monitor_websocket_thread.is_alive: {self.monitor_websocket_thread.is_alive()}")

    def start_monitor_update_kimp_to_redis(self, pickled_kimp_df_name="pickled_kp", update_loop_secs=0.1, monitor_loop_secs=2.5):
        if self.monitor_bot_token is None or self.monitor_api_url is None:
            self.kimp_bot_core_logger.error(f"start_monitor_update_kimp_to_redis|monitor setting hasn't configured.")
            return
        def loop_monitor_update_kimp_to_redis():
            self.kimp_bot_core_logger.info(f"start_monitor_update_kimp_to_redis|start_monitor_update_kimp_to_redis started.")
            input_type = "monitor"
            title = "update_kimp_to_redis_thread stopped!"

            def update_kimp_to_redis():
                self.kimp_bot_core_logger.info(f"update_kimp_to_redis|update_kimp_to_redis started.")
                while True:
                    self.redis_client.set_data(pickled_kimp_df_name, pickle.dumps(self.get_kimp_df()))
                    time.sleep(update_loop_secs)
            self.update_kimp_to_redis_thread = Thread(target=update_kimp_to_redis, daemon=True)
            self.update_kimp_to_redis_thread.start()

            while True:
                if not self.update_kimp_to_redis_thread.is_alive():
                    self.kimp_bot_core_logger.error(f"loop_monitor_update_kimp_to_redis|update_kimp_to_redis_thread stopped!")
                    register(self.monitor_bot_token, self.monitor_api_url, self.admin_id, self.origin, input_type, title, "restarting update_kimp_to_redis_thread..")
                    self.update_kimp_to_redis_thread = Thread(target=update_kimp_to_redis, daemon=True)
                    self.update_kimp_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_kimp_to_redis_thread = Thread(target=loop_monitor_update_kimp_to_redis, daemon=True)
        loop_monitor_update_kimp_to_redis_thread.start()

    def start_monitor_update_wa_kimp_to_redis(self, pickled_wa_kimp_dict_name="pickled_wa_kp", update_loop_secs=0.15, monitor_loop_secs=2.5):
        if self.monitor_bot_token is None or self.monitor_api_url is None:
            self.kimp_bot_core_logger.error(f"start_monitor_update_wa_kimp_to_redis|monitor setting hasn't configured.")
            return
        def loop_monitor_update_wa_kimp_to_redis():
            self.kimp_bot_core_logger.info(f"start_monitor_update_wa_kimp_to_redis|start_monitor_update_wa_kimp_to_redis started.")
            input_type = "monitor"
            title = "update_wa_kimp_to_redis_thread stopped!"

            def update_wa_kimp_to_redis():
                self.kimp_bot_core_logger.info(f"update_wa_kimp_to_redis|update_wa_kimp_to_redis started.")
                while True:
                    self.redis_client.set_data(pickled_wa_kimp_dict_name, pickle.dumps(self.get_wa_kimp_dict(exclude_outliers=self.exclude_outliers)))
                    time.sleep(update_loop_secs)
            self.update_wa_kimp_to_redis_thread = Thread(target=update_wa_kimp_to_redis, daemon=True)
            self.update_wa_kimp_to_redis_thread.start()
        
            while True:
                if not self.update_wa_kimp_to_redis_thread.is_alive():
                    self.kimp_bot_core_logger.error(f"loop_monitor_update_wa_kimp_to_redis|update_wa_kimp_to_redis_thread stopped!")
                    register(self.monitor_bot_token, self.monitor_api_url, self.admin_id, self.origin, input_type, title, "restarting update_wa_kimp_to_redis_thread..")
                    self.update_wa_kimp_to_redis_thread = Thread(target=update_wa_kimp_to_redis, daemon=True)
                    self.update_wa_kimp_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_wa_kimp_to_redis_thread = Thread(target=loop_monitor_update_wa_kimp_to_redis, daemon=True)
        loop_monitor_update_wa_kimp_to_redis_thread.start()

    def start_monitor_update_dollar_to_redis(self, pickled_dollar_dict_name="pickled_dollar_dict", update_loop_secs=1, monitor_loop_secs=2.5):
        if self.monitor_bot_token is None or self.monitor_api_url is None:
            self.kimp_bot_core_logger.error(f"start_monitor_update_dollar_to_redis|monitor setting hasn't configured.")
            return
        def loop_monitor_update_dollar_to_redis():
            self.kimp_bot_core_logger.info(f"start_monitor_update_dollar_to_redis|start_monitor_update_dollar_to_redis started.")
            input_type = "monitor"
            title = "update_dollar_to_redis stopped!"

            def update_dollar_to_redis():
                self.kimp_bot_core_logger.info(f"update_dollar_to_redis|update_dollar_to_redis started.")
                while True:
                    self.redis_client.set_data(pickled_dollar_dict_name, pickle.dumps(self.update_dollar_return_dict))
                    time.sleep(update_loop_secs)
            self.update_dollar_to_redis_thread = Thread(target=update_dollar_to_redis, daemon=True)
            self.update_dollar_to_redis_thread.start()

            while True:
                if not self.update_dollar_to_redis_thread.is_alive():
                    self.kimp_bot_core_logger.error(f"loop_monitor_update_dollar_to_redis|update_dollar_to_redis_thread stopped!")
                    register(self.monitor_bot_token, self.monitor_api_url, self.admin_id, self.origin, input_type, title, "restarting update_dollar_to_redis_thread..")
                    self.update_dollar_to_redis_thread = Thread(target=update_dollar_to_redis, daemon=True)
                    self.update_dollar_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_dollar_to_redis_thread = Thread(target=loop_monitor_update_dollar_to_redis, daemon=True)
        loop_monitor_update_dollar_to_redis_thread.start()


