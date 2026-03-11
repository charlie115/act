import os
import json
import sys
import argparse
import traceback
import datetime
import pandas as pd
import numpy as np
import _pickle as pickle
import time
import datetime
from multiprocessing import Process
from threading import Thread
import re

from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.kline_data_generator import (
                                                  insert_kline_to_db, 
                                                  ohlc_1T_generator,
                                                  ohlc_interval_generator,
                                                  )
class InitKlineCore:
    ACTIVATED_INDEX_KEY = "INFO_CORE|ACTIVATED_INDEX"
    ACTIVATED_TTL_SECONDS = 35

    def __init__(
        self,
        admin_id,
        node,
        enabled_market_klines,
        acw_api,
        redis_dict,
        mongodb_dict,
        logging_dir
        ):
        self.node = node
        self.admin_id = admin_id
        self.acw_api = acw_api
        self.logging_dir = logging_dir
        self.kline_logger = InfoCoreLogger("kline_core", logging_dir).logger
        self.kline_logger.info(f"InitKlineCore started.")
        self.remote_redis = RedisHelper(**redis_dict)
        self.local_redis = RedisHelper()
        self.enabled_market_klines = enabled_market_klines
        self.enabled_kline_types = ['1T', '5T', '15T', '30T', '1H', '4H']
        self.kline_proc_dict = {}
        self.pubsub = self.remote_redis.get_pubsub()
        self.mongodb_dict = mongodb_dict
        self.redis_dict = redis_dict
        self.register_enabled_market_klines()
        self._start_generating_kline()

    def _start_generating_kline(self):
        # Start generating kline
        for market_combination in self.enabled_market_klines:
            target_market_code = market_combination.split(':')[0]
            origin_market_code = market_combination.split(':')[1]
            for each_kline_type in self.enabled_kline_types:
                # Use default arguments to capture loop variables by value (not by reference)
                # This fixes the closure bug where all monitors would reference the last loop values
                def create_kline_process(
                    kline_type=each_kline_type,
                    target_mc=target_market_code,
                    origin_mc=origin_market_code
                ):
                    if kline_type == "1T":
                        return Process(
                            target=ohlc_1T_generator,
                            args=(
                                insert_kline_to_db,
                                target_mc,
                                origin_mc,
                                self.acw_api,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir
                            ),
                            daemon=True
                        )
                    else:
                        return Process(
                            target=ohlc_interval_generator,
                            args=(
                                kline_type,
                                insert_kline_to_db,
                                target_mc,
                                origin_mc,
                                self.acw_api,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir,
                            ),
                            daemon=True
                        )

                proc_key = f"{market_combination}_{each_kline_type}_loader"
                self.kline_proc_dict[proc_key] = create_kline_process()
                self.kline_proc_dict[proc_key].start()

                time.sleep(0.5)

                # Add monitoring thread
                # Use default arguments to capture loop variables by value
                def monitor_kline_process(
                    proc_key=proc_key,
                    create_proc=create_kline_process
                ):
                    while True:
                        if not self.kline_proc_dict[proc_key].is_alive():
                            self.kline_logger.error(f"Kline process {proc_key} is dead, restarting..")
                            self.kline_proc_dict[proc_key] = create_proc()
                            self.kline_proc_dict[proc_key].start()
                        time.sleep(2)
                Thread(target=monitor_kline_process, daemon=True).start()
                self.kline_logger.info(f"Kline process monitor for {proc_key} started.")
                    
                
                
    def register_enabled_market_klines(self):
        self.kline_logger.info(f"register_enabled_market_klines|Registering enabled market klines:{self.enabled_market_klines} to redis Started..")
        def register_enabled_market_klines_to_redis():
            while True:
                try:
                    now_timestamp = datetime.datetime.utcnow().timestamp()
                    for each_enabled_market_klines in self.enabled_market_klines:
                        self.remote_redis.set_data(
                            f"INFO_CORE|ACTIVATED|{each_enabled_market_klines}",
                            now_timestamp,
                            ex=self.ACTIVATED_TTL_SECONDS,
                        )
                        self.remote_redis.zadd_member(
                            self.ACTIVATED_INDEX_KEY,
                            {each_enabled_market_klines: now_timestamp},
                        )
                    self.remote_redis.zremrangebyscore(
                        self.ACTIVATED_INDEX_KEY,
                        "-inf",
                        now_timestamp - self.ACTIVATED_TTL_SECONDS,
                    )
                except Exception as e:
                    self.kline_logger.error(f"register_enabled_market_klines|Error in register_enabled_market_klines_to_redis: {traceback.format_exc()}")
                time.sleep(30)
        Thread(target=register_enabled_market_klines_to_redis, daemon=True).start()


        
