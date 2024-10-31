import logging
from multiprocessing import Process
from threading import Thread
import requests
import datetime
import websocket
import json
import time
import sys
import os
import traceback
import pandas as pd
import numpy as np
import pymysql
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import matplotlib.dates as mdates
from io import BytesIO
from sqlalchemy import create_engine
pymysql.install_as_MySQLdb()
import MySQLdb
import mplfinance as mpf

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from info_core.etc.db_handler.postgres_client import InitDBClient
from loggers.logger import InfoCoreLogger

def mean_norm(df_input):
    return df_input.apply(lambda x: (x-x.mean())/x.std(), axis=0)

# Used to save DataFrame into DB
def db_engine(host, port, user, passwd, database):
    url = f'mysql+mysqldb://{user}:{passwd}@{host}:{port}/{database}'
    engine = create_engine(url)
    return engine

# get dollar exchange rate
def get_dollar():
    try:
        exchange_rate = pd.read_html('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%ED%99%98%EC%9C%A8%EC%A1%B0%ED%9A%8C')[0]
        dollar = exchange_rate.iloc[0,1]
    except Exception as e:
        print(f'Except executed in get_dollar function, {e}')
        exchange_rate = pd.read_html('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=1&ie=utf8&query=%ED%99%98%EC%9C%A8%EC%A1%B0%ED%9A%8C')[1]
        dollar = exchange_rate.iloc[0,1]
    return dollar

def krw(krw_num):
    return format(krw_num, ',')

def calculate_service_charge(net_profit, referral_flag=False):
    min_fee = 300000
    service_charge = 0
    net_profit_sections = [0, 3000000, 6000000, 9000000, 12000000, 9999999999]
    fee_sections = [0.15, 0.13, 0.11, 0.09, 0.07]
    body = ""
    for i in range(len(fee_sections)):
        if net_profit - net_profit_sections[i+1] >= 0:
            section_fee = (net_profit_sections[i+1]-net_profit_sections[i])*fee_sections[i]
            service_charge += section_fee
            body += f"<b>{i+1}구간</b>: {krw(net_profit_sections[i])}원~{krw(net_profit_sections[i+1])}원 (요율 {round(fee_sections[i]*100)}%)\n"
            body += f"{i+1}구간 요금: {krw(int(section_fee))}원\n"
        else:
            section_fee = (net_profit - net_profit_sections[i])*fee_sections[i]
            service_charge += section_fee
            body += f"<b>{i+1}구간</b>: {krw(net_profit_sections[i])}원~{krw(net_profit_sections[i+1])}원 (요율 {round(fee_sections[i]*100)}%)\n"
            body += f"{i+1}구간 요금: {krw(int(section_fee))}원"
            break
    if referral_flag:
        service_charge = service_charge * 0.85
        referral_str = "레퍼럴 할인 적용됨"
    else:
        referral_str = "레퍼럴 할인 미적용"
    body += f"\n<b>총계: {krw(int(max(min_fee, service_charge)))}</b>원 (최소 요금 30만 원, {referral_str})"
    return max(min_fee, service_charge), body


