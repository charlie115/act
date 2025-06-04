# Websocket Data Handling Analysis

## Overview
The system uses websocket connections to receive real-time market data from 5 exchanges:
- Binance (SPOT, USD_M, COIN_M markets)
- OKX (SPOT, USD_M, COIN_M markets)
- Bybit (SPOT, USD_M, COIN_M markets)
- Upbit (SPOT only)
- Bithumb (SPOT only)

## Architecture Pattern
All exchanges follow a similar multi-process architecture:
1. **Main websocket class** manages multiple processes
2. **Separate processes** for different data streams (ticker, orderbook)
3. **Symbol list slicing** - distributes symbols across multiple processes
4. **Redis storage** - all data stored as JSON in Redis hashes
5. **Monitoring threads** - watch for stale data and restart dead processes

## Identified Bottlenecks and Inefficiencies

### 1. Frequent JSON Serialization/Deserialization
**Issue**: Every message involves multiple JSON operations:
```python
# In websocket on_message:
message_dict = json.loads(message)  # Parse incoming JSON
# In Redis helper:
stream_data_json = json.dumps(stream_data)  # Serialize for Redis
# When reading:
json.loads(ticker_data)  # Deserialize from Redis
```

**Impact**: High CPU usage, especially with high message volumes
**Optimization**: Consider using msgpack or pickle for internal storage, keep raw JSON for external APIs

### 2. Redundant Data Copying
**Issue**: Multiple dictionary copies and merges:
```python
# In Binance websocket:
{**msg, "last_update_timestamp": int(time.time() * 1_000_000)}
# In dict_convert.py:
OKX_TICKER_DICT_copy = dict(OKX_TICKER_DICT.copy())
```

**Impact**: Memory overhead and CPU cycles
**Optimization**: Modify dictionaries in-place where possible

### 3. Inefficient Timestamp Calculation
**Issue**: Repeated timestamp calculations:
```python
int(time.time() * 1_000_000)  # Microseconds calculated on every message
```

**Impact**: Unnecessary computation
**Optimization**: Calculate once per batch or use monotonic clock

### 4. Busy Waiting in Monitoring Loops
**Issue**: Multiple threads checking conditions every second:
```python
while True:
    time.sleep(1)  # Check every 1 second
```

**Impact**: Thread overhead
**Optimization**: Use event-driven approach or longer intervals

### 5. Inefficient DataFrame Operations in dict_convert.py
**Issue**: Creating DataFrames for simple dictionary operations:
```python
converted_df = pd.DataFrame(OKX_TICKER_DICT_copy).transpose().reset_index(drop=True)
```

**Impact**: Heavy pandas overhead for simple data transformation
**Optimization**: Use dictionary comprehensions or numpy arrays

### 6. Redis Operation Inefficiencies
**Issue**: Individual Redis operations per message:
```python
redis_conn.hset(redis_key, symbol, stream_data_json)
```

**Impact**: Network latency, Redis CPU usage
**Optimization**: Batch updates using pipeline or hmset

### 7. Process Management Overhead
**Issue**: Creating separate processes for each symbol slice:
- Binance: `proc_n * 2` processes
- Other exchanges: `proc_n` processes each

**Impact**: High process overhead, inter-process communication costs
**Optimization**: Use fewer processes with async I/O or thread pools

### 8. Redundant Symbol List Operations
**Issue**: Repeated sorting and list operations:
```python
if sorted(self.before_symbols_list) != sorted(new_symbols_list):
```

**Impact**: O(n log n) operation every 60 seconds
**Optimization**: Use sets for faster comparison

### 9. Stale Data Checking Inefficiency
**Issue**: Fetching all data from Redis to check timestamps:
```python
data = self.local_redis.get_all_exchange_stream_data(redis_stream_type, f"BYBIT_{self.market_type.upper()}")
```

**Impact**: Large data transfer every 60 seconds
**Optimization**: Use Redis TTL or separate timestamp tracking

### 10. Message Validation Overhead
**Issue**: Multiple key existence checks per message:
```python
if 'data' in message_dict.keys():
    if 'content' in message_dict.keys():
```

**Impact**: Repeated dictionary lookups
**Optimization**: Use try/except or get() with defaults

## Recommendations

### High Priority Optimizations
1. **Batch Redis updates** - Use pipelines to reduce network overhead
2. **Replace JSON with msgpack** for internal storage (3-5x faster)
3. **Implement connection pooling** for Redis clients
4. **Use asyncio** instead of multiprocessing where possible
5. **Cache timestamp calculations** per batch

### Medium Priority Optimizations
1. **Optimize dict_convert.py** - Remove pandas dependency
2. **Implement circular buffers** for liquidation data
3. **Use Redis Streams** instead of hashes for time-series data
4. **Reduce monitoring frequency** from 1s to 5-10s

### Low Priority Optimizations
1. **Profile and optimize hot paths** with cProfile
2. **Consider using uvloop** for async operations
3. **Implement message deduplication** at websocket level
4. **Add metrics collection** for performance monitoring

### Architecture Improvements
1. **Single process per exchange** with async websocket handling
2. **Shared memory** for frequently accessed data
3. **Event-driven monitoring** instead of polling
4. **Connection multiplexing** where supported by exchanges