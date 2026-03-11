import pandas as pd
import json
import time
import datetime
from threading import Thread
import numpy as np
import os
import sys
import traceback

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import InfoCoreLogger
from standalone_func.aidata_updater import store_ai_recommendation_data_loop

class InitAiDataCore:
    def __init__(self, admin_id, node, acw_api, ai_api_key, redis_dict, mongodb_dict, logging_dir):
        self.admin_id = admin_id
        self.node = node
        self.acw_api = acw_api
        self.trading_market_code_combinations = self.get_trading_market_code_combinations() # e.g. ['UPBIT_SPOT/KRW:BINANCE_USD_M/USDT']
        self.redis_dict = redis_dict # For server check for futures use. Currently not used.
        self.mongodb_dict = mongodb_dict
        self.ai_api_key = ai_api_key
        self.logging_dir = logging_dir
        self.logger = InfoCoreLogger("aidata_core", logging_dir).logger
        self.logger.info(f"InitAiDataCore Started.")
        
    def get_trading_market_code_combinations(self):
        trading_market_code_combinations = []
        market_code_combination_series = self.acw_api.get_node()['market_code_combinations']
        if len(market_code_combination_series) > 0:
            for node_market_code_combinations in market_code_combination_series:
                for each_market_code_combination in node_market_code_combinations:
                    self.logger.debug("market_code_combination=%s", each_market_code_combination)
                    if each_market_code_combination['trade_support']:
                        trading_market_code_combinations.append(each_market_code_combination['market_code_combination'])
        else:
            self.logger.info(f"No trading market code combinations found.")
        # Remove duplicates
        trading_market_code_combinations = list(set(trading_market_code_combinations))
        return trading_market_code_combinations
    
    def start_aidata_generator(self):
        for each_market_code_combination in self.trading_market_code_combinations:
            Thread(target=store_ai_recommendation_data_loop, args=(each_market_code_combination, self.ai_api_key, self.mongodb_dict, self.logger)).start()
