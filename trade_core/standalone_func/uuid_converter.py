import time
import json
import traceback
import datetime
import pandas as pd
from standalone_func.premium_data_generator import get_premium_df
from etc.redis_connector.redis_helper import RedisHelper
import _pickle as pickle

local_redis = RedisHelper()

def trade_uuid_to_display_id(market_code_combination, trade_uuid, logger):
    # load trade_df from redis
    trade_df_pickled = local_redis.get(f"trade|trade|{market_code_combination}")
    # load alarm_df from redis
    alarm_df_pickled = local_redis.get(f"trade|alarm|{market_code_combination}")
    # load
    if trade_df_pickled is None:
        logger.error(f"trade_uuid_to_display_id|trade_df is None")
        return trade_uuid
    else:
        trade_df = pickle.loads(trade_df_pickled)
    if alarm_df_pickled is None:
        logger.error(f"trade_uuid_to_display_id|alarm_df is None")
        return trade_uuid
    else:
        alarm_df = pickle.loads(alarm_df_pickled)
    
    total_df = pd.concat([trade_df, alarm_df], axis=0)
    if len(total_df) == 0:
        logger.error(f"trade_uuid_to_display_id|total_df is empty")
        return trade_uuid
    picked_trade = total_df[total_df['uuid']==trade_uuid]
    if len(picked_trade) == 0:
        logger.error(f"trade_uuid_to_display_id|trade_uuid {trade_uuid} is not in total_df")
        return trade_uuid
    user_trade_config_uuid = picked_trade['trade_config_uuid'].values[0]
    user_trade_df = total_df[total_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    converted_display_id = int(user_trade_df[user_trade_df['uuid']==trade_uuid].index[0]) + 1
    return converted_display_id

def display_id_to_trade_uuid(market_code_combination, user_trade_config_uuid, display_id, logger):
    # load trade_df from redis
    trade_df_pickled = local_redis.get(f"trade|trade|{market_code_combination}")
    # load alarm_df from redis
    alarm_df_pickled = local_redis.get(f"trade|alarm|{market_code_combination}")
    # load
    if trade_df_pickled is None:
        logger.error(f"display_id_to_trade_uuid|trade_df is None")
        return trade_uuid
    else:
        trade_df = pickle.loads(trade_df_pickled)
    if alarm_df_pickled is None:
        logger.error(f"display_id_to_trade_uuid|alarm_df is None")
        return trade_uuid
    else:
        alarm_df = pickle.loads(alarm_df_pickled)
    
    total_df = pd.concat([trade_df, alarm_df], axis=0)
    if len(total_df) == 0:
        logger.error(f"display_id_to_trade_uuid|total_df is empty")
        return display_id
    user_trade_df = total_df[total_df['trade_config_uuid']==user_trade_config_uuid].sort_values(by=['registered_datetime']).reset_index(drop=True)
    if display_id > len(user_trade_df):
        logger.error(f"display_id_to_trade_uuid|display_id {display_id} is out of range")
        return None
    else:
        trade_uuid = user_trade_df.loc[display_id-1, 'uuid']
        return trade_uuid