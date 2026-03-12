import datetime
import time
import traceback
from threading import Thread

import pandas as pd

from etc.db_handler.mongodb_client import InitDBClient
from loggers.logger import InfoCoreLogger
from standalone_func.funding_wallet_common import (
    build_exchange_adaptors,
    wallet_status_exchange_targets,
)
from standalone_func.store_exchange_status import fetch_market_servercheck


def start_wallet_status_update(admin_id, node, acw_api, logging_dir, db_dict, exchange_api_key_dict):
    logger = InfoCoreLogger("wallet_status_updater", logging_dir).logger
    adaptors = build_exchange_adaptors(exchange_api_key_dict, logging_dir)
    db_client = InitDBClient(**db_dict)
    targets = wallet_status_exchange_targets(adaptors, exchange_api_key_dict)

    if not targets:
        logger.warning("start_wallet_status_update|No wallet-status exchanges are configured.")
        while True:
            time.sleep(60)

    threads = []
    for exchange_name, adaptor, loop_time_secs in targets:
        thread = Thread(
            target=update_wallet_status,
            args=(admin_id, node, acw_api, logger, db_client, exchange_name, adaptor, loop_time_secs),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def update_wallet_status(admin_id, node, acw_api, logger, db_client, exchange_name, exchange_adaptor, loop_time_secs=60):
    logger.info("update_wallet_status|%s thread has started.", exchange_name)
    error_count = 0

    while True:
        try:
            quote_asset = "KRW" if exchange_name in ["UPBIT", "BITHUMB", "COINONE"] else "USDT"
            if fetch_market_servercheck(f"{exchange_name}_SPOT/{quote_asset}"):
                logger.info(
                    "%s_SPOT/%s is in maintenance. Skipping update_wallet_status.",
                    exchange_name,
                    quote_asset,
                )
                time.sleep(loop_time_secs)
                continue

            read_time = 0
            write_time = 0
            api_time = 0

            start = time.time()
            mongo_db_conn = db_client.get_conn()

            read_time_start = time.time()
            mongo_db = mongo_db_conn["wallet_status"]
            collection = mongo_db[f"{exchange_name}"]
            data = collection.find({})
            df = pd.DataFrame(data)
            read_time += time.time() - read_time_start

            api_start = time.time()
            wallet_status_df = exchange_adaptor.wallet_status()
            api_time += time.time() - api_start
            wallet_status_df["datetime_now"] = datetime.datetime.utcnow()

            if len(df) == 0:
                collection.insert_many(wallet_status_df.to_dict("records"))
                logger.info("Collection empty. Inserting %s wallet status to MongoDB", exchange_name)
            else:
                for _, row in wallet_status_df.iterrows():
                    write_time_start = time.time()
                    existing_records = df[
                        (df["asset"] == row["asset"]) & (df["network_type"] == row["network_type"])
                    ]
                    if len(existing_records) == 0:
                        collection.insert_one(row.to_dict())
                    elif len(existing_records) == 1:
                        collection.update_one(
                            {"asset": row["asset"], "network_type": row["network_type"]},
                            {"$set": {key: row[key] for key in row.keys() if key not in ["asset", "network_type"]}},
                        )
                    else:
                        collection.delete_many({"asset": row["asset"], "network_type": row["network_type"]})
                        collection.insert_one(row.to_dict())
                    write_time += time.time() - write_time_start

            error_count = 0
            logger.info(
                "update_wallet_status|%s took %.2f secs (read: %.2f, write: %.2f, API: %.2f)",
                exchange_name,
                time.time() - start,
                read_time,
                write_time,
                api_time,
            )
            time.sleep(loop_time_secs)
        except Exception as exc:
            error_count += 1
            if error_count >= 10:
                content = (
                    f"update_wallet_status|Exception in {exchange_name}'s update_wallet_status! "
                    f"Error: {exc}, {traceback.format_exc()}"
                )
                logger.error(content)
                acw_api.create_message_thread(
                    admin_id,
                    f"Error in {exchange_name} update_wallet_status",
                    content=content,
                )
            time.sleep(loop_time_secs)
