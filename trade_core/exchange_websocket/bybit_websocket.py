from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
import traceback
from pybit.unified_trading import WebSocket
import json
import datetime
import time
import _pickle as pickle
# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import TradeCoreLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper

# Standalone function for the ticker websocket
def init_ticker_websocket(symbol_list, error_event, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Initialize logger inside the function
    logger = TradeCoreLogger(f"bybit_{market_type.lower()}_ticker_websocket", logging_dir).logger
    logger.info(f"[BYBIT {market_type}] started for {symbol_list}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance

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
        if error_event.is_set():
            ws.exit()
            return
        if 'data' in message.keys():
            # ticker_dict[message['data']['symbol']] = {
            #     **message['data'],
            #     'last_update_timestamp': int(datetime.datetime.utcnow().timestamp() * 1000000)
            # }
            local_redis.update_exchange_stream_data("ticker", 
                                                    f"BYBIT_{market_type.upper()}", 
                                                    message['data']['symbol'], 
                                                    {**message['data'], 'last_update_timestamp': int(datetime.datetime.utcnow().timestamp() * 1000000)})
        
            

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
def init_orderbook_websocket(symbol_list, error_event, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=10):
    # Initialize logger inside the function
    logger = TradeCoreLogger(f"bybit_{market_type.lower()}_orderbook_websocket", logging_dir).logger
    logger.info(f"[BYBIT {market_type}] started for {symbol_list}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance

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
        if error_event.is_set():
            ws.exit()
            return
        if 'data' in message.keys():
            # orderbook_dict[message['data']['s']] = {
            #     **message['data'],
            #     'last_update_timestamp': int(datetime.datetime.utcnow().timestamp() * 1000000)
            # }
            local_redis.update_exchange_stream_data("orderbook",
                                                    f"BYBIT_{market_type.upper()}",
                                                    message['data']['s'],
                                                    {**message['data'], 'last_update_timestamp': int(datetime.datetime.utcnow().timestamp() * 1000000)})

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
                    error_event.set()
                    ws.close()
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
        self.websocket_logger = TradeCoreLogger(f"bybit_{self.market_type.lower()}_websocket", logging_dir).logger
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
            if (not self.local_redis.get_all_exchange_stream_data("ticker", f"BYBIT_{self.market_type.upper()}") or
                not self.local_redis.get_all_exchange_stream_data("orderbook", f"BYBIT_{self.market_type.upper()}")):
                self.websocket_logger.info(f"[BYBIT {self.market_type}]waiting for websocket data to be loaded..")
                time.sleep(2)
            else:
                break
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
    
    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if self.stop_restart_websocket is False:
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
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_symbols_list[i]
                                ticker_proc = Process(
                                    target=init_ticker_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
                                        error_event,
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
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_symbols_list[i]
                                orderbook_proc = Process(
                                    target=init_orderbook_websocket,
                                    args=(
                                        self.sliced_symbols_list[i],
                                        error_event,
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

    def terminate_websocket(self):
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[BYBIT {self.market_type}]all websockets' event has been set")
        self.price_proc_event_list = []
    
    def restart_websocket(self):
        self.terminate_websocket()
        time.sleep(1)
        self.stop_restart_websocket = False
    
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

class BybitUSDMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)

class BybitCOINMWebsocket(BybitWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)
        
