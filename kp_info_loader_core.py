import pandas as pd
# from price_websocket import dict_convert, update_dollar, price_websocket
from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_plugin.bithumb_plug import InitBithumbAdaptor
from exchange_plugin.bybit_plug import InitBybitAdaptor
from exchange_websocket.binance_websocket import BinanceWebsocket, BinanceUSDMWebsocket, BinanceCOINMWebsocket
from exchange_websocket.upbit_websocket import UpbitWebsocket
from exchange_websocket.okx_websocket import OkxWebsocket, OkxUSDMWebsocket, OkxCOINMWebsocket
from exchange_websocket.bithumb_websocket import BithumbWebsocket
from exchange_websocket.bybit_websocket import BybitWebsocket, BybitUSDMWebsocket, BybitCOINMWebsocket
from loggers.logger import KimpBotLogger
from etc.redis_connector.redis_connector import InitRedis
from etc.db_handler.mongodb_client import InitDBClient
from kline_generator.kline_core import InitKlineCore
import _pickle as pickle
from threading import Thread
from multiprocessing import Process
import time
import datetime
import os
import traceback

current_file_dir = os.path.realpath(__file__)
current_folder_dir = os.path.abspath(os.path.join(current_file_dir, os.pardir))
logging_dir = f"{current_folder_dir}/loggers/logs/"

