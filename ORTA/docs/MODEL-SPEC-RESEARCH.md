# ORTA Model-Spec Research: RAGFlow v1.0.0 API & Model/Embedding Integration

**Status:** Research / specification only. No infrastructure deployed or duplicated.
**Environment constraint:** No Docker, no root, no user namespaces. RAGFlow v1.0.0 is Docker-native only (official `infiniflow/ragflow:v1.0.0` image, Docker Compose, MySQL + Valkey + Kvrocks + MinIO + Elasticsearch/Infinity + sandbox). It CANNOT be container-deployed here. All findings below are desk research against live upstream sources; nothing has been exercised against a live RAGFlow instance.

## 1. Sources consulted (all live, 2026-11-20)

| Source | What it established |
|--------|---------------------|
| https://github.com/infiniflow/ragflow (tag `v1.0.0`, commit `db1cd5929a7885a3074547791f5ecc4d2f891739`) | Go API route table (`internal/router/router.go`), auth middleware, document/dataset/chunk/retrieval/command handlers, document statuses, response envelope |
| https://github.com/infiniflow/ragflow/sdk/python/ragflow_sdk (tag `v1.0.0`) | Official Python SDK client: `RAGFlow(api_key, base_url)`, `Authorization: Bearer <key>`, `create_dataset`, `retrieve`, dataset/document/chunk methods |
| https://ragflow.io/docs/dev/ (Quickstart, README) | Deployment prereqs (Docker ≥ 24, Compose ≥ v2.26.1, 4 CPU / 16 GB RAM / 50 GB), health `GET /api/v1/system/healthz`, model provider configuration (chat + embedding + reranker, API key + base URL, verify models, set default models), file types, 10-minute tutorial flow (configure models → create dataset → upload → parse → chat) |
| https://github.com/infiniflow/ragflow/releases (tag `v1.0.0`, published 2026-11-06) | Version pin confirmed |
| ORTA foundation docs (not modified): ARCHITECTURE.md, IMPLEMENTATION-PLAN.md, RESOURCE-PLAN.md, UPSTREAM-RESEARCH.md | Port 9380 Go API / 9381 Admin / 80 HTTP; Bridge→RAGFlow contract; Phase 4 model infra; Phase 6 blocked |

## 2. RAGFlow v1.0.0 REST API — verified facts

### 2.1 Base URL, ports, auth

- REST base: `http://<host>/api/v1`. Docs reference both port 80 (HTTP web) and 9380 (Go API); admin on 9381. ORTA ARCHITECTURE.md pins `http://<ragflow>:9380/api/v1/`.
- Auth scheme: **Bearer API token**, `Authorization: Bearer <api_key>`.
- Token acquisition (version-specific, v1.0.0):
  - `POST /api/v1/auth/login` (no-auth route, `userHandler.LoginByEmail`) — email/password login; **exact request/response body not verified from source** (handler body not read).
  - Configured API key: create/list/delete via `GET/POST/DELETE /api/v1/system/tokens` (protected; `systemHandler.ListAPIKeys`/`CreateKey`/`DeleteKey`). Aliased under `/api/v1/system/keys`.
  - No-auth endpoints: `GET /api/v1/system/ping`, `/system/config`, `/system/version`, `/system/healthz`, `/language`, `/auth/login`, `/users` (register).
- Protected routes require `AuthMiddleware`; rejects missing/invalid token with 401 `Invalid access token`. Superusers blocked from tenant API surface.
- Response envelope (SDK convention, verified in `ragflow.py`): `{"code": int, "message": str, "data": ...}`; success when `code == 0`.

### 2.2 Dataset CRUD (verified routes)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET | `/api/v1/datasets` | `ListDatasets` | query: page, page_size, orderby, desc, id, ids, name |
| POST | `/api/v1/datasets` | `CreateDataset` | body: name, parse_type, permission, parser_id\|pipeline_id, embedding_model, parser_config, language, pipeline_version_id |
| GET | `/api/v1/datasets/:dataset_id` | `GetDataset` | |
| PUT | `/api/v1/datasets/:dataset_id` | `UpdateDataset` | |
| DELETE | `/api/v1/datasets` | `DeleteDatasets` | body: {ids, delete_all} |

