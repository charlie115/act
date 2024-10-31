import traceback
import pandas as pd
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from etc.db_handler.mongodb_client import InitDBClient
import pickle
import datetime
from threading import Thread
import time
import numpy as np
import re
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.premium_data_generator import get_premium_df

def insert_kline_to_db(kline_df, channel_name, register_monitor_msg, redis_dict, mongodb_dict, admin_id, node, logger):
    remote_redis = RedisHelper(**redis_dict)
    try:
        service_name = channel_name.split('|')[0].lower()
        market_kline_name = channel_name.split('|')[1]
        market_code_combination = '_'.join(market_kline_name.split('_')[:-2])
        converted_market_code_combination = market_code_combination.replace(':', '-').replace('/', '__')
        kline_type = market_kline_name.split('_')[-2]

        # Check whether the market is in maintenance or not
        server_check = False
        registered_server_check_list = [x.decode('utf-8') for x in remote_redis.get_all_keys() if 'INFO_CORE|SERVER_CHECK' in x.decode('utf-8')]
        for each_market_server_check in registered_server_check_list:
            market_name = each_market_server_check.replace('INFO_CORE|SERVER_CHECK|', '')
            if market_name in market_code_combination:
                server_check_dict = remote_redis.get_dict(each_market_server_check)
                server_check_start_timestamp_utc = server_check_dict['start']
                server_check_end_timestamp_utc = server_check_dict['end']
                now_timestamp_utc = datetime.datetime.utcnow().timestamp()
                if server_check_start_timestamp_utc <= now_timestamp_utc <= server_check_end_timestamp_utc:
                    server_check = True
                    break
        if server_check is True:
            logger.info(f"insert_kline_to_db|channel_name:{channel_name}, kline_type:{kline_type} has been skipped due to server check.")
            return

        mongodb_client = InitDBClient(**mongodb_dict)
        mongodb_conn = mongodb_client.get_conn()
        db = mongodb_conn[converted_market_code_combination]

        closed_kline_df = kline_df[kline_df['closed']==True]
        if len(closed_kline_df) == 0:
            logger.info(f'insert_kline_to_db|{channel_name} No klines to be inserted')
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
                logger.info(f"insert_kline_to_db|database: {market_code_combination}, Filtering {count} klines for {len(inserted_coin_list)} unique base_assets took {filtering_time} seconds")
                logger.info(f"insert_kline_to_db|database: {market_code_combination}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {insert_time} seconds")
                # TEST
                logger.info(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds")
            # print(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds") # TEST
        # mongo_client.close()
    except:
        logger.error(f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}")
        register_monitor_msg.register(admin_id, node, 'error', f"insert_kline_to_db", content=f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}", code=None, sent_switch=0, send_counts=1, remark=None)

def generate_ohlc_df(appended_df, logger, freq='1T'):
    freq = freq.replace('T', 'min').replace('H', 'h')
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
        logger.error(content)
    return ohlc_df
    
def resample_ohlc_df(ohlc_df, resample_period, closed_count):
    resample_period = resample_period.replace('T', 'min').replace('H', 'h')
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
    
def ohlc_1T_loader(
    info_dict,
    convert_rate_dict,
    generate_ohlc_df,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    register_monitor_msg,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.02,
    max_length=300
    ):
    logger = InfoCoreLogger("kline_core", logging_dir).logger
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
    appended_premium_df = pd.DataFrame()
    datetime_now = datetime.datetime.utcnow()
    # Set stream maxlen
    remote_redis.get_redis_client().xtrim(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', maxlen=max_length)
    while True:
        time.sleep(loop_downtime_sec)
        try:
            datetime_before = datetime_now
            premium_df = get_premium_df(info_dict, convert_rate_dict, target_market_code, origin_market_code, logging_dir=logging_dir)
            datetime_now = datetime.datetime.utcnow()
            premium_df['datetime_now'] = datetime_now
            appended_premium_df = pd.concat([appended_premium_df, premium_df], axis=0)
            appended_premium_df.loc[: ,'datetime_now'] = pd.to_datetime(appended_premium_df['datetime_now'])
            # print(f"redis saving ohlc_1T_now time: {time.time()-start}")
            if datetime_before.minute != datetime_now.minute:
                adjusted_datetime_now = datetime.datetime(datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute)
                cut_appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] < adjusted_datetime_now]
                ohlc_df = generate_ohlc_df(cut_appended_premium_df, logger)
                ohlc_df = ohlc_df.merge(premium_df[columns_to_merge], on=['base_asset'], how='inner')
                pickled_ohlc_df = pickle.dumps(ohlc_df)
                # Save into redis db for current data
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                # publish Stream
                remote_redis.get_redis_client().xadd(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', {'data': pickled_ohlc_df}, maxlen=10, approximate=True)
                # Append into redis db for historical data
                old_ohlc_1T_kline = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline')
                if old_ohlc_1T_kline is None:
                    old_ohlc_1T_kline = pd.DataFrame()
                else:
                    old_ohlc_1T_kline = pickle.loads(old_ohlc_1T_kline)
                    old_ohlc_1T_kline = old_ohlc_1T_kline[old_ohlc_1T_kline['base_asset'].isin(ohlc_df['base_asset'].unique())]
                new_ohlc_1T_kline = pd.concat([old_ohlc_1T_kline, ohlc_df], axis=0).tail(max_length*ohlc_df['base_asset'].nunique())
                new_ohlc_1T_kline['closed'] = True
                pickled_ohlc_df = pickle.dumps(new_ohlc_1T_kline)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline', pickled_ohlc_df)
                # Directly insert into the DB
                insert_db_thread = Thread(
                    target=insert_kline_to_db,
                    args=(
                        new_ohlc_1T_kline,
                        f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline",
                        register_monitor_msg,
                        redis_dict,
                        mongodb_dict,
                        admin_id,
                        node,
                        logger
                    )
                )
                insert_db_thread.start()
                appended_premium_df = appended_premium_df[appended_premium_df['datetime_now'] >= adjusted_datetime_now]
            else:
                # Save into redis db for current data
                ohlc_df = generate_ohlc_df(appended_premium_df, logger)
                ohlc_df = ohlc_df.merge(premium_df[columns_to_merge], on=['base_asset'], how='inner')
                pickled_ohlc_df = pickle.dumps(ohlc_df)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                # # Publish to redis pubsub
                # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df) # Current
                # publish Stream
                remote_redis.get_redis_client().xadd(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', {'data': pickled_ohlc_df}, maxlen=10, approximate=True)
        except Exception as e:
            content = f"ohlc_1T_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_1T_loader: {traceback.format_exc()}\n appended_premium_df:{appended_premium_df}, premium_df:{premium_df}"
            logger.error(content)
            register_monitor_msg.register(admin_id, node, 'error', f"ohlc_1T_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)
            time.sleep(3)
                
def ohlc_day_resample_loader(
    resample_ohlc_df,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    original_period,
    resample_period,
    resample_closed_count,
    register_monitor_msg,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.1,
    max_length=300
    ):
    resample_period_number = int(re.search(r'\d+', resample_period).group())
    logger = InfoCoreLogger("kline_core", logging_dir).logger
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
    while True:
        original_ohlc_kline_df = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
        if original_ohlc_kline_df is not None:
            break
        time.sleep(5)

    start = time.time()
    original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
    resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
    resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
    local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Publish to redis pubsub
    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Directly insert into the DB
    insert_db_thread = Thread(
        target=insert_kline_to_db,
        args=(
            resampled_ohlc_history_df,
            f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
            register_monitor_msg,
            redis_dict,
            mongodb_dict,
            admin_id,
            node,
            logger
        )
    )
    insert_db_thread.start()
    logger.info(f"ohlc_day_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

    datetime_now = datetime.datetime.utcnow()        
    while True:
        time.sleep(loop_downtime_sec)
        try:
            datetime_before = datetime_now
            original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
            try:
                original_ohlc_history_last_datetime = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
            except TypeError:
                print(f"original_ohlc_history_last_datetime is None")
                continue
            resampled_ohlc_history_df = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
            datetime_now = datetime.datetime.utcnow()
            if ((datetime_before.hour // resample_period_number != datetime_now.hour // resample_period_number) or
                sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                start = time.time()
                new_resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                # print(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                # Save into the Redis DB
                # start = time.time()
                pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                # Publish to redis pubsub
                # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                # Directly insert into the DB
                insert_db_thread = Thread(
                    target=insert_kline_to_db,
                    args=(
                        resampled_ohlc_history_df,
                        f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
                        register_monitor_msg,
                        redis_dict,
                        mongodb_dict,
                        admin_id,
                        node,
                        logger
                    )
                )
                insert_db_thread.start()
                # self.kline_logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                    removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                    added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                    logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                    if len(removed_list) != 0:
                        # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                        resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                        local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                        logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
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
                    resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(days=resample_period_number)
                    # # Save into the Redis DB
                    # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # # PUBSUB
                    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # publish Stream
                    remote_redis.get_redis_client().xadd(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', {'data': pickle.dumps(resampled_ohlc_last_df)}, maxlen=10, approximate=True)
                except Exception as e:
                    logger.error(f"Exception: {e}, \nError in ohlc_day_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                    time.sleep(3)
        except Exception as e:
            content = f"ohlc_day_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_day_resample_loader: {traceback.format_exc()}"
            logger.error(content)
            register_monitor_msg.register(admin_id, node, 'error', f"ohlc_day_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)
                
def ohlc_hour_resample_loader(
    resample_ohlc_df,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    original_period,
    resample_period,
    resample_closed_count,
    register_monitor_msg,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.1,
    max_length=300
    ):
    resample_period_number = int(re.search(r'\d+', resample_period).group())
    logger = InfoCoreLogger("kline_core", logging_dir).logger
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']
    while True:
        original_ohlc_kline_df = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
        if original_ohlc_kline_df is not None:
            break
        time.sleep(5)

    start = time.time()
    original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
    resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
    resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
    local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Publish to redis pubsub
    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Directly insert into the DB
    insert_db_thread = Thread(
        target=insert_kline_to_db,
        args=(
            resampled_ohlc_history_df, 
            f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
            register_monitor_msg,
            redis_dict,
            mongodb_dict,
            admin_id,
            node,
            logger
        )
    )
    insert_db_thread.start()
    logger.info(f"ohlc_hour_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

    datetime_now = datetime.datetime.utcnow()
    while True:
        time.sleep(loop_downtime_sec)
        try:
            datetime_before = datetime_now
            original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
            try:
                original_ohlc_history_last_datetime = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
            except TypeError:
                print(f"original_ohlc_history_last_datetime is None")
                continue
            resampled_ohlc_history_df = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
            datetime_now = datetime.datetime.utcnow()
            if ((datetime_before.hour // resample_period_number != datetime_now.hour // resample_period_number) or
                sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                start = time.time()
                new_resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                print(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                # Save into the Redis DB
                # start = time.time()
                pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                # Publish to redis pubsub
                # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                # Directly insert into the DB
                insert_db_thread = Thread(
                    target=insert_kline_to_db,
                    args=(
                        resampled_ohlc_history_df,
                        f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
                        register_monitor_msg,
                        redis_dict,
                        mongodb_dict,
                        admin_id,
                        node,
                        logger
                    )
                )
                insert_db_thread.start()
                # self.kline_logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                    removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                    added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                    logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                    if len(removed_list) != 0:
                        # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                        resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                        local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                        logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
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
                    resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(hours=resample_period_number)
                    # # Save into the Redis DB
                    # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # # PUBSUB
                    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # publish Stream
                    remote_redis.get_redis_client().xadd(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', {'data': pickle.dumps(resampled_ohlc_last_df)}, maxlen=10, approximate=True)
                except Exception as e:
                    logger.error(f"Exception: {e}, \nError in ohlc_hour_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                    time.sleep(3)
        except Exception as e:
            content = f"ohlc_hour_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_hour_resample_loader: {traceback.format_exc()}"
            logger.error(content)
            register_monitor_msg.register(admin_id, node, 'error', f"ohlc_hour_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)
            
def ohlc_min_resample_loader(
    resample_ohlc_df,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    original_period,
    resample_period,
    resample_closed_count,
    register_monitor_msg,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.1,
    max_length=300
    ):
    resample_period_number = int(re.search(r'\d+', resample_period).group())
    logger = InfoCoreLogger("kline_core", logging_dir).logger
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    columns_to_merge = ['base_asset', 'tp', 'scr', 'atp24h', 'converted_tp']

    while True:
        original_ohlc_kline_df = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')
        if original_ohlc_kline_df is not None:
            break
        time.sleep(5)

    start = time.time()
    original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
    resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(original_ohlc_kline_df), resample_period, closed_count=resample_closed_count)
    resampled_ohlc_history_df = resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
    pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
    local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Publish to redis pubsub
    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
    # Directly insert into the DB
    insert_db_thread = Thread(
        target=insert_kline_to_db,
        args=(
            resampled_ohlc_history_df,
            f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
            register_monitor_msg,
            redis_dict,
            mongodb_dict,
            admin_id,
            node,
            logger
        )
    )
    insert_db_thread.start()
    logger.info(f"ohlc_min_resample_loader has started. {target_market_code}:{origin_market_code}_{resample_period}_kline, initial generating and storing resampled_ohlc_history_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")

    datetime_now = datetime.datetime.utcnow()
    while True:
        time.sleep(loop_downtime_sec)
        try:
            datetime_before = datetime_now
            original_ohlc_1T_now = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now'))
            try:
                original_ohlc_history_last_datetime = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')).iloc[-1]['datetime_now']
            except TypeError:
                print(f"original_ohlc_history_last_datetime is None")
                continue
            resampled_ohlc_history_df = pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline'))
            datetime_now = datetime.datetime.utcnow()
            if ((datetime_before.minute // resample_period_number != datetime_now.minute // resample_period_number) or
                sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique())):
                # concatenate fetched resampled_ohlc_history_df and newly generated resampled_ohlc_history_df
                start = time.time()
                new_resampled_ohlc_history_df = resample_ohlc_df(pickle.loads(local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{original_period}_kline')), resample_period, closed_count=resample_closed_count)
                new_resampled_ohlc_history_df = new_resampled_ohlc_history_df.merge(original_ohlc_1T_now[columns_to_merge], on=['base_asset'], how='inner')
                resampled_ohlc_history_df = pd.concat([resampled_ohlc_history_df, new_resampled_ohlc_history_df], axis=0, ignore_index=True)
                resampled_ohlc_history_df = resampled_ohlc_history_df.drop_duplicates(subset=['base_asset', 'datetime_now'], keep='last').groupby('base_asset').tail(max_length)
                logger.info(f"resampling ohlc_df(length: {len(resampled_ohlc_history_df)}): {time.time()-start}")
                # Save into the Redis DB
                start = time.time()
                pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                logger.info(f"redis saving {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}")
                # Publish to redis pubsub
                start = time.time() # TEST
                # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                # Directly insert into the DB
                insert_db_thread = Thread(
                    target=insert_kline_to_db,
                    args=(
                        resampled_ohlc_history_df,
                        f"INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline",
                        register_monitor_msg,
                        redis_dict,
                        mongodb_dict,
                        admin_id,
                        node,
                        logger
                    )
                )
                insert_db_thread.start()
                logger.info(f"redis publishing {target_market_code}:{origin_market_code}_{resample_period}_kline time: {time.time()-start}") # TEST
                if sorted(resampled_ohlc_history_df['base_asset'].unique()) != sorted(original_ohlc_1T_now['base_asset'].unique()):
                    removed_list = [x for x in resampled_ohlc_history_df['base_asset'].unique() if x not in original_ohlc_1T_now['base_asset'].unique()]
                    added_list = [x for x in original_ohlc_1T_now['base_asset'].unique() if x not in resampled_ohlc_history_df['base_asset'].unique()]
                    logger.info(f"{target_market_code}:{origin_market_code}_{resample_period}_kline base_asset is not matched. added: {added_list}, removed: {removed_list}")
                    if len(removed_list) != 0:
                        # remove the removed base_asset from resampled_ohlc_history_df and overwrite it
                        resampled_ohlc_history_df = resampled_ohlc_history_df[~resampled_ohlc_history_df['base_asset'].isin(removed_list)]
                        pickled_resampled_ohlc_history_df = pickle.dumps(resampled_ohlc_history_df)
                        local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_kline', pickled_resampled_ohlc_history_df)
                        logger.info(f"resampled_ohlc_history_df has been overwritten. removed_list: {removed_list}")
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
                    resampled_ohlc_last_df.loc[:, 'datetime_now'] = resampled_ohlc_last_df['datetime_now'] + datetime.timedelta(minutes=resample_period_number)
                    # # Save into the Redis DB
                    # self.redis_client.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{converted_resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # # PUBSUB
                    # self.redis_client_db0.publish(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', pickle.dumps(resampled_ohlc_last_df))
                    # publish Stream
                    remote_redis.get_redis_client().xadd(f'INFO_CORE|{target_market_code}:{origin_market_code}_{resample_period}_now', {'data': pickle.dumps(resampled_ohlc_last_df)}, maxlen=10, approximate=True)
                except Exception as e:
                    logger.error(f"Exception: {e}, \nError in ohlc_min_resample_loader: {e}, resampled_ohlc_last_df: {resampled_ohlc_last_df}, original_ohlc_1T_now: {original_ohlc_1T_now}")
                    time.sleep(3)
        except Exception as e:
            content = f"ohlc_min_resample_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, original_period:{original_period}, resample_period:{resample_period}, Error in ohlc_min_resample_loader: {traceback.format_exc()}"
            logger.error(content)
            register_monitor_msg.register(admin_id, node, 'error', f"ohlc_min_resample_loader got an error", content=content[:1995], code=None, sent_switch=0, send_counts=1, remark=None)


