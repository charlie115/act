from multiprocessing import Process, Manager
from threading import Thread
import websocket
import json
import time

from utils import list_slice

# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger

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
        self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        # self.upbit_ticker_proc_list = []
        # self.upbit_orderbook_proc_list = []
        self.upbit_websocket_proc_dict = {}
        self._start_websocket()
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

    def upbit_websocket(self, upbit_result_dict, data):
        def on_message(ws, message):
            message_dict = json.loads(message)
            # if message_dict['cd'] == 'KRW-BCH':                                                         # test
            #     print(message_dict['tp'], datetime.datetime.fromtimestamp(message_dict['tms']/1000))    # test
            upbit_result_dict[message_dict['cd']] = message_dict

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
        def handle_upbit_procs():
            while True:
                for i in range(self.proc_n):
                    upbit_ticker_data = [{"ticket":"kp_info_loader"},{"type":"ticker","codes":self.sliced_upbit_symbols_list[i]}, {"format":"SIMPLE"}]
                    upbit_orderbook_data = [{"ticket":"kp_info_loader"},{"type":"orderbook","codes":[x+'.1' for x in self.sliced_upbit_symbols_list[i]]}, {"format":"SIMPLE"}]

                    if f"{i+1}th_ticker_proc" in self.upbit_websocket_proc_dict.keys() and not self.upbit_websocket_proc_dict[f"{i+1}th_ticker_proc"].is_alive():
                        self.upbit_websocket_proc_dict[f"{i+1}th_ticker_proc"].terminate()
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_ticker_proc terminated.")
                        upbit_ticker_proc = Process(target=self.upbit_websocket, args=(self.upbit_ticker_dict, upbit_ticker_data), daemon=True)
                        self.upbit_websocket_proc_dict[f"{i+1}th_ticker_proc"] = upbit_ticker_proc
                        upbit_ticker_proc.start()
                        content = f"restarted {i+1}th Upbit ticker websocket.. alive state: {self.upbit_websocket_proc_dict[f'{i+1}th_ticker_proc'].is_alive()}"
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{content}")
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'upbit ticker websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
                    elif f"{i+1}th_ticker_proc" not in self.upbit_websocket_proc_dict.keys():
                        self.websocket_logger.info(f"{i+1}th Upbit ticker websocket does not exist. starting..")
                        upbit_ticker_proc = Process(target=self.upbit_websocket, args=(self.upbit_ticker_dict, upbit_ticker_data), daemon=True)
                        self.upbit_websocket_proc_dict[f"{i+1}th_ticker_proc"] = upbit_ticker_proc
                        upbit_ticker_proc.start()
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_ticker_proc started.")

                    if f"{i+1}th_orderbook_proc" in self.upbit_websocket_proc_dict.keys() and not self.upbit_websocket_proc_dict[f"{i+1}th_orderbook_proc"].is_alive():
                        self.upbit_websocket_proc_dict[f"{i+1}th_orderbook_proc"].terminate()
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_orderbook_proc terminated.")
                        upbit_orderbook_proc = Process(target=self.upbit_websocket, args=(self.upbit_orderbook_dict, upbit_orderbook_data), daemon=True)
                        self.upbit_websocket_proc_dict[f"{i+1}th_orderbook_proc"] = upbit_orderbook_proc
                        upbit_orderbook_proc.start()
                        content = f"restarted {i+1}th Upbit orderbook websocket.. alive state: {self.upbit_websocket_proc_dict[f'{i+1}th_orderbook_proc'].is_alive()}"
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{content}")
                        self.register_monitor_msg.register(self.admin_id, self.node, 'monitor', 'upbit orderbook websocket restart', content, code=None, sent_switch=0, send_counts=1, remark=None)
                    elif f"{i+1}th_orderbook_proc" not in self.upbit_websocket_proc_dict.keys():
                        self.websocket_logger.info(f"{i+1}th Upbit orderbook websocket does not exist. starting..")
                        upbit_orderbook_proc = Process(target=self.upbit_websocket, args=(self.upbit_orderbook_dict, upbit_orderbook_data), daemon=True)
                        self.upbit_websocket_proc_dict[f"{i+1}th_orderbook_proc"] = upbit_orderbook_proc
                        upbit_orderbook_proc.start()
                        self.websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_orderbook_proc started.")
                    time.sleep(0.15)
                time.sleep(0.25)
        self.handle_upbit_procs_thread = Thread(target=handle_upbit_procs, daemon=True)
        self.handle_upbit_procs_thread.start()

    def terminate_websocket(self):
        self.sliced_upbit_symbols_list = list_slice(self.get_upbit_symbol_list(), self.proc_n)
        for name, each_proc in self.upbit_websocket_proc_dict.items():
            each_proc.terminate()
            self.websocket_logger.info(f"terminated {name}.")
        self.websocket_logger.info("all upbit_ticker_proc and upbit_orderbook_proc terminated.")
    
    def check_status(self, print_result=False):
        if len(self.upbit_websocket_proc_dict) == 0:
            proc_status = False
            print_text = "Upbit websocket proc is not running."
            return proc_status
        else:
            print_text = ""
            for key, value in self.upbit_websocket_proc_dict.items():
                print_text += f"{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            return all([x.is_alive() for x in self.upbit_websocket_proc_dict.values()])
        


    