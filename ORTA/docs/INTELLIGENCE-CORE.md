# ORTA Intelligence Core

The ORTA Intelligence Core is the central custom intellectual component of the ORTA platform. It owns the intelligence data model and workflows — it does not merely wrap RAGFlow or expose its APIs through another interface. Every important assertion is traceable to supporting evidence.

Status: **Implemented, installed, configured, deployed, and operational** (native Python service on this environment; target DB PostgreSQL, here SQLite due to no-root/no-Docker constraints — see RESOURCE-PLAN.md).

Service: `ORTA Core` — `http://127.0.0.1:8100` (dev), target `8000` internal.
API base: `/api/v1/`. Health: `GET /healthz`.
Stack: Python 3.14, FastAPI, SQLAlchemy, Alembic (migrations), SQLite (dev) / PostgreSQL (target).

## 1. Evidence management

Every evidence record captures:
- Stable `evidence_id`
- Original source URL (`original_url`)
- Source identifier (`source_id`) and source URL (`source_url_id`)
- Content hash (`content_hash`, SHA-256) for dedupe and integrity
- Document identifier (`document_id`, e.g. RAGFlow document id once indexed)
- Collection timestamp (`collection_timestamp`)
- Publication timestamp (`publication_timestamp`, where available)
- Provenance (`provenance` JSON: collector, method, tool, job id)
- Confidence (`confidence`: low/medium/high/verified)
- Verification metadata (`verification_metadata` JSON)
- Evidence relationships (`relationships` JSON: related evidence ids)
- Raw content and extracted text

API: `POST /api/v1/evidence`, `GET /api/v1/evidence`, `GET /api/v1/evidence/{id}`.
Idempotency: evidence is deduplicated by `content_hash` (within a source URL, then globally) — no duplicate evidence records.

## 2. Entity intelligence

Entities model:
- Stable `entity_id`, `name`, `entity_type` (person/organization/location/other)
- `canonical_name` after resolution
- `resolved_to_id` pointing to a canonical cluster (entity resolution)
- `identity_confidence` (low/medium/high)
- `alias_management` JSON (known aliases)
- `historical_changes` JSON
- `profile` JSON
- `duplicate_group_id` for potential-duplicate clusters

Entity mentions link entities to the evidence they were extracted from (`entity_mentions`, with offset and confidence).
Entity relationships (`entity_relationships`) link source→target entities with a type, confidence, and supporting evidence ids.

Rule: ambiguous identities are never automatically merged without sufficient evidence — resolution sets `resolved_to_id` only when confidence and evidence support it.

API: `POST /api/v1/entities`, `GET /api/v1/entities`, `GET /api/v1/entities/{id}`, `POST /api/v1/entities/{id}/relationships`.

## 3. Claims intelligence

Claims model:
- Stable `claim_id`
- `statement` text
- `statement_type`: `source_fact` | `model_interpretation` | `inference` | `hypothesis` — original source statements are distinguishable from model-generated interpretations
- `evidence_id` linking to supporting evidence
- `confidence`
- `temporal_valid_from` / `temporal_valid_to` (temporal changes)
- `contradicted_by_claim_id` (claim relationships / contradiction handling)

API: `POST /api/v1/claims`, `GET /api/v1/claims`, `GET /api/v1/claims/{id}`.
Each claim's `statement_type` keeps source facts separate from model interpretations/inferences/hypotheses, with citations via `evidence_id`.

## 4. Investigation engine

Investigations:
- Stable `investigation_id`, `title`, `research_question`
- `status`: active / paused / completed / archived
- `findings` JSON (structured findings)
- `unanswered_questions` JSON array

Research questions belong to an investigation (`research_questions`, open/answered/unanswered, answer, confidence).
Investigation sources link investigations to evidence (`investigation_sources`, with relevance).
Reports belong to investigations.

Workflow: user creates an investigation from a question/topic → system breaks into research questions → sources discovered → evidence collected → entities/claims identified → findings produced → unanswered questions tracked.

API: `POST /api/v1/investigations`, `GET /api/v1/investigations`, `GET /api/v1/investigations/{id}`, `POST /api/v1/investigations/{id}/questions`.

## 5. Reporting

Reports:
- Stable `report_id`, linked `investigation_id`, `title`, `content`
- `findings`, `sources`, `evidence_ids`, `entity_ids`, `claim_ids`, `contradictions`
- `confidence_limitations`
- `investigation_history`

Reports are traceable: every finding cites evidence ids, entity ids, claim ids, and source references.

API: `POST /api/v1/reports?investigation_id=<n>`, `GET /api/v1/reports/{id}`.

## 6. Jobs

Persistent job state (`jobs` table): `job_id`, `job_type` (crawl/normalize/upload/parse/index/sync/reconcile), `status` (pending/running/completed/failed/dead_letter), `payload`, `result`, `error`, `retry_count`, `max_retries`, `dead_letter`, `correlation_id`, timestamps.

API: `POST /api/v1/jobs`, `GET /api/v1/jobs`, `GET /api/v1/jobs/{id}`, `PATCH /api/v1/jobs/{id}/status`, `POST /api/v1/jobs/{id}/retry`.
Idempotent by `job_id`. Retry with dead-letter after `max_retries`.

## 7. Source registry (lightweight, Core-owned)

Sources table: `source_id`, `source_type`, `domain`, `language`, `category`, `discovery_origin`, `access_method`, `crawl_policy` JSON, `reliability` (0..1), `update_frequency`, `content_volume`, `error_history` JSON, `is_active`, timestamps. Source URLs are tracked separately (`source_urls`, with normalized_url + content_hash dedupe).

API: `POST /api/v1/sources` (idempotent by `source_id`), `GET /api/v1/sources`, `GET /api/v1/sources/{id}`, `PATCH /api/v1/sources/{id}`.

## 8. Engineering

- Database migrations via Alembic (`alembic/` directory, `alembic.ini`, `alembic upgrade head`).
- Stable schemas (see `core/models.py`).
- Transactional integrity via SQLAlchemy sessions.
- Idempotency on evidence (content_hash), sources (source_id), entities (entity_id), claims (claim_id), investigations (investigation_id), reports (report_id), jobs (job_id).
- API validation via Pydantic schemas (`core/schemas.py`).
- No fake data: the DB starts empty; all records are created through the API.
- Health check: `GET /healthz` returns database connectivity.

## 9. Running

```
cd /home/coder/workspace/ORTA/core
export ORTA_DATABASE_URL="sqlite:////home/coder/workspace/ORTA/storage/orta.db"
python3 -m alembic upgrade head
python3 -m uvicorn main:app --host 127.0.0.1 --port 8100
```

Endpoints are validated with Pydantic; all mutations are idempotent; every assertion references evidence via foreign keys and content hashes.
