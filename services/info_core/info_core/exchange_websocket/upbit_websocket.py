from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import traceback
import websocket
import json
import time
import _pickle as pickle
# set directory to upper directory
import os
import sys
from loggers.logger import InfoCoreLogger
from exchange_websocket.heartbeat import (
    has_recent_market_ready,
    is_process_heartbeat_stale,
    touch_market_ready,
    touch_process_heartbeat,
)
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 100

# Move the upbit_websocket function outside the class
def upbit_websocket(stream_data_type, url, data, error_event, proc_name, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Reinitialize the logger inside the function
    logger = InfoCoreLogger("upbit_websocket", logging_dir).logger
    logger.info(f"[UPBIT] {stream_data_type} websocket started for {data[1]['codes']}")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance
    market_code = "UPBIT_SPOT"

    def on_message(ws, message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        try:
            if error_event.is_set():
                ws.close()
                raise Exception("upbit_websocket|error_event is set. closing websocket..")
            message_dict = json.loads(message)
            # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
            msg_ts_ms = message_dict.get('tms')  # Upbit uses 'tms' for timestamp
            if msg_ts_ms:
                current_ts_ms = int(time.time() * 1000)
                if current_ts_ms - msg_ts_ms > MAX_MESSAGE_DELAY_MS:
                    return  # Drop stale message
            timestamp_us = int(time.time() * 1_000_000)
            local_redis.update_exchange_stream_data(
                stream_data_type,
                market_code,
                message_dict['cd'],
                {**message_dict, 'last_update_timestamp': timestamp_us},
            )
            touch_market_ready(local_redis, market_code, stream_data_type, timestamp_us)
            touch_process_heartbeat(local_redis, market_code, stream_data_type, proc_name, timestamp_us)
        except Exception as e:
            logger.error(f"upbit_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set() # Signal error

    def on_error(ws, error):
        logger.error(f'upbit_websocket|on_error executed!\nError: {error}')
        # Optionally, you can register the error with monitor_msg if needed
        acw_api.create_message_thread(admin_id, 'upbit websocket error', str(error))
        error_event.set() # Signal error

    def on_close(ws, close_status_code, close_msg):
        logger.info(
            f"upbit_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}"
        )

    def on_open(ws):
        logger.info(f'upbit_websocket|upbit_websocket for {stream_data_type} started')
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
        logger.info(f"[UPBIT] {stream_data_type} websocket started monitoring inactivity... for {data[1]['codes']}...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(f"[UPBIT] {stream_data_type} websocket has been inactive for {inactivity_time_secs} seconds for {data[1]['codes']}. Closing websocket...")
                try:
                    acw_api.create_message_thread(admin_id, f"[UPBIT] {stream_data_type} websocket Inactivity", f"[UPBIT] {stream_data_type} websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                except Exception as e:
                    logger.error(f"[UPBIT] {stream_data_type} websocket Inactivity|{traceback.format_exc()}")
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
        logger.error(f"upbit_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")
        
    if error_event.is_set():
        raise Exception("upbit_websocket|error_event is set. closing websocket..")
class UpbitWebsocket:
    def __init__(self, admin_id, node, proc_n, get_upbit_symbol_list, acw_api, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_upbit_symbol_list = get_upbit_symbol_list
        self.logging_dir = logging_dir  # Store logging_dir for child processes
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", "UPBIT_SPOT")
        self.local_redis.delete_all_exchange_stream_data("orderbook", "UPBIT_SPOT")
        self.url = "wss://api.upbit.com/websocket/v1"
        self.logger = InfoCoreLogger("upbit_websocket", logging_dir).logger
        self.proc_n = proc_n
        self.before_upbit_symbols_list = self.get_upbit_symbol_list()
        self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self._start_websocket()

        while True:
            if not has_recent_market_ready(
                self.local_redis,
                "UPBIT_SPOT",
                ("ticker", "orderbook"),
            ):
                self.logger.info("[UPBIT SPOT] Waiting for websocket data to be loaded...")
                time.sleep(2)
            else:
                break

        self.monitor_shared_symbol_change_thread = Thread(
            target=self.monitor_shared_symbol_change, daemon=True
        )
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_stale_data_per_proc_thread = Thread(
            target=self.monitor_stale_data_per_proc, daemon=True
        )
        self.monitor_stale_data_per_proc_thread.start()

    def __del__(self):
        self.terminate_websocket()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if not self.stop_restart_websocket:
                        # Check whether UPBIT_SPOT/KRW is in maintenance
                        if fetch_market_servercheck("UPBIT_SPOT/KRW"):
                            self.logger.info("[UPBIT SPOT] UPBIT_SPOT is in maintenance. Skipping (re)starting websockets..")
                            time.sleep(1)
                            continue
                        for i in range(self.proc_n):
                            index = i + 1
                            # Handle ticker process
                            ticker_proc_name = f"{index}th_ticker_proc"
                            ticker_start_proc = False
                            ticker_restarted = False

                            if (
                                ticker_proc_name in self.websocket_proc_dict
                                and not self.websocket_proc_dict[ticker_proc_name].is_alive()
                            ):
                                ticker_start_proc = True
                                ticker_restarted = True
                                self.websocket_proc_dict[ticker_proc_name].terminate()
                                self.websocket_proc_dict[ticker_proc_name].join()
                                self.logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_ticker_proc terminated."
                                )
                            elif ticker_proc_name not in self.websocket_proc_dict:
                                ticker_start_proc = True
                                self.logger.info(
                                    f"{index}th Upbit ticker websocket does not exist. Starting..."
                                )
                                self.logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_ticker_proc started."
                                )

                            if ticker_start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{index}th_ticker_symbol"] = self.sliced_upbit_symbols_list[i]
                                upbit_ticker_data = [
                                    {"ticket": "kp_info_loader"},
                                    {"type": "ticker", "codes": self.sliced_upbit_symbols_list[i]},
                                    {"format": "SIMPLE"}
                                ]
                                upbit_ticker_proc = Process(
                                    target=upbit_websocket,  # Module-level function
                                    args=(
                                        "ticker",
                                        self.url,
                                        upbit_ticker_data,
                                        error_event,
                                        ticker_proc_name,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[ticker_proc_name] = upbit_ticker_proc
                                upbit_ticker_proc.start()
                                if ticker_restarted:
                                    content = (
                                        f"restarted {index}th Upbit ticker websocket.. "
                                        f"alive state: {upbit_ticker_proc.is_alive()}"
                                    )
                                    self.logger.info(
                                        f"upbit_orderbook_ticker_websocket|{content}"
                                    )
                                    self.acw_api.create_message_thread(
                                        self.admin_id, 'upbit ticker websocket restart', content
                                    )

                            time.sleep(0.5)

                            # Handle orderbook process
                            orderbook_proc_name = f"{index}th_orderbook_proc"
                            orderbook_start_proc = False
                            orderbook_restarted = False

                            if (
                                orderbook_proc_name in self.websocket_proc_dict
                                and not self.websocket_proc_dict[orderbook_proc_name].is_alive()
                            ):
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[orderbook_proc_name].terminate()
                                self.websocket_proc_dict[orderbook_proc_name].join()
                                self.logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_orderbook_proc terminated."
                                )
                            elif orderbook_proc_name not in self.websocket_proc_dict:
                                orderbook_start_proc = True
                                self.logger.info(
                                    f"{index}th Upbit orderbook websocket does not exist. Starting..."
                                )
                                self.logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_orderbook_proc started."
                                )

                            if orderbook_start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{index}th_orderbook_symbol"] = self.sliced_upbit_symbols_list[i]
                                upbit_orderbook_data = [
                                    {"ticket": "kp_info_loader"},
                                    {
                                        "type": "orderbook",
                                        "codes": [x + '.1' for x in self.sliced_upbit_symbols_list[i]]
                                    },
                                    {"format": "SIMPLE"}
                                ]
                                upbit_orderbook_proc = Process(
                                    target=upbit_websocket,  # Module-level function
                                    args=(
                                        "orderbook",
                                        self.url,
                                        upbit_orderbook_data,
                                        error_event,
                                        orderbook_proc_name,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id,
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[orderbook_proc_name] = upbit_orderbook_proc
                                upbit_orderbook_proc.start()
                                if orderbook_restarted:
                                    content = (
                                        f"restarted {index}th Upbit orderbook websocket.. "
                                        f"alive state: {upbit_orderbook_proc.is_alive()}"
                                    )
                                    self.logger.info(
                                        f"upbit_orderbook_ticker_websocket|{content}"
                                    )
                                    self.acw_api.create_message_thread(
                                        self.admin_id,
                                        'upbit orderbook websocket restart',
                                        content
                                    )

                            time.sleep(0.5)
                    else:
                        time.sleep(1)
                except Exception:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.logger.error(content)
                    self.acw_api.create_message_thread(
                        self.admin_id, 'upbit websocket error', content
                    )
                    time.sleep(1)
                time.sleep(0.5)

        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.logger.info("[UPBIT SPOT] All websockets' events have been set.")
        self.price_proc_event_list = []
        
    def restart_websocket(self):
        self.terminate_websocket()
        time.sleep(1)
        self.stop_restart_websocket = False
    
    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = "[UPBIT SPOT]Upbit websocket proc is not running."
            if print_result:
                self.logger.info(print_text.rstrip())
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[UPBIT SPOT]{key} status: {value.is_alive()}\n"
            if print_result:
                self.logger.info(print_text.rstrip())
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.logger.info("[UPBIT SPOT]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_upbit_symbols_list = self.get_upbit_symbol_list()
                
                if sorted(self.before_upbit_symbols_list) != sorted(new_upbit_symbols_list):
                    deleted_spot_shared_symbol = [x for x in self.before_upbit_symbols_list if x not in new_upbit_symbols_list]
                    added_spot_shared_symbol = [x for x in new_upbit_symbols_list if x not in self.before_upbit_symbols_list]
                    content = f"monitor_shared_symbol_change|[UPBIT SPOT]SPOT shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.logger.info(content)
                    self.acw_api.create_message_thread(self.admin_id, 'monitor_shared_symbol_change', content)
                    
                    # Set the newer values to before values
                    self.before_upbit_symbols_list = new_upbit_symbols_list
                    # Set sliced values too
                    self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
                    # restart websockets
                    self.restart_websocket()
                    for each_spot_shared_symbol in deleted_spot_shared_symbol:
                        # remove deleted symbol from redis
                        try:
                            self.logger.info(f"monitor_shared_symbol_change|deleting {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("ticker", "UPBIT_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                        try:
                            self.logger.info(f"monitor_shared_symbol_change|deleting {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("orderbook", "UPBIT_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                                    
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, 'monitor_shared_symbol_change', content)
                
    def monitor_stale_data_per_proc(self, loop_time_secs=60, stale_threshold_secs=90):
        """
        Periodically checks if the slice of symbols for each process has not
        been updated within `stale_threshold_secs`. If *all* symbols in that
        slice are stale, forcefully kill only that process. The existing logic
        in `handle_price_procs()` will see the process is dead and restart it.

        :param loop_time_secs: how often to run the check (in seconds).
        :param stale_threshold_secs: how long to wait before deciding data is stale
        """
        self.logger.info("[UPBIT SPOT]started monitor_stale_data_per_proc..")
        while True:
            time.sleep(loop_time_secs)
            now_us = int(time.time() * 1_000_000)  # current time in microseconds
            
            try:
                # We'll iterate over each known process in `self.websocket_proc_dict`.
                # For each, we look up its symbol list in `self.websocket_symbol_dict`.
                for proc_name, proc in list(self.websocket_proc_dict.items()):

                    # If the process is already dead, skip it.
                    if not proc.is_alive():
                        continue

                    if "ticker_proc" in proc_name:
                        redis_stream_type = "ticker"
                    elif "orderbook_proc" in proc_name:
                        redis_stream_type = "orderbook"
                    else:
                        continue

                    if is_process_heartbeat_stale(
                        self.local_redis,
                        "UPBIT_SPOT",
                        redis_stream_type,
                        proc_name,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    ):
                        content = (
                            f"[UPBIT SPOT] {proc_name} => "
                            f"Heartbeat stale for > {stale_threshold_secs}s. "
                            f"Forcing process restart."
                        )
                        self.logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)

                        # Force kill the process
                        self.logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()

                        # The handle_price_procs() loop will detect it is dead
                        # and restart it automatically. Let's sleep a bit
                        time.sleep(60)

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
