import redis
import json
import threading
import struct
import time
import asyncio
from typing import Dict, Any, Optional, Union
from collections import defaultdict
import msgpack

MARKET_STATE_VERSION_PREFIX = "MARKET_STATE_VERSION"

class OptimizedRedisHelper:
    """
    Optimized Redis helper with binary serialization, connection pooling,
    and memory-first caching for high-frequency trading data.
    """
    
    def __init__(self, host="localhost", port=6379, passwd=None, db=0, pool_size=10):
        self.host = host
        self.port = port
        self.db = db
        self.passwd = passwd
        
        # Connection pool for better performance
        self.connection_pool = redis.ConnectionPool(
            host=host, port=port, db=db, password=passwd,
            max_connections=pool_size, decode_responses=False
        )
        
        # Thread-local storage for connections
        self._thread_local = threading.local()
        
        # Memory-first cache for hot data
        self.memory_cache = {}
        self.cache_timestamps = {}
        self.cache_lock = threading.RLock()
        
        # Performance counters
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'redis_operations': 0,
            'serialization_time': 0.0
        }

    def get_redis_client(self):
        """Get thread-local Redis client from pool"""
        if not hasattr(self._thread_local, 'redis_client'):
            self._thread_local.redis_client = redis.Redis(connection_pool=self.connection_pool)
        return self._thread_local.redis_client
    
    # Legacy compatibility methods
    def get_key(self, pattern):
        redis_conn = self.get_redis_client()
        return redis_conn.keys(pattern)
    
    def get_all_keys(self):
        redis_conn = self.get_redis_client()
        return redis_conn.keys()

    def set_data(self, key_name, value, ex=None):
        redis_conn = self.get_redis_client()
        redis_conn.set(key_name, value, ex=ex)
        self.stats['redis_operations'] += 1

    def get_data(self, key_name):
        redis_conn = self.get_redis_client()
        self.stats['redis_operations'] += 1
        return redis_conn.get(key_name)

    def set_dict(self, key_name, dict_obj, ex=None):
        redis_conn = self.get_redis_client()
        redis_conn.set(key_name, json.dumps(dict_obj, ensure_ascii=False), ex=ex)
        self.stats['redis_operations'] += 1
    
    def get_dict(self, key_name):
        redis_conn = self.get_redis_client()
        dumped_json = redis_conn.get(key_name)
        self.stats['redis_operations'] += 1
        if dumped_json:
            return json.loads(dumped_json)
        return None
        
    def hset_dict(self, key_name, mapping):
        redis_conn = self.get_redis_client()
        redis_conn.hset(name=key_name, mapping=mapping)
        self.stats['redis_operations'] += 1
        
    def hgetall_dict(self, key_name):
        redis_conn = self.get_redis_client()
        self.stats['redis_operations'] += 1
        return redis_conn.hgetall(key_name)

    def hget_dict(self, key_name):
        redis_conn = self.get_redis_client()
        self.stats['redis_operations'] += 1
        return redis_conn.hgetall(key_name)
    
    def delete_key(self, key_name):
        redis_conn = self.get_redis_client()
        # Also remove from memory cache
        with self.cache_lock:
            if key_name in self.memory_cache:
                del self.memory_cache[key_name]
                del self.cache_timestamps[key_name]
        redis_conn.delete(key_name)
        self.stats['redis_operations'] += 1

    def publish(self, channel, message):
        redis_conn = self.get_redis_client()
        redis_conn.publish(channel, message)
        self.stats['redis_operations'] += 1
        
    def get_pubsub(self):
        redis_conn = self.get_redis_client()
        return redis_conn.pubsub()

    # Optimized stream data methods
    def _pack_ticker_data(self, price: float, volume: float, change: float, timestamp: int) -> bytes:
        """Pack ticker data into binary format (20 bytes vs ~100+ bytes JSON)"""
        # Use double for timestamp to handle large values
        return struct.pack('!fffd', price, volume, change, float(timestamp))
    
    def _unpack_ticker_data(self, data: bytes) -> Dict[str, float]:
        """Unpack binary ticker data"""
        price, volume, change, timestamp = struct.unpack('!fffd', data)
        return {
            'price': price,
            'volume': volume,
            'change': change,
            'timestamp': timestamp
        }
    
    def _pack_orderbook_data(self, bid_price: float, ask_price: float, bid_qty: float, ask_qty: float, timestamp: int) -> bytes:
        """Pack orderbook data into binary format (24 bytes vs ~80+ bytes JSON)"""
        return struct.pack('!ffffd', bid_price, ask_price, bid_qty, ask_qty, float(timestamp))
    
    def _unpack_orderbook_data(self, data: bytes) -> Dict[str, float]:
        """Unpack binary orderbook data"""
        bid_price, ask_price, bid_qty, ask_qty, timestamp = struct.unpack('!ffffd', data)
        return {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_qty': bid_qty,
            'ask_qty': ask_qty,
            'timestamp': timestamp
        }

    def update_ticker_data_optimized(self, market_code: str, symbol: str, 
                                   price: float, volume: float, change: float, timestamp: int = None):
        """Optimized ticker data update with memory cache only"""
        if timestamp is None:
            timestamp = int(time.time() * 1_000_000)
        
        start_time = time.time()
        
        # Update memory cache only (microsecond access)
        cache_key = f"ticker:{market_code}:{symbol}"
        ticker_data = {
            'price': price,
            'volume': volume, 
            'change': change,
            'timestamp': timestamp,
            'last_update_timestamp': timestamp
        }
        with self.cache_lock:
            self.memory_cache[cache_key] = ticker_data
            self.cache_timestamps[cache_key] = time.time()
        
        # No Redis write here - original message storage handles persistence
        self.stats['serialization_time'] += time.time() - start_time

    def update_orderbook_data_optimized(self, market_code: str, symbol: str,
                                      bid_price: float, ask_price: float,
                                      bid_qty: float, ask_qty: float, timestamp: int = None):
        """Optimized orderbook data update with memory cache only"""
        if timestamp is None:
            timestamp = int(time.time() * 1_000_000)
        
        start_time = time.time()
        
        # Update memory cache only (microsecond access)
        cache_key = f"orderbook:{market_code}:{symbol}"
        orderbook_data = {
            'bid_price': bid_price,
            'ask_price': ask_price,
            'bid_qty': bid_qty,
            'ask_qty': ask_qty,
            'timestamp': timestamp,
            'last_update_timestamp': timestamp
        }
        with self.cache_lock:
            self.memory_cache[cache_key] = orderbook_data
            self.cache_timestamps[cache_key] = time.time()
        
        # No Redis write here - original message storage handles persistence
        self.stats['serialization_time'] += time.time() - start_time

    def get_ticker_data_optimized(self, market_code: str, symbol: str) -> Optional[Dict[str, float]]:
        """Get ticker data with memory-first lookup"""
        cache_key = f"ticker:{market_code}:{symbol}"
        
        # Try memory cache first (microsecond access)
        with self.cache_lock:
            if cache_key in self.memory_cache:
                # Check if cache is fresh (within 1 second)
                if time.time() - self.cache_timestamps[cache_key] < 1.0:
                    self.stats['cache_hits'] += 1
                    return self.memory_cache[cache_key]
        
        # Fallback to Redis
        self.stats['cache_misses'] += 1
        redis_conn = self.get_redis_client()
        redis_key = f"ticker_bin:{market_code}"
        packed_data = redis_conn.hget(redis_key, symbol)
        self.stats['redis_operations'] += 1
        
        if packed_data:
            data = self._unpack_ticker_data(packed_data)
            # Update memory cache
            with self.cache_lock:
                self.memory_cache[cache_key] = data
                self.cache_timestamps[cache_key] = time.time()
            return data
        return None

    def get_orderbook_data_optimized(self, market_code: str, symbol: str) -> Optional[Dict[str, float]]:
        """Get orderbook data with memory-first lookup"""
        cache_key = f"orderbook:{market_code}:{symbol}"
        
        # Try memory cache first
        with self.cache_lock:
            if cache_key in self.memory_cache:
                if time.time() - self.cache_timestamps[cache_key] < 1.0:
                    self.stats['cache_hits'] += 1
                    return self.memory_cache[cache_key]
        
        # Fallback to Redis
        self.stats['cache_misses'] += 1
        redis_conn = self.get_redis_client()
        redis_key = f"orderbook_bin:{market_code}"
        packed_data = redis_conn.hget(redis_key, symbol)
        self.stats['redis_operations'] += 1
        
        if packed_data:
            data = self._unpack_orderbook_data(packed_data)
            # Update memory cache
            with self.cache_lock:
                self.memory_cache[cache_key] = data
                self.cache_timestamps[cache_key] = time.time()
            return data
        return None

    def get_all_ticker_data_optimized(self, market_code: str) -> Dict[str, Dict[str, float]]:
        """Get all ticker data for a market with optimized bulk operations"""
        redis_conn = self.get_redis_client()
        redis_key = f"ticker_bin:{market_code}"
        all_data = redis_conn.hgetall(redis_key)
        self.stats['redis_operations'] += 1
        
        result = {}
        for symbol, packed_data in all_data.items():
            symbol = symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol
            try:
                result[symbol] = self._unpack_ticker_data(packed_data)
            except struct.error:
                # Handle corrupted data gracefully
                continue
        
        return result

    def get_all_orderbook_data_optimized(self, market_code: str) -> Dict[str, Dict[str, float]]:
        """Get all orderbook data for a market with optimized bulk operations"""
        redis_conn = self.get_redis_client()
        redis_key = f"orderbook_bin:{market_code}"
        all_data = redis_conn.hgetall(redis_key)
        self.stats['redis_operations'] += 1
        
        result = {}
        for symbol, packed_data in all_data.items():
            symbol = symbol.decode('utf-8') if isinstance(symbol, bytes) else symbol
            try:
                result[symbol] = self._unpack_orderbook_data(packed_data)
            except struct.error:
                continue
        
        return result

    def pipeline_updates(self, updates: list):
        """Execute multiple Redis updates in a pipeline for better performance"""
        redis_conn = self.get_redis_client()
        pipeline = redis_conn.pipeline()
        
        for update in updates:
            if update['type'] == 'ticker':
                packed_data = self._pack_ticker_data(
                    update['price'], update['volume'], update['change'], update['timestamp']
                )
                pipeline.hset(f"ticker_bin:{update['market_code']}", update['symbol'], packed_data)
            elif update['type'] == 'orderbook':
                packed_data = self._pack_orderbook_data(
                    update['bid_price'], update['ask_price'], 
                    update['bid_qty'], update['ask_qty'], update['timestamp']
                )
                pipeline.hset(f"orderbook_bin:{update['market_code']}", update['symbol'], packed_data)
        
        pipeline.execute()
        self.stats['redis_operations'] += len(updates)

    def cleanup_cache(self, max_age: float = 60.0):
        """Clean up old entries from memory cache"""
        current_time = time.time()
        with self.cache_lock:
            expired_keys = [
                key for key, timestamp in self.cache_timestamps.items()
                if current_time - timestamp > max_age
            ]
            for key in expired_keys:
                del self.memory_cache[key]
                del self.cache_timestamps[key]

    def get_performance_stats(self) -> Dict[str, Union[int, float]]:
        """Get performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        with self.cache_lock:
            cache_size = len(self.memory_cache)
        
        return {
            **self.stats,
            'cache_hit_rate_percent': cache_hit_rate,
            'cache_size': cache_size,
            'total_requests': total_requests
        }

    # Legacy compatibility for existing stream data methods
    def update_exchange_stream_data(self, stream_data_type, market_code, symbol, stream_data):
        """Legacy compatibility method - stores original data with all fields preserved"""
        # ALWAYS store the full original data to preserve exchange-specific field names
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        
        # Ensure timestamp is included
        if 'last_update_timestamp' not in stream_data:
            stream_data['last_update_timestamp'] = int(time.time() * 1_000_000)
            
        stream_data_json = json.dumps(stream_data)
        redis_conn.hset(redis_key, symbol, stream_data_json)
        redis_conn.set(
            f"{MARKET_STATE_VERSION_PREFIX}|{market_code}",
            str(stream_data["last_update_timestamp"]),
        )
        self.stats['redis_operations'] += 1

    def get_exchange_stream_data(self, stream_data_type, market_code, symbol):
        """Legacy compatibility method"""
        if stream_data_type == "ticker":
            return self.get_ticker_data_optimized(market_code, symbol)
        elif stream_data_type == "orderbook":
            return self.get_orderbook_data_optimized(market_code, symbol)
        else:
            # Fallback to original method
            redis_conn = self.get_redis_client()
            redis_key = f"{stream_data_type}:{market_code}"
            stream_data_json = redis_conn.hget(redis_key, symbol)
            self.stats['redis_operations'] += 1
            if stream_data_json:
                return json.loads(stream_data_json)
            return None
    
    def delete_exchange_stream_data(self, stream_data_type, market_code, symbol):
        """Legacy compatibility method"""
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        redis_conn.hdel(redis_key, symbol)
        self.stats['redis_operations'] += 1
        
        # Also remove from optimized storage
        if stream_data_type == "ticker":
            redis_conn.hdel(f"ticker_bin:{market_code}", symbol)
        elif stream_data_type == "orderbook":
            redis_conn.hdel(f"orderbook_bin:{market_code}", symbol)
        
        # Remove from memory cache
        cache_key = f"{stream_data_type}:{market_code}:{symbol}"
        with self.cache_lock:
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
                del self.cache_timestamps[cache_key]
        
    def delete_all_exchange_stream_data(self, stream_data_type, market_code):
        """Legacy compatibility method"""
        redis_conn = self.get_redis_client()
        redis_key = f"{stream_data_type}:{market_code}"
        redis_conn.delete(redis_key)
        
        # Clear memory cache for this market
        with self.cache_lock:
            keys_to_remove = [k for k in self.memory_cache.keys() 
                            if k.startswith(f"{stream_data_type}:{market_code}:")]
            for key in keys_to_remove:
                del self.memory_cache[key]
                if key in self.cache_timestamps:
                    del self.cache_timestamps[key]
        
        self.stats['redis_operations'] += 1

    def get_all_exchange_stream_data(self, stream_data_type, market_code):
        """Legacy compatibility method - ALWAYS returns original format for compatibility"""
        redis_conn = self.get_redis_client()
        
        # ALWAYS use legacy format to preserve original field names
        redis_key = f"{stream_data_type}:{market_code}"
        all_stream_data = redis_conn.hgetall(redis_key)
        self.stats['redis_operations'] += 1
        
        if not all_stream_data:
            return {}
            
        return {symbol.decode('utf-8'): json.loads(ticker_data) for symbol, ticker_data in all_stream_data.items()}
