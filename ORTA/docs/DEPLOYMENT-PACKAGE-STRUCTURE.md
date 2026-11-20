# ORTA Deployment Package Structure

Portable deployment package lives under `/home/coder/workspace/ORTA/deploy/`. It is self-contained and targets a separate server where Docker and Docker Compose are available.

```
deploy/
├── compose/
│   ├── docker-compose.yml          # Full ORTA stack (Core, Bridge, UI, Postgres, Redis, SearXNG, RAGFlow + companions)
│   ├── compose.override.yml.example # Example local overrides (not committed with secrets)
│   └── README.md                    # Compose usage notes
├── searxng/
│   ├── settings.yml                 # SearXNG settings (JSON enabled, internal-only)
│   └── limiter.toml                 # Rate-limiter config (disabled by default)
├── ragflow/
│   ├── .env.example                 # RAGFlow env template (placeholders only)
│   └── service_conf.yaml.template   # RAGFlow service config template
├── env/
│   └── env.example                  # Master ORTA env template (placeholders only, no real secrets)
├── scripts/
│   ├── deploy.sh                    # Full deployment: prep → pull → init → migrate → up → health
│   ├── migrate.sh                   # Alembic migrations for ORTA Core (+Bridge)
│   ├── backup.sh                    # Backup Postgres + volumes + config
│   ├── restore.sh                   # Restore into isolated destination (never overwrites prod)
│   ├── healthcheck.sh               # Verify all service health endpoints
│   └── verify-config.sh             # Validate compose + env before deploying
├── healthchecks/
│   └── README.md                    # Per-service health check definitions
├── backup/
│   └── README.md                    # Backup directory placeholder (created at runtime)
└── restore/
    └── README.md                    # Restore directory placeholder (created at runtime)
```

## Portability rules
- No real secrets committed anywhere (only `.example` templates with placeholders).
- No hardcoded build-host paths (`/home/coder/...`). All paths are Docker volume names or `/opt/orta/...` target paths.
- All image tags pinned (see `docs/UPSTREAM-VERSION-MATRIX.md`).
- Services communicate over internal Docker networks; databases/admin ports not published to the host.
- `deploy/` is the single deployable artifact; it can be copied to the target server and run with `./scripts/deploy.sh`.

## Compose services (summary)
- `postgres` — ORTA Core/Bridge production database
- `redis` — cache + job queue
- `orta-core` — ORTA Intelligence Core (port 8000 internal)
- `orta-bridge` — ORTA Bridge (port 8001 internal)
- `orta-ui` — ORTA Unified UI (port 3000 internal, published to host reverse proxy)
- `searxng` — SearXNG metasearch (port 8080 internal)
- `ragflow` — RAGFlow app (ports 80/9380/9381 internal)
- `mysql`, `valkey`, `kvrocks`, `minio`, `elasticsearch` — RAGFlow companions
- `ragflow-sandbox` — RAGFlow parsing sandbox (docker-in-docker or socket mount)

## Internal networks
- `orta-internal` — all ORTA + upstream services (DBs not exposed externally)
- `orta-frontend` — UI + public gateway (only UI port published)
