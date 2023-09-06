import pandas as pd
# from price_websocket import dict_convert, update_dollar, price_websocket
from exchange_websocket import update_dollar
from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_websocket.binance_websocket import BinanceWebsocket, BinanceUSDMWebsocket, BinanceCOINMWebsocket
from exchange_websocket.upbit_websocket import UpbitWebsocket
from loggers.logger import KimpBotLogger
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

class InitCore:
    def __init__(self, logging_dir, proc_n, node, admin_id, register_monitor_msg, exchange_api_key_dict, enabled_markets_dict):
        # Inital value setting
        self.kimp_bot_core_logger = KimpBotLogger("kimp_bot_core", logging_dir).logger
        self.price_websocket_logger = KimpBotLogger("price_websocket", logging_dir).logger
        self.update_dollar_logger = KimpBotLogger("update_dollar", logging_dir).logger
        self.logging_dir = logging_dir
        self.node = node
        self.admin_id = admin_id
        self.proc_n = proc_n
        self.monitor_websocket_switch = True
        self.exclude_outliers = True
        self.register_monitor_msg = register_monitor_msg
        self.exchange_api_key_dict = exchange_api_key_dict
        self.enabled_markets_dict = enabled_markets_dict
        # For redis connection
        self.redis_client = InitRedis()

        self.kimp_bot_core_logger.info(f"InitCore|InitCore initiated with proc_n={proc_n}")

        self.info_dict = {}
        self.info_thread_dict = {}

        self.okx_adaptor = InitOkxAdaptor()
        self.upbit_adaptor = InitUpbitAdaptor(self.exchange_api_key_dict['upbit_read_only']['api_key'], self.exchange_api_key_dict['upbit_read_only']['secret_key'], self.info_dict)
        self.binance_adaptor = InitBinanceAdaptor(self.exchange_api_key_dict['binance_read_only']['api_key'], self.exchange_api_key_dict['binance_read_only']['secret_key'], self.info_dict)

        # UPBIT SPOT (KRW, BTC Market)
        # UPBIT wallet status
        # BINANCE SPOT, USD-M Futures, COIN-M Futures
        self.data_name_list = [
            "upbit_spot_ticker_df",
            "upbit_wallet_status_df",
            "binance_spot_ticker_df",
            "binance_spot_info_df",
            "binance_usd_m_ticker_df",
            "binance_usd_m_info_df",
            "binance_coin_m_ticker_df",
            "binance_coin_m_info_df",
        ]

        for data_name in self.data_name_list:
            self.info_thread_dict[f"update_{data_name}"] = Thread(target=self.update_exchange_info_as_df, args=(data_name,), daemon=True)
            self.info_thread_dict[f"update_{data_name}"].start()
            self.kimp_bot_core_logger.info(f"InitCore|update_{data_name} thread has started.")

        # Wait until all info df has been updated
        while True:
            if all([x in self.info_dict.keys() for x in self.data_name_list]):
                self.kimp_bot_core_logger.info(f"InitCore|All info df has been updated.")
                break
            else:
                self.kimp_bot_core_logger.info(f"InitCore|Waiting for all info to be updated.")
                time.sleep(2)

        self.exchange_websocket_dict = {}
        self.exchange_websocket_dict['UPBIT_SPOT'] = UpbitWebsocket(self.admin_id, self.node, self.proc_n, self.get_upbit_symbol_list, self.register_monitor_msg, self.logging_dir)
        self.exchange_websocket_dict['BINANCE_SPOT'] = BinanceWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_spot_symbol_list, register_monitor_msg, self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_USD_M'] = BinanceUSDMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_usdm_symbol_list, register_monitor_msg, self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_COIN_M'] = BinanceCOINMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_coinm_symbol_list, register_monitor_msg, self.info_dict, logging_dir)

        self.update_dollar_return_dict = {}
        self.update_dollar_thread = Thread(target=update_dollar.fetch_dollar_loop, args=(self.update_dollar_return_dict, self.update_dollar_logger), daemon=True)
        self.update_dollar_thread.start()
        time.sleep(2)

    def update_exchange_info_as_df(self, data_name, loop_time_secs=15):
        while True:
            try:
                if data_name == "upbit_spot_ticker_df":
                    self.info_dict[data_name] = self.upbit_adaptor.all_tickers()
                elif data_name == "upbit_wallet_status_df":
                    self.info_dict[data_name] = self.upbit_adaptor.wallet_status()
                elif data_name == "binance_spot_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.spot_all_tickers()
                elif data_name == "binance_spot_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.spot_exchange_info()
                elif data_name == "binance_usd_m_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.usdm_all_tickers()
                elif data_name == "binance_usd_m_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.usdm_exchange_info()
                elif data_name == "binance_coin_m_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.coinm_all_tickers()
                elif data_name == "binance_coin_m_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.coinm_exchange_info()
                else:
                    self.kimp_bot_core_logger.error(f"update_exchange_info_as_df|name:{data_name} is not valid.")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} is not valid.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                    break
                time.sleep(loop_time_secs)
            except Exception as e:
                self.kimp_bot_core_logger.error(f"update_exchange_info_as_df|name:{data_name}, {traceback.format_exc()}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} failed.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(loop_time_secs)

    def get_dollar_dict(self):
        return self.update_dollar_return_dict

    def start_monitor_update_to_redis(self):
        if self.register_monitor_msg is None:
            self.kimp_bot_core_logger.error(f"start_monitor_update_to_redis|monitor setting hasn't configured.")
        else:
            self.start_monitor_update_kimp_to_redis()
            self.start_monitor_update_wa_kimp_to_redis()
            self.start_monitor_update_dollar_to_redis()

    # def get_kimp_df(self):
    #     return dict_convert.get_kimp_df(
    #         self.OKX_BOOKTICKER_DICT,
    #         self.UPBIT_TICKER_DICT,
    #         self.UPBIT_ORDERBOOK_DICT,
    #         float(self.update_dollar_return_dict['price']))

    # def get_wa_kimp_dict(self, exclude_outliers=True, kimp_side='last'):
    #     if exclude_outliers == True:
    #         kimp_df = self.get_kimp_df().sort_values('tp_kimp').iloc[1:-1,:]
    #     else:
    #         kimp_df = self.get_kimp_df()
    #     if kimp_side == 'last':
    #         wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['tp_kimp']).sum()
    #         wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['tp_usdt']).sum()
    #         wa_kimp_dict = {
    #             "wa_kimp": wa_kimp,
    #             "wa_usdt": wa_usdt
    #         }
    #     elif kimp_side == 'enter':
    #         wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['enter_kimp']).sum()
    #         wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['enter_usdt']).sum()
    #         wa_kimp_dict = {
    #             "wa_kimp": wa_kimp,
    #             "wa_usdt": wa_usdt
    #         }
    #     else:
    #         wa_kimp = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['exit_kimp']).sum()
    #         wa_usdt = (kimp_df['acc_trade_price_24h']/kimp_df['acc_trade_price_24h'].sum() * kimp_df['exit_usdt']).sum()
    #         wa_kimp_dict = {
    #             "wa_kimp": wa_kimp,
    #             "wa_usdt": wa_usdt
    #         }
    #     return wa_kimp_dict

    def websocket_proc_status(self, print_status=None):
        pass
        # total_proc_dict = {
        #                     **{'Binance|'+k:v for k,v in self.binance_price_websocket.binance_websocket_proc_dict.items()}, 
        #                     **{'Upbit|'+k:v for k,v in self.upbit_price_websocket.upbit_websocket_proc_dict.items()}
        #                    }
        # if len(total_proc_dict) == 0:
        #     proc_status = False
        #     print_text = "any websocket proc is not running."
        #     return proc_status, print_text
        # else:
        #     print_text = ""
        #     for key, value in total_proc_dict.items():
        #         print_text += f"{key} status: {value.is_alive()}\n"
        #     if print_result:
        #         print(print_text)
        #     return all([x.is_alive() for x in total_proc_dict.values()]), print_text
    
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

    # def terminate_websocket_procs(self):
    #     price_websocket.terminate_websocket_proc(
    #         self.OKX_BOOKTICKER_PROC_LIST,
    #         self.UPBIT_TICKER_PROC_LIST,
    #         self.UPBIT_ORDERBOOK_PROC_LIST,
    #         self.price_websocket_logger
    #         )

    # def monitor_websocket(self, loop_secs=2.5):
    #     if self.register_monitor_msg is None:
    #         self.kimp_bot_core_logger.error(f"monitor_websocket|monitor setting hasn't configured.")
    #         return
    #     self.kimp_bot_core_logger.info(f"monitor_websocket|monitor_websocket_procs started.")
    #     def monitor_loop(monitor_bot_token=self.monitor_bot_token, monitor_api_url=self.monitor_api_url):
    #         input_type = "monitor"
    #         title1 = "websocket process stopped!"
    #         title2 = "websocket status after restart"
    #         while self.monitor_websocket_switch:
    #             try:
    #                 integrity_flag, whole_status_str = self.websocket_proc_status(print_status=False)
    #                 if integrity_flag == False:
    #                     self.kimp_bot_core_logger.error(f"websocket integrity has broken. proc_stats: {whole_status_str}")
    #                     self.register_monitor_msg.register(self.admin_id, self.node, input_type, title1, content=whole_status_str, code=None, sent_switch=0, send_counts=1, remark=None)
    #                     # print(f"Before re_init by monitor_loop")
    #                     self.terminate_websocket_procs()
    #                     self.__init__(self.proc_n, self.node, self.admin_id)
    #                     # print(f"After re_init by monitor_loop")
    #                     integrity_flag, whole_status_str = self.websocket_proc_status(print_status=False)
    #                     status_after_restart = f"monitor_websocket|After re_init by monitor_loop. proc_stats: {whole_status_str}"
    #                     self.kimp_bot_core_logger.info(status_after_restart)
    #                     self.register_monitor_msg.register(self.admin_id, self.node, input_type, title2, content=status_after_restart, code=None, sent_switch=0, send_counts=1, remark=None)
    #             except Exception as e:
    #                     self.kimp_bot_core_logger.critical(f"monitor_websocket|monitor_websocket_procs 에러!|{traceback.format_exc()}")
    #                     self.register_monitor_msg.register(self.admin_id, self.origin, input_type, 'monitor_websocket_procs 에러!', content=None, code=None, sent_switch=0, send_counts=1, remark=None)
    #             time.sleep(loop_secs)
    #     self.monitor_websocket_thread = Thread(target=monitor_loop, daemon=True)
    #     self.monitor_websocket_thread.start()

    # def stop_monitor_websocket(self):
    #     self.monitor_websocket_switch = False
    #     # print(f"monitor_websocket_switch has been set to False.")
    #     self.kimp_bot_core_logger.info(f"stop_monitor_websocket|monitor_websocket_switch has been set to False.")
    #     time.sleep(3)
    #     # print(f"self.monitor_websocket_thread.is_alive: {self.monitor_websocket_thread.is_alive()}")
    #     self.kimp_bot_core_logger.info(f"stop_monitor_websocket|self.monitor_websocket_thread.is_alive: {self.monitor_websocket_thread.is_alive()}")

    def start_monitor_update_kimp_to_redis(self, pickled_kimp_df_name="pickled_kp", update_loop_secs=0.1, monitor_loop_secs=2.5):
        if self.register_monitor_msg is None:
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
                    self.register_monitor_msg.register(self.admin_id, self.node, input_type, title, "restarting update_kimp_to_redis_thread..")
                    self.update_kimp_to_redis_thread = Thread(target=update_kimp_to_redis, daemon=True)
                    self.update_kimp_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_kimp_to_redis_thread = Thread(target=loop_monitor_update_kimp_to_redis, daemon=True)
        loop_monitor_update_kimp_to_redis_thread.start()

    def start_monitor_update_wa_kimp_to_redis(self, pickled_wa_kimp_dict_name="pickled_wa_kp", update_loop_secs=0.15, monitor_loop_secs=2.5):
        if self.register_monitor_msg is None:
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
                    self.register_monitor_msg.register(self.admin_id, self.node, input_type, title, "restarting update_wa_kimp_to_redis_thread..")
                    self.update_wa_kimp_to_redis_thread = Thread(target=update_wa_kimp_to_redis, daemon=True)
                    self.update_wa_kimp_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_wa_kimp_to_redis_thread = Thread(target=loop_monitor_update_wa_kimp_to_redis, daemon=True)
        loop_monitor_update_wa_kimp_to_redis_thread.start()

    def start_monitor_update_dollar_to_redis(self, pickled_dollar_dict_name="pickled_dollar_dict", update_loop_secs=1, monitor_loop_secs=2.5):
        if self.register_monitor_msg is None:
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
                    self.register_monitor_msg.register(self.admin_id, self.node, input_type, title, "restarting update_dollar_to_redis_thread..")
                    self.update_dollar_to_redis_thread = Thread(target=update_dollar_to_redis, daemon=True)
                    self.update_dollar_to_redis_thread.start()
                time.sleep(monitor_loop_secs)
        loop_monitor_update_dollar_to_redis_thread = Thread(target=loop_monitor_update_dollar_to_redis, daemon=True)
        loop_monitor_update_dollar_to_redis_thread.start()

    def get_upbit_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][['market','acc_trade_price_24h_krw']].copy()
        upbit_ticker_df['base_symbol'] = upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
        for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
            each_upbit_ticker_df = upbit_ticker_df[upbit_ticker_df['market'].str.startswith(upbit_market)].copy()
            
            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_info_df = self.info_dict['binance_spot_info_df'][self.info_dict['binance_spot_info_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_info_df['base_symbol'] = each_binance_spot_info_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                
                merged_df = each_upbit_ticker_df.merge(each_binance_spot_info_df[['symbol','base_symbol']], on='base_symbol', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usd_m_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']: # ["USDT_PERPETUAL", "BUSD_PERPETUAL"]
                # Check PERPETUAL
                quote_asset, contract_type = binance_usd_m_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_upbit_ticker_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coin_m_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']: # ["PERPETUAL"]
                # Check PERPETUAL
                contract_type = binance_coin_m_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_upbit_ticker_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)
        total_df.drop_duplicates(subset=['market'], inplace=True)
        total_df.sort_values(by='acc_trade_price_24h_krw', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['market'].to_list()

    def get_binance_spot_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][['symbol','volume_usdt']].copy()
        binance_spot_ticker_df = binance_spot_ticker_df.rename(columns={'symbol':'spot_symbol'})

        for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
            each_binance_spot_ticker_df = binance_spot_ticker_df[binance_spot_ticker_df['spot_symbol'].str.endswith(binance_spot_market)].copy()
            each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['spot_symbol'].apply(lambda x: x[:-len(binance_spot_market)])
            
            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                
                merged_df = each_binance_spot_ticker_df.merge(each_upbit_ticker_df[['market','base_symbol']], on='base_symbol', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usdm_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
                quote_asset, contract_type = binance_usdm_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_binance_spot_ticker_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coinm_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
                contract_type = binance_coinm_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_binance_spot_ticker_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['spot_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['spot_symbol'].to_list()

    def get_binance_usdm_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_usd_m_ticker_df = self.info_dict['binance_usd_m_ticker_df'][['symbol','volume_usdt']].copy()
        binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][['symbol','quoteAsset','baseAsset','contractType']].copy()
        binance_usdm_merged_df = binance_usd_m_ticker_df.merge(binance_usd_m_info_df, on='symbol', how='inner')
        binance_usdm_merged_df = binance_usdm_merged_df.rename(columns={'symbol':'usdm_symbol'})

        for binance_usdm_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
            quote_asset, contract_type = binance_usdm_market.split('_')
            each_binance_usdm_merged_df = binance_usdm_merged_df[(binance_usdm_merged_df['quoteAsset']==quote_asset)&(binance_usdm_merged_df['contractType']==contract_type)].copy()

            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                merged_df = each_binance_usdm_merged_df.merge(each_upbit_ticker_df[['market','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][self.info_dict['binance_spot_ticker_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                merged_df = each_binance_usdm_merged_df.merge(each_binance_spot_ticker_df[['symbol','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coinm_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
                contract_type = binance_coinm_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_binance_usdm_merged_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='baseAsset', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['usdm_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['usdm_symbol'].to_list()

    def get_binance_coinm_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_coin_m_ticker_df = self.info_dict['binance_coin_m_ticker_df'][['symbol','volume_usdt']].copy()
        binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][['symbol','baseAsset','contractType']].copy()
        binance_coinm_merged_df = binance_coin_m_ticker_df.merge(binance_coin_m_info_df, on='symbol', how='inner')
        binance_coinm_merged_df = binance_coinm_merged_df.rename(columns={'symbol':'coinm_symbol'})

        for binance_coinm_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
            contract_type = binance_coinm_market
            each_binance_coinm_merged_df = binance_coinm_merged_df[binance_coinm_merged_df['contractType']==contract_type].copy()

            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                merged_df = each_binance_coinm_merged_df.merge(each_upbit_ticker_df[['market','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][self.info_dict['binance_spot_ticker_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                merged_df = each_binance_coinm_merged_df.merge(each_binance_spot_ticker_df[['symbol','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usdm_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
                quote_asset, contract_type = binance_usdm_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_binance_coinm_merged_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='baseAsset', right_on='baseAsset', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['coinm_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['coinm_symbol'].to_list()
    
    def check_status(self, print_result=False, include_text=False):
        exchange_proc_status_tup_list = [x.check_status(include_text=True) for x in self.exchange_websocket_dict.values()]
        proc_status = all([x[0] for x in exchange_proc_status_tup_list])
        print_text = ""
        for each_result in [x[1] for x in exchange_proc_status_tup_list]:
            print_text += f"{each_result}\n"
        if print_result:
            print(print_text)
        if include_text:
            return proc_status, print_text
        return proc_status

    



