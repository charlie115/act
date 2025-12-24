import traceback
import pandas as pd
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from etc.db_handler.mongodb_client import InitDBClient
import pickle
import datetime
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
import time
import numpy as np
import re
from pymongo.errors import BulkWriteError
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.premium_data_generator import get_premium_df
from standalone_func.store_exchange_status import fetch_market_servercheck

# Module-level thread pool for insert operations
# Limits concurrent inserts per process (prevents overwhelming MongoDB)
# 4 workers is optimal: balances throughput with connection pool usage
_INSERT_THREAD_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="kline_insert")

def store_kline_volatility_info(mongo_db_client, market_code_combination, logger, last_n=180, stale_threshold_minutes=10):
    """
    Store volatility info for all 1T kline collections.

    Optimizations:
    - Uses connection pooling (do not close connection - it's shared)
    - Uses datetime_now index for faster sorted queries
    - Ensures indexes exist before querying
    - Filters out stale/delisted symbols (latest data older than stale_threshold_minutes)
    """
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

        # Calculate the stale threshold time
        stale_threshold_time = datetime.datetime.utcnow() - datetime.timedelta(minutes=stale_threshold_minutes)
        skipped_stale_count = 0

        for collection_name in collections_1T:
            # Ensure index exists for this collection (cached, fast check)
            mongo_db_client.ensure_indexes(database, collection_name)

            collection = db[collection_name]

            # Fetch the last n records sorted by 'datetime_now' in descending order
            # Use hint to force index usage for O(n) instead of O(n log n) sort
            # Fetch SL_high and LS_low to calculate spread-adjusted volatility (SL_high - LS_low)
            try:
                records_cursor = collection.find(
                    {},
                    {'_id': 0, 'base_asset': 1, 'SL_high': 1, 'LS_low': 1, 'datetime_now': 1}
                ).sort('datetime_now', -1).limit(last_n).hint([('datetime_now', -1)])
            except Exception:
                # Fallback if hint fails (index might not exist yet)
                records_cursor = collection.find(
                    {},
                    {'_id': 0, 'base_asset': 1, 'SL_high': 1, 'LS_low': 1, 'datetime_now': 1}
                ).sort('datetime_now', -1).limit(last_n)

            # Convert the cursor to a list of dictionaries
            records = list(records_cursor)
            records_df = pd.DataFrame(records)

            # Check if DataFrame is not empty
            if not records_df.empty:
                # Check if the latest record is stale (older than threshold)
                latest_datetime = pd.to_datetime(records_df['datetime_now'].iloc[0])
                if latest_datetime.tzinfo is not None:
                    latest_datetime = latest_datetime.replace(tzinfo=None)

                if latest_datetime < stale_threshold_time:
                    # Skip this symbol - data is stale (likely delisted)
                    skipped_stale_count += 1
                    continue

                # Calculate spread-adjusted volatility: SL_high - LS_low
                # This accounts for the LS-SL spread, giving a more realistic arbitrage profitability measure
                records_df['difference'] = records_df['SL_high'] - records_df['LS_low']
                # Get the mean of the difference
                mean_diff = float(records_df['difference'].mean())
                # Prepare the data dictionary
                data = {
                    'base_asset': records_df['base_asset'].iloc[0],
                    'mean_diff': mean_diff,
                    'datetime_now': datetime.datetime.utcnow()
                }
                data_list.append(data)

        if skipped_stale_count > 0:
            logger.info(f"store_kline_volatility_info|{database}: Skipped {skipped_stale_count} stale symbols (data older than {stale_threshold_minutes} minutes)")

        # Clear the temporary collection (optional, since we're overwriting)
        temp_collection.delete_many({})

        # Insert data into the temporary collection
        if data_list:
            temp_collection.insert_many(data_list)
        else:
            logger.info("No data to insert.")

        # Rename 'volatility_info_temp' to 'volatility_info', dropping the target if it exists
        temp_collection.rename('volatility_info', dropTarget=True)
        # NOTE: Do NOT close the connection - we use connection pooling now
        # The connection is shared and managed by InitDBClient singleton
    except Exception as e:
        logger.error(f"An error occurred during storing volatility data: {e}\n{traceback.format_exc()}")
        # NOTE: Do NOT close the connection - we use connection pooling now
        
