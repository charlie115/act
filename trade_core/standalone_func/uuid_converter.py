import time
import json
import traceback
import datetime
import pandas as pd
from etc.redis_connector.redis_helper import RedisHelper
import _pickle as pickle

local_redis = RedisHelper()

def trade_uuid_to_display_id(market_code_combination, trade_uuid, logger):
    # Load trade_df from Redis
    trade_df_pickled = local_redis.get_data(f"trade|trade|{market_code_combination}")
    # Load alarm_df from Redis
    alarm_df_pickled = local_redis.get_data(f"trade|alarm|{market_code_combination}")
    
    # Unpickle data
    trade_df = pickle.loads(trade_df_pickled) if trade_df_pickled else None
    alarm_df = pickle.loads(alarm_df_pickled) if alarm_df_pickled else None
    
    # Check for valid DataFrames
    dataframes_to_concat = []
    if trade_df is not None and not trade_df.empty and not trade_df.isna().all().all():
        dataframes_to_concat.append(trade_df)
    if alarm_df is not None and not alarm_df.empty and not alarm_df.isna().all().all():
        dataframes_to_concat.append(alarm_df)
    
    if dataframes_to_concat:
        total_df = pd.concat(dataframes_to_concat, axis=0)
    else:
        logger.error(f"trade_uuid_to_display_id|No valid DataFrames to concatenate.")
        return trade_uuid  # Or handle appropriately
    
    if len(total_df) == 0:
        logger.error(f"trade_uuid_to_display_id|total_df is empty")
        return trade_uuid
    
    picked_trade = total_df[total_df['uuid'] == trade_uuid]
    if len(picked_trade) == 0:
        logger.error(f"trade_uuid_to_display_id|trade_uuid {trade_uuid} is not in total_df")
        return trade_uuid
    
    user_trade_config_uuid = picked_trade['trade_config_uuid'].values[0]
    user_trade_df = total_df[total_df['trade_config_uuid'] == user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    converted_display_id = int(user_trade_df[user_trade_df['uuid'] == trade_uuid].index[0]) + 1
    return converted_display_id

def display_id_to_trade_uuid(market_code_combination, user_trade_config_uuid, display_id, logger):
    # Load trade_df from Redis
    trade_df_pickled = local_redis.get_data(f"trade|trade|{market_code_combination}")
    # Load alarm_df from Redis
    alarm_df_pickled = local_redis.get_data(f"trade|alarm|{market_code_combination}")
    
    # Unpickle data
    trade_df = pickle.loads(trade_df_pickled) if trade_df_pickled else None
    alarm_df = pickle.loads(alarm_df_pickled) if alarm_df_pickled else None
    
    # Check for valid DataFrames
    dataframes_to_concat = []
    if trade_df is not None and not trade_df.empty and not trade_df.isna().all().all():
        dataframes_to_concat.append(trade_df)
    if alarm_df is not None and not alarm_df.empty and not alarm_df.isna().all().all():
        dataframes_to_concat.append(alarm_df)
    
    if dataframes_to_concat:
        total_df = pd.concat(dataframes_to_concat, axis=0)
    else:
        logger.error(f"display_id_to_trade_uuid|No valid DataFrames to concatenate.")
        return None  # Or handle appropriately
    
    if len(total_df) == 0:
        logger.error(f"display_id_to_trade_uuid|total_df is empty")
        return None
    
    user_trade_df = total_df[total_df['trade_config_uuid'] == user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    if display_id > len(user_trade_df) or display_id <= 0:
        logger.error(f"display_id_to_trade_uuid|display_id {display_id} is out of range")
        return None
    else:
        trade_uuid = user_trade_df.loc[display_id - 1, 'uuid']
        return trade_uuid