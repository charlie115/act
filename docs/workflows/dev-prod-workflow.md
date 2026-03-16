# Dev And Deploy Workflow

## Goal

Use the monorepo root as the single entry point for:

- environment file initialization
- Docker image builds
- frontend image build and local Next.js dev server
- development, testing, and production stack management
- multi-worker deployment with per-worker market code assignment

## Node Types

| Node | Stack | Services | Purpose |
|------|-------|----------|---------|
| **Master** | `community` | Django, info_core (MASTER=true), Celery, PostgreSQL, Redis, MongoDB, news_core, hdwallet | User-facing backend + market data |
| **Worker** | `worker` | info_core (MASTER=false) | Kline generation for assigned market codes |
| **Trade** | `trade` | trade_core, trade_core_api, PostgreSQL | Trading execution + trigger evaluation |

## Compose Layout

```
infra/compose/
├── community/              # Master node
│   ├── compose.base.yml
│   ├── compose.dev.yml
│   ├── compose.testing.yml
│   └── compose.production.yml
│
├── worker/                 # Worker nodes (multi-instance)
│   ├── compose.base.yml
│   ├── compose.dev.yml
│   ├── compose.testing.yml
│   ├── compose.production.yml
│   └── workers/            # Per-worker configs
│       ├── worker1.env
│       └── worker2.env.example
│
└── trade/                  # Trade node
    ├── compose.base.yml
    ├── compose.dev.yml
    ├── compose.testing.yml
    └── compose.production.yml
```

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

Bring up the Master node backend:

```bash
make dev-up STACK=community
```

Start the local Next.js dev server (runs outside Docker):

```bash
make web-dev
```

The local frontend: `http://localhost:3000`, backend: `http://localhost:8000`.

Bring up the Trade node:

```bash
make dev-up STACK=trade
```

Stop stacks:

```bash
make dev-down STACK=community
make dev-down STACK=trade
make dev-down STACK=all
```

Inspect compose status or logs:

```bash
make stack STACK=community ENV=dev ACTION=ps
make stack STACK=community ENV=dev ACTION=logs ARGS="drf -f"
make stack STACK=trade ENV=dev ACTION=logs ARGS="trade-core -f"
```

## Worker Workflow

Workers run independently with per-worker market code assignment.

List available worker configs:

```bash
make worker-list
```

Start a specific worker:

```bash
make worker-up NAME=worker1              # dev (default)
make worker-up NAME=worker1 ENV=prod     # production
```

Stop a worker:

```bash
make worker-down NAME=worker1
make worker-down NAME=worker1 ENV=prod
```

### Adding a New Worker

1. Copy the example: `cp infra/compose/worker/workers/worker2.env.example infra/compose/worker/workers/worker3.env`
2. Edit `worker3.env`:
   - Set `WORKER_NAME=worker3`
   - Set `WORKER_MARKET_KLINES="BITHUMB_SPOT/KRW:OKX_USD_M/USDT"`
   - Set Master node connection (MongoDB, Redis, ACW API URL)
3. Start: `make worker-up NAME=worker3`

Each worker runs as an independent Docker project with isolated containers and networks.

## Production Workflow

Build and deploy Master node:

```bash
make prod-up STACK=community
```

Deploy Trade node:

```bash
make prod-up STACK=trade
```

Deploy workers:

```bash
make worker-up NAME=worker1 ENV=prod
make worker-up NAME=worker2 ENV=prod
```

Shut down:

```bash
make prod-down STACK=community
make prod-down STACK=trade
make worker-down NAME=worker1 ENV=prod
```

## Lower-Level Commands

Build backend images only:

```bash
make build-images STACK=community ENV=dev
make build-images STACK=trade ENV=testing
make build-images STACK=all ENV=production
```

Build frontend only:

```bash
make build-web ENV=production
```

## Environment Configuration

### Master Node

Service-level `.env` files in each service directory:
- `services/info_core/.env.dev`, `.env.test`, `.env.prod`
- `apps/community_drf/.env.dev`, `.env.test`, `.env.prod`

Compose-level `.env` in `infra/compose/community/{dev,testing,production}/.env`

### Worker Node

Per-worker configs in `infra/compose/worker/workers/workerN.env`:
- `WORKER_MARKET_KLINES` — market codes this worker processes
- `WORKER_MONGODB_HOST` — Master's MongoDB for kline storage
- `WORKER_REDIS_HOST` — Master's Redis for shared data
- `WORKER_ACW_API_URL` — Master's Django for messaging

### Trade Node

- `services/trade_core/.env.dev`, `.env.test`, `.env.prod`
- `infra/compose/trade/{dev,testing,production}/.env`

### Dev-Only Settings

- `DEV_MAX_SYMBOLS=10` — limits symbols to top 10 by volume (reduces CPU/memory)
- `BINANCE_PROC_MULTIPLIER=1` — reduces WebSocket processes

## Notes

- `make env-init` only creates missing files unless `FORCE=1` is passed.
- Community `dev-up` does not start the frontend container (runs locally via `make web-dev`).
- Workers connect to Master's MongoDB/Redis — ensure network connectivity.
- `apps/community_web` is the legacy CRA frontend (reference only).
- Runtime services remain separated even though source control is unified.
