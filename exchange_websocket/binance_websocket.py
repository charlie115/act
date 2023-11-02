from multiprocessing import Process, Manager, Queue, Event
from threading import Thread
import pandas as pd
import datetime
from binance import ThreadedWebsocketManager
from binance.enums import FuturesType
import traceback
import time
import queue
# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger
from exchange_websocket.utils import list_slice


class BinanceWebsocket:
    def __init__(self, admin_id, node, proc_n, get_binance_spot_symbol_list, register_monitor_msg, info_dict, logging_dir):
        self.websocket_logger = KimpBotLogger("binance_websocket", logging_dir).logger
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.get_symbol_list = get_binance_spot_symbol_list
        self.info_dict = info_dict
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        manager = Manager()
        self.bookticker_dict = manager.dict()
        self.ticker_dict = manager.dict()
        self.proc_n = proc_n
        self.before_symbol_list = self.get_symbol_list()
        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self._start_websocket()
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()

    def __del__(self):
        self.terminate_websocket()

    # For fetching ticker, bookticker data for usdm, coinm, spot
    def price_websocket(self, bookticker_dict, ticker_dict, symbol_list, error_event):
        def handle_spot_bookticker_streams(msg):
            try:
                # event_type = msg['stream']
                # print(msg['data']) # test
                # if msg['data']['s'] == 'ETHUSDT': # test
                #     print(msg['data']['T']) # test
                bookticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_spot_bookticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        def handle_spot_ticker_streams(msg):
            try:
                ticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_spot_ticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if symbol_list != []:
            spot_bookticker_list = [x.lower()+'@bookTicker' for x in symbol_list]
            twm.start_multiplex_socket(callback=handle_spot_bookticker_streams, streams=spot_bookticker_list)
            spot_ticker_list = [x.lower()+'@ticker' for x in symbol_list]
            twm.start_multiplex_socket(callback=handle_spot_ticker_streams, streams=spot_ticker_list)
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    # def kline_websocket(self, kline_dict, symbol_list, error_event):
    #     self.websocket_logger.info("started kline_websocket for SPOT..")
    #     def handle_spot_kline_streams(msg):
    #         try:
    #             symbol = msg['data']['s']
    #             if msg['data']['k']['x'] == True:
    #                 kline_dict[symbol].put(msg['data'])
    #         except Exception:
    #             self.websocket_logger.error(f"handle_spot_kline_streams|{traceback.format_exc()}, msg:{msg}")
    #             error_event.set()
    #     twm = ThreadedWebsocketManager()
    #     twm.daemon = True
    #     twm.start()
    #     if symbol_list != []:
    #         spot_kline_list = []
    #         for kline_type in self.binance_kline_type_list:
    #             spot_kline_list += [x.lower()+f'@kline_{kline_type}' for x in symbol_list]
    #         twm.start_multiplex_socket(callback=handle_spot_kline_streams, streams=spot_kline_list)
    #     # twm.join()
    #     while not error_event.is_set():
    #         time.sleep(0.1)
    #     twm.stop()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_webscoket is False:
                        for i in range(self.proc_n):
                            # Check if the process exists and is alive
                            start_proc = False
                            restarted = False
                            if f"{i+1}th_price_proc" in self.websocket_proc_dict and not self.websocket_proc_dict[f"{i+1}th_price_proc"].is_alive():
                                content = f"handle_price_procs|[BINANCE SPOT]{i+1}th_price_proc has died. terminating and restarting.."
                                self.websocket_logger.error(content)
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                                start_proc = True
                                restarted = True
                            elif f"{i+1}th_price_proc" not in self.websocket_proc_dict:
                                self.websocket_logger.info(f"[BINANCE SPOT]{i+1}th_price_proc is not in self.websocket_proc_dict. starting..")
                                start_proc = True
                            if start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                symbol_list = self.sliced_symbol_list[i]
                                self.websocket_proc_dict[f"{i+1}th_price_proc"] = Process(target=self.price_websocket, args=(self.bookticker_dict, self.ticker_dict, symbol_list, error_event), daemon=True)
                                self.websocket_symbol_dict[f"{i+1}th_price_symbol"] = symbol_list
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].start()
                                self.websocket_logger.info(f"[BINANCE SPOT]started {i+1}th_price_proc websocket proc..")
                                if restarted:
                                    content = f"handle_price_procs|[BINANCE SPOT]{i+1}th_price_proc has been restarted. alive status: {self.websocket_proc_dict[f'{i+1}th_price_proc'].is_alive()}"
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                time.sleep(0.5)
                except Exception as e:
                    self.websocket_logger.error(f"handle_price_procs|{traceback.format_exc()}")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"Binance Spot Websocket|handle_price_procs", content=e, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(2)
                time.sleep(0.25)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = "[BINANCE SPOT]Binance websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BINANCE SPOT]{key} status: {value.is_alive()}\n"
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
        self.websocket_logger.info(f"[BINANCE SPOT]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info("[BINANCE SPOT]started monitor_shared_symbol_change..")
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
                        content = f"monitor_shared_symbol_change|[BINANCE SPOT]SPOT shared symbol changed. deleted: {deleted_symbols}, added: {added_symbols}"
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        for each_symbol in deleted_symbols:
                            # remove deleted symbol from upbit_ticker_dict and upbit_orderbook_dict
                            try:
                                del self.bookticker_dict[each_symbol]
                            except Exception:
                                pass
                            try:
                                del self.ticker_dict[each_symbol]
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
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"started monitor_websocket_last_update..")
        while True:
            try:
                time.sleep(loop_time_secs)
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)
                bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)
                for i in range(self.proc_n):
                    terminate_flag = False
                    allocated_symbol_list = self.sliced_symbol_list[i]
                    # check ticker dict's last update
                    allocated_ticker_df = ticker_df[ticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE SPOT]{i+1}th_price_proc has no ticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update'].max()
                    allocated_bookticker_df = bookticker_df[bookticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_bookticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE SPOT]{i+1}th_price_proc has no bookticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    bookticker_last_update = allocated_bookticker_df['last_update'].max()
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.now() - ticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc ticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if (datetime.datetime.now() - bookticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc bookticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if terminate_flag is True:
                        content = f"monitor_websocket_last_update|Restarting Websocket.. {i+1}th_price_proc will be terminated."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
            except Exception as e:
                content = f"monitor_websocket_last_update|[BINANCE SPOT]{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        binance_ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df.loc[:, ['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_merged_df = binance_merged_df.merge(self.info_dict['binance_spot_info_df'][['symbol','base_asset','quote_asset']], left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df


##############################################################################################################################

class BinanceUSDMWebsocket:
    def __init__(self, admin_id, node, proc_n, get_binance_usdm_symbol_list, register_monitor_msg, info_dict, logging_dir):
        self.websocket_logger = KimpBotLogger("binance_usdm_websocket", logging_dir).logger
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.info_dict = info_dict
        self.get_symbol_list = get_binance_usdm_symbol_list
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        manager = Manager()
        self.bookticker_dict = manager.dict()
        self.ticker_dict = manager.dict()
        self.proc_n = proc_n
        self.before_symbol_list = self.get_symbol_list()
        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self.liquidation_list = manager.list()
        self._start_websocket()
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()

    def __del__(self):
        self.terminate_websocket()

    # For fetching ticker, bookticker data
    def price_websocket(self, bookticker_dict, ticker_dict, symbol_list, error_event):
        def handle_usdm_bookticker_streams(msg):
             # event_type = msg['stream']
            # print(msg['data']) # test
            # if msg['data']['s'] == 'ETHUSDT': # test
            #     print(msg['data']['T']) # test
            try:
                bookticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_usdm_bookticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        def handle_usdm_ticker_streams(msg):
            try:
                ticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_usdm_ticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if symbol_list != []:
            usdm_bookticker_list = [x.lower()+'@bookTicker' for x in symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_usdm_bookticker_streams, streams=usdm_bookticker_list)
            usdm_ticker_list = [x.lower()+'@ticker' for x in symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_usdm_ticker_streams, streams=usdm_ticker_list)
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    # For fetching liquidation data
    def liquidation_websocket(self, liquidation_list, error_event):
        self.websocket_logger.info("started liquidation_websocket for USD-M..")
        def handle_usdm_liquidation_streams(msg):
            try:
                if len(liquidation_list) > 1000:
                    liquidation_list.pop(0)
                # Filtering can be applied later.
                liquidation_list.append(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_usdm_liquidation_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        twm.start_futures_multiplex_socket(callback=handle_usdm_liquidation_streams, streams=['!forceOrder@arr'])
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    # def binance_kline_websocket(self, kline_dict, symbol_list, error_event):
    #     self.websocket_logger.info("started binance_kline_websocket for USD-M")
    #     def handle_kline_streams(msg):
    #         try:
    #             symbol = msg['data']['s']
    #             if msg['data']['k']['x'] == True:
    #                 kline_dict[symbol].put(msg['data'])
    #         except Exception:
    #             self.websocket_logger.error(f"handle_kline_streams|{traceback.format_exc()}, msg:{msg}")
    #             error_event.set()
    #     twm = ThreadedWebsocketManager()
    #     twm.daemon = True
    #     twm.start()
    #     if symbol_list != []:
    #         usdm_kline_list = []
    #         for kline_type in self.binance_kline_type_list:
    #             usdm_kline_list += [x.lower()+f'@kline_{kline_type}' for x in symbol_list]
    #         twm.start_futures_multiplex_socket(callback=handle_kline_streams, streams=usdm_kline_list)
    #     # twm.join()
    #     while not error_event.is_set():
    #         time.sleep(0.1)
    #     twm.stop()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_webscoket is False:
                        for i in range(self.proc_n):
                            # Check if the process exists and is alive
                            start_proc = False
                            restarted = False
                            if f"{i+1}th_price_proc" in self.websocket_proc_dict and not self.websocket_proc_dict[f"{i+1}th_price_proc"].is_alive():
                                content = f"handle_price_procs|[BINANCE USD-M]{i+1}th_price_proc has died. terminating and restarting.."
                                self.websocket_logger.error(content)
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                                start_proc = True
                                restarted = True
                            elif f"{i+1}th_price_proc" not in self.websocket_proc_dict:
                                self.websocket_logger.info(f"[BINANCE USD-M]{i+1}th_price_proc is not in self.websocket_proc_dict. starting..")
                                start_proc = True
                            if start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                symbol_list = self.sliced_symbol_list[i]
                                self.websocket_proc_dict[f"{i+1}th_price_proc"] = Process(target=self.price_websocket, args=(self.bookticker_dict, self.ticker_dict, symbol_list, error_event), daemon=True)
                                self.websocket_symbol_dict[f"{i+1}th_price_symbol"] = symbol_list
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].start()
                                self.websocket_logger.info(f"[BINANCE USD-M]started {i+1}th_price_proc websocket..")
                                if restarted:
                                    content = f"handle_price_procs|[BINANCE USD-M]{i+1}th_price_proc has been restarted. alive status: {self.websocket_proc_dict[f'{i+1}th_price_proc'].is_alive()}"
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                time.sleep(0.5)

                        if "liquidation_proc" in self.websocket_proc_dict and not self.websocket_proc_dict["liquidation_proc"].is_alive():
                            content = f"handle_price_procs|[BINANCE USD-M]liquidation_proc has died. terminating and restarting.."
                            self.websocket_logger.error(content)
                            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                            self.websocket_proc_dict["liquidation_proc"].terminate()
                            error_event = Event()
                            self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                            self.websocket_proc_dict["liquidation_proc"].start()
                            content = f"handle_price_procs|liquidation_proc has been restarted. alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}"
                            self.websocket_logger.info(f"[BINANCE USD-M]restarted liquidation_proc websocket alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}")
                            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        elif "liquidation_proc" not in self.websocket_proc_dict:
                            self.websocket_logger.info(f"[BINANCE USD-M]liquidation_proc is not in self.websocket_proc_dict. starting..")
                            error_event = Event()
                            self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                            self.websocket_proc_dict["liquidation_proc"].start()
                            self.websocket_logger.info(f"[BINANCE USD-M]started liquidation_proc websocket proc..")
                except Exception as e:
                    self.websocket_logger.error(f"handle_price_procs|{traceback.format_exc()}")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"Binance USD-M Websocket|handle_price_procs", content=e, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(2)
                time.sleep(0.25)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = "[BINANCE USD-M]websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BINANCE USD-M]{key} status: {value.is_alive()}\n"
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
        self.websocket_logger.info(f"[BINANCE USD-M]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info("[BINANCE USD-M]started monitor_shared_symbol_change..")
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
                        content = f"monitor_shared_symbol_change|[BINANCE USD-M]USD-M FUTURES shared symbol changed. deleted: {deleted_symbols}, added: {added_symbols}"
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        for each_symbol in deleted_symbols:
                            # remove deleted symbol from upbit_ticker_dict and upbit_orderbook_dict
                            try:
                                del self.bookticker_dict[each_symbol]
                            except Exception:
                                pass
                            try:
                                del self.ticker_dict[each_symbol]
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
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"started monitor_websocket_last_update..")
        while True:
            try:
                time.sleep(loop_time_secs)
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)
                bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)
                for i in range(self.proc_n):
                    terminate_flag = False
                    allocated_symbol_list = self.sliced_symbol_list[i]
                    # check ticker dict's last update
                    allocated_ticker_df = ticker_df[ticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE USD-M]{i+1}th_price_proc has no ticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update'].max()
                    allocated_bookticker_df = bookticker_df[bookticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_bookticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE USD-M]{i+1}th_price_proc has no bookticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    bookticker_last_update = allocated_bookticker_df['last_update'].max()
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.now() - ticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc ticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if (datetime.datetime.now() - bookticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc bookticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if terminate_flag is True:
                        content = f"monitor_websocket_last_update|Restarting Websocket.. {i+1}th_price_proc will be terminated."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
            except Exception as e:
                content = f"monitor_websocket_last_update|[BINANCE USD-M]{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        binance_ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df.loc[:, ['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_merged_df = binance_merged_df.merge(self.info_dict['binance_usd_m_info_df'][['symbol','base_asset','quote_asset']], left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df

##############################################################################################################################

class BinanceCOINMWebsocket:
    def __init__(self, admin_id, node, proc_n, get_binance_coinm_symbol_list, register_monitor_msg, info_dict, logging_dir):
        self.websocket_logger = KimpBotLogger("binance_coinm_websocket", logging_dir).logger
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.info_dict = info_dict
        self.get_symbol_list = get_binance_coinm_symbol_list
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        manager = Manager()
        self.bookticker_dict = manager.dict()
        self.ticker_dict = manager.dict()

        self.proc_n = proc_n
        self.before_symbol_list = self.get_symbol_list()
        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.liquidation_list = manager.list()
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self._start_websocket()
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()

    def __del__(self):
        self.terminate_websocket()

    # For fetching ticker, bookticker data
    def price_websocket(self, bookticker_dict, ticker_dict, symbol_list, error_event):
        def handle_coinm_bookticker_streams(msg):
            try:
                # event_type = msg['stream']
                # print(msg['data']) # test
                # if msg['data']['s'] == 'ETHUSDT': # test
                #     print(msg['data']['T']) # test
                bookticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_coinm_bookticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        def handle_coinm_ticker_streams(msg):
            try:
                ticker_dict[msg['data']['s']] = {**msg['data'], "last_update": datetime.datetime.now()}
            except Exception:
                self.websocket_logger.error(f"handle_coinm_ticker_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if symbol_list != []:
            coinm_bookticker_list = [x.lower()+'@bookTicker' for x in symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_coinm_bookticker_streams, streams=coinm_bookticker_list, futures_type=FuturesType.COIN_M)
            coinm_ticker_list = [x.lower()+'@ticker' for x in symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_coinm_ticker_streams, streams=coinm_ticker_list, futures_type=FuturesType.COIN_M)
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    # For fetching liquidation data
    def liquidation_websocket(self, liquidation_list, error_event):
        self.websocket_logger.info("started liquidation_websocket for COIN-M..")
        def handle_coinm_liquidation_streams(msg):
            try:
                if len(liquidation_list) > 1000:
                    liquidation_list.pop(0)
                # Filtering can be applied later.
                liquidation_list.append(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_coinm_liquidation_streams|{traceback.format_exc()}, msg:{msg}")
                error_event.set()
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        twm.start_futures_multiplex_socket(callback=handle_coinm_liquidation_streams, streams=['!forceOrder@arr'], futures_type=FuturesType.COIN_M)
        # twm.join()
        while not error_event.is_set():
            time.sleep(0.1)
        twm.stop()

    # def binance_kline_websocket(self, kline_dict, symbol_list, error_event):
    #     self.websocket_logger.info("started binance_kline_websocket for COIN-M..")
    #     def handle_kline_streams(msg):
    #         try:
    #             symbol = msg['data']['s']
    #             if msg['data']['k']['x'] == True:
    #                 kline_dict[symbol].put(msg['data'])
    #         except Exception:
    #             self.websocket_logger.error(f"handle_kline_streams|{traceback.format_exc()}, msg:{msg}")
    #             error_event.set()
    #     twm = ThreadedWebsocketManager()
    #     twm.daemon = True
    #     twm.start()
    #     if symbol_list != []:
    #         coinm_kline_list = []
    #         for kline_type in self.binance_kline_type_list:
    #             coinm_kline_list += [x.lower()+f'@kline_{kline_type}' for x in symbol_list]
    #         twm.start_futures_multiplex_socket(callback=handle_kline_streams, streams=coinm_kline_list, futures_type=FuturesType.COIN_M)
    #     # twm.join()
    #     while not error_event.is_set():
    #         time.sleep(0.1)
    #     twm.stop()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_webscoket is False:
                        for i in range(self.proc_n):
                            # Check if the process exists and is alive
                            start_proc = False
                            restarted = False
                            if f"{i+1}th_price_proc" in self.websocket_proc_dict and not self.websocket_proc_dict[f"{i+1}th_price_proc"].is_alive():
                                content = f"handle_price_procs|[BINANCE COIN-M]{i+1}th_price_proc has died. terminating and restarting.."
                                self.websocket_logger.error(content)
                                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                                start_proc = True
                                restarted = True
                            elif f"{i+1}th_price_proc" not in self.websocket_proc_dict:
                                self.websocket_logger.info(f"[BINANCE COIN-M]{i+1}th_price_proc is not in self.websocket_proc_dict. starting..")
                                start_proc = True
                            if start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                symbol_list = self.sliced_symbol_list[i]
                                self.websocket_proc_dict[f"{i+1}th_price_proc"] = Process(target=self.price_websocket, args=(self.bookticker_dict, self.ticker_dict, symbol_list, error_event), daemon=True)
                                self.websocket_symbol_dict[f"{i+1}th_price_symbol"] = symbol_list
                                self.websocket_proc_dict[f"{i+1}th_price_proc"].start()
                                self.websocket_logger.info(f"[BINANCE COIN-M]started {i+1}th_price_proc websocket proc..")
                                if restarted:
                                    content = f"handle_price_procs|[BINANCE COIN-M]{i+1}th_price_proc has been restarted. alive status: {self.websocket_proc_dict[f'{i+1}th_price_proc'].is_alive()}"
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                                time.sleep(0.5)

                        if "liquidation_proc" in self.websocket_proc_dict and not self.websocket_proc_dict["liquidation_proc"].is_alive():
                            content = f"handle_price_procs|[BINANCE COIN-M]liquidation_proc has died. terminating and restarting.."
                            self.websocket_logger.error(content)
                            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                            self.websocket_proc_dict["liquidation_proc"].terminate()
                            error_event = Event()
                            self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                            self.websocket_proc_dict["liquidation_proc"].start()
                            content = f"handle_price_procs|liquidation_proc has been restarted. alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}"
                            self.websocket_logger.info(f"[BINANCE COIN-M]restarted liquidation_proc websocket proc.. alive status: {self.websocket_proc_dict['liquidation_proc'].is_alive()}")
                            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        elif "liquidation_proc" not in self.websocket_proc_dict:
                            self.websocket_logger.info(f"[BINANCE COIN-M]liquidation_proc is not in self.websocket_proc_dict. starting..")
                            error_event = Event()
                            self.websocket_proc_dict["liquidation_proc"] = Process(target=self.liquidation_websocket, args=(self.liquidation_list, error_event), daemon=True)
                            self.websocket_proc_dict["liquidation_proc"].start()
                            self.websocket_logger.info(f"[BINANCE COIN-M]started liquidation_proc websocket proc..")
                except Exception as e:
                    self.websocket_logger.error(f"handle_price_procs|{traceback.format_exc()}")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"Binance COIN-M Websocket|handle_price_procs", content=e, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(2)
                time.sleep(0.25)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = "[BINANCE COIN-M]websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BINANCE COIN-M]{key} status: {value.is_alive()}\n"
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
        self.websocket_logger.info(f"[BINANCE COIN-M]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info("[BINANCE COIN-M]started monitor_shared_symbol_change..")
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
                        content = f"monitor_shared_symbol_change|[BINANCE COIN-M] FUTURES shared symbol changed. deleted: {deleted_symbols}, added: {added_symbols}"
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        for each_symbol in deleted_symbols:
                            # remove deleted symbol from upbit_ticker_dict and upbit_orderbook_dict
                            try:
                                del self.bookticker_dict[each_symbol]
                            except Exception:
                                pass
                            try:
                                del self.ticker_dict[each_symbol]
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
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"started monitor_websocket_last_update..")
        while True:
            try:
                time.sleep(loop_time_secs)
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)
                bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)
                for i in range(self.proc_n):
                    terminate_flag = False
                    allocated_symbol_list = self.sliced_symbol_list[i]
                    # check ticker dict's last update
                    allocated_ticker_df = ticker_df[ticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE COIN-M]{i+1}th_price_proc has no ticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update'].max()
                    allocated_bookticker_df = bookticker_df[bookticker_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_bookticker_df) == 0:
                        content = f"monitor_websocket_last_update|[BINANCE COIN-M]{i+1}th_price_proc has no bookticker_dict data. Restarting Websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
                        continue
                    bookticker_last_update = allocated_bookticker_df['last_update'].max()
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.now() - ticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc ticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if (datetime.datetime.now() - bookticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        terminate_flag = True
                        content = f"monitor_websocket_last_update|{i+1}th_price_proc bookticker_dict's last update is older than {update_threshold_mins} mins."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    if terminate_flag is True:
                        content = f"monitor_websocket_last_update|Restarting Websocket.. {i+1}th_price_proc will be terminated."
                        self.websocket_logger.error(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_price_proc"].terminate()
            except Exception as e:
                content = f"monitor_websocket_last_update|[BINANCE COIN-M]{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        binance_ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(dict(self.bookticker_dict)).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df.loc[:, ['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_merged_df = binance_merged_df.merge(self.info_dict['binance_coin_m_info_df'][['symbol','base_asset','quote_asset']], left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df