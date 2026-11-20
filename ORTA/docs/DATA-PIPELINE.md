# ORTA Data Pipeline

The ORTA data pipeline is a single automatic, persistent, recoverable flow:

```
Discovery (CROWler target / ORTA crawler + SearXNG)
  → ORTA Bridge (job, normalize, validate, deduplicate)
  → RAGFlow (target: upload, parse, index)
  → ORTA Core (sync evidence, entities, claims, provenance)
  → ORTA Unified UI (investigations, reports, evidence explorer)
```

Bridge service: `http://127.0.0.1:8101`. Core service: `http://127.0.0.1:8100`.

## 1. Pipeline stages

### Stage A — Discovery
Sources are discovered via configured providers (SearXNG JSON search, RSS, sitemaps, CommonCrawl — target-state). Each discovered URL becomes a `source_urls` record with a normalized URL and is registered in the source registry (`sources`).

Bridge endpoint: `POST /api/v1/discover` (creates a `discover` job calling SearXNG `GET /search?q=&format=json`).

### Stage B — Normalization & validation (Bridge)
URLs normalized (lowercase scheme/host, stripped tracking params, sorted kept query keys). Content validated (size cap 50MB, allowed content types, non-empty extractable text). Content hash (SHA-256) computed for dedupe.

Bridge endpoint: `POST /api/v1/normalize`. `NormalizedContent` table enforces unique `content_hash`.

### Stage C — Deduplication
Bridge and Core both deduplicate by `content_hash` (Bridge `NormalizedContent`; Core `Evidence`). Duplicate content is skipped — no duplicate evidence, no duplicate indexing.

### Stage D — Upload to RAGFlow (target)
Eligible documents uploaded to RAGFlow v1.0.0:
- `POST /api/v1/datasets/{dataset_id}/documents` (type=local, multipart `file`)
- `type=web` form fields `name`+`url` to crawl a URL into a document
- Supported file types: PDF, DOCX, TXT, HTML, images, etc. (version-dependent)
- Auth: `Authorization: Bearer <API_KEY>`

Bridge client: `RAGFlowClient.upload_document`. Unsupported file type (415) → permanent error → dead-letter.

### Stage E — Parse & index (target)
- `POST /api/v1/datasets/{dataset_id}/documents/parse` (StartIngestionTask)
- Poll status via `GET /api/v1/ingestion/tasks` or `GET /api/v1/datasets/{id}/documents` (`ingestion_status`: UNSTART/CREATED/SCHEDULED/RUNNING/COMPLETED/FAILED)
- Parse produces chunks; chunks indexed before retrieval

### Stage F — Core synchronization
On successful indexing, Bridge syncs to Core:
- `POST /api/v1/evidence` (evidence_id, original_url, content_hash, document_id=RAGFlow doc id, provenance, confidence)
- `POST /api/v1/claims` (statement, statement_type, evidence_id, confidence)
- `POST /api/v1/entities` (entity profiles, aliases)
- `POST /api/v1/entities/{id}/relationships`

Preserves: source provenance, RAGFlow document IDs, content hashes, source metadata, processing timestamps. Prevents duplicate evidence via content_hash idempotency.

## 2. Bridge job management

Job types: `discover`, `crawl`, `normalize`, `validate`, `upload`, `parse`, `index`, `sync`, `reconcile`.

Job lifecycle: `pending` → `running` → `completed`/`failed`/`dead_letter`. Persistent state in `bridge_jobs`. Retry with exponential backoff; dead-letter after `max_retries`. Idempotent by `job_id`.

Endpoints:
- `POST /api/v1/jobs` (create, idempotent)
- `GET /api/v1/jobs` (list)
- `GET /api/v1/jobs/{id}` (get)
- `PATCH /api/v1/jobs/{id}` (update status/result/error)
- `POST /api/v1/jobs/{id}/retry` (retry, increments retry_count)

Background worker polls pending jobs every 2s, runs them, records results/errors.

## 3. Recovery & reliability

The pipeline tolerates:
- Service restarts → job state persisted; reconcile reclaims stale `running` jobs back to `pending`
- Network failures → retry (transient) with backoff
- API timeouts → per-call timeout, retryable
- Invalid documents → validation, permanent → dead-letter
- Duplicate content → content-hash dedupe, skip
- Interrupted jobs → resume on restart
- Temporary provider failures → circuit breaker, alternate source

Dead-letter handling: jobs exceeding `max_retries` move to `dead_letter=true`, surfaced in UI Processing Jobs and System Health.

## 4. Idempotency

- Evidence: dedupe by `content_hash`
- Sources: idempotent by `source_id`
- Entities: idempotent by `entity_id`
- Claims: idempotent by `claim_id`
- Jobs: idempotent by `job_id`
- Re-upload to RAGFlow: keyed on `document_id` + `content_hash`

## 5. Contracts documented

Full route/auth/health contract summary in INTEGRATION-ARCHITECTURE.md §5 and UPSTREAM-RESEARCH.md. RAGFlow v1.0.0 endpoints verified from source (route table); auth login body and exact response shapes remain unverified until a live instance is available (see MODEL-SPEC-RESEARCH.md §3).

## 6. Integration tests

See `tests/acceptance.py` — runs against live Core (8100), Bridge (8101), and UI (3000) services. Upstream (SearXNG/RAGFlow/CROWler) integration is documented but not executable in this environment (no Docker/root — see RESOURCE-PLAN.md §1).
