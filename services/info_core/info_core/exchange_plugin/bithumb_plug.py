import os
import sys
import datetime
import pandas as pd
import time
import traceback
import requests

from loggers.logger import InfoCoreLogger

class Bithumb:
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.server_url = "https://api.bithumb.com"
        self.headers = {"accept": "application/json"}

    def spot_all_tickers(self, market=None):
        if market is None:
            market_list = ["KRW", "BTC"]
        else:
            market_list = [market]
        total_df = pd.DataFrame()
        for each_market in market_list:
            url = f"/public/ticker/ALL_{each_market}"
            res = requests.get(self.server_url + url, headers=self.headers)
            ticker_df = pd.DataFrame(res.json()['data']).T.reset_index()
            ticker_df['quote_asset'] = each_market
            total_df = pd.concat([total_df, ticker_df], axis=0)
        total_df.reset_index(drop=True, inplace=True)
        total_df = total_df[total_df['index'] != 'date'].rename(columns={'index': 'base_asset', 'acc_trade_value_24H':'atp24h', "closing_price":"lastPrice"})
        total_df.loc[:, 'opening_price':'fluctate_rate_24H'] = total_df.loc[:, 'opening_price':'fluctate_rate_24H'].astype(float)
        total_df['symbol'] = total_df['base_asset'] + '_' + total_df['quote_asset']
        return total_df
    
    def spot_exchange_info(self):
        return self.spot_all_tickers()

    def wallet_status(self):
        network_df = pd.DataFrame()
        base_asset_list = self.spot_all_tickers()['base_asset'].to_list()
        for each_base_asset in base_asset_list:
            res = requests.get(f'https://api.bithumb.com/public/assetsstatus/multichain/{each_base_asset}')
            df = pd.DataFrame(res.json()['data'])
            df.loc[:, 'currency'] = each_base_asset
            network_df = pd.concat([network_df, df])
            time.sleep(0.025)
        network_df = network_df.rename(columns={'currency': 'asset', 'net_type':'network_type', 'deposit_status': 'deposit', 'withdrawal_status': 'withdraw'})
        network_df.loc[:, 'deposit'] = network_df['deposit'].apply(lambda x: str(x) == '1')
        network_df.loc[:, 'withdraw'] = network_df['withdraw'].apply(lambda x: str(x) == '1')
        network_df.loc[:, 'network_type'] = network_df['network_type'].apply(lambda x: x.split('_')[0])

        return network_df

class InitBithumbAdaptor:
    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        self.my_client = Bithumb(my_access_key, my_secret_key)
        self.pub_client = Bithumb()
        self.bithumb_plug_logger = InfoCoreLogger("bithumb_plug", logging_dir).logger
        self.bithumb_plug_logger.info(f"bithumb_plug_logger started.")

    def wallet_status(self):
        return self.pub_client.wallet_status()
    
    def spot_all_tickers(self):
        return self.pub_client.spot_all_tickers()

    def spot_exchange_info(self):
        return self.pub_client.spot_exchange_info()