CreateDataset parse modes (SDK `create_dataset`): `parse_type=1` BuiltIn (parser_id defaults `"general"`); `parse_type=2` Pipeline (requires `pipeline_id` + pinned `pipeline_version_id`). A dataset binds exactly one embedding model (`embedding_model`) — this is the model used to vectorize its documents at index time.

### 2.3 Document upload (verified routes)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| POST | `/api/v1/documents/upload` | `UploadInfo` | multipart file |
| POST | `/api/v1/datasets/:dataset_id/documents` | `UploadDocuments` | `type=local\|web\|empty` |
| GET | `/api/v1/datasets/:dataset_id/documents` | `ListDocuments` | query: page, orderby, desc, keywords, name, id, ids, suffixes, types, run_status, create_time_from/to, metadata |
| GET | `/api/v1/datasets/:dataset_id/documents/:document_id` | `DownloadDocument` / `GetDocumentByID` | |
| PATCH | `/api/v1/datasets/:dataset_id/documents/:document_id` | `UpdateDatasetDocument` | |
| DELETE | `/api/v1/datasets/:dataset_id/documents` | `DeleteDocuments` | body: {ids} or {delete_all} |

Upload modes: `local` = multipart `file` field(s); `web` = form fields `name` + `url` (http/https); `empty` = JSON `{name}`. Filename ≤ 255 chars. Optional `parser_config` override (allow-listed keys `table_column_mode`, `table_column_roles`). Response maps raw keys to public shape: `id, name, type, size, suffix, source_type, created_by, parser_config, location, pipeline_id, content_hash, chunk_count (chunk_num), token_count (token_num), dataset_id (kb_id), parser_id, ingestion_status`.

### 2.4 Supported file types (verified from README/Quickstart)

Word documents, PowerPoint presentations, Excel spreadsheets, TXT files, Markdown, images, PDFs (incl. scanned copies), structured data, web pages. Quickstart tutorial uses TXT / Markdown / text-based PDF. **Exact extension list and per-type limits not verified from source** (version-dependent, treat as indicative).

### 2.5 Parse + index + status polling (verified routes)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| POST | `/api/v1/datasets/:dataset_id/documents/parse` | `StartIngestionTask` | body: {document_ids: [...]}, requires OperationRun on dataset |
| POST | `/api/v1/datasets/:dataset_id/documents/stop` | `StopParseDocuments` | |
| GET | `/api/v1/ingestion/tasks` | `ListIngestionTasks` | body: {dataset_id}; lists ingestion tasks with status |
| PUT | `/api/v1/ingestion/tasks` | `StopIngestionTasks` | |
| DELETE | `/api/v1/ingestion/tasks` | `RemoveIngestionTasks` | |
| POST | `/api/v1/documents/ingest` | `Ingest` | single-document ingest |

Document ingestion statuses (verified `runStatusMap`): `UNSTART, CREATED, SCHEDULED, RUNNING, STOPPING, STOPPED, COMPLETED, FAILED`. Poll `ListIngestionTasks` (or `ListDocuments` which returns `ingestion_status` + `progress`/`progress_msg` + `latest_ingestion_event`) until `COMPLETED` or `FAILED`. Parse converts a document into chunks; a document must have chunks before retrieval.

### 2.6 Retrieval endpoint (verified routes)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| POST | `/api/v1/retrieval` | `SearchDatasets` | body below |
| POST | `/api/v1/datasets/:dataset_id/search` | `SearchDataset` | per-dataset retrieval |

`POST /api/v1/retrieval` body (verified from SDK `retrieve`):
- `question` (str), `dataset_ids` (list), `document_ids` (list, optional)
- `page`, `page_size`, `similarity_threshold` (default 0.2), `vector_similarity_weight` (default 0.3), `top_k` (default 1024)
- `rerank_id` (optional), `keyword` (bool), `cross_languages` (list), `metadata_condition` (dict), `use_kg` (bool)
- Returns `data.chunks` (list of chunk objects) on `code == 0`.

