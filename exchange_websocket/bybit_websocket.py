from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import traceback
from pybit.unified_trading import WebSocket
import json
import datetime
import time
# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger
from exchange_websocket.utils import list_slice

class BybitWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir=None):
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.get_symbol_list = get_symbol_list
        self.info_dict = info_dict
        self.websocket_logger = KimpBotLogger(f"bybit_{self.market_type.lower()}_websocket", logging_dir).logger
        manager = Manager()
        self.ticker_dict = manager.dict()
        self.orderbook_dict = manager.dict()
        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self._start_websocket()
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()

    def init_ticker_websocket(self, ticker_dict, symbol_list, error_event):
        def cut_list(list):
            return [list[i:i + 10] for i in range(0, len(list), 10)]
        if self.market_type == "SPOT":
            channel_type = 'spot'
        elif self.market_type == "USD_M":
            channel_type = "linear"
        elif self.market_type == "COIN_M":
            channel_type = "inverse"
        else:
            raise Exception(f"market_type {self.market_type} is not supported.")

        ws = WebSocket(
            testnet=False,
            channel_type=channel_type
        )

        def handle_message(message):
            if error_event.is_set():
                ws.exit()
                return
            if 'data' in message.keys():
                ticker_dict[message['data']['symbol']] = {**message['data'], 'last_update': datetime.datetime.utcnow()}
        
        if self.market_type == "SPOT":
            for symbol_bunch in cut_list(symbol_list):
                ws.ticker_stream(
                    symbol=symbol_bunch,
                    callback=handle_message
                )
                time.sleep(0.1)
        else:
            ws.ticker_stream(
                symbol=symbol_list,
                callback=handle_message
            )
        # idle
        while error_event.is_set() is False:
            time.sleep(1)

    def init_orderbook_websocket(self, orderbook_dict, symbol_list, error_event):
        def cut_list(list):
            return [list[i:i + 10] for i in range(0, len(list), 10)]
        if self.market_type == "SPOT":
            channel_type = 'spot'
        elif self.market_type == "USD_M":
            channel_type = "linear"
        elif self.market_type == "COIN_M":
            channel_type = "inverse"
        else:
            raise Exception(f"market_type {self.market_type} is not supported.")

        ws = WebSocket(
            testnet=False,
            channel_type=channel_type
        )

        def handle_message(message):
            if error_event.is_set():
                ws.exit()
                return
            if 'data' in message.keys():
                orderbook_dict[message['data']['s']] = {**message['data'], 'last_update': datetime.datetime.utcnow()}

        if self.market_type == "SPOT":
            for symbol_bunch in cut_list(symbol_list):
                ws.orderbook_stream(
                    depth=1,
                    symbol=symbol_bunch,
                    callback=handle_message
                )
                time.sleep(0.1)
        else:
            ws.orderbook_stream(
                depth=1,
                symbol=symbol_list,
                callback=handle_message
            )
        # idle
        while error_event.is_set() is False:
            time.sleep(1)
    
    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_webscoket is False:
                        for i in range(self.proc_n):
                            ticker_start_proc = False
                            ticker_restarted = False
                            if f"{i+1}th_ticker_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_ticker_proc"].is_alive():
                                ticker_start_proc = True
                                ticker_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                                self.websocket_logger.info(f"bybit_ticker_websocket|{i+1}th bybit_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Bybit ticker websocket does not exist. starting..")
                                self.websocket_logger.info(f"bybit_ticker_websocket|{i+1}th bybit_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_proc = Process(target=self.init_ticker_websocket, args=(self.ticker_dict, self.sliced_symbols_list[i], error_event), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"] = ticker_proc
                                ticker_proc.start()
                                if ticker_restarted:
                                    content = f"restarted {i+1}th ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.websocket_logger.info(f"ticker_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', f'BYBIT {self.market_type} ticker websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
                            time.sleep(0.5)
                            orderbook_start_proc = False
                            orderbook_restarted = False
                            if f"{i+1}th_orderbook_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                                self.websocket_logger.info(f"bybit_orderbook_websocket|{i+1}th bybit_orderbook_proc terminated.")
                            elif f"{i+1}th_orderbook_proc" not in self.websocket_proc_dict.keys():
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Bybit orderbook websocket does not exist. starting..")
                                self.websocket_logger.info(f"bybit_orderbook_websocket|{i+1}th bybit_orderbook_proc started.")
                            if orderbook_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_proc = Process(target=self.init_orderbook_websocket, args=(self.orderbook_dict, self.sliced_symbols_list[i], error_event), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"] = orderbook_proc
                                orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"restarted {i+1}th orderbook websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                                    self.websocket_logger.info(f"orderbook_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', f'BYBIT {self.market_type} orderbook websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[BYBIT {self.market_type}]handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(1)
                time.sleep(0.5)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        self.stop_restart_webscoket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[BYBIT {self.market_type}]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False
    
    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = f"[BYBIT {self.market_type}]websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BYBIT {self.market_type}]{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info(f"[BYBIT {self.market_type}]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                restart_websockets = False
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    restart_websockets = True
                    deleted_spot_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_spot_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[BYBIT {self.market_type}]shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.websocket_logger.info(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                    for each_shared_symbol in deleted_spot_shared_symbol:
                        # remove deleted symbol from ticker_dict
                        try:
                            del self.ticker_dict[each_shared_symbol]
                        except Exception:
                            pass
                
                if restart_websockets is True:
                    # Set the newer values to before values
                    self.before_symbols_list = new_symbols_list
                    # Set sliced values too
                    self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
                    # terminate websockets
                    self.terminate_websocket()
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"[BYBIT {self.market_type}]started monitor_websocket_last_update..")
        while True:
            time.sleep(loop_time_secs)
            try:
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index()
                for i in range(self.proc_n):
                    allocated_symbol_list = self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"]
                    # check ticker dict's last_update
                    allocated_ticker_df = ticker_df[ticker_df['symbol'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc has no ticker_dict data. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update'].max()
                    # check orderbook dict's last_update
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.utcnow() - ticker_last_update).total_seconds() / 60 > update_threshold_mins:
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()

                orderbook_df = pd.DataFrame(dict(self.orderbook_dict)).T.reset_index()
                for i in range(self.proc_n):
                    allocated_symbol_list = self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"]
                    # check orderbook dict's last_update
                    allocated_orderbook_df = orderbook_df[orderbook_df['s'].isin(allocated_symbol_list)]
                    if len(allocated_orderbook_df) == 0:
                        content = f"monitor_websocket_last_update|{i+1}th_orderbook_proc has no orderbook_dict data. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                        continue
                    orderbook_last_update = allocated_orderbook_df['last_update'].max()
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.utcnow() - orderbook_last_update).total_seconds() / 60 > update_threshold_mins:
                        content = f"monitor_websocket_last_update|{i+1}th_orderbook_proc last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
            except Exception as e:
                content = f"monitor_websocket_last_update|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[BYBIT {self.market_type}] monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        ticker_df = pd.DataFrame(self.ticker_dict.values())
        orderbook_df = pd.DataFrame(self.orderbook_dict.values())
        merged_df = ticker_df.merge(orderbook_df, left_on='symbol', right_on='s', how='inner')
        merged_df = merged_df.merge(self.info_dict[f'bybit_{self.market_type.lower()}_info_df'][['symbol','base_asset','quote_asset']], on='symbol', how='inner')
        merged_df.loc[:, 'b'] = merged_df['b'].apply(lambda x: x[0][0])
        merged_df.loc[:, 'a'] = merged_df['a'].apply(lambda x: x[0][0])
        merged_df.loc[:, 'price24hPcnt'] = merged_df['price24hPcnt'].astype(float) * 100
        if self.market_type == "COIN_M":
            merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'volume24h':'atp24h'})
        else:
            merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'turnover24h':'atp24h'})
        merged_df.loc[:, ['tp','ap','bp','scr','atp24h']] = merged_df[['tp','ap','bp','scr','atp24h']].astype(float)
        merged_df = merged_df[['symbol','base_asset','quote_asset','tp','bp','ap','scr','atp24h']]
        return merged_df

class BybitUSDMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir)

class BybitCOINMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, register_monitor_msg, market_type, info_dict, logging_dir)
        
