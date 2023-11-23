from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import numpy as np
import traceback
import websocket
import json
import datetime
import time
import _pickle as pickle
# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_connector import InitRedis

class BithumbWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, register_monitor_msg, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.url = "wss://pubwss.bithumb.com/pub/ws"
        self.register_monitor_msg = register_monitor_msg
        self.get_symbol_list = get_symbol_list
        self.websocket_logger = KimpBotLogger("bithumb_websocket", logging_dir).logger
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
        self.redis_client_db1 = InitRedis(db=1)
        self._start_websocket()
        while True:
            if self.ticker_dict.values() == [] or self.orderbook_dict.values() == []:
                self.websocket_logger.info(f"[BITHUMB SPOT]waiting for websocket data to be loaded..")
                time.sleep(2)
            else:
                break
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()

    def __del__(self):
        self.terminate_websocket()

    def bithumb_websocket(self, result_dict, data, error_event, data_name):
        def on_message(ws, message):
            if error_event.is_set():
                ws.close()
                raise Exception("bithumb_websocket|error_event is set. closing websocket..")
            message_dict = json.loads(message)
            # print(message_dict) # TEST
            if 'content' in message_dict.keys():
                result_dict[message_dict['content']['symbol']] = {**message_dict['content'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp()*1000000)}
                # self.redis_client_db1.set_data(f"INFO_CORE|BITHUMB_SPOT|{data_name}|{message_dict['content']['symbol']}", json.dumps({**message_dict['content'], "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1000000)}))
                # self.redis_client_db1.set_data(f"INFO_CORE|BITHUMB_SPOT|{data_name}", pickle.dumps(dict(result_dict)))

        def on_error(ws, error):
            # print(f'bithumb_websocket on_error executed!')
            # print(error)
            self.websocket_logger.error(f'bithumb_websocket|bithumb_websocket on_error executed!\n Error: {error}')

        def on_close(ws, close_status_code, close_msg):
            # print(f"\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")
            self.websocket_logger.info(f"bithumb_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")
            pass # TEST

        def on_open(ws):
            # print(f'bithumb_websocket started')
            self.websocket_logger.info(f'bithumb_websocket|bithumb_websocket started')
            ws.send(json.dumps(data))

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(self.url,
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
        ws.run_forever(ping_interval=30)

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
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                                self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.websocket_logger.info(f"{i+1}th bithumb ticker websocket does not exist. starting..")
                                self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_data = {"type": "ticker", "symbols": self.sliced_symbols_list[i], "tickTypes": ["24H"]}
                                ticker_proc = Process(target=self.bithumb_websocket, args=(self.ticker_dict, ticker_data, error_event, 'ticker'), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"] = ticker_proc
                                ticker_proc.start()
                                if ticker_restarted:
                                    content = f"restarted {i+1}th Bithumb ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'bithumb ticker websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)

                            time.sleep(0.5)
                            orderbook_start_proc = False
                            orderbook_restarted = False
                            if f"{i+1}th_orderbook_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
                                self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_orderbook_proc terminated.")
                            elif f"{i+1}th_orderbook_proc" not in self.websocket_proc_dict.keys():
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"{i+1}th bithumb orderbook websocket does not exist. starting..")
                                self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_orderbook_proc started.")
                            if orderbook_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_data = {"type": "orderbooksnapshot", "symbols": self.sliced_symbols_list[i]}
                                orderbook_proc = Process(target=self.bithumb_websocket, args=(self.orderbook_dict, orderbook_data, error_event, 'orderbook'), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"] = orderbook_proc
                                orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"restarted {i+1}th bithumb orderbook websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                                    self.websocket_logger.info(f"bithumb_orderbook_ticker_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'bithumb orderbook websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"handle_price_procs", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
                    time.sleep(1)
                time.sleep(0.5)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        self.stop_restart_webscoket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[BITHUMB SPOT]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False
    
    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = "[BITHUMB SPOT]bithumb websocket proc is not running."
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[BITHUMB SPOT]{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info("[BITHUMB SPOT]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                restart_websockets = False
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    restart_websockets = True
                    deleted_spot_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_spot_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[BITHUMB SPOT]SPOT shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.websocket_logger.info(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                    for each_spot_shared_symbol in deleted_spot_shared_symbol:
                        # remove deleted symbol from bithumb_ticker_dict and bithumb_orderbook_dict
                        try:
                            del self.ticker_dict[each_spot_shared_symbol]
                            # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|BITHUMB_SPOT|ticker|{each_spot_shared_symbol}")
                        except Exception:
                            pass
                        try:
                            del self.orderbook_dict[each_spot_shared_symbol]
                            # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|BITHUMB_SPOT|orderbook|{each_spot_shared_symbol}")
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
        time.sleep(10)
        self.websocket_logger.info(f"[BITHUMB SPOT]started monitor_websocket_last_update..")
        while True:
            time.sleep(loop_time_secs)
            try:
                ticker_df = pd.DataFrame(dict(self.ticker_dict)).T.reset_index()
                orderbook_df = pd.DataFrame(dict(self.orderbook_dict)).T.reset_index()
                for i in range(self.proc_n):
                    allocated_symbol_list = self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"]
                    # check ticker dict's last_update
                    allocated_ticker_df = ticker_df[ticker_df['symbol'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc has no ticker_dict data. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update_timestamp'].max()
                    # check orderbook dict's last_update
                    allocated_orderbook_df = orderbook_df[orderbook_df['symbol'].isin(allocated_symbol_list)]
                    if len(allocated_orderbook_df) == 0:
                        content = f"monitor_websocket_last_update|{i+1}th_orderbook_proc has no orderbook_dict data. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
                        continue
                    orderbook_last_update = allocated_orderbook_df['last_update_timestamp'].max()
                    # If the last update is older than update_threshold_mins, restart websocket
                    if (datetime.datetime.utcnow().timestamp() - ticker_last_update/1000000) > update_threshold_mins*60:
                        slow_ticker_symbol = allocated_ticker_df[allocated_ticker_df['last_update_timestamp'] == ticker_last_update]['symbol'].values[0]
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc {slow_ticker_symbol} last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                    if (datetime.datetime.utcnow().timestamp() - orderbook_last_update/1000000) > update_threshold_mins*60:
                        slow_orderbook_symbol = allocated_orderbook_df[allocated_orderbook_df['last_update_timestamp'] == orderbook_last_update]['symbol'].values[0]
                        content = f"monitor_websocket_last_update|{i+1}th_orderbook_proc {slow_orderbook_symbol} last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
            except Exception as e:
                content = f"monitor_websocket_last_update|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        orderbook_df = pd.DataFrame(self.orderbook_dict.values())
        ticker_df = pd.DataFrame(self.ticker_dict.values())
        orderbook_df['best_ask'] = orderbook_df['asks'].apply(lambda x: x[0][0])
        orderbook_df['best_bid'] = orderbook_df['bids'].apply(lambda x: x[0][0])
        merged_df = orderbook_df.merge(ticker_df[['symbol','chgRate','value']], on='symbol', how='inner')
        merged_df[['base_asset', 'quote_asset']] = merged_df['symbol'].str.split('_', expand=True)
        merged_df = merged_df.rename(columns={'value':'atp24h', 'chgRate':'scr', 'best_ask':'ap', 'best_bid':'bp'})
        merged_df.loc[:, ['scr','atp24h','ap','bp']] = merged_df.loc[:, ['scr','atp24h','ap','bp']].astype(float)
        merged_df['tp'] = np.nan
        return merged_df