class InitCore:
    def __init__(self, logging_dir, proc_n, node, admin_id, register_monitor_msg, exchange_api_key_dict, enabled_markets_dict, db_dict):
        # Inital value setting
        self.logger = KimpBotLogger("kp_info_loader", logging_dir).logger
        self.price_websocket_logger = KimpBotLogger("price_websocket", logging_dir).logger
        self.update_dollar_logger = KimpBotLogger("update_dollar", logging_dir).logger
        self.logging_dir = logging_dir
        self.node = node
        self.admin_id = admin_id
        self.proc_n = proc_n
        self.monitor_websocket_switch = True
        self.exclude_outliers = True
        self.register_monitor_msg = register_monitor_msg
        self.exchange_api_key_dict = exchange_api_key_dict
        self.enabled_markets_dict = enabled_markets_dict
        self.db_client = InitDBClient(**db_dict)
        # TESTTEST
        self.upbit_symbols_to_exclude = []
        self.binance_usd_m_symbols_to_exclude = []
        # For redis connesction
        self.redis_client = InitRedis()

        self.logger.info(f"InitCore|InitCore initiated with proc_n={proc_n}")

        self.update_dollar_return_dict = {}
        self.update_dollar_thread = Thread(target=self.fetch_dollar_loop, args=(self.update_dollar_logger,), daemon=True)
        self.update_dollar_thread.start()

        self.info_dict = {}
        self.info_thread_dict = {}

        self.okx_adaptor = InitOkxAdaptor(self.exchange_api_key_dict['okx_read_only']['api_key'], self.exchange_api_key_dict['okx_read_only']['secret_key'], self.exchange_api_key_dict['okx_read_only']['passphrase'], logging_dir=self.logging_dir)
        self.upbit_adaptor = InitUpbitAdaptor(self.exchange_api_key_dict['upbit_read_only']['api_key'], self.exchange_api_key_dict['upbit_read_only']['secret_key'], self.info_dict, self.logging_dir)
        self.binance_adaptor = InitBinanceAdaptor(self.exchange_api_key_dict['binance_read_only']['api_key'], self.exchange_api_key_dict['binance_read_only']['secret_key'], self.info_dict, self.logging_dir)
        self.bithumb_adaptor = InitBithumbAdaptor(logging_dir=self.logging_dir)
        self.bybit_adaptor = InitBybitAdaptor(self.exchange_api_key_dict['bybit_read_only']['api_key'], self.exchange_api_key_dict['bybit_read_only']['secret_key'], self.info_dict, self.logging_dir)

        # UPBIT SPOT (KRW, BTC Market)
        # UPBIT wallet status
        # BINANCE SPOT, USD-M Futures, COIN-M Futures
        self.data_name_list = [
            "upbit_spot_info_df",
            "upbit_spot_ticker_df",
            # "upbit_wallet_status_df",
            "binance_spot_ticker_df",
            "binance_spot_info_df",
            "binance_usd_m_ticker_df",
            "binance_usd_m_info_df",
            "binance_coin_m_ticker_df",
            "binance_coin_m_info_df",
            "okx_spot_ticker_df",
            "okx_spot_info_df",
            "okx_usd_m_ticker_df",
            "okx_usd_m_info_df",
            "okx_coin_m_ticker_df",
            "okx_coin_m_info_df",
            "bithumb_spot_info_df",
            "bithumb_spot_ticker_df",
            # "bithumb_wallet_status_df",
            "bybit_spot_info_df",
            "bybit_spot_ticker_df",
            "bybit_usd_m_info_df",
            "bybit_usd_m_ticker_df",
            "bybit_coin_m_info_df",
            "bybit_coin_m_ticker_df"
        ]

        for data_name in self.data_name_list:
            if 'okx' in data_name:
                self.info_thread_dict[f"update_{data_name}"] = Thread(target=self.update_exchange_info_as_df, args=(data_name, 3), daemon=True)
            else:
                self.info_thread_dict[f"update_{data_name}"] = Thread(target=self.update_exchange_info_as_df, args=(data_name,), daemon=True)
            self.info_thread_dict[f"update_{data_name}"].start()
            self.logger.info(f"InitCore|update_{data_name} thread has started.")

        # Wait until all info df has been updated
        while True:
            if all([x in self.info_dict.keys() for x in self.data_name_list]):
                self.logger.info(f"InitCore|All info df has been updated.")
                break
            else:
                self.logger.info(f"InitCore|Waiting for all info to be updated.")
                time.sleep(2)

        self.exchange_websocket_dict = {}
        self.exchange_websocket_dict['UPBIT_SPOT'] = UpbitWebsocket(self.admin_id, self.node, self.proc_n, self.get_upbit_symbol_list, self.register_monitor_msg, self.logging_dir)
        self.exchange_websocket_dict['BITHUMB_SPOT'] = BithumbWebsocket(self.admin_id, self.node, self.proc_n, self.get_bithumb_symbol_list, self.register_monitor_msg, self.logging_dir)
        self.exchange_websocket_dict['BINANCE_SPOT'] = BinanceWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_spot_symbol_list, register_monitor_msg, "SPOT", self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_USD_M'] = BinanceUSDMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_usd_m_symbol_list, register_monitor_msg, "USD_M", self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_COIN_M'] = BinanceCOINMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_coin_m_symbol_list, register_monitor_msg, "COIN_M", self.info_dict, logging_dir)
        self.exchange_websocket_dict['OKX_SPOT'] = OkxWebsocket(self.admin_id, self.node, self.proc_n, self.get_okx_spot_symbol_list, register_monitor_msg, "SPOT", logging_dir)
        self.exchange_websocket_dict['OKX_USD_M'] = OkxUSDMWebsocket(self.admin_id, self.node, self.proc_n, self.get_okx_usd_m_symbol_list, register_monitor_msg, "USD_M", logging_dir)
        self.exchange_websocket_dict['OKX_COIN_M'] = OkxCOINMWebsocket(self.admin_id, self.node, self.proc_n, self.get_okx_coin_m_symbol_list, register_monitor_msg, "COIN_M", logging_dir)
        self.exchange_websocket_dict['BYBIT_SPOT'] = BybitWebsocket(self.admin_id, self.node, self.proc_n, self.get_bybit_spot_symbol_list, register_monitor_msg, "SPOT", self.info_dict, logging_dir)
        self.exchange_websocket_dict['BYBIT_USD_M'] = BybitUSDMWebsocket(self.admin_id, self.node, self.proc_n, self.get_bybit_usd_m_symbol_list, register_monitor_msg, "USD_M", self.info_dict, logging_dir)
        self.exchange_websocket_dict['BYBIT_COIN_M'] = BybitCOINMWebsocket(self.admin_id, self.node, self.proc_n, self.get_bybit_coin_m_symbol_list, register_monitor_msg, "COIN_M", self.info_dict, logging_dir)
        self.logger.info(f"InitCore|exchange_websocket_dict, {self.exchange_websocket_dict.keys()} has been initiated.")
        time.sleep(10)

        ## Start updating fundingrate
        self.binance_update_fundingrate_thread = Thread(target=self.update_fundingrate, args=("BINANCE", self.binance_adaptor), daemon=True)
        self.binance_update_fundingrate_thread.start()
        self.okx_update_fundingrate_thread = Thread(target=self.update_fundingrate, args=("OKX", self.okx_adaptor, 180), daemon=True)
        self.okx_update_fundingrate_thread.start()
        self.bybit_update_fundingrate_thread = Thread(target=self.update_fundingrate, args=("BYBIT", self.bybit_adaptor), daemon=True)
        self.bybit_update_fundingrate_thread.start()

        ## Start updating wallet status
        self.upbit_update_wallet_status_thread = Thread(target=self.update_wallet_status, args=("UPBIT", self.upbit_adaptor), daemon=True)
        self.upbit_update_wallet_status_thread.start()
        self.binance_update_wallet_status_thread = Thread(target=self.update_wallet_status, args=("BINANCE", self.binance_adaptor), daemon=True)
        self.binance_update_wallet_status_thread.start()
        self.okx_update_wallet_status_thread = Thread(target=self.update_wallet_status, args=("OKX", self.okx_adaptor), daemon=True)
        self.okx_update_wallet_status_thread.start()
        self.bithumb_update_wallet_status_thread = Thread(target=self.update_wallet_status, args=("BITHUMB", self.bithumb_adaptor), daemon=True)
        self.bithumb_update_wallet_status_thread.start()
        self.bybit_update_wallet_status_thread = Thread(target=self.update_wallet_status, args=("BYBIT", self.bybit_adaptor), daemon=True)
        self.bybit_update_wallet_status_thread.start()

        # Start kline generator
        self.kline_generator = InitKlineCore(self.admin_id, node, self.get_premium_df, self.get_market_code_list, register_monitor_msg, self.redis_client, self.db_client, logging_dir)

    def update_exchange_info_as_df(self, data_name, error_count_limit=1, loop_time_secs=30):
        error_count = 0
        while True:
            try:
                if data_name == "upbit_spot_info_df":
                    self.info_dict[data_name] = self.upbit_adaptor.spot_exchange_info()
                elif data_name == "upbit_spot_ticker_df":
                    self.info_dict[data_name] = self.upbit_adaptor.spot_all_tickers()
                elif data_name == "upbit_wallet_status_df":
                    self.info_dict[data_name] = self.upbit_adaptor.wallet_status()
                elif data_name == "binance_spot_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.spot_all_tickers()
                elif data_name == "binance_spot_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.spot_exchange_info()
                elif data_name == "binance_usd_m_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.usd_m_all_tickers()
                elif data_name == "binance_usd_m_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.usd_m_exchange_info()
                elif data_name == "binance_coin_m_ticker_df":
                    self.info_dict[data_name] = self.binance_adaptor.coin_m_all_tickers()
                elif data_name == "binance_coin_m_info_df":
                    self.info_dict[data_name] = self.binance_adaptor.coin_m_exchange_info()
                elif data_name == "okx_spot_ticker_df":
                    self.info_dict[data_name] = self.okx_adaptor.spot_all_tickers()
                elif data_name == "okx_spot_info_df":
                    self.info_dict[data_name] = self.okx_adaptor.spot_exchange_info()
                elif data_name == "okx_usd_m_ticker_df":
                    self.info_dict[data_name] = self.okx_adaptor.usd_m_all_tickers()
                elif data_name == "okx_usd_m_info_df":
                    self.info_dict[data_name] = self.okx_adaptor.usd_m_exchange_info()
                elif data_name == "okx_coin_m_ticker_df":
                    self.info_dict[data_name] = self.okx_adaptor.coin_m_all_tickers()
                elif data_name == "okx_coin_m_info_df":
                    self.info_dict[data_name] = self.okx_adaptor.coin_m_exchange_info()
                elif data_name == "bithumb_spot_info_df":
                    self.info_dict[data_name] = self.bithumb_adaptor.spot_exchange_info()
                elif data_name == "bithumb_spot_ticker_df":
                    self.info_dict[data_name] = self.bithumb_adaptor.spot_all_tickers()
                elif data_name == "bithumb_wallet_status_df":
                    self.info_dict[data_name] = self.bithumb_adaptor.wallet_status()
                elif data_name == "bybit_spot_info_df":
                    self.info_dict[data_name] = self.bybit_adaptor.spot_exchange_info()
                elif data_name == "bybit_spot_ticker_df":
                    self.info_dict[data_name] = self.bybit_adaptor.spot_all_tickers()
                elif data_name == "bybit_usd_m_info_df":
                    self.info_dict[data_name] = self.bybit_adaptor.usd_m_exchange_info()
                elif data_name == "bybit_usd_m_ticker_df":
                    self.info_dict[data_name] = self.bybit_adaptor.usd_m_all_tickers()
                elif data_name == "bybit_coin_m_info_df":
                    self.info_dict[data_name] = self.bybit_adaptor.coin_m_exchange_info()
                elif data_name == "bybit_coin_m_ticker_df":
                    self.info_dict[data_name] = self.bybit_adaptor.coin_m_all_tickers()
                else:
                    self.logger.error(f"update_exchange_info_as_df|name:{data_name} is not valid.")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} is not valid.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                    break
                time.sleep(loop_time_secs)
                error_count = 0
            except Exception as e:
                error_count += 1
                if error_count >= error_count_limit:
                    self.logger.error(f"update_exchange_info_as_df|name:{data_name}, {traceback.format_exc()}")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} failed.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(loop_time_secs)

    def get_dollar_dict(self):
        dollar_dict = self.redis_client.get_dict('INFO_CORE|dollar')
        return dollar_dict

    def get_market_code_list(self):
        market_code_list = []
        for exchange in self.exchange_websocket_dict.keys():
            for quote_asset in self.exchange_websocket_dict[exchange].get_price_df()['quote_asset'].unique():
                market_code_list.append(f"{exchange}/{quote_asset}")
        return market_code_list
    
    def dollar_update_thread_status(self):
        dollar_update_alive_flag = self.update_dollar_thread.is_alive()
        if dollar_update_alive_flag is True:
            dollar_update_status_str = "dollar_update_thread is alive"
            integrity_flag = True
        else:
            dollar_update_status_str = "dollar_update_thread is dead"
            integrity_flag = False
        return integrity_flag, dollar_update_status_str
    
    def reinitiate_dollar_update_thread(self):
        before_reinitiate = "Before reinit:  " + self.dollar_update_thread_status()[1]
        self.update_dollar_thread = Thread(target=self.fetch_dollar_loop, args=(self.update_dollar_return_dict, self.update_dollar_logger), daemon=True)
        self.update_dollar_thread.start()
        time.sleep(1)
        after_reinitiate = "After reinit: " + self.dollar_update_thread_status()[1]
        self.logger.info(f"reinitiate_dollar_update_thread|{before_reinitiate} -> {after_reinitiate}")
        self.logger.info("reinitiate_dollar_update_thread|dollar_update_thread has been reinitiated.")
        return before_reinitiate + "\n" + after_reinitiate

    def get_symbol_list(self, target_market): # E.g) UPBIT_SPOT, BINANCE_SPOT, BINANCE_USD_M, BINANCE_COIN_M
        target_exchange = target_market.split('_')[0]
        target_market_type = '_'.join(target_market.split('_')[1:])

        comparing_exchanges = self.enabled_markets_dict.keys()
        comparison_list = []
        total_df = pd.DataFrame()
        for exchange in comparing_exchanges:
            for market_type in self.enabled_markets_dict[exchange]:
                if market_type == "SPOT":
                    for quote_asset in self.enabled_markets_dict[exchange][market_type]:
                        comparison_list.append({"exchange": exchange, "market_type": market_type, "contract_type":None, "quote_asset": quote_asset})
                else:
                    for contract_type in self.enabled_markets_dict[exchange][market_type]:
                        for quote_asset in self.enabled_markets_dict[exchange][market_type][contract_type]:
                            comparison_list.append({"exchange": exchange, "market_type": market_type, "contract_type":contract_type, "quote_asset": quote_asset})

        for i, comparison_dict in enumerate(comparison_list):
            if comparison_dict['exchange'] == target_exchange and comparison_dict['market_type'] == target_market_type:
                target_market_dict = comparison_list.pop(i)
                break

        # Start compare and concat
        target_market_ticker_df = self.info_dict[f"{target_market_dict['exchange'].lower()}_{target_market_dict['market_type'].lower()}_ticker_df"]
        # check if it's spot or not
        if target_market_dict['market_type'] != "SPOT":
            target_market_info_df = self.info_dict[f"{target_market_dict['exchange'].lower()}_{target_market_dict['market_type'].lower()}_info_df"][['symbol','perpetual']]
            target_market_ticker_df = target_market_ticker_df.merge(target_market_info_df, on='symbol', how='inner')
            if target_market_dict['contract_type'] == "PERPETUAL":
                target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['perpetual'] == True]
            else: # FUTURES
                target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['perpetual'] == False]
        target_market_ticker_df = target_market_ticker_df[target_market_ticker_df['quote_asset']==target_market_dict['quote_asset']][['symbol','lastPrice','atp24h','base_asset','quote_asset']]
        for each_comparison_dict in comparison_list:
            each_market_info_df = self.info_dict[f"{each_comparison_dict['exchange'].lower()}_{each_comparison_dict['market_type'].lower()}_info_df"]
            if each_comparison_dict['contract_type'] is None:
                each_market_info_df = each_market_info_df[each_market_info_df['quote_asset']==each_comparison_dict['quote_asset']]
            else: # contract_type is PERPETUAL or FUTURES
                if each_comparison_dict['contract_type'] == "PERPETUAL":
                    each_market_info_df = each_market_info_df[(each_market_info_df['quote_asset']==each_comparison_dict['quote_asset'])&(each_market_info_df['perpetual'] == True)]
                else: # FUTURES
                    each_market_info_df = each_market_info_df[(each_market_info_df['quote_asset']==each_comparison_dict['quote_asset'])&(each_market_info_df['perpetual'] == False)]
            comparison_market_code = f"{each_comparison_dict['exchange'].lower()}_{each_comparison_dict['market_type'].lower()}"
            new_symbol = f"symbol_{comparison_market_code}"
            new_quote_asset = f"quote_asset_{comparison_market_code}"
            each_market_info_df = each_market_info_df.rename(columns={"symbol":new_symbol, "quote_asset": new_quote_asset})
            merged_df = target_market_ticker_df.merge(each_market_info_df[[new_symbol, "base_asset", new_quote_asset]], on='base_asset', how='inner')
            total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(['symbol'], inplace=True)
        total_df.sort_values('atp24h', ascending=False)
        total_df.reset_index(drop=True, inplace=True)
        return total_df['symbol'].to_list()

    def get_upbit_symbol_list(self):
        symbol_list = self.get_symbol_list('UPBIT_SPOT')
        return [x for x in symbol_list if x not in (['KRW-'+y for y in self.upbit_symbols_to_exclude]+['BTC-'+y for y in self.upbit_symbols_to_exclude])]
    
    def get_bithumb_symbol_list(self):
        symbol_list = self.get_symbol_list('BITHUMB_SPOT')
        return symbol_list
    
    def get_binance_spot_symbol_list(self):
        symbol_list = self.get_symbol_list('BINANCE_SPOT')
        return symbol_list

    def get_binance_usd_m_symbol_list(self):
        symbol_list = self.get_symbol_list('BINANCE_USD_M')
        return [x for x in symbol_list if x not in [y+'USDT' for y in self.binance_usd_m_symbols_to_exclude]]

    def get_binance_coin_m_symbol_list(self):
        symbol_list = self.get_symbol_list('BINANCE_COIN_M')
        return symbol_list

    def get_okx_spot_symbol_list(self):
        symbol_list = self.get_symbol_list('OKX_SPOT')
        return symbol_list
    
    def get_okx_usd_m_symbol_list(self):
        symbol_list = self.get_symbol_list('OKX_USD_M')
        return symbol_list
    
    def get_okx_coin_m_symbol_list(self):
        symbol_list = self.get_symbol_list('OKX_COIN_M')
        return symbol_list
    
    def get_bybit_spot_symbol_list(self):
        symbol_list = self.get_symbol_list('BYBIT_SPOT')
        return symbol_list
    
    def get_bybit_usd_m_symbol_list(self):
        symbol_list = self.get_symbol_list('BYBIT_USD_M')
        return symbol_list
    
    def get_bybit_coin_m_symbol_list(self):
        symbol_list = self.get_symbol_list('BYBIT_COIN_M')
        return symbol_list
    
    def check_status(self, print_result=False, include_text=False):
        exchange_proc_status_tup_list = [x.check_status(include_text=True) for x in self.exchange_websocket_dict.values()]
        proc_status = all([x[0] for x in exchange_proc_status_tup_list])
        print_text = ""
        for each_result in [x[1] for x in exchange_proc_status_tup_list]:
            print_text += f"{each_result}\n"
        if print_result:
            print(print_text)
        if include_text:
            return proc_status, print_text
        return proc_status
    
    def convert_asset_rate(self, origin_market, origin_quote_asset, target_market, target_quote_asset):
        if origin_quote_asset == "USD":
            origin_quote_asset = "USDT"
        if target_quote_asset == "USD":
            target_quote_asset = "USDT"
        if origin_quote_asset == target_quote_asset:
            return 1
        origin_market_spot_info_df = self.info_dict[f"{origin_market.lower().split('_')[0]}_spot_ticker_df"]
        # First try to find the rate from the info_dict

        def convert_between_coins(origin_market_spot_info_df, origin_quote_asset, target_quote_asset):
            df = origin_market_spot_info_df[(origin_market_spot_info_df['base_asset']==origin_quote_asset)&(origin_market_spot_info_df['quote_asset']==target_quote_asset)]
            reverse_df = origin_market_spot_info_df[(origin_market_spot_info_df['quote_asset']==origin_quote_asset)&(origin_market_spot_info_df['base_asset']==target_quote_asset)]
            if len(df) == 1:
                convert_rate = df['lastPrice'].values[0]
            elif len(reverse_df) == 1:
                convert_rate = 1 / reverse_df['lastPrice'].values[0]
            else:
                convert_rate = None
            return convert_rate
        convert_rate = convert_between_coins(origin_market_spot_info_df, origin_quote_asset, target_quote_asset)
        if convert_rate is None: # not between coins
            # print("1st convert_rate is None, Not between coins")
            if target_quote_asset == "KRW" and origin_quote_asset == "USDT":
                convert_rate = self.get_dollar_dict()['price']
            elif target_quote_asset == "USDT" and origin_quote_asset == "KRW":
                convert_rate = 1 / self.get_dollar_dict()['price']
            elif target_quote_asset == "KRW":
                convert_rate = convert_between_coins(origin_market_spot_info_df, origin_quote_asset, "USDT") * self.get_dollar_dict()['price']
            elif origin_quote_asset == "KRW":
                temp_convert_rate = self.convert_asset_rate(target_market, target_quote_asset, origin_market, origin_quote_asset)
                if temp_convert_rate is not None:
                    convert_rate = 1 / temp_convert_rate
                else:
                    title = f"target_market: {target_market}, target_quote_asset: {target_quote_asset}, origin_market:{origin_market}, origin_quote_asset: {origin_quote_asset}"
                    raise Exception(f"Cannot find the convert rate for {title}")
            else:
                temp_convert_rate = self.convert_asset_rate(target_market, target_quote_asset, origin_market, origin_quote_asset)
                if temp_convert_rate is not None:
                    convert_rate = 1 / temp_convert_rate
                    return convert_rate
                else:
                    pass
                title = f"target_market: {target_market}, target_quote_asset: {target_quote_asset}, origin_market:{origin_market}, origin_quote_asset: {origin_quote_asset}"
                raise Exception(f"Cannot find the convert rate for {title}")
        return convert_rate

    def get_premium_df(self, target_market_code, origin_market_code):
        try:
            # POSSIBLE quote_assets: USDT, BUSD, BTC, KRW
            origin_market = origin_market_code.split('/')[0]
            quote_asset_one = origin_market_code.split('/')[1]
            target_market = target_market_code.split('/')[0]
            quote_asset_two = target_market_code.split('/')[1]

            origin_market_df = self.exchange_websocket_dict[origin_market].get_price_df()
            origin_market_df = origin_market_df[origin_market_df['quote_asset'] == quote_asset_one]
            target_market_df = self.exchange_websocket_dict[target_market].get_price_df()
            target_market_df = target_market_df[target_market_df['quote_asset'] == quote_asset_two]

            shared_bass_asset_list = list(set(origin_market_df['base_asset'].values).intersection(set(target_market_df['base_asset'].values)))
            origin_market_df = origin_market_df[origin_market_df['base_asset'].isin(shared_bass_asset_list)].sort_values('base_asset').reset_index(drop=True)
            target_market_df = target_market_df[target_market_df['base_asset'].isin(shared_bass_asset_list)].sort_values('base_asset').reset_index(drop=True)

            convert_rate = self.convert_asset_rate(origin_market, quote_asset_one, target_market, quote_asset_two)
            origin_market_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['tp','ap','bp']] * convert_rate
            # target_market_df[['converted_tp','converted_ap','converted_bp']] = target_market_df[['tp','ap','bp']]

            # divide by target_market_df[['tp','ap','bp']]
            premium_df = pd.DataFrame((target_market_df[['tp','ap','bp']].values - origin_market_df[['converted_tp','converted_bp','converted_ap']].values)/
                                    origin_market_df[['converted_tp','converted_bp','converted_ap']].values, columns=['tp_premium','LS_premium','SL_premium'])
            premium_df['LS_SL_spread'] = premium_df['LS_premium'] - premium_df['SL_premium']
            premium_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']] = target_market_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']]
            premium_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['converted_tp','converted_ap', 'converted_bp']]
            premium_df.loc[:, ['tp_premium','LS_premium','SL_premium','LS_SL_spread']] = premium_df[['tp_premium','LS_premium','SL_premium','LS_SL_spread']] * 100
            premium_df = premium_df.sort_values('atp24h', ascending=False).reset_index(drop=True)
            # TEST
            premium_df['dollar'] = self.get_dollar_dict()['price']
            # TEST
        except Exception as e:
            self.logger.error(f"get_premium_df|Exception occured! Error: {e}, traceback: {traceback.format_exc()}, origin_market_df: {origin_market_df}")
            # raise original exception
            raise e
        return premium_df

        
    def fetch_dollar(self, update_dollar_logger, url='https://finance.naver.com/marketindex/exchangeDegreeCountQuote.naver?marketindexCd=FX_USDKRW', timedelta_hours=9):
        # global DOLLAR_INFO_DICT
        # return_dict = {
        #     'price': None,
        #     'change': None,
        #     'last_updated_time': None
        # }
        try:
            exchange_rate = pd.read_html(url)[0]
            self.update_dollar_return_dict['price'] = exchange_rate.iloc[0,1]
            # return_dict['change'] = exchange_rate.iloc[0,-1]
            self.update_dollar_return_dict['change'] = exchange_rate.iloc[0,2]
            self.update_dollar_return_dict['last_updated_time'] = datetime.datetime.utcnow()
            dict_for_redis = {
                "price": self.update_dollar_return_dict['price'],
                "change": self.update_dollar_return_dict['change'],
                "last_updated_time": self.update_dollar_return_dict['last_updated_time'].strftime("%Y-%m-%d %H:%M:%S")
            }
            self.redis_client.set_dict('INFO_CORE|dollar', dict_for_redis)
            update_dollar_logger.info(f"fetch_dollar|Dollar price ({self.update_dollar_return_dict['price']} KRW) has been updated.")
        except Exception as e:
            # print(f'Except executed in get_dollar function, {e}')
            update_dollar_logger.warning(f"fetch_dollar|Exception occured! Error: {e}, pd.read_html(url): {pd.read_html(url)}")
            exchange_rate = pd.read_html(url)[1]
            self.update_dollar_return_dict['price'] = exchange_rate.iloc[0,1]
            # return_dict['change'] = exchange_rate.iloc[0,-1]
            self.update_dollar_return_dict['change'] = exchange_rate.iloc[0,2]
            self.update_dollar_return_dict['last_updated_time'] = datetime.datetime.utcnow()
        return self.update_dollar_return_dict

    def fetch_dollar_loop(self, update_dollar_logger, loop_time=30):
        while True:
            self.fetch_dollar(update_dollar_logger)
            time.sleep(loop_time)

    # TESTTEST
    def add_symbol_to_exclude(self, market, base_asset):
        if market == "UPBIT_SPOT":
            self.upbit_symbols_to_exclude.append(base_asset)
        elif market == "BINANCE_USD_M":
            self.binance_usd_m_symbols_to_exclude.append(base_asset)
        else:
            raise Exception(f"market: {market} is not supported.")
    # TESTTEST
    def remove_symbol_to_exclude(self, market, base_asset):
        if market == "UPBIT_SPOT":
            self.upbit_symbols_to_exclude.remove(base_asset)
        elif market == "BINANCE_USD_M":
            self.binance_usd_m_symbols_to_exclude.remove(base_asset)
        else:
            raise Exception(f"market: {market} is not supported.")
        
    def update_fundingrate(self, exchange_name, exchange_adaptor, loop_time_secs=60):
        self.logger.info(f"update_fundingrate|{exchange_name} update_fundingrate thread has started.")
        while True:
            try:
                for futures_type in ["USD_M", "COIN_M"]:
                    mongo_db_conn = self.db_client.get_conn()
                    # First fetch from the mongodb
                    # fetch from mongodb
                    mongo_db = mongo_db_conn[f"{exchange_name}_fundingrate"]
                    collection = mongo_db[futures_type]
                    # get all the data
                    data = collection.find({})
                    # convert to dataframe
                    df = pd.DataFrame(data)
                    funding_df = exchange_adaptor.get_fundingrate(futures_type)[['symbol','funding_rate','funding_time','base_asset','quote_asset','perpetual']]
                    funding_df['datetime_now'] = datetime.datetime.utcnow()
                    if len(df) == 0:
                        # Store
                        funding_dict = funding_df.to_dict('records')
                        collection.insert_many(funding_dict)
                        self.logger.info(f"Collection empty. Inserting {futures_type} fundingrate to mongodb")
                    else:
                        merged_funding_df = funding_df.merge(df, on=['symbol','funding_time'], how='left')
                        for row_tup in merged_funding_df.iterrows():
                            row = row_tup[1]
                            if not pd.isna(row['_id']):
                                # UPDATE with new funding_rate
                                collection.update_one({'_id':row['_id']}, {'$set':{'funding_rate':row['funding_rate_x'], 'datetime_now':row['datetime_now_x']}})
                                # self.logger.info(f"{each_market_code}_fundingrate updated... symbol: {row['symbol']}, old fundingrate: {row['funding_rate_y']}({row['datetime_now_y']}), new fundingrate: {row['funding_rate_x']}({row['datetime_now_x']})")
                            else:
                                # INSERT new funding_rate
                                row_dict = row.to_dict()
                                collection.insert_one({'symbol': row_dict['symbol'], 'funding_rate': row_dict['funding_rate_x'], 'funding_time': row_dict['funding_time'],
                                                        'base_asset': row_dict['base_asset_x'], 'quote_asset': row_dict['quote_asset_x'], 'perpetual': row_dict['perpetual_x'],
                                                        'datetime_now': row_dict['datetime_now_x']})
                                # self.logger.info(f"{each_market_code}_fundingrate, New funding data inserted.. symbol: {row_dict['symbol']}")
                mongo_db_conn.close()
            except Exception as e:
                content = f"update_fundingrate|Exception occured! Error: {e}, {traceback.format_exc()}"
                self.logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', "Error occured in update_fundingrate.", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
            time.sleep(loop_time_secs)

    def update_wallet_status(self, exchange_name, exchange_adaptor, loop_time_secs=60):
        exchange_name = exchange_name.upper()
        self.logger.info(f"update_wallet_status|{exchange_name} update_wallet_status thread has started.")
        error_count = 0
        while True:
            try:
                mongo_db_conn = self.db_client.get_conn()
                # First fetch from the mongodb
                # fetch from mongodb
                mongo_db = mongo_db_conn["wallet_status"]
                collection = mongo_db[f"{exchange_name}"]
                # get all the data
                data = collection.find({})
                # convert to dataframe
                df = pd.DataFrame(data)
                wallet_status_df = exchange_adaptor.wallet_status()
                wallet_status_df['datetime_now'] = datetime.datetime.utcnow()
                if len(df) == 0:
                    # Store
                    wallet_status_dict = wallet_status_df.to_dict('records')
                    collection.insert_many(wallet_status_dict)
                    self.logger.info(f"Collection empty. Inserting {exchange_name}'s wallet_status to mongodb")
                else:
                    for row_tup in wallet_status_df.iterrows():
                        row = row_tup[1]
                        # if the asset with the network_type already exist in the db, update it otherwise insert it.
                        if len(df[(df['asset']==row['asset'])&(df['network_type']==row['network_type'])]) == 1:
                            collection.update_one({'asset':row['asset'], 'network_type':row['network_type']}, {'$set':{k: row[k] for k in row.keys() if k not in ['asset','network_type']}})
                        else:
                            collection.insert_one(row.to_dict())
                mongo_db_conn.close()
                error_count = 0
            except Exception as e:
                error_count += 1
                if error_count >= 10:
                    content = f"update_wallet_status|Exception occured in {exchange_name}'s update_wallet_status! Error: {e}, {traceback.format_exc()}"
                    self.logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"Error occured in {exchange_name} update_wallet_status.", content=content, code=None, sent_switch=0, send_counts=1, remark=None)
            time.sleep(loop_time_secs)
