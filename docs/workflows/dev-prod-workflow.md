# Dev And Deploy Workflow

## Goal

Use the monorepo root as the single entry point for:

- environment file initialization
- Docker image builds
- frontend image build and optional local Next.js build
- testing stack startup and shutdown
- production stack startup and shutdown

The root workflow now prefers the normalized compose layout and the official Next.js frontend:

- `infra/compose/community/compose.base.yml`
- `infra/compose/community/compose.testing.yml`
- `infra/compose/community/compose.production.yml`
- `infra/compose/trade/compose.base.yml`
- `infra/compose/trade/compose.testing.yml`
- `infra/compose/trade/compose.production.yml`

Legacy environment-specific `testing/docker-compose.yml` and `production/docker-compose.yml`
are left in place as fallback references.

The official public frontend is now `apps/community_web_next`.
The CRA app remains in the repo as legacy source, but the root workflow no longer depends on its build artifact.

## Commands

From the repository root:

```bash
make help
make doctor
make env-init
```

## Development Workflow

Initialize missing env files:

```bash
make env-init
```

Bring up everything needed for the testing/development stack:

```bash
make dev-up STACK=all
```

Bring up only the community-side stack:

```bash
make dev-up STACK=community
```

Bring up only the trade-side stack:

```bash
make dev-up STACK=trade
```

Stop stacks:

```bash
make dev-down STACK=all
```

Inspect compose status or logs:

```bash
make stack STACK=community ENV=testing ACTION=ps
make stack STACK=community ENV=testing ACTION=logs ARGS="drf -f"
make stack STACK=trade ENV=testing ACTION=logs ARGS="trade-core -f"
```

## Production Workflow

Build and deploy both stacks:

```bash
make prod-up STACK=all
```

Deploy only one stack:

```bash
make prod-up STACK=community
make prod-up STACK=trade
```

Shut down:

```bash
make prod-down STACK=all
```

## Lower-Level Commands

Build backend images only:

```bash
make build-images STACK=all ENV=testing
make build-images STACK=all ENV=production
```

Build frontend only:

```bash
make build-web ENV=testing
make build-web ENV=production
```

The old frontend artifact sync command is now a no-op because the official frontend runs as a container:

```bash
make sync-web ENV=testing
make sync-web ENV=production
```

## Notes

- `make env-init` only creates missing files unless `FORCE=1` is passed.
- `make build-web` now runs a local Next.js production build in `apps/community_web_next`.
- Community stack startup uses the `community-web-next` container as the public entrypoint.
- Runtime services remain separated even though source control is unified.
