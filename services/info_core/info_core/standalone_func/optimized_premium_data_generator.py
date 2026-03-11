from etc.redis_connector.optimized_redis_helper import OptimizedRedisHelper
from etc.redis_connector.redis_helper import RedisHelper
import pandas as pd
import json
import traceback
from loggers.logger import InfoCoreLogger
from standalone_func.get_dollar_dict import get_dollar_dict
from standalone_func.optimized_price_df_generator import get_price_df, get_price_data_manager
import numpy as np
import time
from typing import Dict, Optional, Tuple

class OptimizedPremiumDataGenerator:
    """
    Optimized premium data generator with caching and incremental processing
    for sub-50ms premium data generation.
    """
    
    def __init__(self, redis_client: OptimizedRedisHelper):
        self.redis_client = redis_client
        self.price_data_manager = get_price_data_manager(redis_client)
        
        # Cache for market DataFrames
        self.market_df_cache = {}
        self.cache_timestamps = {}
        self.cache_lock = None  # Will be set if threading is used
        self.cache_ttl = 0.1  # 100ms cache TTL for market data
        
        # Cache for convert rates
        self.convert_rate_cache = {}
        self.convert_rate_timestamp = 0
        self.convert_rate_ttl = 1.0  # 1 second TTL for convert rates
        
        # Performance stats
        self.stats = {
            'premium_calculations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_processing_time': 0.0,
            'average_processing_time_ms': 0.0
        }

    def _get_cached_market_df(self, origin_market: str, quote_asset: str) -> Optional[pd.DataFrame]:
        """Get cached market DataFrame if valid"""
        cache_key = f"{origin_market}_{quote_asset}"
        current_time = time.time()
        
        if (cache_key in self.market_df_cache and 
            cache_key in self.cache_timestamps and
            current_time - self.cache_timestamps[cache_key] < self.cache_ttl):
            self.stats['cache_hits'] += 1
            return self.market_df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        return None

    def _cache_market_df(self, origin_market: str, quote_asset: str, df: pd.DataFrame):
        """Cache market DataFrame with timestamp"""
        cache_key = f"{origin_market}_{quote_asset}"
        self.market_df_cache[cache_key] = df.copy()
        self.cache_timestamps[cache_key] = time.time()

    def _get_cached_convert_rates(self, convert_rate_dict: Dict) -> Dict:
        """Get cached convert rates or refresh if needed"""
        current_time = time.time()
        
        if (self.convert_rate_cache and 
            current_time - self.convert_rate_timestamp < self.convert_rate_ttl):
            return self.convert_rate_cache
        
        # Update cache
        self.convert_rate_cache = convert_rate_dict.copy()
        self.convert_rate_timestamp = current_time
        return self.convert_rate_cache

    def get_premium_df_optimized(self, convert_rate_dict: Dict, target_market_code: str, 
                                origin_market_code: str, logger) -> pd.DataFrame:
        """
        Optimized premium data generation with caching and vectorized operations.
        Target: sub-50ms processing time.
        """
        start_time = time.time()
        
        try:
            # Parse market codes
            origin_market = origin_market_code.split('/')[0]
            quote_asset_one = origin_market_code.split('/')[1]
            target_market = target_market_code.split('/')[0]
            quote_asset_two = target_market_code.split('/')[1]

            # Get cached convert rates
            cached_convert_rates = self._get_cached_convert_rates(convert_rate_dict)
            convert_rate = cached_convert_rates.get(f"{target_market_code}:{origin_market_code}")
            
            if convert_rate is None:
                if logger:
                    logger.warning(f"Convert rate not found for {target_market_code}:{origin_market_code}")
                return pd.DataFrame()

            # Try to get cached market DataFrames
            origin_market_df = self._get_cached_market_df(origin_market, quote_asset_one)
            target_market_df = self._get_cached_market_df(target_market, quote_asset_two)

            # If not cached, generate new ones
            if origin_market_df is None:
                origin_market_df = get_price_df(self.redis_client, origin_market)
                if not origin_market_df.empty:
                    origin_market_df = origin_market_df[origin_market_df['quote_asset'] == quote_asset_one]
                    self._cache_market_df(origin_market, quote_asset_one, origin_market_df)

            if target_market_df is None:
                target_market_df = get_price_df(self.redis_client, target_market)
                if not target_market_df.empty:
                    target_market_df = target_market_df[target_market_df['quote_asset'] == quote_asset_two]
                    self._cache_market_df(target_market, quote_asset_two, target_market_df)

            # Check if DataFrames are valid
            if origin_market_df.empty or target_market_df.empty:
                if logger:
                    logger.warning(f"Empty DataFrames: origin={len(origin_market_df)}, target={len(target_market_df)}")
                return pd.DataFrame()

            # Find common symbols using numpy for faster set operations
            origin_symbols = set(origin_market_df['base_asset'].values)
            target_symbols = set(target_market_df['base_asset'].values)
            shared_base_asset_list = list(origin_symbols & target_symbols)
            
            if not shared_base_asset_list:
                if logger:
                    logger.warning("No shared symbols between markets")
                return pd.DataFrame()

            # Filter and sort DataFrames - use vectorized operations
            origin_mask = origin_market_df['base_asset'].isin(shared_base_asset_list)
            target_mask = target_market_df['base_asset'].isin(shared_base_asset_list)
            
            origin_filtered = origin_market_df[origin_mask].sort_values('base_asset').reset_index(drop=True)
            target_filtered = target_market_df[target_mask].sort_values('base_asset').reset_index(drop=True)

            # Ensure we have the same number of rows after filtering
            if len(origin_filtered) != len(target_filtered):
                # Use merge to ensure proper alignment
                merged_base = pd.merge(
                    origin_filtered[['base_asset', 'tp', 'ap', 'bp']],
                    target_filtered[['base_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']],
                    on='base_asset',
                    suffixes=('_origin', '_target')
                )
                
                if merged_base.empty:
                    return pd.DataFrame()
                
                # Extract aligned data
                origin_prices = merged_base[['tp_origin', 'ap_origin', 'bp_origin']].values
                target_prices = merged_base[['tp_target', 'ap_target', 'bp_target']].values
                target_metadata = merged_base[['base_asset', 'scr', 'atp24h']].copy()
                target_metadata['quote_asset'] = quote_asset_two
                target_metadata['tp'] = merged_base['tp_target']
                target_metadata['ap'] = merged_base['ap_target']
                target_metadata['bp'] = merged_base['bp_target']
                
            else:
                # Direct vectorized operations (faster path)
                origin_prices = origin_filtered[['tp', 'ap', 'bp']].values
                target_prices = target_filtered[['tp', 'ap', 'bp']].values
                target_metadata = target_filtered[['base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']].copy()

            # Vectorized price conversion
            converted_prices = origin_prices * convert_rate

            # Vectorized premium calculations
            # premium = (target_price - converted_origin_price) / converted_origin_price * 100
            premium_calculations = (target_prices - converted_prices) / converted_prices * 100

            # Create premium DataFrame with vectorized operations
            premium_df = pd.DataFrame({
                'tp_premium': premium_calculations[:, 0],
                'LS_premium': premium_calculations[:, 1], 
                'SL_premium': premium_calculations[:, 2]
            })
            
            premium_df['LS_SL_spread'] = premium_df['LS_premium'] - premium_df['SL_premium']
            
            # Add metadata
            premium_df = pd.concat([premium_df, target_metadata], axis=1)
            
            # Add converted prices
            premium_df['converted_tp'] = converted_prices[:, 0]
            premium_df['converted_ap'] = converted_prices[:, 1]
            premium_df['converted_bp'] = converted_prices[:, 2]
            
            # Sort by volume (atp24h) in descending order
            premium_df = premium_df.sort_values('atp24h', ascending=False).reset_index(drop=True)
            
            # Add dollar rate (cached)
            premium_df['dollar'] = get_dollar_dict(self.redis_client)['price']
            
            # Update performance stats
            processing_time = time.time() - start_time
            self.stats['premium_calculations'] += 1
            self.stats['total_processing_time'] += processing_time
            self.stats['average_processing_time_ms'] = (
                self.stats['total_processing_time'] / self.stats['premium_calculations'] * 1000
            )
            
            # Log performance for monitoring
            if logger and self.stats['premium_calculations'] % 100 == 0:  # Log every 100 calculations
                logger.info(f"Premium calculation stats: avg={self.stats['average_processing_time_ms']:.2f}ms, "
                           f"cache_hit_rate={self.stats['cache_hits']/(self.stats['cache_hits']+self.stats['cache_misses'])*100:.1f}%")
            
            return premium_df
            
        except Exception as e:
            if logger:
                logger.error(f"get_premium_df_optimized|Exception occurred! Error: {e}, traceback: {traceback.format_exc()}")
            raise e

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'cache_hit_rate_percent': cache_hit_rate,
            'total_requests': total_requests,
            'cache_size': len(self.market_df_cache)
        }

    def cleanup_cache(self, max_age: float = 1.0):
        """Clean up old cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, timestamp in self.cache_timestamps.items()
            if current_time - timestamp > max_age
        ]
        for key in expired_keys:
            if key in self.market_df_cache:
                del self.market_df_cache[key]
            if key in self.cache_timestamps:
                del self.cache_timestamps[key]

# Global instance for optimized premium data generator
_premium_data_generator = None
_premium_generator_lock = None

def get_premium_data_generator(redis_client: OptimizedRedisHelper) -> OptimizedPremiumDataGenerator:
    """Get or create global premium data generator instance"""
    global _premium_data_generator
    if _premium_data_generator is None:
        _premium_data_generator = OptimizedPremiumDataGenerator(redis_client)
    return _premium_data_generator

def get_premium_df(redis_client, convert_rate_dict, target_market_code, origin_market_code, logger):
    """
    Main entry point for premium data generation.
    Automatically uses optimized path if OptimizedRedisHelper is provided.
    """
    if isinstance(redis_client, OptimizedRedisHelper):
        # Use optimized path
        generator = get_premium_data_generator(redis_client)
        return generator.get_premium_df_optimized(
            convert_rate_dict, target_market_code, origin_market_code, logger
        )
    else:
        # Fallback to original implementation for legacy RedisHelper
        try:
            # POSSIBLE quote_assets: USDT, BUSD, BTC, KRW
            origin_market = origin_market_code.split('/')[0]
            quote_asset_one = origin_market_code.split('/')[1]
            target_market = target_market_code.split('/')[0]
            quote_asset_two = target_market_code.split('/')[1]

            origin_market_df = get_price_df(redis_client, origin_market)
            origin_market_df = origin_market_df[origin_market_df['quote_asset'] == quote_asset_one]
            target_market_df = get_price_df(redis_client, target_market)
            target_market_df = target_market_df[target_market_df['quote_asset'] == quote_asset_two]

            shared_base_asset_list = list(set(origin_market_df['base_asset'].values).intersection(set(target_market_df['base_asset'].values)))
            origin_market_df = origin_market_df[origin_market_df['base_asset'].isin(shared_base_asset_list)].sort_values('base_asset').reset_index(drop=True)
            target_market_df = target_market_df[target_market_df['base_asset'].isin(shared_base_asset_list)].sort_values('base_asset').reset_index(drop=True)

            convert_rate = convert_rate_dict[f"{target_market_code}:{origin_market_code}"]
            origin_market_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['tp','ap','bp']] * convert_rate

            # divide by target_market_df[['tp','ap','bp']]
            premium_df = pd.DataFrame((target_market_df[['tp','ap','bp']].values - origin_market_df[['converted_tp','converted_bp','converted_ap']].values)/
                                    origin_market_df[['converted_tp','converted_bp','converted_ap']].values, columns=['tp_premium','LS_premium','SL_premium'])
            premium_df['LS_SL_spread'] = premium_df['LS_premium'] - premium_df['SL_premium']
            premium_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']] = target_market_df[['base_asset','quote_asset','tp','ap','bp','scr','atp24h']]
            premium_df[['converted_tp','converted_ap','converted_bp']] = origin_market_df[['converted_tp','converted_ap', 'converted_bp']]
            premium_df.loc[:, ['tp_premium','LS_premium','SL_premium','LS_SL_spread']] = premium_df[['tp_premium','LS_premium','SL_premium','LS_SL_spread']] * 100
            premium_df = premium_df.sort_values('atp24h', ascending=False).reset_index(drop=True)
            premium_df['dollar'] = get_dollar_dict(redis_client)['price']
        except Exception as e:
            if logger:
                logger.error(f"get_premium_df|Exception occurred! Error: {e}, traceback: {traceback.format_exc()}")
            raise e
        return premium_df