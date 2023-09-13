import os
import json
import sys
import argparse
import datetime
import pandas as pd
import numpy as np
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
    def __init__(self, node, get_premium_df, get_market_code_list, register_monitor_msg, logging_dir):
        self.node = node
        self.get_premium_df = get_premium_df
        self.register_monitor_msg = register_monitor_msg
        self.kline_logger = KimpBotLogger("kline_core", logging_dir).logger
        self.kline_logger.info(f"InitKlineCore started.")
        self.redis_client = InitRedis()
        self.market_code_list = get_market_code_list()
        self._start_generating_kline()

    def _start_generating_kline(self):
        # Start generating kline
        # TEST
        self.test_process = Process(target=self.ohlc_1T_loader, args=("BINANCE_USD_M/USDT", "UPBIT_SPOT/KRW"), daemon=True)
        self.test_process.start()

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

    def ohlc_1T_loader(self, origin_exchange_code, target_exchange_code, loop_downtime_sec=0.01, max_length=300):
        appended_premium_df = pd.DataFrame()
        kline_switch = False
        while True:
            time.sleep(loop_downtime_sec)
            premium_df = self.get_premium_df(origin_exchange_code, target_exchange_code)
            datetime_now = datetime.datetime.now()
            premium_df['datetime_now'] = datetime_now
            appended_premium_df = pd.concat([appended_premium_df, premium_df], axis=0)
            appended_premium_df.loc[: ,'datetime_now'] = pd.to_datetime(appended_premium_df['datetime_now'])
            # print(f"redis saving ohlc_1T_now time: {time.time()-start}")
            if datetime_now.second == 0 and kline_switch == True:
                adjusted_datetime_now = datetime.datetime(datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute)
                cut_appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] < adjusted_datetime_now]
                # start = time.time()
                ohlc_df = self.generate_ohlc_df(cut_appended_premium_df)
                # print(f"generating ohlc_df(length: {len(cut_appended_premium_df)}): {time.time()-start}")
                # Save into redis db for current data
                # start = time.time()
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_1T_now', pickle.dumps(ohlc_df))
                # print(f"redis saving ohlc_1T_now time: {time.time()-start}")
                # Append into redis db for historical data
                # start = time.time()
                old_ohlc_1T_kline = self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_1T_kline')
                if old_ohlc_1T_kline is None:
                    old_ohlc_1T_kline = pd.DataFrame()
                else:
                    old_ohlc_1T_kline = pickle.loads(old_ohlc_1T_kline)
                new_ohlc_1T_kline = pd.concat([old_ohlc_1T_kline, ohlc_df], axis=0).tail(max_length*ohlc_df['base_asset'].nunique())
                new_ohlc_1T_kline['closed'] = True
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_1T_kline', pickle.dumps(new_ohlc_1T_kline))
                # print(f"redis ohlc_1T_kline load and saving time after appending: {time.time()-start}")
                appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] >= adjusted_datetime_now]
                kline_switch = False
            elif datetime_now.second != 0:
                # Save into redis db for current data
                ohlc_df = self.generate_ohlc_df(appended_premium_df)
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_1T_now', pickle.dumps(ohlc_df))
                kline_switch = True
            else:
                # Save into redis db for current data
                ohlc_df = self.generate_ohlc_df(appended_premium_df)
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_1T_now', pickle.dumps(ohlc_df))

    def resample_ohlc_df(self, ohlc_df, resample_period, closed_count):
        ohlc_df['count'] = 1
        ohlc_df = ohlc_df.set_index(['base_asset','datetime_now'])
        resampled_df = ohlc_df.groupby('base_asset').resample(resample_period, level='datetime_now').agg({
            'tp_open': 'first',
            'tp_high': 'max',
            'tp_low': 'min',
            'tp_close': 'last',
            'LS_open': 'first',
            'LS_high': 'max',
            'LS_low': 'min',
            'LS_close': 'last',
            'SL_open': 'first',
            'SL_high': 'max',
            'SL_low': 'min',
            'SL_close': 'last',
            'count': 'sum'
        })
        resampled_df = resampled_df.reset_index()
        resampled_df['closed'] = resampled_df['count'].apply(lambda x: True if x==closed_count else False)
        return resampled_df
    
    def ohlc_min_resample_loader(self, origin_exchange_code, target_exchange_code, original_period, resample_period, resample_closed_count, loop_downtime_sec=0.1, max_length=300):
        start = time.time()
        resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
        self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_{resample_period}_kline', pickle.dumps(resampled_ohlc_history_df))
        print(f"initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

        while True:
            time.sleep(loop_downtime_sec)
            original_ohlc_1T_now = pickle.loads(self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_1T_now'))
            try:
                original_ohlc_history_last_datetime = pickle.loads(self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_{original_period}_kline')).iloc[-1]['datetime_now']
            except TypeError:
                print(f"original_ohlc_history_last_datetime is None")
                continue
            resampled_ohlc_history_df = pickle.loads(self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_{resample_period}_kline'))
            resampled_ohlc_history_df = resampled_ohlc_history_df[resampled_ohlc_history_df['closed']==True]
            resampled_ohlc_history_last_datetime = resampled_ohlc_history_df.iloc[-1]['datetime_now']
            datetime_now = datetime.datetime.now()
            # print(f"(original_ohlc_history_last_datetime.minute + int(original_period[:-1])) % int(resample_period[:-1]): {(original_ohlc_history_last_datetime.minute + int(original_period[:-1])) % int(resample_period[:-1])}")
            # print(f"datetime_now - resampled_ohlc_history_last_datetime > datetime.timedelta(minutes=int(resample_period[:-1])*2): {datetime_now - resampled_ohlc_history_last_datetime > datetime.timedelta(minutes=int(resample_period[:-1])*2)}")
            # print(f"datetime_now: {datetime_now}")
            # print(f"resampled_ohlc_history_last_datetime: {resampled_ohlc_history_last_datetime}")
            # print(f"(datetime_now - resampled_ohlc_history_last_datetime): {datetime_now - resampled_ohlc_history_last_datetime}")
            if ((original_ohlc_history_last_datetime.minute + int(original_period[:-1])) % int(resample_period[:-1]) == 0 and
                (datetime_now - resampled_ohlc_history_last_datetime) > datetime.timedelta(minutes=int(resample_period[:-1])*2)):
                # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                start = time.time()
                resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, self.resample_ohlc_df(pickle.loads(self.redis_client.get_data(f'{origin_exchange_code}:{target_exchange_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)], axis=0, ignore_index=True)
                resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                # print(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                self.kline_logger.info(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                # Save into the Redis DB
                # start = time.time()
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_{resample_period}_kline', pickle.dumps(resampled_ohlc_history_df))
                # print(f"redis saving {origin_exchange_code}:{target_exchange_code}_{resample_period}_kline time: {time.time()-start}")
            else:
                # generate resampled_ohlc_now_df
                resampled_ohlc_last_df = resampled_ohlc_history_df.groupby('base_asset').tail(1).reset_index(drop=True).copy()
                # Compare it to thr original_ohlc_1T_now
                resampled_ohlc_last_df.loc[:, 'tp_high'] = np.where(resampled_ohlc_last_df['tp_high']>original_ohlc_1T_now['tp_high'], resampled_ohlc_last_df['tp_high'], original_ohlc_1T_now['tp_high'])
                resampled_ohlc_last_df.loc[:, 'tp_low'] = np.where(resampled_ohlc_last_df['tp_low']<original_ohlc_1T_now['tp_low'], resampled_ohlc_last_df['tp_low'], original_ohlc_1T_now['tp_low'])
                resampled_ohlc_last_df.loc[:, 'tp_close'] = original_ohlc_1T_now['tp_close']
                resampled_ohlc_last_df.loc[:, 'LS_high'] = np.where(resampled_ohlc_last_df['LS_high']>original_ohlc_1T_now['LS_high'], resampled_ohlc_last_df['LS_high'], original_ohlc_1T_now['LS_high'])
                resampled_ohlc_last_df.loc[:, 'LS_low'] = np.where(resampled_ohlc_last_df['LS_low']<original_ohlc_1T_now['LS_low'], resampled_ohlc_last_df['LS_low'], original_ohlc_1T_now['LS_low'])
                resampled_ohlc_last_df.loc[:, 'LS_close'] = original_ohlc_1T_now['LS_close']
                resampled_ohlc_last_df.loc[:, 'SL_high'] = np.where(resampled_ohlc_last_df['SL_high']>original_ohlc_1T_now['SL_high'], resampled_ohlc_last_df['SL_high'], original_ohlc_1T_now['SL_high'])
                resampled_ohlc_last_df.loc[:, 'SL_low'] = np.where(resampled_ohlc_last_df['SL_low']<original_ohlc_1T_now['SL_low'], resampled_ohlc_last_df['SL_low'], original_ohlc_1T_now['SL_low'])
                resampled_ohlc_last_df.loc[:, 'SL_close'] = original_ohlc_1T_now['SL_close']
                resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(minutes=int(resample_period[:-1]))
                # Save into the Redis DB
                self.redis_client.set_data(f'{origin_exchange_code}:{target_exchange_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