Retrieval uses the dataset's bound embedding model to embed the query, then vector similarity over the dataset's chunks. Reranking is optional via `rerank_id`.

### 2.7 Document IDs

- Documents carry a server-generated `id` (UUID-like), returned on upload (`POST /datasets/:dataset_id/documents`) and listed via `ListDocuments` (`docs[].id`). The `content_hash` field supports dedup. ORTA must persist `document_id` + `dataset_id` + `content_hash` to enable idempotent re-upload and status sync.

### 2.8 Providers / models / embeddings / rerank (verified routes)

| Method | Path | Handler | Notes |
|--------|------|---------|-------|
| GET/POST | `/api/v1/providers` | `ListProviders` / `AddProvider` | provider pool |
| GET/PUT/DELETE | `/api/v1/providers/:id` | `ShowProvider` / `AlterProviderInstance` / `DeleteProvider` | |
| GET | `/api/v1/providers/:id/models` | `ListModels` | |
| POST | `/api/v1/command/chat/to-model` | `ChatToModel` | LLM completion |
| POST | `/api/v1/command/embeddings` | `EmbedText` | embedding |
| POST | `/api/v1/command/rerank` | `RerankDocument` | reranking |
| GET | `/api/v1/models` | `ListModelsForUserInTenant` | user's models in tenant |
| PATCH | `/api/v1/models/default` | `SetDefaultModels` | tenant default chat/embedding |

RAGFlow configures chat model + embedding model (+ reranker) per provider instance (API key + base URL), verifies them, and sets tenant default models. Embedding model is bound to a dataset at creation and used consistently for indexing and query embedding at retrieval time.

## 3. What remains UNVERIFIED (no live instance available)

Because RAGFlow cannot be deployed here (no Docker/root), the following are **not** confirmed against a running v1.0.0 server and must be treated as hypotheses pending Phase 6/7 deployment:

- Exact `POST /api/v1/auth/login` request body (email/password field names) and response field carrying the Bearer token.
- Exact `CreateDataset` / `UploadDocuments` response field names and `data` shape beyond the SDK-mapped fields above.
- Exact `POST /api/v1/retrieval` response chunk object structure (fields per chunk).
- Exact `POST /api/v1/command/embeddings` and `/command/rerank` request/response schemas.
- Default HTTP port (80 vs 9380) behavior and whether both serve `/api/v1`.
- Complete supported file extension list and max file size.
- Per-provider credential fields (API key vs base URL vs model name) for each provider type.
- Chunk size / parsing modes beyond `general` BuiltIn and pipeline parse_type.
- Health endpoint uptime semantics (`/api/v1/system/healthz` returns 200 when ready).

**Any ORTA Bridge client code written now must be written against the verified route table above and re-validated against a live instance before production use.** Functions that depend on unverified request/response bodies remain unverified.

## 4. Model provider abstraction design for ORTA

ORTA Phase 4 (IMPLEMENTATION-PLAN.md) requires: embedding provider abstraction, LLM provider abstraction, optional reranking (quality-verified), secure credentials, no invented credentials, preserve working local embedding services. RAGFlow is the target-state upstream document index/retrieval; ORTA's model layer is ORTA-owned and configurable, not a fork of RAGFlow's model UI.

### 4.1 Design principles (from ARCHITECTURE.md guiding principles)

- Every assertion traceable to supporting evidence; no invented credentials; versions pinned.
- Use existing upstream capabilities before building replacements — RAGFlow owns document parse/index/retrieve; ORTA owns the model-abstraction layer that drives LLM/embedding calls for intelligence tasks.
- Internal databases/admin services never publicly exposed; credentials in `ORTA/secrets/` (gitignored), never in logs/images.

### 4.2 Embedding provider abstraction