def store_kline_volatility_info_loop(enabled_market_klines, mongodb_dict, logging_dir, last_n, loop_time_secs=60):
    logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
    logger.info(f"store_kline_volatility_info_loop started.")
    mongo_db_client = InitDBClient(**mongodb_dict)
    while True:
        try:
            start = time.time()
            for market_code_combination in enabled_market_klines:
                first_market_code, second_market_code = market_code_combination.split(':')
                # Check if the one of the market_code is in maintenance
                if fetch_market_servercheck(first_market_code) or fetch_market_servercheck(second_market_code):
                    logger.info(f"store_kline_volatility_info_loop|{market_code_combination} has been skipped due to server check.")
                    time.sleep(1)
                    continue
                store_kline_volatility_info(mongo_db_client, market_code_combination, logger, last_n)
            logger.info(f"store_kline_volatility_info took {time.time()-start} seconds. for {len(enabled_market_klines)} market_code_combinations.")
        except Exception as e:
            logger.error(f"Error in store_kline_volatility_info_loop: {e}\n{traceback.format_exc()}")
        time.sleep(loop_time_secs)

def _bulk_insert_with_retry(db, collection_name, docs, mongodb_client, database_name, max_retries=3):
    """
    Insert documents to a collection with retry logic for transient failures.

    Args:
        db: MongoDB database object
        collection_name: Name of the collection
        docs: List of documents to insert
        mongodb_client: InitDBClient instance for ensure_indexes
        database_name: Database name for ensure_indexes
        max_retries: Maximum retry attempts

    Returns:
        tuple: (inserted_count, failed)
    """
    if not docs:
        return 0, False

    # Ensure index exists before insert (cached check, fast)
    mongodb_client.ensure_indexes(database_name, collection_name)
    collection = db[collection_name]

    for attempt in range(max_retries):
        try:
            result = collection.insert_many(docs, ordered=False)
            return len(result.inserted_ids), False
        except BulkWriteError as bwe:
            # Some documents may have succeeded
            inserted = bwe.details.get('nInserted', 0)
            if inserted == len(docs):
                # All docs inserted despite error (e.g., duplicate key warnings)
                return inserted, False

            # Get documents that failed (for potential retry)
            write_errors = bwe.details.get('writeErrors', [])
            if attempt == max_retries - 1:
                # Last attempt failed
                return inserted, True
            # Wait before retry with exponential backoff
            time.sleep(0.1 * (attempt + 1))
        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on final attempt
            time.sleep(0.1 * (attempt + 1))

    return 0, True


