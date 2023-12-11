import os
import sys
import datetime
import pandas as pd
import time
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class Bithumb:
    def __init__(self, api_key=None, secret_key=None):
        self.api_key = api_key
        self.secret_key = secret_key
        self.server_url = "https://api.bithumb.com"
        self.headers = {"accept": "application/json"}
        self.chrome_driver_path = "/usr/local/bin/chromedriver"

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
        url = "https://www.bithumb.com/coin_inout/compare_price"
        # Set up driver
        service = Service(self.chrome_driver_path)
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

        # Get a webpage
        driver.get(url)
        wait = WebDriverWait(driver, 10)
        element = wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'g_tb_list')))

        element_list = driver.find_elements(By.CLASS_NAME, 'coin_list')
        element_list = [x.text for x in element_list]

        # Clean up (close browser once done)
        driver.quit()

        wallet_status_list = [x.split('(')[1] for x in element_list]
        wallet_status_list = [x.replace(')','').split(' ') for x in wallet_status_list]
        wallet_status_df = pd.DataFrame(wallet_status_list)
        def temp(row):
            try:
                float(row[2])
                if row[1] == "Mainnet":
                    return row[0]
                else:
                    return row[1]
            except:
                network_name = row[1] + " " + row[2]
                return network_name.upper()
        wallet_status_df['network_type'] = wallet_status_df.apply(lambda row:temp(row), axis=1)
        wallet_status_df = wallet_status_df.rename(columns={0:'asset', 3: 'deposit', 4: 'withdraw'})
        wallet_status_df.loc[:, 'deposit'] = wallet_status_df['deposit'].apply(lambda x: True if x == '정상' else False)
        wallet_status_df.loc[:, 'withdraw'] = wallet_status_df['withdraw'].apply(lambda x: True if x == '정상' else False)
        wallet_status_df['network_type'] = wallet_status_df['network_type'].replace('ERC-20', 'ETH').replace('TRC-20', 'TRX').replace('BEP-20', 'BSC')
        wallet_status_df = wallet_status_df[['asset','network_type','deposit','withdraw']]

        return wallet_status_df

class InitBithumbAdaptor:
    def __init__(self, my_access_key=None, my_secret_key=None, logging_dir=None):
        self.my_client = Bithumb(my_access_key, my_secret_key)
        self.pub_client = Bithumb()
        self.bithumb_plug_logger = KimpBotLogger("bithumb_plug", logging_dir).logger
        self.bithumb_plug_logger.info(f"bithumb_plug_logger started.")

    def wallet_status(self):
        return self.pub_client.wallet_status()
    
    def spot_all_tickers(self):
        return self.pub_client.spot_all_tickers()

    def spot_exchange_info(self):
        return self.pub_client.spot_exchange_info()