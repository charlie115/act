import datetime
import time
import traceback
import pandas as pd
from psycopg2 import extras
from etc.db_handler.mongodb_client import InitDBClient as InitMongoDBClient
from etc.db_handler.postgres_client import InitDBClient as InitPostgresDBClient
from loggers.logger import TradeCoreLogger
from threading import Thread
from multiprocessing import Process
from threading import Thread
from standalone_func.trigger_functions import (fetch_users_with_negative_balance, 
                                               fetch_users_with_negative_balance_loop,
                                               load_trade_config,
                                               load_trade_config_loop,
                                               load_trade_df,
                                               start_trigger_loop,
                                               high_break,
                                               low_break,
                                               load_merged_repeat_df,
                                               handle_repeat_trade_loop,
                                               handle_repeat_trade,
                                               )

class InitTrigger:
    def __init__(self,
                 admin_id,
                 enabled_market_code_combinations,
                 acw_api,
                 redis_dict,
                 postgres_db_dict,
                 mongo_db_dict,
                 logging_dir):
        self.admin_id = admin_id
        self.acw_api = acw_api
        self.enabled_market_code_combinations = enabled_market_code_combinations
        self.redis_dict = redis_dict
        self.postgres_db_dict = postgres_db_dict
        self.mongo_db_dict = mongo_db_dict
        self.postgres_client = InitPostgresDBClient(**{**postgres_db_dict, 'database': 'trade_core'})
        self.logging_dir = logging_dir
        self.logger = TradeCoreLogger("trigger", logging_dir).logger
        
        # Initialize trade_config_df
        load_trade_config(
                          self.postgres_client,
                          self.admin_id,
                          self.acw_api,
                          self.logger,
                          ex=30)
        
        self.users_with_negative_balance_thread = Thread(
            target=fetch_users_with_negative_balance_loop,
            args=(
                admin_id,
                acw_api,
                logging_dir,
                'negative_balance_users'
                ),
            daemon=True)
        self.users_with_negative_balance_thread.start()
        
        self.load_trade_config_loop_thread = Thread(
            target=load_trade_config_loop,
            args=(
                self.postgres_db_dict,
                self.admin_id,
                self.acw_api,
                self.logging_dir,
                ),
            daemon=True
        )
        self.load_trade_config_loop_thread.start()

        self.trade_proc_dict = {}
        self.logger.info(f"Enabled Market Code Combinations: {self.enabled_market_code_combinations}")
        for each_market_code_combination in self.enabled_market_code_combinations:
            market_code_combination_name = each_market_code_combination['market_code_combination']
            trade_support = each_market_code_combination['trade_support']
            # Activate trade service accroding to the trade_support value from the ACW
            if trade_support:
                # Only Trade Triggers
                self.trade_proc_dict[f"trade|{market_code_combination_name}"] = Process(
                    target=start_trigger_loop,
                    args=(
                        market_code_combination_name,
                        trade_support,
                        postgres_db_dict,
                        self.mongo_db_dict,
                        admin_id,
                        acw_api,
                        logging_dir,
                        'trade',
                        0.04
                    ),
                    daemon=True)
                self.trade_proc_dict[f"trade|{market_code_combination_name}"].start()
            # Only Alarms
            self.trade_proc_dict[f"alarm|{market_code_combination_name}"] = Process(
                target=start_trigger_loop,
                args=(
                    market_code_combination_name,
                    False,
                    postgres_db_dict,
                    self.mongo_db_dict,
                    admin_id,
                    acw_api,
                    logging_dir,
                    'trade',
                    2
                ),
                daemon=True)
            self.trade_proc_dict[f"alarm|{market_code_combination_name}"].start()        
        
        # Redis key list for data
        # trade|trade|{market_code_combination}
        # trade|alarm|{market_code_combination}
        # trade_config|{market_code_combination}
        # repeat_trade|{market_code_combination}
        
    def check_status(self, print_result=False, include_text=False):
        trade_proc_status_tup_list = [(each_key, each_proc.is_alive()) for each_key, each_proc in self.trade_proc_dict.items()]
        proc_status = all([each_result[1] for each_result in trade_proc_status_tup_list])
        print_text = ""
        for each_result in trade_proc_status_tup_list:
            print_text += f"{each_result[0]}: {each_result[1]}\n"
        if print_result:
            print(print_text)
        if include_text:
            return proc_status, print_text
        return proc_status
        