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

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger
from etc.redis_connector.redis_helper import RedisHelper
from standalone_func.kline_data_generator import (
                                                  insert_kline_to_db, 
                                                  ohlc_1T_generator,
                                                  ohlc_interval_generator,
                                                  )
from standalone_func.price_df_generator import get_price_df

class InitKlineCore:
    def __init__(
        self,
        admin_id,
        node,
        info_dict,
        convert_rate_dict,
        enabled_market_klines,
        register_monitor_msg,
        redis_dict,
        mongodb_dict,
        logging_dir
        ):
        self.node = node
        self.admin_id = admin_id
        self.info_dict = info_dict
        self.convert_rate_dict = convert_rate_dict
        self.register_monitor_msg = register_monitor_msg
        self.logging_dir = logging_dir
        self.kline_logger = InfoCoreLogger("kline_core", logging_dir).logger
        self.kline_logger.info(f"InitKlineCore started.")
        self.remote_redis = RedisHelper(**redis_dict)
        self.local_redis = RedisHelper()
        # self.market_code_list = get_market_code_list()
        # self.market_combination_list = self.get_market_combination_list()
        self.enabled_market_klines = enabled_market_klines
        self.enabled_kline_types = ['1T', '5T', '15T', '30T', '1H', '4H']
        self.kline_proc_dict = {}
        self.pubsub = self.remote_redis.get_pubsub()
        self.mongodb_dict = mongodb_dict
        self.redis_dict = redis_dict
        # self.enaled_market_combination_list = []
        self.register_enabled_market_klines()
        self._start_generating_kline()

    def _start_generating_kline(self):
        # Start generating kline        
        for market_combination in self.enabled_market_klines:
            target_market_code = market_combination.split(':')[0]
            origin_market_code = market_combination.split(':')[1]
            for each_kline_type in self.enabled_kline_types:
                def create_kline_process():
                    if each_kline_type == "1T":
                        return Process(
                            target=ohlc_1T_generator,
                            args=(
                                self.info_dict,
                                self.convert_rate_dict,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                self.register_monitor_msg,
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
                                each_kline_type,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                self.register_monitor_msg,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir,
                            ),
                            daemon=True
                        )
                self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"] = create_kline_process()
                self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"].start()
                
                time.sleep(0.25)
                
                # Add monitoring thread
                def monitor_kline_process():
                    while True:
                        if not self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"].is_alive():
                            self.kline_logger.error(f"Kline process {market_combination}_{each_kline_type}_loader is dead, restarting..")
                            self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"] = create_kline_process()
                            self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"].start()
                        time.sleep(2)
                Thread(target=monitor_kline_process, daemon=True).start()
                self.kline_logger.info(f"Kline process monitor for {market_combination}_{each_kline_type}_loader started.")
                    
                
                
    def register_enabled_market_klines(self):
        self.kline_logger.info(f"register_enabled_market_klines|Registering enabled market klines:{self.enabled_market_klines} to redis Started..")
        def register_enabled_market_klines_to_redis():
            while True:
                try:
                    for each_enabled_market_klines in self.enabled_market_klines:
                        self.remote_redis.set_data(f"INFO_CORE|ACTIVATED|{each_enabled_market_klines}", datetime.datetime.utcnow().timestamp(), ex=35)
                except Exception as e:
                    self.kline_logger.error(f"register_enabled_market_klines|Error in register_enabled_market_klines_to_redis: {traceback.format_exc()}")
                time.sleep(30)
        Thread(target=register_enabled_market_klines_to_redis, daemon=True).start()


        

