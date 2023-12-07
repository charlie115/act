import redis
import json
import datetime
import pandas as pd
import os
import sys

upper_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
upper_upper_dir = os.path.dirname(upper_dir)
config_name = "info_core_config.json"

sys.path.append(upper_upper_dir)

with open(f"{upper_upper_dir}/{config_name}") as f:
    config = json.load(f)

node = config['node']
node_settings = config['node_settings'][node]
redis_settings_name = node_settings['redis_settings']
redis_setting_dict = config['database_setting'][redis_settings_name]

class InitRedis:
    def __init__(self, passwd=redis_setting_dict['passwd'], host=redis_setting_dict['host'], port=redis_setting_dict['port'], db=0): # Temporary
        self.redis_pool = redis.ConnectionPool(host=host, port=port, db=db, password=passwd, decode_responses=False, max_connections=20)
        self.redis_conn = redis.Redis(connection_pool=self.redis_pool)

    def set_data(self, key_name, value, ex=None):
        self.redis_conn.set(key_name, value, ex=ex)

    def get_data(self, key_name):
        return self.redis_conn.get(key_name)

    def set_dict(self, key_name, dict_obj, ex=None):
        self.redis_conn.set(key_name, json.dumps(dict_obj, ensure_ascii=False).encode('utf-8'), ex=ex)
    
    def get_dict(self, key_name):
        dumped_json = self.redis_conn.get(key_name)
        return dict(json.loads(dumped_json.decode('utf-8')))
        
    def hset_dict(self, keyname, dict_obj):
        self.redis_conn.hset(keyname, mapping=dict_obj)

    def hget_dict(self, keyname):
        return self.redis_conn.hgetall(keyname)

    def close_connector(self):
        self.redis_conn.close()

    def disconnect_pool(self):
        self.redis_pool.disconnect()

    def close_all(self):
        self.close_connector()
        self.disconnect_pool()

    def read_json_to_df(self):
        redis_key_list = self.redis_conn.scan(0)[1]
        redis_data_dict_list = []
        for each_key in redis_key_list:
            redis_data_dict_list.append(json.loads(self.get_data(each_key)))

        redis_data_df = pd.DataFrame(redis_data_dict_list)
        redis_data_df = redis_data_df.where(redis_data_df.notnull(), None)

        if 'datetime' in redis_data_df.columns:
            redis_data_df.loc[:, 'datetime'] = pd.to_datetime(redis_data_df.loc[:, 'datetime'])
        
        if 'datetime_end' in redis_data_df.columns:
            redis_data_df.loc[:, 'datetime_end'] = pd.to_datetime(redis_data_df.loc[:, 'datetime_end'])

        return redis_data_df
    
    def publish(self, channel, message):
        self.redis_conn.publish(channel, message)