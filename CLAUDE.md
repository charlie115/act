# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

info_core is a market data aggregation service for a cryptocurrency arbitrage platform. It collects real-time price data from multiple exchanges via WebSocket connections, generates candlestick (kline) data, calculates arbitrage opportunities, and provides AI-powered market analysis.

## Commands

```bash
# Run directly (from /opt/info_core/info_core/)
python info_core_main.py

# Run with custom config
python info_core_main.py --config /path/to/.env --proc_n 4 --log /path/to/logs/

# Restart service
./restart.sh

# Stop service
./stop.sh

# Docker builds
docker build . --target base -t base-info-core:base
docker build . --target dev -t dev-info-core:dev
docker build . --target test -t info-core:test
docker build . --target prod -t info-core
```

## Architecture

### Entry Point
- `info_core_main.py` - Loads environment config, initializes `InitCore`, starts `CommandHandler` loop

### Core Module (`info_core.py`)
The `InitCore` class orchestrates:
- Exchange adaptor initialization (read-only API connections)
- WebSocket connections for real-time price feeds
- Background threads for data updates (dollar rate, USDT price, exchange info)
- Sub-cores: `InitKlineCore`, `InitAbitrageCore`, `InitAiDataCore`

### Exchange Integration

**exchange_plugin/** - REST API adaptors per exchange:
- `binance_plug.py` - Spot, USD-M futures, COIN-M futures
- `okx_plug.py` - Spot and futures
- `upbit_plug.py` - Korean exchange (KRW pairs)
- `bithumb_plug.py` - Korean exchange
- `bybit_plug.py` - Spot and futures

**exchange_websocket/** - Real-time WebSocket clients:
- Each exchange has classes for spot and futures (e.g., `BinanceWebsocket`, `BinanceUSDMWebsocket`, `BinanceCOINMWebsocket`)
- `dict_convert.py` - Normalizes different exchange data formats

### Data Generators

**kline_generator/** - Candlestick data:
- Generates 1T, 5T, 15T, 30T, 1H, 4H intervals
- Stores in MongoDB via Redis pub/sub
- Calculates volatility metrics

**arbitrage_generator/** - Arbitrage opportunities:
- Monitors funding rate differences between exchanges
- Calculates average funding rates
- Cleans up delisted pairs

**aidata_generator/** - AI analysis:
- Uses Google GenAI API (`AIENGINE_API_KEY`)
- Generates trading recommendations

### Utilities

**etc/** - Shared infrastructure:
- `redis_connector/redis_helper.py` - Thread-safe Redis client wrapper
- `db_handler/mongodb_client.py` - MongoDB client with connection pooling (singleton pattern)
- `acw_api.py` - API client for community_drf backend
- `command_handler.py` - Remote command processing

### MongoDB Optimizations

The MongoDB client (`etc/db_handler/mongodb_client.py`) implements several performance optimizations:

1. **Connection Pooling**: Uses singleton pattern to reuse `MongoClient` instances per URI. Never call `close()` on connections - they are managed by the pool.

2. **Automatic Indexing**: `ensure_indexes()` method creates `datetime_now` descending index on collections for fast sorted queries.

3. **Efficient Methods**:
   - `is_collection_empty()` - Uses `estimated_document_count()` (O(1)) instead of `count_documents({})` (full scan)
   - `get_last_datetime()` - Uses index hint for O(1) lookup of last document

4. **Redis Timestamp Caching**: `insert_kline_to_db()` caches last inserted timestamps in local Redis to avoid repeated MongoDB queries.

**Important**: Do NOT call `mongo_db_conn.close()` in any function - the connection pool manages connection lifecycle.

**standalone_func/** - Background data processors:
- `kline_data_generator.py` - OHLC generation
- `arbitrage_data_updater.py` - Funding rate storage
- `aidata_updater.py` - AI recommendation updates
- `wallet_funding_updater.py` - Wallet balance tracking
- `get_dollar_dict.py` - USD/KRW exchange rate
- `store_exchange_status.py` - Exchange server status

**loggers/** - Logging infrastructure with rotating file logs

## Data Flow

1. WebSocket clients receive real-time ticker data from exchanges
2. Data normalized and stored in local Redis as DataFrames (pickle serialized)
3. Kline generator subscribes to Redis, aggregates into candlesticks, stores in MongoDB
4. Arbitrage generator calculates cross-exchange opportunities
5. Results accessible via community_drf API

## Configuration

See `.env.example` for required variables:
- `MASTER` - Boolean, master node runs arbitrage calculations
- `PROC_N` - Number of WebSocket handler processes
- `ENABLED_MARKET_KLINES` - Comma-separated market pairs for kline generation (e.g., `UPBIT_SPOT/KRW:BINANCE_USD_M/USDT`)
- `ENALBED_ARBITRAGE_MARKETS` - Market pairs for arbitrage tracking
- Exchange API keys (read-only): Binance, OKX, Upbit, Bithumb, Bybit
- Database connections: MongoDB, Redis

## Key Data Structures

Market code format: `{EXCHANGE}_{TYPE}/{QUOTE}` (e.g., `UPBIT_SPOT/KRW`, `BINANCE_USD_M/USDT`)

Redis keys for exchange data:
- `{exchange}_{type}_ticker_df` - Real-time ticker data
- `{exchange}_{type}_info_df` - Exchange symbol metadata
