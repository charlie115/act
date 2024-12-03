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

def store_kline_volatility_info(mongo_db_client, market_code_combination, logger, last_n=180):
    try:
        database = market_code_combination.replace('/', '__').replace(':', '-')
        mongo_db_conn = mongo_db_client.get_conn()
        db = mongo_db_conn[database]
        # Get all collection names in the database
        all_collections = db.list_collection_names()
        # Filter collections that end with '_1T'
        collections_1T = [name for name in all_collections if name.endswith('_1T')]
        if not collections_1T:
            logger.info(f"No 1T collections found in {database}.")
            return

        # Use the temporary collection in the target database
        temp_collection = db['volatility_info_temp']

        # List to store the data to be inserted into the temporary collection
        data_list = []

        for collection_name in collections_1T:
            collection = db[collection_name]
            
            # Fetch the last n records sorted by 'datetime_now' in descending order
            records_cursor = collection.find(
                {},
                {'_id': 0, 'base_asset': 1, 'LS_high': 1, 'LS_low': 1, 'datetime_now': 1}
            ).sort('datetime_now', -1).limit(last_n)
            
            # Convert the cursor to a list of dictionaries
            records = list(records_cursor)
            records_df = pd.DataFrame(records)
            
            # Check if DataFrame is not empty
            if not records_df.empty:
                # Get difference between high and low
                records_df['difference'] = records_df['LS_high'] - records_df['LS_low']
                # Get the mean of the difference
                mean_diff = float(records_df['difference'].mean())
                # Prepare the data dictionary
                data = {
                    'base_asset': records_df['base_asset'].iloc[0],
                    'mean_diff': mean_diff,
                    'datetime_now': datetime.datetime.utcnow()
                }
                data_list.append(data)    

        # Clear the temporary collection (optional, since we're overwriting)
        temp_collection.delete_many({})

        # Insert data into the temporary collection
        if data_list:
            temp_collection.insert_many(data_list)
        else:
            logger.info("No data to insert.")
            
        # Rename 'volatility_info_temp' to 'volatility_info', dropping the target if it exists
        temp_collection.rename('volatility_info', dropTarget=True)
        mongo_db_conn.close()
    except Exception as e:
        logger.error(f"An error occurred during storing volatility data: {e}\n{traceback.format_exc()}")
        mongo_db_conn.close()
        
def store_kline_volatility_info_loop(enabled_market_klines, mongodb_dict, logging_dir, last_n, loop_time_secs=60):
    logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
    logger.info(f"store_kline_volatility_info_loop started.")
    mongo_db_client = InitDBClient(**mongodb_dict)
    while True:
        try:
            start = time.time()
            for market_code_combination in enabled_market_klines:
                store_kline_volatility_info(mongo_db_client, market_code_combination, logger, last_n)
            logger.info(f"store_kline_volatility_info took {time.time()-start} seconds. for {len(enabled_market_klines)} market_code_combinations.")
        except Exception as e:
            logger.error(f"Error in store_kline_volatility_info_loop: {e}\n{traceback.format_exc()}")
        time.sleep(loop_time_secs)

