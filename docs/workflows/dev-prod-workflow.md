# Dev And Deploy Workflow

## Goal

Use the monorepo root as the single entry point for:

- environment file initialization
- Docker image builds
- frontend build and artifact sync
- testing stack startup and shutdown
- production stack startup and shutdown

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

Sync built frontend artifact into the host path expected by compose:

```bash
make sync-web ENV=testing
make sync-web ENV=production
```

## Notes

- `make env-init` only creates missing files unless `FORCE=1` is passed.
- Community compose expects frontend build artifacts under:
  - `~/test-community-web/build`
  - `~/prod-community-web/build`
- The root workflow script syncs the frontend build output to those paths automatically.
- Runtime services remain separated even though source control is unified.
