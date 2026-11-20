# ORTA Integration Test Plan

Test categories and execution status. Services: Core (:8100), Bridge (:8101), UI (:3000). Upstream (SearXNG/RAGFlow) not available in build environment.

## 1. Passed against live services (55 tests — tests/acceptance.py)

| Area | Coverage | Result |
|------|----------|--------|
| Infrastructure deployment | Core, Bridge, UI start | pass |
| Service health | Core DB ok, Bridge core_reachable | pass |
| API connectivity | UI→Core proxy, UI→Bridge proxy | pass |
| Source registration | create, idempotent, get, list | pass |
| URL normalization | canonical form, content hash | pass |
| Bridge job creation | create, auto-process, result | pass |
| Retry / dead-letter | discover→SearXNG unreachable→retry→dead_letter→retry | pass |
| Evidence persistence | create, idempotent content-hash dedupe, get, list | pass |
| Entity extraction & resolution | create, idempotent, list | pass |
| Claim creation | source_fact type, list | pass |
| Investigation workflow | create, research question, get, list | pass |
| Report generation | create, cite evidence, get | pass |
| UI workflows | index loads, dashboard real counts, services present | pass |
| Storage persistence | DB file exists, sources persist | pass |

**Total: 55 passed, 0 failed.**

## 2. Contract tests (upstream not live — validated against verified route table)

| Contract | Verified against | Status |
|----------|------------------|--------|
| SearXNG `GET /search?q=&format=json` | docs/API-CONTRACTS-RESEARCH.md (source code) | contract |
| SearXNG `GET /healthz` → OK | docs/API-CONTRACTS-RESEARCH.md | contract |
| RAGFlow `POST /api/v1/datasets` | docs/MODEL-SPEC-RESEARCH.md §2 | contract |
| RAGFlow `POST /datasets/{id}/documents` (upload) | docs/MODEL-SPEC-RESEARCH.md §2 | contract |
| RAGFlow `POST /datasets/{id}/documents/parse` | docs/MODEL-SPEC-RESEARCH.md §2 | contract |
| RAGFlow ingestion status polling | docs/MODEL-SPEC-RESEARCH.md §2 | contract |
| RAGFlow `POST /api/v1/retrieval` | docs/MODEL-SPEC-RESEARCH.md §2 | contract |
| RAGFlow Bearer token auth | docs/MODEL-SPEC-RESEARCH.md §2.2 | contract |

Note: exact request/response bodies for login/upload/retrieval are **not live-verified** (no RAGFlow instance). Marked pending target-server execution.

## 3. Configuration / static validation

| Check | Method | Status |
|-------|--------|--------|
| Compose YAML valid | python yaml.safe_load | pass |
| No `latest` image tags | grep compose | pass |
| Bridge imports clean | python import | pass |
| Core imports clean | python import | pass |
| UI imports clean | python import | pass |
| Alembic migration valid | alembic upgrade head (SQLite) | pass |

## 4. Pending target-server execution (requires Docker + upstream services)

| Test | Reason |
|------|--------|
| Live SearXNG search + source registration | SearXNG not deployed (no Docker) |
| Live RAGFlow upload → parse → index → sync | RAGFlow not deployed (no Docker/RAM) |
| Live end-to-end discovery→ingest→index→evidence→investigation→report | Requires all upstreams |
| PostgreSQL migration (live DB) | PostgreSQL not installed |
| Backup/restore (real restore test) | Requires target server + isolated destination |
| Docker container health checks | Docker daemon unavailable |

## 5. Integration test execution commands

```
# Live services (build env):
cd /home/coder/workspace/ORTA
python3 tests/acceptance.py        # 55/55 pass against Core:8100, Bridge:8101, UI:3000

# Target server (after deploy):
bash deploy/scripts/verify-config.sh
bash deploy/scripts/deploy.sh
bash deploy/scripts/healthcheck.sh
python3 tests/acceptance.py  # re-run against deployed services (update URLs)
```
