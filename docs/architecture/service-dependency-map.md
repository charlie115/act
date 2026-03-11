# ACW Service Dependency Map

## Current Topology

```text
community_web
  -> community_drf (HTTP, WebSocket)

community_drf
  -> community_db (PostgreSQL, default)
  -> newscore_db (PostgreSQL, read-heavy via db router)
  -> messagecore_db (PostgreSQL)
  -> Redis
  -> MongoDB
  -> trade_core_api (HTTP)
  -> hdwallet_service (HTTP)
  -> info_core data (indirect via Redis + MongoDB)
  -> news_core data (indirect via newscore_db)

news_core
  -> newscore_db (PostgreSQL)
  -> external media sites

info_core
  -> Redis
  -> MongoDB
  -> community_drf APIs via ACW_API_URL (message, referral, deposit, status, market codes)
  -> external exchange REST/WebSocket APIs

trade_core_engine
  -> trade_db (PostgreSQL)
  -> Redis
  -> MongoDB
  -> community_drf APIs via ACW_API_URL
  -> external exchange REST/WebSocket APIs

trade_core_api
  -> trade_db (PostgreSQL)
  -> trade_core Redis
  -> MongoDB
  -> community_drf APIs via ACW_API_URL
  -> external exchanges through trading adaptors

arbitrage_community
  -> deploys: community_web build, community_drf, celery, news_core, info_core, wallet infra

arbitrage_trade
  -> deploys: trade_core_engine, trade_core_api, trade postgres, nginx
```

## Repository-Level View

This directory is not a single repo yet. It is a multi-repo workspace:

- `community_web`: frontend SPA
- `community_drf`: BFF, auth, community domain, websocket hub, integration hub
- `news_core`: scraping worker
- `info_core`: market data engine
- `trade_core`: trading engine + FastAPI server
- `arbitrage_community`: community deployment compose repo
- `arbitrage_trade`: trade deployment compose repo

## Main Coupling Axes

### 1. HTTP Coupling

- `community_web` only talks to `community_drf`
- `community_drf` talks to `trade_core_api` and `hdwallet_service`
- `info_core` and `trade_core` both talk back to `community_drf` via `ACW_API_URL`

### 2. Shared Data Stores

- `community_drf` reads live/derived data from Redis and MongoDB that `info_core` produces
- `community_drf` reads `news_core` output from `newscore_db`
- `trade_core_api` and `trade_core_engine` share their own Postgres and Redis

### 3. Deployment Coupling

- Runtime composition currently lives outside the service repos
- Image build responsibility and runtime wiring are split across different repos
- Environment-specific compose files duplicate a large amount of config

## What This Means For Refactoring

The real system boundary is not per repository. The real boundary is per runtime/service:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core_engine`
- `trade_core_api`
- `hdwallet_service` (external to this workspace)

Those should remain separate deployable units even after monorepo migration.

## Immediate Structural Problems

- Repository boundaries do not match change boundaries
- Deployment config is separated from service source, so one feature change often spans multiple repos
- `community_drf` is both a business backend and an integration gateway
- `info_core` and `trade_core` duplicate runtime/bootstrap/integration code
- Some dependencies are API-based, some are datastore-based, and some are compose-only, which makes the system hard to reason about globally
