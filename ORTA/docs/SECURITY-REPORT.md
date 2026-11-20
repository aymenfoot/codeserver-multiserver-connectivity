# ORTA Security Report

Scope: ORTA Core, Bridge, Unified UI (live build-env services). Upstream (SearXNG/RAGFlow/CROWler) not deployed in build env.

## A. Secrets
- No credentials hardcoded in source or docs.
- Runtime config via environment variables (`ORTA_CORE_URL`, `ORTA_BRIDGE_URL`, `ORTA_SEARXNG_URL`, `ORTA_RAGFLOW_URL`, `ORTA_RAGFLOW_API_KEY`, `ORTA_DATABASE_URL`).
- Secrets intended for `ORTA/secrets/` (gitignored, empty).
- `deploy/env/env.example` contains only placeholder secrets (`REPLACE_ME`).
- API keys/tokens not logged. Bridge injects Bearer token at runtime from env.

## B. Authentication & authorization
- Core API: no auth middleware (dev build; Pydantic validation only).
- Bridge API: no auth middleware (dev build).
- UI: no login; bound to localhost only.
- **Gap:** authN/authZ not enforced — required before production.

## C. Network exposure
- All services bind to `127.0.0.1` only (build env).
- Compose publishes only to 127.0.0.1 (Core 8000, Bridge 8001, UI 3000, RAGFlow 9380/9381).
- No public exposure of databases or admin services.
- Reverse proxy recommended in front of UI in production.

## D. Database access
- SQLite files in `storage/` (filesystem permissions only, no network).
- Target: PostgreSQL on internal network, not published.

## E. API security
- Pydantic validation on all mutating endpoints.
- Idempotency keys prevent duplicate processing.
- SQLAlchemy ORM (no SQL injection surface).
- CORS `allow_origins=["*"]` — localhost dev; restrict in production.

## F. Dependency vulnerabilities
- Python deps: fastapi, uvicorn, sqlalchemy, alembic, requests, httpx, python-multipart. No vulnerability scan run (no root/audit tooling). Production: `pip audit` / `safety`.

## G. Container security
- No containers built/run in build env (Docker unavailable). N/A here.
- Compose uses `security_opt: no-new-privileges` on SearXNG (reference pattern).

## H. File handling
- Bridge caps document size (50MB) and content types; validation logic present (live upload not exercised — RAGFlow not deployed).
- Evidence stores raw/extracted text; no executable content served.

## I. Logging
- Uvicorn access logs (stdout). No request bodies/secrets logged intentionally.
- Bridge records job `error` text — review for credential leakage before production.

## J. Remediation before production
1. Add authentication (session/JWT) + authorization to Core and Bridge APIs.
2. Restrict CORS to trusted origins.
3. Run dependency vulnerability scan (`pip audit`).
4. Store secrets in `ORTA/secrets/` with restricted permissions; inject at runtime.
5. Audit job error logging for secret leakage.
6. Deploy upstreams behind internal network only; no public DB/admin exposure.
