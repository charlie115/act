# Core Runtime Boundaries

## Why `info_core` and `trade_core` Must Stay Separate At Runtime

`info_core` and `trade_core` have duplicated code, but they do **not** have the same runtime responsibility.

They should share internal libraries where practical, but they should not be merged into one running service.

## `info_core` Role

`info_core` is a distributed market-data and derived-data engine.

Its responsibilities include:

- exchange websocket ingestion
- exchange metadata refresh
- convert-rate generation
- kline generation
- volatility/arbitrage/AI-related derived data
- publishing activated market combinations to Redis

Code evidence:

- node-scoped enabled markets come from env: `info_core/.env.example`
- node runtime bootstrap: `info_core/info_core/info_core.py`
- master-only workloads: `wallet_funding_update`, `arbitrage_generator`, `ai_data_generator`
- per-market kline worker processes: `info_core/info_core/kline_generator/kline_core.py`

## `trade_core` Role

`trade_core` is a distributed execution engine.

Its responsibilities include:

- its own exchange websocket ingestion
- its own local market snapshot generation
- trigger evaluation with high-frequency loops
- real trade execution using user API keys
- storing trade state in its own Postgres
- exposing trade APIs through a separate FastAPI runtime

Code evidence:

- node-scoped enabled market combinations are fetched from ACW node config: `trade_core/trade_core/trade_core.py`
- user-to-node allocation is managed in `community_drf`: `community_drf/apps/tradecore/serializers.py`
- trigger processes are started per market combination: `trade_core/trade_core/trigger/trigger.py`
- trade API and engine are separate runtimes inside one service area

## Architectural Constraint

`trade_core` does not rely on `info_core` to stream execution-critical data into it.

That is intentional and should be preserved.

Reason:

- execution paths are latency-sensitive
- cross-service forwarding adds delay and a new failure point
- trade nodes must continue to operate from local market state
- trade nodes are intentionally distributed across multiple servers for compute spread and exchange/IP rate-limit avoidance

This means:

- do not redesign `trade_core` to consume execution-critical ticks from `info_core`
- do not move trigger evaluation into `community_drf`
- do not centralize all exchange websocket ingestion into one service if trade latency would increase

## Shared State That Can Remain Loose

Loose coupling is acceptable for:

- node metadata and routing via `community_drf`
- exchange server health via ACW APIs and Redis
- activated market visibility via Redis
- monitoring and operational commands

But not for execution-critical tick-to-trade control flow.

## Correct Refactoring Direction

### Share Code

Good shared-package candidates:

- exchange adaptor interfaces
- websocket utility layers
- Redis helper
- Mongo/Postgres bootstrap
- ACW API client
- common premium/price dataframe builders
- logging and config loaders

### Keep Runtime Isolation

Keep these runtime separations:

- `info_core` data generation plane
- `trade_core` execution plane
- `trade_core_api` control/query plane

## Operational Principle

The target architecture is:

- one monorepo
- shared internal libraries
- separate deployable runtimes
- node-aware horizontal scaling preserved

That preserves the original operational reason for the split while removing repository sprawl.
