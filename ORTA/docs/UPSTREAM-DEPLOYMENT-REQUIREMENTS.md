# ORTA Upstream Deployment Requirements

Target-server deployment requirements for each upstream component, based on official documentation and the selected pinned versions.

## 1. SearXNG — `searxng/searxng:2026.11.11-626105eec`

| Item | Requirement |
|------|-------------|
| Official repo | github.com/searxng/searxng |
| Deployment | Docker container |
| Listen port | 8080 (HTTP) inside container |
| Health endpoint | `GET /healthz` → `OK` (text/plain) |
| Required env | `SEARXNG_SECRET` (strong random), `SEARXNG_BASE_URL` |
| Config mount | `/etc/searxng` (`settings.yml`, `limiter.toml`) |
| Persistent storage | `/var/cache/searxng` (favicon cache, etc.) |
| Dependencies | None (standalone Python app); Valkey/Redis optional for rate limiting |
| Networks | Internal ORTA network only; NOT published to public |
| ORTA integration | `GET /search?q=<query>&format=json` — unauthenticated within internal network |
| Resource estimate | ~0.25–0.5 CPU, 256–512 MiB RAM, 2–5 GiB disk |
| Restart policy | `unless-stopped` |
| Health check | `wget -qO- http://localhost:8080/healthz`, interval 30s, timeout 10s, retries 3 |

### Settings (reference from verified stack)
- `use_default_settings: true`
- `formats: [html, json, csv, rss]` (JSON enabled for ORTA)
- `server.limiter: false` (private/internal); can be enabled with Valkey
- `server.public_instance: false`
- Engines: google, duckduckgo, bing, wikipedia, wikidata, arxiv, github (default set)

## 2. RAGFlow — `infiniflow/ragflow:v1.0.0`

| Item | Requirement |
|------|-------------|
| Official repo | github.com/infiniflow/ragflow |
| Deployment | Docker Compose only (official `docker/docker-compose.yml` + base) |
| Ports | Web/API 80, Go API 9380, Admin 9381 |
| Required env | `.env` + `service_conf.yaml.template` |
| Required companion services | MySQL, Valkey/Redis, Kvrocks, MinIO, Elasticsearch/Infinity, Docker sandbox |
| Auth | Bearer API token (`Authorization: Bearer <key>`); token via `/api/v1/auth/login` or `/api/v1/system/tokens` |
| Health endpoint | `GET /api/v1/system/healthz` → 200 |
| Networks | Internal ORTA network only; admin (9381) NOT published publicly |
| ORTA integration | dataset → upload → parse → index → poll status → retrieve; Bearer token |
| Resource estimate (official) | 4 CPU, 16 GB RAM, 50 GiB disk (starting config) — exceeds this build host |
| Restart policy | `unless-stopped` |

### Companion service roles
- MySQL: RAGFlow application metadata (users, datasets, documents, chunks)
- Valkey/Redis: cache + message queue (Python services)
- Kvrocks: Go services cache backend
- MinIO: object storage for uploaded files
- Elasticsearch/Infinity: document/search index
- Docker sandbox: document parsing (requires container runtime access)

## 3. CROWler — UNRESOLVED

No official verifiable repository. Not deployable. ORTA Bridge prepares a clean adapter interface for future integration once the official project is identified.

## 4. ORTA custom components (production target)

| Component | Runtime | Port | Production DB |
|-----------|---------|------|---------------|
| ORTA Core | Python/FastAPI | 8000 | PostgreSQL |
| ORTA Bridge | Python/FastAPI | 8001 | SQLite (dev) / PostgreSQL (target) |
| ORTA Unified UI | Python/FastAPI | 3000 | — (proxy only) |

### PostgreSQL (production)
- Official `postgres:15-alpine` or `postgres:16-alpine`
- Database: `orta`; user: `orta`; password via secret
- Migrations: Alembic, run at startup via `scripts/migrate.sh`
- Persistent volume: `/var/lib/postgresql/data`

### Redis (cache/queue)
- Official `redis:7-alpine`
- Persistent volume: `/data`

## 5. Target-server minimum requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 | 8+ |
| RAM | 8 GiB | 16+ GiB |
| Disk | 50 GiB | 100+ GiB |
| Docker | Engine 24+, Compose v2 | Engine 24+, Compose v2 |
| OS | Linux (amd64) | Linux (amd64) |

Note: RAGFlow alone recommends 4 CPU / 16 GB RAM / 50 GB. The full ORTA stack (Core, Bridge, UI, Postgres, Redis, SearXNG, RAGFlow + companions) exceeds the build host (4 CPU, 7.7 GB RAM, 6 GiB free). Deployment must target a separate, larger server.
