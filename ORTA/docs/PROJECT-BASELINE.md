# ORTA Project Baseline

Baseline established: 2026-11-20
ORTA workspace: `/home/coder/workspace/ORTA/`

## A. What exists (verified)

### Services (source present, not currently running)
- **ORTA Intelligence Core** — `core/main.py` (FastAPI), `core/models.py` (SQLAlchemy), `core/schemas.py` (Pydantic), `core/crud.py`, `core/database.py`, `core/alembic/` (migration `902782639ec4_initial_schema`). Port 8100 (dev).
- **ORTA Bridge** — `bridge/main.py` (FastAPI + background job worker), `bridge/clients.py` (Core/SearXNG/RAGFlow clients), `bridge/normalization.py`, `bridge/models.py`, `bridge/schemas.py`, `bridge/database.py`. Port 8101 (dev).
- **ORTA Unified UI** — `ui/server.py` (FastAPI proxy to Core/Bridge + SPA), `ui/static/index.html`. Port 3000 (dev).

### Tests
- `tests/acceptance.py` — 55 integration-style tests against live Core/Bridge/UI.

### Data (preserved)
- `storage/orta.db` — SQLite, Alembic head `902782639ec4`. Rows: sources 4, evidence 3, entities 1, investigations 1, reports 1, claims 1, research_questions 1.
- `storage/bridge.db` — SQLite. Rows: bridge_jobs 2, normalized_content 1.

### Documentation (15 files)
ARCHITECTURE, UPSTREAM-RESEARCH, RESOURCE-PLAN, IMPLEMENTATION-PLAN, INTELLIGENCE-CORE, INTEGRATION-ARCHITECTURE, DATA-PIPELINE, API-CONTRACTS-RESEARCH, MODEL-SPEC-RESEARCH, FINAL-DELIVERY-REPORT, ACCEPTANCE-REPORT, SECURITY-REPORT, BACKUP-RESTORE-REPORT, UPSTREAM-VERSION-MATRIX, KNOWN-LIMITATIONS.

### Missing (to be created in this completion cycle)
- `deploy/` — portable deployment package (compose, env, scripts, healthchecks, backup, restore)
- `config/` — configuration templates
- `scripts/` — deployment automation scripts
- `ENVIRONMENT-AUDIT.md`, `STORAGE-AUDIT-AND-CLEANUP.md`, `PROJECT-BASELINE.md` (this document)
- `UPSTREAM-COMPLETION.md`, `UPSTREAM-DEPLOYMENT-REQUIREMENTS.md`, `DEPLOYMENT-PACKAGE-STRUCTURE.md`, `UPSTREAM-VERSION-MATRIX.md` (update/create)
- `CORE-COMPLETION-REPORT.md`, `BRIDGE-COMPLETION-REPORT.md`, `INTEGRATION-TEST-PLAN.md`
- `GLOBAL-DISCOVERY-STRATEGY.md`, `MODEL-INFRASTRUCTURE.md`, `INTELLIGENCE-EVALUATION.md`
- `UI-COMPLETION-REPORT.md`, `OPERATIONS-AND-OBSERVABILITY.md`, `SCALABILITY.md`
- `DEPLOYMENT-RUNBOOK.md`, `TARGET-SERVER-REQUIREMENTS.md`, `BUILD-TO-DEPLOYMENT-HANDOFF.md`

## B. Service contracts (current)

| Service | Base URL | Health | Key endpoints |
|---------|----------|--------|---------------|
| Core | `http://127.0.0.1:8100/api/v1` | `/healthz` | sources, evidence, entities, claims, investigations, reports, jobs |
| Bridge | `http://127.0.0.1:8101/api/v1` | `/healthz` | jobs, normalize, discover, sync |
| UI | `http://127.0.0.1:3000` | `/` | `/api/core/*`, `/api/bridge/*`, `/api/dashboard` |

## C. Known gaps (from source inspection)

1. Bridge `_run_upload` returns `uploaded: True` immediately after RAGFlow upload WITHOUT verifying parsing/indexing completion (Part 3.D gap).
2. Bridge `_run_discover` calls SearXNG but does not register discovered sources into the Core source registry or create SourceURL records (Part 3.C / 4.A gap).
3. No authentication/authorization on Core or Bridge APIs; CORS wildcard (`allow_origins=["*"]`).
4. Bridge background worker is an infinite daemon thread with no graceful shutdown or process-manager integration.
5. No Docker Compose, no env templates, no healthchecks, no backup/restore scripts.
6. SQLite only; no PostgreSQL configuration for production.
7. `deploy/`, `config/`, `scripts/` directories are empty.

## D. Baseline constraints (carried forward)

- Build host has no root/sudo, no Docker daemon, no user namespaces → containers cannot run here.
- 6.0 GiB free disk → deployment package must be lightweight; no large duplicate copies.
- Upstream services (SearXNG, RAGFlow, CROWler) target a separate server with Docker.
- All documented versions are pinned (no `latest`): SearXNG `2026.11.11-626105eec`, RAGFlow `v1.0.0`.
- CROWler official repository not verified; adapter interface to be prepared.

## E. Acceptance baseline

Previous run: 55 passed, 0 failed against live services (services were running at that time). Services are currently stopped; baseline tests must be re-run after services are restarted to confirm the baseline still holds.
