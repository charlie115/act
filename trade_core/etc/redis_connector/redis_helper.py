import redis
import json
import threading

class RedisHelper:
   
    # def __init__(self, host="localhost", port=6379, passwd='LocalRedis123!', db=0):
    def __init__(self, host="localhost", port=6379, passwd=None, db=0):
        self.host = host
        self.port = port
        self.db = db
        self.passwd = passwd
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
        return redis_conn.keys(pattern)
    
    def get_all_keys(self):
        redis_conn = self.get_redis_client()
        return redis_conn.keys()

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