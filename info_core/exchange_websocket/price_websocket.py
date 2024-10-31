from multiprocessing import Process, Manager
from threading import Thread
import datetime
import time
import pandas as pd
import websocket
import json

from upbit.client import Upbit

# Global variables Initialization
OKX_TICKER_DICT = None
OKX_TICKER_PROC_LIST = None
UPBIT_TICKER_DICT = None
UPBIT_ORDERBOOK_DICT = None
UPBIT_TICKER_PROC_LIST = None
UPBIT_ORDERBOOK_PROC_LIST = None

def list_slice(lst, n):
    sliced_nested_list = []
    for i in range(n):
        sliced_nested_list.append(lst[i::n])
    return sliced_nested_list

##################################################################################################################################

def okx_ticker_websocket(both_listed_okx_symbols, proc_n, price_websocket_logger):
    global OKX_TICKER_DICT
    global OKX_TICKER_PROC_LIST

    def okx_websocket(okx_result_dict, data):
        def on_message(ws, message):
            message_dict = json.loads(message)
            if 'data' in message_dict.keys():
                # print(message_dict)
                okx_result_dict[message_dict['data'][0]['instId']] = message_dict['data'][0]

        def on_error(ws, error):
            price_websocket_logger.error(f'okx_ticker_websocket|okx_websocket on_error executed!\n Error: {error}')
            pass

        def on_close(ws, close_status_code, close_msg):
            price_websocket_logger.info(f"okx_ticker_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

        def on_open(ws):
            # print(f'okx_ticker_websocket on_open started')
            price_websocket_logger.info('okx_ticker_websocket|okx_websocket started')
            ws.send(json.dumps(data))

        # websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://ws.okx.com:8443/ws/v5/public",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
        ws.run_forever()

    sliced_both_listed_okx_symbols_list = list_slice(both_listed_okx_symbols, proc_n)

    manager = Manager()
    OKX_TICKER_DICT = manager.dict()

    OKX_TICKER_PROC_LIST = []

    for i, each_both_listed_okx_symbols in enumerate(sliced_both_listed_okx_symbols_list):
        okx_ticker_data = {"op": "subscribe", "args": []}
        for each_symbol in each_both_listed_okx_symbols:
            okx_ticker_data['args'].append({"channel": "tickers", "instId": each_symbol})

        okx_ticker_proc = Process(target=okx_websocket, args=(OKX_TICKER_DICT, okx_ticker_data), daemon=True)
        OKX_TICKER_PROC_LIST.append(okx_ticker_proc)
        okx_ticker_proc.start()
        # print(f"{i+1}th upbit_ticker_proc started.")
        price_websocket_logger.info(f"okx_ticker_websocket|{i+1}th okx_ticker_proc started.")
        time.sleep(0.5)

    for each_proc in OKX_TICKER_PROC_LIST:
        each_proc.join()

def upbit_orderbook_ticker_websocket(both_listed_upbit_symbols, proc_n, price_websocket_logger):
    global UPBIT_TICKER_DICT
    global UPBIT_ORDERBOOK_DICT
    global UPBIT_TICKER_PROC_LIST
    global UPBIT_ORDERBOOK_PROC_LIST

    def upbit_websocket(upbit_result_dict, data):
        def on_message(ws, message):
            message_dict = json.loads(message)
            # if message_dict['cd'] == 'KRW-BCH':                                                         # test
            #     print(message_dict['tp'], datetime.datetime.fromtimestamp(message_dict['tms']/1000))    # test
            upbit_result_dict[message_dict['cd']] = message_dict

        def on_error(ws, error):
            # print(f'upbit_websocket on_error executed!')
            # print(error)
            price_websocket_logger.error(f'upbit_orderbook_ticker_websocket|upbit_websocket on_error executed!\n Error: {error}')
            pass

        def on_close(ws, close_status_code, close_msg):
            # print(f"\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")
            price_websocket_logger.info(f"upbit_orderbook_ticker_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")

        def on_open(ws):
            # print(f'upbit_websocket started')
            price_websocket_logger.info(f'upbit_orderbook_ticker_websocket|upbit_websocket started')
            ws.send(json.dumps(data))

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp("wss://api.upbit.com/websocket/v1",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
        ws.run_forever()

    sliced_both_listed_upbit_symbols_list = list_slice(both_listed_upbit_symbols, proc_n)

    manager = Manager()
    UPBIT_TICKER_DICT = manager.dict()
    UPBIT_ORDERBOOK_DICT = manager.dict()

    UPBIT_TICKER_PROC_LIST = []
    UPBIT_ORDERBOOK_PROC_LIST = []

    for i, each_both_listed_upbit_symbols in enumerate(sliced_both_listed_upbit_symbols_list):
        upbit_ticker_data = [{"ticket":"people9"},{"type":"ticker","codes":each_both_listed_upbit_symbols}, {"format":"SIMPLE"}]
        upbit_orderbook_data = [{"ticket":"people9"},{"type":"orderbook","codes":[x+'.1' for x in each_both_listed_upbit_symbols]}, {"format":"SIMPLE"}]

        upbit_ticker_proc = Process(target=upbit_websocket, args=(UPBIT_TICKER_DICT, upbit_ticker_data), daemon=True)
        UPBIT_TICKER_PROC_LIST.append(upbit_ticker_proc)
        upbit_ticker_proc.start()
        # print(f"{i+1}th upbit_ticker_proc started.")
        price_websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_ticker_proc started.")
        time.sleep(0.5)

        upbit_orderbook_proc = Process(target=upbit_websocket, args=(UPBIT_ORDERBOOK_DICT, upbit_orderbook_data), daemon=True)
        UPBIT_ORDERBOOK_PROC_LIST.append(upbit_orderbook_proc)
        upbit_orderbook_proc.start()
        # print(f"{i+1}th upbit_orderbook_proc started.")
        price_websocket_logger.info(f"upbit_orderbook_ticker_websocket|{i+1}th upbit_orderbook_proc started.")
        time.sleep(0.5)

    for each_proc in UPBIT_TICKER_PROC_LIST:
        each_proc.join()
    for each_proc in UPBIT_ORDERBOOK_PROC_LIST:
        each_proc.join()
    

def okx_upbit_websocket(both_listed_okx_symbols, both_listed_upbit_symbols, proc_n, price_websocket_logger):
    price_websocket_logger.info("okx_upbit_websocket|price_websocket.okx_upbit_websocket executed")
    okx_ticker_websocket_th = Thread(target=okx_ticker_websocket, args=(both_listed_okx_symbols, proc_n, price_websocket_logger), daemon=True)
    okx_ticker_websocket_th.start()
    time.sleep(0.5)
    upbit_orderbook_ticker_websocket(both_listed_upbit_symbols, proc_n, price_websocket_logger)
    okx_ticker_websocket_th.join()


def check_proc_status(OKX_TICKER_PROC_LIST, UPBIT_TICKER_PROC_LIST, UPBIT_ORDERBOOK_PROC_LIST, price_websocket_logger, print_status=False):
    whole_status_flag_list = []
    whole_status_str = 'Proc Status'
    
    if OKX_TICKER_PROC_LIST is not None:
        for i, each_proc in enumerate(OKX_TICKER_PROC_LIST):
            each_proc_status = each_proc.is_alive()
            whole_status_flag_list.append(each_proc_status)
            status_str = f"\n{i+1}th okx_ticker_proc status: {each_proc_status}"
            whole_status_str += status_str
            if print_status:
                print(status_str.strip())
    if UPBIT_TICKER_PROC_LIST is not None:
        for i, each_proc in enumerate(UPBIT_TICKER_PROC_LIST):
            each_proc_status = each_proc.is_alive()
            whole_status_flag_list.append(each_proc_status)
            status_str = f"\n{i+1}th upbit_ticker_proc status: {each_proc_status}"
            whole_status_str += status_str
            if print_status:
                print(status_str.strip())
    if UPBIT_ORDERBOOK_PROC_LIST is not None:
        for i, each_proc in enumerate(UPBIT_ORDERBOOK_PROC_LIST):
            each_proc_status = each_proc.is_alive()
            whole_status_flag_list.append(each_proc_status)
            status_str = f"\n{i+1}th upbit_orderbook_proc status: {each_proc_status}"
            whole_status_str += status_str
            if print_status:
                print(status_str.strip())
    if print_status:
        # print(f"whole_status_flag_list: {whole_status_flag_list}")
        price_websocket_logger.info(f"check_proc_status|whole_status_flag_list: {whole_status_flag_list}")
    integrity_flag = sum(whole_status_flag_list) == len(whole_status_flag_list)
    if print_status:
        # print(f"Integrity Flag: {integrity_flag}")
        price_websocket_logger.info(f"check_proc_status|Integrity Flag: {integrity_flag}")
    return integrity_flag, whole_status_str

def terminate_websocket_proc(OKX_TICKER_PROC_LIST, UPBIT_TICKER_PROC_LIST, UPBIT_ORDERBOOK_PROC_LIST, price_websocket_logger):
    for i, each_proc in enumerate(OKX_TICKER_PROC_LIST):
        # print(f"terminating {i+1}th okx_ticker_proc..")
        price_websocket_logger.info(f"terminate_websocket_proc|terminating {i+1}th okx_ticker_proc..")
        each_proc.terminate()
    for i, each_proc in enumerate(UPBIT_TICKER_PROC_LIST):
        # print(f"terminating {i+1}th upbit_ticker_proc..")
        price_websocket_logger.info(f"terminate_websocket_proc|terminating {i+1}th upbit_ticker_proc..")
        each_proc.terminate()
    for i, each_proc in enumerate(UPBIT_ORDERBOOK_PROC_LIST):
        # print(f"terminating {i+1}th upbit_orderbook_proc..")
        price_websocket_logger.info(f"terminate_websocket_proc|terminating {i+1}th upbit_orderbook_proc..")
        each_proc.terminate()
    time.sleep(2)
    for i, each_proc in enumerate(OKX_TICKER_PROC_LIST):
        # print(f"{i+1}th okx_ticker_proc is_alive: {each_proc.is_alive()}")
        price_websocket_logger.info(f"terminate_websocket_proc|{i+1}th okx_ticker_proc is_alive: {each_proc.is_alive()}")
    for i, each_proc in enumerate(UPBIT_TICKER_PROC_LIST):
        # print(f"{i+1}th upbit_ticker_proc is_alive: {each_proc.is_alive()}")
        price_websocket_logger.info(f"terminate_websocket_proc|{i+1}th upbit_ticker_proc is_alive: {each_proc.is_alive()}")
    for i, each_proc in enumerate(UPBIT_ORDERBOOK_PROC_LIST):
        # print(f"{i+1}th upbit_orderbook_proc is_alive: {each_proc.is_alive()}")
        price_websocket_logger.info(f"terminate_websocket_proc|{i+1}th upbit_orderbook_proc is_alive: {each_proc.is_alive()}")
