from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_plugin.bithumb_plug import InitBithumbAdaptor
from exchange_plugin.bybit_plug import InitBybitAdaptor
from loggers.logger import InfoCoreLogger
import time
import datetime
from threading import Thread
from etc.db_handler.mongodb_client import InitDBClient
import pandas as pd
import traceback

def start_wallet_funding_update(admin_id, node, acw_api, logging_dir, db_dict, exchange_api_key_dict):
    # Reinitialize the logger inside the function
    logger = InfoCoreLogger("info_core", logging_dir).logger

    # Initialize exchange adaptors within the child process
    okx_adaptor = InitOkxAdaptor(
        exchange_api_key_dict['okx_read_only']['api_key'],
        exchange_api_key_dict['okx_read_only']['secret_key'],
        exchange_api_key_dict['okx_read_only']['passphrase'],
        logging_dir=logging_dir
    )
    upbit_adaptor = InitUpbitAdaptor(
        exchange_api_key_dict['upbit_read_only']['api_key'],
        exchange_api_key_dict['upbit_read_only']['secret_key'],
        {},  # Empty info_dict
        logging_dir
    )
    binance_adaptor = InitBinanceAdaptor(
        exchange_api_key_dict['binance_read_only']['api_key'],
        exchange_api_key_dict['binance_read_only']['secret_key'],
        {},  # Empty info_dict
        logging_dir
    )
    bithumb_adaptor = InitBithumbAdaptor(logging_dir=logging_dir)
    bybit_adaptor = InitBybitAdaptor(
        exchange_api_key_dict['bybit_read_only']['api_key'],
        exchange_api_key_dict['bybit_read_only']['secret_key'],
        {},  # Empty info_dict
        logging_dir
    )

    # Initialize the database client within the child process
    db_client = InitDBClient(**db_dict)

    # Start updating funding rate and wallet status in separate threads
    update_thread_list = []
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "BINANCE", binance_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "OKX", okx_adaptor, 180), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "BYBIT", bybit_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "UPBIT", upbit_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BINANCE", binance_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "OKX", okx_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BITHUMB", bithumb_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BYBIT", bybit_adaptor), daemon=True))

    for each_thread in update_thread_list:
        each_thread.start()
    for each_thread in update_thread_list:
        each_thread.join()

# Modify update_fundingrate to accept exchange_adaptor
def update_fundingrate(admin_id, node, acw_api, logger, db_client, exchange_name, exchange_adaptor, loop_time_secs=60):
    logger.info(f"update_fundingrate|{exchange_name} update_fundingrate thread has started.")

    while True:
        try:
            read_time = 0
            write_time = 0
            calculate_time = 0
            api_time = 0

            start = time.time()
            mongo_db_conn = db_client.get_conn()
            for futures_type in ["USD_M", "COIN_M"]:
                # Fetch from MongoDB
                read_time_start = time.time()
                mongo_db = mongo_db_conn[f"{exchange_name}_fundingrate"]
                collection = mongo_db[futures_type]
                data = collection.find({})
                df = pd.DataFrame(data)
                read_time += time.time() - read_time_start

                # Fetch funding rate data from the exchange
                api_start = time.time()
                funding_df = exchange_adaptor.get_fundingrate(futures_type)[['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual']]
                api_time += time.time() - api_start
                funding_df['datetime_now'] = datetime.datetime.utcnow()

                if len(df) == 0:
                    # Store initial data
                    funding_dict = funding_df.to_dict('records')
                    collection.insert_many(funding_dict)
                    logger.info(f"Collection empty. Inserting {futures_type} funding rate to MongoDB")
                else:
                    calculate_time_start = time.time()
                    # Set the dtype of funding_time to datetime64[ns]
                    funding_df['funding_time'] = pd.to_datetime(funding_df['funding_time'], errors='coerce')
                    df['funding_time'] = pd.to_datetime(df['funding_time'], errors='coerce')
                    merged_funding_df = funding_df.merge(df, on=['symbol', 'funding_time'], how='left')
                    calculate_time += time.time() - calculate_time_start
                    for _, row in merged_funding_df.iterrows():
                        write_time_start = time.time()
                        if not pd.isna(row['_id']):
                            # UPDATE with new funding_rate
                            collection.update_one({'_id': row['_id']}, {'$set': {'funding_rate': row['funding_rate_x'], 'datetime_now': row['datetime_now_x']}})
                        else:
                            # INSERT new funding_rate
                            row_dict = row.to_dict()
                            collection.insert_one({
                                'symbol': row_dict['symbol'],
                                'funding_rate': row_dict['funding_rate_x'],
                                'funding_time': row_dict['funding_time'],
                                'base_asset': row_dict['base_asset_x'],
                                'quote_asset': row_dict['quote_asset_x'],
                                'perpetual': row_dict['perpetual_x'],
                                'datetime_now': row_dict['datetime_now_x']
                            })
                        write_time += time.time() - write_time_start

            logger.info(f"update_fundingrate|{exchange_name} took {time.time() - start:.2f} secs (read: {read_time:.2f}, write: {write_time:.2f}, calc: {calculate_time:.2f}, API: {api_time:.2f})")
            time.sleep(loop_time_secs)
        except Exception as e:
            content = f"update_fundingrate|Exception occurred updating {exchange_name}'s funding rate! Error: {e}, {traceback.format_exc()}"
            logger.error(content)
            acw_api.create_message_thread(admin_id, "Error in update_fundingrate", content=content)
            time.sleep(loop_time_secs)