def insert_kline_to_db(kline_df, channel_name, acw_api, redis_dict, mongodb_dict, admin_id, node, logger):
    """
    Insert kline data to MongoDB with optimizations:
    - Connection pooling (reuses MongoClient via InitDBClient singleton)
    - Batch Redis MGET for cache warming (single round-trip for all keys)
    - DataFrame groupby optimization (single operation vs repeated filtering)
    - Bulk insert with retry logic (handles transient failures)
    - Batch Redis cache updates (single pipeline for all updates)
    - Automatic index creation on datetime_now
    """
    remote_redis = RedisHelper(**redis_dict)
    local_redis = RedisHelper()  # For caching last timestamps
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

        # Use connection pooling - InitDBClient.get_conn() returns cached MongoClient
        mongodb_client = InitDBClient(**mongodb_dict)
        mongodb_conn = mongodb_client.get_conn()
        db = mongodb_conn[converted_market_code_combination]

        closed_kline_df = kline_df[kline_df['closed']==True].copy()
        closed_kline_df['datetime_now'] = pd.to_datetime(closed_kline_df['datetime_now']).dt.tz_localize(None)
        if len(closed_kline_df) == 0:
            logger.info(f'insert_kline_to_db|{channel_name} No klines to be inserted')
            return

        start = time.time()
        base_asset_list = list(closed_kline_df['base_asset'].unique())
        cache_key_prefix = f"KLINE_LAST_TS|{converted_market_code_combination}|{kline_type}"

        # OPTIMIZATION 1: Batch Redis MGET - single round-trip for all cache keys
        cache_keys = [f"{cache_key_prefix}|{asset}" for asset in base_asset_list]
        cached_values = local_redis.mget_data(cache_keys)

        # Build cached timestamps dict
        cached_timestamps = {}
        for asset, cached_ts in zip(base_asset_list, cached_values):
            if cached_ts is not None:
                try:
                    cached_timestamps[asset] = pd.to_datetime(float(cached_ts.decode('utf-8')), unit='s')
                except (ValueError, AttributeError):
                    cached_timestamps[asset] = None
            else:
                cached_timestamps[asset] = None

        # OPTIMIZATION 2: Pre-group DataFrame by base_asset (single pandas operation)
        grouped = closed_kline_df.groupby('base_asset')

        # Prepare insert batches and cache updates
        count = 0
        inserted_coin_list = []
        cache_updates = {}  # {cache_key: new_timestamp_str}
        failed_collections = []

        for base_asset, group_df in grouped:
            collection_name = f"{base_asset}_{kline_type}"
            cache_key = f"{cache_key_prefix}|{base_asset}"
            last_datetime = cached_timestamps.get(base_asset)

            # Determine which records to insert
            if last_datetime is not None:
                # Cache hit - filter using cached timestamp
                df_to_insert = group_df[group_df['datetime_now'] > last_datetime]
            else:
                # Cache miss - check if collection is empty using efficient method
                is_empty = mongodb_client.is_collection_empty(
                    converted_market_code_combination, collection_name
                )

                if is_empty:
                    # Collection is empty, insert all data for this asset
                    df_to_insert = group_df
                else:
                    # Collection has data - get last timestamp using indexed query
                    last_datetime = mongodb_client.get_last_datetime(
                        converted_market_code_combination, collection_name
                    )
                    if last_datetime is not None:
                        df_to_insert = group_df[group_df['datetime_now'] > last_datetime]
                    else:
                        # Couldn't get last datetime, insert all
                        df_to_insert = group_df

            if len(df_to_insert) > 0:
                docs = df_to_insert.to_dict('records')

                # OPTIMIZATION 3: Bulk insert with retry logic
                inserted, failed = _bulk_insert_with_retry(
                    db, collection_name, docs, mongodb_client, converted_market_code_combination
                )

                count += inserted
                if inserted > 0:
                    inserted_coin_list.append(base_asset)
                    # Prepare cache update
                    new_last_ts = df_to_insert['datetime_now'].max().timestamp()
                    cache_updates[cache_key] = str(new_last_ts)

                if failed:
                    failed_collections.append(collection_name)

        # OPTIMIZATION 4: Batch Redis cache updates - single pipeline
        if cache_updates:
            local_redis.mset_data_with_expiry(cache_updates, ex=3600)  # Cache for 1 hour

        if count > 0:
            elapsed = time.time() - start
            logger.info(f"insert_kline_to_db|channel_name: {channel_name}, Inserted {count} klines for {len(inserted_coin_list)} unique base_assets took {elapsed:.3f} seconds")
            if failed_collections:
                logger.warning(f"insert_kline_to_db|{channel_name} Failed collections (after retries): {failed_collections}")
            if count != len(inserted_coin_list):
                logger.error(f"kline mismatch: {count} != {len(inserted_coin_list)}")
                logger.error(f"closed_kline_df: {closed_kline_df}")
    except Exception:
        logger.error(f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, 'Error in insert_kline_to_db', content=f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()[:1995]}")

