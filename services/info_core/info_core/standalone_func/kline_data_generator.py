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
from pymongo import UpdateOne
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.premium_data_generator import get_convert_rate_version, get_or_build_premium_df
from standalone_func.price_df_generator import get_market_data_signature
from standalone_func.store_exchange_status import fetch_market_servercheck

# Module-level thread pool for insert operations
# Limits concurrent inserts per process (prevents overwhelming MongoDB)
# 4 workers is optimal: balances throughput with connection pool usage
_INSERT_THREAD_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="kline_insert")
VOLATILITY_WINDOW_PREFIX = "VOLATILITY_WINDOW"


def _market_state_code(market_code):
    return market_code.split("/")[0]

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


def _build_volatility_windows_from_closed_stream(local_redis, market_code_combination, window_size):
    stream_key = _build_local_stream_key(f"INFO_CORE|{market_code_combination}_1T_closed")
    volatility_windows = {}
    closed_entries = local_redis.get_redis_client().xrevrange(
        stream_key,
        count=max(window_size, 1),
    )
    for _, entry_data in reversed(closed_entries):
        closed_df = pickle.loads(entry_data[b"data"])
        if closed_df.empty:
            continue
        for row in closed_df.itertuples(index=False):
            base_asset = getattr(row, "base_asset", None)
            sl_high = getattr(row, "SL_high", None)
            ls_low = getattr(row, "LS_low", None)
            if base_asset is None or pd.isna(sl_high) or pd.isna(ls_low):
                continue
            diff_window = volatility_windows.get(base_asset, [])
            diff_window.append(float(sl_high) - float(ls_low))
            volatility_windows[base_asset] = diff_window[-window_size:]
    return volatility_windows


def update_incremental_kline_volatility(
    market_code_combination,
    closed_ohlc_df,
    local_redis,
    mongodb_dict,
    logger,
    window_size=180,
):
    try:
        if closed_ohlc_df is None or closed_ohlc_df.empty:
            return

        cache_key = f"{VOLATILITY_WINDOW_PREFIX}|{market_code_combination}"
        cached_windows = local_redis.get_data(cache_key)
        if cached_windows is None:
            volatility_windows = _build_volatility_windows_from_closed_stream(
                local_redis,
                market_code_combination,
                window_size,
            )
        else:
            volatility_windows = pickle.loads(cached_windows)
            for row in closed_ohlc_df.itertuples(index=False):
                base_asset = getattr(row, "base_asset", None)
                sl_high = getattr(row, "SL_high", None)
                ls_low = getattr(row, "LS_low", None)
                if base_asset is None or pd.isna(sl_high) or pd.isna(ls_low):
                    continue
                diff_window = volatility_windows.get(base_asset, [])
                diff_window.append(float(sl_high) - float(ls_low))
                volatility_windows[base_asset] = diff_window[-window_size:]

        local_redis.set_data(cache_key, pickle.dumps(volatility_windows))

        database = market_code_combination.replace("/", "__").replace(":", "-")
        mongo_db_client = InitDBClient(**mongodb_dict)
        mongo_db_conn = mongo_db_client.get_conn()
        collection = mongo_db_conn[database]["volatility_info"]
        current_datetime = datetime.datetime.utcnow()

        operations = []
        for base_asset, diff_window in volatility_windows.items():
            if not diff_window:
                continue
            operations.append(
                UpdateOne(
                    {"base_asset": base_asset},
                    {
                        "$set": {
                            "base_asset": base_asset,
                            "mean_diff": float(np.mean(diff_window)),
                            "window_size": min(len(diff_window), window_size),
                            "datetime_now": current_datetime,
                        }
                    },
                    upsert=True,
                )
            )

        if operations:
            collection.bulk_write(operations, ordered=False)
    except Exception:
        logger.error(
            f"update_incremental_kline_volatility|{market_code_combination}|{traceback.format_exc()}"
        )

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

    total_inserted = 0
    remaining_docs = docs

    for attempt in range(max_retries):
        try:
            result = collection.insert_many(remaining_docs, ordered=False)
            return total_inserted + len(result.inserted_ids), False
        except BulkWriteError as bwe:
            inserted = bwe.details.get('nInserted', 0)
            total_inserted += inserted

            if total_inserted >= len(docs):
                return total_inserted, False

            # Retry only documents that failed with transient errors (not duplicate key)
            write_errors = bwe.details.get('writeErrors', [])
            failed_indices = {e['index'] for e in write_errors if e.get('code') != 11000}
            if not failed_indices:
                # All failures were duplicate keys — nothing to retry
                return total_inserted, False

            remaining_docs = [remaining_docs[i] for i in failed_indices]

            if attempt == max_retries - 1:
                return total_inserted, True
            time.sleep(0.1 * (attempt + 1))
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(0.1 * (attempt + 1))

    return total_inserted, True


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
    local_redis = RedisHelper()  # For caching last timestamps
    try:
        service_name = channel_name.split('|')[0].lower()
        market_kline_name = channel_name.split('|')[1]
        market_code_combination = '_'.join(market_kline_name.split('_')[:-2])
        converted_market_code_combination = market_code_combination.replace(':', '-').replace('/', '__')
        kline_type = market_kline_name.split('_')[-2]

        target_market_code, origin_market_code = market_code_combination.split(":")
        if fetch_market_servercheck(target_market_code) or fetch_market_servercheck(origin_market_code):
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
                # count may legitimately exceed len(inserted_coin_list) when
                # multiple candles close for the same asset in a single cycle.
                # Only log as warning, not error, since this is expected behavior.
                logger.warning(f"kline count ({count}) differs from unique assets ({len(inserted_coin_list)}) - likely multiple candles per asset")
    except Exception:
        logger.error(f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()}")
        acw_api.create_message_thread(admin_id, 'Error in insert_kline_to_db', content=f"insert_kline_to_db|Error in insert_kline_to_db: {traceback.format_exc()[:1995]}")


