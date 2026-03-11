
## Docker Build Instructions

### 1. Build Base Image
```bash
docker build . --target base -t base-info-core:base
```

### 2. Build Development Image
```bash
docker build . --target dev -t dev-info-core:dev
```

### 3. Build Test Image
```bash
docker build . --target test -t info-core:test
```

### 4. Build Production Image
```bash
docker build . --target prod -t info-core
```

### Key Details:
- Base image includes:
  - Python 3.11
  - Redis server
  - Apache utilities
  - All Python dependencies
- Environment-specific images:
  - Copy different start scripts (`start-*-service.sh`)
  - Use corresponding env files (`.env.dev`, `.env.test`, `.env.prod`)
  - Run as daemon processes with redis-server
- Multi-stage build automatically handles base image dependency
