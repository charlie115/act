import os
import json
import sys
import argparse
import traceback
import datetime
import pandas as pd
import numpy as np
import _pickle as pickle
import time
import datetime
from multiprocessing import Process
from threading import Thread

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger
# from etc.db_handler.create_schema_tables import InitDBClient
from etc.redis_connector.redis_connector import InitRedis


class InitKlineCore:
    def __init__(self, admin_id, node, get_premium_df, enabled_market_klines, register_monitor_msg, redis_client, db_client, logging_dir):
        self.node = node
        self.admin_id = admin_id
        self.get_premium_df = get_premium_df
        self.register_monitor_msg = register_monitor_msg
        self.kline_logger = KimpBotLogger("kline_core", logging_dir).logger
        self.kline_logger.info(f"InitKlineCore started.")
        self.redis_client_db0 = InitRedis()
        self.local_redis_client = InitRedis(host='localhost', port=6379, db=0, passwd=None)
        # self.market_code_list = get_market_code_list()
        # self.market_combination_list = self.get_market_combination_list()
        self.enabled_market_klines = enabled_market_klines
        self.enabled_kline_types = ['1T', '5T', '15T', '30T', '1H', '4H']
        self.kline_proc_dict = {}
        self.pubsub = self.redis_client_db0.redis_conn.pubsub()
        self.db_client = db_client
        # self.enaled_market_combination_list = []
        self._start_generating_kline()
        # self.subscribe_kline_channel()
        subscribe_kline_channel_proc = Process(target=self.subscribe_kline_channel, daemon=True)
        subscribe_kline_channel_proc.start()

    def _start_generating_kline(self):
        # Start generating kline
        for market_combination in self.enabled_market_klines:
            target_market_code = market_combination.split(':')[0]
            origin_market_code = market_combination.split(':')[1]
            for i, each_kline_type in enumerate(self.enabled_kline_types):
                if each_kline_type.endswith('T'):
                    if each_kline_type == '1T':
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"] = Process(target=self.ohlc_1T_loader, args=(self.get_premium_df, target_market_code, origin_market_code), daemon=True)
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"].start()
                    else:
                        count = int(each_kline_type[:-1]) / int(self.enabled_kline_types[i-1][:-1])
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(target=self.ohlc_min_resample_loader, args=(target_market_code, origin_market_code, self.enabled_kline_types[i-1], each_kline_type, count), daemon=True)
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                elif each_kline_type.endswith('H'):
                    if each_kline_type == '1H':
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(target=self.ohlc_hour_resample_loader, args=(target_market_code, origin_market_code, "30T", "1H", 2), daemon=True)
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                    else:
                        count = int(each_kline_type[:-1]) / int(self.enabled_kline_types[i-1][:-1])
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(target=self.ohlc_hour_resample_loader, args=(target_market_code, origin_market_code, self.enabled_kline_types[i-1], each_kline_type, count), daemon=True)
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                elif each_kline_type.endswith('D'):
                    if each_kline_type == "1D":
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(target=self.ohlc_day_resample_loader, args=(target_market_code, origin_market_code, "4H", "1D", 6), daemon=True)
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                    else:
                        pass
                else:
                    raise ValueError(f"Invalid kline_type: {each_kline_type}")
                time.sleep(1)

    # def get_market_combination_list(self):
    #     market_combination_list = []
    #     for market_one in self.market_code_list:
    #         for market_two in self.market_code_list:
    #             if market_one != market_two:
    #                 market_combination_list.append((market_one, market_two))
    #     return market_combination_list

    def generate_ohlc_df(self, appended_df, freq='1T'):
        df = appended_df.set_index(['base_asset', 'datetime_now'])
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
        # TEST
        ohlc_df['dollar'] = df['dollar'].iloc[-1]
        ohlc_df.reset_index(inplace=True)
        # TEST
        try:
            ohlc_df['record_count'] = appended_df.groupby('base_asset')['base_asset'].count().values
        except Exception as e:
            content = f"Error in generate_ohlc_df: {traceback.format_exc()}\n ohlc_df:{ohlc_df}, appended_df.groupby('base_asset'):{appended_df.groupby('base_asset')}\n appended_df:{appended_df}"
            self.kline_logger.error(content)
        return ohlc_df

    def ohlc_1T_loader(self, get_premium_df, target_market_code, origin_market_code, loop_downtime_sec=0.02, max_length=300):
        columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
        appended_premium_df = pd.DataFrame()
        datetime_now = datetime.datetime.utcnow()
        while True:
            time.sleep(loop_downtime_sec)
            try:
                datetime_before = datetime_now
                # premium_df = self.get_premium_df(target_market_code, origin_market_code)
                premium_df = get_premium_df(target_market_code, origin_market_code)
                datetime_now = datetime.datetime.utcnow()
                premium_df['datetime_now'] = datetime_now
                appended_premium_df = pd.concat([appended_premium_df, premium_df], axis=0)
                appended_premium_df.loc[: ,'datetime_now'] = pd.to_datetime(appended_premium_df['datetime_now'])
                # print(f"redis saving ohlc_1T_now time: {time.time()-start}")
                if datetime_before.minute != datetime_now.minute:
                    adjusted_datetime_now = datetime.datetime(datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute)
                    cut_appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] < adjusted_datetime_now]
                    ohlc_df = self.generate_ohlc_df(cut_appended_premium_df)
                    ohlc_df = ohlc_df.merge(premium_df[columns_to_merge], on=['base_asset'], how='inner')
                    pickled_ohlc_df = pickle.dumps(ohlc_df)
                    # Save into redis db for current data
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                    # Publish to redis pubsub
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                    # Append into redis db for historical data
                    old_ohlc_1T_kline = self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline')
                    if old_ohlc_1T_kline is None:
                        old_ohlc_1T_kline = pd.DataFrame()
                    else:
                        old_ohlc_1T_kline = pickle.loads(old_ohlc_1T_kline)
                        old_ohlc_1T_kline = old_ohlc_1T_kline[old_ohlc_1T_kline['base_asset'].isin(ohlc_df['base_asset'].unique())]
                    new_ohlc_1T_kline = pd.concat([old_ohlc_1T_kline, ohlc_df], axis=0).tail(max_length*ohlc_df['base_asset'].nunique())
                    new_ohlc_1T_kline['closed'] = True
                    pickled_ohlc_df = pickle.dumps(new_ohlc_1T_kline)
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline', pickled_ohlc_df)
                    # Publish to redis pubsub
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline', pickled_ohlc_df)
                    appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] >= adjusted_datetime_now]
                else:
                    # Save into redis db for current data
                    ohlc_df = self.generate_ohlc_df(appended_premium_df)
                    ohlc_df = ohlc_df.merge(premium_df[columns_to_merge], on=['base_asset'], how='inner')
                    pickled_ohlc_df = pickle.dumps(ohlc_df)
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                    # Publish to redis pubsub
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
            except Exception as e:
                content = f"ohlc_1T_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_1T_loader: {traceback.format_exc()}\n appended_premium_df:{appended_premium_df}, premium_df:{premium_df}"
                self.kline_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"ohlc_1T_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)
                time.sleep(3)

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
            'dollar': 'last',
            'count': 'sum'
        })
        resampled_df = resampled_df.reset_index()
        resampled_df['closed'] = resampled_df['count'].apply(lambda x: True if x==closed_count else False)
        return resampled_df

    def ohlc_day_resample_loader(self, target_market_code, origin_market_code, original_period, resample_period, resample_closed_count, loop_downtime_sec=0.1, max_length=300):
        columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
        while True:
            original_ohlc_kline_df = self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
            if original_ohlc_kline_df is not None:
                break
            time.sleep(5)

        start = time.time()
        original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
        resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
        resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
        self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        # Publish to redis pubsub
        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        self.kline_logger.info(f"ohlc_day_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

        datetime_now = datetime.datetime.utcnow()        
        while True:
            time.sleep(loop_downtime_sec)
            try:
                datetime_before = datetime_now
                original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
                try:
                    original_ohlc_history_last_datetime = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
                except TypeError:
                    print(f"original_ohlc_history_last_datetime is None")
                    continue
                resampled_ohlc_history_df = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
                datetime_now = datetime.datetime.utcnow()
                if ((datetime_before.hour // int(resample_period[:-1]) != datetime_now.hour // int(resample_period[:-1])) or
                    sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                    # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                    start = time.time()
                    new_resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                    new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                    resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                    resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                    print(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                    # Save into the Redis DB
                    # start = time.time()
                    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    # Publish to redis pubsub
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    # self.kline_logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                    if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                        removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                        added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                        self.kline_logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                        if len(removed_list) != 0:
                            # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                            resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                            pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                            self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                            self.kline_logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
                        time.sleep(5)
                else:
                    # generate resampled_ohlc_now_df
                    resampled_ohlc_last_df = resampled_ohlc_history_df.groupby('base_asset').tail(1).reset_index(drop=True).copy()
                    try:
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
                        resampled_ohlc_last_df[columns_to_merge] = original_ohlc_1T_now[columns_to_merge]
                        resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(hours=int(resample_period[:-1]))
                        # # Save into the Redis DB
                        # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                        # PUBSUB
                        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    except Exception as e:
                        self.kline_logger.error(f"Exception: {e}, \nError in ohlc_day_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                        time.sleep(3)
            except Exception as e:
                content = f"ohlc_day_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_day_resample_loader: {traceback.format_exc()}"
                self.kline_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"ohlc_day_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)

    def ohlc_hour_resample_loader(self, target_market_code, origin_market_code, original_period, resample_period, resample_closed_count, loop_downtime_sec=0.1, max_length=300):
        columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
        while True:
            original_ohlc_kline_df = self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
            if original_ohlc_kline_df is not None:
                break
            time.sleep(5)

        start = time.time()
        original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
        resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
        resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
        self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        # Publish to redis pubsub
        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        self.kline_logger.info(f"ohlc_hour_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

        datetime_now = datetime.datetime.utcnow()
        while True:
            time.sleep(loop_downtime_sec)
            try:
                datetime_before = datetime_now
                original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
                try:
                    original_ohlc_history_last_datetime = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
                except TypeError:
                    print(f"original_ohlc_history_last_datetime is None")
                    continue
                resampled_ohlc_history_df = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
                datetime_now = datetime.datetime.utcnow()
                if ((datetime_before.hour // int(resample_period[:-1]) != datetime_now.hour // int(resample_period[:-1])) or
                    sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                    # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                    start = time.time()
                    new_resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                    new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                    resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                    resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                    print(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                    # Save into the Redis DB
                    # start = time.time()
                    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    # Publish to redis pubsub
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    # self.kline_logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                    if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                        removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                        added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                        self.kline_logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                        if len(removed_list) != 0:
                            # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                            resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                            pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                            self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                            self.kline_logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
                        time.sleep(5)
                else:
                    # generate resampled_ohlc_now_df
                    resampled_ohlc_last_df = resampled_ohlc_history_df.groupby('base_asset').tail(1).reset_index(drop=True).copy()
                    try:
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
                        resampled_ohlc_last_df[columns_to_merge] = original_ohlc_1T_now[columns_to_merge]
                        resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(hours=int(resample_period[:-1]))
                        # # Save into the Redis DB
                        # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                        # PUBSUB
                        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    except Exception as e:
                        self.kline_logger.error(f"Exception: {e}, \nError in ohlc_hour_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                        time.sleep(3)
            except Exception as e:
                content = f"ohlc_hour_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_hour_resample_loader: {traceback.format_exc()}"
                self.kline_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"ohlc_hour_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)

    def ohlc_min_resample_loader(self, target_market_code, origin_market_code, original_period, resample_period, resample_closed_count, loop_downtime_sec=0.1, max_length=300):
        columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']

        while True:
            original_ohlc_kline_df = self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
            if original_ohlc_kline_df is not None:
                break
            time.sleep(5)

        start = time.time()
        original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
        resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
        resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
        self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        # Publish to redis pubsub
        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
        self.kline_logger.info(f"ohlc_min_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

        datetime_now = datetime.datetime.utcnow()
        while True:
            time.sleep(loop_downtime_sec)
            try:
                datetime_before = datetime_now
                original_ohlc_1T_now = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
                try:
                    original_ohlc_history_last_datetime = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
                except TypeError:
                    print(f"original_ohlc_history_last_datetime is None")
                    continue
                resampled_ohlc_history_df = pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
                datetime_now = datetime.datetime.utcnow()
                if ((datetime_before.minute // int(resample_period[:-1]) != datetime_now.minute // int(resample_period[:-1])) or
                    sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                    # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                    start = time.time()
                    new_resampled_ohlc_history_df = self.resample_ohlc_df(pickle.loads(self.local_redis_client.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                    new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                    resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                    resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                    self.kline_logger.info(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                    # Save into the Redis DB
                    start = time.time()
                    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                    self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    self.kline_logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                    # Publish to redis pubsub
                    start = time.time() # TEST
                    self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                    self.kline_logger.info(f"redis publishing {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}") # TEST
                    if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                        removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                        added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                        self.kline_logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                        if len(removed_list) != 0:
                            # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                            resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                            pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                            self.local_redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                            self.kline_logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
                        time.sleep(5)
                else:
                    # generate resampled_ohlc_now_df
                    resampled_ohlc_last_df = resampled_ohlc_history_df.groupby('base_asset').tail(1).reset_index(drop=True).copy()
                    try:
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
                        resampled_ohlc_last_df[columns_to_merge] = original_ohlc_1T_now[columns_to_merge]
                        resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(minutes=int(resample_period[:-1]))
                        # # Save into the Redis DB
                        # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{converted_resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                        # PUBSUB
                        self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    except Exception as e:
                        self.kline_logger.error(f"Exception: {e}, \nError in ohlc_min_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                        time.sleep(3)
            except Exception as e:
                content = f"ohlc_min_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_min_resample_loader: {traceback.format_exc()}"
                self.kline_logger.error(content)
                self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"ohlc_min_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)

    def insert_kline_to_db(self, kline_df, channel_name):
        try:
            service_name = channel_name.split('|')[0].lower()
            market_kline_name = channel_name.split('|')[1]
            market_code_combination = '_'.join(market_kline_name.split('_')[:-2])
            converted_market_code_combination = market_code_combination.replace(':', '-').replace('/', '__')
            kline_type = market_kline_name.split('_')[-2]
            
            mongo_client = self.db_client.get_conn()
            db = mongo_client[converted_market_code_combination]

            closed_kline_df = kline_df[kline_df['closed']==True]
            if len(closed_kline_df) == 0:
                self.kline_logger.info(f'insert_kline_to_db|{channel_name} No klines to be inserted')
                # print(f'insert_kline_to_db|{channel_name} No klines to be inserted') # TEST
            else:
                # Filter the klines to be inserted
                start = time.time()
                base_asset_list = closed_kline_df['base_asset'].unique()
                count = 0
                inserted_coin_list = []
                filtering_time = 0 # TEST
                insert_time = 0 # TEST
                for each_base_asset in base_asset_list:
                    # start2 = time.time()
                    collection_name = f"{each_base_asset}_{kline_type}"
                    collection = db[collection_name]
                    document_count = collection.count_documents({})
                    if document_count == 0:
                        df_to_insert = closed_kline_df[closed_kline_df['base_asset']==each_base_asset]
                    else:
                        # TEST
                        start_filter = time.time()
                        df_to_insert = closed_kline_df[(closed_kline_df['base_asset']==each_base_asset)&(closed_kline_df['datetime_now']>collection.find_one(sort=[("datetime_now", -1)])['datetime_now'])]
                        # TEST
                        filtering_time += (time.time() - start_filter)
                    if len(df_to_insert) != 0:
                        # TEST
                        start_insert = time.time()       
                        collection.insert_many(df_to_insert.to_dict('records'))
                        # TEST
                        insert_time += (time.time() - start_insert)
                        count += len(df_to_insert)
                        inserted_coin_list.append(each_base_asset)
                        # self.kline_logger.info(f"insert_kline_to_db|database: {market_code_combination}, collection:{collection_name}, Inserting {len(df_to_insert)} klines took {time.time() - start2} seconds")
                if count != 0:
                    # TEST
                    self.kline_logger.info(f"insert_kline_to_db|database: {market_code_combination}, Filtering {count} klines for {len(inserted_coin_list)} unique base_assets took {filtering_time} seconds")
                    self.kline_logger.info(f"insert_kline_to_db|database: {market_code_combination}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {insert_time} seconds")
                    # TEST
                    self.kline_logger.info(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds")
                # print(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds") # TEST
            mongo_client.close()
        except:
            try:
                mongo_client.close()
            except:
                pass
            self.kline_logger.error(f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}")
            self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"insert_kline_to_db", content=f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}", code=None, sent_switch=0, send_counts=1, remark=None)

    def subscribe_kline_channel(self):
        self.kline_logger.info(f"subscribe_kline_channel|Subscribing to kline channels Started..")
        def message_handler(message):
            try:
                data = message['data']
                if data != 1:
                    kline_df = pickle.loads(data)
                    self.insert_kline_to_db(kline_df, message['channel'].decode('utf-8'))
            except Exception as e:
                self.kline_logger.error(f"subscribe_kline_channel|Error in message_handler: {traceback.format_exc()}")

        channels_dict = {}
        for market_combination in self.enabled_market_klines:
            for each_kline_type in self.enabled_kline_types:
                channel_name = f'INFO_CORE|{market_combination}_{each_kline_type}_kline'
                channels_dict[channel_name] = message_handler
                self.kline_logger.info(f"subscribe_kline_channel|Subscribing to {channel_name}")

        def keep_alive_check():
            while True:
                try:
                    self.pubsub.ping()  # Try to ping the Redis server
                    time.sleep(15)  # Check every 30 seconds
                except:  # If ping fails, we can assume the connection has dropped
                    content = f"subscribe_kline_channel|Connection lost. Attempting to reconnect..., error:{traceback.format_exc()}"
                    self.kline_logger.error(content)
                    self.register_monitor_msg.register(self.admin_id, self.node, 'error', f"subscribe_kline_channel", content, code=None, sent_switch=0, send_counts=1, remark=None)
                    subscribe_to_channels()

        def subscribe_to_channels():
            while True:
                try:
                    self.pubsub.subscribe(**channels_dict)
                    self.pubsub.run_in_thread(sleep_time=0.05, daemon=True)
                    break
                except Exception as e:
                    self.kline_logger.error(f"subscribe_kline_channel|Error in subscription: {traceback.format_exc()}")
                    time.sleep(5)

        subscribe_to_channels()
        # # Start the keep_alive_check in another thread
        # Thread(target=keep_alive_check, daemon=True).start()
        keep_alive_check()

    def unsubscribe_kline_channel(self):
        self.pubsub.unsubscribe() 

        