def insert_kline_to_db(kline_df, channel_name, acw_api, redis_dict, mongodb_dict, admin_id, node, logger):
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
        closed_kline_df['datetime_now'] = pd.to_datetime(closed_kline_df['datetime_now']).dt.tz_localize(None)
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
                # logger.info(f"insert_kline_to_db|database: {market_code_combination} {kline_type}, Filtering {count} klines for {len(inserted_coin_list)} unique base_assets took {filtering_time} seconds")
                # logger.info(f"insert_kline_to_db|database: {market_code_combination} {kline_type}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {insert_time} seconds")
                # TEST
                logger.info(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds")
            # print(f"insert_kline_to_db|channel_name: {channel_name}, Inserting {count} klines for {len(inserted_coin_list)} unique base_assets took {time.time() - start} seconds") # TEST
        # mongo_client.close()
    except:
        logger.error(f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, 'Error in insert_kline_to_db', content=f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()[:1995]}")
    
def ohlc_1T_generator(
    info_dict,
    convert_rate_dict,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    acw_api,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.02,
    max_length=300
    ):
    logger = InfoCoreLogger("kline_core", logging_dir).logger
    logger.info(f"ohlc_1T_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code} has started.")
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    datetime_now = datetime.datetime.utcnow()
    per_minute_ohlc_df = pd.DataFrame()

    # Initialize columns outside the loop
    prefixes = ['tp', 'LS', 'SL']
    price_columns = ['tp_premium', 'LS_premium', 'SL_premium']
    other_columns = ['tp', 'scr', 'atp24h', 'converted_tp']
    ohlc_columns = [f"{prefix}_{col}" for prefix in prefixes for col in ['open', 'high', 'low', 'close']]

    for col in ohlc_columns + other_columns:
        per_minute_ohlc_df[col] = np.nan  # Initialize columns with NaN

    remote_redis.get_redis_client().xtrim(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', maxlen=max_length)

    loop_downtime_sec = 0.05
    while True:
        try:
            time.sleep(loop_downtime_sec)
            # datetime_before = datetime_now
            datetime_before = datetime_now.replace(second=0, microsecond=0)
            # datetime_now = datetime.datetime.utcnow()
            datetime_now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
            premium_df = get_premium_df(info_dict, convert_rate_dict, target_market_code, origin_market_code, logger=logger)
            premium_df['datetime_now'] = datetime_now

            # Extract necessary columns and set 'base_asset' as the index
            prices_df = premium_df.set_index('base_asset')[price_columns + other_columns]

            # Keep only base_assets that are in prices_df (remove delisted cryptos)
            per_minute_ohlc_df = per_minute_ohlc_df.reindex(prices_df.index)

            # Identify new base_assets (where 'LS_open' is NaN)
            mask_new = per_minute_ohlc_df['LS_open'].isna()

            # For new base_assets, initialize OHLC values
            if mask_new.any():
                # Extract prices for new base_assets
                new_prices = prices_df.loc[mask_new, price_columns]
                
                # Create a DataFrame for the OHLC columns
                # This will have columns like 'tp_open', 'tp_high', ..., 'SL_close'
                ohlc_cols = [f'{prefix}_{col}' for prefix in prefixes for col in ['open', 'high', 'low', 'close']]
                
                # Repeat the prices for 'open', 'high', 'low', 'close'
                # The shape of new_prices.values is (num_assets, num_prefixes)
                # We need to repeat each price 4 times (for 'open', 'high', 'low', 'close')
                repeated_prices = np.repeat(new_prices.values, 4, axis=1)
                
                # Create a DataFrame with the repeated prices
                new_ohlc_values = pd.DataFrame(
                    data=repeated_prices,
                    index=new_prices.index,
                    columns=ohlc_cols
                )
                

                # Assign the new OHLC values to per_minute_ohlc_df
                per_minute_ohlc_df.loc[mask_new, ohlc_cols] = new_ohlc_values.astype('float64')
                
                # Assign other columns
                per_minute_ohlc_df.loc[mask_new, other_columns] = prices_df.loc[mask_new, other_columns].astype('float64')

            # Update other columns for new base_assets
            per_minute_ohlc_df.loc[mask_new, other_columns] = prices_df.loc[mask_new, other_columns].astype('float64')

            # Create a mapping from prefixes to price columns
            prefix_price_map = dict(zip(prefixes, price_columns))

            # Create prices_df_prices with columns as prefixes
            prices_df_prices = prices_df[price_columns].rename(columns=dict(zip(price_columns, prefixes)))

            # Update 'high' for all prefixes
            per_minute_ohlc_df_high = per_minute_ohlc_df[[f'{prefix}_high' for prefix in prefixes]].rename(columns=lambda x: x.replace('_high', ''))
            per_minute_ohlc_df_high = np.maximum(per_minute_ohlc_df_high, prices_df_prices).astype('float64')
            per_minute_ohlc_df_high.columns = [f'{col}_high' for col in per_minute_ohlc_df_high.columns]
            per_minute_ohlc_df.update(per_minute_ohlc_df_high)

            # Update 'low' for all prefixes
            per_minute_ohlc_df_low = per_minute_ohlc_df[[f'{prefix}_low' for prefix in prefixes]].rename(columns=lambda x: x.replace('_low', ''))
            per_minute_ohlc_df_low = np.minimum(per_minute_ohlc_df_low, prices_df_prices).astype('float64')
            per_minute_ohlc_df_low.columns = [f'{col}_low' for col in per_minute_ohlc_df_low.columns]
            per_minute_ohlc_df.update(per_minute_ohlc_df_low)

            # Update 'close' for all prefixes
            per_minute_ohlc_df_close = prices_df_prices.copy().astype('float64')
            per_minute_ohlc_df_close.columns = [f'{col}_close' for col in per_minute_ohlc_df_close.columns]
            per_minute_ohlc_df.update(per_minute_ohlc_df_close)

            # Update other columns
            per_minute_ohlc_df[other_columns] = prices_df[other_columns]

            # Update per_minute_ohlc_df in the Redis 'now' data
            ohlc_now_df = per_minute_ohlc_df.reset_index()
            ohlc_now_df['datetime_now'] = datetime_now
            ohlc_now_df['dollar'] = get_dollar_dict()['price']
            pickled_ohlc_now_df = pickle.dumps(ohlc_now_df)
            local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_now_df)
            
            # Publish Stream
            remote_redis.get_redis_client().xadd(
                f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now',
                {'data': pickled_ohlc_now_df},
                maxlen=10,
                approximate=True
            )

            # Check if the minute has changed
            if datetime_before.minute != datetime_now.minute:
                adjusted_datetime_now = datetime.datetime(
                    datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute
                )
                # Finalize the per-minute OHLC DataFrame
                ohlc_df = per_minute_ohlc_df.reset_index()
                ohlc_df['datetime_now'] = adjusted_datetime_now - datetime.timedelta(minutes=1)
                ohlc_df['dollar'] = get_dollar_dict()['price']
                ohlc_df['closed'] = True

                # Serialize and store the ohlc_df
                pickled_ohlc_df = pickle.dumps(ohlc_df)
                # Save into Redis for current data
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_df)
                # Publish Stream
                remote_redis.get_redis_client().xadd(
                    f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now',
                    {'data': pickled_ohlc_df},
                    maxlen=10,
                    approximate=True
                )
                # Append into Redis for historical data
                old_ohlc_1T_kline = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline')
                if old_ohlc_1T_kline is None:
                    old_ohlc_1T_kline = pd.DataFrame()
                else:
                    old_ohlc_1T_kline = pickle.loads(old_ohlc_1T_kline)
                    # Keep only base_assets that are in ohlc_df
                    old_ohlc_1T_kline = old_ohlc_1T_kline[old_ohlc_1T_kline['base_asset'].isin(ohlc_df['base_asset'].unique())]
                new_ohlc_1T_kline = pd.concat([old_ohlc_1T_kline, ohlc_df], axis=0).tail(max_length * ohlc_df['base_asset'].nunique())
                pickled_ohlc_df = pickle.dumps(new_ohlc_1T_kline)
                local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline', pickled_ohlc_df)
                # TEST
                logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Finalized {len(ohlc_df)} klines for {ohlc_df['base_asset'].nunique()} unique base_assets")
                # Insert into the database
                insert_db_thread = Thread(
                    target=insert_kline_to_db,
                    args=(
                        new_ohlc_1T_kline,
                        f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline",
                        acw_api,
                        redis_dict,
                        mongodb_dict,
                        admin_id,
                        node,
                        logger
                    )
                )
                insert_db_thread.start()
                # Reset per_minute_ohlc_df for the new minute
                per_minute_ohlc_df = pd.DataFrame()
                # Re-initialize columns for the new DataFrame
                for col in ohlc_columns + other_columns:
                    per_minute_ohlc_df[col] = np.nan
        except Exception as e:
            content = f"ohlc_1T_loader|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_1T_loader: {traceback.format_exc()}"
            logger.error(content)
            acw_api.create_message_thread(admin_id, 'Error in ohlc_1T_loader', content=content[:1995])
            time.sleep(3)
            
