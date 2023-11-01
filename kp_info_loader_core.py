import pandas as pd
# from price_websocket import dict_convert, update_dollar, price_websocket
from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_websocket.binance_websocket import BinanceWebsocket, BinanceUSDMWebsocket, BinanceCOINMWebsocket
from exchange_websocket.upbit_websocket import UpbitWebsocket
from exchange_websocket.okx_websocket import OkxWebsocket, OkxUSDMWebsocket, OkxCOINMWebsocket
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

        self.okx_adaptor = InitOkxAdaptor(logging_dir=self.logging_dir)
        self.upbit_adaptor = InitUpbitAdaptor(self.exchange_api_key_dict['upbit_read_only']['api_key'], self.exchange_api_key_dict['upbit_read_only']['secret_key'], self.info_dict, self.logging_dir)
        self.binance_adaptor = InitBinanceAdaptor(self.exchange_api_key_dict['binance_read_only']['api_key'], self.exchange_api_key_dict['binance_read_only']['secret_key'], self.info_dict, self.logging_dir)

        # UPBIT SPOT (KRW, BTC Market)
        # UPBIT wallet status
        # BINANCE SPOT, USD-M Futures, COIN-M Futures
        self.data_name_list = [
            "upbit_spot_ticker_df",
            "upbit_wallet_status_df",
            "binance_spot_ticker_df",
            "binance_spot_info_df",
            "binance_usd_m_ticker_df",
            "binance_usd_m_info_df",
            "binance_coin_m_ticker_df",
            "binance_coin_m_info_df",
            "okx_spot_ticker_df",
            "okx_usd_m_ticker_df",
            "okx_coin_m_ticker_df"
        ]

        for data_name in self.data_name_list:
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
        self.exchange_websocket_dict['BINANCE_SPOT'] = BinanceWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_spot_symbol_list, register_monitor_msg, self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_USD_M'] = BinanceUSDMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_usd_m_symbol_list, register_monitor_msg, self.info_dict, logging_dir)
        self.exchange_websocket_dict['BINANCE_COIN_M'] = BinanceCOINMWebsocket(self.admin_id, self.node, self.proc_n, self.get_binance_coin_m_symbol_list, register_monitor_msg, self.info_dict, logging_dir)
        # self.exchange_websocket_dict['OKX_SPOT'] = 
        self.logger.info(f"InitCore|exchange_websocket_dict, {self.exchange_websocket_dict.keys()} has been initiated.")
        time.sleep(10)

        # Start updating fundingrate
        # self.update_fundingrate_proc = Process(target=self.update_fundingrate, daemon=True) # Deprecated
        # self.update_fundingrate_proc.start()
        self.update_fundingrate_thread = Thread(target=self.update_fundingrate, daemon=True)
        self.update_fundingrate_thread.start()

        # Start kline generator
        self.kline_generator = InitKlineCore(self.admin_id, node, self.get_premium_df, self.get_market_code_list, register_monitor_msg, self.redis_client, self.db_client, logging_dir)

    def update_exchange_info_as_df(self, data_name, loop_time_secs=15):
        while True:
            try:
                if data_name == "upbit_spot_ticker_df":
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
                elif data_name == "okx_usd_m_ticker_df":
                    self.info_dict[data_name] = self.okx_adaptor.usd_m_all_tickers()
                elif data_name == "okx_coin_m_ticker_df":
                    self.info_dict[data_name] = self.okx_adaptor.coin_m_all_tickers()
                else:
                    self.logger.error(f"update_exchange_info_as_df|name:{data_name} is not valid.")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} is not valid.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                    break
                time.sleep(loop_time_secs)
            except Exception as e:
                self.logger.error(f"update_exchange_info_as_df|name:{data_name}, {traceback.format_exc()}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"update_exchange_info_as_df|name:{data_name} failed.", content=None, code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(loop_time_secs)

    def get_dollar_dict(self):
        dollar_dict = self.redis_client.get_dict('INFO_CORE|dollar')
        return dollar_dict

    def get_market_code_list(self):
        market_code_list = []
        for exchange in self.exchange_websocket_dict.keys():
            for quete_asset in self.exchange_websocket_dict[exchange].get_price_df()['quote_asset'].unique():
                market_code_list.append(f"{exchange}/{quete_asset}")
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

    def get_upbit_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][['market','acc_trade_price_24h_krw']].copy()
        upbit_ticker_df['base_symbol'] = upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
        for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
            each_upbit_ticker_df = upbit_ticker_df[upbit_ticker_df['market'].str.startswith(upbit_market)].copy()
            
            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_info_df = self.info_dict['binance_spot_info_df'][self.info_dict['binance_spot_info_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_info_df['base_symbol'] = each_binance_spot_info_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                merged_df = each_upbit_ticker_df.merge(each_binance_spot_info_df[['symbol','base_symbol']], on='base_symbol', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usd_m_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']: # ["USDT_PERPETUAL", "BUSD_PERPETUAL"]
                # Check PERPETUAL
                quote_asset, contract_type = binance_usd_m_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_upbit_ticker_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coin_m_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']: # ["PERPETUAL"]
                # Check PERPETUAL
                contract_type = binance_coin_m_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_upbit_ticker_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            # for okx_spot_quote_asset in self.enabled_market_dict['OKX']['SPOT']:
            #     each_okx_spot_ticker_df = self.info_dict['okx_spot_ticker_df'][self.info_dict['okx_spot_ticker_df']['quote_asset']==okx_spot_market].copy()


        total_df.drop_duplicates(subset=['market'], inplace=True)
        total_df.sort_values(by='acc_trade_price_24h_krw', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        market_symbol_list = total_df['market'].to_list()
        # return market_symbol_list
        # TEST
        return [x for x in market_symbol_list if x not in (['KRW-'+y for y in self.upbit_symbols_to_exclude]+['BTC-'+y for y in self.upbit_symbols_to_exclude])]
    
    def get_binance_spot_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][['symbol','volume_usdt']].copy()
        binance_spot_ticker_df = binance_spot_ticker_df.rename(columns={'symbol':'spot_symbol'})

        for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
            each_binance_spot_ticker_df = binance_spot_ticker_df[binance_spot_ticker_df['spot_symbol'].str.endswith(binance_spot_market)].copy()
            each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['spot_symbol'].apply(lambda x: x[:-len(binance_spot_market)])
            
            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                merged_df = each_binance_spot_ticker_df.merge(each_upbit_ticker_df[['market','base_symbol']], on='base_symbol', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usd_m_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
                quote_asset, contract_type = binance_usd_m_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_binance_spot_ticker_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coin_m_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
                contract_type = binance_coin_m_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_binance_spot_ticker_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='base_symbol', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['spot_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['spot_symbol'].to_list()

    def get_binance_usd_m_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_usd_m_ticker_df = self.info_dict['binance_usd_m_ticker_df'][['symbol','volume_usdt']].copy()
        binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][['symbol','quoteAsset','baseAsset','contractType']].copy()
        binance_usd_m_merged_df = binance_usd_m_ticker_df.merge(binance_usd_m_info_df, on='symbol', how='inner')
        binance_usd_m_merged_df = binance_usd_m_merged_df.rename(columns={'symbol':'usd_m_symbol'})

        for binance_usd_m_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
            quote_asset, contract_type = binance_usd_m_market.split('_')
            each_binance_usd_m_merged_df = binance_usd_m_merged_df[(binance_usd_m_merged_df['quoteAsset']==quote_asset)&(binance_usd_m_merged_df['contractType']==contract_type)].copy()

            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                merged_df = each_binance_usd_m_merged_df.merge(each_upbit_ticker_df[['market','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][self.info_dict['binance_spot_ticker_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                merged_df = each_binance_usd_m_merged_df.merge(each_binance_spot_ticker_df[['symbol','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_coin_m_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
                contract_type = binance_coin_m_market
                each_binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][self.info_dict['binance_coin_m_info_df']['contractType']==contract_type].copy()
                merged_df = each_binance_usd_m_merged_df.merge(each_binance_coin_m_info_df[['symbol','baseAsset']], left_on='baseAsset', right_on='baseAsset' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['usd_m_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        symbol_list = total_df['usd_m_symbol'].to_list()
        # return total_df['usd_m_symbol'].to_list()
        # TEST
        return [x for x in symbol_list if x not in [y+'USDT' for y in self.binance_usd_m_symbols_to_exclude]]

    def get_binance_coin_m_symbol_list(self, return_df=False):
        total_df = pd.DataFrame()
        binance_coin_m_ticker_df = self.info_dict['binance_coin_m_ticker_df'][['symbol','volume_usdt']].copy()
        binance_coin_m_info_df = self.info_dict['binance_coin_m_info_df'][['symbol','baseAsset','contractType']].copy()
        binance_coin_m_merged_df = binance_coin_m_ticker_df.merge(binance_coin_m_info_df, on='symbol', how='inner')
        binance_coin_m_merged_df = binance_coin_m_merged_df.rename(columns={'symbol':'coin_m_symbol'})

        for binance_coin_m_market in self.enabled_markets_dict['BINANCE']['COIN_M_FUTURES']:
            contract_type = binance_coin_m_market
            each_binance_coin_m_merged_df = binance_coin_m_merged_df[binance_coin_m_merged_df['contractType']==contract_type].copy()

            for upbit_market in self.enabled_markets_dict['UPBIT']['SPOT']:
                each_upbit_ticker_df = self.info_dict['upbit_spot_ticker_df'][self.info_dict['upbit_spot_ticker_df']['market'].str.startswith(upbit_market)].copy()
                each_upbit_ticker_df['base_symbol'] = each_upbit_ticker_df['market'].apply(lambda x: x.split('-')[1])
                merged_df = each_binance_coin_m_merged_df.merge(each_upbit_ticker_df[['market','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_spot_market in self.enabled_markets_dict['BINANCE']['SPOT']:
                each_binance_spot_ticker_df = self.info_dict['binance_spot_ticker_df'][self.info_dict['binance_spot_ticker_df']['symbol'].str.endswith(binance_spot_market)].copy()
                each_binance_spot_ticker_df['base_symbol'] = each_binance_spot_ticker_df['symbol'].apply(lambda x: x[:-len(binance_spot_market)])
                merged_df = each_binance_coin_m_merged_df.merge(each_binance_spot_ticker_df[['symbol','base_symbol']], left_on='baseAsset', right_on='base_symbol' ,how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

            for binance_usd_m_market in self.enabled_markets_dict['BINANCE']['USD_M_FUTURES']:
                quote_asset, contract_type = binance_usd_m_market.split('_')
                each_binance_usd_m_info_df = self.info_dict['binance_usd_m_info_df'][(self.info_dict['binance_usd_m_info_df']['quoteAsset']==quote_asset)&(self.info_dict['binance_usd_m_info_df']['contractType']==contract_type)].copy()        
                merged_df = each_binance_coin_m_merged_df.merge(each_binance_usd_m_info_df[['symbol','baseAsset']], left_on='baseAsset', right_on='baseAsset', how='inner')
                total_df = pd.concat([total_df, merged_df], axis=0, ignore_index=True)

        total_df.drop_duplicates(subset=['coin_m_symbol'], inplace=True)
        total_df.sort_values(by='volume_usdt', ascending=False, inplace=True)
        total_df.reset_index(drop=True, inplace=True)
        if return_df:
            return total_df
        return total_df['coin_m_symbol'].to_list()
    
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
        
    def update_fundingrate(self, loop_time_secs=60):
        while True:
            try:
                mongo_db_conn = self.db_client.get_conn()
                for each_market_code in [x for x in self.exchange_websocket_dict.keys() if 'SPOT' not in x]:
                    exchange = each_market_code.split('_')[0]
                    futures_type = each_market_code.split('_')[1]+'_'+each_market_code.split('_')[2]
                    # First fetch from the mongodb
                    # fetch from mongodb
                    mongo_db = mongo_db_conn[f"{exchange}_fundingrate"]
                    collection = mongo_db[futures_type]
                    # get all the data
                    data = collection.find({})
                    # convert to dataframe
                    df = pd.DataFrame(data)
                    if exchange == "BINANCE":
                        funding_df = self.binance_adaptor.get_fundingrate(futures_type)
                    else:
                        raise Exception(f"exchange: {exchange} is not supported.")
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

