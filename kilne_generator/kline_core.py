import os
import json
import sys
import argparse
import datetime
import pandas as pd
import _pickle as pickle
import time
import datetime
from multiprocessing import Process

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
from etc.register_monitor_msg import RegisterMonitorMsg
# from etc.db_handler.create_schema_tables import InitDBClient
from etc.redis_connector.redis_connector import InitRedis


class InitKlineCore:
    def __init__(self, node, core, register_monitor_msg, logging_dir):
        self.node = node
        self.core = core
        self.register_monitor_msg = register_monitor_msg
        self.kline_logger = KimpBotLogger("kline_core", logging_dir).logger
        self.kline_logger.info(f"InitKlineCore started.")
        self.redis_client = InitRedis()

    def generate_ohlc_df(self, df, freq='1T'):
        df = df.set_index(['base_asset', 'datetime_now'])
        ohlc_df = pd.DataFrame()
        if 'tp_premium' in df.columns:
            df['tp_premium'] = pd.to_numeric(df['tp_premium'], errors='coerce')
            tp_ohlc_df = df.groupby(['base_asset', pd.Grouper(level='datetime_now', freq=freq)])['tp_premium'].ohlc()
            # add prefix of tp_ to the column names
            tp_ohlc_df.columns = ['tp_' + col for col in tp_ohlc_df.columns]
            ohlc_df = pd.concat([ohlc_df, tp_ohlc_df], axis=1)
        if 'LS_premium' in df.columns:
            df['LS_premium'] = pd.to_numeric(df['LS_premium'], errors='coerce')
            LS_ohlc_df = df.groupby(['base_asset', pd.Grouper(level='datetime_now', freq=freq)])['LS_premium'].ohlc()
            # add prefix of LS_ to the column names
            LS_ohlc_df.columns = ['LS_' + col for col in LS_ohlc_df.columns]
            ohlc_df = pd.concat([ohlc_df, LS_ohlc_df], axis=1)
        if 'SL_premium' in df.columns:
            df['SL_premium'] = pd.to_numeric(df['SL_premium'], errors='coerce')
            SL_ohlc_df = df.groupby(['base_asset', pd.Grouper(level='datetime_now', freq=freq)])['SL_premium'].ohlc()
            # add prefix of SL_ to the column names
            SL_ohlc_df.columns = ['SL_' + col for col in SL_ohlc_df.columns]
            ohlc_df = pd.concat([ohlc_df, SL_ohlc_df], axis=1)
        if 'tp_premium' not in df.columns and 'LS_premium' not in df.columns and 'SL_premium' not in df.columns:
            raise ValueError('There is no proper column in the dataframe')
        ohlc_df.reset_index(inplace=True)
        return ohlc_df

    def ohlc_1m_loader(self, origin_exchange_code, target_exchange_code, redis_cli, loop_downtime_sec=0.01, max_length=300):
        appended_premium_df = pd.DataFrame()
        kline_switch = False
        while True:
            time.sleep(loop_downtime_sec)
            premium_df = self.core.get_premium_df(origin_exchange_code, target_exchange_code)
            datetime_now = datetime.datetime.now()
            premium_df['datetime_now'] = datetime_now
            appended_premium_df = pd.concat([appended_premium_df, premium_df], axis=0)
            appended_premium_df.loc[: ,'datetime_now'] = pd.to_datetime(appended_premium_df['datetime_now'])
            # print(f"redis saving ohlc_1m_now time: {time.time()-start}")
            if datetime_now.second == 0 and kline_switch == True:
                adjusted_datetime_now = datetime.datetime(datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute)
                cut_appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] < adjusted_datetime_now]
                # start = time.time()
                ohlc_df = self.generate_ohlc_df(cut_appended_premium_df)
                # print(f"generating ohlc_df(length: {len(cut_appended_premium_df)}): {time.time()-start}")
                # INSERT into redis db for current data
                # start = time.time()
                redis_cli.set_data('ohlc_1m_now', pickle.dumps(ohlc_df))
                # print(f"redis saving ohlc_1m_now time: {time.time()-start}")
                # Append into redis db for historical data
                # start = time.time()
                old_ohlc_1m_kline = redis_cli.get_data('ohlc_1m_kline')
                if old_ohlc_1m_kline is None:
                    old_ohlc_1m_kline = pd.DataFrame()
                else:
                    old_ohlc_1m_kline = pickle.loads(old_ohlc_1m_kline)
                new_ohlc_1m_kline = pd.concat([old_ohlc_1m_kline, ohlc_df], axis=0).tail(max_length)
                new_ohlc_1m_kline['closed'] = True
                redis_cli.set_data('ohlc_1m_kline', pickle.dumps(new_ohlc_1m_kline))
                # print(f"redis ohlc_1m_kline load and saving time after appending: {time.time()-start}")
                appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] >= adjusted_datetime_now]
                kline_switch = False
            elif datetime_now.second != 0:
                # INSERT into redis db for current data
                ohlc_df = self.generate_ohlc_df(appended_premium_df)
                redis_cli.set_data('ohlc_1m_now', pickle.dumps(ohlc_df))
                kline_switch = True
            else:
                # INSERT into redis db for current data
                ohlc_df = self.generate_ohlc_df(appended_premium_df)
                redis_cli.set_data('ohlc_1m_now', pickle.dumps(ohlc_df))
