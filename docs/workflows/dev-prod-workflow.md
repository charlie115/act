# Dev And Deploy Workflow

## Goal

Use the monorepo root as the single entry point for:

- environment file initialization
- Docker image builds
- frontend image build and local Next.js dev server
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

For day-to-day frontend development:

- backend/data services run in Docker
- `community_web_next` runs locally with `next dev`
- hot reload happens outside Docker

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

Bring up the backend/data services for local development:

```bash
make dev-up STACK=all
```

Bring up only the community-side backend stack:

```bash
make dev-up STACK=community
```

Start the local Next.js dev server:

```bash
make web-dev
```

The local frontend will be available on `http://localhost:3000`.
The backend will be available on `http://localhost:8000`.

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

Run the local frontend dev server:

```bash
make web-dev
```

The old frontend artifact sync command is now a no-op because the official frontend runs as a container:

```bash
make sync-web ENV=testing
make sync-web ENV=production
```

## Notes

- `make env-init` only creates missing files unless `FORCE=1` is passed.
- `make build-web` now runs a local Next.js production build in `apps/community_web_next`.
- `make web-dev` runs `community_web_next` locally with hot reload on port `3000`.
- Community `dev-up` uses `infra/compose/community/compose.dev.yml` and does not start the frontend container.
- Runtime services remain separated even though source control is unified.
