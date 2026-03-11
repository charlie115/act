import redis
import json
import threading
import _pickle as pickle
import pandas as pd
import os

MARKET_STATE_VERSION_PREFIX = "MARKET_STATE_VERSION"

class RedisHelper:
   
    def __init__(self, host="localhost", port=6379, passwd=None, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.passwd = os.getenv("REDIS_PASSWORD") if passwd is None else passwd
        self._thread_local = threading.local()

    def get_redis_client(self):
        if not hasattr(self._thread_local, 'redis_client'):
            self._thread_local.redis_client = redis.Redis(
                host=self.host, port=self.port, db=self.db,
                password=self.passwd, decode_responses=False
            )
        return self._thread_local.redis_client
    
    def get_key(self, pattern):
        redis_conn = self.get_redis_client()
        return list(redis_conn.scan_iter(match=pattern))
    
    def get_all_keys(self):
        redis_conn = self.get_redis_client()
        return list(redis_conn.scan_iter())

    def set_data(self, key_name, value, ex=None):
        redis_conn = self.get_redis_client()
        redis_conn.set(key_name, value, ex=ex)

    def get_data(self, key_name):
        redis_conn = self.get_redis_client()
        return redis_conn.get(key_name)

    def set_dict(self, key_name, dict_obj, ex=None):
        redis_conn = self.get_redis_client()
        redis_conn.set(key_name, json.dumps(dict_obj, ensure_ascii=False), ex=ex)
    
    def get_dict(self, key_name):
        redis_conn = self.get_redis_client()
        dumped_json = redis_conn.get(key_name)
        if dumped_json:
            return json.loads(dumped_json)
        return None
        
    def hset_dict(self, key_name, mapping):
        redis_conn = self.get_redis_client()
        redis_conn.hset(name=key_name, mapping=mapping)

    def hgetall_dict(self, key_name):
        redis_conn = self.get_redis_client()
        return redis_conn.hgetall(key_name)
    
    def hget_dict(self, key_name, field):
        redis_conn = self.get_redis_client()
        return redis_conn.hget(key_name, field)

    def zadd_member(self, key_name, mapping):
        redis_conn = self.get_redis_client()
        redis_conn.zadd(key_name, mapping)

    def zrangebyscore(self, key_name, minimum, maximum):
        redis_conn = self.get_redis_client()
        return redis_conn.zrangebyscore(key_name, minimum, maximum)

    def zremrangebyscore(self, key_name, minimum, maximum):
        redis_conn = self.get_redis_client()
        redis_conn.zremrangebyscore(key_name, minimum, maximum)

    def zrem_member(self, key_name, member):
        redis_conn = self.get_redis_client()
        redis_conn.zrem(key_name, member)
    
    def delete_key(self, key_name):
        redis_conn = self.get_redis_client()
        redis_conn.delete(key_name)

    def publish(self, channel, message):
        redis_conn = self.get_redis_client()
        redis_conn.publish(channel, message)
        
    def get_pubsub(self):
        redis_conn = self.get_redis_client()
        return redis_conn.pubsub()
        
    # Ticker handling methods
    def update_exchange_stream_data(self, stream_data_type, market_code, symbol, stream_data):
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        # Serialize stream_data_type data to JSON
        stream_data_json = json.dumps(stream_data)
        # Update the ticker data for the symbol
        redis_conn.hset(redis_key, symbol, stream_data_json)
        last_update_timestamp = stream_data.get("last_update_timestamp")
        if last_update_timestamp is not None:
            redis_conn.set(
                f"{MARKET_STATE_VERSION_PREFIX}|{market_code}",
                str(last_update_timestamp),
            )

    def get_exchange_stream_data(self, stream_data_type, market_code, symbol):
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        stream_data_json = redis_conn.hget(redis_key, symbol)
        if stream_data_json:
            return json.loads(stream_data_json)
        return None
    
    def delete_exchange_stream_data(self, stream_data_type, market_code, symbol):
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        redis_conn.hdel(redis_key, symbol)
        
    def delete_all_exchange_stream_data(self, stream_data_type, market_code):
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        redis_conn.delete(redis_key)

    def get_all_exchange_stream_data(self, stream_data_type, market_code):
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        # Get all fields and values from the hash
        all_stream_data = redis_conn.hgetall(redis_key)
        # Deserialize JSON strings back to dictionaries
        return {symbol.decode('utf-8'): json.loads(ticker_data) for symbol, ticker_data in all_stream_data.items()}
    
    def get_fundingrate_df(self, market_code_combination, market_code):
        redis_conn = self.get_redis_client()
        redis_key = f'fundingrate|{market_code_combination}|{market_code}'
        fundingrate_df_raw = redis_conn.get(redis_key)
        if fundingrate_df_raw:
            return pickle.loads(fundingrate_df_raw)
        return pd.DataFrame()
