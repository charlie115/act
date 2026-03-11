# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a cryptocurrency arbitrage trading platform that monitors price differences across multiple exchanges (Binance, Upbit, Bithumb, OKX, Bybit) and executes automated trades. The system supports both spot and futures markets with real-time websocket data feeds.

## Core Architecture

### Main Components
- **`trade_core.py`**: Central `InitCore` class that orchestrates the entire system
- **`trade_core_main.py`**: Main entry point with CLI argument parsing
- **`api/main.py`**: FastAPI REST API server for external access
- **`exchange_plugin/`**: Exchange-specific adapters for order execution
- **`exchange_websocket/`**: Real-time websocket connections for market data
- **`trigger/`**: Trading logic and arbitrage opportunity detection

### System Flow
1. Real-time market data flows through websocket connections
2. `InitCore` processes data and detects arbitrage opportunities
3. `InitTrigger` evaluates trading conditions and risk parameters
4. Exchange plugins execute trades across multiple markets
5. All activities are logged to PostgreSQL and monitored via Telegram

## Development Commands

### Running the System

**Main Trading Engine:**
```bash
python trade_core/trade_core_main.py [options]
```

**CLI Options:**
- `-p, --proc_n`: Number of processes for websocket handling
- `-l, --log`: Log directory (default: `trade_core/loggers/logs/`)
- `-c, --config`: Config file path (default: `.env`)

**FastAPI Server:**
```bash
# From trade_core/api/ directory
uvicorn main:app --reload
```

### Docker Commands

**Build Commands:**
```bash
# Main trading engine - test environment
docker build . --target test -t trade-core:test

# API server - test environment  
docker build . --target api_test -t trade-core-api:test

# Development builds
docker build . --target dev -t trade-core:dev
docker build . --target api_dev -t trade-core-api:dev

# Production builds
docker build . --target prod -t trade-core:prod  
docker build . --target api_prod -t trade-core-api:prod
```

**Run Commands:**
```bash
# Run trading engine
docker run -d --name trade-core trade-core:test

# Run API server
docker run -d -p 8000:8000 --name trade-core-api trade-core-api:test
```

### Dependencies

**Install Requirements:**
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- FastAPI + SQLAlchemy for API and database
- Redis for caching and real-time data
- PostgreSQL for persistent storage
- Exchange-specific clients (python-binance, pybit, python-okx, upbit-client)
- WebSocket clients for real-time data

## Configuration

### Environment Variables
The system uses environment-specific `.env` files:
- `.env.dev` - Development environment
- `.env.test` - Testing environment  
- `.env.prod` - Production environment

**Required Variables:**
- `NODE`: Node identifier for multi-node deployments
- `PROC_N`: Number of websocket processes
- `POSTGRES_HOST/PORT`: PostgreSQL connection
- `REDIS_HOST/PORT`: Redis connection
- `MONGODB_HOST/PORT`: MongoDB connection
- Exchange API credentials for each supported exchange
- `ADMIN_TELEGRAM_ID`: Telegram bot notifications

### Node-Based Configuration
The system supports multi-node deployments where each node can handle different market combinations. Configuration is loaded based on the `NODE` environment variable.

## Database Schema

### PostgreSQL Tables (via SQLAlchemy)
- **trade_configs**: Trading configuration per user/market
- **orders**: Order execution history
- **positions**: Current position tracking
- **pnl_history**: Profit/loss tracking

### Data Flow
- **Redis**: Real-time price data, websocket state, temporary calculations
- **PostgreSQL**: Persistent trading data, configurations, audit logs
- **MongoDB**: Additional data storage for analytics

## API Endpoints

The FastAPI server provides REST endpoints for:
- CRUD operations on trading configurations
- Position and balance queries
- Order history and PnL tracking
- Real-time market data access

## Testing

Currently no automated test suite is configured. Testing is done through:
- Docker test builds with test environment
- Manual API testing via `test_api.ipynb` notebook
- Live trading with small position sizes

## Logging

Comprehensive logging system with separate loggers for:
- `trade_core`: Main application logs
- `price_websocket`: WebSocket connection logs  
- `update_dollar`: Currency conversion logs

Logs are stored in `trade_core/loggers/logs/` directory.

## Key Development Patterns

### Exchange Integration
Each exchange follows the adapter pattern with consistent interfaces for:
- Order placement and cancellation
- Balance and position queries
- Market data access
- WebSocket connection management

### Error Handling
The system implements robust error handling for:
- Network connectivity issues
- Exchange API rate limits
- WebSocket reconnection
- Database connection failures

### Risk Management
Built-in risk controls include:
- Position size limits per market
- Negative balance monitoring
- Trading window restrictions
- Configurable risk thresholds

## Monitoring

### Telegram Integration
Real-time notifications for:
- System startup/shutdown
- Trading opportunities and executions
- Error conditions and alerts
- Performance metrics

### Health Checks
The system monitors:
- Exchange connection status
- WebSocket data freshness
- Database connectivity
- Redis cache performance