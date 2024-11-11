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

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger
from standalone_func.arbitrage_data_updater import store_funding_diff_loop, store_average_funding_loop, remove_delisted_funding_rate_loop

class InitAbitrageCore:
    def __init__(self, admin_id, node, info_dict, acw_api, enabled_arbitrage_markets, mongodb_dict, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.info_dict = info_dict
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