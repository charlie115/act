from multiprocessing import Process, Manager, Queue, Event
from threading import Thread
import pandas as pd
import datetime
from binance import ThreadedWebsocketManager
from binance.enums import FuturesType
import traceback
import time
import queue
import _pickle as pickle
# set directory to upper directory
import os
import sys
import json
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_connector import InitRedis

class BinanceWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir):
        self.market_type = market_type
        self.websocket_logger = KimpBotLogger(f"binance_{self.market_type.lower()}_websocket", logging_dir).logger
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.get_symbol_list = get_symbol_list
        self.info_dict = info_dict
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        manager = Manager()
        self.bookticker_dict = manager.dict()
        self.ticker_dict = manager.dict()
        self.proc_n = int(proc_n * 2)
        self.before_symbol_list = self.get_symbol_list()
        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self.liquidation_list = manager.list()
        self.redis_client_db1 = InitRedis(db=1)
        self._start_websocket()
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()
        
    def __del__(self):
        self.terminate_websocket()

    # For fetching ticker, bookticker data for usdm, coinm, spot
    def price_websocket(self, store_dict, symbol_list, error_event, proc_name, data_name):
        if symbol_list == []:
            raise Exception(f"price_websocket|symbol_list should not be empty")
        def handle_bookticker_streams(msg):
            try:
                # event_type = msg['stream']
                # print(msg['data']) # test
                # if msg['data']['s'] == 'ETHUSDT': # test
                #     print(msg['data']['T']) # test
                store_dict[msg['data']['s']] = {**msg['data'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp()*1000000)}
                # self.redis_client_db1.set_data(f"INFO_CORE|BINANCE_{self.market_type}|{data_name}|{msg['data']['s']}", json.dumps({**msg['data'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1000000)}))
                # self.redis_client_db1.set_data(f"INFO_CORE|BINANCE_{self.market_type}|{data_name}", pickle.dumps(dict(store_dict)))
            except Exception:
                self.websocket_logger.error(f"handle_bookticker_streams|{proc_name}, {traceback.format_exc()}, msg:{msg}")
                error_event.set()
        def handle_ticker_streams(msg):
            try:
                store_dict[msg['data']['s']] = {**msg['data'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp()*1000000)}
                # self.redis_client_db1.set_data(f"INFO_CORE|BINANCE_{self.market_type}|{data_name}|{msg['data']['s']}", json.dumps({**msg['data'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1000000)}))
                # self.redis_client_db1.set_data(f"INFO_CORE|BINANCE_{self.market_type}|{data_name}", pickle.dumps(dict(store_dict)))
            except Exception:
                self.websocket_logger.error(f"handle_ticker_streams|{proc_name}, {traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if 'bookticker' in proc_name:
            stream_list = [x.lower()+'@bookTicker' for x in symbol_list]
            if self.market_type == "SPOT":
                twm.start_multiplex_socket(callback=handle_bookticker_streams, streams=stream_list)
            elif self.market_type == "USD_M":
                twm.start_futures_multiplex_socket(callback=handle_bookticker_streams, streams=stream_list)
            elif self.market_type == "COIN_M":
                twm.start_futures_multiplex_socket(callback=handle_bookticker_streams, streams=stream_list, futures_type=FuturesType.COIN_M)
            else:
                raise Exception(f"price_websocket|market_type should be SPOT, USD_M or COIN_M, not {self.market_type}")
        else:
            stream_list = [x.lower()+'@ticker' for x in symbol_list]
            if self.market_type == "SPOT":
                twm.start_multiplex_socket(callback=handle_ticker_streams, streams=stream_list)
            elif self.market_type == "USD_M":
                twm.start_futures_multiplex_socket(callback=handle_ticker_streams, streams=stream_list)
            elif self.market_type == "COIN_M":
                twm.start_futures_multiplex_socket(callback=handle_ticker_streams, streams=stream_list, futures_type=FuturesType.COIN_M)
            else:
                raise Exception(f"price_websocket|market_type should be SPOT, USD_M or COIN_M, not {self.market_type}")
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop_socket(stream_list)
        twm.stop()
        self.websocket_logger.info(f"[BINANCE {self.market_type}]{proc_name} websocket has been terminated. (twm.stop() has been executed)")
        raise Exception(f"[BINANCE {self.market_type}]{proc_name} websocket has been terminated. (twm.stop() has been executed)")

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_webscoket is False:
                        for i in range(self.proc_n):
                            # Check if the process exists and is alive
                            start_proc = False
                            restarted = False
                            if f"{i+1}th_bookticker_proc" in self.websocket_proc_dict and not self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].is_alive():
                                content = f"handle_price_procs|[BINANCE {self.market_type}]{i+1}th_bookticker_proc has died. terminating and restarting.."
                                self.websocket_logger.error(content)
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].join()
                                start_proc = True
                                restarted = True
                            elif f"{i+1}th_bookticker_proc" not in self.websocket_proc_dict:
                                self.websocket_logger.info(f"[BINANCE {self.market_type}]{i+1}th_bookticker_proc is not in self.websocket_proc_dict. starting..")
                                start_proc = True
                            if start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                symbol_list = self.sliced_symbol_list[i]
                                self.websocket_proc_dict[f"{i+1}th_bookticker_proc"] = Process(target=self.price_websocket, args=(self.bookticker_dict, symbol_list, error_event, f"{i+1}th_bookticker_proc", "bookticker"), daemon=True)
                                self.websocket_symbol_dict[f"{i+1}th_bookticker_symbol"] = symbol_list
                                self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].start()
                                self.websocket_logger.info(f"[BINANCE {self.market_type}]started {i+1}th_bookticker_proc websocket proc..")
                                if restarted:
                                    content = f"handle_price_procs|[BINANCE {self.market_type}]{i+1}th_bookticker_proc has been restarted. alive status: {self.websocket_proc_dict[f'{i+1}th_bookticker_proc'].is_alive()}"
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                time.sleep(0.5)
                        
                        start_proc = False
                        restarted = False
                        if "ticker_proc" in self.websocket_proc_dict and not self.websocket_proc_dict["ticker_proc"].is_alive():
                            content = f"handle_price_procs|[BINANCE {self.market_type}]ticker_proc has died. terminating and restarting.."
                            self.websocket_logger.error(content)
                            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                            self.websocket_proc_dict["ticker_proc"].terminate()
                            self.websocket_proc_dict["ticker_proc"].join()
                            start_proc = True
                            restarted = True
                        elif "ticker_proc" not in self.websocket_proc_dict:
                            self.websocket_logger.info(f"[BINANCE {self.market_type}]ticker_proc is not in self.websocket_proc_dict. starting..")
                            start_proc = True
                        if start_proc:
                            error_event = Event()
                            self.price_proc_event_list.append(error_event)
                            symbol_list = self.before_symbol_list
                            self.websocket_proc_dict["ticker_proc"] = Process(target=self.price_websocket, args=(self.ticker_dict, symbol_list, error_event, "ticker_proc", "ticker"), daemon=True)
                            self.websocket_symbol_dict["ticker_symbol"] = symbol_list
                            self.websocket_proc_dict["ticker_proc"].start()
                            self.websocket_logger.info(f"[BINANCE {self.market_type}]started ticker_proc websocket proc..")
                            if restarted:
                                content = f"handle_price_procs|[BINANCE {self.market_type}]ticker_proc has been restarted. alive status: {self.websocket_proc_dict['ticker_proc'].is_alive()}"
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

                        # Spawning liquidation process in case the market_type is USD_M or COIN_M
                        if self.market_type != "SPOT":
                            if "liquidation_proc" in self.websocket_proc_dict and not self.websocket_proc_dict["liquidation_proc"].is_alive():
                                content = f"handle_price_procs|[BINANCE {self.market_type}]liquidation_proc has died. terminating and restarting.."
                                self.websocket_logger.error(content)
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                self.websocket_proc_dict["liquidation_proc"].terminate()
                                self.websocket_proc_dict["liquidation_proc"].join()
                                error_event = Event()
                                self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                                self.websocket_proc_dict["liquidation_proc"].start()
                                content = f"handle_price_procs|liquidation_proc has been restarted. alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}"
                                self.websocket_logger.info(f"[BINANCE {self.market_type}]restarted liquidation_proc websocket alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}")
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                            elif "liquidation_proc" not in self.websocket_proc_dict:
                                self.websocket_logger.info(f"[BINANCE {self.market_type}]liquidation_proc is not in self.websocket_proc_dict. starting..")
                                error_event = Event()
                                self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                                self.websocket_proc_dict["liquidation_proc"].start()
                                self.websocket_logger.info(f"[BINANCE {self.market_type}]started liquidation_proc websocket proc..")
                except Exception as e:
                    self.websocket_logger.error(f"handle_price_procs|{traceback.format_exc()}")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"Binance {self.market_type} Websocket|handle_price_procs", content=e, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(2)
                time.sleep(0.25)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    # For fetching liquidation data in case the market_type is USD_M or COIN_M
    def liquidation_websocket(self, liquidation_list, error_event):
        self.websocket_logger.info(f"started liquidation_websocket for {self.market_type}..")
        def handle_futures_liquidation_streams(msg):
            try:
                if len(liquidation_list) > 1000:
                    liquidation_list.pop(0)
                # Filtering can be applied later.
                liquidation_list.append(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_futures_liquidation_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if self.market_type == "USD_M":
            twm.start_futures_multiplex_socket(callback=handle_futures_liquidation_streams, streams=['!forceOrder@arr'])
        elif self.market_type == "COIN_M":
            twm.start_futures_multiplex_socket(callback=handle_futures_liquidation_streams, streams=['!forceOrder@arr'], futures_type=FuturesType.COIN_M)
        else:
            raise Exception(f"liquidation_websocket|market_type should be USD_M or COIN_M, not {self.market_type}")
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = f"[BINANCE {self.market_type}]Binance websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BINANCE {self.market_type}]{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        
    def terminate_websocket(self):
        self.stop_restart_webscoket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[BINANCE {self.market_type}]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info(f"[BINANCE {self.market_type}]started monitor_shared_symbol_change..")
        monitor_shared_symbol_change_count = 0
        while True:
            time.sleep(loop_time_secs)
            try:
                restart_websockets = False
                new_symbol_list = self.get_symbol_list()
                
                if sorted(self.before_symbol_list) != sorted(new_symbol_list):
                    monitor_shared_symbol_change_count += 1
                    if monitor_shared_symbol_change_count > 5:
                        restart_websockets = True
                        deleted_symbols = [x for x in self.before_symbol_list if x not in new_symbol_list]
                        added_symbols = [x for x in new_symbol_list if x not in self.before_symbol_list]
                        content = f"monitor_shared_symbol_change|[BINANCE {self.market_type}]{self.market_type} shared symbol changed. deleted: {deleted_symbols}, added: {added_symbols}"
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        for each_symbol in deleted_symbols:
                            # remove deleted symbol from ticker_dict and bookticker_dict
                            try:
                                del self.bookticker_dict[each_symbol]
                                # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|BINANCE_{self.market_type}|bookticker|{each_symbol}")
                            except Exception:
                                pass
                            try:
                                del self.ticker_dict[each_symbol]
                                # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|BINANCE_{self.market_type}|ticker|{each_symbol}")
                            except Exception:
                                pass
                else:
                    monitor_shared_symbol_change_count = 0
                
                if restart_websockets is True:
                    # Set the newer values to before values
                    self.before_symbol_list = new_symbol_list
                    # Set sliced values too
                    self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
                    # terminate websockets
                    self.terminate_websocket()
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[BINANCE {self.market_type}] monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"started monitor_websocket_last_update..")
        while True:
            try:
                time.sleep(loop_time_secs)
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)
                bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)
                ticker_terminate_flag = False
                allocated_ticker_df = ticker_df[ticker_df['s'].isin(self.before_symbol_list)]
                ticker_last_update = allocated_ticker_df['last_update_timestamp'].max()
                if len(allocated_ticker_df) == 0:
                    content = f"monitor_websocket_last_update|[BINANCE {self.market_type}]ticker_proc has no ticker_dict data. Restarting Websocket.."
                    self.websocket_logger.info(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    self.websocket_proc_dict[f"ticker_proc"].terminate()
                    self.websocket_proc_dict[f"ticker_proc"].join()
                    continue
                if (datetime.datetime.utcnow().timestamp() - ticker_last_update/1000000) > update_threshold_mins*60:
                    ticker_terminate_flag = True
                    slow_ticker_symbol = allocated_ticker_df[allocated_ticker_df['last_update_timestamp'] == ticker_last_update]['s'].values[0]
                    content = f"monitor_websocket_last_update|ticker_proc ticker_dict's {slow_ticker_symbol} last update is older than {update_threshold_mins} mins."
                    self.websocket_logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[BINANCE {self.market_type}]monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                if ticker_terminate_flag is True:
                    content = f"monitor_websocket_last_update|Restarting Websocket.. ticker_proc will be terminated."
                    self.websocket_logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    self.websocket_proc_dict["ticker_proc"].terminate()
                    self.websocket_proc_dict["ticker_proc"].join()

                for i in range(self.proc_n):
                    bookticker_terminate_flag = False
                    allocated_symbol_list = self.sliced_symbol_list[i]
                    # check ticker dict's last update
                    allocated_bookticker_df = bookticker_df[bookticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_bookticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE {self.market_type}]{i+1}th_bookticker_proc has no bookticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].join()
                        continue
                    bookticker_last_update = allocated_bookticker_df['last_update_timestamp'].max()
                    # If the last update is older than update_threshold_mins, restart websocket

                    if (datetime.datetime.utcnow().timestamp() - bookticker_last_update/1000000) > update_threshold_mins*60:
                        bookticker_terminate_flag = True
                        slow_bookticker_symbol = allocated_bookticker_df[allocated_bookticker_df['last_update_timestamp'] == bookticker_last_update]['s'].values[0]
                        content = f"monitor_websocket_last_update|{i+1}th_bookticker_proc bookticker_dict's {slow_bookticker_symbol} last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[BINANCE {self.market_type}]monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if bookticker_terminate_flag is True:
                        content = f"monitor_websocket_last_update|Restarting Websocket.. {i+1}th_bookticker_proc will be terminated."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_bookticker_proc"].join()
            except Exception as e:
                content = f"monitor_websocket_last_update|[BINANCE {self.market_type}]{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        binance_ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df.loc[:, ['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_merged_df = binance_merged_df.merge(self.info_dict[f'binance_{self.market_type.lower()}_info_df'][['symbol','base_asset','quote_asset']], left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df


##############################################################################################################################

class BinanceUSDMWebsocket(BinanceWebsocket):
    def __init__(self, admin_id, node, proc_n, get_binance_usdm_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n, get_binance_usdm_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir)

##############################################################################################################################

class BinanceCOINMWebsocket(BinanceWebsocket):
    def __init__(self, admin_id, node, proc_n, get_binance_coinm_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n/2, get_binance_coinm_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir)
