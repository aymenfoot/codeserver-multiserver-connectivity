# ORTA Upstream Research & Verification

This document records the official upstream repositories, versions, deployment methods,
dependencies, APIs, and compatibility findings for the three primary upstream projects:
CROWler, SearXNG, and RAGFlow. All findings were verified against live upstream sources
on 2026-11-20. No similarly-named forks or unofficial images were trusted without
verification.

## 1. Official repositories

### SearXNG — metasearch / source discovery

| Field | Value |
|-------|-------|
| Official repository | https://github.com/searxng/searxng |
| Verified HEAD | 368baa340d87428a4a30077b2b0531032906b811 |
| Official Docker image | `searxng/searxng` (Docker Hub) |
| Pinned image tag (existing verified stack) | `searxng/searxng:2026.11.11-626105eec` |
| Versioning scheme | Date + commit (`YYYY.MM.DD-<shortsha>`) |
| License | AGPLv3 |
| Documentation | https://docs.searxng.org/ |

Verification: `git ls-remote https://github.com/searxng/searxng.git HEAD` returned the
HEAD above; the image tag matches the pre-existing `searxng-ldr-stack` in this workspace
(which pins `searxng/searxng:2026.11.11-626105eec`).

Release API (`/repos/searxng/searxng/releases/latest`) returns 404 — SearXNG does not
publish GitHub Releases; versions are date-based tags/images. The pinned tag above is the
stable reference.

### RAGFlow — document processing, knowledge indexing, retrieval

| Field | Value |
|-------|-------|
| Official repository | https://github.com/infiniflow/ragflow |
| Latest stable release | `v1.0.0` |
| Release commit | db1cd5929a7885a3074547791f5ecc4d2f891739 |
| Published | 2026-11-06T12:31:31Z |
| Official Docker image | `infiniflow/ragflow` (Docker Hub) |
| Documentation | https://ragflow.io/docs/dev/ |
| License | Apache-2.0 |

Verification: `git ls-remote --tags https://github.com/infiniflow/ragflow.git` shows
`v1.0.0` as the latest stable tag (rc1/rc2/rc3 precede it). Release API confirms
`tag_name: v1.0.0`, published 2026-11-06.

### CROWler — discovery, crawling, source collection

| Field | Value |
|-------|-------|
| Official repository | NOT FOUND (no verifiable official project) |
| Status | UNRESOLVED |

Extensive search was performed for an official "CROWler" discovery/crawling project:

- GitHub org `CROWler`: repositories `CROWler`, `crowler`, `CROWLER` all return
  "Repository not found".
- GitHub repository search for `"CROWler"`, `crowler`, `CROWLER`, `crowler discovery
  crawler`, `CROWler osint intelligence`, `crowler framework web crawler`: no project
  matching a general-purpose discovery/crawling/source-collection platform.