def _empty_interval_state(all_columns):
    interval_state_df = pd.DataFrame(columns=all_columns)
    for col in all_columns:
        interval_state_df[col] = pd.Series(dtype="float64")
    return interval_state_df


def _extract_snapshot_minute(snapshot_df):
    snapshot_minute = pd.to_datetime(snapshot_df["datetime_now"]).iloc[0]
    if snapshot_minute.tzinfo is not None:
        snapshot_minute = snapshot_minute.replace(tzinfo=None)
    return snapshot_minute.replace(second=0, microsecond=0)


def _build_local_stream_key(stream_key):
    return f"{stream_key}|local_stream"


def _publish_kline_stream(
    local_redis,
    remote_redis,
    stream_key,
    snapshot_df,
    maxlen=10,
    store_local_key=False,
    publish_local_stream=True,
):
    pickled_snapshot_df = pickle.dumps(snapshot_df)
    if store_local_key or publish_local_stream:
        local_client = local_redis.get_redis_client()
        local_pipeline = local_client.pipeline(transaction=False)
        if store_local_key:
            local_pipeline.set(stream_key, pickled_snapshot_df)
        if publish_local_stream:
            local_pipeline.xadd(
                _build_local_stream_key(stream_key),
                {"data": pickled_snapshot_df},
                maxlen=maxlen,
                approximate=True,
            )
        local_pipeline.execute()
    remote_redis.get_redis_client().xadd(
        stream_key,
        {"data": pickled_snapshot_df},
        maxlen=maxlen,
        approximate=True,
    )
    return pickled_snapshot_df


