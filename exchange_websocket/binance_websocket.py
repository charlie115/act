from multiprocessing import Process, Manager, Queue
from binance import ThreadedWebsocketManager
from binance.enums import FuturesType
import traceback
import time
import queue

from utils import list_slice

# set directory to upper directory
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from loggers.logger import KimpBotLogger


class BinanceWebsocket:
    def __init__(self, get_binance_spot_symbol_list, get_binance_usdm_symbol_list, get_binance_coinm_symbol_list, proc_n, logging_dir):
        self.websocket_logger = KimpBotLogger("binance_websocket", logging_dir).logger
        self.get_binance_usdm_symbol_list = get_binance_usdm_symbol_list
        self.get_binance_coinm_symbol_list = get_binance_coinm_symbol_list
        self.get_binance_spot_symbol_list = get_binance_spot_symbol_list
        self.binance_websocket_proc_dict = {}
        manager = Manager()
        self.binance_usdm_bookticker_dict = manager.dict()
        self.binance_usdm_ticker_dict = manager.dict()
        self.binance_coinm_bookticker_dict = manager.dict()
        self.binance_coinm_ticker_dict = manager.dict()
        self.binance_spot_bookticker_dict = manager.dict()
        self.binance_spot_ticker_dict = manager.dict()
        self.proc_n = proc_n
        # self.binance_usdm_bookticker_proc_list = []
        # self.binance_usdm_ticker_proc_list = []
        # self.binance_coinm_bookticker_proc_list = []
        # self.binance_coinm_ticker_proc_list = []
        # self.binance_spot_bookticker_proc_list = []
        # self.binance_spot_ticker_proc_list = []
        self.sliced_binance_usdm_symbols_list = list_slice(self.get_binance_usdm_symbol_list(), self.proc_n)
        self.sliced_binance_coinm_symbols_list = list_slice(self.get_binance_coinm_symbol_list(), self.proc_n)
        self.sliced_binance_spot_symbols_list = list_slice(self.get_binance_spot_symbol_list(), self.proc_n)
        self.binance_usdm_liquidation_list = manager.list()
        self.binance_coinm_liquidation_list = manager.list()
        self.binance_kline_type_list = ['1m','3m','5m','15m','30m','1h','4h','6h','8h','12h','1d','1w','1M']
        # self.binance_usdm_kline_queue_dict = manager.dict()
        self.binance_usdm_kline_queue_dict = {}
        for each_symbol in self.get_binance_usdm_symbol_list():
            self.binance_usdm_kline_queue_dict[each_symbol] = Queue()
        # self.binance_coinm_kline_queue_dict = manager.dict()
        self.binance_coinm_kline_queue_dict = {}
        for each_symbol in self.get_binance_coinm_symbol_list():
            self.binance_coinm_kline_queue_dict[each_symbol] = Queue()
        # self.binance_spot_kline_queue_dict = manager.dict()
        self.binance_spot_kline_queue_dict = {}
        for each_symbol in self.get_binance_spot_symbol_list():
            self.binance_spot_kline_queue_dict[each_symbol] = Queue()
        self._start_websocket()

    def __del__(self):
        self.terminate_websocket()

    # For fetching ticker, bookticker data for usdm, coinm, spot
    def binance_price_websocket(self, binance_usdm_bookticker_dict, binance_usdm_ticker_dict,
                           binance_coinm_bookticker_dict, binance_coinm_ticker_dict, 
                           binance_spot_bookticker_dict, binance_spot_ticker_dict,
                           binance_usdm_symbol_list, binance_coinm_symbol_list, binance_spot_symbol_list):
        def handle_usdm_bookticker_streams(msg):
             # event_type = msg['stream']
            # print(msg['data']) # test
            # if msg['data']['s'] == 'ETHUSDT': # test
            #     print(msg['data']['T']) # test
            try:
                binance_usdm_bookticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_usdm_bookticker_streams|{traceback.format_exc()}")
        def handle_usdm_ticker_streams(msg):
            try:
                binance_usdm_ticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_usdm_ticker_streams|{traceback.format_exc()}")
        def handle_coinm_bookticker_streams(msg):
            try:
                # event_type = msg['stream']
                # print(msg['data']) # test
                # if msg['data']['s'] == 'ETHUSDT': # test
                #     print(msg['data']['T']) # test
                binance_coinm_bookticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_coinm_bookticker_streams|{traceback.format_exc()}")
        def handle_coinm_ticker_streams(msg):
            try:
                binance_coinm_ticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_coinm_ticker_streams|{traceback.format_exc()}")
        def handle_spot_bookticker_streams(msg):
            try:
                # event_type = msg['stream']
                # print(msg['data']) # test
                # if msg['data']['s'] == 'ETHUSDT': # test
                #     print(msg['data']['T']) # test
                binance_spot_bookticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_spot_bookticker_streams|{traceback.format_exc()}")
        def handle_spot_ticker_streams(msg):
            try:
                binance_spot_ticker_dict[msg['data']['s']] = msg['data']
            except Exception:
                self.websocket_logger.error(f"handle_spot_ticker_streams|{traceback.format_exc()}")
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if binance_usdm_symbol_list != []:
            usdm_bookticker_list = [x.lower()+'@bookTicker' for x in binance_usdm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_usdm_bookticker_streams, streams=usdm_bookticker_list)
            usdm_ticker_list = [x.lower()+'@ticker' for x in binance_usdm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_usdm_ticker_streams, streams=usdm_ticker_list)
        if binance_coinm_symbol_list != []:
            coinm_bookticker_list = [x.lower()+'@bookTicker' for x in binance_coinm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_coinm_bookticker_streams, streams=coinm_bookticker_list, futures_type=FuturesType.COIN_M)
            coinm_ticker_list = [x.lower()+'@ticker' for x in binance_coinm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_coinm_ticker_streams, streams=coinm_ticker_list, futures_type=FuturesType.COIN_M)
        if binance_spot_symbol_list != []:
            spot_bookticker_list = [x.lower()+'@bookTicker' for x in binance_spot_symbol_list]
            twm.start_multiplex_socket(callback=handle_spot_bookticker_streams, streams=spot_bookticker_list)
            spot_ticker_list = [x.lower()+'@ticker' for x in binance_spot_symbol_list]
            twm.start_multiplex_socket(callback=handle_spot_ticker_streams, streams=spot_ticker_list)
        twm.join()

    # For fetching liquidation data for usdm, coinm
    def binance_liquidation_websocket(self, binance_usdm_liquidation_list, binance_coinm_liquidation_list):
        self.websocket_logger.info("started binance_liquidation_websocket for usdm, coinm..")
        def handle_usdm_liquidation_streams(msg):
            try:
                if len(binance_usdm_liquidation_list) > 1000:
                    binance_usdm_liquidation_list.pop(0)
                # Filtering can be applied later.
                binance_usdm_liquidation_list.append(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_usdm_liquidation_streams|{traceback.format_exc()}")
        def handle_coinm_liquidation_streams(msg):
            try:
                if len(binance_coinm_liquidation_list) > 1000:
                    binance_coinm_liquidation_list.pop(0)
                # Filtering can be applied later.
                binance_coinm_liquidation_list.append(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_coinm_liquidation_streams|{traceback.format_exc()}")
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        twm.start_futures_multiplex_socket(callback=handle_usdm_liquidation_streams, streams=['!forceOrder@arr'])
        twm.start_futures_multiplex_socket(callback=handle_coinm_liquidation_streams, streams=['!forceOrder@arr'], futures_type=FuturesType.COIN_M)
        twm.join()

    def binance_kline_websocket(self, binance_usdm_kline_dict, binance_coinm_kline_dict, binance_spot_kline_dict, binance_usdm_symbol_list, binance_coinm_symbol_list, binance_spot_symbol_list):
        self.websocket_logger.info("started binance_kline_websocket for usdm, coinm, spot..")
        def handle_usdm_kline_streams(msg):
            try:
                symbol = msg['data']['s']
                if msg['data']['k']['x'] == True:
                    binance_usdm_kline_dict[symbol].put(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_usdm_kline_streams|{traceback.format_exc()}")
        def handle_coinm_kline_streams(msg):
            try:
                symbol = msg['data']['s']
                if msg['data']['k']['x'] == True:
                    binance_coinm_kline_dict[symbol].put(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_coinm_kline_streams|{traceback.format_exc()}")
        def handle_spot_kline_streams(msg):
            try:
                symbol = msg['data']['s']
                if msg['data']['k']['x'] == True:
                    binance_spot_kline_dict[symbol].put(msg['data'])
            except Exception:
                self.websocket_logger.error(f"handle_spot_kline_streams|{traceback.format_exc()}")
        twm = ThreadedWebsocketManager()
        twm.daemon = True
        twm.start()
        if binance_usdm_symbol_list != []:
            usdm_kline_list = []
            for kline_type in self.binance_kline_type_list:
                usdm_kline_list += [x.lower()+f'@kline_{kline_type}' for x in binance_usdm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_usdm_kline_streams, streams=usdm_kline_list)
        if binance_coinm_symbol_list != []:
            coinm_kline_list = []
            for kline_type in self.binance_kline_type_list:
                coinm_kline_list += [x.lower()+f'@kline_{kline_type}' for x in binance_coinm_symbol_list]
            twm.start_futures_multiplex_socket(callback=handle_coinm_kline_streams, streams=coinm_kline_list, futures_type=FuturesType.COIN_M)
        if binance_spot_symbol_list != []:
            spot_kline_list = []
            for kline_type in self.binance_kline_type_list:
                spot_kline_list += [x.lower()+f'@kline_{kline_type}' for x in binance_spot_symbol_list]
            twm.start_multiplex_socket(callback=handle_spot_kline_streams, streams=spot_kline_list)
        twm.join()

    def _start_websocket(self):
        for i in range(self.proc_n):
            binance_usdm_symbol_list = self.sliced_binance_usdm_symbols_list[i]
            binance_coinm_symbol_list = self.sliced_binance_coinm_symbols_list[i]
            binance_spot_symbol_list = self.sliced_binance_spot_symbols_list[i]
            binance_price_websocket_proc = Process(target=self.binance_price_websocket, args=(self.binance_usdm_bookticker_dict, self.binance_usdm_ticker_dict,
                                                                                    self.binance_coinm_bookticker_dict, self.binance_coinm_ticker_dict,
                                                                                    self.binance_spot_bookticker_dict, self.binance_spot_ticker_dict,
                                                                                    binance_usdm_symbol_list, binance_coinm_symbol_list, binance_spot_symbol_list), daemon=True)
            binance_price_websocket_proc.start()
            self.websocket_logger.info(f"started {i+1}th Binance price websocket for usdm, coinm, spot proc..")
            self.binance_websocket_proc_dict[f"{i+1}th_price_proc"] = binance_price_websocket_proc
            time.sleep(0.1)
        binance_liquidation_websocket_proc = Process(target=self.binance_liquidation_websocket, args=(self.binance_usdm_liquidation_list, self.binance_coinm_liquidation_list), daemon=True)
        binance_liquidation_websocket_proc.start()
        self.binance_websocket_proc_dict["usdm_liquidation_proc"] = binance_liquidation_websocket_proc
        binance_kline_websocket_proc = Process(target=self.binance_kline_websocket, args=(self.binance_usdm_kline_queue_dict, self.binance_coinm_kline_queue_dict, self.binance_spot_kline_queue_dict
                                                                                          ,self.get_binance_usdm_symbol_list(), self.get_binance_coinm_symbol_list(), self.get_binance_spot_symbol_list()), daemon=True)
        binance_kline_websocket_proc.start()
        self.binance_websocket_proc_dict["kline_proc"] = binance_kline_websocket_proc


    def check_status(self, print_result=False):
        if len(self.binance_websocket_proc_dict) == 0:
            proc_status = False
            print_text = "Binance websocket proc is not running."
            return proc_status
        else:
            print_text = ""
            for key, value in self.binance_websocket_proc_dict.items():
                print_text += f"{key} status: {value.is_alive()}\n"
            if print_result:
                print(print_text)
            return all([x.is_alive() for x in self.binance_websocket_proc_dict.values()])
        
    def terminate_websocket(self):
        for name, each_proc in self.binance_websocket_proc_dict.items():
            each_proc.terminate()
            self.websocket_logger.info(f"terminated {name}.")
        self.websocket_logger.info("all binance websocket terminated.")