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
from standalone_func.kline_data_generator import (resample_ohlc_df,
                                                  generate_ohlc_df,
                                                  insert_kline_to_db, 
                                                  ohlc_1T_loader, 
                                                  ohlc_day_resample_loader, 
                                                  ohlc_hour_resample_loader, 
                                                  ohlc_min_resample_loader)
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
            for i, each_kline_type in enumerate(self.enabled_kline_types):
                if each_kline_type.endswith('T'):
                    if each_kline_type == '1T':
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"] = Process(
                            target=ohlc_1T_loader,
                            args=(
                                self.info_dict,
                                self.convert_rate_dict,
                                generate_ohlc_df,
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
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_loader"].start()
                    else:
                        count = int(re.search(r'\d+', each_kline_type).group()) / int(re.search(r'\d+', self.enabled_kline_types[i-1]).group())
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(
                            target=ohlc_min_resample_loader,
                            args=(
                                resample_ohlc_df,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                self.enabled_kline_types[i-1],
                                each_kline_type,
                                count,
                                self.register_monitor_msg,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir
                            ),
                            daemon=True
                        )
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                elif each_kline_type.endswith('H'):
                    if each_kline_type == '1H':
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(
                            target=ohlc_hour_resample_loader,
                            args=(
                                resample_ohlc_df,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                "30min",
                                "1h",
                                2,
                                self.register_monitor_msg,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir
                            ),
                            daemon=True
                        )
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                    else:
                        count = int(re.search(r'\d+', each_kline_type).group()) / int(re.search(r'\d+', self.enabled_kline_types[i-1]).group())
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(
                            target=ohlc_hour_resample_loader,
                            args=(
                                resample_ohlc_df,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                self.enabled_kline_types[i-1],
                                each_kline_type,
                                count,
                                self.register_monitor_msg,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir
                            ),
                            daemon=True
                        )
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                elif each_kline_type.endswith('D'):
                    if each_kline_type == "1D":
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"] = Process(
                            target=ohlc_day_resample_loader,
                            args=(
                                resample_ohlc_df,
                                insert_kline_to_db,
                                target_market_code,
                                origin_market_code,
                                "4H",
                                "1D",
                                6,
                                self.register_monitor_msg,
                                self.admin_id,
                                self.node,
                                self.redis_dict,
                                self.mongodb_dict,
                                self.logging_dir
                            ),
                            daemon=True
                        )
                        self.kline_proc_dict[f"{market_combination}_{each_kline_type}_reample_loader"].start()
                    else:
                        pass
                else:
                    raise ValueError(f"Invalid kline_type: {each_kline_type}")
                time.sleep(1)
                
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


        

