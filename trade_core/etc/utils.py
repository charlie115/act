import _pickle as pickle
import json
from etc.redis_connector.redis_helper import RedisHelper
import pandas as pd

local_redis = RedisHelper()

def get_trade_df(market_code_combination, trade_support, table_name='trade'):
    if trade_support:
        trade_df_pickled = local_redis.get_data(f"{table_name}|trade|{market_code_combination}")
    else:
        trade_df_pickled = local_redis.get_data(f"{table_name}|alarm|{market_code_combination}")
        
    if trade_df_pickled is not None:
        return pickle.loads(trade_df_pickled)
    else:
        return pd.DataFrame()
    
def get_users_with_negative_balance(key_name='negative_balance_users'):
    users_with_negative_balance_pickled = local_redis.get_data(key_name)
    if users_with_negative_balance_pickled is not None:
        return json.loads(users_with_negative_balance_pickled)
    else:
        return []
    
def get_trade_config_df(market_code_combination, table_name='trade_config'):
    trade_config_df_pickled = local_redis.get_data(f"{table_name}|{market_code_combination}")
    if trade_config_df_pickled is not None:
        return pickle.loads(trade_config_df_pickled)
    else:
        return pd.DataFrame()
    