import datetime
import time
import pandas as pd

from binance.client import Client

def binance_usdm_fundingrate(timedelta_hours=9):
    bi_client = Client()
    binance_fund = pd.DataFrame(bi_client.futures_mark_price())[['symbol','lastFundingRate','nextFundingTime']]
    binance_fund = binance_fund.rename(columns={'symbol':'binance', 'lastFundingRate':'binance_fundingrate', 'nextFundingTime':'fundingtime'})
    binance_fund.iloc[:,-1] = binance_fund.iloc[:,-1].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
    binance_fund['symbol'] = binance_fund['binance'].apply(lambda x: x.replace('USDT',''))
    first_column = binance_fund.pop('symbol')
    binance_fund.insert(0, 'symbol', first_column)
    binance_fund = binance_fund[~binance_fund['binance'].str.contains(r'\d')].reset_index(drop=True)
    binance_fund = binance_fund.rename(columns={'binance':'full_symbol', 'binance_fundingrate':'fundingrate'})
    binance_fund['exchange'] = 'binance'
    binance_fund.loc[:,'fundingtime'] = binance_fund['fundingtime'] + datetime.timedelta(hours=timedelta_hours)
    return binance_fund

def fetch_fundingrate_loop(return_dict):
    return_dict['result'] = binance_usdm_fundingrate()
    return_dict['last_updated_time'] = datetime.datetime.now()
    before_day = None
    before_hour = None
    before_minute = None
    while True:
        time.sleep(0.15)
        now_datetime = datetime.datetime.now()
        now_day = now_datetime.day
        now_hour = now_datetime.hour
        now_minute = now_datetime.minute
        now_second = now_datetime.second
        if now_second == 1:
            if now_day == before_day and now_hour == before_hour and now_minute == before_minute:
                return_dict['result'] = binance_usdm_fundingrate()
                return_dict['last_updated_time'] = datetime.datetime.now()
                continue
            else:
                before_day = now_day
                before_hour = now_hour
                before_minute = now_minute
                # print(f"now_datetime: {now_datetime}")