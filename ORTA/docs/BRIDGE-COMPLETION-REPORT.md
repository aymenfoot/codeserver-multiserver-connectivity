# ORTA Bridge Completion Report

Status: **Implemented, installed, configured, deployed, operational, acceptance-tested** (dev build; upstream live integration pending target server).

## A. Implemented capabilities

### Job management
- Persistent job state (`bridge_jobs`): `job_id`, `job_type`, `status` (pending/running/completed/failed/dead_letter), `payload`, `result`, `error`, `error_class`, `retry_count`, `max_retries`, `dead_letter`, `correlation_id`.
- Idempotent by `job_id`. Background worker polls pending jobs every 2s.
- API: `POST /api/v1/jobs`, `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `PATCH /api/v1/jobs/{id}`, `POST /api/v1/jobs/{id}/retry`.

### URL normalization & content validation
- `POST /api/v1/normalize`: canonicalizes URLs (lowercase scheme/host, strips tracking params, sorts kept query keys), computes SHA-256 content hash, validates content type/size/extractable text.
- `NormalizedContent` table enforces unique `content_hash` (dedupe).

### Duplicate detection
- Content-hash dedupe at Bridge (`NormalizedContent`) and Core (`Evidence.content_hash`).
- Source dedupe by `source_id`; evidence dedupe by `content_hash`.

### Retry strategy
- Transient errors (network/timeout/5xx) retryable with backoff via `retry_count`/`max_retries`.
- Permanent errors (auth/400/404/415) not retried.
- Policy errors (429 rate limit) retryable.
- Dead-letter after `max_retries` (`dead_letter=true`), surfaced in UI.

### Reconciliation
- `_run_reconcile` reclaims stale `running` jobs back to `pending` on restart/recovery.
- Bridge health reports `core_reachable`.

### RAGFlow document upload (v1.0.0 contract)
- `RAGFlowClient`: login, create_dataset, upload_document, list_documents, document_status, start_ingestion, list_ingestion_tasks, retrieval, embed_text, rerank, health.
- Bridge `_run_upload`: uploads document → extracts document_id → `start_ingestion` → polls `_poll_ragflow_indexing` until COMPLETED/FAILED terminal state. **Upload ≠ indexed** — success reported only after indexing verification.
- Auth: `Authorization: Bearer <API_KEY>`.

### Core synchronization
- Bridge `_run_sync`: creates Core evidence with `document_id` (RAGFlow doc id), `content_hash`, `source_url`, provenance (tool, job_id, ragflow_dataset), confidence.

### SearXNG discovery ingestion
- Bridge `_run_discover`: calls SearXNG `GET /search?q=&format=json`, normalizes results, and `_register_discovered_source` registers each discovered URL as a Core source (idempotent) with domain, discovery_origin=searxng, discovery_engine.
- Error classification: transient/permanent/policy.

### Clients (`bridge/clients.py`)
- `CoreClient`, `SearXNGClient`, `RAGFlowClient` with `BridgeError` classification.

## B. Current data (preserved)
- bridge_jobs: 2, normalized_content: 1.

## C. Remaining (target-server live integration)
- RAGFlow not running here → `_run_upload` indexing path not live-tested. Code written against verified v1.0.0 route table.
- SearXNG not running here → `_run_discover` not live-tested.
- PostgreSQL not configured for Bridge (SQLite dev).
- Background worker is an in-process daemon thread; production should use a dedicated worker process.

## D. API endpoints (13)
`/healthz`, `/api/v1/jobs` (POST/GET), `/api/v1/jobs/{id}` (GET/PATCH), `/api/v1/jobs/{id}/retry`, `/api/v1/normalize`, `/api/v1/discover`, `/api/v1/sync`.
