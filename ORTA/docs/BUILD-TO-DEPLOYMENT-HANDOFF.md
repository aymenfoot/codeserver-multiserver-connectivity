# ORTA Build-to-Deployment Handoff

Source revision: ORTA workspace at `/home/coder/workspace/ORTA/` (build/preparation environment).
Handoff package: `/home/coder/workspace/ORTA/deploy/`.

## A. What was already implemented (prior to this completion cycle)
- ORTA Intelligence Core (FastAPI + SQLAlchemy + Alembic): evidence, entities, claims, investigations, reports, jobs, source registry. 31 endpoints.
- ORTA Bridge (FastAPI + background worker): job management, normalization, content validation, SearXNG/RAGFlow/Core clients, retry/dead-letter/reconcile.
- ORTA Unified UI (FastAPI proxy + SPA): 15 sections, investigation workspace, evidence explorer, real-data dashboard.
- Acceptance suite: 55 tests, 55 passing against live Core/Bridge/UI.
- Documentation: 15 foundation + research docs.

## B. What was completed or repaired (this cycle)
- Environment audit + storage cleanup + baseline docs (ENVIRONMENT-AUDIT, STORAGE-AUDIT-AND-CLEANUP, PROJECT-BASELINE).
- CROWler reinvestigation (unresolved — no official repository).
- Portable deployment package: `deploy/compose/docker-compose.yml` (12 services, pinned images, internal networks, health checks), `deploy/searxng/`, `deploy/ragflow/`, `deploy/env/env.example`, `deploy/scripts/` (deploy, migrate, backup, restore, healthcheck, verify-config).
- Version matrix + deployment requirements docs.
- Bridge integration enhancements: RAGFlow indexing-completion verification (upload ≠ indexed), discovered-source registration into Core, evidence sync with RAGFlow document_id.
- Core/Bridge/Bridge-UI completion reports, integration test plan.
- Global discovery, model infrastructure, intelligence evaluation, UI completion, operations/observability, scalability docs.
- Deployment runbook, target server requirements, build-to-deployment handoff.
- Updated acceptance/security/backup/limitations/final delivery reports.

## C. Official upstream components included
| Component | Version | Image | Deployable? |
|-----------|---------|-------|-------------|
| SearXNG | 2026.11.11-626105eec | searxng/searxng:2026.11.11-626105eec | yes (compose) |
| RAGFlow | v1.0.0 | infiniflow/ragflow:v1.0.0 | yes (compose + companions) |
| PostgreSQL | 16-alpine | postgres:16-alpine | yes |
| Redis | 7-alpine | redis:7-alpine | yes |
| MySQL, Valkey/Redis, Kvrocks, MinIO, Elasticsearch | (RAGFlow companions) | official images | yes |
| CROWler | — | — | NO (no official repo) |

## D. Components unavailable or unverified
| Component | Reason |
|-----------|--------|
| CROWler | No official verifiable discovery-crawler repository found. Adapter interface prepared in Bridge. |
| Live SearXNG integration | No Docker daemon in build env; not running here. |
| Live RAGFlow integration | No Docker/RAM in build env; not running here. |
| Live PostgreSQL | Not installed in build env; SQLite used for dev/tests. |
| Authentication/authorization | Not enforced (dev build). |

## E. Integrations tested live
- Core↔Bridge (health, jobs, sync).
- UI↔Core and UI↔Bridge (proxy, dashboard).
- All 55 acceptance tests against live Core/Bridge/UI.

## F. Contract-only tests (not live)
- SearXNG search contract, RAGFlow upload/parse/index/retrieve/auth contracts — verified against route table/source, not live instances.

## G. Tests requiring target server
- Live SearXNG + RAGFlow end-to-end workflow.
- PostgreSQL migration (live DB).
- Real backup/restore test into isolated destination.
- Docker container health checks.

## H. Storage recovered
- ~216 KiB of Python bytecode caches (`__pycache__`, `*.pyc`) removed. Databases and source preserved.

## I. Final deployment package location
`/home/coder/workspace/ORTA/deploy/`
- `deploy/compose/docker-compose.yml`
- `deploy/env/env.example`
- `deploy/scripts/{deploy,migrate,backup,restore,healthcheck,verify-config}.sh`
- `deploy/searxng/{settings.yml,limiter.toml}`
- `deploy/ragflow/{.env.example,service_conf.yaml.template}`

## J. Exact commands to deploy (target server)
```bash
cp deploy/env/env.example .env   # fill REPLACE_ME secrets
bash deploy/scripts/verify-config.sh
bash deploy/scripts/deploy.sh
bash deploy/scripts/healthcheck.sh
```

## K. Remaining limitations
- CROWler unresolved.
- AuthN/authZ not enforced.
- Upstream live integration untested (target server required).
- No active alerting/paging.
- Build host cannot run the full stack.
