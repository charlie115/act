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
from loggers.logger import KimpBotLogger
from exchange_websocket.utils import list_slice
from etc.redis_connector.redis_connector import InitRedis

class UpbitWebsocket:
    def __init__(self, admin_id, node, proc_n, get_upbit_symbol_list, register_monitor_msg, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.register_monitor_msg = register_monitor_msg
        self.get_upbit_symbol_list = get_upbit_symbol_list
        self.websocket_logger = KimpBotLogger("upbit_websocket", logging_dir).logger
        manager = Manager()
        self.upbit_ticker_dict = manager.dict()
        self.upbit_orderbook_dict = manager.dict()
        self.proc_n = proc_n
        self.before_upbit_symbols_list = self.get_upbit_symbol_list()
        self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        self.stop_restart_webscoket = False
        self.price_proc_event_list = []
        self.websocket_proc_dict = {}
        self.websocket_symbol_dict = {}
        self.redis_client_db1 = InitRedis(db=1)
        self._start_websocket()
        while True:
            if self.upbit_ticker_dict.values() == [] or self.upbit_orderbook_dict.values() == []:
                self.websocket_logger.info(f"[UPBIT SPOT]waiting for websocket data to be loaded..")
                time.sleep(2)
            else:
                break
        self.monitor_shared_symbol_change_thread = Thread(target=self.monitor_shared_symbol_change, daemon=True)
        self.monitor_shared_symbol_change_thread.start()
        self.monitor_websocket_last_update_thread = Thread(target=self.monitor_websocket_last_update, daemon=True)
        self.monitor_websocket_last_update_thread.start()
        self.ticker_column_name_dict = {
            'ty': 'type', # ticker
            'cd': 'code', # ex) KRW-BTC
            'op': 'opening_price',
            'hp': 'high_price',
            'lp': 'low_price',
            'tp': 'trade_price',
            'pcp': 'prev_closing_price', # 전일 종가
            'c': 'change', # 전일 대비, RISE or EVEN or FALL
            'cp': 'change_price', # 전일 대비 변화액의 절대값
            'scp': 'signed_change_price', # 전일 대비 변화액의 부호를 가진 값
            'cr': 'change_rate', # 전일 대비 변화율
            'scr': 'signed_change_rate', # 전일 대비 변화율의 부호를 가진 값
            'tv': 'trade_volume', # 가장 최근 거래량
            'atv': 'acc_trade_volume', # 누적 거래량(UTC 0시 기준)
            'atv24h': 'acc_trade_volume_24h', # 24시간 누적 거래량
            'atp': 'acc_trade_price', # 누적 거래대금(UTC 0시 기준)
            'atp24h': 'acc_trade_price_24h', # 24시간 누적 거래대금
            'tdt': 'trade_date_time', # 가장 최근 거래 일자(UTC 기준)
            'ttm': 'trade_time', # 가장 최근 거래 시각(UTC 기준)
            'ttms': 'trade_timestamp', # 가장 최근 거래 타임스탬프
            'ab': 'ask_bid', # 매수/매도 구분
            'aav': 'acc_ask_volume', # 누적 매도량
            'abv': 'acc_bid_volume', # 누적 매수량
            'h52wp': 'highest_52_week_price', # 52주 최고가
            'h52wdt': 'highest_52_week_date', # 52주 최고가 달성일
            'l52wp': 'lowest_52_week_price', # 52주 최저가
            'l52wdt': 'lowest_52_week_date', # 52주 최저가 달성일
            # 'ts': 'trade_status', # 거래상태, Deprecated
            'ms': 'market_state', # 거래상태, PREVIEW(입금지원), ACTIVE(거래지원가능), DELISTED(거래지원종료)
            'msfi': 'market_state_for_ios', # 거래상태, Deprecated
            'its': 'is_trading_suspended', # 거래정지 여부
            'dd': 'delisting_date', # 상장폐지일
            'mw': 'market_warning', # 유의 종목 여부, NONE or CAUTION
            'tms': 'timestamp', # 타임스탬프
            'st': 'stream_type' # 스트림 타입, SNAPSHOT or REALTIME
        }
        self.orderbook_column_name_dict = {
            'ty': 'type', # orderbook
            'cd': 'code', # ex) KRW-BTC
            'tas': 'total_ask_size', # 호가 매도 총 잔량
            'tbs': 'total_bid_size', # 호가 매수 총 잔량
            'obu': 'orderbook_units', # 호가 List Object
            'ap': 'ask_price', # 매도호가
            'bp': 'bid_price', # 매수호가
            'as': 'ask_size', # 매도 잔량
            'bs': 'bid_size', # 매수 잔량
            'tms': 'timestamp', # 타임스탬프
        }

    def __del__(self):
        self.terminate_websocket()

    def upbit_websocket(self, upbit_result_dict, data, error_event, data_name):
        def on_message(ws, message):
            if error_event.is_set():
                ws.close()
                raise Exception("upbit_websocket|error_event is set. closing websocket..")
            message_dict = json.loads(message)
            # if message_dict['cd'] == 'KRW-BCH':                                                         # test
            #     print(message_dict['tp'], datetime.datetime.fromtimestamp(message_dict['tms']/1000))    # test
            upbit_result_dict[message_dict['cd']] = {**message_dict, "last_update_timestamp": int(datetime.datetime.utcnow().timestamp()*1000000)}
            # self.redis_client_db1.set_data(f"INFO_CORE|UPBIT_SPOT|{data_name}|{message_dict['cd']}", json.dumps({**message_dict, "last_update_timestamp": int(datetime.datetime.utcnow().timestamp() * 1000000)}))
            # self.redis_client_db1.set_data(f"INFO_CORE|UPBIT_SPOT|{data_name}", pickle.dumps(dict(upbit_result_dict)))

        def on_error(ws, error):
            # print(f'upbit_websocket on_error executed!')
            # print(error)
            self.websocket_logger.error(f'upbit_websocket|upbit_websocket on_error executed!\n Error: {error}')
            pass

        def on_close(ws, close_status_code, close_msg):
            # print(f"\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")
            self.websocket_logger.info(f"upbit_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

        def on_open(ws):
            # print(f'upbit_websocket started')
            self.websocket_logger.info(f'upbit_websocket|upbit_websocket started')
            ws.send(json.dumps(data))

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://api.upbit.com/websocket/v1",
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
                                self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_ticker_proc terminated.")
                            elif f"{i+1}th_ticker_proc" not in self.websocket_proc_dict.keys():
                                ticker_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Upbit ticker websocket does not exist. starting..")
                                self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_ticker_proc started.")
                            if ticker_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"] = self.sliced_upbit_symbols_list[i]
                                upbit_ticker_data = [{"ticket":"kp_info_loader"},{"type":"ticker","codes":self.sliced_upbit_symbols_list[i]}, {"format":"SIMPLE"}]
                                upbit_ticker_proc = Process(target=self.upbit_websocket, args=(self.upbit_ticker_dict, upbit_ticker_data, error_event, "ticker"), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_ticker_proc"] = upbit_ticker_proc
                                upbit_ticker_proc.start()
                                if ticker_restarted:
                                    content = f"restarted {i+1}th Upbit ticker websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                                    self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'upbit ticker websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)

                            time.sleep(0.5)
                            orderbook_start_proc = False
                            orderbook_restarted = False
                            if f"{i+1}th_orderbook_proc" in self.websocket_proc_dict.keys() and not self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                                orderbook_start_proc = True
                                orderbook_restarted = True
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
                                self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_orderbook_proc terminated.")
                            elif f"{i+1}th_orderbook_proc" not in self.websocket_proc_dict.keys():
                                orderbook_start_proc = True
                                self.websocket_logger.info(f"{i+1}th Upbit orderbook websocket does not exist. starting..")
                                self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_orderbook_proc started.")
                            if orderbook_start_proc is True:
                                error_event = Event()
                                self.price_proc_event_list.append(error_event)
                                self.websocket_symbol_dict[f"{i+1}th_orderbook_symbol"] = self.sliced_upbit_symbols_list[i]
                                upbit_orderbook_data = [{"ticket":"kp_info_loader"},{"type":"orderbook","codes":[x+'.1' for x in self.sliced_upbit_symbols_list[i]]}, {"format":"SIMPLE"}]
                                upbit_orderbook_proc = Process(target=self.upbit_websocket, args=(self.upbit_orderbook_dict, upbit_orderbook_data, error_event, "orderbook"), daemon=True)
                                self.websocket_proc_dict[f"{i+1}th_orderbook_proc"] = upbit_orderbook_proc
                                upbit_orderbook_proc.start()
                                if orderbook_restarted:
                                    content = f"restarted {i+1}th Upbit orderbook websocket.. alive state: {self.websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                                    self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{content}")
                                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'upbit orderbook websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
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
        # self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        # for name, each_proc in self.websocket_proc_dict.items():
        #     self.websocket_logger.info(f"Before termination of {name} process, alive status: {each_proc.is_alive()}")
        #     each_proc.terminate()
        #     self.websocket_logger.info(f"terminated {name}")
        # self.websocket_logger.info("[UPBIT SPOT]all upbit_ticker_proc and upbit_orderbook_proc terminated.")
        self.stop_restart_webscoket = True
        time.sleep(0.5)
        for each_event in self.price_proc_event_list:
            each_event.set()
        self.websocket_logger.info(f"[UPBIT SPOT]all websockets' event has been set")
        self.price_proc_event_list = []
        time.sleep(1)
        self.stop_restart_webscoket = False
    
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
                restart_websockets = False
                new_upbit_symbols_list = self.get_upbit_symbol_list()
                
                if sorted(self.before_upbit_symbols_list) != sorted(new_upbit_symbols_list):
                    restart_websockets = True
                    deleted_spot_shared_symbol = [x for x in self.before_upbit_symbols_list if x not in new_upbit_symbols_list]
                    added_spot_shared_symbol = [x for x in new_upbit_symbols_list if x not in self.before_upbit_symbols_list]
                    content = f"monitor_shared_symbol_change|[UPBIT SPOT]SPOT shared symbol changed. deleted: {deleted_spot_shared_symbol}, added: {added_spot_shared_symbol}"
                    self.websocket_logger.info(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_shared_symbol_change', content, code=None, sent_switch=0, send_counts=1, remark=None)
                    for each_spot_shared_symbol in deleted_spot_shared_symbol:
                        # remove deleted symbol from upbit_ticker_dict and upbit_orderbook_dict
                        try:
                            del self.upbit_ticker_dict[each_spot_shared_symbol]
                            # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|UPBIT_SPOT|ticker|{each_spot_shared_symbol}")
                        except Exception:
                            pass
                        try:
                            del self.upbit_orderbook_dict[each_spot_shared_symbol]
                            # self.redis_client_db1.redis_conn.delete(f"INFO_CORE|UPBIT_SPOT|orderbook|{each_spot_shared_symbol}")
                        except Exception:
                            pass
                
                if restart_websockets is True:
                    # Set the newer values to before values
                    self.before_upbit_symbols_list = new_upbit_symbols_list
                    # Set sliced values too
                    self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
                    # terminate websockets
                    self.terminate_websocket()
            except Exception as e:
                content = f"monitor_shared_symbol_change|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"monitor_shared_symbol_change", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def monitor_websocket_last_update(self, update_threshold_mins=10, loop_time_secs=15):
        self.websocket_logger.info(f"[UPBIT SPOT]started monitor_websocket_last_update..")
        while True:
            time.sleep(loop_time_secs)
            try:
                ticker_df = pd.DataFrame(dict(self.upbit_ticker_dict)).T.reset_index()
                orderbook_df = pd.DataFrame(dict(self.upbit_orderbook_dict)).T.reset_index()
                for i in range(self.proc_n):
                    allocated_symbol_list = self.websocket_symbol_dict[f"{i+1}th_ticker_symbol"]
                    # check ticker dict's last_update
                    allocated_ticker_df = ticker_df[ticker_df['cd'].isin(allocated_symbol_list)]
                    if len(allocated_ticker_df) == 0:
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc has no ticker_dict data. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                        continue
                    ticker_last_update = allocated_ticker_df['last_update_timestamp'].max()
                    # check orderbook dict's last_update
                    allocated_orderbook_df = orderbook_df[orderbook_df['cd'].isin(allocated_symbol_list)]
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
                        slow_ticker_symbol = allocated_ticker_df[allocated_ticker_df['last_update_timestamp'] == ticker_last_update]['cd'].values[0]
                        content = f"monitor_websocket_last_update|{i+1}th_ticker_proc {slow_ticker_symbol} last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', '[UPBIT SPOT]monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_ticker_proc"].join()
                    if (datetime.datetime.utcnow().timestamp() - orderbook_last_update/1000000) > update_threshold_mins*60:
                        slow_orderbook_symbol = allocated_orderbook_df[allocated_orderbook_df['last_update_timestamp'] == ticker_last_update]['cd'].values[0]
                        content = f"monitor_websocket_last_update|{i+1}th_orderbook_proc {slow_orderbook_symbol} last_update is older than {update_threshold_mins} mins. Restarting websocket.."
                        self.websocket_logger.info(content)
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', '[UPBIT SPOT]monitor_websocket_last_update', content, code=None, sent_switch=0, send_counts=1, remark=None)
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                        self.websocket_proc_dict[f"{i+1}th_orderbook_proc"].join()
            except Exception as e:
                content = f"monitor_websocket_last_update|{traceback.format_exc()}"
                self.websocket_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"[UPBIT SPOT]monitor_websocket_last_update", content=content, code=None, sent_switch=0, send_counts=1, remark=None)

    def get_price_df(self):
        upbit_ticker_df = pd.DataFrame(dict(self.upbit_ticker_dict)).T.reset_index()[['index','tp','scr','atp24h','h52wp','l52wp','ms','mw','tms']]
        upbit_orderbook_df = pd.DataFrame(dict(self.upbit_orderbook_dict)).T.reset_index(drop=True)[['cd','tms','obu']]
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
        


    