def ohlc_1T_generator(
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
    
    # Initialize convert_rate_dict
    while True:
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_convert_rate_dict:
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            break
        logger.info("convert_rate_dict is not ready yet. Waiting for 1 second...")
        time.sleep(1)
    
    # Loop Thread for saving servercheck status
    target_market_servercheck = False
    origin_market_servercheck = False
    def save_servercheck_status():
        logger.info(f"ohlc_1T_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, save_servercheck_status thread has started.")
        nonlocal target_market_servercheck, origin_market_servercheck
        while True:
            try:
                target_market_servercheck = fetch_market_servercheck(target_market_code)
                origin_market_servercheck = fetch_market_servercheck(origin_market_code)
                time.sleep(1)
            except Exception as e:
                logger.error(f"ohlc_1T_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in save_servercheck_status: {traceback.format_exc()}")
                time.sleep(3)
    save_servercheck_status_thread = Thread(target=save_servercheck_status, daemon=True)
    save_servercheck_status_thread.start()

    loop_downtime_sec = 0.05
    while True:
        try:
            # Check if one of the markets is in maintenance
            if target_market_servercheck or origin_market_servercheck:
                # logger.info(f"ohlc_1T_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, has been skipped due to server check.")
                time.sleep(1)
                continue
            time.sleep(loop_downtime_sec)
            
            # # Performance tracking - start of iteration
            # loop_start_time = time.time()
            
            # datetime_before = datetime_now
            datetime_before = datetime_now.replace(second=0, microsecond=0)
            # datetime_now = datetime.datetime.utcnow()
            datetime_now = datetime.datetime.utcnow().replace(second=0, microsecond=0)
            
            # # Performance tracking - premium data fetch
            # premium_fetch_start = time.time()
            premium_df = get_premium_df(local_redis, fetched_convert_rate_dict, target_market_code, origin_market_code, logger=logger)
            premium_df['datetime_now'] = datetime_now
            # premium_fetch_time = time.time() - premium_fetch_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Fetching premium data took {premium_fetch_time:.4f} seconds")

            # Extract necessary columns and set 'base_asset' as the index
            # # Performance tracking - data preparation
            # prep_start = time.time()
            prices_df = premium_df.set_index('base_asset')[price_columns + other_columns]

            # Keep only base_assets that are in prices_df (remove delisted cryptos)
            per_minute_ohlc_df = per_minute_ohlc_df.reindex(prices_df.index)

            # Identify new base_assets (where 'LS_open' is NaN)
            mask_new = per_minute_ohlc_df['LS_open'].isna()
            # prep_time = time.time() - prep_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Data preparation took {prep_time:.4f} seconds")

            # # Performance tracking - process new assets
            # new_assets_start = time.time()
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
            # new_assets_time = time.time() - new_assets_start
            # if mask_new.any():
            #     logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Processing {mask_new.sum()} new assets took {new_assets_time:.4f} seconds")

            # Update other columns for new base_assets
            per_minute_ohlc_df.loc[mask_new, other_columns] = prices_df.loc[mask_new, other_columns].astype('float64')

            # # Performance tracking - update OHLC values
            # update_ohlc_start = time.time()
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
            # update_ohlc_time = time.time() - update_ohlc_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Updating OHLC values took {update_ohlc_time:.4f} seconds")

            # # Performance tracking - Redis update
            # redis_update_start = time.time()
            # Update per_minute_ohlc_df in the Redis 'now' data
            ohlc_now_df = per_minute_ohlc_df.reset_index()
            ohlc_now_df['datetime_now'] = datetime_now
            ohlc_now_df['dollar'] = get_dollar_dict(local_redis)['price']
            pickled_ohlc_now_df = pickle.dumps(ohlc_now_df)
            local_redis.set_data(f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now', pickled_ohlc_now_df)
            
            # Publish Stream
            remote_redis.get_redis_client().xadd(
                f'INFO_CORE|{target_market_code}:{origin_market_code}_1T_now',
                {'data': pickled_ohlc_now_df},
                maxlen=10,
                approximate=True
            )
            # redis_update_time = time.time() - redis_update_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Redis updates took {redis_update_time:.4f} seconds")

            # # Performance tracking - minute transition
            # minute_transition_start = None
            # minute_transition_time = 0
            
            # Check if the minute has changed
            if datetime_before.minute != datetime_now.minute:
                minute_transition_start = time.time()
                adjusted_datetime_now = datetime.datetime(
                    datetime_now.year, datetime_now.month, datetime_now.day, datetime_now.hour, datetime_now.minute
                )
                # Finalize the per-minute OHLC DataFrame
                ohlc_df = per_minute_ohlc_df.reset_index()
                ohlc_df['datetime_now'] = adjusted_datetime_now - datetime.timedelta(minutes=1)
                ohlc_df['dollar'] = get_dollar_dict(local_redis)['price']
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
                # # TEST
                # minute_transition_time = time.time() - minute_transition_start
                # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Minute transition processing took {minute_transition_time:.4f} seconds")
                logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Finalized {len(ohlc_df)} klines for {ohlc_df['base_asset'].nunique()} unique base_assets")
                
                # Insert into the database using thread pool (reuses threads, limits concurrency)
                _INSERT_THREAD_POOL.submit(
                    insert_kline_to_db,
                    new_ohlc_1T_kline,
                    f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline",
                    acw_api,
                    redis_dict,
                    mongodb_dict,
                    admin_id,
                    node,
                    logger
                )
                # db_insert_time = time.time() - db_insert_start
                # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, DB insert thread creation took {db_insert_time:.4f} seconds")
                
                # Reset per_minute_ohlc_df for the new minute
                per_minute_ohlc_df = pd.DataFrame()
                # Re-initialize columns for the new DataFrame
                for col in ohlc_columns + other_columns:
                    per_minute_ohlc_df[col] = np.nan
                    
            # Performance tracking - info dict reload
            # convert_rate_dict_reload_start = time.time()
            # Reload convert_rate_dict
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in local_redis.hgetall_dict('convert_rate_dict').items()}
            # convert_rate_dict_reload_time = time.time() - convert_rate_dict_reload_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Info dict reload took {convert_rate_dict_reload_time:.4f} seconds")
            
            # # Performance tracking - full iteration
            # total_loop_time = time.time() - loop_start_time
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Full iteration took {total_loop_time:.4f} seconds [premium:{premium_fetch_time:.4f}, prep:{prep_time:.4f}, update:{update_ohlc_time:.4f}, redis:{redis_update_time:.4f}, minute_change:{minute_transition_time:.4f}, reload:{convert_rate_dict_reload_time:.4f}]")
            
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
        ohlc_df['dollar'] = get_dollar_dict(local_redis)['price']
        ohlc_df['closed'] = True
        
        # Find symbols in each DataFrame to handle new symbols safely
        ohlc_symbols = set(ohlc_df['base_asset'].unique())
        last_1T_symbols = set(last_ohlc_1T_kline_df['base_asset'].unique())
        common_symbols = ohlc_symbols & last_1T_symbols
        new_symbols = ohlc_symbols - last_1T_symbols  # Symbols only in ohlc_df (newly listed)

        if new_symbols:
            logger.info(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, New symbols detected (keeping existing values): {new_symbols}")

        # Split ohlc_df into common symbols and new symbols
        ohlc_df_common = ohlc_df[ohlc_df['base_asset'].isin(common_symbols)].copy()
        ohlc_df_new = ohlc_df[ohlc_df['base_asset'].isin(new_symbols)].copy()

        # Process common symbols: update close/high/low from 1T data
        if len(ohlc_df_common) > 0:
            # Filter and sort both DataFrames by base_asset to ensure row alignment
            last_ohlc_1T_common = last_ohlc_1T_kline_df[last_ohlc_1T_kline_df['base_asset'].isin(common_symbols)].copy()
            ohlc_df_common = ohlc_df_common.sort_values('base_asset').reset_index(drop=True)
            last_ohlc_1T_common = last_ohlc_1T_common.sort_values('base_asset').reset_index(drop=True)

            # Overwrite close data with the last 1T close data
            for prefix in prefixes:
                ohlc_df_common[f'{prefix}_close'] = last_ohlc_1T_common[f'{prefix}_close'].values

            # Compare the high and low with the last 1T high and low
            for prefix in prefixes:
                ohlc_df_common[f'{prefix}_high'] = np.maximum(ohlc_df_common[f'{prefix}_high'], last_ohlc_1T_common[f'{prefix}_high'].values)
                ohlc_df_common[f'{prefix}_low'] = np.minimum(ohlc_df_common[f'{prefix}_low'], last_ohlc_1T_common[f'{prefix}_low'].values)

        # Recombine: common symbols (updated) + new symbols (keep existing values)
        ohlc_df = pd.concat([ohlc_df_common, ohlc_df_new], ignore_index=True)

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
    
    # Loop Thread for saving servercheck status
    target_market_servercheck = False
    origin_market_servercheck = False
    def save_servercheck_status():
        logger.info(f"ohlc_interval_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, interval_label: {interval_label} save_servercheck_status thread has started.")
        nonlocal target_market_servercheck, origin_market_servercheck
        while True:
            try:
                target_market_servercheck = fetch_market_servercheck(target_market_code)
                origin_market_servercheck = fetch_market_servercheck(origin_market_code)
                time.sleep(1)
            except Exception as e:
                logger.error(f"ohlc_interval_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, interval_label: {interval_label} Error in save_servercheck_status: {traceback.format_exc()}")
                time.sleep(3)
    save_servercheck_status_thread = Thread(target=save_servercheck_status, daemon=True)
    save_servercheck_status_thread.start()

    while True:
        time.sleep(loop_downtime_sec)
        try:
            # Check if one of the markets is in maintenance
            if target_market_servercheck or origin_market_servercheck:
                logger.info(f"ohlc_interval_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, interval_label: {interval_label}, has been skipped due to server check.")
                time.sleep(1)
                continue
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
            # Use .values to avoid pandas dtype inference issues with mixed types
            if mask_existing.any():
                per_interval_ohlc_df.loc[mask_existing, other_columns] = temp_df.loc[mask_existing, other_columns].values

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
                
                # Finalize interval using thread pool (reuses threads, limits concurrency)
                logger.info(f"ohlc_interval_generator|{target_market_code}:{origin_market_code}, {interval_label}, Finalizing the interval.")
                _INSERT_THREAD_POOL.submit(
                    generate_interval_kline,
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
                )

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