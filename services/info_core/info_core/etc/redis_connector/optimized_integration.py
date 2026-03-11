"""
Optimized Redis Integration Module

This module provides a seamless integration layer for the optimized Redis system.
It handles the migration from legacy RedisHelper to OptimizedRedisHelper while
maintaining backward compatibility.
"""

import os
import sys
from typing import Union, Optional
import threading
import time

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etc.redis_connector.redis_helper import RedisHelper
from etc.redis_connector.optimized_redis_helper import OptimizedRedisHelper
from exchange_websocket.optimized_websocket_handler import OptimizedWebsocketHandler, create_optimized_websocket_handler
from standalone_func.optimized_price_df_generator import get_price_data_manager
from standalone_func.optimized_premium_data_generator import get_premium_data_generator

class OptimizedRedisIntegration:
    """
    Integration layer that manages the transition to optimized Redis operations.
    Provides factory methods and migration utilities.
    """
    
    def __init__(self, redis_config: dict, enable_optimizations: bool = True):
        self.redis_config = redis_config
        self.enable_optimizations = enable_optimizations
        self._optimized_client = None
        self._legacy_client = None
        self._websocket_handlers = {}
        self._performance_monitor = None
        self._lock = threading.RLock()
        
        # Performance monitoring
        self.stats = {
            'optimized_operations': 0,
            'legacy_operations': 0,
            'optimization_enabled_time': time.time() if enable_optimizations else None
        }

    def get_redis_client(self, force_legacy: bool = False) -> Union[OptimizedRedisHelper, RedisHelper]:
        """
        Get Redis client - optimized by default, legacy if requested or if optimizations disabled.
        """
        with self._lock:
            if force_legacy or not self.enable_optimizations:
                if self._legacy_client is None:
                    self._legacy_client = RedisHelper(**self.redis_config)
                self.stats['legacy_operations'] += 1
                return self._legacy_client
            else:
                if self._optimized_client is None:
                    self._optimized_client = OptimizedRedisHelper(**self.redis_config, pool_size=15)
                self.stats['optimized_operations'] += 1
                return self._optimized_client

    def get_websocket_handler(self, market_code: str, force_legacy: bool = False) -> OptimizedWebsocketHandler:
        """
        Get websocket handler for a specific market.
        """
        if force_legacy or not self.enable_optimizations:
            # Return None to indicate legacy handling should be used
            return None
        
        with self._lock:
            if market_code not in self._websocket_handlers:
                redis_client = self.get_redis_client()
                self._websocket_handlers[market_code] = create_optimized_websocket_handler(
                    redis_client, market_code
                )
            return self._websocket_handlers[market_code]

    def enable_optimization_monitoring(self, interval: int = 60):
        """
        Enable performance monitoring with specified interval in seconds.
        """
        def monitor_performance():
            while True:
                time.sleep(interval)
                self._log_performance_stats()
        
        if self._performance_monitor is None:
            monitor_thread = threading.Thread(target=monitor_performance, daemon=True)
            monitor_thread.start()
            self._performance_monitor = monitor_thread

    def _log_performance_stats(self):
        """Log performance statistics"""
        redis_client = self.get_redis_client()
        if isinstance(redis_client, OptimizedRedisHelper):
            redis_stats = redis_client.get_performance_stats()
            
            # Get price data manager stats
            price_manager = get_price_data_manager(redis_client)
            price_stats = price_manager.get_performance_stats()
            
            # Get premium data generator stats
            premium_generator = get_premium_data_generator(redis_client)
            premium_stats = premium_generator.get_performance_stats()
            
            print(f"""
=== Optimized Redis Performance Stats ===
Redis Operations: {redis_stats['redis_operations']}
Cache Hit Rate: {redis_stats['cache_hit_rate_percent']:.1f}%
Cache Size: {redis_stats['cache_size']} items
Serialization Time: {redis_stats['serialization_time']:.3f}s

Price Data Manager:
- Cache Hit Rate: {price_stats['cache_hit_rate_percent']:.1f}%
- DF Rebuilds: {price_stats['df_rebuilds']}
- Cache Size: {price_stats['cache_size']} DataFrames

Premium Data Generator:
- Calculations: {premium_stats['premium_calculations']}
- Avg Processing Time: {premium_stats['average_processing_time_ms']:.2f}ms
- Cache Hit Rate: {premium_stats['cache_hit_rate_percent']:.1f}%

Integration Stats:
- Optimized Operations: {self.stats['optimized_operations']}
- Legacy Operations: {self.stats['legacy_operations']}
- Optimization Rate: {self.stats['optimized_operations']/(self.stats['optimized_operations']+self.stats['legacy_operations'])*100:.1f}%
==========================================""")

    def migrate_to_optimized(self, market_codes: list = None):
        """
        Migrate specific markets or all markets to optimized storage.
        This copies data from legacy format to optimized binary format.
        """
        redis_client = self.get_redis_client()
        legacy_client = self.get_redis_client(force_legacy=True)
        
        if not isinstance(redis_client, OptimizedRedisHelper):
            print("Cannot migrate: optimized client not available")
            return
        
        if market_codes is None:
            # Auto-detect market codes from Redis keys
            all_keys = legacy_client.get_all_keys()
            market_codes = set()
            for key in all_keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                if ':' in key_str and ('ticker:' in key_str or 'orderbook:' in key_str):
                    market_code = key_str.split(':', 1)[1]
                    market_codes.add(market_code)
            market_codes = list(market_codes)
        
        print(f"Migrating {len(market_codes)} markets to optimized storage...")
        
        for market_code in market_codes:
            try:
                # Migrate ticker data
                ticker_data = legacy_client.get_all_exchange_stream_data("ticker", market_code)
                if ticker_data:
                    for symbol, data in ticker_data.items():
                        if isinstance(data, dict):
                            price = float(data.get('c', 0))
                            volume = float(data.get('v', 0))
                            change = float(data.get('P', 0))
                            timestamp = int(data.get('last_update_timestamp', time.time() * 1_000_000))
                            
                            redis_client.update_ticker_data_optimized(
                                market_code, symbol, price, volume, change, timestamp
                            )
                
                # Migrate orderbook data
                orderbook_data = legacy_client.get_all_exchange_stream_data("orderbook", market_code)
                if orderbook_data:
                    for symbol, data in orderbook_data.items():
                        if isinstance(data, dict):
                            bid_price = float(data.get('b', 0))
                            ask_price = float(data.get('a', 0))
                            bid_qty = float(data.get('B', 0))
                            ask_qty = float(data.get('A', 0))
                            timestamp = int(data.get('last_update_timestamp', time.time() * 1_000_000))
                            
                            redis_client.update_orderbook_data_optimized(
                                market_code, symbol, bid_price, ask_price, bid_qty, ask_qty, timestamp
                            )
                
                print(f"Migrated {market_code}: {len(ticker_data)} tickers, {len(orderbook_data)} orderbooks")
                
            except Exception as e:
                print(f"Failed to migrate {market_code}: {e}")
        
        print("Migration completed!")

    def benchmark_performance(self, iterations: int = 1000) -> dict:
        """
        Benchmark performance comparison between optimized and legacy systems.
        """
        print(f"Running performance benchmark with {iterations} iterations...")
        
        # Benchmark data
        test_data = {
            'symbol': 'BTCUSDT',
            'price': 45000.0,
            'volume': 1000000.0,
            'change': 2.5,
            'bid_price': 44990.0,
            'ask_price': 45010.0,
            'bid_qty': 10.0,
            'ask_qty': 8.5
        }
        
        # Benchmark optimized system
        optimized_client = self.get_redis_client()
        optimized_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Ticker update
            optimized_client.update_ticker_data_optimized(
                "TEST_MARKET", test_data['symbol'], 
                test_data['price'], test_data['volume'], test_data['change']
            )
            
            # Orderbook update
            optimized_client.update_orderbook_data_optimized(
                "TEST_MARKET", test_data['symbol'],
                test_data['bid_price'], test_data['ask_price'],
                test_data['bid_qty'], test_data['ask_qty']
            )
            
            # Read operations
            optimized_client.get_ticker_data_optimized("TEST_MARKET", test_data['symbol'])
            optimized_client.get_orderbook_data_optimized("TEST_MARKET", test_data['symbol'])
            
            optimized_times.append(time.time() - start_time)
        
        # Benchmark legacy system
        legacy_client = self.get_redis_client(force_legacy=True)
        legacy_times = []
        
        for _ in range(iterations):
            start_time = time.time()
            
            # Legacy ticker update
            legacy_client.update_exchange_stream_data(
                "ticker", "TEST_MARKET", test_data['symbol'],
                {
                    'c': test_data['price'],
                    'v': test_data['volume'],
                    'P': test_data['change']
                }
            )
            
            # Legacy orderbook update  
            legacy_client.update_exchange_stream_data(
                "orderbook", "TEST_MARKET", test_data['symbol'],
                {
                    'b': test_data['bid_price'],
                    'a': test_data['ask_price'],
                    'B': test_data['bid_qty'],
                    'A': test_data['ask_qty']
                }
            )
            
            # Read operations
            legacy_client.get_exchange_stream_data("ticker", "TEST_MARKET", test_data['symbol'])
            legacy_client.get_exchange_stream_data("orderbook", "TEST_MARKET", test_data['symbol'])
            
            legacy_times.append(time.time() - start_time)
        
        # Calculate statistics
        optimized_avg = sum(optimized_times) / len(optimized_times) * 1000  # ms
        legacy_avg = sum(legacy_times) / len(legacy_times) * 1000  # ms
        improvement = (legacy_avg - optimized_avg) / legacy_avg * 100
        
        # Cleanup test data
        optimized_client.delete_all_exchange_stream_data("ticker", "TEST_MARKET")
        optimized_client.delete_all_exchange_stream_data("orderbook", "TEST_MARKET")
        legacy_client.delete_all_exchange_stream_data("ticker", "TEST_MARKET")
        legacy_client.delete_all_exchange_stream_data("orderbook", "TEST_MARKET")
        
        results = {
            'optimized_avg_ms': optimized_avg,
            'legacy_avg_ms': legacy_avg,
            'improvement_percent': improvement,
            'iterations': iterations
        }
        
        print(f"""
=== Performance Benchmark Results ===
Iterations: {iterations}
Optimized Average: {optimized_avg:.3f}ms
Legacy Average: {legacy_avg:.3f}ms
Performance Improvement: {improvement:.1f}%
=====================================""")
        
        return results

    def get_integration_stats(self) -> dict:
        """Get integration statistics"""
        redis_client = self.get_redis_client()
        stats = {
            'optimization_enabled': self.enable_optimizations,
            'optimized_operations': self.stats['optimized_operations'],
            'legacy_operations': self.stats['legacy_operations'],
            'active_websocket_handlers': len(self._websocket_handlers)
        }
        
        if isinstance(redis_client, OptimizedRedisHelper):
            stats['redis_performance'] = redis_client.get_performance_stats()
        
        return stats

# Global integration instance
_global_integration = None
_integration_lock = threading.Lock()

def get_redis_integration(redis_config: dict = None, enable_optimizations: bool = True) -> OptimizedRedisIntegration:
    """
    Get or create global Redis integration instance.
    """
    global _global_integration
    
    with _integration_lock:
        if _global_integration is None:
            if redis_config is None:
                # Use default localhost config
                redis_config = {
                    'host': 'localhost',
                    'port': 6379,
                    'passwd': None,
                    'db': 0
                }
            _global_integration = OptimizedRedisIntegration(redis_config, enable_optimizations)
        return _global_integration

def create_optimized_redis_client(host="localhost", port=6379, passwd=None, db=0, pool_size=10) -> OptimizedRedisHelper:
    """
    Factory function to create an optimized Redis client.
    """
    return OptimizedRedisHelper(host=host, port=port, passwd=passwd, db=db, pool_size=pool_size)

def migrate_existing_system(redis_config: dict, market_codes: list = None):
    """
    Convenience function to migrate an existing system to optimized Redis.
    """
    integration = OptimizedRedisIntegration(redis_config, enable_optimizations=True)
    integration.migrate_to_optimized(market_codes)
    return integration