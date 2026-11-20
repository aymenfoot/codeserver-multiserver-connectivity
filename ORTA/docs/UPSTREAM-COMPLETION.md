# ORTA Upstream Completion

Research and packaging status for the three upstream components.

## CROWler — UNRESOLVED

Extensive reinvestigation (2026-11-20) confirmed there is **no official verifiable CROWler discovery/crawling repository**:

- GitHub org `CROWler`: repos `CROWler`, `crowler`, `CROWLER` all return "Repository not found".
- Repository search for `"CROWler"`, `crowler`, `CROWLER`, `crowler crawler discovery`, `CROWler source discovery`: no general-purpose discovery/crawling/source-collection platform.
- Closest name matches are unrelated: `andeya/pholcus` (Go distributed crawler), `AhmedEmbaby1998/Crowler`, `moontai0724/fantia-downloader`, `lihn1987/t66y_crowler`, `LixinZhang/miniCrowler` (stale, 2013). None is a maintained CROWler platform.

**Decision:** CROWler is not replaced with an unrelated project (per mission rule). ORTA Bridge defines a clean adapter interface for future CROWler integration. Discovery in the deployment package is provided by SearXNG (verified official) plus the Bridge's normalize/validate/dedupe pipeline.

## SearXNG — VERIFIED

- Official repository: github.com/searxng/searxng
- Verified image: `searxng/searxng:2026.11.11-626105eec` (HEAD `368baa34...`)
- Config reference: verified stack at `/home/coder/workspace/searxng-ldr-stack/searxng/config/` (settings.yml with JSON format enabled; limiter.toml)
- Deployment: Docker Compose, internal network, `/healthz` health check, `SEARXNG_SECRET` required
- Packaged under `deploy/searxng/` and `deploy/compose/docker-compose.yml`

## RAGFlow — VERIFIED

- Official repository: github.com/infiniflow/ragflow
- Verified release: `v1.0.0` (2026-11-06, commit `db1cd592...`)
- Image: `infiniflow/ragflow:v1.0.0`
- Deployment: Docker Compose + MySQL + Valkey/Redis + Kvrocks + MinIO + Elasticsearch/Infinity + sandbox
- Auth: Bearer API token; `/api/v1/system/healthz` health check
- Packaged under `deploy/ragflow/` and `deploy/compose/docker-compose.yml`

## Bridge adapter readiness

The Bridge (`bridge/clients.py`) already contains:
- `SearXNGClient.search()` — JSON search, rate-limit (429) handling, error classification
- `RAGFlowClient` — login, create_dataset, upload_document, list_documents, document_status, start_ingestion, list_ingestion_tasks, retrieval, embed_text, rerank, health
- `CoreClient` — sync evidence/claims/entities/investigations/reports to Core

Remaining to wire into live jobs (Part 3):
- `discover` job → register discovered sources into Core source registry
- `upload` job → verify parsing/indexing completion (not just upload success)
- `sync` job → pull RAGFlow document_id/content_hash into Core evidence