#######################################################################################################################################################################
class InitCommonInfo:
    def __init__(self, logging_dir, node, admin_id, db_dict, register_monitor_msg, kimp_core, kline_schema_name='coin_kimp_kline', MASTER=True):
        self.node = node
        self.admin_id = admin_id
        self.db_dict = db_dict
        self.register_monitor_msg = register_monitor_msg
        self.get_both_listed_okx_symbols = kimp_core.get_both_listed_okx_symbols
        self.common_info_logger = InfoCoreLogger("common_info_logger", logging_dir).logger
        self.upbit_adaptor = kimp_core.upbit_adaptor
        self.okx_adaptor = kimp_core.okx_adaptor
        self.kline_schema_name = kline_schema_name
        self.funding_dict = {}
        self.kimp_kline_proc1 = None
        self.kimp_kline_proc2 = None

        if MASTER:
            self.start_monitor_kimp_kline1(self.get_both_listed_okx_symbols())
            time.sleep(1.5)
            self.start_monitor_kimp_kline2(self.get_both_listed_okx_symbols())
            self.start_monitor_funding_info()

    # Check status of kline fetcher
    def kline_fetcher_proc_status(self):
        integrity_flag1 = self.kimp_kline_proc1.is_alive()
        integrity_flag2 = self.kimp_kline_proc2.is_alive()
        status_str = f"self.kimp_kline_proc1.is_alive(): {self.kimp_kline_proc1.is_alive()}"
        status_str += f"\nself.kimp_kline_proc2.is_alive(): {self.kimp_kline_proc2.is_alive()}"
        integrity_flag = integrity_flag1 and integrity_flag2
        return integrity_flag, status_str
        
    # Fetch dollar exchage rate for 200days
    def fetch_update_dollar_200(self):
        # If today's dollar data has already been stored, than use it
        def update_dollar_200():
            self.common_info_logger.info(f"update_dollar_200|Updating dollar 200 data.")
            concat_df = pd.DataFrame()
            for i in range(1,21):
                time.sleep(0.05)
                fetched = pd.read_html(f'https://finance.naver.com/marketindex/exchangeDailyQuote.nhn?marketindexCd=FX_USDKRW&page={i}')[0]
                concat_df = pd.concat([concat_df,fetched], ignore_index=True)
            concat_df.columns = [x[-1] for x in concat_df.columns]
            concat_df['날짜'] = concat_df['날짜'].apply(lambda x: datetime.datetime.strptime(x, '%Y.%m.%d')).apply(lambda x: x.date())
            dollar_df = concat_df.sort_values(by=['날짜'])
            dollar_df['last_updated_time'] = datetime.datetime.now()
            # Save to DB
            engine = db_engine(**self.db_dict)
            dollar_df.to_sql('dollar200', con=engine, if_exists='replace')
            return dollar_df
        
        db_client = InitDBClient(**self.db_dict)
        db_client.curr.execute("""SELECT * from dollar200;""")
        db_client.conn.close()
        fetched = db_client.curr.fetchall()
        fetched_df = pd.DataFrame(fetched)
        if len(fetched_df) == 0:
            dollar_df = update_dollar_200()
            return dollar_df
        else:
            fetched_df = fetched_df.drop('index', axis=1)

            # Fetch time info
            # conn, curr = connect_db(schema_name)
            # curr.execute("""SELECT object FROM pickle WHERE name='dollar_time'""")
            # fetched = curr.fetchall()[0]['object']
            # dollar_time = pickle.loads(fetched)
            dollar_time = fetched_df['last_updated_time'].iloc[-1]

            # If it's not been 1 hour from last update, just use old data
            if dollar_time != None and (dollar_time + datetime.timedelta(hours=1)) > datetime.datetime.now():
                # print('dollar200 is not older than 1 hour, using stored data.')
                return fetched_df

            # If it's been more than 1 hour, update dollar info and store new time data
            # conn, curr = connect_db(schema_name)
            # curr.execute("""UPDATE pickle SET object=%s WHERE name='dollar_time'""", (pickle.dumps(datetime.datetime.now())))
            # conn.commit()
            # conn.close()
            db_client = InitDBClient(**self.db_dict)
            db_client.curr.execute("""UPDATE dollar200 SET last_updated_time=%s""", (datetime.datetime.now()))
            db_client.conn.commit()
            db_client.conn.close()

            today_date = datetime.datetime.now().date()
            today_hour = datetime.datetime.now().hour
            if today_date.weekday() in [5,6]:
                today_adjusted = today_date - datetime.timedelta(days=(today_date.weekday()-4))
            else:
                today_adjusted = today_date

            if today_adjusted == fetched_df['날짜'].iloc[-1] or (today_hour < 10 or today_hour > 20):
                dollar = float(get_dollar())
                fetched_df.iloc[-1,1] = dollar
                dollar_df = fetched_df
                # Update newest dollar price to DB
                print(f"Updating only the latest day's dollar info of dollar200")
                db_client = InitDBClient(**self.db_dict)
                db_client.curr.execute("""UPDATE dollar200 SET 매매기준율=%s, last_updated_time=%s WHERE 날짜=%s""",(dollar, datetime.datetime.now(), today_adjusted))
                db_client.conn.commit()
                db_client.conn.close()
            # Else, update DB by fetching today's data
            else:
                dollar_df = dollar_df = update_dollar_200()
            return dollar_df

    # Calculate Kimp
    def kimp_history(self, coin, period, count=200):
        upbit = self.upbit_adaptor.upbit_fetch_candle(f'KRW-{coin}'.upper(), period, count)[0]
        okx = self.okx_adaptor.okx_fetch_candle(f'{coin}-USDT-SWAP'.upper(), period, count)
        # Fetch dollar data
        dollar_df = self.fetch_update_dollar_200()
        # Merge info from upbit and okx
        merged = upbit[['candle_date_time_kst','opening_price','high_price','low_price','trade_price']].merge(okx, how='inner', left_on='candle_date_time_kst', right_on='okx_time')
        merged['date'] = merged['candle_date_time_kst'].apply(lambda x: x.date())
        merged = merged.merge(dollar_df[['날짜','매매기준율']], how='left', left_on='date', right_on='날짜').drop('날짜', axis=1).fillna(method='ffill').fillna(dollar_df.iloc[-1,1])
        merged = merged.rename(columns={'candle_date_time_kst':'datetime_kst','high_price':'upbit_high', 'opening_price':'upbit_open', 'low_price':'upbit_low', 'trade_price':'upbit_close'})
        merged.loc[:,'okx_open':'okx_close'] = merged.loc[:,'okx_open':'okx_close'].astype(float)
        merged = merged.drop(['okx_time','date'], axis=1)
        merged['okx_open_krw'] = merged['okx_open'].multiply(merged['매매기준율'], axis=0)#.round(1)
        merged['okx_high_krw'] = merged['okx_high'].multiply(merged['매매기준율'], axis=0)#.round(1)
        merged['okx_low_krw'] = merged['okx_low'].multiply(merged['매매기준율'], axis=0)#.round(1)
        merged['okx_close_krw'] = merged['okx_close'].multiply(merged['매매기준율'], axis=0)#.round(1)
        merged['okx_open_kimp'] = (merged['upbit_open'] - merged['okx_open_krw'])/merged['okx_open_krw']
        merged['okx_high_kimp'] = (merged['upbit_high'] - merged['okx_high_krw'])/merged['okx_high_krw']
        merged['okx_low_kimp'] = (merged['upbit_low'] - merged['okx_low_krw'])/merged['okx_low_krw']
        merged['okx_close_kimp'] = (merged['upbit_close'] - merged['okx_close_krw'])/merged['okx_close_krw']
        return merged

    # Store kimp kline data to DB
    def store_kimp_kline(self, both_listed_symbols, period_list):
        self.common_info_logger.info(f"store_kimp_kline|store_kimp_kline started, period_list: {period_list}")
        db_dict = self.remote_db_dict.copy()
        db_dict['database'] = self.kline_schema_name
        db_dict['create_database'] = True
        start = datetime.datetime.now()
        coin_list = [x.replace('-USDT-SWAP','') for x in both_listed_symbols]

        # period_list = [1]
        # period_list = [5,30,60,240,'days','weeks']

        db_client = InitDBClient(**db_dict)
        for coin in coin_list:
            sql = """
                CREATE TABLE IF NOT EXISTS upbit_okxf_{coin}
                (
                    id int(10) NOT NULL AUTO_INCREMENT PRIMARY KEY,
                    datetime_kst datetime,
                    period text,
                    upbit_open float,
                    upbit_high float,
                    upbit_low float,
                    upbit_close float,
                    okx_open float,
                    okx_high float,
                    okx_low float,
                    okx_close float,
                    dollar float,
                    okx_open_krw float,
                    okx_high_krw float,
                    okx_low_krw float,
                    okx_close_krw float,
                    okx_open_kimp float,
                    okx_high_kimp float,
                    okx_low_kimp float,
                    okx_close_kimp float
                )
                """.format(coin=coin)
            db_client.curr.execute(sql)
            for period in period_list:
                result = db_client.curr.execute("""SELECT datetime_kst FROM upbit_okxf_{coin} WHERE period=%s ORDER BY datetime_kst DESC LIMIT 1""".format(coin=coin), str(period))
                if result == 0:
                    last_time = datetime.datetime.fromtimestamp(0)
                else:
                    fetched = db_client.curr.fetchall()
                    last_time = fetched[0]['datetime_kst']

                # Fetch kline data from upbit and okx
                kimp_kline_df = self.kimp_history(coin, period, count=200)
                time.sleep(0.2)
                filtered_kimp_kline_df = kimp_kline_df[kimp_kline_df['datetime_kst']>last_time].reset_index(drop=True)
                if len(filtered_kimp_kline_df) == 0:
                    continue

                for row_tup in filtered_kimp_kline_df.iterrows():
                    index = row_tup[0]
                    row = row_tup[1]
                    sql = """
                    INSERT INTO upbit_okxf_{coin}(
                        datetime_kst,
                        period,
                        upbit_open,
                        upbit_high,
                        upbit_low,
                        upbit_close,
                        okx_open,
                        okx_high,
                        okx_low,
                        okx_close,
                        dollar,
                        okx_open_krw,
                        okx_high_krw,
                        okx_low_krw,
                        okx_close_krw,
                        okx_open_kimp,
                        okx_high_kimp,
                        okx_low_kimp,
                        okx_close_kimp
                    ) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """.format(coin=coin)
                    val = (
                        row['datetime_kst'].to_pydatetime(),
                        str(period),
                        row['upbit_open'],
                        row['upbit_high'],
                        row['upbit_low'],
                        row['upbit_close'],
                        row['okx_open'],
                        row['okx_high'],
                        row['okx_low'],
                        row['okx_close'],
                        row['매매기준율'],
                        row['okx_open_krw'],
                        row['okx_high_krw'],
                        row['okx_low_krw'],
                        row['okx_close_krw'],
                        row['okx_open_kimp'],
                        row['okx_high_kimp'],
                        row['okx_low_kimp'],
                        row['okx_close_kimp']
                    )
                    db_client.curr.execute(sql, val)
                    # try:
                    #     db_client.curr.execute(sql,val)
                    # except:
                    #     raise Exception(f"store_kimp_kline|error occured, sql: {sql}, coin: {coin}, val: {val}")
        db_client.conn.commit()
        db_client.conn.close()
        self.common_info_logger.info(f'store_kimp_kline|history time spent: {datetime.datetime.now()-start}, period_list: {period_list}')

    # Functions for Thread
    # Every minute
    def while_kimp_kline1(self, both_listed_symbols):
        period_list = [1]
        self.common_info_logger.info(f"while_kimp_kline1|while_kimp_kline1 started, period_list: {period_list}")
        while True:
            try:
                now = datetime.datetime.now()
                if now.second == 1:
                    self.store_kimp_kline(both_listed_symbols, period_list)
                    self.common_info_logger.info(f"while_kimp_kline1 finished at: {datetime.datetime.now()}")
                    time.sleep(1)
            except Exception as e:
                self.common_info_logger.error(f"Error occurred in while_kimp_kline1, {e}|{traceback.format_exc()}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', "while_kimp_kline1", content=f"{e}")
                print(f'Error occurred in while_kimp_kline1, {e}')
                time.sleep(0.5)
            time.sleep(0.1)

    def start_monitor_kimp_kline1(self, both_listed_symbols, monitor_loop_secs=2):
        self.common_info_logger.info(f"start_monitor_kimp_kline1|start_monitor_kimp_kline1 started.")
        def monitor_func1():
            self.kimp_kline_proc1 = Process(target=self.while_kimp_kline1, args=(both_listed_symbols,), daemon=True)
            self.kimp_kline_proc1.start()
            while True:
                time.sleep(monitor_loop_secs)
                if not self.kimp_kline_proc1.is_alive():
                    self.common_info_logger.error(f"start_monitor_kimp_kline1|kimp_kline_proc1 stopped! Restarting the process..")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_kimp_kline1", "kimp_kline_proc1 stopped! Restarting the process..")
                    self.kimp_kline_proc1 = Process(target=self.while_kimp_kline1, args=(both_listed_symbols,), daemon=True)
                    self.kimp_kline_proc1.start()
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_kimp_kline1", f"kimp_kline_proc1.is_alive: {self.kimp_kline_proc1.is_alive()}")
        monitor_func1_thread = Thread(target=monitor_func1, daemon=True)
        monitor_func1_thread.start()

    # Every 5 minutes
    def while_kimp_kline2(self, both_listed_symbols):
        period_list = [5,30,60,240,'days','weeks']
        self.common_info_logger.info(f"while_kimp_kline2|while_kimp_kline2 started, period_list: {period_list}")
        while True:
            try:
                now = datetime.datetime.now()
                if (now.minute % 5 == 0) and now.second == 35:
                    self.store_kimp_kline(both_listed_symbols, period_list)
                    self.common_info_logger.info(f"while_kimp_kline2 finished at: {datetime.datetime.now()}")
                    time.sleep(1)
            except Exception as e:
                self.common_info_logger.error(f"Error occurred in while_kimp_kline2, {e}|{traceback.format_exc()}")
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', "while_kimp_kline2", content=f"{e}")
                time.sleep(0.5)
            time.sleep(0.1)

    def start_monitor_kimp_kline2(self, both_listed_symbols, monitor_loop_secs=2):
        self.common_info_logger.info(f"start_monitor_kimp_kline2|start_monitor_kimp_kline2 started.")
        def monitor_func2():
            self.kimp_kline_proc2 = Process(target=self.while_kimp_kline2, args=(both_listed_symbols,), daemon=True)
            self.kimp_kline_proc2.start()
            while True:
                time.sleep(monitor_loop_secs)
                if not self.kimp_kline_proc2.is_alive():
                    self.common_info_logger.error(f"start_monitor_kimp_kline2|kimp_kline_proc2 stopped! Restarting the process..")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_kimp_kline2", "kimp_kline_proc2 stopped! Restarting the process..")
                    self.kimp_kline_proc2 = Process(target=self.while_kimp_kline2, args=(both_listed_symbols,), daemon=True)
                    self.kimp_kline_proc2.start()
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_kimp_kline2", f"kimp_kline_proc2.is_alive: {self.kimp_kline_proc2.is_alive()}")
        monitor_func2_thread = Thread(target=monitor_func2, daemon=True)
        monitor_func2_thread.start()

    def update_funding_info(self, loop_time=60):
        self.common_info_logger.info(f"update_funding_info|update_funding_info started.")
        try:
            def okx_funding_rate_websocket(funding_dict, data):
                last_timestamp = [time.time()]
                def on_message(ws, message):
                    last_timestamp[0] = time.time()
                    if message == 'pong':
                        # print(f"pong received from the server!") # TEST
                        pass
                    else:
                        try:
                            message_dict = json.loads(message)
                            if 'data' in message_dict.keys():
                                # print(f"timestamp: {last_timestamp[0]}, {message_dict}") # TEST
                                funding_dict[message_dict['data'][0]['instId']] = {**message_dict['data'][0], "last_updated_time": datetime.datetime.now()}
                        except Exception as e:
                            self.common_info_logger.info(f"Error occured while json.loads message: {traceback.format_exc()}, message: {message}")
                            # print(f"Error occured while json.loads message: {traceback.format_exc()}, message: {message}") # TEST

                def on_error(ws, error):
                    self.common_info_logger.error(f'okx_funding_rate_websocket|okx_websocket on_error executed!\n Error: {error}')
                    # print(f'okx_funding_rate_websocket|okx_websocket on_error executed!\n Error: {error}') # TEST
                    raise Exception('okx_funding_rate_websocket|on_error executed!')

                def on_close(ws, close_status_code, close_msg):
                    self.common_info_logger.info(f"okx_funding_rate_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}")
                    # print(f"okx_funding_rate_websocket|\n\n### closed ###\nclose_msg: {close_msg}\nclose_status_code: {close_status_code}") # TEST
                    raise Exception('okx_funding_rate_websocket|on_close executed!')

                def on_open(ws):
                    # print(f'okx_funding_rate_websocket on_open started')
                    self.common_info_logger.info('okx_funding_rate_websocket|okx_websocket for fundingrate started')
                    # print('okx_funding_rate_websocket|okx_websocket started') # TEST
                    ws.send(json.dumps(data))

                def ping(ws):
                    while True:
                        time.sleep(0.5)
                        if time.time() - last_timestamp[0] > 25:
                            try:
                                ws.send('ping')
                                # print(f"ping sent to the server!") # TEST
                            except Exception as e:
                                self.common_info_logger.error(f"Error while trying to ping: {traceback.format_exc()}")
                                # print(f"Error while trying to ping: {traceback.format_exc()}") # TEST

                # websocket.enableTrace(False)
                ws = websocket.WebSocketApp("wss://ws.okx.com:8443/ws/v5/public",
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
                ping_thread = Thread(target=ping, args=(ws,))
                ping_thread.start()
                ws.run_forever()
            data = {"op": "subscribe", "args": []}
            for symbol in self.get_both_listed_okx_symbols():
                data["args"].append({"channel": "funding-rate", "instId": symbol})
            websocket_thread = Thread(target=okx_funding_rate_websocket, args=(self.funding_dict, data))
            websocket_thread.start()

            while True:
                db_client = InitDBClient(**self.remote_db_dict)
                db_client.curr.execute("""SELECT * FROM funding_info""")
                fetched_df = pd.DataFrame(db_client.curr.fetchall())
                if len(fetched_df) == 0:
                    old_fund_df = pd.DataFrame({"rec": None}, index=[])
                else:
                    old_fund_df = fetched_df

                # Fetch OKX funding df
                funding_df = pd.DataFrame(self.funding_dict).T.reset_index(drop=True)
                if len(funding_df) == 0:
                    continue
                funding_df.loc[:, ['fundingRate', 'fundingTime', 'nextFundingRate', 'nextFundingTime']] = funding_df.loc[:, ['fundingRate', 'fundingTime', 'nextFundingRate', 'nextFundingTime']].astype(float)
                funding_df.loc[:, 'fundingTime'] = funding_df['fundingTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
                funding_df.loc[:, 'nextFundingTime'] = funding_df['nextFundingTime'].apply(lambda x: datetime.datetime.fromtimestamp(x/1000))
                funding_df = funding_df.rename(columns={'fundingRate':'fundingrate', 'fundingTime':'fundingtime', 'nextFundingTime':'nextfundingtime', 'nextFundingRate':"nextfundingrate", 'instId':'okx_symbol'})
                funding_df['exchange'] = 'okx'
                funding_df['rec'] = funding_df['okx_symbol'] + funding_df['fundingtime'].astype(str) + funding_df['exchange']

                # Compare old and new data
                for row_tup in funding_df.iterrows():
                    row = row_tup[1]
                    if row['rec'] not in old_fund_df['rec'].to_list():
                        # INSERT INTO funding_info
                        db_client.curr.execute("""INSERT INTO funding_info (symbol, okx_symbol, fundingrate, fundingtime, nextfundingrate, nextfundingtime, exchange, last_updated_time, rec) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)"""
                                               , (row['okx_symbol'].replace('-USDT-SWAP',''), row['okx_symbol'], row['fundingrate'], row['fundingtime'].to_pydatetime(), row['nextfundingrate'], row['nextfundingtime'].to_pydatetime(), row['exchange'], row['last_updated_time'].to_pydatetime(), row['rec']))
                    else:
                        # UPDATE funding_info
                        db_client.curr.execute("""UPDATE funding_info SET fundingrate = %s, fundingtime = %s, nextfundingrate = %s, nextfundingtime = %s, last_updated_time = %s WHERE rec = %s""" 
                                               , (row['fundingrate'], row['fundingtime'].to_pydatetime(), row['nextfundingrate'], row['nextfundingtime'].to_pydatetime(), row['last_updated_time'].to_pydatetime(), row['rec']))
                    db_client.conn.commit()
                db_client.conn.close()
                time.sleep(loop_time)
        except Exception:
            self.common_info_logger.error(f"update_funding_info|{traceback.format_exc()}")
            self.register_monitor_msg.register(self.admin_id, self.node, 'error', "update_funding_info", f"{traceback.format_exc()}")
            raise Exception(f"update_funding_info|{traceback.format_exc()}")

    def start_monitor_funding_info(self, monitor_loop_secs=2.5):
        self.common_info_logger.info(f"start_monitor_funding_info|start_monitor_funding_info started.")
        def funding_monitor_func():
            self.update_fundinginfo_proc = Process(target=self.update_funding_info, daemon=True)
            self.update_fundinginfo_proc.start()
            while True:
                time.sleep(monitor_loop_secs)
                if not self.update_fundinginfo_proc.is_alive():
                    self.common_info_logger.error(f"start_monitor_funding_info|update_fundinginfo_proc stopped! Restarting the process..")
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_funding_info", "update_fundinginfo_proc stopped! Restarting the process..")
                    self.update_fundinginfo_proc = Process(target=self.update_funding_info, daemon=True)
                    self.update_fundinginfo_proc.start()
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', "start_monitor_funding_info", f"update_fundinginfo_proc.is_alive: {self.update_fundinginfo_proc.is_alive()}")
        funding_monitor_func_thread = Thread(target=funding_monitor_func, daemon=True)
        funding_monitor_func_thread.start()