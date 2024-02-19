import sys
import os
import datetime
import traceback
import pandas as pd
import numpy as np
import time
from binance.client import Client

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

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
    def __init__(self, recvWindow=45000, logging_dir=None):
        self.user_client_dict = {}
        self.recvWindow = recvWindow
        self.logger = KimpBotLogger("user_binance_plug", logging_dir).logger
        self.retry_term_sec = 0.2
        self.retry_count_limit = 2
        self.logger.info(f"user_binance_plug_logger started.")

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
        if return_dict is None:
            client = self.load_user_client(access_key, secret_key)
            usdm_balance_df = pd.DataFrame(client.futures_account_balance())
            usdm_balance_df.loc[:, ['balance', 'maxWithdrawAmount']] = usdm_balance_df[['balance', 'maxWithdrawAmount']].astype(float)
            return usdm_balance_df
        else:
            client = self.load_user_client(access_key, secret_key)
            usdm_balance_df = pd.DataFrame(client.futures_account_balance())
            usdm_balance_df.loc[:, ['balance', 'maxWithdrawAmount']] = usdm_balance_df[['balance', 'maxWithdrawAmount']].astype(float)
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

    def market_enter(self, access_key, secret_key, symbol, qty, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            if retry_count >= 1:
                self.logger.info(f"market_enter|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
            try:
                res = client.futures_create_order(
                    symbol=symbol,
                    side='SELL',
                    type='MARKET',
                    quantity=qty,
                    recvWindow=self.recvWindow
                )
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['state'] = 'OK'
                return res
            except Exception as e:
                if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['state'] = 'ERROR'
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

    def market_exit(self, access_key, secret_key, symbol, qty, return_dict=None):
        client = self.load_user_client(access_key, secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            if retry_count >= 1:
                self.logger.info(f"market_exit|retry_count: {retry_count}, retry_term_sec: {self.retry_term_sec}, retry_count_limit: {self.retry_count_limit}") # For TESTING
            try:
                res = client.futures_create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=qty,
                recvWindow=self.recvWindow
                )
                if return_dict is not None:
                    return_dict['res'] = res
                    return_dict['state'] = 'OK'
                return res
            except Exception as e:
                if e.code not in [-1000, -1001] or retry_count == self.retry_count_limit:
                    if return_dict is None:
                        raise e
                    else:
                        return_dict['res'] = e
                        return_dict['state'] = 'ERROR'
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