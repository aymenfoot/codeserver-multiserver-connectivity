# ORTA API Contracts Research — Upstream Integrations

Research findings on the official SearXNG and RAGFlow APIs/integration contracts, plus the CROWler repository status. Sources are cited inline with links. This document records research/specification only — no implementation code and no code that duplicates existing ORTA infrastructure. The four foundation docs (ARCHITECTURE.md, UPSTREAM-RESEARCH.md, RESOURCE-PLAN.md, IMPLEMENTATION-PLAN.md) are intentionally not modified.

## 0. Scope, method, and environment constraints

- Environment: Debian GNU/Linux 13, 4 CPU, ~4.7 GiB RAM, 6.2 GiB disk free, `coder` user (no sudo/root), Docker NOT installed, user namespaces blocked (`unshare -U` → "Operation not permitted"). Consequence: the Docker-native upstreams (SearXNG official image; RAGFlow) cannot be container-deployed here. RAGFlow v1.0.0 does support launching from source for development (Go 1.27, Clang/LLD/CMake/PRE2, native libs), but that is a development path, not the ORTA production target. This doc is research/spec only; no containers are pulled or run. [RESOURCE-PLAN.md §1, §3][ragflow-readme]
- Versions pinned per UPSTREAM-RESEARCH.md §6:
  - SearXNG image `searxng/searxng:2026.11.11-626105eec` (verified HEAD `368baa340d87428a4a30077b2b0531032906b811`).
  - RAGFlow `v1.0.0` (2026-11-06, release commit `db1cd5929a7885a3074547791f5ecc4d2f891739`), image `infiniflow/ragflow:v1.0.0`.
- All claims below are traceable to live upstream sources (docs, GitHub repo, source code).

## 1. SearXNG — metasearch / source discovery

### 1.1 Identity, deployment, and configuration

| Field | Value | Source |
|---|---|---|
| Official repository | https://github.com/searxng/searxng | UPSTREAM-RESEARCH.md §1 |
| Verified HEAD | `368baa340d87428a4a30077b2b0531032906b811` | UPSTREAM-RESEARCH.md §1 |
| Official Docker image | `searxng/searxng` (Docker Hub; GHCR mirror `ghcr.io/searxng/searxng`) | searxng install-docker |
| Pinned image tag | `searxng/searxng:2026.11.11-626105eec` | UPSTREAM-RESEARCH.md §1 |
| Listening port | 8080 (HTTP) | searxng install-docker |
| Health endpoint | `GET /healthz` → `200 OK` (`text/plain` body `OK`) | searxng webapp source |
| Config mount | `/etc/searxng` (`settings.yml`, `limiter.toml`, …) | searxng install-docker Volumes |
| Cache/data mount | `/var/cache/searxng` (e.g. `faviconcache.db`) | searxng install-docker Volumes |
| Secret | `SEARXNG_SECRET` → `server.secret_key` (cryptography); must be changed from default `ultrasecretkey` | searxng settings_server, webapp `init()` |
| Valkey (optional, for rate limiting) | `valkey://…:6379/0`, `$SEARXNG_VALKEY_URL` | searxng settings_valkey, limiter |

`GET /healthz` returns `Response('OK', mimetype='text/plain')` — confirmed in `searx/webapp.py`. [searxng webapp source]

### 1.2 Search request/response shape

Endpoints: `GET /`, `GET /search`, `POST /`, `POST /search`. GET passes parameters as URL query; POST as `application/x-www-form-urlencoded`. JSON output via `format=json` (also `csv`, `rss`). Format must be enabled in `settings:formats`, otherwise `403 Forbidden`. [searxng search-api]

Request parameters:
- `q` (required) — search query; engine-specific syntax (e.g. `site:github.com SearXNG`) is passed through.
- `categories` (optional) — comma-separated list of active categories.
- `language` (optional) — language code; default from `search:` settings.
- `pageno` (optional, default `1`) — search page number.
- `time_range` (optional) — `day` \| `month` \| `year`.
- `format` (optional) — `json` \| `csv` \| `rss`.
- `safesearch` (optional) — `0` \| `1` \| `2`.
- `theme` (optional) — default `simple`.

Internal call shape used by ORTA Bridge:
```
GET http://<searxng>:8080/search?q=<query>&format=json[&categories=…][&language=…][&pageno=N][&time_range=…][&safesearch=N]
```

JSON response (when `format=json`): produced by `webutils.get_json_response(search_query, result_container)`; an object containing the query context plus a `results` array. Each result is a `MainResult` with these fields: `title`, `content`, `url`, `engine`, `score`, `category`, `img_src`, `thumbnail`, `publishedDate`, `author`, `metadata`, `engines` (set of engine names for merged results), `positions`, `priority`, `length`, `views`, `iframe_src`, `audio_src`, `template`, `open_group`, `close_group`, `parsed_url`, `pubdate`. [searxng mainresult]