def generate_interval_kline(
    per_interval_ohlc_df,
    previous_interval_start,
    interval_minutes,
    prefixes,
    insert_kline_to_db,
    interval_label,
    target_market_code,
    origin_market_code,
    acw_api,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logger,
    max_length
    ):
    try:
        # TEST
        logger.info(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, Thread has started.")
        local_redis = RedisHelper()
        error_count = 0
        # wait until the last 1T kline is available
        while True:
            # Load the ohlc_1T_kline
            pickled_ohlc_1T_kline = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline')
            if pickled_ohlc_1T_kline is None:
                logger.warning(f"No 1T Kline data available for {target_market_code}:{origin_market_code}, {interval_label}")
                return
            ohlc_1T_kline_df = pickle.loads(pickled_ohlc_1T_kline)
            last_ohlc_1T_kline_df = ohlc_1T_kline_df[ohlc_1T_kline_df['datetime_now'] == ohlc_1T_kline_df['datetime_now'].max()]
            last_kline_datetime_upto_minute = pd.to_datetime(last_ohlc_1T_kline_df['datetime_now']).iloc[0].replace(second=0, microsecond=0, tzinfo=None)  
            
            if last_kline_datetime_upto_minute == previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1):
                error_count = 0
                break
            else:            
                # logger.info(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, Waiting for the last 1T kline to be available")
                # logger.info(f"last_kline_datetime_upto_minute: {last_kline_datetime_upto_minute}")
                # logger.info(f"previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1): {previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1)}")
                error_count += 1
                if error_count > 100:
                    logger.error(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, Error: Timeout waiting for the last 1T kline to be available")
                    logger.info(f"last_kline_datetime_upto_minute: {last_kline_datetime_upto_minute}")
                    logger.info(f"previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1): {previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1)}")
                    logger.info(f"datetime.datetime.now(): {datetime.datetime.now()}")
                    return 
                time.sleep(0.05)
              

        
        # Finalize the per-interval OHLC DataFrame
        ohlc_df = per_interval_ohlc_df.reset_index()
        ohlc_df['datetime_now'] = previous_interval_start
        ohlc_df['dollar'] = get_dollar_dict()['price']
        ohlc_df['closed'] = True
        
        last_ohlc_1T_kline_df = last_ohlc_1T_kline_df[last_ohlc_1T_kline_df['base_asset'].isin(ohlc_df['base_asset'].unique())]
        
        # overwrite close data with the last 1T close data
        for prefix in prefixes:
            ohlc_df[f'{prefix}_close'] = last_ohlc_1T_kline_df[f'{prefix}_close'].values
            
        # Compare the high and low with the last 1T high and low
        for prefix in prefixes:
            ohlc_df[f'{prefix}_high'] = np.maximum(ohlc_df[f'{prefix}_high'], last_ohlc_1T_kline_df[f'{prefix}_high'].values)
            ohlc_df[f'{prefix}_low'] = np.minimum(ohlc_df[f'{prefix}_low'], last_ohlc_1T_kline_df[f'{prefix}_low'].values)

        # Append into Redis for historical data
        old_ohlc_kline = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_kline')
        if old_ohlc_kline is None:
            old_ohlc_kline = pd.DataFrame()
        else:
            old_ohlc_kline = pickle.loads(old_ohlc_kline)
            # Keep only base_assets that are in ohlc_df
            old_ohlc_kline = old_ohlc_kline[old_ohlc_kline['base_asset'].isin(ohlc_df['base_asset'].unique())]
        new_ohlc_kline = pd.concat([old_ohlc_kline, ohlc_df], axis=0).tail(max_length * ohlc_df['base_asset'].nunique())
        pickled_new_ohlc_kline = pickle.dumps(new_ohlc_kline)
        local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_kline', pickled_new_ohlc_kline)
        # Insert into the database
        insert_kline_to_db(
            new_ohlc_kline,
            f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_kline",
            acw_api,
            redis_dict,
            mongodb_dict,
            admin_id,
            node,
            logger
        )
    except Exception as e:
        content = f"ohlc_{interval_label}_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_{interval_label}_generator: {traceback.format_exc()}"
        logger.error(content)
        acw_api.create_message_thread(admin_id, f'Error in ohlc_{interval_label}_generator', content=content[:1995])
        time.sleep(3)
                
def ohlc_interval_generator(
    interval_label,
    insert_kline_to_db,
    target_market_code,
    origin_market_code,
    acw_api,
    admin_id,
    node,
    redis_dict,
    mongodb_dict,
    logging_dir,
    loop_downtime_sec=0.1,
    max_length=300
):
    logger = InfoCoreLogger(f"kline_core", logging_dir).logger
    logger.info(f"Starting kline_core for {target_market_code}:{origin_market_code} with interval_label: {interval_label}")
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()
    datetime_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    # Determine interval duration in minutes
    if interval_label.endswith('T'):
        interval_minutes = int(interval_label[:-1])
    elif interval_label.endswith('H'):
        interval_minutes = int(interval_label[:-1]) * 60
    else:
        raise ValueError(f"Invalid interval_label: {interval_label}")

    # Function to get the start time of the interval
    def get_interval_start(dt):
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        interval_seconds = interval_minutes * 60
        timestamp = dt.timestamp()
        interval_start_timestamp = (timestamp // interval_seconds) * interval_seconds
        return datetime.datetime.fromtimestamp(interval_start_timestamp).replace(tzinfo=None)

    # Initialize current interval start
    current_interval_start = get_interval_start(datetime_now)
    previous_interval_start = current_interval_start

    per_interval_ohlc_df = pd.DataFrame()

    # Initialize columns outside the loop
    prefixes = ['tp', 'LS', 'SL']
    ohlc_columns = [f"{prefix}_{col}" for prefix in prefixes for col in ['open', 'high', 'low', 'close']]
    other_columns = ['tp', 'scr', 'atp24h', 'converted_tp']
    all_columns = ohlc_columns + other_columns

    # Initialize per_interval_ohlc_df with NaNs
    for col in all_columns:
        per_interval_ohlc_df[col] = np.nan

    initialize_open_prices = True  # Flag to indicate if we need to initialize open prices
    finalize_interval = False      # Flag to indicate when to finalize the interval

    while True:
        time.sleep(loop_downtime_sec)
        try:
            datetime_now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

            # Fetch the latest 1T Now data from Redis
            pickled_1T_now = local_redis.get_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now')
            if pickled_1T_now is None:
                logger.warning(f"No 1T Now data available for {target_market_code}:{origin_market_code}_{interval_label}")
                time.sleep(5)
                continue
            
            ohlc_1T_df = pickle.loads(pickled_1T_now)
            ohlc_1T_df_datetime_now = pd.to_datetime(ohlc_1T_df['datetime_now']).iloc[0]
            ohlc_1T_df_datetime_upto_minute = ohlc_1T_df_datetime_now.replace(second=0, microsecond=0, tzinfo=None)

            # Check if the interval has changed
            new_interval_start = get_interval_start(datetime_now)

            if new_interval_start != current_interval_start:
                # The interval has changed
                finalize_interval = True
                current_interval_start = new_interval_start
                initialize_open_prices = True  # Prepare to initialize open prices for the new interval

            # Proceed to process data as usual
            temp_df = ohlc_1T_df.set_index('base_asset')[all_columns]
            per_interval_ohlc_df = per_interval_ohlc_df.reindex(temp_df.index)

            # Identify new base_assets
            mask_new = per_interval_ohlc_df['LS_open'].isna()

            # For new base_assets, initialize OHLC values
            if mask_new.any():
                per_interval_ohlc_df.loc[mask_new, ohlc_columns] = temp_df.loc[mask_new, ohlc_columns].astype('float64')
                per_interval_ohlc_df.loc[mask_new, other_columns] = temp_df.loc[mask_new, other_columns].astype('float64')

            # For existing base_assets, update high, low, close
            mask_existing = ~mask_new
            for prefix in prefixes:
                per_interval_ohlc_df.loc[mask_existing, f'{prefix}_high'] = np.maximum(
                    per_interval_ohlc_df.loc[mask_existing, f'{prefix}_high'],
                    temp_df.loc[mask_existing, f'{prefix}_high']
                )
                per_interval_ohlc_df.loc[mask_existing, f'{prefix}_low'] = np.minimum(
                    per_interval_ohlc_df.loc[mask_existing, f'{prefix}_low'],
                    temp_df.loc[mask_existing, f'{prefix}_low']
                )
                per_interval_ohlc_df.loc[mask_existing, f'{prefix}_close'] = temp_df.loc[mask_existing, f'{prefix}_close']

            # Update other columns for existing assets
            per_interval_ohlc_df.loc[mask_existing, other_columns] = temp_df.loc[mask_existing, other_columns]

            # Update per_interval_ohlc_df in the Redis 'now' data
            ohlc_now_df = per_interval_ohlc_df.reset_index()
            # ohlc_now_df['datetime_now'] = datetime_now
            ohlc_now_df['datetime_now'] = current_interval_start
            pickled_ohlc_now_df = pickle.dumps(ohlc_now_df)
            local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_now', pickled_ohlc_now_df)

            # Publish Stream
            remote_redis.get_redis_client().xadd(
                f'INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_now',
                {'data': pickled_ohlc_now_df},
                maxlen=10,
                approximate=True
            )

            # If initialize_open_prices is True and new data is available for the new interval
            if (initialize_open_prices and 
                ohlc_1T_df_datetime_upto_minute == current_interval_start.replace(tzinfo=None)):
                # Initialize per_interval_ohlc_df open prices with temp_df data
                per_interval_ohlc_df = per_interval_ohlc_df.reindex(temp_df.index)

                # Set open prices
                per_interval_ohlc_df[ohlc_columns] = temp_df[ohlc_columns]
                per_interval_ohlc_df[other_columns] = temp_df[other_columns]

                # Reset high and low prices to open prices
                for prefix in prefixes:
                    per_interval_ohlc_df[f'{prefix}_high'] = per_interval_ohlc_df[f'{prefix}_open']
                    per_interval_ohlc_df[f'{prefix}_low'] = per_interval_ohlc_df[f'{prefix}_open']

                initialize_open_prices = False

            # Finalize the interval after processing the last 1T data of the previous interval
            if (finalize_interval and
                ohlc_1T_df_datetime_upto_minute == previous_interval_start.replace(tzinfo=None) + datetime.timedelta(minutes=interval_minutes - 1)):
                
                # TEST
                logger.info(f"ohlc_interval_generator|{target_market_code}:{origin_market_code}, {interval_label}, Finalizing the interval. Thread will be started.")
                generate_interval_kline_thread = Thread(
                    target=generate_interval_kline,
                    args=(
                        per_interval_ohlc_df,
                        previous_interval_start,
                        interval_minutes,
                        prefixes,
                        insert_kline_to_db,
                        interval_label,
                        target_market_code,
                        origin_market_code,
                        acw_api,
                        admin_id,
                        node,
                        redis_dict,
                        mongodb_dict,
                        logger,
                        max_length
                    ),
                    daemon=True
                )
                generate_interval_kline_thread.start()

                # Reset per_interval_ohlc_df for the new interval
                per_interval_ohlc_df = pd.DataFrame()
                for col in all_columns:
                    per_interval_ohlc_df[col] = np.nan

                finalize_interval = False
                previous_interval_start = current_interval_start  # Update previous interval start

        except Exception as e:
            content = f"ohlc_{interval_label}_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_{interval_label}_generator: {traceback.format_exc()}"
            logger.error(content)
            acw_api.create_message_thread(admin_id, f'Error in ohlc_{interval_label}_generator', content=content[:1995])
            time.sleep(3)