def _apply_1t_snapshot_to_interval_state(interval_state_df, snapshot_df, prefixes, other_columns):
    if snapshot_df is None or snapshot_df.empty:
        return interval_state_df

    ohlc_columns = [f"{prefix}_{col}" for prefix in prefixes for col in ["open", "high", "low", "close"]]
    all_columns = ohlc_columns + other_columns
    if interval_state_df is None or len(interval_state_df.columns) == 0:
        interval_state_df = _empty_interval_state(all_columns)

    temp_df = snapshot_df.set_index("base_asset")[all_columns]
    interval_state_df = interval_state_df.reindex(temp_df.index)

    mask_new = interval_state_df["LS_open"].isna()
    if mask_new.any():
        interval_state_df.loc[mask_new, ohlc_columns] = temp_df.loc[mask_new, ohlc_columns].astype("float64")
        interval_state_df.loc[mask_new, other_columns] = temp_df.loc[mask_new, other_columns].astype("float64")

    mask_existing = ~mask_new
    for prefix in prefixes:
        interval_state_df.loc[mask_existing, f"{prefix}_high"] = np.maximum(
            interval_state_df.loc[mask_existing, f"{prefix}_high"],
            temp_df.loc[mask_existing, f"{prefix}_high"],
        )
        interval_state_df.loc[mask_existing, f"{prefix}_low"] = np.minimum(
            interval_state_df.loc[mask_existing, f"{prefix}_low"],
            temp_df.loc[mask_existing, f"{prefix}_low"],
        )
        interval_state_df.loc[mask_existing, f"{prefix}_close"] = temp_df.loc[mask_existing, f"{prefix}_close"]

    if mask_existing.any():
        interval_state_df.loc[mask_existing, other_columns] = temp_df.loc[mask_existing, other_columns].values

    return interval_state_df

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
    local_redis.fallback_redis_client = remote_redis
    datetime_now = datetime.datetime.utcnow()
    per_minute_ohlc_df = pd.DataFrame()

    # Initialize columns outside the loop
    prefixes = ['tp', 'LS', 'SL']
    price_columns = ['tp_premium', 'LS_premium', 'SL_premium']
    other_columns = ['tp', 'scr', 'atp24h', 'converted_tp']
    ohlc_columns = [f"{prefix}_{col}" for prefix in prefixes for col in ['open', 'high', 'low', 'close']]

    for col in ohlc_columns + other_columns:
        per_minute_ohlc_df[col] = np.nan  # Initialize columns with NaN

    # Local cache for dollar price (avoid Redis round-trip every 50ms)
    _cached_dollar_price = None
    _cached_dollar_time = 0
    _DOLLAR_CACHE_TTL = 10  # seconds

    def _get_dollar_price():
        nonlocal _cached_dollar_price, _cached_dollar_time
        now = time.time()
        if _cached_dollar_price is None or (now - _cached_dollar_time) > _DOLLAR_CACHE_TTL:
            _cached_dollar_price = get_dollar_dict(local_redis)['price']
            _cached_dollar_time = now
        return _cached_dollar_price

    one_t_now_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_now"
    one_t_closed_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_closed"
    remote_redis.get_redis_client().xtrim(one_t_now_key, maxlen=max_length)
    local_redis.get_redis_client().xtrim(_build_local_stream_key(one_t_now_key), maxlen=max_length)
    remote_redis.get_redis_client().xtrim(one_t_closed_key, maxlen=max_length)
    local_redis.get_redis_client().xtrim(_build_local_stream_key(one_t_closed_key), maxlen=max_length)
    
    # Initialize convert_rate_dict
    market_code_combination = f"{target_market_code}:{origin_market_code}"
    last_convert_rate_version = None
    while True:
        fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
        if fetched_convert_rate_dict:
            fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
            last_convert_rate_version = get_convert_rate_version(local_redis, market_code_combination)
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
    target_market_state_code = _market_state_code(target_market_code)
    origin_market_state_code = _market_state_code(origin_market_code)
    last_source_signature = None
    last_prices_index = None
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
            
            datetime_before = datetime_now.replace(second=0, microsecond=0)
            datetime_now = datetime.datetime.utcnow().replace(second=0, microsecond=0)

            current_convert_rate_version = get_convert_rate_version(local_redis, market_code_combination)
            if current_convert_rate_version != last_convert_rate_version:
                fetched_convert_rate_dict = local_redis.hgetall_dict('convert_rate_dict')
                fetched_convert_rate_dict = {key.decode('utf-8'): float(value) for key, value in fetched_convert_rate_dict.items()}
                last_convert_rate_version = current_convert_rate_version

            source_signature = (
                get_market_data_signature(local_redis, target_market_state_code),
                get_market_data_signature(local_redis, origin_market_state_code),
                current_convert_rate_version,
            )
            minute_changed = datetime_before != datetime_now
            if not minute_changed and source_signature == last_source_signature:
                continue
            
            # # Performance tracking - premium data fetch
            # premium_fetch_start = time.time()
            premium_df = get_or_build_premium_df(
                local_redis,
                market_code_combination,
                logger=logger,
                convert_rate_dict=fetched_convert_rate_dict,
                target_market_code=target_market_code,
                origin_market_code=origin_market_code,
            )
            premium_df['datetime_now'] = datetime_now
            # premium_fetch_time = time.time() - premium_fetch_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Fetching premium data took {premium_fetch_time:.4f} seconds")

            current_index = pd.Index(
                premium_df["base_asset"].to_numpy(copy=False),
                name="base_asset",
            )
            price_matrix = premium_df[price_columns].to_numpy(dtype="float64", copy=False)
            other_matrix = premium_df[other_columns].to_numpy(copy=False)

            # Keep only base_assets that are in prices_df (remove delisted cryptos)
            if (
                last_prices_index is None
                or per_minute_ohlc_df.empty
                or not current_index.equals(last_prices_index)
            ):
                per_minute_ohlc_df = per_minute_ohlc_df.reindex(current_index)
                last_prices_index = current_index.copy()

            # Identify new base_assets (where 'LS_open' is NaN)
            mask_new = per_minute_ohlc_df['LS_open'].isna().to_numpy()
            # prep_time = time.time() - prep_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Data preparation took {prep_time:.4f} seconds")

            # # Performance tracking - process new assets
            # new_assets_start = time.time()
            # For new base_assets, initialize OHLC values
            if mask_new.any():
                new_index = current_index[mask_new]
                
                # Create a DataFrame for the OHLC columns
                # This will have columns like 'tp_open', 'tp_high', ..., 'SL_close'
                ohlc_cols = [f'{prefix}_{col}' for prefix in prefixes for col in ['open', 'high', 'low', 'close']]
                
                # Repeat the prices for 'open', 'high', 'low', 'close'
                # The shape of new_prices.values is (num_assets, num_prefixes)
                # We need to repeat each price 4 times (for 'open', 'high', 'low', 'close')
                repeated_prices = np.repeat(price_matrix[mask_new], 4, axis=1)
                
                # Assign the new OHLC values to per_minute_ohlc_df
                per_minute_ohlc_df.loc[new_index, ohlc_cols] = repeated_prices
            # new_assets_time = time.time() - new_assets_start
            # if mask_new.any():
            #     logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Processing {mask_new.sum()} new assets took {new_assets_time:.4f} seconds")

            # # Performance tracking - update OHLC values
            # update_ohlc_start = time.time()
            for prefix, price_column in zip(prefixes, price_columns):
                price_values = premium_df[price_column].to_numpy(dtype="float64", copy=False)
                high_values = per_minute_ohlc_df[f"{prefix}_high"].to_numpy(dtype="float64", copy=False)
                low_values = per_minute_ohlc_df[f"{prefix}_low"].to_numpy(dtype="float64", copy=False)
                close_values = per_minute_ohlc_df[f"{prefix}_close"].to_numpy(dtype="float64", copy=False)
                np.maximum(high_values, price_values, out=high_values)
                np.minimum(low_values, price_values, out=low_values)
                close_values[:] = price_values

            # Update other columns
            per_minute_ohlc_df[other_columns] = other_matrix
            # update_ohlc_time = time.time() - update_ohlc_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Updating OHLC values took {update_ohlc_time:.4f} seconds")

            # # Performance tracking - Redis update
            # redis_update_start = time.time()
            # Update per_minute_ohlc_df in the Redis 'now' data
            ohlc_now_df = per_minute_ohlc_df.reset_index()
            ohlc_now_df['datetime_now'] = datetime_now
            ohlc_now_df['dollar'] = _get_dollar_price()
            _publish_kline_stream(
                local_redis,
                remote_redis,
                one_t_now_key,
                ohlc_now_df,
                maxlen=10,
                store_local_key=True,
            )
            # redis_update_time = time.time() - redis_update_start
            # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Redis updates took {redis_update_time:.4f} seconds")
            last_source_signature = source_signature

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
                ohlc_df['dollar'] = _get_dollar_price()
                ohlc_df['closed'] = True

                _publish_kline_stream(
                    local_redis,
                    remote_redis,
                    one_t_closed_key,
                    ohlc_df,
                    maxlen=max_length,
                )
                # # TEST
                # minute_transition_time = time.time() - minute_transition_start
                # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Minute transition processing took {minute_transition_time:.4f} seconds")
                logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, Finalized {len(ohlc_df)} klines for {ohlc_df['base_asset'].nunique()} unique base_assets")
                
                # Insert into the database using thread pool (reuses threads, limits concurrency)
                _INSERT_THREAD_POOL.submit(
                    insert_kline_to_db,
                    ohlc_df,
                    f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_kline",
                    acw_api,
                    redis_dict,
                    mongodb_dict,
                    admin_id,
                    node,
                    logger
                )
                update_incremental_kline_volatility(
                    f"{target_market_code}:{origin_market_code}",
                    ohlc_df,
                    local_redis,
                    mongodb_dict,
                    logger,
                )
                # db_insert_time = time.time() - db_insert_start
                # logger.info(f"ohlc_1T_generator|{target_market_code}:{origin_market_code}, DB insert thread creation took {db_insert_time:.4f} seconds")
                
                # Reset per_minute_ohlc_df for the new minute
                per_minute_ohlc_df = pd.DataFrame()
                last_prices_index = None
                # Re-initialize columns for the new DataFrame
                for col in ohlc_columns + other_columns:
                    per_minute_ohlc_df[col] = np.nan
                    
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
        logger.info(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, Finalizing interval snapshot.")
        remote_redis = RedisHelper(**redis_dict)
        local_redis = RedisHelper()
        local_redis.fallback_redis_client = remote_redis

        if per_interval_ohlc_df is None or per_interval_ohlc_df.empty:
            logger.warning(f"generate_interval_kline|{target_market_code}:{origin_market_code}, {interval_label}, Empty interval state.")
            return

        ohlc_df = per_interval_ohlc_df.reset_index()
        ohlc_df["datetime_now"] = previous_interval_start
        ohlc_df["dollar"] = get_dollar_dict(local_redis)["price"]
        ohlc_df["closed"] = True

        closed_stream_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_closed"
        _publish_kline_stream(
            local_redis,
            remote_redis,
            closed_stream_key,
            ohlc_df,
            maxlen=max_length,
        )

        insert_kline_to_db(
            ohlc_df,
            f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_kline",
            acw_api,
            redis_dict,
            mongodb_dict,
            admin_id,
            node,
            logger,
        )
    except Exception:
        content = f"ohlc_{interval_label}_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_{interval_label}_generator: {traceback.format_exc()}"
        logger.error(content)
        acw_api.create_message_thread(admin_id, f"Error in ohlc_{interval_label}_generator", content=content[:1995])
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
    local_redis.fallback_redis_client = remote_redis
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
        return datetime.datetime.utcfromtimestamp(interval_start_timestamp).replace(tzinfo=None)

    # Initialize current interval start
    current_interval_start = None

    # Initialize columns outside the loop
    prefixes = ['tp', 'LS', 'SL']
    ohlc_columns = [f"{prefix}_{col}" for prefix in prefixes for col in ['open', 'high', 'low', 'close']]
    other_columns = ['tp', 'scr', 'atp24h', 'converted_tp']
    all_columns = ohlc_columns + other_columns

    per_interval_ohlc_df = _empty_interval_state(all_columns)
    one_t_now_stream_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_now"
    one_t_closed_stream_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_1T_closed"
    interval_now_stream_key = f"INFO_CORE|{target_market_code}:{origin_market_code}_{interval_label}_now"
    last_stream_ids = {
        _build_local_stream_key(one_t_closed_stream_key): "$",
        _build_local_stream_key(one_t_now_stream_key): "$",
    }
    last_finalized_interval_start = None

    def publish_interval_now():
        if current_interval_start is None or per_interval_ohlc_df.empty:
            return
        ohlc_now_df = per_interval_ohlc_df.reset_index()
        ohlc_now_df["datetime_now"] = current_interval_start
        _publish_kline_stream(
            local_redis,
            remote_redis,
            interval_now_stream_key,
            ohlc_now_df,
            maxlen=10,
            store_local_key=True,
        )

    def apply_snapshot(snapshot_df):
        nonlocal per_interval_ohlc_df
        per_interval_ohlc_df = _apply_1t_snapshot_to_interval_state(
            per_interval_ohlc_df,
            snapshot_df,
            prefixes,
            other_columns,
        )

    def process_now_snapshot(snapshot_df):
        nonlocal current_interval_start, per_interval_ohlc_df
        snapshot_minute = _extract_snapshot_minute(snapshot_df)
        snapshot_interval_start = get_interval_start(snapshot_minute)

        if (
            last_finalized_interval_start is not None
            and snapshot_interval_start <= last_finalized_interval_start
        ):
            return

        if current_interval_start is None or current_interval_start != snapshot_interval_start:
            current_interval_start = snapshot_interval_start
            per_interval_ohlc_df = _empty_interval_state(all_columns)

        apply_snapshot(snapshot_df)
        publish_interval_now()

    def process_closed_snapshot(snapshot_df):
        nonlocal current_interval_start, per_interval_ohlc_df, last_finalized_interval_start
        snapshot_minute = _extract_snapshot_minute(snapshot_df)
        snapshot_interval_start = get_interval_start(snapshot_minute)

        if (
            last_finalized_interval_start is not None
            and snapshot_interval_start <= last_finalized_interval_start
        ):
            return

        if current_interval_start is None or current_interval_start != snapshot_interval_start:
            current_interval_start = snapshot_interval_start
            per_interval_ohlc_df = _empty_interval_state(all_columns)

        apply_snapshot(snapshot_df)
        publish_interval_now()

        if snapshot_minute == snapshot_interval_start + datetime.timedelta(minutes=interval_minutes - 1):
            logger.info(f"ohlc_interval_generator|{target_market_code}:{origin_market_code}, {interval_label}, Finalizing interval from 1T_closed.")
            _INSERT_THREAD_POOL.submit(
                generate_interval_kline,
                per_interval_ohlc_df.copy(),
                snapshot_interval_start,
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
                max_length,
            )
            last_finalized_interval_start = snapshot_interval_start
            current_interval_start = None
            per_interval_ohlc_df = _empty_interval_state(all_columns)

    # Warm the current interval state from recent 1T closed entries and the latest 1T now snapshot.
    seed_interval_start = get_interval_start(datetime_now)
    try:
        closed_entries = local_redis.get_redis_client().xrevrange(
            _build_local_stream_key(one_t_closed_stream_key),
            count=max(interval_minutes, 1),
        )
        current_interval_start = seed_interval_start
        for _, entry_data in reversed(closed_entries):
            snapshot_df = pickle.loads(entry_data[b"data"])
            if get_interval_start(_extract_snapshot_minute(snapshot_df)) == seed_interval_start:
                apply_snapshot(snapshot_df)

        pickled_1t_now = local_redis.get_data(one_t_now_stream_key)
        if pickled_1t_now is not None:
            snapshot_df = pickle.loads(pickled_1t_now)
            if get_interval_start(_extract_snapshot_minute(snapshot_df)) == seed_interval_start:
                apply_snapshot(snapshot_df)
                publish_interval_now()
    except Exception:
        logger.error(
            f"ohlc_interval_generator|{target_market_code}:{origin_market_code}, {interval_label}, Error warming state: {traceback.format_exc()}"
        )
        current_interval_start = None
        per_interval_ohlc_df = _empty_interval_state(all_columns)
    
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
        try:
            # Check if one of the markets is in maintenance
            if target_market_servercheck or origin_market_servercheck:
                time.sleep(1)
                continue
            stream_response = local_redis.get_redis_client().xread(
                streams=last_stream_ids,
                count=20,
                block=max(int(loop_downtime_sec * 1000), 100),
            )
            if not stream_response:
                continue

            closed_entries = []
            now_entries = []
            for stream_key, entries in stream_response:
                normalized_stream_key = (
                    stream_key.decode("utf-8")
                    if isinstance(stream_key, bytes)
                    else stream_key
                )
                if not entries:
                    continue
                last_entry_id = entries[-1][0]
                if isinstance(last_entry_id, bytes):
                    last_entry_id = last_entry_id.decode("utf-8")
                last_stream_ids[normalized_stream_key] = last_entry_id

                if normalized_stream_key == _build_local_stream_key(one_t_closed_stream_key):
                    closed_entries.extend(entries)
                elif normalized_stream_key == _build_local_stream_key(one_t_now_stream_key):
                    now_entries.extend(entries)

            for _, entry_data in closed_entries:
                snapshot_df = pickle.loads(entry_data[b"data"])
                process_closed_snapshot(snapshot_df)

            for _, entry_data in now_entries:
                snapshot_df = pickle.loads(entry_data[b"data"])
                process_now_snapshot(snapshot_df)

        except Exception:
            content = f"ohlc_{interval_label}_generator|target_market_code:{target_market_code}, origin_market_code:{origin_market_code}, Error in ohlc_{interval_label}_generator: {traceback.format_exc()}"
            logger.error(content)
            acw_api.create_message_thread(admin_id, f'Error in ohlc_{interval_label}_generator', content=content[:1995])
            time.sleep(3)
