# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

info_core is a real-time cryptocurrency exchange data aggregation and analysis system that connects to multiple exchanges (Binance, OKX, Upbit, Bithumb, Bybit) via websockets and REST APIs. It processes market data for spot, USD-M futures, and COIN-M futures markets, identifying arbitrage opportunities and generating AI-driven insights.

## Development Commands

### Running the Application
```bash
# Direct Python execution
python info_core_main.py

# Using shell scripts
./restart.sh  # Stops existing process and restarts
./stop.sh     # Stops the running process

# Docker commands
docker build . --target base -t base-info-core:base
docker build . --target dev -t info-core:dev
docker build . --target test -t info-core:test
docker build . --target prod -t info-core:prod
```

### Environment Setup
1. Copy `.env.example` to `.env` and configure required variables
2. Install dependencies: `pip install -r requirements.txt`
3. Ensure Redis and MongoDB are accessible with configured credentials

## Architecture Overview

### Core Components

1. **InitCore** (`info_core/info_core.py`): Main orchestrator that manages all subsystems
   - Initializes exchange connections based on configuration
   - Manages process lifecycle for data generators
   - Coordinates Redis storage and MongoDB persistence

2. **Exchange Integration**:
   - **Plugins** (`exchange_plugin/`): REST API interfaces for each exchange
   - **Websockets** (`exchange_websocket/`): Real-time data streaming
   - Each exchange has both spot and futures market support

3. **Data Processing Pipelines**:
   - **KlineCore** (`kline_generator/kline_core.py`): Generates candlestick data from raw trades
   - **ArbitrageCore** (`arbitrage_generator/arbitrage_core.py`): Identifies cross-exchange arbitrage opportunities
   - **AidataCore** (`aidata_generator/aidata_core.py`): AI-powered market analysis using Google Gemini

4. **Standalone Functions** (`standalone_func/`):
   - Independent processes that can be run separately
   - Handle specific data updates (price dataframes, funding rates, wallet data)
   - Designed for distributed deployment across multiple nodes

### Data Flow

1. Exchange websockets → Redis (real-time cache)
2. Redis → Data processors (kline, arbitrage, AI analysis)
3. Processed data → MongoDB (persistent storage)
4. Alerts/Monitoring → Telegram bot

### Key Design Patterns

- **Multi-process Architecture**: Each data generator runs in its own process
- **Redis as Message Bus**: All real-time data passes through Redis
- **Master/Slave Nodes**: Supports distributed deployment with node designation
- **Symbol Whitelisting**: Configurable symbol filtering per exchange
- **Graceful Shutdown**: Proper cleanup of websocket connections and processes

## Important Implementation Details

- Exchange websockets use different message formats - see `dict_convert.py` for standardization
- Funding rate calculations differ between exchanges (8h vs 24h intervals)
- Korean exchanges (Upbit, Bithumb) require special handling for KRW pairs
- The system tracks connection health and automatically reconnects failed websockets
- All timestamps are stored in milliseconds (Unix timestamp * 1000)

## Common Development Tasks

When adding new exchange support:
1. Create plugin in `exchange_plugin/` following existing patterns
2. Create websocket handler in `exchange_websocket/`
3. Update `InitCore` to recognize new exchange
4. Add exchange-specific configuration in `.env`

When modifying data processing:
1. Standalone functions should be independent and idempotent
2. Always handle Redis connection failures gracefully
3. Use the centralized logger from `loggers/logger.py`
4. Ensure proper cleanup in signal handlers