Error responses:
- No query + JSON → `400` with `{"error": "No query"}` (via `index_error`).
- Unknown/invalid `format` → `403 Forbidden`.
- Search exception → `500` with `{"error": "search error"}`.

### 1.3 Rate limiting

- Limiter requires a Valkey database; enabled via `server.limiter: true` (`$SEARXNG_LIMITER`). [searxng settings_server]
- Limiter configuration lives in `/etc/searxng/limiter.toml` (`[botdetection]` section): `ipv4_prefix`/`ipv6_prefix`, `trusted_proxies`, `[botdetection.ip_limit]` (`link_token`, `filter_link_local`), `[botdetection.ip_lists]` (`block_ip`, `pass_ip`, `pass_searxng_org`). [searxng limiter]
- Bot detection methods: HTTP-header probe, IP block/pass lists, and behavior-based dynamic rate limiting. Client IP resolved via `X-Forwarded-For` / `X-Real-IP` (must be set correctly behind a reverse proxy). [searxng limiter]
- `pre_request()` is installed as a Flask `before_request`; `is_installed()` is true only when limiter active and Valkey available. [searxng limiter]
- ORTA Bridge should assume 1–2 queries/sec internally (per RESOURCE-PLAN §3 rate-limit guidance) and honor `Server-Timing`/429-style backoff; SearXNG itself does not publish a documented numeric request quota in the public API docs — treat rate limits as instance-configured and back off on 403/429/500.

### 1.4 How CROWler / Bridge would call SearXNG internally

- Reachable on port 8080 via Docker network DNS (target) or `localhost:8080` (native dev); never published to the public network. [ARCHITECTURE.md §4, §9]
- Bridge calls `GET /search?q=&format=json` as an unauthenticated discovery/search provider; search itself is unauthenticated within the internal network. `SEARXNG_SECRET` protects settings/cryptography only, not search. [ARCHITECTURE.md §6, §7; searxng search-api]
- CROWler (target) can call the same JSON endpoint as a discovery provider. [UPSTREAM-RESEARCH.md §4]
- Correlation IDs propagated across Bridge → SearXNG → Core for traceability. [ARCHITECTURE.md §8]

## 2. RAGFlow — document processing, indexing, retrieval (v1.0.0)

### 2.1 Identity, deployment, and configuration

| Field | Value | Source |
|---|---|---|
| Official repository | https://github.com/infiniflow/ragflow | UPSTREAM-RESEARCH.md §1 |
| Latest stable release | `v1.0.0`, published 2026-11-06T12:31:31Z, commit `db1cd592…` | UPSTREAM-RESEARCH.md §1; ragflow-readme |
| Official Docker image | `infiniflow/ragflow:v1.0.0` | UPSTREAM-RESEARCH.md §1 |
| Deployment | Docker compose (official `docker/docker-compose.yml` + base); source launch is dev-only | ragflow-readme Local Deployment |
| Required services | MySQL, Valkey/Redis, Kvrocks, MinIO (object storage), Elasticsearch/Infinity (doc engine), Docker sandbox for parsing | UPSTREAM-RESEARCH.md §3; ragflow-readme |
| Ports | Web/API `80` (HTTP, `SVR_WEB_HTTP_PORT`); Go API `9380`; Admin `9381`; HTTPS `443` is the TLS counterpart to 80 | ragflow-readme; UPSTREAM-RESEARCH.md §3 |
| Config | `docker/.env` + `conf/service_conf.yaml` | ragflow-readme |
| Resource estimate | 4 CPU, 16 GB RAM, 50 GB disk (starting config); exceeds this server | ragflow-readme Prerequisites |
| Health check | `curl -f http://<host>:<port>/api/v1/system/healthz` → HTTP 200 | ragflow quickstart; router.go |

Note: RAGFlow docs say local deployment supports Docker (production/eval) and launching from source (development/debugging). The ORTA target is Docker compose; source build is not the ORTA path. [ragflow-readme]

### 2.2 Authentication (version-specific — v1.0.0)

REST base: `http://<ragflow>:9380/api/v1/` (Go API on port 9380; web on 80). [ragflow-readme; router.go]

