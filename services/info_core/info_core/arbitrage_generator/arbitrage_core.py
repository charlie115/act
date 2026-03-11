import pandas as pd
import json
import time
import datetime
from threading import Thread
import numpy as np
import os
import sys
from multiprocessing import Process
import traceback

from loggers.logger import InfoCoreLogger
from standalone_func.arbitrage_data_updater import store_funding_diff_loop, store_average_funding_loop, remove_delisted_funding_rate_loop

class InitAbitrageCore:
    def __init__(self, admin_id, node, acw_api, enabled_arbitrage_markets, mongodb_dict, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.enabled_arbitrage_markets = enabled_arbitrage_markets
        self.mongodb_dict = mongodb_dict
        self.logger = InfoCoreLogger("arbitrage_core", logging_dir).logger
        self.logger.info(f"InitArbitrageCore Started.")
        self.store_funding_diff_proc = Process(target=store_funding_diff_loop,
                                               args=(self.enabled_arbitrage_markets, self.mongodb_dict, logging_dir),
                                               daemon=True)
        self.store_funding_diff_proc.start()
        self.store_average_fundingrate_proc = Process(target=store_average_funding_loop,
                                                      args=(self.enabled_arbitrage_markets, self.mongodb_dict, logging_dir),
                                                      daemon=True)
        self.store_average_fundingrate_proc.start()
        self.remove_delisted_funding_rate_proc = Process(target=remove_delisted_funding_rate_loop,
                                                         args=(self.enabled_arbitrage_markets, self.mongodb_dict, logging_dir),
                                                         daemon=True)
        self.remove_delisted_funding_rate_proc.start()

    def check_status(self, print_result=False, include_text=False):
        process_statuses = {
            "store_funding_diff_proc": self.store_funding_diff_proc.is_alive(),
            "store_average_fundingrate_proc": self.store_average_fundingrate_proc.is_alive(),
            "remove_delisted_funding_rate_proc": self.remove_delisted_funding_rate_proc.is_alive(),
        }
        runtime_status = all(process_statuses.values())
        status_text = "\n".join(
            f"{name} is {'alive' if is_alive else 'dead'}"
            for name, is_alive in process_statuses.items()
        )
        if print_result:
            self.logger.info(status_text)
        if include_text:
            return runtime_status, status_text
        return runtime_status
