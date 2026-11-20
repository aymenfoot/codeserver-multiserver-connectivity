# ORTA Upstream Version Matrix

Pinned upstream versions for the portable deployment package. No `latest` tags are used anywhere.

| Component | Official repository | Selected version | Image / artifact | Deployment method | Status |
|-----------|---------------------|------------------|------------------|-------------------|--------|
| SearXNG | github.com/searxng/searxng | date-based `2026.11.11-626105eec` (verified HEAD `368baa34...`) | `searxng/searxng:2026.11.11-626105eec` | Docker Compose | Pinned; ready to deploy |
| RAGFlow | github.com/infiniflow/ragflow | `v1.0.0` (2026-11-06, commit `db1cd592...`) | `infiniflow/ragflow:v1.0.0` | Docker Compose | Pinned; ready to deploy |
| CROWler | — | — | — | — | UNRESOLVED: no official verifiable discovery-crawler repository |

RAGFlow v1.0.0 required companion services (pinned via the official `docker-compose-base.yml` pattern):
- MySQL (official `mysql:8` community image) — application database
- Valkey / Redis (official `valkey/valkey:8` or `redis:7-alpine`) — cache + message queue
- Kvrocks (official `gresearch/kvrocks`) — Go services cache backend
- MinIO (official `minio/minio:RELEASE.2023-...`) — object storage
- Elasticsearch or Infinity — document/search engine
- Docker sandbox — parsing services (container runtime access required)

## Environment variables (placeholders only — no real secrets committed)

| Variable | Example placeholder | Used by |
|----------|---------------------|---------|
| `SEARXNG_IMAGE` | `searxng/searxng:2026.11.11-626105eec` | Compose |
| `SEARXNG_SECRET` | `<generate with secrets.token_hex(32)>` | SearXNG |
| `SEARXNG_BASE_URL` | `http://searxng:8080/` | SearXNG |
| `RAGFLOW_IMAGE` | `infiniflow/ragflow:v1.0.0` | Compose |
| `RAGFLOW_VERSION` | `v1.0.0` | Compose/docs |
| `MYSQL_IMAGE` | `mysql:8` | Compose |
| `MYSQL_ROOT_PASSWORD` | `<secret>` | RAGFlow |
| `RAGFLOW_DB_PASSWORD` | `<secret>` | RAGFlow |
| `MINIO_ROOT_USER` | `<secret>` | RAGFlow object storage |
| `MINIO_ROOT_PASSWORD` | `<secret>` | RAGFlow object storage |
| `ORTA_CORE_URL` | `http://orta-core:8000` | Bridge/UI |
| `ORTA_BRIDGE_URL` | `http://orta-bridge:8001` | UI |
| `ORTA_RAGFLOW_URL` | `http://ragflow:9380` | Bridge |
| `ORTA_RAGFLOW_API_KEY` | `<secret>` | Bridge→RAGFlow |
| `ORTA_DATABASE_URL` | `postgresql+psycopg2://orta:<secret>@postgres:5432/orta` | Core |
| `POSTGRES_PASSWORD` | `<secret>` | Core database |
| `REDIS_PASSWORD` | `<secret>` | Cache/queue |

## Breaking changes and compatibility

- SearXNG: date-based versioning; pinned tag stable. JSON output requires `formats: json` in `settings.yml` (enabled in the reference config). `/healthz` returns `OK`.
- RAGFlow: v1.0.0 removed v0.x endpoint aliases (e.g. `/api/v1/file/upload` → `/api/v1/datasets/{id}/documents`, `/v1/system/healthz` → `/api/v1/system/healthz`); dataset creation uses `parse_type`/`parser_id` instead of legacy `chunk_method`. Bridge client written against v1.0.0 route table.
- CROWler: N/A (no repository).

## Version pin source

`docs/UPSTREAM-RESEARCH.md §6`, `docs/API-CONTRACTS-RESEARCH.md §4`, `docs/UPSTREAM-DEPLOYMENT-REQUIREMENTS.md`.
