# ORTA Core Completion Report

Status: **Implemented, installed, configured, deployed, operational, acceptance-tested** (dev build; PostgreSQL target prepared).

## A. Implemented capabilities

### Evidence management
- Evidence records with: `evidence_id`, `original_url`, `source_id`, `source_url_id`, `document_id` (RAGFlow doc id), `content_hash` (SHA-256), `collection_timestamp`, `publication_timestamp`, `provenance` JSON, `confidence`, `verification_metadata`, `relationships`, `raw_content`, `extracted_text`.
- Idempotent by `content_hash` — no duplicate evidence records.
- API: `POST /api/v1/evidence`, `GET /api/v1/evidence`, `GET /api/v1/evidence/{id}`, `GET /api/v1/evidence/{id}/claims`.

### Entity intelligence
- Entity profiles: `entity_id`, `name`, `entity_type`, `canonical_name`, `resolved_to_id` (entity resolution cluster), `identity_confidence`, `alias_management`, `historical_changes`, `profile`, `duplicate_group_id`.
- Entity mentions link entities to evidence (`entity_mentions`, offset/confidence).
- Entity relationships (`entity_relationships`) with type, confidence, supporting evidence ids.
- **No automatic merge of ambiguous identities** — `resolved_to_id` set only when evidence/confidence support it.
- API: `POST /api/v1/entities`, `GET /api/v1/entities`, `GET /api/v1/entities/{id}`, `POST /api/v1/entities/{id}/relationships`.

### Claims intelligence
- Claims: `claim_id`, `statement`, `statement_type` (`source_fact` | `model_interpretation` | `inference` | `hypothesis`), `evidence_id`, `confidence`, `temporal_valid_from/to`, `contradicted_by_claim_id`.
- Source facts distinguishable from model interpretations/inferences/hypotheses via `statement_type`.
- Contradiction handling via `contradicted_by_claim_id`.
- API: `POST /api/v1/claims`, `GET /api/v1/claims`, `GET /api/v1/claims/{id}`.

### Investigation engine
- Investigations: `investigation_id`, `title`, `research_question`, `status`, `findings`, `unanswered_questions`.
- Research sub-questions (`research_questions`: open/answered/unanswered, answer, confidence).
- Investigation sources link to evidence (`investigation_sources`, relevance).
- Reports belong to investigations.
- API: `POST /api/v1/investigations`, `GET /api/v1/investigations`, `GET /api/v1/investigations/{id}`, `POST /api/v1/investigations/{id}/questions`.

### Reporting
- Traceable reports: `report_id`, `investigation_id`, `title`, `content`, `findings`, `sources`, `evidence_ids`, `entity_ids`, `claim_ids`, `contradictions`, `confidence_limitations`, `investigation_history`.
- API: `POST /api/v1/reports?investigation_id=<n>`, `GET /api/v1/reports/{id}`.

### Source registry
- Sources: `source_id`, `source_type`, `domain`, `language`, `category`, `discovery_origin`, `access_method`, `crawl_policy`, `reliability`, `update_frequency`, `content_volume`, `error_history`, `is_active`.
- Source URLs tracked separately (`source_urls`, normalized_url + content_hash dedupe).
- Idempotent by `source_id`.
- API: `POST /api/v1/sources`, `GET /api/v1/sources`, `GET /api/v1/sources/{id}`, `PATCH /api/v1/sources/{id}`.

### Job tracking
- Jobs: `job_id`, `job_type`, `status`, `payload`, `result`, `error`, `error_class`, `retry_count`, `max_retries`, `dead_letter`, `correlation_id`, timestamps.
- Idempotent by `job_id`. Retry/dead-letter via `PATCH /api/v1/jobs/{id}/status` and `POST /api/v1/jobs/{id}/retry`.
- API: `POST /api/v1/jobs`, `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `PATCH /api/v1/jobs/{id}/status`, `POST /api/v1/jobs/{id}/retry`.

### Provenance & audit
- Every evidence record carries `provenance` (collector, method, tool, job id) and `content_hash`.
- Claims cite `evidence_id`. Entities cite evidence via `entity_mentions`. Reports cite evidence/entity/claim ids.
- Health: `GET /healthz` (database connectivity).

## B. Engineering
- SQLAlchemy models (`core/models.py`), Alembic migration `902782639ec4_initial_schema` (head).
- Pydantic schemas (`core/schemas.py`) for API validation.
- Transactional integrity via SQLAlchemy sessions.
- FastAPI app (`core/main.py`), 31 endpoints.
- SQLite dev database (`storage/orta.db`); PostgreSQL target configured via `ORTA_DATABASE_URL`.
- Alembic `alembic upgrade head` for deterministic migrations.

## C. Current data (preserved)
- sources: 4, evidence: 3, entities: 1, investigations: 1, reports: 1, claims: 1, research_questions: 1.

## D. Remaining (production)
- Authentication/authorization not enforced on Core API (dev build).
- PostgreSQL migration script prepared (`deploy/scripts/migrate.sh`); live PostgreSQL test pending target server.
- `ORTA_DATABASE_URL` supports PostgreSQL; SQLite only for dev/tests.
