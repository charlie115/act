# ACW Consolidation Matrix

## Merge Into The Root Monorepo

These should be imported into one root repository and managed together:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core`
- `arbitrage_community`
- `arbitrage_trade`
- root docs
- root deployment scripts
- shared CI/CD
- shared env contract documentation

## Keep As Separate Runtime Services

These should remain independently deployable and independently startable:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core` engine
- `trade_core` API
- `hdwallet_service`

Additional rule:

- `info_core` and `trade_core` may share code, but must remain separate runtime planes because trading execution is latency-sensitive and node/IP-distributed.

## Unify As Shared Internal Packages

These are strong candidates for extraction into shared libraries after the monorepo import:

### Python

- ACW API client used by `info_core` and `trade_core`
- exchange REST adaptors
- exchange websocket helpers
- Redis connection helpers
- MongoDB/Postgres bootstrap helpers
- logging bootstrap
- environment loading and config parsing

### JavaScript

- frontend API contract typings or schema snapshots
- shared endpoint definitions if contract tooling is introduced later

## Keep Logically Separate Inside The Monorepo

These should live in one repository but still have clear boundaries:

### `community_drf`

Split logically into:

- community domain
- auth domain
- referral/coupon domain
- integrations: `tradecore`, `infocore`, `wallet`
- platform/common library

### `trade_core`

Split logically into:

- engine runtime
- API runtime
- shared trading domain code

### `info_core`

Split logically into:

- exchange ingest
- data generation
- AI/analytics generation
- operational control

## Do Not Merge Early

Avoid these early migration moves:

- collapsing all Python services into one runtime
- merging `community_drf` and `trade_core` into one backend
- moving `news_core` into Django app code
- merging all databases
- removing API boundaries before contract mapping is complete

## Recommended Order

1. Merge repositories into one root monorepo
2. Consolidate infra and compose definitions
3. Extract duplicated runtime libraries
4. Refactor service boundaries internally
5. Revisit which API or datastore integrations should be tightened or reduced