Auth model confirmed from `internal/handler/auth.go` and `internal/router/router.go`:
- **Session / login auth:** `POST /api/v1/auth/login` (no-auth group, `LoginByEmail`) issues a user access token/session (cookie `oauthAuthCookie`). `POST /api/v1/users` registers. `POST /api/v1/auth/logout` (protected) ends a session. [router.go]
- **API-token auth (integration contract):** `Authorization: Bearer <API_KEY>` on protected endpoints. `AuthMiddleware` resolves a user access token first, then an API token (`ResolveAPIToken`), then (beta) a beta API token. Missing/invalid → `401 Unauthorized`; business code `109` authentication error / `102` "Authorization is not valid!". [auth.go]
- **API-key management:** `GET/POST /api/v1/system/tokens` (alias `/api/v1/system/keys`) and `DELETE /api/v1/system/tokens/:key` — list, create, delete API keys (protected). [router.go]
- Superusers are rejected from the tenant API surface (`403 "Super user shouldn't access the URL"`). [auth.go]

**Version-specific auth note:** v1.0.0 changed authentication HTTP statuses and validation business codes versus earlier releases; the migration doc says to branch on documented codes rather than exact message text. [ragflow http-api-reference Migrate to 1.0]

**APIs are NOT interchangeable across versions:** v1.0.0 removes several endpoint aliases (clients must use replacements) and changes dataset parser selection (`parse_type`/`parser_id`/`pipeline_id` instead of legacy `chunk_method`). Removed aliases include `GET /v1/system/healthz` → `GET /api/v1/system/healthz`, `POST /api/v1/file/upload` → `POST /api/v1/files`, `PUT /api/v1/datasets/{id}/documents/{doc_id}/chunks/{chunk_id}` → `PATCH …`, etc. A v0.x client will break against v1.0.0. [ragflow http-api-reference Removed API aliases / Migrate to 1.0]

### 2.3 Document lifecycle (dataset → upload → parse → index → retrieve)

All protected endpoints require `Authorization: Bearer <API_KEY>`. Response envelope: `{ "code": <int>, "message": <string>, "data": <optional> }`; `code == 0` = success; `message` is always non-empty ("success" on success). Business codes: 0 success, 101 invalid argument, 102 invalid/missing data, 103 operation error, 105 connection error, 106 operation still running, 108 permission, 109 authentication. HTTP status: 200/400/401/403/404/409/500. [ragflow http-api-reference Error Codes]

1. **Create dataset** — `POST /api/v1/datasets`
   - Body: `name` (required, BMP, ≤128 chars, case-insensitive), `parse_type` (required int: `1`=BuiltIn with `parser_id`, `2`=Pipeline with `pipeline_id`), `parser_id` (`general`, `qa`, `manual`, `table`, `paper`, `book`, `laws`, `presentation`, `picture`, `one`, `audio`, `email`; default `general`), `pipeline_id` (32-char lowercase hex), `language`, `embedding_model` (`model_name@model_factory`), `permission` (`me`\|`team`), `parser_config` (component-scoped keys containing `:`).
   - Legacy `chunk_method`/`avatar`/`description`/`auto_metadata_config` are NOT accepted by v1.0 create. [ragflow http-api-reference Create dataset; python-api-reference]
   - Response: `{ code:0, data: { id, name, parser_id, parser_config, embedding_model, language, permission, document_count:0, chunk_count:0, … } }`.

2. **Upload document** — `POST /api/v1/datasets/{dataset_id}/documents`
   - `type=local` (default, omitted): `multipart/form-data`, field `file=@<path>` (one or more files).
   - `type=web`: form fields `name` + `url` (crawl a URL into a document).
   - `type=empty`: `application/json` body `{ "name": "blank.txt" }`.
   - Response data items include `id`, `name`, `location`, `size`, `type`, `run` (processing status), `chunk_method`, `parser_config`, `dataset_id`, `created_by`. [ragflow http-api-reference Upload documents]

3. **Parse / index** — triggers ingestion:
   - Built-in chunking pipeline: `POST /api/v1/datasets/{dataset_id}/chunks` (`chunkHandler.Parse`).
   - Ingestion pipeline: `POST /api/v1/documents/ingest` (`documentHandler.Ingest`); each document ingests with its own stored `parser_id`/pipeline+pinned version.
   - Start ingestion task: `POST /api/v1/datasets/{dataset_id}/documents/parse` (`StartIngestionTask`).
   - Parsing produces chunks and indexes them (progress_msg includes "Indexing done"). [router.go; python-api-reference parse_documents]

4. **Status polling** — document `run` field values: `0/UNSTART` (not yet processed), `1/RUNNING`, `2/CANCEL`, `3/DONE`, `4/FAIL`, `5/SCHEDULE`.
   - `GET /api/v1/datasets/{dataset_id}/documents?run=DONE|FAIL|…&suffix=pdf&page=1&page_size=30` — filter/list documents by status (`run`) and suffix; `include_parsing_status=true` on dataset list returns `unstart_count/running_count/done_count/fail_count/cancel_count`.
   - `GET /api/v1/datasets/{dataset_id}/ingestions` and `GET /api/v1/ingestion/tasks` — ingestion logs/tasks.
   - `Document.parse_documents()` (SDK) blocks polling until terminal state or `progress >= 1.0` → `DONE`; raises on failure. [ragflow http-api-reference List documents; python-api-reference]

