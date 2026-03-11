# Info Core Kline Pipeline Redesign

## Goal

Redesign `info_core` kline generation so that:

- `1T`, `5T`, `15T`, `30T`, `1H`, `4H` all remain correct
- the current open candle for `5T+` remains live and accurate
- closed-candle generation becomes event-driven
- Redis and Mongo write amplification is reduced
- the design remains horizontally partitionable by enabled market combinations

This document assumes the current monorepo structure and runtime boundaries remain in place.

## Non-Negotiable Behavior

The redesign must preserve both of these:

1. Closed candles must be exact.
2. The current open candle for `5T+` must reflect live premium movement before the interval closes.

That means a pure `finalized 1T only` pipeline is not sufficient.

## Current Problems

### 1. `1T` rebuilds full premium snapshots too often

Current `1T` workers rebuild full `premium_df` snapshots in a tight loop:

- [kline_data_generator.py#L389](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L389)
- [premium.py#L30](/Users/charlie/Projects/acw/packages/python/acw_common/acw_common/marketdata/premium.py#L30)
- [price_df.py#L345](/Users/charlie/Projects/acw/packages/python/acw_common/acw_common/marketdata/price_df.py#L345)

The current `price_df` path reads full Redis hashes and rebuilds DataFrames repeatedly:

- [redis_helper.py#L134](/Users/charlie/Projects/acw/services/info_core/info_core/etc/redis_connector/redis_helper.py#L134)

### 2. `5T+` workers poll instead of consuming events

Each market combination starts 6 processes:

- [kline_core.py#L60](/Users/charlie/Projects/acw/services/info_core/info_core/kline_generator/kline_core.py#L60)

`5T+` workers loop and repeatedly read `1T_now`:

- [kline_data_generator.py#L785](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L785)

This causes repeated unpickle, reshape, repickle, and stream publish even when no meaningful state change occurred.

### 3. Redis history is rewritten as whole DataFrames

Minute close and interval close both do full read-concat-tail-write cycles:

- [kline_data_generator.py#L538](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L538)
- [kline_data_generator.py#L683](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L683)

### 4. Server-check lookups scan Redis keys

The Mongo flush path scans all Redis keys and filters them in Python:

- [kline_data_generator.py#L213](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L213)

### 5. Volatility is computed by periodic full rescan

The volatility loop sweeps all market combinations and all `_1T` collections:

- [kline_data_generator.py#L23](/Users/charlie/Projects/acw/services/info_core/info_core/standalone_func/kline_data_generator.py#L23)

## Target Architecture

Split the kline pipeline into two event types and four runtime roles.

### Event Types

#### 1. Live Snapshot Event

Represents the current open candle state for the active minute.

Used for:

- `1T_now`
- `5T+ now`
- UI/API reads of current open candles

#### 2. Closed Candle Event

Represents a finalized candle that will never change again.

Used for:

- `1T_closed`
- `5T+` finalize
- Mongo persistence
- volatility updates

### Runtime Roles

#### 1. Premium Snapshot Runtime

Produces a bounded-lifetime premium snapshot per market combination.

Responsibilities:

- consume local market state already maintained by `market_ingest`
- compute `premium_df` once per market combination per cycle
- publish a local snapshot and optional local stream event

Suggested local key:

- `premium|{market_code_combination}`

Suggested payload:

- pickled DataFrame or a compact tabular format
- short TTL, for example `1-3s`

#### 2. `1T` Live Aggregator

Consumes premium snapshots and maintains the current minute candle state in memory.

Responsibilities:

- update `open/high/low/close` for the current minute
- maintain `1T_now`
- publish lightweight `1T_now` updates only when data changed
- finalize the minute at boundary and emit `1T_closed`

This replaces the current pattern of recalculating everything from Redis on each loop.

#### 3. Higher-Interval Aggregator

Consumes both:

- `1T_now` live updates
- `1T_closed` finalized updates

Responsibilities:

- keep `5T/15T/30T/1H/4H now` accurate while the interval is open
- finalize interval candles only from `1T_closed`

This is the key to preserving correct real-time last candles.

#### 4. Persistence And Analytics Consumers

Consume only closed-candle events.

Responsibilities:

- persist finalized candles to Mongo
- update volatility windows incrementally
- maintain bounded Redis read models

## Why `5T+` Live Accuracy Still Works

The redesign must not derive `5T+ now` from finalized `1T` candles only.

It should derive `5T+ now` from:

- closed `1T` candles already inside the interval
- plus the current live `1T_now`

For example, current `15T now` at `12:07` should be built from:

- finalized `1T_closed` for `12:00` through `12:06`
- current `1T_now` for `12:07`

That gives correct:

- `open`: first candle open in the interval
- `high`: max of all finalized highs and current `1T_now` high
- `low`: min of all finalized lows and current `1T_now` low
- `close`: current `1T_now` close

So the redesign is:

- closed-bar path: event-driven from `1T_closed`
- live-now path: event-driven from `1T_now`

not:

- closed-bar path only

## Target Data Flow

```text
market_ingest local state
  -> premium snapshot runtime
    -> premium|{combination} local cache
    -> premium_snapshot event

premium_snapshot event
  -> 1T live aggregator
    -> INFO_CORE|{combination}_1T_now
    -> 1T_now event
    -> on minute boundary: 1T_closed event

1T_now event
  -> 5T/15T/30T/1H/4H live aggregators
    -> INFO_CORE|{combination}_{interval}_now

1T_closed event
  -> higher-interval finalize logic
  -> Mongo writer
  -> volatility updater
  -> bounded history cache updater
```

## Redis Model

### Keep

- `*_now` read models for current candle snapshots
- bounded live stream for external consumers when needed

### Change

Do not keep rebuilding full Redis history DataFrames on every close.

Instead:

- keep `*_now` as the hot read model
- keep a bounded append-only close stream or ring buffer for recent closed candles
- use Mongo as the long-horizon historical source of truth

Suggested pattern:

- `INFO_CORE|{combination}|1T|closed`
- `INFO_CORE|{combination}|5T|closed`
- `INFO_CORE|{combination}|15T|closed`

These can be Redis Streams or bounded Lists, but they should be append-oriented, not full-DataFrame rewrite oriented.

## In-Memory State Model

Each aggregator process should keep its current interval state in memory, keyed by `base_asset`.

Suggested internal state per interval:

- `open`
- `high`
- `low`
- `close`
- `tp`
- `scr`
- `atp24h`
- `converted_tp`
- current `dollar`
- current interval start

This avoids repeated Redis deserialize -> DataFrame -> reserialize loops.

## Server Check Model

Replace key scans with direct lookup.

Current anti-pattern:

- scan all keys
- filter keys in Python

Target:

- fetch exact market keys only
- for example `INFO_CORE|SERVER_CHECK|{market_code}`

For a market combination:

- direct GET `target_market_code`
- direct GET `origin_market_code`

No `KEYS`, no full keyspace scan.

## Volatility Model

Move volatility to incremental update from `1T_closed`.

Target behavior:

- on each `1T_closed`, compute `SL_high - LS_low`
- append only the latest value into a bounded rolling window per `base_asset`
- update current volatility summary from that rolling window

This replaces the current periodic full collection rescan.

Suggested storage:

- Redis bounded list / stream for rolling spread values
- Mongo materialized volatility collection for external reads

## Process Topology

### Current

Per market combination:

- `1T` process
- `5T`
- `15T`
- `30T`
- `1H`
- `4H`

plus monitoring threads

### Target

Per market combination:

- `premium snapshot worker`
- `1T live/finalize worker`
- one `higher-interval worker` handling all `5T+` intervals for that combination

This reduces process count and consolidates repeated reads.

## Migration Plan

### Phase 1. Premium Snapshot Cache

Introduce per-combination premium snapshot cache in `info_core`.

Result:

- `1T` worker stops rebuilding premium state directly from raw Redis every loop
- hot-path CPU cost drops immediately

### Phase 2. `1T` Event Emitter

Refactor `1T` worker to:

- maintain in-memory current-minute state
- publish `1T_now`
- emit `1T_closed` at minute boundary

Result:

- `1T` becomes the only source of truth for minute candles

### Phase 3. Higher-Interval Event Consumer

Replace `5T+` polling with a consumer that reacts to:

- `1T_now` for live open-candle updates
- `1T_closed` for exact close/finalize transitions

Result:

- correct live `5T+ now`
- no repeated polling loops over Redis snapshots

### Phase 4. History Storage Rewrite

Replace full-DataFrame Redis history rewrite with append-only bounded close events.

Result:

- reduced pickle churn
- lower Redis bandwidth and CPU

### Phase 5. Server Check Cleanup

Replace `KEYS` scanning with exact key access.

Result:

- lower Redis overhead
- more predictable runtime cost

### Phase 6. Incremental Volatility

Move volatility updates to closed-bar consumers.

Result:

- remove periodic full Mongo rescan
- smoother write cost

## Acceptance Criteria

The redesign is acceptable only if all of the following are true.

- `1T now` matches current premium movement
- `5T+ now` changes while the interval is still open
- `5T+` finalized candles match the previous implementation within expected floating-point tolerance
- Redis CPU and bandwidth are lower under the same enabled market set
- Mongo write volume becomes more regular and less bursty
- no feature regression in community-facing candle reads

## Recommended Implementation Order

Implement in this order:

1. premium snapshot cache
2. `1T now` / `1T closed` split
3. higher-interval consumer rewrite
4. Redis history rewrite
5. server-check cleanup
6. incremental volatility

That order gives measurable wins early without forcing a big-bang rewrite.
