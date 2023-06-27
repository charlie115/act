import os
import sys
import datetime
import pandas as pd
from upbit.client import Upbit
import time
import traceback

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

def calculate_upbit_price(price):
    if price >= 2000000:
        price = int(price/1000)*1000
    elif price >= 1000000:
        price = int(price/500)*500
    elif price >= 500000:
        price = int(price/100)*100
    elif price >= 100000:
        price = int(price/50)*50
    elif price >= 10000:
        price = int(price/10)*10
    elif price >= 1000:
        price = int(price/5)*5
    elif price >= 100:
        price = int(price)
    elif price >= 10:
        price = int(price*10)/10
    elif price >= 1:
        price = int(price*100)/100
    elif price >= 0.1:
        price = int(price*1000)/1000
    elif 0.1 > price:
        price = int(price*10000)/10000

    return price

class InitUpbitAdaptor:
    def __init__(self, my_upbit_access_key=None, my_upbit_secret_key=None, logging_dir=None):
        self.my_upbit_client = Upbit(my_upbit_access_key, my_upbit_secret_key)
        self.pub_upbit_client = Upbit()
        self.user_client_dict = {}
        self.upbit_plug_logger = KimpBotLogger("upbit_plug", logging_dir).logger
        self.retry_term_sec = 0.2
        self.retry_count_limit = 2
        self.upbit_plug_logger.info(f"upbit_plug_logger started.")

    def load_user_client(self, user_upbit_access_key, user_upbit_secret_key):
        user_client = self.user_client_dict.get(user_upbit_access_key)
        if user_client is None:
            self.user_client_dict[user_upbit_access_key] = Upbit(user_upbit_access_key, user_upbit_secret_key)
            return self.user_client_dict[user_upbit_access_key]
        else:
            return user_client

    def check_upbit_api_key(self, user_upbit_access_key, user_upbit_secret_key):
        self.user_client_dict.pop(user_upbit_access_key, None)
        client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        res = client.Account.Account_info()
        if res['response']['status_code'] == 200:
            return (True, 'OK')
        else:
            self.user_client_dict.pop(user_upbit_access_key, None)
            return (False, res['result']['error']['message'])

    # Upbit order functions # Original
    def upbit_market_enter(self, user_upbit_access_key, user_upbit_secret_key, symbol, capital, return_dict=None):
        client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        if return_dict is None:
            res = client.Order.Order_new(
                market=symbol,
                side='bid',
                price=capital,
                ord_type='price'
            )
            return res
        else:
            res = client.Order.Order_new(
                market=symbol,
                side='bid',
                price=capital,
                ord_type='price'
            )
            return_dict['res'] = res

    # # Upbit order functions # retry version
    # def upbit_market_enter(self, user_upbit_access_key, user_upbit_secret_key, symbol, capital, return_dict=None):
    #     client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)

    #     retry_count = 0

    #     while retry_count <= self.retry_count_limit:
    #         res = client.Order.Order_new(
    #             market=symbol,
    #             side='bid',
    #             price=capital,
    #             ord_type='price'
    #         )
    #         res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.retry_count_limit, 'retry_term_sec': self.retry_term_sec}
    #         if return_dict is not None:
    #             return_dict['res'] = res
    #         if retry_count != 0:
    #             self.upbit_plug_logger.info(f"upbit_market_enter|res: {res}, symbol: {symbol}, capital: {capital}")
    #         if res['response']['status_code'] == 201: # If it's not error -> return
    #             return res
    #         retry_error_case = False
    #         if '알수없는' in res['result']['error']['message']:
    #             retry_error_case = True
    #         if '일시적인 거래량 급증' in res['result']['error']['message']:
    #             retry_error_case = True
    #         if retry_error_case is False: # If it's normal error -> return
    #             return res
    #         retry_count += 1
    #         time.sleep(self.retry_term_sec)
    #     return res
    
    # Upbit order functions # retry version
    def upbit_limit_market_enter(self, user_upbit_access_key, user_upbit_secret_key, symbol, qty, price, return_dict=None):
        client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            res = client.Order.Order_new(
                market=symbol,
                side='bid',
                volume=str(qty),
                price=str(calculate_upbit_price(price*1.25)),
                ord_type='limit'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.retry_count_limit, 'retry_term_sec': self.retry_term_sec}
            if return_dict is not None:
                return_dict['res'] = res
            if retry_count != 0:
                self.upbit_plug_logger.info(f"upbit_limit_market_enter|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}")
            if res['response']['status_code'] == 201: # If it's not error -> return
                return res
            retry_error_case = False
            if '알수없는' in res['result']['error']['message']:
                retry_error_case = True
            if '일시적인 거래량 급증' in res['result']['error']['message']:
                retry_error_case = True
            if retry_error_case is False: # If it's normal error -> return
                self.upbit_plug_logger.info(f"upbit_limit_market_enter|res: {res}, symbol: {symbol}, qty: {qty}, price: {price}") # TEST
                return res
            retry_count += 1
            time.sleep(self.retry_term_sec)
        return res


    def upbit_order_info(self, user_upbit_access_key, user_upbit_secret_key, uuid, return_dict=None):
        client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        if return_dict is None:
            res = client.Order.Order_info(uuid=uuid)
            if res['response']['status_code'] != 200:
                raise Exception(res['result']['error']['message'])
            return res
        else:
            return_dict['res'] = client.Order.Order_info(uuid=uuid)
            # if res['response']['status_code'] != 200:
            #     raise Exception(res['result']['error']['message'])

    # # Original
    # def upbit_market_exit(self, user_upbit_access_key, user_upbit_secret_key, symbol, executed_volume, return_dict=None):
    #     client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
    #     if return_dict is None:
    #         res = client.Order.Order_new(
    #             market=symbol,
    #             side='ask',
    #             volume=executed_volume,
    #             ord_type='market'
    #         )
    #         # if res['response']['status_code'] != 201:   # test
    #         #     raise Exception(res['result']['error']['message'])  # test
    #         return res
    #     else:
    #         return_dict['res'] = client.Order.Order_new(
    #             market=symbol,
    #             side='ask',
    #             volume=executed_volume,
    #             ord_type='market'
    #         )

    def upbit_market_exit(self, user_upbit_access_key, user_upbit_secret_key, symbol, executed_volume, return_dict=None):
        client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)

        retry_count = 0

        while retry_count <= self.retry_count_limit:
            res = client.Order.Order_new(
                market=symbol,
                side='ask',
                volume=executed_volume,
                ord_type='market'
            )
            res = {**res, 'retry_count': retry_count, 'retry_count_limit': self.retry_count_limit, 'retry_term_sec': self.retry_term_sec}
            if return_dict is not None:
                return_dict['res'] = res
            if retry_count != 0:
                self.upbit_plug_logger.info(f"upbit_market_exit|res: {res}, symbol: {symbol}, executed_volume: {executed_volume}")
            if res['response']['status_code'] == 201: # If it's not error -> return
                return res
            retry_error_case = False
            if '알수없는' in res['result']['error']['message']:
                retry_error_case = True
            if '일시적인 거래량 급증' in res['result']['error']['message']:
                retry_error_case = True
            if retry_error_case is False: # If it's normal error -> return
                return res
            retry_count += 1
            time.sleep(self.retry_term_sec)
        return res

    def upbit_position_information(self, user_upbit_access_key, user_upbit_secret_key, symbol, return_dict=None):
        upbit_client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        if return_dict is None:
            res = upbit_client.Account.Account_info()
            if res['response']['status_code'] != 200:
                raise Exception(res['result']['error']['message'])
            position_df = pd.DataFrame(res['result'])
            symbol_df = position_df[position_df['currency']==symbol]['balance']
            if len(symbol_df)==0:
                upbit_remaining_qty =0
            else:
                upbit_remaining_qty = float(symbol_df.iloc[0])
            return upbit_remaining_qty
        else:
            return_dict['res'] = upbit_client.Account.Account_info()

    def upbit_all_position_information(self, user_upbit_access_key, user_upbit_secret_key, return_dict=None):
        upbit_client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        if return_dict is None:
            res = upbit_client.Account.Account_info()
            if res['response']['status_code'] != 200:
                raise Exception(res['result']['error']['message'])
            position_df = pd.DataFrame(res['result'])
            position_df.loc[:, 'balance':'avg_buy_price'] = position_df.loc[:, 'balance':'avg_buy_price'].astype(float)
            return position_df
        else:
            return_dict['res'] = upbit_client.Account.Account_info()

    def upbit_all_ticker(self, user_upbit_access_key, user_upbit_secret_key, return_dict=None):
        upbit_client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        upbit_symbols_df = pd.DataFrame(upbit_client.Market.Market_info_all()['result'])
        upbit_symbols = upbit_symbols_df[upbit_symbols_df['market'].str.contains('KRW')]['market'].to_list()
        upbit_all_ticker_df = pd.DataFrame(upbit_client.Trade.Trade_ticker(markets=','.join(upbit_symbols))['result'])
        if return_dict is None:
            res = upbit_all_ticker_df
            return res
        else:
            return_dict['res'] = upbit_all_ticker_df

    def get_upbit_spot_balance(self, user_upbit_access_key, user_upbit_secret_key, return_dict=None):
        upbit_client = self.load_user_client(user_upbit_access_key, user_upbit_secret_key)
        result_df = pd.DataFrame(upbit_client.Account.Account_info()['result'])
        result_df.loc[:, ['balance','locked','avg_buy_price']] = result_df[['balance','locked','avg_buy_price']].astype(float)
        if return_dict is None:
            return result_df
        else:
            return_dict['res'] = result_df

    # Upbit fetching candles
    def upbit_fetch_candle(self, coin_name, period, count=200):
        try:
            period = str(period)
            if period.lower() == 'days':
                res = self.pub_upbit_client.Candle.Candle_days(market=coin_name, count=count)
            elif period.lower() == 'weeks':
                res = self.pub_upbit_client.Candle.Candle_weeks(market=coin_name, count=count)
            elif period.lower() == 'months':
                res = self.pub_upbit_client.Candle.Candle_month(market=coin_name, count=count)
            else:
                period = int(period)
                res = self.pub_upbit_client.Candle.Candle_minutes(unit=period, market=coin_name, count=count)

            btc_200days = pd.DataFrame(res['result'])
            btc_200days_df = btc_200days[['candle_date_time_kst', 'opening_price', 'high_price', 'low_price', 'trade_price', 'candle_acc_trade_volume']]
            btc_200days_df.iloc[:,0] = btc_200days_df['candle_date_time_kst'].apply(lambda x:datetime.datetime.strptime(x, "%Y-%m-%dT%H:%M:%S"))#.apply(lambda x: x.date())
            btc_200days_df = btc_200days_df.sort_values(by='candle_date_time_kst', ascending=True).reset_index(drop=True)
            return btc_200days_df, btc_200days
        except Exception:
            self.upbit_plug_logger.error(f"upbit_fetch_candle|Error occured coin_name:{coin_name}, period: {[period]}, res: {res}, {traceback.format_exc()}")
            raise Exception