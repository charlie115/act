import datetime
import pickle
import time
import traceback
from threading import Thread

import pandas as pd

from etc.db_handler.mongodb_client import InitDBClient
from etc.redis_connector.redis_helper import RedisHelper
from loggers.logger import InfoCoreLogger
from standalone_func.funding_wallet_common import (
    build_exchange_adaptors,
    funding_exchange_targets,
)
from standalone_func.store_exchange_status import fetch_market_servercheck

FUNDING_LATEST_PREFIX = "INFO_CORE|FUNDING_LATEST|"


def _funding_latest_key(exchange_name, futures_type, quote_asset):
    return f"{FUNDING_LATEST_PREFIX}{exchange_name}_{futures_type}/{quote_asset}"


def _store_latest_funding_snapshot(redis_client, exchange_name, futures_type, quote_asset, funding_df, ttl_seconds=120):
    if funding_df.empty:
        return

    latest_docs = {}
    for row in funding_df.itertuples(index=False):
        doc = {
            "symbol": row.symbol,
            "funding_rate": row.funding_rate,
            "funding_time": row.funding_time,
            "datetime_now": row.datetime_now,
        }
        if hasattr(row, "funding_interval_hours"):
            doc["funding_interval_hours"] = row.funding_interval_hours
        latest_docs[row.base_asset] = [doc]

    redis_client.set_data(
        _funding_latest_key(exchange_name, futures_type, quote_asset),
        pickle.dumps(latest_docs),
        ex=ttl_seconds,
    )


def start_funding_update(admin_id, node, acw_api, logging_dir, db_dict, redis_dict, exchange_api_key_dict):
    logger = InfoCoreLogger("funding_updater", logging_dir).logger
    adaptors = build_exchange_adaptors(exchange_api_key_dict, logging_dir)
    db_client = InitDBClient(**db_dict)
    remote_redis = RedisHelper(**redis_dict)

    threads = []
    for exchange_name, adaptor, loop_time_secs in funding_exchange_targets(adaptors):
        thread = Thread(
            target=update_fundingrate,
            args=(
                admin_id,
                node,
                acw_api,
                logger,
                db_client,
                remote_redis,
                exchange_name,
                adaptor,
                loop_time_secs,
            ),
            daemon=True,
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()


def update_fundingrate(
    admin_id,
    node,
    acw_api,
    logger,
    db_client,
    redis_client,
    exchange_name,
    exchange_adaptor,
    loop_time_secs=60,
):
    logger.info("update_fundingrate|%s thread has started.", exchange_name)

    while True:
        try:
            read_time = 0
            write_time = 0
            calculate_time = 0
            api_time = 0

            start = time.time()
            mongo_db_conn = db_client.get_conn()
            for futures_type in ["USD_M", "COIN_M"]:
                quote_asset = "USDC" if exchange_name == "HYPERLIQUID" and futures_type == "USD_M" else ("USDT" if futures_type == "USD_M" else "USD")
                if fetch_market_servercheck(f"{exchange_name}_{futures_type}/{quote_asset}"):
                    logger.info(
                        "%s_%s/%s is in maintenance. Skipping update_fundingrate.",
                        exchange_name,
                        futures_type,
                        quote_asset,
                    )
                    time.sleep(1)
                    continue

                read_time_start = time.time()
                mongo_db = mongo_db_conn[f"{exchange_name}_fundingrate"]
                collection = mongo_db[futures_type]
                data = collection.find({})
                df = pd.DataFrame(data)
                read_time += time.time() - read_time_start

                api_start = time.time()
                raw_funding_df = exchange_adaptor.get_fundingrate(futures_type)
                base_columns = ["symbol", "funding_rate", "funding_time", "base_asset", "quote_asset", "perpetual"]
                if "funding_interval_hours" in raw_funding_df.columns:
                    base_columns.append("funding_interval_hours")
                funding_df = raw_funding_df[base_columns]
                api_time += time.time() - api_start
                funding_df["datetime_now"] = datetime.datetime.utcnow()
                _store_latest_funding_snapshot(
                    redis_client,
                    exchange_name,
                    futures_type,
                    quote_asset,
                    funding_df,
                )

                if len(df) == 0:
                    if len(funding_df) == 0:
                        logger.info(
                            "update_fundingrate|%s %s: No funding rate data available from exchange API, skipping",
                            exchange_name,
                            futures_type,
                        )
                        continue
                    collection.insert_many(funding_df.to_dict("records"))
                    logger.info("Collection empty. Inserting %s funding rate to MongoDB", futures_type)
                    continue

                calculate_time_start = time.time()
                funding_df["funding_time"] = pd.to_datetime(funding_df["funding_time"], errors="coerce")
                df["funding_time"] = pd.to_datetime(df["funding_time"], errors="coerce")
                merged_funding_df = funding_df.merge(df, on=["symbol", "funding_time"], how="left")
                calculate_time += time.time() - calculate_time_start

                funding_interval_col = None
                if "funding_interval_hours_x" in merged_funding_df.columns:
                    funding_interval_col = "funding_interval_hours_x"
                elif "funding_interval_hours" in merged_funding_df.columns:
                    funding_interval_col = "funding_interval_hours"

                for _, row in merged_funding_df.iterrows():
                    write_time_start = time.time()
                    if not pd.isna(row["_id"]):
                        update_fields = {
                            "funding_rate": row["funding_rate_x"],
                            "datetime_now": row["datetime_now_x"],
                        }
                        if funding_interval_col and not pd.isna(row[funding_interval_col]):
                            update_fields["funding_interval_hours"] = int(row[funding_interval_col])
                        collection.update_one({"_id": row["_id"]}, {"$set": update_fields})
                    else:
                        row_dict = row.to_dict()
                        insert_doc = {
                            "symbol": row_dict["symbol"],
                            "funding_rate": row_dict["funding_rate_x"],
                            "funding_time": row_dict["funding_time"],
                            "base_asset": row_dict["base_asset_x"],
                            "quote_asset": row_dict["quote_asset_x"],
                            "perpetual": row_dict["perpetual_x"],
                            "datetime_now": row_dict["datetime_now_x"],
                        }
                        if funding_interval_col and not pd.isna(row_dict.get(funding_interval_col)):
                            insert_doc["funding_interval_hours"] = int(row_dict[funding_interval_col])
                        collection.insert_one(insert_doc)
                    write_time += time.time() - write_time_start

            logger.info(
                "update_fundingrate|%s took %.2f secs (read: %.2f, write: %.2f, calc: %.2f, API: %.2f)",
                exchange_name,
                time.time() - start,
                read_time,
                write_time,
                calculate_time,
                api_time,
            )
            time.sleep(loop_time_secs)
        except Exception as exc:
            content = (
                f"update_fundingrate|Exception occurred updating {exchange_name}'s funding rate! "
                f"Error: {exc}, {traceback.format_exc()}"
            )
            logger.error(content)
            acw_api.create_message_thread(admin_id, "Error in update_fundingrate", content=content)
            time.sleep(loop_time_secs)
