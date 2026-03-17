from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import traceback
from pybit.unified_trading import WebSocket
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
from acw_common.websocket import evaluate_process_staleness, wait_for_market_ready
from acw_common.websocket import (
    get_process_group_status,
    restart_process_group,
    terminate_process_group,
)
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Maximum allowed message delay in milliseconds - drop messages older than this
MAX_MESSAGE_DELAY_MS = 200

# Standalone function for the ticker websocket
def init_ticker_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Initialize logger inside the function
    logger = InfoCoreLogger(f"bybit_{market_type.lower()}_ticker_websocket", logging_dir).logger
    logger.info(f"[BYBIT {market_type}] started for {symbol_list}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance
    market_code = f"BYBIT_{market_type.upper()}"

    def cut_list(lst):
        return [lst[i:i + 10] for i in range(0, len(lst), 10)]

    if market_type == "SPOT":
        channel_type = 'spot'
    elif market_type == "USD_M":
        channel_type = "linear"
    elif market_type == "COIN_M":
        channel_type = "inverse"
    else:
        raise Exception(f"market_type {market_type} is not supported.")

    ws = WebSocket(
        testnet=False,
        channel_type=channel_type
    )

    def handle_message(message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        try:
            if error_event.is_set():
                ws.exit()
                return
            if 'data' in message.keys() and 'symbol' in message.get('data', {}):
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                msg_ts_ms = message.get('ts')
                if msg_ts_ms:
                    current_ts_ms = int(time.time() * 1000)
                    if current_ts_ms - msg_ts_ms > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message
                timestamp_us = int(time.time() * 1_000_000)
                local_redis.update_exchange_stream_data(
                    "ticker",
                    market_code,
                    message['data']['symbol'],
                    {**message['data'], 'last_update_timestamp': timestamp_us},
                )
                touch_market_ready(local_redis, market_code, "ticker", timestamp_us)
                touch_process_heartbeat(local_redis, market_code, "ticker", proc_name, timestamp_us)
        except Exception as e:
            logger.error(f"handle_message|ticker error: {e}, message: {message}, traceback: {traceback.format_exc()}")
            error_event.set()
        
            

    try:
        if market_type == "SPOT":
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
            
        
        # Monitoring function to check for inactivity
        def check_inactivity():
            logger.info(f"init_ticker_websocket|bybit_{market_type.lower()}_ticker_websocket started monitoring inactivity... for {symbol_list}...")
            while True:
                if time.time() - last_message_time > inactivity_time_secs:
                    logger.error(f"init_ticker_websocket|bybit_{market_type.lower()}_ticker_websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                    try:
                        acw_api.create_message_thread(admin_id, f"bybit_{market_type.lower()}_ticker_websocket Inactivity", f"bybit_{market_type.lower()}_ticker_websocket for {symbol_list} has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                    except Exception as e:
                        logger.error(f"init_ticker_websocket|{traceback.format_exc()}")
                    error_event.set()
                    ws.close()
                    break
                time.sleep(1) # Check every 1 second
                
        # Start the monitoring thread
        monitor_thread = Thread(target=check_inactivity, daemon=True)
        monitor_thread.start()
            
        # Idle loop
        while True:
            time.sleep(1)
            if error_event.is_set():
                raise Exception(f"init_ticker_websocket|bybit_{market_type.lower()}_ticker_websocket error_event is set. closing websocket..")
    except Exception as e:
        content = f"init_ticker_websocket|{traceback.format_exc()}"
        logger.error(content)

# Standalone function for the orderbook websocket
def init_orderbook_websocket(symbol_list, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=10):
    # Initialize logger inside the function
    logger = InfoCoreLogger(f"bybit_{market_type.lower()}_orderbook_websocket", logging_dir).logger
    logger.info(f"[BYBIT {market_type}] started for {symbol_list}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance
    market_code = f"BYBIT_{market_type.upper()}"

    def cut_list(lst):
        return [lst[i:i + 10] for i in range(0, len(lst), 10)]

    if market_type == "SPOT":
        channel_type = 'spot'
    elif market_type == "USD_M":
        channel_type = "linear"
    elif market_type == "COIN_M":
        channel_type = "inverse"
    else:
        raise Exception(f"market_type {market_type} is not supported.")

    ws = WebSocket(
        testnet=False,
        channel_type=channel_type
    )

    def handle_message(message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        try:
            if error_event.is_set():
                ws.exit()
                return
            if 'data' in message.keys() and 's' in message.get('data', {}):
                # Check message delay - drop if older than MAX_MESSAGE_DELAY_MS
                msg_ts_ms = message.get('ts')
                if msg_ts_ms:
                    current_ts_ms = int(time.time() * 1000)
                    if current_ts_ms - msg_ts_ms > MAX_MESSAGE_DELAY_MS:
                        return  # Drop stale message
                timestamp_us = int(time.time() * 1_000_000)
                local_redis.update_exchange_stream_data(
                    "orderbook",
                    market_code,
                    message['data']['s'],
                    {**message['data'], 'last_update_timestamp': timestamp_us},
                )
                touch_market_ready(local_redis, market_code, "orderbook", timestamp_us)
                touch_process_heartbeat(local_redis, market_code, "orderbook", proc_name, timestamp_us)
        except Exception as e:
            logger.error(f"handle_message|orderbook error: {e}, message: {message}, traceback: {traceback.format_exc()}")
            error_event.set()

    try:
        if market_type == "SPOT":
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
            
        # Monitoring function to check for inactivity
        def check_inactivity():
            logger.info(f"init_orderbook_websocket|bybit_{market_type.lower()}_orderbook_websocket started monitoring inactivity... for {symbol_list}...")
            while True:
                if time.time() - last_message_time > inactivity_time_secs:
                    logger.error(f"init_orderbook_websocket|bybit_{market_type.lower()}_orderbook_websocket has been inactive for {inactivity_time_secs} seconds for {symbol_list}. Closing websocket...")
                    try:
                        acw_api.create_message_thread(admin_id, f"bybit_{market_type.lower()}_orderbook_websocket Inactivity", f"bybit_{market_type.lower()}_orderbook_websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                    except Exception as e:
                        logger.error(f"init_orderbook_websocket|{traceback.format_exc()}")
                    # ---- THE CRUCIAL PART: EXPLICITLY CLOSE THE WEBSOCKET ----
                    try:
                        ws.close()
                    except Exception:
                        pass
                    error_event.set()
                    break
                time.sleep(1)
                
        # Start the monitoring thread
        monitor_thread = Thread(target=check_inactivity, daemon=True)
        monitor_thread.start()
        
        # Idle loop
        while True:
            time.sleep(1)
            if error_event.is_set():
                raise Exception(f"init_orderbook_websocket|bybit_{market_type.lower()}_orderbook_websocket error_event is set. closing websocket..")
    except Exception as e:
        content = f"init_orderbook_websocket|{traceback.format_exc()}"
        logger.error(content)

class BybitWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir=None):
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.logging_dir = logging_dir
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", f"BYBIT_{self.market_type.upper()}")
        self.local_redis.delete_all_exchange_stream_data("orderbook", f"BYBIT_{self.market_type.upper()}")
        self.websocket_logger = InfoCoreLogger(f"bybit_{self.market_type.lower()}_websocket", logging_dir).logger
        manager = Manager()
        self.proc_n = proc_n
        self.before_symbols_list = self.get_symbol_list()
        self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.stop_restart_websocket = False
        self.price_proc_event_list = {}
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.partial_stale_strikes = {}
        self._start_websocket()
        wait_for_market_ready(
            self.local_redis,
            f"BYBIT_{self.market_type.upper()}",
            ("ticker", "orderbook"),
            self.websocket_logger,
            f"[BYBIT {self.market_type}]waiting for websocket data to be loaded..",
        )
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
                        if fetch_market_servercheck(f"BYBIT_{self.market_type}/{quote_asset}"):
                            self.websocket_logger.info(f"[BYBIT_{self.market_type}] BYBIT_{self.market_type} is in maintenance. Skipping (re)starting websockets..")
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
                                self.websocket_logger.info(f"bybit_ticker_websocket|{i+1}th bybit_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Bybit ticker websocket does not exist. starting..")
                                self.websocket_logger.info(f"bybit_ticker_websocket|{i+1}th bybit_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list[f"{i+1}th_ticker_proc"] = error_event
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_proc = Process(
                                    target=init_ticker_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
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
                                    content = f"[BYBIT {self.market_type}] restarted {i+1}th ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.websocket_logger.info(f"ticker_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, f'BYBIT {self.market_type} ticker websocket restart', content)
                                time.sleep(2)
                            time.sleep(0.5)
                            orderbook_start_proc = False
                            orderbook_restarted = False
                            if f"{i+1}th_orderbook_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
                                self.websocket_logger.info(f"bybit_orderbook_websocket|{i+1}th bybit_orderbook_proc terminated.")
                            elif f"{i+1}th_orderbook_proc" not in self.websocket_proc_dict.keys():
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Bybit orderbook websocket does not exist. starting..")
                                self.websocket_logger.info(f"bybit_orderbook_websocket|{i+1}th bybit_orderbook_proc started.")
                            if orderbook_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list[f"{i+1}th_orderbook_proc"] = error_event
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_proc = Process(
                                    target=init_orderbook_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
                                        error_event,
                                        f"{i+1}th_orderbook_proc",
                                        self.market_type,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"] = orderbook_proc
                                orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"restarted {i+1}th orderbook websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                                    self.websocket_logger.info(f"orderbook_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, f'BYBIT {self.market_type} orderbook websocket restart', content)
                                time.sleep(2)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
                    self.acw_api.create_message_thread(self.admin_id, f"[BYBIT {self.market_type}]handle_price_procs", content)
                    time.sleep(1)
                time.sleep(0.5)
        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()
        
        # Start the per-process stale checker (only if not already running):
        if not hasattr(self, 'stale_data_per_proc_thread') or not self.stale_data_per_proc_thread.is_alive():
            self.stale_data_per_proc_thread = Thread(
                target=self.monitor_stale_data_per_proc,
                daemon=True
            )
            self.stale_data_per_proc_thread.start()

    def terminate_websocket(self):
        terminate_process_group(
            self,
            self.websocket_logger,
            f"[BYBIT {self.market_type}]all websockets' event has been set",
        )
    
    def restart_websocket(self):
        restart_process_group(
            self,
            self.websocket_logger,
            f"[BYBIT {self.market_type}]all websockets' event has been set",
        )
    
    def check_status(self, print_result=False, include_text=False):
        return get_process_group_status(
            self.websocket_proc_dict,
            self.websocket_logger,
            f"[BYBIT {self.market_type}]",
            print_result=print_result,
            include_text=include_text,
        )

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info(f"[BYBIT {self.market_type}]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    deleted_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[BYBIT {self.market_type}]shared symbol changed. deleted: {deleted_shared_symbol}, added: {added_shared_symbol}"
                    self.websocket_logger.info(content)
                    self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)
                    
                    # Set the newer values to before values
                    self.before_symbols_list = new_symbols_list
                    # Set sliced values too
                    self.sliced_symbols_list = list_slice(self.get_symbol_list(), self.proc_n)
                    # restart websockets
                    self.restart_websocket()
                    for each_shared_symbol in deleted_shared_symbol:
                        # remove deleted symbol from ticker_dict and orderbook_dict
                        try:
                            self.websocket_logger.info(f"monitor_shared_symbol_change|deleting ticker data for {each_shared_symbol} from redis")
                            self.local_redis.delete_exchange_stream_data("ticker", f"BYBIT_{self.market_type.upper()}", each_shared_symbol)
                        except Exception:
                            self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                        try:
                            self.websocket_logger.info(f"monitor_shared_symbol_change|deleting orderbook data for {each_shared_symbol} from redis")
                            self.local_redis.delete_exchange_stream_data("orderbook", f"BYBIT_{self.market_type.upper()}", each_shared_symbol)
                        except Exception:
                            self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")                    
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
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
        self.websocket_logger.info(f"[BYBIT {self.market_type}]started monitor_stale_data_per_proc..")
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
                    elif "orderbook_proc" in proc_name:
                        symbol_list_key = proc_name.replace("proc", "symbol")
                        redis_stream_type = "orderbook"
                    else:
                        continue

                    symbol_list = self.websocket_symbol_dict.get(symbol_list_key, [])
                    if not symbol_list:
                        continue

                    result = evaluate_process_staleness(
                        self.local_redis,
                        f"BYBIT_{self.market_type.upper()}",
                        redis_stream_type,
                        proc_name,
                        symbol_list,
                        self.partial_stale_strikes,
                        stale_threshold_secs=stale_threshold_secs,
                        now_us=now_us,
                    )
                    if result["action"] == "restart":
                        if result["reason"] == "heartbeat":
                            content = (
                                f"[BYBIT {self.market_type}] {proc_name} => "
                                f"Heartbeat stale for > {stale_threshold_secs}s. "
                                f"Forcing process restart."
                            )
                        elif result["reason"] == "all_symbols":
                            content = (
                                f"[BYBIT {self.market_type}] {proc_name} => "
                                f"All {result['stale_count']}/{result['total_symbols']} symbols stale for > {stale_threshold_secs}s. "
                                f"Forcing process restart."
                            )
                        else:
                            content = (
                                f"[BYBIT {self.market_type}] {proc_name} => "
                                f"Partial stale persisted ({result['stale_count']}/{result['total_symbols']}, strike={result['strike_count']}). "
                                f"Forcing process restart."
                            )
                        self.websocket_logger.error(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_stale_data_per_proc", content)
                        self.websocket_logger.warning(f"Killing process: {proc_name}")
                        proc.terminate()
                        proc.join()
                        time.sleep(60)
                        continue
                    if result["action"] == "warn":
                        self.websocket_logger.warning(
                            f"[BYBIT {self.market_type}] {proc_name} partial stale "
                            f"{result['stale_count']}/{result['total_symbols']}, strike={result['strike_count']}, "
                            f"symbols={result['stale_symbols_preview']}"
                        )
                        continue
                    if result["action"] != "healthy":
                        continue

            except Exception as e:
                content = f"monitor_stale_data_per_proc|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[BYBIT {self.market_type}] monitor_stale_data_per_proc", content)
class BybitUSDMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)

class BybitCOINMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)
        
