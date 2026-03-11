# ACW Monorepo

This repository is the root monorepo for ACW.

It was assembled from the previously separate repositories:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core`
- `arbitrage_community`
- `arbitrage_trade`

The monorepo direction is:

- one root Git repository
- service-based monorepo layout
- shared architecture and deployment docs
- shared internal libraries where duplication exists
- separate runtime services preserved

## Target Layout

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
  packages/
    python/
    js/
  docs/
    architecture/
  scripts/
    monorepo/
```

## Runtime Services That Stay Separate

These should remain separate deployable units even after monorepo migration:

- `community_web`
- `community_drf`
- `news_core`
- `info_core`
- `trade_core` engine
- `trade_core` API
- `hdwallet_service`

## Migration Assets

- Architecture map: [docs/architecture/service-dependency-map.md](docs/architecture/service-dependency-map.md)
- Migration plan: [docs/architecture/monorepo-migration-plan.md](docs/architecture/monorepo-migration-plan.md)
- Consolidation matrix: [docs/architecture/consolidation-matrix.md](docs/architecture/consolidation-matrix.md)
- Core runtime boundaries: [docs/architecture/core-runtime-boundaries.md](docs/architecture/core-runtime-boundaries.md)
- Execution data plane recommendation: [docs/architecture/execution-data-plane-recommendation.md](docs/architecture/execution-data-plane-recommendation.md)
- Dev/prod workflow: [docs/workflows/dev-prod-workflow.md](docs/workflows/dev-prod-workflow.md)
- Import manifest: [scripts/monorepo/repos.manifest](scripts/monorepo/repos.manifest)
- Import script: [scripts/monorepo/create_monorepo.sh](scripts/monorepo/create_monorepo.sh)

## Import Workflow

1. Review and commit or stash changes in each nested repository.
2. Run the preflight check:

```bash
./scripts/monorepo/create_monorepo.sh --check
```

3. Create the monorepo in a separate destination directory:

```bash
./scripts/monorepo/create_monorepo.sh ../acw-monorepo
```

If you want the current dirty working tree state copied too:

```bash
./scripts/monorepo/create_monorepo.sh --overlay-working-tree ../acw-monorepo
```

The import script preserves history by using `git merge --allow-unrelated-histories`
and `git read-tree --prefix`.

## Notes

- Runtime services still remain separate even though source control is unified.
- `info_core` and `trade_core` should share internal libraries where practical, but they should not be merged into one runtime.
- The pre-monorepo workspace has been archived at `/Users/charlie/Projects/acw-legacy-20260311`.
