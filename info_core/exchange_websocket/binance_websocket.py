from multiprocessing import Process, Manager, Queue, Event
from threading import Thread
import pandas as pd
import datetime
import websocket
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
from loggers.logger import InfoCoreLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Move binance_websocket function outside the class
def binance_websocket(stream_data_type, data, error_event, proc_name, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Reinitialize the logger inside the function
    logger = InfoCoreLogger(f"binance_{market_type.lower()}_{stream_data_type}_websocket", logging_dir).logger
    logger.info(f"[BINANCE {market_type}] started for {data['params']}...")
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
                raise Exception(f"binance_websocket|{proc_name} error_event is set. closing websocket..")
            msg = json.loads(message)
            if 's' in msg.keys():
                local_redis.update_exchange_stream_data(stream_data_type, f"BINANCE_{market_type.upper()}", msg['s'], {**msg, "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1_000_000)})
        except Exception as e:
            logger.error(f"binance_websocket|{proc_name} on_message error: {e}, traceback: {traceback.format_exc()}")
            error_event.set()  # Signal the main loop to close and restart

    def on_error(ws, error):
        logger.error(f'binance_websocket|{proc_name} on_error executed!\n Error: {error}, traceback: {traceback.format_exc()}')
        # Optionally, you can register the error with monitor_msg if needed
        acw_api.create_message_thread(admin_id, f'binance_websocket_on_error_{proc_name}', str(error))
        error_event.set() # Signal the main loop

    def on_close(ws, close_status_code, close_msg):
        logger.info(f"binance_websocket|{proc_name} ### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

    def on_open(ws):
        ws.send(json.dumps(data))

    websocket.enableTrace(False)
    if market_type == "SPOT":
        wss_url = "wss://stream.binance.com/ws"
    elif market_type == "USD_M":
        wss_url = "wss://fstream.binance.com/ws"
    elif market_type == "COIN_M":
        wss_url = "wss://dstream.binance.com/ws"
    else:
        raise Exception(f"binance_websocket|market_type should be SPOT, USD_M or COIN_M, not {market_type}")

    ws = websocket.WebSocketApp(
        wss_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # Monitoring function to check for inactivity
    def check_inactivity():
        logger.info(f"binance_websocket|{proc_name} started monitoring inactivity... for {data['params']}...")
        while True:
            if time.time() - last_message_time > inactivity_time_secs:
                logger.error(f"binance_websocket|{proc_name} has been inactive for {inactivity_time_secs} seconds for {data['params']}. Closing websocket... and set error_event..")
                try:
                    acw_api.create_message_thread(admin_id, f"binance_websocket|{proc_name} Inactivity", f"binance_websocket|{proc_name} has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                except Exception as e:
                    logger.error(f"binance_websocket|{proc_name} check_inactivity|{traceback.format_exc()}")
                error_event.set()
                break
            time.sleep(1) # Check every 1 second
            
    # Start the monitoring thread
    monitor_thread = Thread(target=check_inactivity, daemon=True)
    monitor_thread.start()
    
    ws.run_forever(ping_interval=30)
    
    if error_event.is_set():
        ws.close()
        raise Exception(f"binance_websocket|{proc_name} error_event is set. closing websocket..")

# Move liquidation_websocket function outside the class
def liquidation_websocket(liquidation_list, error_event, market_type, logging_dir, acw_api, admin_id):
    websocket_logger = InfoCoreLogger(f"binance_{market_type.lower()}_websocket", logging_dir).logger
    websocket_logger.info(f"started liquidation_websocket for {market_type}...")

    def handle_futures_liquidation_streams(msg):
        try:
            if len(liquidation_list) > 1000:
                liquidation_list.pop(0)
            # Filtering can be applied later.
            liquidation_list.append(msg['data'])
        except Exception:
            websocket_logger.error(f"handle_futures_liquidation_streams|{traceback.format_exc()}, msg:{msg}")
            error_event.set()

    twm = ThreadedWebsocketManager()
    twm.daemon = True
    twm.start()
    if market_type == "USD_M":
        twm.start_futures_multiplex_socket(callback=handle_futures_liquidation_streams, streams=['!forceOrder@arr'])
    elif market_type == "COIN_M":
        twm.start_futures_multiplex_socket(callback=handle_futures_liquidation_streams, streams=['!forceOrder@arr'], futures_type=FuturesType.COIN_M)
    else:
        raise Exception(f"liquidation_websocket|market_type should be USD_M or COIN_M, not {market_type}")
    # twm.join()
    while not error_event.is_set():
        time.sleep(0.1)
    twm.stop()

class BinanceWebsocket:
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, info_dict, logging_dir):
        self.market_type = market_type
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.get_symbol_list = get_symbol_list
        self.info_dict = info_dict
        self.logging_dir = logging_dir  # Store logging_dir for child processes
        self.local_redis = RedisHelper()
        self.local_redis.delete_all_exchange_stream_data("ticker", f"BINANCE_{self.market_type.upper()}")
        self.local_redis.delete_all_exchange_stream_data("orderbook", f"BINANCE_{self.market_type.upper()}")
        self.logger = InfoCoreLogger(f"binance_{self.market_type.lower()}_websocket", logging_dir).logger

        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.proc_n = int(proc_n * 2)
        self.before_symbol_list = self.get_symbol_list()
        self.logger.info(f"[BINANCE {self.market_type}] total symbol list: {self.before_symbol_list}")
        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
        self.logger.info(f"[BINANCE {self.market_type}] Sliced symbol list: {self.sliced_symbol_list}")
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        manager = Manager()
        self.liquidation_list = manager.list()
        self._start_websocket()

        while True:
            if (not self.local_redis.get_all_exchange_stream_data("orderbook", f"BINANCE_{market_type.upper()}") or
                not self.local_redis.get_all_exchange_stream_data("ticker", f"BINANCE_{market_type.upper()}")):
                self.logger.info(f"[BINANCE {self.market_type}] Waiting for websocket data to be loaded...")
                time.sleep(2)
            else:
                break

        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
    
    def __del__(self):
        self.terminate_websocket()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if not self.stop_restart_websocket:
                        # Check whether BINANCE_{self.market_type}/{quote_asset} is in maintenance
                        if self.market_type == "SPOT":
                            quote_asset = "USDT"
                        elif self.market_type == "USD_M":
                            quote_asset = "USDT"
                        else:
                            quote_asset = "USD"
                        if fetch_market_servercheck(f"BINANCE_{self.market_type}/{quote_asset}"):
                            self.logger.info(f"[BINANCE_{self.market_type}] BINANCE_{self.market_type} is in maintenance. Skipping (re)starting websockets..")
                            time.sleep(1)
                            continue
                        for i in range(self.proc_n):
                            index = i + 1
                            # Handle bookticker process
                            bookticker_proc_name = f"{index}th_bookticker_proc"
                            start_proc = False
                            restarted = False

                            if (
                                bookticker_proc_name in self.websocket_proc_dict
                                and not self.websocket_proc_dict[bookticker_proc_name].is_alive()
                            ):
                                content = f"handle_price_procs|[BINANCE {self.market_type}]{index}th_bookticker_proc has died. Terminating and restarting..."
                                self.logger.error(content)
                                self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                                self.websocket_proc_dict[bookticker_proc_name].terminate()
                                self.websocket_proc_dict[bookticker_proc_name].join()
                                start_proc = True
                                restarted = True
                            elif bookticker_proc_name not in self.websocket_proc_dict:
                                self.logger.info(f"[BINANCE {self.market_type}]{index}th_bookticker_proc is not in self.websocket_proc_dict. Starting...")
                                start_proc = True

                            if start_proc:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                symbol_list = self.sliced_symbol_list[i]
                                self.logger.info(f"[BINANCE {self.market_type}] {index}th_bookticker_proc symbol list: {symbol_list}")
                                bookticker_data = {
                                    "method": "SUBSCRIBE",
                                    "params": [x.lower() + "@bookTicker" for x in symbol_list],
                                    "id": index
                                }
                                upbit_bookticker_proc = Process(
                                    target=binance_websocket,  # Module-level function
                                    args=(
                                        "orderbook",
                                        bookticker_data,
                                        error_event,
                                        bookticker_proc_name,
                                        self.market_type,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id,
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[bookticker_proc_name] = upbit_bookticker_proc
                                self.websocket_symbol_dict[f"{index}th_bookticker_symbol"] = symbol_list
                                upbit_bookticker_proc.start()
                                self.logger.info(f"[BINANCE {self.market_type}] Started {bookticker_proc_name} websocket process.")
                                if restarted:
                                    content = f"handle_price_procs|[BINANCE {self.market_type}]{bookticker_proc_name} has been restarted. Alive status: {upbit_bookticker_proc.is_alive()}"
                                    self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                                time.sleep(2)

                        # Handle ticker process
                        ticker_proc_name = "ticker_proc"
                        start_proc = False
                        restarted = False

                        if (
                            ticker_proc_name in self.websocket_proc_dict
                            and not self.websocket_proc_dict[ticker_proc_name].is_alive()
                        ):
                            content = f"handle_price_procs|[BINANCE {self.market_type}] {ticker_proc_name} has died. Terminating and restarting..."
                            self.logger.error(content)
                            self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                            self.websocket_proc_dict[ticker_proc_name].terminate()
                            self.websocket_proc_dict[ticker_proc_name].join()
                            start_proc = True
                            restarted = True
                        elif ticker_proc_name not in self.websocket_proc_dict:
                            self.logger.info(f"[BINANCE {self.market_type}] {ticker_proc_name} is not in self.websocket_proc_dict. Starting...")
                            start_proc = True

                        if start_proc:
                            error_event = Event()
                            self.price_proc_event_list.append(error_event)
                            symbol_list = self.before_symbol_list
                            self.logger.info(f"[BINANCE {self.market_type}] {ticker_proc_name} symbol list: {symbol_list}")
                            ticker_data = {
                                "method": "SUBSCRIBE",
                                "params": [x.lower() + "@ticker" for x in symbol_list],
                                "id": 0
                            }
                            upbit_ticker_proc = Process(
                                target=binance_websocket,  # Module-level function
                                args=(
                                    "ticker",
                                    ticker_data,
                                    error_event,
                                    ticker_proc_name,
                                    self.market_type,
                                    self.logging_dir,
                                    self.acw_api,
                                    self.admin_id,
                                ),
                                daemon=True
                            )
                            self.websocket_proc_dict[ticker_proc_name] = upbit_ticker_proc
                            self.websocket_symbol_dict["ticker_symbol"] = symbol_list
                            upbit_ticker_proc.start()
                            self.logger.info(f"[BINANCE {self.market_type}] Started {ticker_proc_name} websocket process.")
                            if restarted:
                                content = f"handle_price_procs|[BINANCE {self.market_type}] {ticker_proc_name} has been restarted. Alive status: {upbit_ticker_proc.is_alive()}"
                                self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                            time.sleep(2)

                        # Handle liquidation process for futures markets
                        if self.market_type != "SPOT":
                            liquidation_proc_name = "liquidation_proc"
                            if (
                                liquidation_proc_name in self.websocket_proc_dict
                                and not self.websocket_proc_dict[liquidation_proc_name].is_alive()
                            ):
                                content = f"handle_price_procs|[BINANCE {self.market_type}] {liquidation_proc_name} has died. Terminating and restarting..."
                                self.logger.error(content)
                                self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                                self.websocket_proc_dict[liquidation_proc_name].terminate()
                                self.websocket_proc_dict[liquidation_proc_name].join()
                                error_event = Event()
                                self.websocket_proc_dict[liquidation_proc_name] = Process(
                                    target=liquidation_websocket,
                                    args=(
                                        self.liquidation_list,
                                        error_event,
                                        self.market_type,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id,
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[liquidation_proc_name].start()
                                content = f"handle_price_procs|{liquidation_proc_name} has been restarted. Alive status: {self.websocket_proc_dict[liquidation_proc_name].is_alive()}"
                                self.logger.info(f"[BINANCE {self.market_type}] Restarted {liquidation_proc_name} websocket. Alive status: {self.websocket_proc_dict[liquidation_proc_name].is_alive()}")
                                self.acw_api.create_message_thread(self.admin_id, "handle_price_procs", content)
                            elif liquidation_proc_name not in self.websocket_proc_dict:
                                self.logger.info(f"[BINANCE {self.market_type}] {liquidation_proc_name} is not in self.websocket_proc_dict. Starting...")
                                error_event = Event()
                                self.websocket_proc_dict[liquidation_proc_name] = Process(
                                    target=liquidation_websocket,
                                    args=(
                                        self.liquidation_list,
                                        error_event,
                                        self.market_type,
                                        self.logging_dir,
                                        self.acw_api,
                                        self.admin_id,
                                    ),
                                    daemon=True
                                )
                                self.websocket_proc_dict[liquidation_proc_name].start()
                                self.logger.info(f"[BINANCE {self.market_type}] Started {liquidation_proc_name} websocket process.")

                    else:
                        time.sleep(1)
                except Exception as e:
                    self.logger.error(f"handle_price_procs|{traceback.format_exc()}")
                    self.acw_api.create_message_thread(self.admin_id, f"Binance {self.market_type} Websocket|handle_price_procs", str(e))
                    time.sleep(2)
                time.sleep(0.25)

        self.handle_price_procs_thread = Thread(target=handle_price_procs, daemon=True)
        self.handle_price_procs_thread.start()

    # Rest of your class methods remain unchanged, but ensure that you don't reference self.binance_websocket or self.liquidation_websocket

    def terminate_websocket(self):
        self.stop_restart_websocket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.logger.info(f"[BINANCE {self.market_type}] All websockets' events have been set.")
        self.price_proc_event_list = []
        
    def restart_websocket(self):
        self.terminate_websocket()
        time.sleep(1)
        self.stop_restart_websocket = False
        
    def check_status(self, print_result=False, include_text=False):
        if len(self.websocket_proc_dict) == 0:
            proc_status = False
            print_text = f"[BINANCE {self.market_type}]websocket proc is not running."
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

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.logger.info(f"[BINANCE {self.market_type}]started monitor_shared_symbol_change..")
        monitor_shared_symbol_change_count = 0
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbol_list = self.get_symbol_list()
                
                if sorted(self.before_symbol_list) != sorted(new_symbol_list):
                    monitor_shared_symbol_change_count += 1
                    if monitor_shared_symbol_change_count > 5:
                        deleted_symbols = [x for x in self.before_symbol_list if x not in new_symbol_list]
                        added_symbols = [x for x in new_symbol_list if x not in self.before_symbol_list]
                        content = f"monitor_shared_symbol_change|[BINANCE {self.market_type}]{self.market_type} shared symbol changed. deleted: {deleted_symbols}, added: {added_symbols}"
                        self.logger.info(content)
                        self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)

                        # Set the newer values to before values
                        self.before_symbol_list = new_symbol_list
                        # Set sliced values too
                        self.sliced_symbol_list = list_slice(self.get_symbol_list(), self.proc_n)
                        # restart websockets
                        self.restart_websocket()
                        for each_symbol in deleted_symbols:
                            # remove deleted symbol from redis ticker hash and redis orderbook hash
                            try:
                                self.logger.info(f"monitor_shared_symbol_change|Deleting {each_symbol} from redis..")
                                self.local_redis.delete_exchange_stream_data("ticker", f"BINANCE_{self.market_type.upper()}", each_symbol)
                            except Exception:
                                self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                            try:
                                self.logger.info(f"monitor_shared_symbol_change|Deleting {each_symbol} from redis..")
                                self.local_redis.delete_exchange_stream_data("orderbook", f"BINANCE_{self.market_type.upper()}", each_symbol)
                            except Exception:
                                self.logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                else:
                    monitor_shared_symbol_change_count = 0
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, f"[BINANCE {self.market_type}] monitor_shared_symbol_change", content)

    def get_price_df(self):
        binance_ticker_df = pd.DataFrame(self.local_redis.get_all_exchange_stream_data("ticker", f"BINANCE_{self.market_type.upper()}")).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(self.local_redis.get_all_exchange_stream_data("orderbook", f"BINANCE_{self.market_type.upper()}")).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df.loc[:, ['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_merged_df = binance_merged_df.merge(self.info_dict[f'binance_{self.market_type.lower()}_info_df'][['symbol','base_asset','quote_asset']], left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df


##############################################################################################################################

class BinanceUSDMWebsocket(BinanceWebsocket):
    def __init__(self, admin_id, node, proc_n, get_binance_usdm_symbol_list, acw_api, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n, get_binance_usdm_symbol_list, acw_api, market_type, info_dict, logging_dir)

##############################################################################################################################

class BinanceCOINMWebsocket(BinanceWebsocket):
    def __init__(self, admin_id, node, proc_n, get_binance_coinm_symbol_list, acw_api, market_type, info_dict, logging_dir):
        super().__init__(admin_id, node, proc_n/2, get_binance_coinm_symbol_list, acw_api, market_type, info_dict, logging_dir)
