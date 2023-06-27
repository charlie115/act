import redis
import json
import datetime
import pandas as pd

class InitRedis:
    def __init__(self, host='127.0.0.1', port=6379, db=0):
        self.redis_pool = redis.ConnectionPool(host=host, port=port, db=db, decode_responses=False)
        self.redis_conn = redis.Redis(connection_pool=self.redis_pool)

    def set_data(self, key_name, value):
        self.redis_conn.set(key_name, value)

    def get_data(self, key_name):
        return self.redis_conn.get(key_name)

    def set_dict(self, key_name, dict_obj):
        self.redis_conn.set(key_name, json.dumps(dict_obj, ensure_ascii=False).encode('utf-8'))
    
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