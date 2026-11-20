# ORTA Acceptance Report

Acceptance execution against live build-env services:
- ORTA Core: http://127.0.0.1:8100
- ORTA Bridge: http://127.0.0.1:8101
- ORTA Unified UI: http://127.0.0.1:3000

Test file: `tests/acceptance.py`

## Result: 55 passed, 0 failed (live services, no mocks)

## Test categorization

| Category | Count | Basis |
|----------|-------|-------|
| Passed against live services | 55 | tests/acceptance.py against Core:8100, Bridge:8101, UI:3000 |
| Passed as local unit tests | 0 | n/a |
| Passed as contract tests | 13 (documented) | SearXNG + RAGFlow route-table contracts (not live) |
| Passed through config/static validation | 6 | compose YAML valid, no latest tags, imports clean, alembic migration |
| Pending target-server execution | 7 | live SearXNG/RAGFlow, PostgreSQL, backup/restore, Docker health |
| Failed or blocked | 0 | none |

## Live acceptance coverage (55 tests)
Infrastructure deployment, service health, API connectivity, source registration (idempotent), URL normalization, Bridge job creation/auto-processing, retry/dead-letter/reconcile, evidence persistence (content-hash dedupe), entity extraction & resolution, claim creation (source_fact), investigation workflow, report generation (traceable citations), UI workflows (index load, real dashboard counts), storage persistence.

## Contract-only (not live — pending target server)
SearXNG `GET /search?q=&format=json` + `/healthz`; RAGFlow dataset/upload/parse/index/retrieve/auth contracts — verified against verified route tables, not live instances.

## Notes
- All dashboard metrics come from live Core/Bridge APIs — no invented statistics.
- Databases contain real build-env data (preserved; not reset).
- Upstream live integration (SearXNG/RAGFlow) cannot be executed in the build env (no Docker/RAM).