| Capability | Requirement | RAGFlow mapping |
|------------|-------------|-----------------|
| Identity | provider name + instance id + model name | RAGFlow provider instance; dataset-bound `embedding_model` |
| Dimensions | exposed per model (e.g. 1536 / 1024 / 768); ORTA stores with vector | not exposed by verified routes — to be discovered at deployment |
| Input compatibility | text input; batch size limits; token limits | `POST /api/v1/command/embeddings` (EmbedText) — schema unverified |
| Batch | multi-text embedding in one call | `EmbedText` — schema unverified |
| Vector indexing/retrieval | RAGFlow indexes dataset chunks; ORTA queries via `/api/v1/retrieval` | `POST /api/v1/retrieval` (embeds query internally with dataset's model) |
| Consistent model indexing vs querying | Same embedding model must be used to embed documents at index time and queries at query time | Enforced by binding `embedding_model` to the dataset; ORTA must record and reuse the same model id for query embedding if ORTA does its own embedding |

**ORTA design:** an `EmbeddingProvider` interface with `EmbedTexts([]string) ([][]float32, error)` and `Dimensions() int`, `ModelID() string`. Implementations: (a) RAGFlow-backed via `/api/v1/command/embeddings`, (b) local fallback (preserve any working local embedding service, e.g. sentence-transformers / ONNX runtime) for offline/dev. Configuration selects provider + model + base URL + credentials from secrets. ORTA records `dataset_id` + `embedding_model_id` used at index time and requires the same model id for query-time embedding to avoid cross-model vector mismatch.

### 4.3 LLM provider abstraction

| Capability | Requirement | RAGFlow mapping |
|------------|-------------|-----------------|
| Content understanding | chat/completion over retrieved context | `POST /api/v1/command/chat/to-model` (ChatToModel); RAGFlow chat `/api/v1/chat/completions` |
| Entity extraction | structured entity recognition | LLM prompt-driven via ChatToModel |
| Claim extraction | claim + supporting evidence extraction | LLM prompt-driven via ChatToModel |
| Classification | document/source classification | LLM prompt-driven via ChatToModel |
| Summarization | document/source summarization | LLM prompt-driven via ChatToModel |
| Investigation planning | multi-step question decomposition | Agentic RAG (`internal/agentic_rag`, Low/Medium/High/Ultra modes) — ORTA-side orchestration |
| Evidence analysis | cite-backed reasoning over chunks | RAGFlow `/api/v1/retrieval` + citations (`Show citations`) |
| Report generation | traceable report assembly | ORTA-side, grounded in retrieved chunks + citations |

**ORTA design:** an `LLMProvider` interface with `Complete(messages, options) (string, error)` and structured variants (`ExtractEntities`, `ExtractClaims`, `Classify`, `Summarize`, `PlanInvestigation`, `AnalyzeEvidence`, `GenerateReport`) built on top of `Complete` with JSON-schema prompting. Implementations: RAGFlow-backed (`/api/v1/command/chat/to-model`) and any configured OpenAI-compatible endpoint. Credentials: provider API key + base URL from secrets; never hardcoded; never invented.

### 4.4 Reranking (quality-gated)

RAGFlow supports `rerank_id` in `/api/v1/retrieval` and a `POST /api/v1/command/rerank` (RerankDocument) route. Per ARCHITECTURE.md / IMPLEMENTATION-PLAN.md: reranking enabled **only after retrieval-quality verification**. ORTA design: a `RerankerProvider` interface (`Rerank(query, candidates) (reranked, error)`), disabled by default, enabled only after an evaluation run demonstrates relevance improvement (see INTELLIGENCE-EVALUATION.md, Phase 4).

### 4.5 Secure credential handling

- Credentials (API keys, base URLs, model names) live in `ORTA/secrets/` (gitignored), never in logs, images, or source.
- ORTA never invents credentials; if external credentials are unavailable, the affected functions are reported as unverified and fall back to local/offline paths where possible.
- RAGFlow API token is an ORTA-managed secret (obtained via `/api/v1/auth/login` or pre-configured API key), stored in secrets, injected at runtime into the Bridge client.
- Access tokens vs API tokens: RAGFlow `AuthMiddleware` resolves user access tokens or API tokens; API keys are a paid capability (Trial tenants blocked). ORTA should use a dedicated service API token for Bridge→RAGFlow.

### 4.6 Preserve working local embedding services

Any existing local embedding service (e.g. local sentence-transformers/ONNX model used for ORTA-side vector work) is preserved as the default/fallback provider. RAGFlow integration is additive: ORTA uses RAGFlow for document parse/index/retrieve, and may use RAGFlow's embedding command or keep its local embedding service depending on configuration. Do not remove or replace working local services to force RAGFlow adoption.

### 4.7 Mapping: ORTA capability → RAGFlow API (for the Bridge client, Phase 2)

| ORTA Bridge responsibility | RAGFlow v1.0.0 endpoint | Verified? |
|----------------------------|-------------------------|-----------|
| Obtain service token | `POST /api/v1/auth/login` or pre-configured API key | Route verified; body unverified |
| Create dataset (bind embedding model) | `POST /api/v1/datasets` | Yes |
| Upload document | `POST /datasets/:dataset_id/documents` (multipart) | Yes |
| Start parse/index | `POST /datasets/:dataset_id/documents/parse` | Yes |
| Poll status | `GET /ingestion.tasks` or `GET /datasets/:id/documents` | Yes |
| Retrieve chunks | `POST /api/v1/retrieval` | Yes |
| Read document/chunk | `GET /documents/:id`, `GET /datasets/:id/documents/:doc/chunks` | Yes |
| List/delete documents | `GET/DELETE /datasets/:id/documents` | Yes |
| Embed text (ORTA-side) | `POST /api/v1/command/embeddings` | Route verified; schema unverified |
| Rerank | `POST /api/v1/command/rerank` | Route verified; schema unverified |
| Health | `GET /api/v1/system/healthz` | Yes |

## 5. Analytical integrity

ORTA's analytical integrity requirement (ARCHITECTURE.md guiding principle 4): every assertion traceable to supporting evidence. Applied to RAGFlow-derived content, classify every statement into one of five tiers and maintain citations/provenance:

| Tier | Definition | Provenance requirement |
|------|------------|------------------------|
| Source fact | Verbatim/near-verbatim content from an ingested source document | Source URL + document ID + chunk ID + byte/offset range |
| Extracted statement | Statement produced by an extraction model (entity, claim) from source text | Model id + prompt version + source chunk(s) + confidence |
| Model interpretation | Model-generated synthesis/summary/reasoning over retrieved chunks | Model id + retrieved chunk IDs + retrieval query + rerank id (if used) |
| Inference | Conclusion drawn by combining multiple extracted statements | All input statement IDs + inference rule/chain + confidence |
| Unverified hypothesis | Assertion not yet backed by source or model evidence | Flagged; requires investigation task; not surfaced as fact |

Citations/provenance: RAGFlow returns chunks with document context; ORTA must persist `document_id`, `chunk_id`, `dataset_id`, retrieval query, similarity score, model id, and prompt version for every extracted/interpreted statement. Reports must cite chunk-level sources with links back to the source document. ORTA Core (PostgreSQL) is the system of record for evidence, entities, claims, investigations, reports, and provenance (ARCHITECTURE.md §5, §6).

## 6. Implementation notes for ORTA

- Write the Bridge RAGFlow REST client now (Phase 2) against the verified route table; mark it "live integration when RAGFlow available" (IMPLEMENTATION-PLAN.md §2).
- Do not deploy or duplicate RAGFlow infrastructure here (Phase 6 blocked, RESOURCE-PLAN.md §1, §3). Target-state compose files go in `ORTA/compose/` only.
- Pin `RAGFLOW_VERSION=v1.0.0`, image `infiniflow/ragflow:v1.0.0` (UPSTREAM-RESEARCH.md §6).
- Re-verify all unverified items (§3) against a live v1.0.0 instance before Phase 7 integration; update this doc with confirmed schemas.
- Keep ORTA's model provider abstraction independent of RAGFlow's model UI; RAGFlow is the document index/retrieval backend, ORTA owns the intelligence model layer.
