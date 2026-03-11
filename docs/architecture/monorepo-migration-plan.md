# ACW Monorepo Migration Plan

## Recommendation

Yes. ACW should be managed as one root repository.

But it should become a **monorepo of services**, not a single merged application.

That means:

- one root Git repository
- one architecture view
- one CI/CD entry point
- one shared docs/env/deploy structure
- separate runtime services preserved where needed

## What To Integrate

Integrate these into the root monorepo:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core`
- `arbitrage_community`
- `arbitrage_trade`

Also integrate:

- root docs
- root env templates
- root compose and deployment definitions
- shared tooling and CI

## What Should Stay Separate At Runtime

Do not collapse these into one running app:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core_engine`
- `trade_core_api`
- `hdwallet_service`

These have different scaling, failure, scheduling, and dependency patterns.

## What Can Be Unified Internally

### Shared Python Runtime Layer

Candidates for extraction from `info_core` and `trade_core`:

- exchange adaptors
- websocket clients
- logging setup
- env/config bootstrap
- Redis/Mongo/Postgres connectors
- `ACW_API_URL` client

Suggested destination:

- `packages/python/acw_common/`

### Shared Deployment Layer

Current compose repos should be absorbed into:

- `infra/compose/community/`
- `infra/compose/trade/`

Use a base file plus env overlays instead of duplicating full files.

### Shared Architecture Docs

Keep system-level docs only at root:

- dependency map
- service ownership
- runtime contracts
- env contract
- migration notes

## What Should Probably Be Reorganized, Not Merged

### `community_drf`

Keep as one Django service for now, but split it logically:

- `domains/community/`
- `domains/auth/`
- `domains/referral/`
- `integrations/tradecore/`
- `integrations/infocore/`
- `integrations/wallet/`
- `platform/common/`

Do not try to split this into multiple deployable Django services first. That would add risk too early.

### `trade_core`

Keep one repo area, but treat it as two runtimes:

- engine
- API

They can share code, but should not be forced into one process.

Also, `trade_core` should not be collapsed into `info_core`.
The engine intentionally maintains its own execution-critical market state to avoid cross-service delay and to preserve multi-node/IP-distributed execution.

### `news_core`

Keep separate as a worker-style service. It is operationally different from the web/backend stack.

### `info_core`

Keep separate as a long-running data engine. It is closer to streaming infrastructure than to a normal backend.

Also, `info_core` should remain horizontally partitionable by enabled market sets and master/non-master responsibilities.

## Recommended Target Layout

```text
acw/
  apps/
    community_web/
    community_drf/
  services/
    news_core/
    info_core/
    trade_core/
  infra/
    compose/
      community/
      trade/
    docker/
  packages/
    python/
      acw_common/
    js/
  docs/
    architecture/
  scripts/
```

This keeps service identity clear while giving you one place to reason about the system.

## Migration Strategy

### Phase 1. Monorepo First, No Runtime Changes

- create root Git repository
- import each existing repo with history preserved
- remove nested `.git` directories after import
- do not change service code yet
- do not change runtime topology yet

Preferred approach:

- use `git subtree` or history-preserving import
- avoid "copy files + new init" unless history loss is acceptable

### Phase 2. Normalize Layout

- move service folders into `apps/`, `services/`, `infra/`
- add root README and architecture docs
- add root `.gitignore`
- centralize env examples and operational docs

### Phase 3. Unify Deployment Definitions

- fold `arbitrage_community` and `arbitrage_trade` into root `infra/compose`
- remove duplicated test/prod compose structure where possible
- introduce shared base compose + environment overrides

### Phase 4. Extract Shared Libraries

- extract duplicated Python integration/runtime code
- introduce internal packages with stable import paths
- update `info_core` and `trade_core` to consume shared packages
- do not centralize execution-critical tick flow into a shared runtime while doing so

### Phase 5. Clean Service Boundaries

- reduce datastore-coupled reads where appropriate
- define internal contracts for `community_drf <-> trade_core`
- decide which shared DB access patterns should remain and which should become API contracts

## Non-Goals For The First Migration

Do not do these in the first pass:

- merge all services into one process
- merge all databases
- rewrite `community_drf` into microservices
- replace all compose/deploy logic at once
- force frontend/backend/shared package refactors before root import

## Practical Decision

The correct immediate move is:

1. convert the workspace into a real monorepo
2. preserve service boundaries
3. centralize deployment and documentation
4. then refactor shared code and integration boundaries

That gives global visibility without destabilizing runtime behavior.
