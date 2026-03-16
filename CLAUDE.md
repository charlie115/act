# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

ACW is a cryptocurrency arbitrage platform organized as a service-based monorepo. It consolidates previously separate repos while keeping runtime services as separate deployable units.

### Key Services

| Service | Location | Stack | Port |
|---------|----------|-------|------|
| **Frontend** (Next.js) | `apps/community_web_next/` | Next.js 16, React 19, Tailwind 4, MUI 5 | 3000 |
| **Backend API** (Django) | `apps/community_drf/` | Django 4.2, DRF, Channels, Celery | 8000 |
| **Market Data Engine** | `services/info_core/` | Python 3.11, Redis, MongoDB, WebSockets | — |
| **Trading Engine** | `services/trade_core/` | Python 3.10, FastAPI, Redis, MongoDB | — |
| **HD Wallet** | `services/hdwallet/` | Python 3.11, FastAPI, Tron (USDT deposit) | 8000 (internal) |
| **News Scraper** | `services/news_core/` | Scrapy, PostgreSQL | — |
| **Shared Python Lib** | `packages/python/acw_common/` | Shared clients, market data utils, websocket helpers, DB clients | — |

`apps/community_web` is the legacy CRA frontend (reference only) — `apps/community_web_next` is the official one.

## Build & Development Commands

All commands run from the repo root via `make` (which delegates to `scripts/workflow/acw.sh`).

```bash
make help                    # Show all available commands
make doctor                  # Verify local setup
make env-init                # Create missing .env files (FORCE=1 to overwrite)

# Development (backend in Docker, frontend local with hot-reload)
make dev-up STACK=all        # Start all backend/data services
make dev-up STACK=community  # Community stack only
make dev-up STACK=trade      # Trade stack only
make web-dev                 # Local Next.js dev server (port 3000)
make dev-down STACK=all      # Stop all dev services

# Production
make prod-up STACK=all       # Build and deploy both stacks
make prod-down STACK=all

# Build
make build-images STACK=all ENV=testing
make build-web ENV=production

# Docker Compose inspection
make stack STACK=community ENV=testing ACTION=ps
make stack STACK=community ENV=testing ACTION=logs ARGS="drf -f"
```

### Frontend (community_web_next)

```bash
cd apps/community_web_next
pnpm install                 # Install deps (project uses pnpm)
pnpm dev                     # Next.js dev server with turbopack
pnpm build                   # Production build
pnpm lint                    # ESLint (flat config, core-web-vitals)
```

### Backend (community_drf)

```bash
cd apps/community_drf
python manage.py runserver       # Dev server (uses config.settings.dev)
python manage.py test <app>      # Run tests for a specific Django app
python manage.py makemigrations  # Generate migrations
python manage.py migrate         # Apply migrations
```

Django settings split: `config/settings/{base,dev,test,prod}.py`. The `.env` file lives in `apps/community_drf/`.

Python linting: Flake8 with max-line-length 119, excludes migrations.

## Architecture

### Data Flow

```
community_web_next (Next.js)
    │ HTTP / WebSocket
    ▼
community_drf (Django REST + Channels)
    │
    ├── PostgreSQL 16 (users, trades, news)
    ├── Redis 7 (cache, pub/sub, real-time)
    ├── MongoDB 6 (time-series market data)
    ├── Celery (async tasks via celery-worker + celery-beat)
    │
    ├── info_core → exchange WebSockets, kline generation, arbitrage detection
    ├── trade_core → order execution, trading logic (engine + FastAPI API)
    ├── hdwallet → Tron USDT deposit/withdrawal management
    └── news_core → Scrapy spiders for news/announcements
```

### info_core Master/Worker Model

- `MASTER=true`: Runs market data ingestion + kline generation + arbitrage analysis + AI recommendations
- `MASTER=false` (worker/kline_core): Runs market data ingestion + kline generation only (on separate servers)
- `DEV_MAX_SYMBOLS=10`: Limits symbols to top N by volume in dev (reduces CPU/memory load)

### Shared Library (acw_common)

`packages/python/acw_common/acw_common/` contains code shared between info_core and trade_core:

| Module | Contents |
|--------|----------|
| `db/mongodb_client.py` | MongoDB client with connection pooling (singleton, fork-safe) |
| `marketdata/price_df.py` | Exchange price DataFrame construction with signature-based caching |
| `marketdata/premium.py` | Arbitrage premium calculation |
| `marketdata/dollar.py` | USD/KRW exchange rate fetching with staleness detection |
| `marketdata/exchange_status.py` | Exchange server maintenance status (with in-memory cache) |
| `websocket/dict_convert.py` | Ticker/orderbook data conversion utilities |
| `websocket/heartbeat.py` | Process heartbeat monitoring |
| `websocket/monitoring.py` | Process staleness evaluation |
| `websocket/process_group.py` | Process group lifecycle management |
| `clients/acw_api.py` | REST client for community_drf API (messaging, node config) |

Services import from acw_common via `_acw_common.py` path helper, NOT pip install.

### Telegram Messaging

All services send messages through Django's messagecore pipeline:
```
info_core/trade_core → AcwApi.create_message_thread() → Django /messagecore/messages/ API
→ PM2 telegram_send_message → Telegram Bot API
```

Bot tokens are managed in Django admin (ProxySocialApp model). Users are auto-assigned to the least-loaded bot at registration.

### Frontend API Proxy

`next.config.mjs` proxies backend routes via `ACW_API_PROXY_TARGET`. Backend prefixes: auth, board, chat, coupon, exchange-status, fee, infocore, messagecore, newscore, referral, tradecore, users, wallet.

### Docker Compose Layout

Compose files live in `infra/compose/{community,trade}/`:
- `compose.base.yml` — service definitions
- `compose.dev.yml` — dev overrides (exposed ports, volumes, no nginx)
- `compose.testing.yml` / `compose.production.yml` — environment overlays

Each service Dockerfile uses multi-stage builds with targets: `base`, `dev`, `test`, `prod`.

### Django App Structure

Django apps live in `apps/community_drf/apps/` — authentication, users, api, board, chat, coupon, exchangestatus, fee, infocore, messagecore, newscore, referral, tradecore, wallet.

### Django Middleware

GZip compression is enabled globally. Rate limiting: anon 60/min, authenticated 300/min.

### info_core Modules

`exchange_plugin/` (REST adaptors), `exchange_websocket/` (WebSocket clients), `kline_generator/`, `arbitrage_generator/`, `aidata_generator/`, `market_ingest/`. Supports Binance, OKX, Upbit, Bithumb, Bybit, Gate.io, Coinone, Hyperliquid.

## Key Conventions

- `acw_common` package is added to `PYTHONPATH` in Docker images (not pip-installed)
- Next.js output mode is `"standalone"`
- Django `manage.py` defaults to `config.settings.dev`
- Environment names: `dev`, `testing`, `production` (the workflow script normalizes these)
- `STACK` variable accepts: `community`, `trade`, `all`
- MongoDB: Never call `close()` on connections from `InitDBClient.get_conn()` — the pool manages lifecycle
- Frontend kline cache uses SWR pattern with long TTLs (WebSocket handles live updates)
- Font: Space Grotesk (sans), JetBrains Mono (mono); premium table uses tabular-nums without font-mono
