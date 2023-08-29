import sys
import os
import datetime
import traceback
import pandas as pd
import time
from binance.client import Client

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class InitBinanceAdaptor:
    def __init__(self, my_binance_access_key=None, my_binance_secret_key=None, recvWindow=45000, logging_dir=None):
        self.my_bi_client = Client(my_binance_access_key, my_binance_secret_key)
        self.pub_client = Client()
        self.recvWindow = recvWindow
        self.binance_plug_logger = KimpBotLogger("binance_plug", logging_dir).logger
        self.binance_plug_logger.info(f"binance_plug_logger started.")

    # Admin
    def get_deposit(self, asset='EOS'):
        deposit = pd.DataFrame(self.my_bi_client.get_deposit_history(asset=asset))
        deposit.loc[:,'insertTime'] = deposit['insertTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        deposit.loc[:, 'amount'] = deposit['amount'].astype(float)
        return deposit
    
    def spot_all_tickers(self):
        df = pd.DataFrame(self.pub_client.get_ticker())
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def spot_exchange_info(self):
        df = pd.DataFrame(self.pub_client.get_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def usdm_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df
    
    def coinm_exchange_info(self):
        df = pd.DataFrame(self.pub_client.futures_coin_exchange_info()['symbols'])
        df = df.applymap(lambda x: pd.to_numeric(x, errors='ignore'))
        return df

    def usdm_fundingrate(self):
        bi_client = self.pub_client
        binance_fund = pd.DataFrame(bi_client.futures_mark_price())
        binance_fund = binance_fund.rename(columns={'symbol':'binance', 'lastFundingRate':'binance_fundingrate', 'nextFundingTime':'fundingtime'})
        binance_fund.loc[:,['nextFundingTime', 'time']] = binance_fund.loc[:,['nextFundingTime', 'time']].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
        binance_fund['symbol'] = binance_fund['binance'].apply(lambda x: x.replace('USDT',''))
        return binance_fund
