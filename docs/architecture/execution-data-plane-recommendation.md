# Execution Data Plane Recommendation

## Question

Should `trade_core` consume premium data computed by `info_core`, or should it keep computing local market state and premium on the trade node?

## Recommendation

Do **not** move execution-critical premium computation fully into `info_core`.

If forced to choose between the two current extremes, keep the current direction closer to `trade_core` local computation.

But the better target is a **hybrid per-host execution data plane**:

- `info_core`: shared analytics/data plane
- `trade_core market sidecar`: host-local real-time market ingest + premium cache
- `trade_core executor`: trigger evaluation + order execution

## Why

### Current `trade_core` Hot Path Is Extremely Tight

The trade trigger loop runs at very short intervals for trading paths.

That makes added hops expensive:

- websocket receive
- normalize/update local state
- compute premium
- merge with trade config
- evaluate trigger
- execute trade

Adding:

- `info_core` compute
- publish/serialize
- network transfer
- deserialize/consume in `trade_core`

would add jitter, backpressure risk, and another failure domain.

### `info_core` Is Better For Shared Data, Not Trade-Decision Hot Paths

`info_core` already fits these responsibilities:

- kline generation
- volatility/arbitrage/funding analytics
- community-facing data serving
- discovery of activated market combinations

Those workloads tolerate shared-service latency better than trade execution does.

### Centralizing Hot Premium Computation Creates a Worse Bottleneck

If `info_core` becomes the single premium producer for all trade nodes:

- `info_core` becomes a central hot-path bottleneck
- one lagging producer can affect all trade nodes
- failure blast radius increases
- trade execution becomes dependent on inter-service freshness

That is a poor trade for a latency-sensitive execution path.

## What To Change Instead

### Keep Local On Trade Hosts

Keep these local to each trade host:

- exchange websocket/book/ticker ingest
- local normalized market snapshot
- convert-rate cache needed for execution
- premium calculation used by triggers
- trigger loops
- order execution

### Move Only Non-Critical Or Slow Data To Shared Planes

Fine to share from `info_core`:

- kline/historical data
- volatility/funding summaries
- AI recommendations
- community-facing market data
- market activation registry
- health/status information

### Reduce Duplication Per Host, Not Across All Hosts

The best optimization is not "one global `info_core` computes everything".

The best optimization is:

- one local market-data producer per trade host
- multiple local trigger/execution workers consume that producer

That preserves low latency while avoiding duplicate websocket and premium work among workers on the same host.

## Practical Target Shape

Inside the monorepo, evolve toward:

- `services/info_core/`: shared analytics plane
- `services/trade_core/market_runtime/`: host-local ingest and premium cache
- `services/trade_core/execution_runtime/`: trigger and execution workers
- shared library for duplicated exchange/premium code

## Decision Summary

- `info_core -> trade_core` for execution-critical premium feed: not recommended
- current fully duplicated architecture: safer than central hot premium feed, but wasteful
- recommended end state: hybrid local execution data plane plus shared analytics plane
