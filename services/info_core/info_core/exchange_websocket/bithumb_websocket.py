from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import numpy as np
import traceback
import websocket
import json
import time
import _pickle as pickle
# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import InfoCoreLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 100

# Move the bithumb_websocket function outside the class
def bithumb_websocket(stream_data_type, url, data, error_event, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Initialize logger inside the function
    logger = InfoCoreLogger(f"bithumb_websocket", logging_dir).logger
    logger.info(f"[BITHUMB {stream_data_type}]bithumb_websocket started for {data['symbols']}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance

    def on_message(ws, message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        try:
            if error_event.is_set():
                ws.close()
                raise Exception("bithumb_websocket|error_event is set. closing websocket..")
            message_dict = json.loads(message)
            if 'content' in message_dict.keys():
                content = message_dict['content']
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                # Bithumb uses 'datetime' field (Unix timestamp in milliseconds)
                msg_ts_ms = content.get('datetime')
                if msg_ts_ms:
                    current_ts_ms = int(time.time() * 1000)
                    if current_ts_ms - int(msg_ts_ms) > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message
                local_redis.update_exchange_stream_data(stream_data_type, "BITHUMB_SPOT", content['symbol'], {
                    **content,
                    "last_update_timestamp": int(time.time() * 1_000_000)
                })
        except Exception as e:
            logger.error(f"bithumb_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()  # Signal error

    def on_error(ws, error):
        logger.error(f'bithumb_websocket|on_error executed!\nError: {error}, traceback: {traceback.format_exc()}')
        error_event.set() # Add this line

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"bithumb_websocket|\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        logger.info(f'bithumb_websocket|bithumb_websocket for {stream_data_type} started')
        ws.send(json.dumps(data))

    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Monitoring function to check for inactivity
    def check_inactivity():
        logger.info(f"[BITHUMB {stream_data_type}]bithumb_websocket started monitoring inactivity... for {data['symbols']}...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(f"[BITHUMB {stream_data_type}]bithumb_websocket has been inactive for {inactivity_time_secs} seconds for {data['symbols']}. Closing websocket... and set error_event..")
                try:
                    acw_api.create_message_thread(admin_id, f"[BITHUMB {stream_data_type}]bithumb_websocket Inactivity", f"[BITHUMB {stream_data_type}]bithumb_websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                except Exception as e:
                    logger.error(f"[BITHUMB {stream_data_type}]bithumb_websocket|{traceback.format_exc()}")
                    
                # ---- THE CRUCIAL PART: EXPLICITLY CLOSE THE WEBSOCKET ----
                try:
                    ws.close()
                except Exception:
                    pass
                
                error_event.set()
                break
            time.sleep(1) # Check every 1 second
            
    # Start the monitoring thread
    monitor_thread = Thread(target=check_inactivity, daemon=True)
    monitor_thread.start()
    
    try:
        ws.run_forever(ping_interval=30, ping_timeout=10)
    except Exception as e:
        logger.error(f"bithumb_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")
    
    if error_event.is_set():
        raise Exception("bithumb_websocket|error_event is set. closing websocket..")
class BithumbWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.url = "wss://pubwss.bithumb.com/pub/ws"
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.logging_dir = logging_dir
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", "BITHUMB_SPOT")
        self.local_redis.delete_all_exchange_stream_data("orderbook", "BITHUMB_SPOT")
        self.logger = InfoCoreLogger("bithumb_websocket", logging_dir).logger
        manager = Manager()
        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self._start_websocket()
        while True:
            if (not self.local_redis.get_all_exchange_stream_data("ticker", "BITHUMB_SPOT") or
                not self.local_redis.get_all_exchange_stream_data("orderbook", "BITHUMB_SPOT")):
                self.logger.info(f"[BITHUMB SPOT]waiting for websocket data to be loaded..")
                time.sleep(2)
            else:
                break
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_stale_data_per_proc_thread = Thread(target=self.monitor_stale_data_per_proc, daemon=True)
        self.monitor_stale_data_per_proc_thread.start()

    def __del__(self):
        self.terminate_websocket()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_websocket is False:
                        # Check whether BITHUMB_SPOT/KRW is in maintenance
                        if fetch_market_servercheck("BITHUMB_SPOT/KRW"):
                            self.logger.info("[BITHUMB SPOT] BITHUMB_SPOT is in maintenance. Skipping (re)starting websockets..")
                            time.sleep(1)
                            continue
                        for i in range(self.proc_n):
                            ticker_start_proc = False
                            ticker_restarted = False
                            if f"{i+1}th_ticker_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_ticker_proc"].is_alive():
                                ticker_start_proc = True
                                ticker_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                                self.logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.logger.info(f"{i+1}th bithumb ticker websocket does not exist. starting..")
                                self.logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_data = {"type": "ticker", "symbols": self.sliced_symbols_list[i], "tickTypes": ["24H"]}
                                ticker_proc = Process(
                                    target=bithumb_websocket, # Module-level function
                                    args=(
                                        'ticker',
                                        self.url,
                                        ticker_data,
                                        error_event,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id
                                        ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"] = ticker_proc
                                ticker_proc.start()
                                if ticker_restarted:
                                    content = f"restarted {i+1}th Bithumb ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.logger.info(f"bithumb_orderbook_ticker_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, 'bithumb ticker websocket restart', content)
                                time.sleep(2)
                            time.sleep(0.5)
                            orderbook_start_proc = False
                            orderbook_restarted = False
                            if f"{i+1}th_orderbook_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
                                self.logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_orderbook_proc terminated.")
                            elif f"{i+1}th_orderbook_proc" not in self.websocket_proc_dict.keys():
                                orderbook_start_proc = True
                                self.logger.info(f"{i+1}th bithumb orderbook websocket does not exist. starting..")
                                self.logger.info(f"bithumb_orderbook_ticker_websocket|{i+1}th bithumb_orderbook_proc started.")
                            if orderbook_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_data = {"type": "orderbooksnapshot", "symbols": self.sliced_symbols_list[i]}
                                orderbook_proc = Process(
                                    target=bithumb_websocket,
                                    args=(
                                        'orderbook',
                                        self.url,
                                        orderbook_data,
                                        error_event,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id
                                        ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"] = orderbook_proc
                                orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"restarted {i+1}th bithumb orderbook websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                                    self.logger.info(f"bithumb_orderbook_ticker_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, 'bithumb orderbook websocket restart', content)
                                time.sleep(2)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.logger.error(content)
                    self.acw_api.create_message_thread(self.admin_id, 'handle_price_procs', content)
                    time.sleep(1)
                time.sleep(0.5)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.logger.info(f"[BITHUMB SPOT]all websockets' event has been set")
        self.price_proc_event_list = []
        
    def restart_websocket(self):
        self.terminate_websocket()
        time.sleep(1)
        self.stop_restart_websocket = False
    
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
        self.logger.info("[BITHUMB SPOT]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    deleted_spot_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_spot_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[BITHUMB SPOT]SPOT shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.logger.info(content)
                    self.acw_api.create_message_thread(self.admin_id, 'monitor_shared_symbol_change', content)
                    
                    # Set the newer values to before values
                    self.before_symbols_list = new_symbols_list
                    # Set sliced values too
                    self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
                    # restart websockets
                    self.restart_websocket()
                    for each_spot_shared_symbol in deleted_spot_shared_symbol:
                        # remove deleted symbol from bithumb_ticker_dict and bithumb_orderbook_dict
                        try:
                            self.logger.info(f"monitor_shared_symbol_change|deleting ticker data for {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("ticker", "BITHUMB_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                        try:
                            self.logger.info(f"monitor_shared_symbol_change|deleting orderbook data for {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("orderbook", "BITHUMB_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, 'monitor_shared_symbol_change', content)
                
    def monitor_stale_data_per_proc(self, loop_time_secs=60, stale_threshold_secs=90):
        """
        Periodically checks if the slice of symbols for each process
        has not been updated within `stale_threshold_secs`.
        If all symbols in that slice are stale, forcefully kill only that process.
        handle_price_procs() will then detect the process is dead and restart it.
        """
        self.logger.info("[BITHUMB SPOT]started monitor_stale_data_per_proc..")
        while True:
            time.sleep(loop_time_secs)
            now_us = int(time.time() * 1_000_000)  # current time in microseconds

            try:
                # For each known process in self.websocket_proc_dict:
                #   - If it's ticker_proc => check ticker data in Redis
                #   - If it's orderbook_proc => check orderbook data in Redis
                for proc_name, proc in list(self.websocket_proc_dict.items()):
                    # Skip if the process is already dead
                    if not proc.is_alive():
                        continue

                    # Determine if it's ticker or orderbook
                    if "ticker_proc" in proc_name:
                        # e.g. "1th_ticker_proc" => symbol key: "1th_ticker_symbol"
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "ticker"
                    elif "orderbook_proc" in proc_name:
                        # e.g. "1th_orderbook_proc" => symbol key: "1th_orderbook_symbol"
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "orderbook"
                    else:
                        # If there's any other type, skip or adapt logic
                        continue

                    symbol_list = self.websocket_symbol_dict.get(symbol_list_key, [])
                    if not symbol_list:
                        # If no symbols found for that process, skip
                        continue
                    
                    data = None
                    while data is None:
                        data = self.local_redis.get_all_exchange_stream_data(
                            redis_stream_type, f"BITHUMB_SPOT"
                        )
                        if data is None:
                            time.sleep(0.5)  # Add small delay to prevent busy waiting

                    # Check if all symbols are stale
                    stale_count = 0
                    for sym in symbol_list:
                        symbol_data = data.get(sym, {})
                        last_update_ts = symbol_data.get("last_update_timestamp")  # microseconds
                        if last_update_ts is None:
                            # If no timestamp, treat as stale
                            stale_count += 1
                            continue

                        diff_us = now_us - last_update_ts
                        if diff_us > stale_threshold_secs * 1_000_000:
                            # self.logger.info(f"Stale sym: {sym}, data: {symbol_data}")
                            stale_count += 1

                    if stale_count == len(symbol_list):
                        # All symbols are stale => kill process
                        content = (
                            f"[BITHUMB SPOT]{proc_name} => "
                            f"All {stale_count} symbols stale > {stale_threshold_secs}s. "
                            f"Forcing process restart."
                        )
                        self.logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)

                        self.logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()

                        # handle_price_procs() will detect it's dead and restart it.
                        time.sleep(60)
                    else:
                        self.logger.info(f"monitor_stale_data_per_proc|{proc_name} => {stale_count} symbols among {len(symbol_list)} symbols are stale for > {stale_threshold_secs}s.")

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[BITHUMB SPOT] monitor_stale_data_per_proc", content)
