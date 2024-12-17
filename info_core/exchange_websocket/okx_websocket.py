from multiprocessing import Process, Manager, Event
from threading import Thread
import pandas as pd
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
from loggers.logger import InfoCoreLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.store_exchange_status import fetch_market_servercheck

# Standalone function for the websocket
def init_websocket(stream_data_type, url, data, error_event, market_type, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Initialize logger inside the function
    logger = InfoCoreLogger(f"okx_{market_type.lower()}_websocket", logging_dir).logger
    logger.info(f"[OKX {market_type}]init_websocket started for {data['args']}...")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance

    def on_message(ws, message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
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
            local_redis.update_exchange_stream_data(stream_data_type, f"OKX_{market_type.upper()}", message_data_dict['instId'], {
                **message_data_dict,
                "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1000000)
            })

    def on_error(ws, error):
        logger.error(f"okx_websocket|on_error executed!\nError: {error}, traceback: {traceback.format_exc()}")

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
                    error_event.set()
                    ws.close()
                    break
                time.sleep(1) # Check every 1 second
                
        # Start the monitoring thread
        monitor_thread = Thread(target=check_inactivity, daemon=True)
        monitor_thread.start()
        
        ws.run_forever(ping_interval=15)
        
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
        self.websocket_logger = InfoCoreLogger(f"okx_{self.market_type.lower()}_websocket", logging_dir).logger
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
            if not self.local_redis.get_all_exchange_stream_data("ticker", f"OKX_{self.market_type.upper()}"):
                self.websocket_logger.info(f"[OKX {self.market_type}]waiting for websocket data to be loaded..")
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
                        # Check whether BINANCE_{self.market_type}/{quote_asset} is in maintenance
                        if self.market_type == "SPOT":
                            quote_asset = "USDT"
                        elif self.market_type == "USD_M":
                            quote_asset = "USDT"
                        else:
                            quote_asset = "USD"
                        if fetch_market_servercheck(f"OKX_{self.market_type}/{quote_asset}"):
                            self.websocket_logger.info(f"[OKX_{self.market_type}] OKX_{self.market_type} is in maintenance. Skipping (re)starting websockets..")
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
                                self.websocket_logger.info(f"okx_ticker_websocket|{i+1}th okx_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Okx ticker websocket does not exist. starting..")
                                self.websocket_logger.info(f"okx_ticker_websocket|{i+1}th okx_ticker_proc started.")
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
                                    self.websocket_logger.info(f"ticker_websocket|{content}")
                                    self.acw_api.create_message_thread(self.admin_id, f'OKX {self.market_type} ticker websocket restart', content)
                            time.sleep(0.5)
                except Exception as e:
                    content = f"handle_price_procs|{traceback.format_exc()}"
                    self.websocket_logger.error(content)
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
        self.websocket_logger.info(f"[OKX {self.market_type}]all websockets' event has been set")
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
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[OKX {self.market_type}]{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info(f"[OKX {self.market_type}]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_symbols_list = self.get_symbol_list()
                
                if sorted(self.before_symbols_list) != sorted(new_symbols_list):
                    deleted_shared_symbol = [x for x in self.before_symbols_list if x not in new_symbols_list]
                    added_shared_symbol = [x for x in new_symbols_list if x not in self.before_symbols_list]
                    content = f"monitor_shared_symbol_change|[OKX {self.market_type}]shared symbol changed. deleted: {deleted_shared_symbol}, added: {added_shared_symbol}"
                    self.websocket_logger.info(content)
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
                            self.websocket_logger.info(f"monitor_shared_symbol_change|deleting {each_shared_symbol} from ticker redis..")
                            self.local_redis.delete_exchange_stream_data("ticker", f"OKX_{self.market_type.upper()}", each_shared_symbol)
                        except Exception:
                            self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")                    
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, "monitor_shared_symbol_change", content)

    def get_price_df(self):
        try:
            ticker_df = pd.DataFrame(self.local_redis.get_all_exchange_stream_data("ticker", f"OKX_{self.market_type.upper()}")).T
            ticker_df['base_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[0])
            ticker_df['quote_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[1])
            ticker_df = ticker_df.rename(columns={"last": "tp", "askPx": "ap", "bidPx":"bp", "volCcy24h":"atp24h"})
            ticker_df.loc[:, ['tp', 'ap', 'bp', 'open24h', 'atp24h']] = ticker_df.loc[:, ['tp', 'ap', 'bp', 'open24h', 'atp24h']].astype(float)
            ticker_df['atp24h'] = ticker_df.apply(lambda x: x['tp']*x['atp24h'] if x['instType'] != "SPOT" else x['atp24h'], axis=1)
            ticker_df['scr'] = (ticker_df['tp'] - ticker_df['open24h'])/ticker_df['open24h'] * 100
            ticker_df = ticker_df[['instId', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']]
            return ticker_df
        except Exception as e:
            content = f"get_price_df|{traceback.format_exc()}"
            self.websocket_logger.error(content)
            empty_string_rows = ticker_df[ticker_df[['tp', 'ap', 'bp', 'open24h', 'atp24h']].eq('').any(axis=1)]
            self.websocket_logger.error(f"get_price_df|empty_string_rows: {empty_string_rows[['instId','tp', 'ap', 'bp', 'open24h', 'atp24h']]}")
            self.websocket_logger.error(f"{empty_string_rows[['instId','tp', 'ap', 'bp', 'open24h', 'atp24h']].to_dict()}")
            # Find where the cell in dataframe is empty string

            raise e

class OkxUSDMWebsocket(OkxWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)

class OkxCOINMWebsocket(OkxWebsocket):
    def __init__(self, admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir):
        super().__init__(admin_id, node, proc_n, get_symbol_list, acw_api, market_type, logging_dir)
        
