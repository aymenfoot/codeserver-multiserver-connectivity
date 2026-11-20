# ORTA Environment Audit

Audit performed: 2026-11-20
Build/preparation host: `75bd0b422def`
ORTA workspace: `/home/coder/workspace/ORTA/`

## A. Host environment

| Item | Value |
|------|-------|
| OS | Debian GNU/Linux 13 (trixie) |
| Kernel | Linux 7.0.0-43-generic #43-Ubuntu SMP PREEMPT_DYNAMIC x86_64 |
| CPU | 4 cores |
| RAM | 7.7 GiB total / 4.6 GiB available |
| Swap | 0 B |
| Root filesystem | overlay, 40 GiB total, 32 GiB used, 6.0 GiB free (85%) |
| User | `coder` (uid 1000), no sudo/root privileges |
| Network | Internet reachable (github.com, api.github.com respond HTTP 200) |
| Package manager | apt 3.0.3 available (cannot install system packages without root) |
| pip | pip 26.2.2 (Python 3.14, user installs work) |

## B. Runtimes

| Runtime | Version | Notes |
|---------|---------|-------|
| Python | 3.14.9 | `/home/coder/bin/python3` |
| pip | 26.2.2 | user-site installs |
| Node.js | v20.20.2 | npm 10.8.2 |
| sqlite3 module | present | Python built-in |
| PostgreSQL | not installed | no server binary |
| Redis | not installed | no server binary |
| Docker Engine | client binary only (`/home/coder/.local/bin/docker` v29.10.0) | daemon NOT installed/running; `docker compose` plugin missing |
| Docker Compose | not available | `docker compose` → unknown command |
| Rootless Docker | not usable | user namespaces blocked (`unshare -U` → Operation not permitted); no `newuidmap`/`newgidmap` |

## C. Docker / container status

- Docker client binary present but no daemon, no root, no user namespaces → **containers cannot be built or run in this environment.**
- This is a build-and-preparation environment only. Deployment artifacts must target a separate server where Docker is available.

## D. Existing services and ports

- No ORTA services running (no uvicorn, no postgres, no redis processes).
- No ports occupied by ORTA.
- Previous services (Core :8100, Bridge :8101, UI :3000) were stopped; not currently running.

## E. Python packages (user site)

Installed and importable: fastapi, uvicorn, sqlalchemy, requests, httpx, alembic, sqlite3.

## F. Constraints affecting preparation

1. No root/sudo → cannot install Docker daemon, PostgreSQL, Redis, or system packages.
2. No Docker daemon/compose → cannot containerize or run upstream services here.
3. User namespaces blocked → rootless Docker not possible.
4. 6.0 GiB free disk → limited; avoid large image pulls and duplicate copies.
5. No running services → integration tests requiring live Core/Bridge/UI must start them first.

## G. ORTA workspace layout

```
/home/coder/workspace/ORTA/
  core/          ORTA Intelligence Core (FastAPI + SQLAlchemy + Alembic)
  bridge/        ORTA Bridge (FastAPI, job worker, SearXNG/RAGFlow clients)
  ui/            ORTA Unified UI (FastAPI proxy + SPA static)
  tests/         acceptance.py (55 tests)
  storage/       orta.db, bridge.db (SQLite; REAL DATA - must preserve)
  docs/          15 documentation markdown files
  alembic/       migrations (single initial schema)
  scripts/       empty (deployment scripts to be added)
  config/        empty (config templates to be added)
  compose/       empty (compose files to be added)
  secrets/       empty (no secrets committed)
  pipeline/      empty
```

## H. Verified facts (not assumptions)

- Core, Bridge, and UI source files are present and importable.
- Alembic migration `902782639ec4_initial_schema` is the head; `alembic_version` table records it.
- SQLite databases contain real data (sources: 4, evidence: 3, entities: 1, investigations: 1, reports: 1, claims: 1, bridge_jobs: 2, normalized_content: 1).
- No deploy/ directory, no env templates, no healthchecks, no backup/restore scripts exist yet.
- No Docker Compose configuration exists yet.