5. **Retrieve** — `POST /api/v1/retrieval` (`datasetsHandler.SearchDatasets`); or OpenAI-compatible `POST /api/v1/openai/{chat_id}/chat/completions` with `extra_body.reference: true` returns reference chunks (`document_id`, `document_name`, `similarity`, `vector_similarity`, `term_similarity`, `positions`, `document_metadata`). [router.go; ragflow http-api-reference OpenAI-compatible; python-api-reference retrieve]
   - `retrieve(params)`: `dataset_ids` (required), `document_ids`, `question`, `page`, `page_size`, `similarity_threshold` (default 0.2), `vector_similarity_weight` (default 0.3), `top_k` (default 1024), `rerank_id`, `keyword`, `metadata_condition`.

### 2.4 Supported file types

Stated in the RAGFlow README (version-dependent): Word documents, PowerPoint presentations, Excel spreadsheets, TXT files, images, PDFs, scanned copies, structured data, web pages, and more. The documents list endpoint supports a `suffix` filter (e.g. `pdf`, `txt`, `docx`). DeepDoc layout analysis/OCR/table recognition use CPU inference in the open-source 1.0 release. [ragflow-readme Key Features; quickstart]

### 2.5 Health and ports

- `GET /api/v1/system/healthz` → HTTP 200 when ready (no-auth group). Also `GET /health` (root). Use `/api/v1/system/healthz` per the quickstart. [ragflow quickstart; router.go]
- Admin listens on `9381`, API on `9380` by default (source launch); web port 80 via `SVR_WEB_HTTP_PORT`. [ragflow-readme]

## 3. CROWler — discovery/crawling (unresolved)

No official verifiable "CROWler" discovery/crawling repository exists. Candidates examined and rejected:

- GitHub org `CROWler`: repositories `CROWler`, `crowler`, `CROWLER` all return "Repository not found". [UPSTREAM-RESEARCH.md §3]
- GitHub repository search for `"CROWler"`, `crowler`, `CROWLER`, `crowler discovery crawler`, `CROWler osint intelligence`, `crowler framework web crawler`: no project matching a general-purpose discovery/crawling/source-collection platform. [UPSTREAM-RESEARCH.md §3]
- Closest name match: `psiotwo/crowler` ("crOWLer - Web Crawler for extracting RDF(S) and OWL data"), Java, 2 stars, last updated 2026-11-01 (stale). This is an RDF/OWL semantic-web crawler, NOT a general discovery/crawling platform, and is low-adoption/stale. Explicitly NOT selected. [UPSTREAM-RESEARCH.md §3]

**Finding:** CROWler is an upstream dependency blocker — no verifiable official repository satisfying the mission (complete official project for discovery/crawling/source collection with RSS/Sitemap/CommonCrawl/SearXNG providers). Per the "Do not add unrelated upstream projects" rule, ORTA will not substitute an unverified project; ORTA Bridge will define its own ingestion contract. [UPSTREAM-RESEARCH.md §3; ARCHITECTURE.md §2]

## 4. Version pins adopted (for all downstream compose/config)

```
SEARXNG_IMAGE=searxng/searxng:2026.11.11-626105eec
RAGFLOW_VERSION=v1.0.0
RAGFLOW_IMAGE=infiniflow/ragflow:v1.0.0
CROWLER_STATUS=unresolved (no official repo)
```
[UPSTREAM-RESEARCH.md §6]

## 5. Key integration contract summary (target-state)

| Boundary | Contract | Auth | Health |
|---|---|---|---|
| Bridge → SearXNG | `GET /search?q=&format=json` (port 8080) | none for search; `SEARXNG_SECRET` for settings | `GET /healthz` → `OK` |
| Bridge → RAGFlow | `POST /api/v1/datasets` → `POST /api/v1/datasets/{id}/documents` → `POST …/chunks` or `/documents/ingest` → poll `?run=` → `POST /api/v1/retrieval` | `Authorization: Bearer <API_KEY>` | `GET /api/v1/system/healthz` → 200 |

SearXNG search is unauthenticated inside the internal network; RAGFlow requires a Bearer API token obtained after web-UI login (`POST /api/v1/auth/login`) and managed via `/api/v1/system/tokens`. Neither upstream is deployable in this environment (no Docker/root; RAGFlow resource needs exceed available RAM/disk), so Bridge clients are written now for live integration when the upstreams are available. [ARCHITECTURE.md §6; RESOURCE-PLAN §3; IMPLEMENTATION-PLAN §2, §6]
