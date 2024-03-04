import sys
import os
import datetime
import traceback
import pandas as pd
import numpy as np
import time
from binance.client import Client
from binance import AsyncClient, BinanceSocketManager # For MarginCallback
import asyncio # For MarginCallback
from psycopg2 import extras
from threading import Thread

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from etc.acw_api import AcwApi
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from api.utils import decrypt_data, MyException

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, info_dict=None, recvWindow=45000, logging_dir=None):
        self.my_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.info_dict = info_dict
        self.recvWindow = recvWindow
        self.binance_plug_logger = KimpBotLogger("binance_plug", logging_dir).logger
        self.binance_plug_logger.info(f"binance_plug_logger started.")

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_client.get_deposit_history(asset=asset))
        deposit.loc[:,'insertTime'] = deposit['insertTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        deposit.loc[:, 'amount'] = deposit['amount'].astype(float)
        return deposit
    
    def spot_all_tickers(self):
        df = pd.DataFrame(self.pub_client.get_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        if self.info_dict is None or self.info_dict.get('binance_spot_info_df') is None:
            # TEST
            spot_exchange_info_df = self.spot_exchange_info()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_info_df') is None, Fetched from API")
        else:
            spot_exchange_info_df = self.info_dict.get('binance_spot_info_df')
        df = df.merge(spot_exchange_info_df[['symbol', 'base_asset', 'quote_asset']], on='symbol', how='inner')
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['atp24h'] = df['quoteVolume'] * df['lastPrice2']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)
        # if quote_asset is 'USDT', atp24h is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'atp24h'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        return df
    
    def spot_exchange_info(self):
        df = pd.DataFrame(self.pub_client.get_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        return df
    
    def usd_m_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def usd_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        if self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None:
            # TEST
            usd_m_exchange_info_df = self.usd_m_exchange_info()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None, Fetched from API")
        else:
            usd_m_exchange_info_df = self.info_dict.get('binance_usd_m_info_df')
        if self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None:
            # TEST
            binance_spot_ticker_df = self.spot_all_tickers()
            self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_spot_ticker_df') is None, Fetched from API")
        else:
            binance_spot_ticker_df = self.info_dict.get('binance_spot_ticker_df')
        df = df.merge(usd_m_exchange_info_df[['symbol', 'base_asset', 'quote_asset']], on='symbol', how='inner')
        df['quote_symbol'] = df['quote_asset'] + 'USDT'
        df2 = binance_spot_ticker_df.copy()
        df2.rename(columns={"symbol": "symbol2", "lastPrice": "lastPrice2"}, inplace=True)
        df = df.merge(df2[['symbol2','lastPrice2']], left_on='quote_symbol', right_on='symbol2', how='left')
        df['atp24h'] = df['quoteVolume'] * df['lastPrice2']
        # if quote_asset is 'USDT', atp24h is quoteVolume
        df.loc[df['quote_asset'] == 'USDT', 'atp24h'] = df.loc[df['quote_asset'] == 'USDT', 'quoteVolume']
        df.drop(columns=['symbol2', 'lastPrice2'], inplace=True)

        return df
    
    def coin_m_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_coin_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df = df.rename(columns={"baseAsset":"base_asset", "quoteAsset":"quote_asset"})
        df['perpetual'] = df['contractType'].apply(lambda x: True if x=="PERPETUAL" else False)
        return df
    
    def coin_m_all_tickers(self):
        df = pd.DataFrame(self.pub_client.futures_coin_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        df['base_asset'] = df['symbol'].str.split('USD_').str[0]
        df['quote_asset'] = 'USD' # ?
        df['atp24h'] = df['volume'] * 100
        return df

    def get_fundingrate(self, futures_type="USD_M"):
        bi_client = self.pub_client
        if futures_type == "USD_M":
            if self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None:
                usd_m_exchange_info_df = self.usd_m_exchange_info()
                self.binance_plug_logger.info(f"self.info_dict is None or self.info_dict.get('binance_usd_m_info_df') is None, Fetched from API")
            else:
                usd_m_exchange_info_df = self.info_dict.get('binance_usd_m_info_df')
            binance_fund = pd.DataFrame(bi_client.futures_mark_price())
            binance_fund = binance_fund.merge(usd_m_exchange_info_df[['symbol','base_asset','quote_asset']], on='symbol', how='left')
            binance_fund = binance_fund.rename(columns={'lastFundingRate':'funding_rate', 'nextFundingTime':'funding_time'})
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # replace '' to None
            binance_fund.replace("", None, inplace=True)
            binance_fund.loc[:, 'funding_rate'] = binance_fund['funding_rate'].astype(float)
            binance_fund.drop(columns=['markPrice','indexPrice','estimatedSettlePrice','interestRate','time'], inplace=True)
            binance_fund['perpetual'] = binance_fund['symbol'].apply(lambda x: False if '_' in x else True)
            return binance_fund
        elif futures_type == "COIN_M":
            binance_fund = pd.DataFrame(bi_client.futures_coin_mark_price())
            binance_fund['base_asset'] = binance_fund['symbol'].str.split('USD_').str[0]
            binance_fund['quote_asset'] = 'USD'
            binance_fund = binance_fund.rename(columns={'lastFundingRate':'funding_rate', 'nextFundingTime':'funding_time'})
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000, tz=datetime.timezone.utc))
            binance_fund.loc[:,'funding_time'] = binance_fund.loc[:,'funding_time'].dt.tz_localize(None)
            # replace '' to None
            binance_fund.replace("", None, inplace=True)
            binance_fund.loc[:, 'funding_rate'] = binance_fund['funding_rate'].astype(float)
            binance_fund.drop(columns=['markPrice','indexPrice','estimatedSettlePrice','interestRate','pair','time'], inplace=True)
            binance_fund['perpetual'] = binance_fund['symbol'].apply(lambda x: True if '_PERP' in x else False)
            return binance_fund
        else:
            raise Exception(f"Invalid futures_type: {futures_type}")
        
    def wallet_status(self):
        binance_network_list = [x['networkList'] for x in self.my_client.get_all_coins_info()]
        binance_network_list = [item for sublist in binance_network_list for item in sublist]
        binance_wallet_status_df = pd.DataFrame(binance_network_list)
        binance_wallet_status_df = binance_wallet_status_df.rename(columns={"network": "network_type", "coin": "asset", "withdrawEnable": "withdraw", "depositEnable": "deposit"})
        return binance_wallet_status_df
        

################################################################################################################################################
class UserBinanceAdaptor:
    def __init__(self, admin_telegram_id, node=None, db_dict=None, trade_df_dict=None, market_combi_code=None, recvWindow=45000, logging_dir=None):
        self.admin_telegram_id = admin_telegram_id
        self.node = node
        self.user_client_dict = {}
        self.user_stream_monitoring_list = []
        self.recvWindow = recvWindow
        self.logger = KimpBotLogger("user_binance_plug", logging_dir).logger
        self.retry_term_sec = 0.2
        self.retry_count_limit = 2
        if db_dict is not None:
            self.postgres_client = InitPostgresDBClient(**{**db_dict, 'database': 'trade_core'})
            self.user_api_key_df = self.load_user_api_keys()
        else:
            self.postgres_client = None
            self.user_api_key_df = None
        self.trade_df_dict = trade_df_dict
        self.market_combi_code = market_combi_code
        if market_combi_code is not None:
            self.my_exchange = [x for x in market_combi_code.split('_') if 'BINANCE' in x][0]
            self.counterpart_exchange = [x for x in market_combi_code.split('_') if 'BINANCE' not in x][0]
        else:
            self.my_exchange = None
            self.counterpart_exchange = None
        self.acw_api = AcwApi()
        self.logger.info(f"user_binance_plug_logger|{market_combi_code} started.")
        
    def load_user_api_keys(self):
        conn = self.postgres_client.pool.getconn()
        curr = conn.cursor(cursor_factory=extras.RealDictCursor)
        sql = "SELECT * FROM exchange_api_key WHERE exchange='BINANCE'"
        curr.execute(sql)
        user_api_key_df = pd.DataFrame(curr.fetchall())
        self.postgres_client.pool.putconn(conn)
        user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].applymap(lambda x: x.tobytes() if isinstance(x, memoryview) else x)
        user_api_key_df.loc[:, ['access_key','secret_key']] = user_api_key_df[['access_key','secret_key']].applymap(lambda x: decrypt_data(x).decode('utf-8') if x is not None else None)
        self.user_api_key_df = user_api_key_df
        return user_api_key_df

    def loop_load_user_api_keys(self, loop_interval_secs=60):
        self.logger.info(f"loop_load_user_api_keys started.")
        while True:
            try:
                self.user_api_key_df = self.load_user_api_keys()
            except Exception as e:
                self.logger.error(f"loop_load_user_api_keys|{traceback.format_exc()}")
                self.acw_api.create_message_thread(self.admin_telegram_id, "loop_load_user_api_keys", self.node, "monitor", str(e))
            time.sleep(loop_interval_secs)

    def get_api_key_tup(self, trade_config_uuid, futures, raise_error=True):
        # Pick one randomly using .sample among the same trade_config_uuid and futures flag
        try:
            api_key_df = self.user_api_key_df[(self.user_api_key_df['trade_config_uuid']==trade_config_uuid) & (self.user_api_key_df['futures']==futures)].sample(1)
            return (api_key_df['access_key'].values[0], api_key_df['secret_key'].values[0])
        except ValueError:
            if raise_error:
                raise MyException(f"No API Key found for trade_config_uuid: {trade_config_uuid}, futures: {futures}", error_code=1)
            else:
                return (None, None)

    def load_user_client(self, access_key, secret_key):
        user_client = self.user_client_dict.get(access_key)
        if user_client is None:
            self.user_client_dict[access_key] = Client(access_key, secret_key)
            return self.user_client_dict[access_key]
        else:
            return user_client

    def check_api_key(self, access_key, secret_key, futures=False):
        self.user_client_dict.pop(access_key, None)
        try:
            if futures is False:
                self.get_spot_balance(access_key, secret_key)
            else:
                self.get_usdm_balance(access_key, secret_key)
            return (True, 'OK')
        except Exception as e:
            self.user_client_dict.pop(access_key, None)
            return (False, str(e))

    def get_spot_balance(self, access_key, secret_key):
        client = self.load_user_client(access_key, secret_key)
        spot_balance = pd.DataFrame(client.get_account()['balances'])
        spot_balance.loc[:,['free','locked']] = spot_balance[['free','locked']].astype(float)
        spot_balance_df = spot_balance[spot_balance['free']>0].reset_index(drop=True)
        return spot_balance_df

    def get_usdm_balance(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        usdm_balance_df = pd.DataFrame(client.futures_account()['assets'])
        usdm_balance_df.loc[:, ['walletBalance', 'unrealizedProfit', 'availableBalance']] = usdm_balance_df[['walletBalance', 'unrealizedProfit', 'availableBalance']].astype(float)
        if return_dict is None:
            return usdm_balance_df
        else:
            return_dict['res'] = usdm_balance_df

    def get_balance(self, access_key, secret_key, market_type='SPOT'):
        if market_type == "SPOT":
            return self.get_spot_balance(access_key, secret_key)
        elif market_type == "USD_M":
            return self.get_usdm_balance(access_key, secret_key)
        elif market_type == "COIN_M":
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")

    # Binancef order functions
    def change_margin_type(self, access_key, secret_key, symbol, marginType='ISOLATED'):
        client = self.load_user_client(access_key, secret_key)
        try:
            res = client.futures_change_margin_type(
                symbol=symbol,
                marginType=marginType
            )
        except Exception as e:
            error_code = e.code
            if error_code == -4046:
                res = {'code': 200, 'msg': e.message}
            else:
                self.logger.error(f"change_margin_type|{traceback.format_exc()}")
                raise Exception(e)
        return res

    def change_leverage(self, access_key, secret_key, symbol, leverage):
        client = self.load_user_client(access_key, secret_key)
        res = client.futures_change_leverage(symbol=symbol, leverage=leverage)
        return res

    def futures_order_info(self, access_key, secret_key, symbol, orderId, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        if return_dict is None:
            res = client.futures_get_order(symbol=symbol, orderId=orderId, recvWindow=self.recvWindow)
            return res
        else:
            try:
                return_dict['res'] = client.futures_get_order(symbol=symbol, orderId=orderId, recvWindow=self.recvWindow)
                return_dict['state'] = 'OK'
            except Exception as e:
                self.logger.error(f"futures_order_info|{traceback.format_exc()}")
                return_dict['res'] = e
                return_dict['state'] = 'ERROR'
    # Original
    # def market_enter(self, access_key, secret_key, symbol, qty, return_dict=None):
    #     client = self.load_user_client(access_key, secret_key)
    #     if return_dict is None:
    #         res = client.futures_create_order(
    #             symbol=symbol,
    #             side='SELL',
    #             type='MARKET',
    #             quantity=qty,
    #             recvWindow=self.recvWindow
    #             # workingType='MARK_PRICE'
    #         )
    #         return res
    #     else:
    #         try:
    #             return_dict['res'] =  client.futures_create_order(
    #                 symbol=symbol,
    #                 side='SELL',
    #                 type='MARKET',
    #                 quantity=qty,
    #                 recvWindow=self.recvWindow
    #                 # workingType='MARK_PRICE'
    #             )
    #             return_dict['state'] = 'OK'
    #         except Exception as e:
    #             self.logger.error(f"market_enter|{traceback.format_exc()}")
    #             return_dict['res'] = e
    #             return_dict['state'] = 'ERROR'

    def market_long(self, access_key, secret_key, symbol, qty, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            if retry_count >= 1:
                self.logger.info(f"market_enter|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
            try:
                if market_type == "USD_M":
                    res = client.futures_create_order(
                        symbol=symbol,
                        side='SELL',
                        type='MARKET',
                        quantity=qty,
                        recvWindow=self.recvWindow
                    )
                    if return_dict is not None:
                        return_dict['res'] = res
                        return_dict['error_code'] = None
                    return res
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = e.code
                        return
            retry_count += 1

    # # Original
    # def market_exit(self, access_key, secret_key, symbol, qty, return_dict=None):
    #     client = self.load_user_client(access_key, secret_key)
    #     if return_dict is None:
    #         res = client.futures_create_order(
    #             symbol=symbol,
    #             side='BUY',
    #             type='MARKET',
    #             quantity=qty,
    #             recvWindow=self.recvWindow
    #         )
    #         return res
    #     else:
    #         try:
    #             return_dict['res'] = client.futures_create_order(
    #             symbol=symbol,
    #             side='BUY',
    #             type='MARKET',
    #             quantity=qty,
    #             recvWindow=self.recvWindow
    #         )
    #             return_dict['state'] = 'OK'
    #         except Exception as e:
    #             self.logger.error(f"market_exit|{traceback.format_exc()}")
    #             return_dict['res'] = e
    #             return_dict['state'] = 'ERROR'

    def market_short(self, access_key, secret_key, symbol, qty, market_type, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            if retry_count >= 1:
                self.logger.info(f"market_short|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
            try:
                if market_type == "USD_M":
                    res = client.futures_create_order(
                    symbol=symbol,
                    side='BUY',
                    type='MARKET',
                    quantity=qty,
                    recvWindow=self.recvWindow
                    )
                    if return_dict is not None:
                        return_dict['res'] = res
                        return_dict['error_code'] = None
                    return res
                else:
                    raise Exception(f"market_type: {market_type} is not supported yet.")
            except Exception as e:
                if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['error_code'] = e.code
                        return
            retry_count += 1
    # Original
    # def position_information(self, access_key, secret_key, symbol, return_dict=None):
    #     client = self.load_user_client(access_key, secret_key)
    #     if return_dict is None:
    #         res = client.futures_position_information()
    #         position_df = pd.DataFrame(res)
    #         symbol_df = position_df[position_df['symbol']==symbol]
    #         if len(symbol_df) == 0:
    #             position_qty = 0
    #             liquidation_price = None
    #         else:
    #             position_qty = abs(float(symbol_df['positionAmt'].iloc[0]))
    #             liquidation_price = float(symbol_df['liquidationPrice'].iloc[0])
    #         return (position_qty, liquidation_price)
    #     else:
    #         try:
    #             res = client.futures_position_information()
    #             position_df = pd.DataFrame(res)
    #             symbol_df = position_df[position_df['symbol']==symbol]
    #             if len(symbol_df) == 0:
    #                 position_qty = 0
    #                 liquidation_price = None
    #             else:
    #                 position_qty = abs(float(symbol_df['positionAmt'].iloc[0]))
    #                 liquidation_price = float(symbol_df['liquidationPrice'].iloc[0])
    #             return_dict['res'] = (position_qty, liquidation_price)
    #             return_dict['state'] = 'OK'
    #         except Exception as e:
    #             self.logger.error(f"position_information|{traceback.format_exc()}")
    #             return_dict['res'] = e
    #             return_dict['state'] = 'ERROR'

    def position_information(self, access_key, secret_key, symbol, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            try:
                res = client.futures_position_information()
                position_df = pd.DataFrame(res)
                symbol_df = position_df[position_df['symbol']==symbol]
                if len(symbol_df) == 0:
                    position_qty = 0
                    liquidation_price = None
                else:
                    position_qty = abs(float(symbol_df['positionAmt'].iloc[0]))
                    liquidation_price = float(symbol_df['liquidationPrice'].iloc[0])
                if return_dict is not None:
                    return_dict['res'] = (position_qty, liquidation_price)
                    return_dict['state'] = 'OK'
                return (position_qty, liquidation_price)
            except Exception as e:
                if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['state'] = 'ERROR'
                        return
            retry_count += 1

    def all_position_information(self, access_key, secret_key, market_type='USD_M', return_dict=None):
        if market_type not in ["USD_M", 'COIN_M']:
            raise Exception(f"Invalid market_type: {market_type}")
        client = self.load_user_client(access_key, secret_key)
        if market_type == "USD_M":
            res = client.futures_position_information()
            position_df = pd.DataFrame(res)
            position_df.loc[:, 'positionAmt':'maxNotionalValue'] = position_df.loc[:,'positionAmt':'maxNotionalValue'].astype(float)
            position_df = position_df[position_df['positionAmt']!=0].reset_index(drop=True)
        elif market_type == "COIN_M":
            # raise error for not supported yet
            raise Exception(f"market_type: {market_type} is not supported yet.")
        else:
            raise Exception(f"Invalid market_type: {market_type}")
        if return_dict is None:
            return position_df
        else:
            try:
                return_dict['res'] = position_df
                return_dict['state'] = 'OK'
            except Exception as e:
                self.logger.error(f"all_position_information|{traceback.format_exc()}")
                return_dict['res'] = e
                return_dict['state'] = 'ERROR'

    def get_futures_account(self, access_key, secret_key, return_dict=None):
        client = self.load_user_client(access_key, secret_key)
        if return_dict is None:
            res = client.futures_account()
            res_df = pd.DataFrame(res['assets'])
            res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
            return res_df
        else:
            try:
                res = client.futures_account()
                res_df = pd.DataFrame(res['assets'])
                res_df.loc[:, 'walletBalance':'updateTime'] = res_df.loc[:, 'walletBalance':'updateTime'].astype(float)
                return_dict['res'] = res_df
                return_dict['state'] = 'OK'
            except Exception as e:
                self.logger.error(f"get_futures_account|{traceback.format_exc()}")
                return_dict['res'] = e
                return_dict['state'] = 'ERROR'

    # Functions for monitoring binance margin call
    def usd_m_margin_call_callback(self, res, trade_config_uuid, margin_call_mode, telegram_id, integrated_margin_call_callback):
        try:
            # margin_call_mode == None -> Do nothing,
            # margin_call_mode == 1 -> Only warning message, 
            # margin_call_mode == 2 -> message & auto exit
            if margin_call_mode == None:
                return

            elif margin_call_mode == 1 or margin_call_mode == 2:
                margin_type = res['p'][0]['mt'] # CROSSED or ISOLATED
                base_asset = res['p'][0]['s'].replace('USDT', '')
                position_side = res['p'][0]['ps']
                mark_price = float(res['p'][0]['mp'])
                position_amount = float(res['p'][0]['pa'])
                unrealized_pnl = float(res['p'][0]['up'])
                # Send margin call message
                title = f"<b>마진콜 경고!</b> 바이낸스 {base_asset}USDT 의 <b>미실현손익이 위험수위</b>에 도달했습니다.\n"
                body += f"바이낸스 포지션: {position_side}, 마진타입: {margin_type}\n"
                body += f"미실현손익: {unrealized_pnl}USDT, 포지션수량: {position_amount}\n"
                body += f"{base_asset}USDT 현재 Mark가격: {mark_price}USDT"
                msg_full = f"{title}\n{body}"
                self.acw_api.create_message_thread(telegram_id, title, self.node, 'warning', msg_full, send_times=5, send_term=5)

                # If margin_call_mode == 2, execute auto exit
                if margin_call_mode == 2:
                    body = f"마진콜 모니터링 설정에 따라, 자동거래에 진입되어 있는 {self.my_exchange}와 {self.counterpart_exchange}의 포지션을 자동정리합니다."
                    self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리", self.node, 'info', body)

                    trade_df = self.trade_df_dict.get(self.market_combi_code)
                    waiting_df = trade_df[(trade_df['trade_config_uuid']==trade_config_uuid)&(trade_df['base_asset']==base_asset)&(self.addcoin_df['trade_switch']==-1)]
                    if len(waiting_df) == 0:
                        body = f"{base_asset}USDT는 차익거래에 진입되어있는 상태가 아닙니다.\n"
                        body += f"포지션 자동정리를 취소합니다."
                        self.acw_api.create_message_thread(telegram_id, "마진콜 자동정리 취소", self.node, 'info', body)
                        return
                    integrated_margin_call_callback(trade_config_uuid, margin_call_mode, telegram_id, base_asset, waiting_df)
                    



                # # There's waiting trade
                # for row_tup in waiting_df.iterrows():
                #     # load api keys
                #     access_key, secret_key = self.get_api_key_tup(trade_config_uuid, futures=True)
                #     row = row_tup[1]
                #     redis_uuid = row['redis_uuid']
                #     symbol = row['symbol'].replace('USDT', '')
                #     # Order record validation
                #     if row['enter_upbit_uuid'] == None or row['enter_binance_orderId'] == None:
                #         body = f"거래ID:{redis_uuid_to_display_id(self.addcoin_df, redis_uuid)}({symbol})에 대한 진입기록이 조회되지 않습니다.\n"
                #         body += f"포지션 자동정리를 취소합니다."
                #         self.telegram_bot.send_thread(chat_id=user_id, text=body)
                #         self.register_trading_msg(user_id, "usd_m_margin_call_callback", "user_msg", 'normal', "마진콜 자동정리 취소", body)
                #         continue
                #     # # UPDATE DataFrame memory
                #     # user_alarm_df.loc[row['id'], 'auto_trade_switch'] = 1
                #     corr_index = self.addcoin_df[self.addcoin_df['redis_uuid']==redis_uuid].index[0]
                #     self.addcoin_df.loc[corr_index, 'auto_trade_switch'] = 1
                #     # UPDATE database
                #     db_client = InitDBClient(**self.local_db_dict)
                #     db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, auto_trade_switch=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, 1, row['redis_uuid']))
                #     db_client.conn.commit()

                #     upbit_exit_qty = self.trade_history_df[self.trade_history_df['upbit_uuid']==row['enter_upbit_uuid']]['upbit_qty'].values[0]
                #     binance_exit_qty = self.trade_history_df[self.trade_history_df['upbit_uuid']==row['enter_upbit_uuid']]['binance_qty'].values[0]
                #     exit_id_list = []
                #     self.exit_func(self.get_kimp_df_func(), self.get_dollar_dict()['price'], user_id, redis_uuid, symbol, (upbit_exit_qty,binance_exit_qty), \
                #         user_upbit_access_key, user_upbit_secret_key, user_binance_access_key, user_binance_secret_key, exit_id_list)
                #     try:
                #         self.exec_pnl(self.get_kimp_df_func(), user_id, redis_uuid, exit_id_list[0], self.get_dollar_dict()['price'])
                #     except Exception as e:
                #         self.snatcher_logger.error(f"usd_m_margin_call_callback 에서 exit_func 이후 exec_pnl 실패|{traceback.format_exc()}")
                #         body = traceback.format_exc(e)
                #         register(self.monitor_bot_token, self.monitor_bot_url, self.admin_id, self.node, 'error', "usd_m_margin_call_callback 에서 exec_pnl 에러 발생", body)
                #     try:
                #         db_client.curr.execute("""UPDATE addcoin SET last_updated_timestamp=%s, exit_upbit_uuid=%s, exit_binance_orderId=%s WHERE redis_uuid=%s""", (datetime.datetime.now().timestamp()*10000000, exit_id_list[0], exit_id_list[1], row['redis_uuid']))
                #         db_client.conn.commit()
                #         db_client.conn.close()
                #     except Exception as e:
                #         db_client.conn.close()
                #         self.snatcher_logger.error(f"usd_m_margin_call_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패|{traceback.format_exc()}")
                #         title = "usd_m_margin_call_callback 에서 exit_func 이후 uuid, orderId UPDATE 실패"
                #         body = f"{title}\n"
                #         body += f"user_id: {user_id}, redis_uuid: {row['redis_uuid']}, symbol: {symbol}\n"
                #         body += f"Error: {e}"
                #         self.telegram_bot.send_thread(chat_id=self.admin_id, text=body)
                #         self.register_trading_msg(self.admin_id, "usd_m_margin_call_callback", "admin_msg", 'error', title, body)
            else:
                return
        except Exception as e:
            self.logger.error(f"usd_m_margin_call_callback|{traceback.format_exc()}")
            title = "usd_m_margin_call_callback 에서 에러 발생!"
            body = f"{title}\n"
            body += f"trade_config_uuid: {trade_config_uuid}, margin_call_mode: {margin_call_mode}({type(margin_call_mode)}), error: {e}"
            full_content = f"{title}\n{body}"
            self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'monitor', full_content, send_times=1, send_term=1)
            return
        
    def usd_m_liquidation_callback(res, trade_config_uuid, margin_call_mode, telegram_id, counterpart_liquidation_callback):
        pass

    async def user_usd_m_socket(self, access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id, counterpart_margin_call_callback, counterpart_liquidation_callback):
        client = await AsyncClient.create(access_key, secret_key)
        bm = BinanceSocketManager(client)
        # start any sockets here, i.e a trade socket
        ts = bm.futures_socket()
        # then start receiving messages
        async with ts as tscm:
            while True:
                try:
                    res = await tscm.recv()
                    self.logger.info(f"user_usd_m_socket stream|trade_config_uuid:{trade_config_uuid}\nres: {res}\n") # test
                    if res['e'] == "MARGIN_CALL":
                        self.usd_m_margin_call_callback(res, trade_config_uuid, margin_call_mode, telegram_id, counterpart_margin_call_callback)
                    if res['e'] == "ACCOUNT_UPDATE":
                        # self.reflect_binance_account_update(user_id, res)
                        pass
                    if res['e'] == "ORDER_TRADE_UPDATE" and res['o']['o'] == 'LIQUIDATION':
                        self.usd_m_liquidation_callback(res, trade_config_uuid, margin_call_mode, telegram_id, counterpart_liquidation_callback)
                except Exception as e:
                    title = "user_usd_m_socket 에서 에러 발생!"
                    body = f"{title}]n"
                    body += f"error: {e}"
                    msg_full = f"{title}\n{body}"
                    self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'error', msg_full, send_times=1, send_term=1)
                time.sleep(0.3)

    def user_usd_m_socket_async(self, access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id, counterpart_margin_call_callback, counterpart_liquidation_callback):
        asyncio.run(self.user_usd_m_socket(access_key, secret_key, trade_config_uuid, margin_call_mode, telegram_id, counterpart_margin_call_callback, counterpart_liquidation_callback))

    def start_user_socket_stream(self, market_type, counterpart_margin_call_callback, counterpart_liquidation_callback, loop_secs=3, monitor_loop_secs=2.5):
        # A user should have at least one trade_df setting to start user socket stream.
        if market_type.upper() not in ["USD_M"]:
            raise Exception(f"market_type: {market_type} is not supported yet.")
        self.logger.info(f"start_socket_stream|start_socket_stream started.")
        def monitor_user_stream_loop():
            input_type = 'monitor'
            title = 'monitor_user_stream stopped! restarting monitor_user_stream thread..'
            def monitor_user_stream():
                try:
                    while True:
                        time.sleep(loop_secs)
                        # Add monitoring thread if there isn't one
                        trade_df = self.trade_df_dict.get(self.market_combi_code)
                        if len(trade_df) == 0:
                            continue
                        unique_trade_df = trade_df.drop_duplicates(subset=['trade_config_uuid'])
                        # temporary df
                        unique_trade_df['api_keys'] = unique_trade_df['trade_config_uuid'].apply(lambda x: self.get_api_key_tup(x, futures=(False if market_type.upper()=='SPOT' else True), raise_error=False))
                        unique_trade_df[['access_key','secret_key']] = pd.DataFrame(unique_trade_df['api_keys'].tolist(), index=unique_trade_df.index)
                        # delete temporary df
                        unique_trade_df.drop(columns=['api_keys'], inplace=True)
                        # Drop if there's no api key
                        unique_trade_df = unique_trade_df.dropna(subset=['access_key', 'secret_key'])

                        for row_tup in unique_trade_df.iterrows():
                            row = row_tup[1]
                            if 'BINANCE' in self.market_combi_code.split(':')[0]:
                                margin_call_mode = row['target_market_margin_call']
                            else:
                                margin_call_mode = row['origin_market_margin_call']
                            if self.user_stream_monitoring_list == []:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_socket_async, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id'], counterpart_margin_call_callback, counterpart_liquidation_callback), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"trade_config_uuid: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            elif row['trade_config_uuid'] not in [x[0] for x in self.user_stream_monitoring_list]:
                                monitor_thread_tup = (row['trade_config_uuid'], Thread(target=self.user_usd_m_socket_async, args=(
                                    row['access_key'], row['secret_key'], row['trade_config_uuid'], margin_call_mode, row['telegram_id'], counterpart_margin_call_callback, counterpart_liquidation_callback), daemon=True))
                                monitor_thread_tup[1].start()
                                self.user_stream_monitoring_list.append(monitor_thread_tup)
                                self.logger.info(f"user_id: {row['trade_config_uuid']}'s user_stream monitor thread has been initiated.")
                            time.sleep(0.25)
                        # Remove dead thread or unauthorized thread from the list
                        for i,each_tup in enumerate(self.user_stream_monitoring_list):
                            trade_config_uuid = self.user_stream_monitoring_list[i][0]
                            status_flag = True
                            if each_tup[1].is_alive() is False:
                                status_flag = False
                                self.logger.error(f"trade_config_uuid: {trade_config_uuid}'s user_stream monitoring thread has died!")
                                title = f"trade_config_uuid: {trade_config_uuid}'s binance user_stream monitoring thread has died!"
                                self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'monitor', title, send_times=1, send_term=1)
                            if trade_config_uuid not in unique_trade_df['trade_config_uuid'].values:
                                title = f"trade_config_uuid: {trade_config_uuid}'s not in the unique_trade_df! status_flag = False.."
                                self.logger.info(title)
                                status_flag = False
                            if status_flag is False:
                                title = f"trade_config_uuid: {trade_config_uuid}'s user_stream monitoring thread has been removed!"
                                self.logger.info(title)
                                self.user_stream_monitoring_list.pop(i)
                except Exception:
                    self.logger.error(f"monitor_user_stream|{traceback.format_exc()}")

            monitor_user_stream_thread = Thread(target=monitor_user_stream, daemon=True)
            monitor_user_stream_thread.start()
            while True:
                if not monitor_user_stream_thread.is_alive():
                    self.logger.error(f"monitor_user_stream|monitor_user_stream stopped! restarting monitor_user_stream thread..")
                    title = 'monitor_user_stream stopped! restarting monitor_user_stream thread..'
                    self.acw_api.create_message_thread(self.admin_telegram_id, title, self.node, 'monitor', title, send_times=1, send_term=1)
                    monitor_user_stream_thread = Thread(target=monitor_user_stream, daemon=True)
                    monitor_user_stream_thread.start()
                time.sleep(monitor_loop_secs)
        self.start_socket_stream_thread = Thread(target=monitor_user_stream_loop, daemon=True)
        self.start_socket_stream_thread.start()