# Modify update_wallet_status to accept exchange_adaptor
def update_wallet_status(admin_id, node, acw_api, logger, db_client, exchange_name, exchange_adaptor, loop_time_secs=60):
    logger.info(f"update_wallet_status|{exchange_name} update_wallet_status thread has started.")
    error_count = 0

    while True:
        try:
            read_time = 0
            write_time = 0
            calculate_time = 0
            api_time = 0

            start = time.time()
            mongo_db_conn = db_client.get_conn()
            # Fetch from MongoDB
            read_time_start = time.time()
            mongo_db = mongo_db_conn["wallet_status"]
            collection = mongo_db[f"{exchange_name}"]
            data = collection.find({})
            df = pd.DataFrame(data)
            read_time += time.time() - read_time_start

            # Fetch wallet status from the exchange
            api_start = time.time()
            wallet_status_df = exchange_adaptor.wallet_status()
            api_time += time.time() - api_start
            wallet_status_df['datetime_now'] = datetime.datetime.utcnow()

            if len(df) == 0:
                # Store initial data
                wallet_status_dict = wallet_status_df.to_dict('records')
                collection.insert_many(wallet_status_dict)
                logger.info(f"Collection empty. Inserting {exchange_name}'s wallet status to MongoDB")
            else:
                for _, row in wallet_status_df.iterrows():
                    write_time_start = time.time()
                    existing_records = df[(df['asset'] == row['asset']) & (df['network_type'] == row['network_type'])]
                    if len(existing_records) == 0:
                        collection.insert_one(row.to_dict())
                    elif len(existing_records) == 1:
                        collection.update_one(
                            {'asset': row['asset'], 'network_type': row['network_type']},
                            {'$set': {k: row[k] for k in row.keys() if k not in ['asset', 'network_type']}}
                        )
                    else:
                        collection.delete_many({'asset': row['asset'], 'network_type': row['network_type']})
                        collection.insert_one(row.to_dict())
                    write_time += time.time() - write_time_start

            error_count = 0
            logger.info(f"update_wallet_status|{exchange_name} took {time.time() - start:.2f} secs (read: {read_time:.2f}, write: {write_time:.2f}, calc: {calculate_time:.2f}, API: {api_time:.2f})")
            time.sleep(loop_time_secs)
        except Exception as e:
            error_count += 1
            if error_count >= 10:
                content = f"update_wallet_status|Exception in {exchange_name}'s update_wallet_status! Error: {e}, {traceback.format_exc()}"
                logger.error(content)
                acw_api.create_message_thread(admin_id, f"Error in {exchange_name} update_wallet_status", content=content)
            time.sleep(loop_time_secs)