- Closest name match: `psiotwo/crowler` ("crOWLer - Web Crawler for extracting RDF(S)
  and OWL data"), Java, 2 stars, last updated 2025-11-01. This is an RDF/OWL semantic-web
  crawler, NOT a general discovery/crawling platform, and is stale/low-adoption. It was
  explicitly NOT selected.

**Finding:** No verifiable official upstream "CROWler" repository exists that satisfies the
mission requirement (complete official project for discovery, crawling, source collection,
with RSS/Sitemap/CommonCrawl/SearXNG providers). This is recorded as an upstream
dependency blocker. See ARCHITECTURE.md and KNOWN-LIMITATIONS.md for the mitigation
(ORTA will provide its own discovery/crawling bridge component rather than substituting an
unverified project, per the rule "Do not add unrelated upstream projects").

## 2. Version selection

### SearXNG — pinned: `searxng/searxng:2026.11.11-626105eec`

- Chosen because it is the tag already verified in this environment's
  `searxng-ldr-stack` (docker-compose.yml, pinned 2026-11-12).
- Date-based versioning; no GitHub Releases. Image tag is the version pin.
- No breaking-change risk at this pin; stable for deployment.

### RAGFlow — pinned: `v1.0.0`

- Latest stable release (not a release candidate).
- Breaking changes between v0.x and v1.0.0 are possible; v1.0.0 is the stable target.
- All subsequent docs and compose files pin `v1.0.0` / image `infiniflow/ragflow:v1.0.0`.
- Uncontrolled `latest` tags are explicitly avoided.

### CROWler — not applicable (unresolved)

No version selected pending repository resolution.

## 3. Deployment methods & dependencies

### SearXNG

| Item | Detail |
|------|--------|
| Deployment | Docker container (`searxng/searxng:<tag>`) |
| Official method | Docker / docker-compose (docs.searxng.org/install) |
| Listening port | 8080 (HTTP) |
| Health endpoint | `/healthz` |
| Required config | `searxng` settings mount + `SEARXNG_SECRET` env var |
| Persistent state | `/var/cache/searxng` (cache), `/etc/searxng` (config) |
| Dependencies | None (standalone Python app; Redis optional for rate limiting) |
| Integration | HTTP JSON API; SearXNG can be used as an upstream by CROWler via HTTP |

### RAGFlow (v1.0.0)

| Item | Detail |
|------|--------|
| Deployment | Docker compose (official `docker/docker-compose.yml` + `docker-compose-base.yml`) |
| Official method | Docker compose only (no native install) |
| Web/API port | 80 (HTTP), 443 (HTTPS), 9380 (Go API), 9381 (Admin) |
| Required services | MySQL, Valkey/Redis, Kvrocks, MinIO (object storage), Elasticsearch/Infinity, Docker sandbox for parsing |
| Image | `infiniflow/ragflow:v1.0.0` |
| Config | `service_conf.yaml.template` + `.env` |
| Persistent storage | `./ragflow-logs`, MinIO data, MySQL data, Valkey data, Kvrocks data |
| Authentication | API key-based (`Authorization: Bearer <key>`) via `/api/v1/` |
| Resource note | Heavy: multiple services, GBs of images, significant RAM |

### CROWler

Not applicable (repository unresolved).

## 4. APIs & integration mechanisms

### SearXNG

- JSON output: append `&format=json` to search requests.
- Endpoint: `GET /search?q=<query>&format=json` (and `/search` HTML).
- Internal network access: reachable via container name on port 8080 within the Docker
  network.
- CROWler connectivity: CROWler can call SearXNG's JSON endpoint as a discovery provider.
- Auth: `SEARXNG_SECRET` for settings; search itself is typically unauthenticated internally.

### RAGFlow

- REST API base: `http://<ragflow>:9380/api/v1/` (Go API).
- Auth: Bearer API token (obtained via `/api/v1/auth/login` or configured API key).
- Document lifecycle: create dataset → upload document → parse → index → retrieve.
- Supported file types: PDF, DOCX, TXT, HTML, image, etc. (version-dependent).
- Document status API: polling for parsing/indexing completion.
- Retrieval: `/api/v1/retrieval` with vector similarity.

### CROWler

Not applicable (repository unresolved). ORTA Bridge will define its own ingestion contract.

## 5. Known compatibility issues (verified)

| Project | Issue |
|---------|-------|
| SearXNG | None at pinned tag. Requires `SEARXNG_SECRET`; exposes `/healthz`. |
| RAGFlow | v1.0.0 requires Docker compose + MySQL + Valkey + Kvrocks + MinIO + sandbox. Not runnable natively. Heavy resource use. |
| CROWler | No official repository located — cannot verify APIs, versions, or compatibility. |

## 6. Version pins adopted (for all downstream compose/config)

```
SEARXNG_IMAGE=searxng/searxng:2026.11.11-626105eec
RAGFLOW_VERSION=v1.0.0
RAGFLOW_IMAGE=infiniflow/ragflow:v1.0.0
CROWLER_STATUS=unresolved (no official repo)
```

## 7. Verification method

- `git ls-remote` against official GitHub remotes for HEAD and tags.
- GitHub Releases API for release metadata.
- Existing workspace stack `searxng-ldr-stack/docker-compose.yml` for the pinned SearXNG
  image tag and deployment pattern.
- Direct `curl` to `raw.githubusercontent.com` for README/compose file contents.
