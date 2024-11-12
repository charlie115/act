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

# Move the upbit_websocket function outside the class
def upbit_websocket(stream_data_type, url, data, error_event, logging_dir, acw_api, admin_id, inactivity_time_secs=60):
    # Reinitialize the logger inside the function
    logger = InfoCoreLogger("upbit_websocket", logging_dir).logger
    logger.info(f"[UPBIT] {stream_data_type} websocket started for {data[1]['codes']}")
    local_redis = RedisHelper()
    
    # For monitoring the last message time
    last_message_time = time.time()
    ws = None  # Placeholder for the WebSocketApp instance

    def on_message(ws, message):
        nonlocal last_message_time # Declare nonlocal to modify the outer variable
        last_message_time = time.time() # Update the time of the last received message
        if error_event.is_set():
            ws.close()
            raise Exception("upbit_websocket|error_event is set. closing websocket..")
        message_dict = json.loads(message)
        local_redis.update_exchange_stream_data(stream_data_type, "UPBIT_SPOT", message_dict['cd'],
                                                {**message_dict, 'last_update_timestamp': datetime.datetime.utcnow().timestamp()*1000000})

    def on_error(ws, error):
        logger.error(f'upbit_websocket|on_error executed!\nError: {error}')
        # Optionally, you can register the error with monitor_msg if needed
        acw_api.create_message_thread(admin_id, 'upbit websocket error', str(error))

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
                acw_api.create_message_thread(admin_id, f"[UPBIT] {stream_data_type} websocket Inactivity", f"[UPBIT] {stream_data_type} websocket has been inactive for {inactivity_time_secs} seconds. Closing websocket...")
                ws.close()
                break
            time.sleep(1) # Check every 1 second
            
    # Start the monitoring thread
    monitor_thread = Thread(target=check_inactivity, daemon=True)
    monitor_thread.start()

    
    ws.run_forever(ping_interval=30)

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
        self.websocket_logger = InfoCoreLogger("upbit_websocket", logging_dir).logger
        self.proc_n = proc_n
        self.before_upbit_symbols_list = self.get_upbit_symbol_list()
        self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        self.stop_restart_websocket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self._start_websocket()

        while True:
            if (not self.local_redis.get_all_exchange_stream_data("ticker", "UPBIT_SPOT") or
                not self.local_redis.get_all_exchange_stream_data("orderbook", "UPBIT_SPOT")):
                self.websocket_logger.info("[UPBIT SPOT] Waiting for websocket data to be loaded...")
                time.sleep(2)
            else:
                break

        self.monitor_shared_symbol_change_thread = Thread(
            target=self.monitor_shared_symbol_change, daemon=True
        )
        self.monitor_shared_symbol_change_thread.start()

    def __del__(self):
        self.terminate_websocket()

    def _start_websocket(self):
        def handle_price_procs():
            while True:
                try:
                    if not self.stop_restart_websocket:
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
                                self.websocket_logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_ticker_proc terminated."
                                )
                            elif ticker_proc_name not in self.websocket_proc_dict:
                                ticker_start_proc = True
                                self.websocket_logger.info(
                                    f"{index}th Upbit ticker websocket does not exist. Starting..."
                                )
                                self.websocket_logger.info(
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
                                    self.websocket_logger.info(
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
                                self.websocket_logger.info(
                                    f"upbit_orderbook_ticker_websocket|{index}th upbit_orderbook_proc terminated."
                                )
                            elif orderbook_proc_name not in self.websocket_proc_dict:
                                orderbook_start_proc = True
                                self.websocket_logger.info(
                                    f"{index}th Upbit orderbook websocket does not exist. Starting..."
                                )
                                self.websocket_logger.info(
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
                                    self.websocket_logger.info(
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
                    self.websocket_logger.error(content)
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
        self.websocket_logger.info("[UPBIT SPOT] All websockets' events have been set.")
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
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status
        else:
            proc_status = all([x.is_alive() for x in self.websocket_proc_dict.values()])
            print_text = ""
            for key, value in self.websocket_proc_dict.items():
                print_text += f"[UPBIT SPOT]{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            if include_text:
                return (proc_status, print_text)
            return proc_status

    def monitor_shared_symbol_change(self, loop_time_secs=60):
        self.websocket_logger.info("[UPBIT SPOT]started monitor_shared_symbol_change..")
        while True:
            time.sleep(loop_time_secs)
            try:
                new_upbit_symbols_list = self.get_upbit_symbol_list()
                
                if sorted(self.before_upbit_symbols_list) != sorted(new_upbit_symbols_list):
                    deleted_spot_shared_symbol = [x for x in self.before_upbit_symbols_list if x not in new_upbit_symbols_list]
                    added_spot_shared_symbol = [x for x in new_upbit_symbols_list if x not in self.before_upbit_symbols_list]
                    content = f"monitor_shared_symbol_change|[UPBIT SPOT]SPOT shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.websocket_logger.info(content)
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
                            self.websocket_logger.info(f"monitor_shared_symbol_change|deleting {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("ticker", "UPBIT_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                        try:
                            self.websocket_logger.info(f"monitor_shared_symbol_change|deleting {each_spot_shared_symbol} from redis..")
                            self.local_redis.delete_exchange_stream_data("orderbook", "UPBIT_SPOT", each_spot_shared_symbol)
                        except Exception:
                            self.websocket_logger.error(f"monitor_shared_symbol_change|{traceback.format_exc()}")
                                    
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.acw_api.create_message_thread(self.admin_id, 'monitor_shared_symbol_change', content)

    def get_price_df(self):
        upbit_ticker_df = pd.DataFrame(self.local_redis.get_all_exchange_stream_data("ticker", "UPBIT_SPOT")).T.reset_index()[['index','tp','scr','atp24h','h52wp','l52wp','ms','mw','tms']]
        upbit_orderbook_df = pd.DataFrame(self.local_redis.get_all_exchange_stream_data("orderbook", "UPBIT_SPOT")).T.reset_index(drop=True)[['cd','tms','obu']]
        upbit_orderbook_df['ap'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['ap'])
        upbit_orderbook_df['bp'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['bp'])
        upbit_orderbook_df.drop('obu', axis=1, inplace=True)
        upbit_merged_df = pd.merge(upbit_ticker_df, upbit_orderbook_df, left_on='index', right_on='cd', how='inner')
        upbit_merged_df['base_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[1])
        upbit_merged_df['quote_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[0])
        upbit_merged_df.drop('index', axis=1, inplace=True)
        upbit_merged_df.loc[:, ['scr','atp24h','h52wp','l52wp','ap','bp']] = upbit_merged_df.loc[:, ['scr','atp24h','h52wp','l52wp','ap','bp']].astype(float)
        upbit_merged_df.loc[:, 'scr'] = upbit_merged_df['scr'] * 100
        return upbit_merged_df