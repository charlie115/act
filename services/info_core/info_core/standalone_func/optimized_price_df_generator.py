import pandas as pd
from etc.redis_connector.optimized_redis_helper import OptimizedRedisHelper
from etc.redis_connector.redis_helper import RedisHelper
import numpy as np
import traceback
import _pickle as pickle
import time
from typing import Dict, Optional, Tuple
import threading

class OptimizedPriceDataManager:
    """
    Optimized price data manager with caching and incremental updates
    for high-frequency price data processing.
    """
    
    def __init__(self, redis_client: OptimizedRedisHelper):
        self.redis_client = redis_client
        self.df_cache = {}
        self.cache_timestamps = {}
        self.cache_lock = threading.RLock()
        self.cache_ttl = 0.5  # 500ms cache TTL for price data
        
        # Performance stats
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'df_rebuilds': 0,
            'incremental_updates': 0
        }

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached DataFrame is still valid"""
        if cache_key not in self.cache_timestamps:
            return False
        return (time.time() - self.cache_timestamps[cache_key]) < self.cache_ttl

    def _update_cache(self, cache_key: str, df: pd.DataFrame):
        """Update DataFrame cache with timestamp"""
        with self.cache_lock:
            self.df_cache[cache_key] = df.copy()
            self.cache_timestamps[cache_key] = time.time()

    def get_binance_price_df_optimized(self, market_type: str) -> pd.DataFrame:
        """Optimized Binance price DataFrame generation"""
        cache_key = f"binance_{market_type.lower()}_price_df"
        
        # Try cache first
        with self.cache_lock:
            if cache_key in self.df_cache and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        self.stats['df_rebuilds'] += 1
        
        start_time = time.time()
        
        # Get ticker and orderbook data using optimized methods
        market_code = f"BINANCE_{market_type.upper()}"
        ticker_data = self.redis_client.get_all_ticker_data_optimized(market_code)
        orderbook_data = self.redis_client.get_all_orderbook_data_optimized(market_code)
        
        if not ticker_data or not orderbook_data:
            # Fallback to legacy method if optimized data not available
            return self._get_binance_price_df_legacy(market_type)
        
        # Convert to DataFrame format
        ticker_records = []
        for symbol, data in ticker_data.items():
            ticker_records.append({
                's': symbol,
                'c': data['price'],
                'v': data['volume'], 
                'P': data['change']
            })
        
        orderbook_records = []
        for symbol, data in orderbook_data.items():
            if symbol in ticker_data:  # Only include symbols that have ticker data
                orderbook_records.append({
                    's': symbol,
                    'b': data['bid_price'],
                    'a': data['ask_price']
                })
        
        # Create DataFrames
        if not ticker_records or not orderbook_records:
            return pd.DataFrame()
        
        ticker_df = pd.DataFrame(ticker_records)
        orderbook_df = pd.DataFrame(orderbook_records)
        
        # Rename columns to match expected format
        ticker_df.rename(columns={"v": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        orderbook_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        
        # Merge ticker and orderbook data
        merged_df = pd.merge(ticker_df, orderbook_df, on='s', how='inner')
        
        if merged_df.empty:
            return pd.DataFrame()
        
        # Convert to numeric types
        merged_df[['scr','tp','atp24h','ap','bp']] = merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        
        # Get info DataFrame from Redis (cached)
        try:
            info_df = pickle.loads(self.redis_client.get_data(f'binance_{market_type.lower()}_info_df'))
            if info_df is not None:
                info_df = info_df[['symbol','base_asset','quote_asset']]
                merged_df = merged_df.merge(info_df, left_on='s', right_on='symbol', how='inner')
                merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        except:
            # If info_df not available, create minimal structure
            merged_df['base_asset'] = merged_df['s'].str.extract(r'([A-Z]+)(?:USDT|BTC|ETH)')
            merged_df['quote_asset'] = 'USDT'  # Default assumption
            merged_df.drop(['s'], axis=1, inplace=True)
        
        # Cache the result
        self._update_cache(cache_key, merged_df)
        
        print(f"Binance {market_type} DF generation took {time.time() - start_time:.4f}s, {len(merged_df)} rows")
        return merged_df

    def _get_binance_price_df_legacy(self, market_type: str) -> pd.DataFrame:
        """Fallback to legacy method"""
        try:
            # Use legacy Redis client for fallback
            legacy_redis = RedisHelper(
                host=self.redis_client.host,
                port=self.redis_client.port,
                passwd=self.redis_client.passwd
            )
            return get_binance_price_df(legacy_redis, market_type)
        except:
            return pd.DataFrame()

    def get_okx_price_df_optimized(self, market_type: str) -> pd.DataFrame:
        """Optimized OKX price DataFrame generation"""
        cache_key = f"okx_{market_type.lower()}_price_df"
        
        with self.cache_lock:
            if cache_key in self.df_cache and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        self.stats['df_rebuilds'] += 1
        
        start_time = time.time()
        
        # Get ticker data using optimized methods
        market_code = f"OKX_{market_type.upper()}"
        ticker_data = self.redis_client.get_all_ticker_data_optimized(market_code)
        
        if not ticker_data:
            return self._get_okx_price_df_legacy(market_type)
        
        # Convert to DataFrame
        records = []
        for symbol, data in ticker_data.items():
            # Parse OKX symbol format (e.g., BTC-USDT)
            parts = symbol.split('-')
            if len(parts) >= 2:
                base_asset = parts[0]
                quote_asset = parts[1]
                
                records.append({
                    'instId': symbol,
                    'base_asset': base_asset,
                    'quote_asset': quote_asset,
                    'tp': data['price'],
                    'ap': data.get('ask_price', data['price']),  # Fallback to price if no ask
                    'bp': data.get('bid_price', data['price']),  # Fallback to price if no bid
                    'atp24h': data['volume'],
                    'scr': data['change']
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df[['tp', 'ap', 'bp', 'atp24h', 'scr']] = df[['tp', 'ap', 'bp', 'atp24h', 'scr']].astype(float)
        
        # Adjust volume calculation for non-SPOT markets
        if market_type != "SPOT":
            df['atp24h'] = df['tp'] * df['atp24h']
        
        df = df[['instId', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']]
        
        self._update_cache(cache_key, df)
        print(f"OKX {market_type} DF generation took {time.time() - start_time:.4f}s, {len(df)} rows")
        return df

    def _get_okx_price_df_legacy(self, market_type: str) -> pd.DataFrame:
        """Fallback to legacy OKX method"""
        try:
            legacy_redis = RedisHelper(
                host=self.redis_client.host,
                port=self.redis_client.port,
                passwd=self.redis_client.passwd
            )
            return get_okx_price_df(legacy_redis, market_type)
        except:
            return pd.DataFrame()

    def get_upbit_price_df_optimized(self) -> pd.DataFrame:
        """Optimized Upbit price DataFrame generation"""
        cache_key = "upbit_spot_price_df"
        
        with self.cache_lock:
            if cache_key in self.df_cache and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        self.stats['df_rebuilds'] += 1
        
        start_time = time.time()
        
        # Get ticker and orderbook data
        market_code = "UPBIT_SPOT"
        ticker_data = self.redis_client.get_all_ticker_data_optimized(market_code)
        orderbook_data = self.redis_client.get_all_orderbook_data_optimized(market_code)
        
        if not ticker_data or not orderbook_data:
            return self._get_upbit_price_df_legacy()
        
        # Convert to expected format
        ticker_records = []
        for symbol, data in ticker_data.items():
            ticker_records.append({
                'index': symbol,
                'tp': data['price'],
                'scr': data['change'],
                'atp24h': data['volume']
            })
        
        orderbook_records = []
        for symbol, data in orderbook_data.items():
            if symbol in ticker_data:
                orderbook_records.append({
                    'cd': symbol,
                    'ap': data['ask_price'],
                    'bp': data['bid_price']
                })
        
        if not ticker_records or not orderbook_records:
            return pd.DataFrame()
        
        ticker_df = pd.DataFrame(ticker_records)
        orderbook_df = pd.DataFrame(orderbook_records)
        
        # Merge data
        merged_df = pd.merge(ticker_df, orderbook_df, left_on='index', right_on='cd', how='inner')
        merged_df = merged_df.dropna(subset=['tp', 'ap', 'bp'])
        
        # Parse symbol format (KRW-BTC -> base_asset=BTC, quote_asset=KRW)
        merged_df['base_asset'] = merged_df['index'].apply(lambda x: x.split('-')[1] if '-' in x else x)
        merged_df['quote_asset'] = merged_df['index'].apply(lambda x: x.split('-')[0] if '-' in x else 'KRW')
        merged_df.drop(['index', 'cd'], axis=1, inplace=True)
        
        # Convert to float and adjust change rate
        merged_df[['scr','atp24h','ap','bp']] = merged_df[['scr','atp24h','ap','bp']].astype(float)
        merged_df['scr'] = merged_df['scr'] * 100  # Convert to percentage
        
        self._update_cache(cache_key, merged_df)
        print(f"Upbit DF generation took {time.time() - start_time:.4f}s, {len(merged_df)} rows")
        return merged_df

    def _get_upbit_price_df_legacy(self) -> pd.DataFrame:
        """Fallback to legacy Upbit method"""
        try:
            legacy_redis = RedisHelper(
                host=self.redis_client.host,
                port=self.redis_client.port,
                passwd=self.redis_client.passwd
            )
            return get_upbit_price_df(legacy_redis)
        except:
            return pd.DataFrame()

    def get_bybit_price_df_optimized(self, market_type: str) -> pd.DataFrame:
        """Optimized Bybit price DataFrame generation"""
        cache_key = f"bybit_{market_type.lower()}_price_df"
        
        with self.cache_lock:
            if cache_key in self.df_cache and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        self.stats['df_rebuilds'] += 1
        
        start_time = time.time()
        
        # Get data using optimized methods
        market_code = f"BYBIT_{market_type.upper()}"
        ticker_data = self.redis_client.get_all_ticker_data_optimized(market_code)
        orderbook_data = self.redis_client.get_all_orderbook_data_optimized(market_code)
        
        if not ticker_data or not orderbook_data:
            return self._get_bybit_price_df_legacy(market_type)
        
        # Convert to DataFrame format
        records = []
        for symbol, ticker in ticker_data.items():
            if symbol in orderbook_data:
                orderbook = orderbook_data[symbol]
                records.append({
                    'symbol': symbol,
                    'lastPrice': ticker['price'],
                    'price24hPcnt': ticker['change'],
                    'volume24h': ticker['volume'] if market_type == "COIN_M" else None,
                    'turnover24h': ticker['volume'] if market_type != "COIN_M" else None,
                    'b': orderbook['bid_price'],
                    'a': orderbook['ask_price']
                })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        
        # Get info DataFrame for base/quote assets
        try:
            info_df = pickle.loads(self.redis_client.get_data(f'bybit_{market_type.lower()}_info_df'))
            if info_df is not None:
                info_df = info_df[['symbol','base_asset','quote_asset']]
                df = df.merge(info_df, on='symbol', how='inner')
        except:
            # Fallback: parse from symbol
            df['base_asset'] = df['symbol'].str.extract(r'([A-Z]+)(?:USDT|USD)')
            df['quote_asset'] = 'USDT'
        
        # Convert and rename columns
        df['price24hPcnt'] = df['price24hPcnt'].astype(float) * 100
        if market_type == "COIN_M":
            df = df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'volume24h':'atp24h'})
        else:
            df = df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'turnover24h':'atp24h'})
        
        df[['tp','ap','bp','scr','atp24h']] = df[['tp','ap','bp','scr','atp24h']].astype(float)
        df = df[['symbol','base_asset','quote_asset','tp','bp','ap','scr','atp24h']]
        
        self._update_cache(cache_key, df)
        print(f"Bybit {market_type} DF generation took {time.time() - start_time:.4f}s, {len(df)} rows")
        return df

    def _get_bybit_price_df_legacy(self, market_type: str) -> pd.DataFrame:
        """Fallback to legacy Bybit method"""
        try:
            legacy_redis = RedisHelper(
                host=self.redis_client.host,
                port=self.redis_client.port,
                passwd=self.redis_client.passwd
            )
            return get_bybit_price_df(legacy_redis, market_type)
        except:
            return pd.DataFrame()

    def get_bithumb_price_df_optimized(self) -> pd.DataFrame:
        """Optimized Bithumb price DataFrame generation"""
        cache_key = "bithumb_spot_price_df"
        
        with self.cache_lock:
            if cache_key in self.df_cache and self._is_cache_valid(cache_key):
                self.stats['cache_hits'] += 1
                return self.df_cache[cache_key].copy()
        
        self.stats['cache_misses'] += 1
        self.stats['df_rebuilds'] += 1
        
        start_time = time.time()
        
        # Get data using optimized methods
        market_code = "BITHUMB_SPOT"
        ticker_data = self.redis_client.get_all_ticker_data_optimized(market_code)
        orderbook_data = self.redis_client.get_all_orderbook_data_optimized(market_code)
        
        if not ticker_data or not orderbook_data:
            return self._get_bithumb_price_df_legacy()
        
        # Convert to expected format
        records = []
        for symbol, ticker in ticker_data.items():
            if symbol in orderbook_data and orderbook_data[symbol]['bid_price'] > 0:
                orderbook = orderbook_data[symbol]
                # Parse symbol (e.g., BTC_KRW)
                parts = symbol.split('_')
                if len(parts) == 2:
                    base_asset, quote_asset = parts
                    records.append({
                        'symbol': symbol,
                        'base_asset': base_asset,
                        'quote_asset': quote_asset,
                        'tp': ticker['price'],
                        'scr': ticker['change'],
                        'atp24h': ticker['volume'],
                        'ap': orderbook['ask_price'],
                        'bp': orderbook['bid_price']
                    })
        
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df[['scr','atp24h','tp','ap','bp']] = df[['scr','atp24h','tp','ap','bp']].astype(float)
        
        self._update_cache(cache_key, df)
        print(f"Bithumb DF generation took {time.time() - start_time:.4f}s, {len(df)} rows")
        return df

    def _get_bithumb_price_df_legacy(self) -> pd.DataFrame:
        """Fallback to legacy Bithumb method"""
        try:
            legacy_redis = RedisHelper(
                host=self.redis_client.host,
                port=self.redis_client.port,
                passwd=self.redis_client.passwd
            )
            return get_bithumb_price_df(legacy_redis)
        except:
            return pd.DataFrame()

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total_requests = self.stats['cache_hits'] + self.stats['cache_misses']
        cache_hit_rate = (self.stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0
        
        with self.cache_lock:
            cache_size = len(self.df_cache)
        
        return {
            **self.stats,
            'cache_hit_rate_percent': cache_hit_rate,
            'cache_size': cache_size,
            'total_requests': total_requests
        }

# Global instance for optimized price data manager
_price_data_manager = None
_price_data_manager_lock = threading.Lock()

def get_price_data_manager(redis_client: OptimizedRedisHelper) -> OptimizedPriceDataManager:
    """Get or create global price data manager instance"""
    global _price_data_manager
    with _price_data_manager_lock:
        if _price_data_manager is None:
            _price_data_manager = OptimizedPriceDataManager(redis_client)
        return _price_data_manager

# Legacy compatibility functions
def get_binance_price_df(redis_client, market_type):
    """Legacy compatibility function"""
    if isinstance(redis_client, OptimizedRedisHelper):
        manager = get_price_data_manager(redis_client)
        return manager.get_binance_price_df_optimized(market_type)
    else:
        # Original implementation for legacy RedisHelper
        binance_ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"BINANCE_{market_type}")).T.reset_index(drop=True)[['s','P','c','v','q']]
        binance_ticker_df.rename(columns={"q": "atp24h", 'P': 'scr', 'c': 'tp'}, inplace=True)
        binance_bookticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", f"BINANCE_{market_type}")).T.reset_index(drop=True)[['s','b','a']]
        binance_bookticker_df.rename(columns={"b": "bp", "a": "ap"}, inplace=True)
        binance_merged_df = pd.merge(binance_ticker_df, binance_bookticker_df, on='s', how='inner')
        binance_merged_df[['scr','tp','atp24h','ap','bp']] = binance_merged_df[['scr','tp','atp24h','ap','bp']].astype(float)
        binance_info_df = pickle.loads(redis_client.get_data(f'binance_{market_type.lower()}_info_df'))[['symbol','base_asset','quote_asset']]
        binance_merged_df = binance_merged_df.merge(binance_info_df, left_on='s', right_on='symbol', how='inner')
        binance_merged_df.drop(['symbol', 's'], axis=1, inplace=True)
        return binance_merged_df

def get_bithumb_price_df(redis_client):
    """Legacy compatibility function"""
    if isinstance(redis_client, OptimizedRedisHelper):
        manager = get_price_data_manager(redis_client)
        return manager.get_bithumb_price_df_optimized()
    else:
        # Original implementation
        orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", "BITHUMB_SPOT")).T.reset_index()
        ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", "BITHUMB_SPOT")).T.reset_index()

        # Drop records where bids data is an empty list
        orderbook_df = orderbook_df[orderbook_df['bids'].apply(lambda x: len(x) > 0)]
        
        # Extract the first price from asks and bids
        orderbook_df['best_ask'] = orderbook_df['asks'].apply(lambda x: x[0][0])
        orderbook_df['best_bid'] = orderbook_df['bids'].apply(lambda x: x[0][0])

        # Continue only if the DataFrame is not empty after dropping rows
        if orderbook_df.empty:
            print("WARN: Bithumb orderbook DataFrame became empty after removing rows with invalid asks/bids.")
            return pd.DataFrame(columns=['symbol', 'best_ask', 'best_bid', 'tp', 'scr', 'atp24h', 'base_asset', 'quote_asset', 'ap', 'bp'])

        merged_df = orderbook_df.merge(ticker_df[['symbol','closePrice','chgRate','value']], on='symbol', how='inner')
        merged_df[['base_asset', 'quote_asset']] = merged_df['symbol'].str.split('_', expand=True)
        merged_df = merged_df.rename(columns={'value':'atp24h', 'chgRate':'scr', 'closePrice': 'tp', 'best_ask':'ap', 'best_bid':'bp'})

        # Convert to float
        merged_df[['scr','atp24h','tp','ap','bp']] = merged_df[['scr','atp24h','tp','ap','bp']].astype(float)
        return merged_df

def get_bybit_price_df(redis_client, market_type):
    """Legacy compatibility function"""
    if isinstance(redis_client, OptimizedRedisHelper):
        manager = get_price_data_manager(redis_client)
        return manager.get_bybit_price_df_optimized(market_type)
    else:
        # Original implementation
        ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"BYBIT_{market_type}")).T.reset_index()
        orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", f"BYBIT_{market_type}")).T.reset_index()
        merged_df = ticker_df.merge(orderbook_df, left_on='symbol', right_on='s', how='inner')
        bybit_info_df = pickle.loads(redis_client.get_data(f'bybit_{market_type.lower()}_info_df'))[['symbol','base_asset','quote_asset']]
        merged_df = merged_df.merge(bybit_info_df, on='symbol', how='inner')
        merged_df['b'] = merged_df['b'].apply(lambda x: x[0][0])
        merged_df['a'] = merged_df['a'].apply(lambda x: x[0][0])
        merged_df['price24hPcnt'] = merged_df['price24hPcnt'].astype(float) * 100
        if market_type == "COIN_M":
            merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'volume24h':'atp24h'})
        else:
            merged_df = merged_df.rename(columns={"lastPrice":'tp', 'a':'ap', 'b':'bp', 'price24hPcnt':'scr', 'turnover24h':'atp24h'})
        merged_df[['tp','ap','bp','scr','atp24h']] = merged_df[['tp','ap','bp','scr','atp24h']].astype(float)
        merged_df = merged_df[['symbol','base_asset','quote_asset','tp','bp','ap','scr','atp24h']]
        return merged_df

def get_okx_price_df(redis_client, market_type):
    """Legacy compatibility function"""
    if isinstance(redis_client, OptimizedRedisHelper):
        manager = get_price_data_manager(redis_client)
        return manager.get_okx_price_df_optimized(market_type)
    else:
        # Original implementation
        try:
            ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", f"OKX_{market_type}")).T
            ticker_df['base_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[0])
            ticker_df['quote_asset'] = ticker_df['instId'].apply(lambda x: x.split('-')[1])
            ticker_df = ticker_df.rename(columns={"last": "tp", "askPx": "ap", "bidPx":"bp", "volCcy24h":"atp24h"})
            ticker_df[['tp', 'ap', 'bp', 'open24h', 'atp24h']] = ticker_df[['tp', 'ap', 'bp', 'open24h', 'atp24h']].astype(float)
            ticker_df['atp24h'] = ticker_df.apply(lambda x: x['tp']*x['atp24h'] if x['instType'] != "SPOT" else x['atp24h'], axis=1)
            ticker_df['scr'] = (ticker_df['tp'] - ticker_df['open24h']) / ticker_df['open24h'] * 100
            ticker_df = ticker_df[['instId', 'base_asset', 'quote_asset', 'tp', 'ap', 'bp', 'scr', 'atp24h']]
            return ticker_df
        except Exception as e:
            content = f"get_price_df|{traceback.format_exc()}"
            raise e

def get_upbit_price_df(redis_client):
    """Legacy compatibility function"""
    if isinstance(redis_client, OptimizedRedisHelper):
        manager = get_price_data_manager(redis_client)
        return manager.get_upbit_price_df_optimized()
    else:
        # Original implementation
        upbit_ticker_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("ticker", "UPBIT_SPOT")).T.reset_index()[['index','tp','scr','atp24h','h52wp','l52wp','ms','mw','tms']]
        upbit_orderbook_df = pd.DataFrame(redis_client.get_all_exchange_stream_data("orderbook", "UPBIT_SPOT")).T.reset_index(drop=True)[['cd','tms','obu']]
        upbit_orderbook_df['ap'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['ap'])
        upbit_orderbook_df['bp'] = upbit_orderbook_df['obu'].apply(lambda x: x[0]['bp'])
        upbit_orderbook_df.drop('obu', axis=1, inplace=True)
        upbit_merged_df = pd.merge(upbit_ticker_df, upbit_orderbook_df, left_on='index', right_on='cd', how='inner')
        upbit_merged_df = upbit_merged_df.dropna(subset=['tp', 'ap', 'bp'])
        upbit_merged_df['base_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[1])
        upbit_merged_df['quote_asset'] = upbit_merged_df['index'].apply(lambda x: x.split('-')[0])
        upbit_merged_df.drop('index', axis=1, inplace=True)
        upbit_merged_df[['scr','atp24h','h52wp','l52wp','ap','bp']] = upbit_merged_df[['scr','atp24h','h52wp','l52wp','ap','bp']].astype(float)
        upbit_merged_df['scr'] = upbit_merged_df['scr'] * 100
        return upbit_merged_df

# Updated handler mapping
EXCHANGE_HANDLERS = {
    "BINANCE": get_binance_price_df,
    "BITHUMB": get_bithumb_price_df,
    "BYBIT": get_bybit_price_df,
    "OKX": get_okx_price_df,
    "UPBIT": get_upbit_price_df
}

def get_price_df(redis_client, market_code):
    """Main entry point - automatically uses optimized path if OptimizedRedisHelper is provided"""
    exchange = market_code.split('_')[0]
    # all the part excluding exchange
    market_type = '_'.join(market_code.split('_')[1:])
    exchange = exchange.upper()
    market_type = market_type.upper()

    handler = EXCHANGE_HANDLERS.get(exchange)
    if handler:
        if exchange in ["BINANCE", "BYBIT", "OKX"]:
            return handler(redis_client, market_type)
        else:
            return handler(redis_client)
    else:
        raise ValueError(f"get_price_df|exchange: {exchange} is not supported!")