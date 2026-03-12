from threading import Thread

from standalone_func.funding_updater import start_funding_update, update_fundingrate
from standalone_func.wallet_status_updater import (
    start_wallet_status_update,
    update_wallet_status,
)


def start_wallet_funding_update(
    admin_id,
    node,
    acw_api,
    logging_dir,
    db_dict,
    exchange_api_key_dict,
    redis_dict=None,
):
    threads = [
        Thread(
            target=start_funding_update,
            args=(
                admin_id,
                node,
                acw_api,
                logging_dir,
                db_dict,
                redis_dict or {"host": "localhost", "port": 6379, "passwd": None},
                exchange_api_key_dict,
            ),
            daemon=True,
        ),
        Thread(
            target=start_wallet_status_update,
            args=(admin_id, node, acw_api, logging_dir, db_dict, exchange_api_key_dict),
            daemon=True,
        ),
    ]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()


__all__ = [
    "start_wallet_funding_update",
    "start_funding_update",
    "start_wallet_status_update",
    "update_fundingrate",
    "update_wallet_status",
]
