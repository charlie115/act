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
from acw_common.websocket import get_stale_symbol_summary
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 100

# Standalone function for the websocket
def init_websocket(stream_data_type, url, data, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Initialize logger inside the function
    logger = InfoCoreLogger(f"okx_{market_type.lower()}_websocket", logging_dir).logger
    logger.info(f"[OKX {market_type}]init_websocket started for {data['args']}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance
    market_code = f"OKX_{market_type.upper()}"

    def on_message(ws, message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        try:
            if error_event.is_set():
                ws.close()
                raise Exception("okx_websocket|error_event is set. closing websocket..")
            message_dict = json.loads(message)
            if 'data' in message_dict.keys():
                message_data_dict = message_dict['data'][0]
                try:
                    if '' in message_data_dict.values():
                        logger.error(f"okx_websocket|Empty string detected.\n{message_data_dict}")
                        return
                except Exception:
                    logger.error(f"okx_websocket|message_data_dict.values(): {message_data_dict.values()}")
                    logger.error(f"okx_websocket|{traceback.format_exc()}")
                    return
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                msg_ts_ms = message_data_dict.get('ts')
                if msg_ts_ms:
                    current_ts_ms = int(time.time() * 1000)
                    if current_ts_ms - int(msg_ts_ms) > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message
                timestamp_us = int(time.time() * 1_000_000)
                local_redis.update_exchange_stream_data(
                    stream_data_type,
                    market_code,
                    message_data_dict['instId'],
                    {
                        **message_data_dict,
                        "last_update_timestamp": timestamp_us,
                    },
                )
                touch_market_ready(local_redis, market_code, stream_data_type, timestamp_us)
                touch_process_heartbeat(local_redis, market_code, stream_data_type, proc_name, timestamp_us)
        except Exception as e:
            logger.error(f"okx_websocket|on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set() # Signal error

    def on_error(ws, error):
        logger.error(f"okx_websocket|on_error: {error}, traceback: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, 'okx_websocket_on_error', str(error))
        error_event.set() # Signal error

    def on_close(ws, close_status_code, close_msg):
        logger.info(
            f"okx_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}"
        )

    def on_open(ws):
        logger.info(f"okx_websocket|okx_websocket started")
        ws.send(json.dumps(data))        

    try:
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
            logger.info(f"okx_{market_type.lower()}_websocket started monitoring inactivity... for {data['args']}...")
            while True:
                if time.time() - last_message_time > inactivity_time_secs:
                    logger.error(f"okx_{market_type.lower()}_websocket has been inactive for {inactivity_time_secs} seconds for {data['args']}. Closing websocket...")
                    try:
                        acw_api.create_message_thread(admin_id, f"okx_{market_type.lower()}_websocket", f"okx_{market_type.lower()}_websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                    except Exception as e:
                        logger.error(f"okx_{market_type.lower()}_websocket|{traceback.format_exc()}")
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
            ws.run_forever(ping_interval=15, ping_timeout=10)
        except Exception as e:
            logger.error(f"okx_websocket|run_forever error: {e}, traceback: {traceback.format_exc()}")
        
        if error_event.is_set():
            raise Exception("okx_websocket|error_event is set. closing websocket..")
    except Exception:
        logger.error(f"okx_websocket|{traceback.format_exc()}")
        raise

class OkxWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir=None):
        self.url = "wss://ws.okx.com:8443/ws/v5/public"
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.logging_dir = logging_dir
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", f"OKX_{self.market_type.upper()}")
        self.logger = InfoCoreLogger(f"okx_{self.market_type.lower()}_websocket", logging_dir).logger
        manager = Manager()
        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.partial_stale_strikes = {}
        self._start_websocket()
        while True:
            if not has_recent_market_ready(
                self.local_redis,
                f"OKX_{self.market_type.upper()}",
                ("ticker",),
            ):
                self.logger.info(f"[OKX {self.market_type}]waiting for websocket data to be loaded..")
                time.sleep(2)
            else:
                break
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_stale_data_per_proc_thread = Thread(target=self.monitor_stale_data_per_proc, daemon=True)
        self.monitor_stale_data_per_proc_thread.start()
    
    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_websocket is False:
                        # Check whether BINANCE_{self.market_type}/{quote_asset} is in maintenance
                        if self.market_type == "SPOT":
                            quote_asset = "USDT"
                        elif self.market_type == "USD_M":
                            quote_asset = "USDT"
                        else:
                            quote_asset = "USD"
                        if fetch_market_servercheck(f"OKX_{self.market_type}/{quote_asset}"):
                            self.logger.info(f"[OKX_{self.market_type}] OKX_{self.market_type} is in maintenance. Skipping (re)starting websockets..")
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
                                self.logger.info(f"okx_ticker_websocket|{i+1}th okx_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.logger.info(f"{i+1}th Okx ticker websocket does not exist. starting..")
                                self.logger.info(f"okx_ticker_websocket|{i+1}th okx_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_data = {
                                    "op": "subscribe",
                                    "args": [
                                        {"channel": "tickers", "instId": f"{x}"} for x in self.sliced_symbols_list[i]
                                    ]
                                }
                                ticker_proc = Process(
                                    target=init_websocket,
                                    args=("ticker",
                                          self.url,
                                          ticker_data,
                                          error_event,
                                          f"{i+1}th_ticker_proc",
                                          self.market_type,
                                          self.logging_dir,
                                          self.acw_api,
                                          self.admin_id
                                        ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"] = ticker_proc
                                ticker_proc.start()
                                if ticker_restarted:
                                    content = f"[OKX {self.market_type}]restarted {i+1}th ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.logger.info(f"ticker_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, f'OKX {self.market_type} ticker websocket restart', content)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.logger.error(content)
                    self.acw_api.create_message_thread(self.admin_id, f"[OKX {self.market_type}]handle_price_procs", content)
                    time.sleep(1)
                time.sleep(0.5)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    def terminate_websocket(self):
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.logger.info(f"[OKX {self.market_type}]all websockets' event has been set")
        self.price_proc_event_list = []

    def restart_websocket(self):
        self.terminate_websocket()
        time.sleep(1)
        self.stop_restart_websocket = False
    
    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = f"[OKX {self.market_type}]websocket proc is not running."
            if print_result:
                self.logger.info(print_text.rstrip())
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[OKX {self.market_type}]{key} status: {value.is_alive()}\n"
            if print_result:
                self.logger.info(print_text.rstrip())
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.logger.info(f"[OKX {self.market_type}]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    deleted_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[OKX {self.market_type}]shared symbol changed. deleted: {deleted_shared_symbol}, added: {added_shared_symbol}"
                    self.logger.info(content)
                    self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)
                    
                    # Set the newer values to before values
                    self.before_symbols_list = new_symbols_list
                    # Set sliced values too
                    self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
                    # restart websockets
                    self.restart_websocket()
                    for each_shared_symbol in deleted_shared_symbol:
                        # remove deleted symbol from redis
                        try:
                            self.logger.info(f"monitor_shared_symbol_change|deleting {each_shared_symbol} from ticker redis..")
                            self.local_redis.delete_exchange_stream_data("ticker", f"OKX_{self.market_type.upper()}", each_shared_symbol)
                        except Exception:
                            self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")                    
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)
                
    def monitor_stale_data_per_proc(self, loop_time_secs=60, stale_threshold_secs=90):
        """
        Periodically checks if the slice of symbols for each process has not
        been updated within `stale_threshold_secs`. If *all* symbols in that
        slice are stale, forcefully kill only that process. The existing logic
        in `handle_price_procs()` will see the process is dead and restart it.

        :param loop_time_secs: how often to run the check (in seconds).
        :param stale_threshold_secs: how long to wait before deciding data is stale
        """
        self.logger.info(f"[OKX {self.market_type}]started monitor_stale_data_per_proc..")
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
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "ticker"
                    else:
                        continue

                    symbol_list = self.websocket_symbol_dict.get(symbol_list_key, [])
                    if not symbol_list:
                        continue

                    if is_process_heartbeat_stale(
                        self.local_redis,
                        f"OKX_{self.market_type.upper()}",
                        redis_stream_type,
                        proc_name,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    ):
                        self.partial_stale_strikes.pop(proc_name, None)
                        content = (
                            f"[OKX {self.market_type}] {proc_name} => "
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
                        continue

                    summary = get_stale_symbol_summary(
                        self.local_redis,
                        f"OKX_{self.market_type.upper()}",
                        redis_stream_type,
                        symbol_list,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    )
                    stale_count = summary["stale_count"]
                    total_symbols = summary["total_symbols"]
                    if stale_count == 0:
                        self.partial_stale_strikes.pop(proc_name, None)
                        continue

                    strike_count = self.partial_stale_strikes.get(proc_name, 0) + 1
                    self.partial_stale_strikes[proc_name] = strike_count
                    stale_symbols_preview = summary["stale_symbols"][:5]

                    if stale_count == total_symbols:
                        content = (
                            f"[OKX {self.market_type}] {proc_name} => "
                            f"All {stale_count}/{total_symbols} symbols stale for > {stale_threshold_secs}s. "
                            f"Forcing process restart."
                        )
                        self.logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
                        self.logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)
                        continue

                    self.logger.warning(
                        f"[OKX {self.market_type}] {proc_name} partial stale "
                        f"{stale_count}/{total_symbols}, strike={strike_count}, "
                        f"symbols={stale_symbols_preview}"
                    )
                    if strike_count >= 2 and (stale_count >= min(2, total_symbols) or summary["stale_ratio"] >= 0.25):
                        content = (
                            f"[OKX {self.market_type}] {proc_name} => "
                            f"Partial stale persisted ({stale_count}/{total_symbols}, strike={strike_count}). "
                            f"Forcing process restart."
                        )
                        self.logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
                        self.logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        self.partial_stale_strikes.pop(proc_name, None)
                        time.sleep(60)

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[OKX {self.market_type}] monitor_stale_data_per_proc", content)

class OkxUSDMWebsocket(OkxWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)

class OkxCOINMWebsocket(OkxWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)
        
