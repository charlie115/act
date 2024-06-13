import pandas as pd
from db_handler.postgres_client import InitDBClient
import os
import sys
upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(upper_dir)
from loggers.logger import KimpBotLogger

class UUIDConverter:
    def __init__(self, trade_df_dict, alarm_df_dict, logging_dir):
        self.logger = KimpBotLogger("uuid_converter", logging_dir).logger
        self.trade_df_dict = trade_df_dict
        self.alarm_df_dict = alarm_df_dict
        
    def trade_uuid_to_display_id(self, market_code_combination, trade_uuid):
        trade_df = self.trade_df_dict.get(market_code_combination)
        alarm_df = self.alarm_df_dict.get(market_code_combination)
        if trade_df is None:
            self.logger.error(f"trade_df is None")
            return trade_uuid
        if alarm_df is None:
            self.logger.error(f"alarm_df is None")
            return trade_uuid
        
        total_df = pd.concat([trade_df, alarm_df], axis=0)
        if len(total_df) == 0:
            self.logger.error(f"total_df is empty")
            return trade_uuid
        picked_trade = total_df[total_df['uuid']==trade_uuid]
        if len(picked_trade) == 0:
            self.logger.error(f"trade_uuid {trade_uuid} is not in total_df")
            return trade_uuid
        user_trade_config_uuid = picked_trade['trade_config_uuid'].values[0]
        user_trade_df = total_df[total_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
        converted_display_id = int(user_trade_df[user_trade_df['uuid']==trade_uuid].index[0]) + 1
        return converted_display_id

    # def trade_uuid_to_display_id(self, trade_df, trade_uuid):
    #         if trade_df is None:
    #             return trade_uuid
    #         elif trade_uuid is None:
    #             return None
    #         else:
    #             picked_trade = trade_df[trade_df['uuid']==trade_uuid]
    #         if len(picked_trade) == 0:
    #             return None
    #         else:
    #             user_trade_config_uuid = picked_trade['trade_config_uuid'].values[0]
    #             user_trade_df = trade_df[trade_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    #             converted_display_id = int(user_trade_df[user_trade_df['uuid']==trade_uuid].index[0]) + 1
    #             return converted_display_id
    
    def display_id_to_trade_uuid(self, market_code_combination, user_trade_config_uuid, display_id):
        trade_df = self.trade_df_dict.get(market_code_combination)
        alarm_df = self.alarm_df_dict.get(market_code_combination)
        if trade_df is None:
            self.logger.error(f"trade_df is None")
            return display_id
        if alarm_df is None:
            self.logger.error(f"alarm_df is None")
            return display_id
        
        total_df = pd.concat([trade_df, alarm_df], axis=0)
        if len(total_df) == 0:
            self.logger.error(f"total_df is empty")
            return display_id
        user_trade_df = total_df[total_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
        if display_id > len(user_trade_df):
            self.logger.error(f"display_id {display_id} is out of range")
            return None
        else:
            trade_uuid = user_trade_df.loc[display_id-1, 'uuid']
            return trade_uuid
            
    # def display_id_to_trade_uuid(self, trade_df, user_trade_config_uuid, display_id):
    #     if trade_df is None:
    #         return display_id
    #     elif user_trade_config_uuid is None:
    #         return None
    #     else:
    #         user_trade_df = trade_df[trade_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    #         if display_id > len(user_trade_df):
    #             return None
    #         else:
    #             trade_uuid = user_trade_df.loc[display_id-1, 'uuid']
    #             return trade_uuid