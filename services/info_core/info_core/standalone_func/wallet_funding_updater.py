from exchange_plugin.okx_plug import InitOkxAdaptor
from exchange_plugin.upbit_plug import InitUpbitAdaptor
from exchange_plugin.binance_plug import InitBinanceAdaptor
from exchange_plugin.bithumb_plug import InitBithumbAdaptor
from exchange_plugin.bybit_plug import InitBybitAdaptor
from exchange_plugin.gate_plug import InitGateAdaptor
from exchange_plugin.coinone_plug import InitCoinoneAdaptor
from exchange_plugin.hyperliquid_plug import InitHyperliquidAdaptor
from loggers.logger import InfoCoreLogger
import time
import datetime
from threading import Thread
from etc.db_handler.mongodb_client import InitDBClient
import pandas as pd
import traceback
from standalone_func.store_exchange_status import fetch_market_servercheck

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
        logging_dir
    )
    binance_adaptor = InitBinanceAdaptor(
        exchange_api_key_dict['binance_read_only']['api_key'],
        exchange_api_key_dict['binance_read_only']['secret_key'],
        logging_dir
    )
    bithumb_adaptor = InitBithumbAdaptor(logging_dir=logging_dir)
    bybit_adaptor = InitBybitAdaptor(
        exchange_api_key_dict['bybit_read_only']['api_key'],
        exchange_api_key_dict['bybit_read_only']['secret_key'],
        logging_dir
    )
    gate_adaptor = InitGateAdaptor(
        exchange_api_key_dict.get('gate_read_only', {}).get('api_key'),
        exchange_api_key_dict.get('gate_read_only', {}).get('secret_key'),
        logging_dir
    )
    coinone_adaptor = InitCoinoneAdaptor(
        exchange_api_key_dict.get('coinone_read_only', {}).get('api_key'),
        exchange_api_key_dict.get('coinone_read_only', {}).get('secret_key'),
        logging_dir
    )
    # Hyperliquid (DEX) - no API keys required
    hyperliquid_adaptor = InitHyperliquidAdaptor(logging_dir)

    # Initialize the database client within the child process
    db_client = InitDBClient(**db_dict)

    # Start updating funding rate and wallet status in separate threads
    update_thread_list = []
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "BINANCE", binance_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "OKX", okx_adaptor, 180), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "BYBIT", bybit_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "GATE", gate_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_fundingrate, args=(admin_id, node, acw_api, logger, db_client, "HYPERLIQUID", hyperliquid_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "UPBIT", upbit_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BINANCE", binance_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "OKX", okx_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BITHUMB", bithumb_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "BYBIT", bybit_adaptor), daemon=True))
    update_thread_list.append(Thread(target=update_wallet_status, args=(admin_id, node, acw_api, logger, db_client, "COINONE", coinone_adaptor), daemon=True))

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
                # Check whether {exchange_name}_FUTURES is in maintenance
                if futures_type == "USD_M":
                    # Hyperliquid uses USDC, other exchanges use USDT
                    quote_asset = "USDC" if exchange_name == "HYPERLIQUID" else "USDT"
                else:
                    quote_asset = "USD"
                if fetch_market_servercheck(f"{exchange_name}_{futures_type}/{quote_asset}"):
                    logger.info(f"{exchange_name}_{futures_type}/{quote_asset} is in maintenance. Skipping update_fundingrate.")
                    time.sleep(1)
                    continue
                # Fetch from MongoDB
                read_time_start = time.time()
                mongo_db = mongo_db_conn[f"{exchange_name}_fundingrate"]
                collection = mongo_db[futures_type]
                data = collection.find({})
                df = pd.DataFrame(data)
                read_time += time.time() - read_time_start

                # Fetch funding rate data from the exchange
                api_start = time.time()
                raw_funding_df = exchange_adaptor.get_fundingrate(futures_type)
                # Select columns, including funding_interval_hours if available
                base_columns = ['symbol', 'funding_rate', 'funding_time', 'base_asset', 'quote_asset', 'perpetual']
                if 'funding_interval_hours' in raw_funding_df.columns:
                    base_columns.append('funding_interval_hours')
                funding_df = raw_funding_df[base_columns]
                api_time += time.time() - api_start
                funding_df['datetime_now'] = datetime.datetime.utcnow()

                if len(df) == 0:
                    # Store initial data
                    if len(funding_df) == 0:
                        logger.info(f"update_fundingrate|{exchange_name} {futures_type}: No funding rate data available from exchange API, skipping")
                        continue
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
                    # Check if funding_interval_hours is available in the funding_df
                    # Note: After merge, if the column only exists in funding_df (not in df from MongoDB),
                    # it keeps the original name without _x suffix. Check both possibilities.
                    funding_interval_col = None
                    if 'funding_interval_hours_x' in merged_funding_df.columns:
                        funding_interval_col = 'funding_interval_hours_x'
                    elif 'funding_interval_hours' in merged_funding_df.columns:
                        funding_interval_col = 'funding_interval_hours'

                    for _, row in merged_funding_df.iterrows():
                        write_time_start = time.time()
                        if not pd.isna(row['_id']):
                            # UPDATE with new funding_rate and funding_interval_hours
                            update_fields = {'funding_rate': row['funding_rate_x'], 'datetime_now': row['datetime_now_x']}
                            if funding_interval_col and not pd.isna(row[funding_interval_col]):
                                update_fields['funding_interval_hours'] = int(row[funding_interval_col])
                            collection.update_one({'_id': row['_id']}, {'$set': update_fields})
                        else:
                            # INSERT new funding_rate
                            row_dict = row.to_dict()
                            insert_doc = {
                                'symbol': row_dict['symbol'],
                                'funding_rate': row_dict['funding_rate_x'],
                                'funding_time': row_dict['funding_time'],
                                'base_asset': row_dict['base_asset_x'],
                                'quote_asset': row_dict['quote_asset_x'],
                                'perpetual': row_dict['perpetual_x'],
                                'datetime_now': row_dict['datetime_now_x']
                            }
                            if funding_interval_col and not pd.isna(row_dict.get(funding_interval_col)):
                                insert_doc['funding_interval_hours'] = int(row_dict[funding_interval_col])
                            collection.insert_one(insert_doc)
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
            # Check whether {exchange_name}_SPOT/{quote_asset} is in maintenance
            if exchange_name in ["UPBIT", "BITHUMB", "COINONE"]:
                quote_asset = "KRW"
            else:
                quote_asset = "USDT"
            if fetch_market_servercheck(f"{exchange_name}_SPOT/{quote_asset}"):
                logger.info(f"{exchange_name}_SPOT/{quote_asset} is in maintenance. Skipping update_wallet_status.")
                time.sleep(loop_time_secs)
                continue
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