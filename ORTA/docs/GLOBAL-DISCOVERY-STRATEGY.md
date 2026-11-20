# ORTA Global Discovery Strategy

Status: **Architecture designed; source registry implemented in Core; discovery clients implemented in Bridge; live upstream integration pending target server.**

## A. Source diversity

ORTA is designed for broad, continuously expanding discovery across source categories:

| Category | Access method | ORTA support |
|----------|---------------|--------------|
| Websites | HTTP/HTML | SearXNG + direct crawl |
| Search engines | JSON API | SearXNG `?format=json` |
| RSS/Atom feeds | HTTP XML | Bridge source registry (type=rss) |
| Public datasets | HTTP/API | Source registry (type=public_dataset) |
| Open web indexes | HTTP | Source registry (type=open_index) |
| Sitemaps | HTTP XML | Source registry (type=sitemap) |
| Documentation repositories | HTTP | Source registry (type=documentation) |
| Research publications | HTTP/API (arxiv, etc.) | SearXNG arxiv engine + direct |
| Public forums/communities | HTTP | Source registry (type=forum) |
| Public company/org info | HTTP/API | Source registry (type=company_info) |
| Public APIs | HTTP/JSON | Source registry (type=public_api) |
| Publicly accessible documents | HTTP (PDF/DOCX/TXT) | Bridge → RAGFlow |
| Specialized directories | HTTP | Source registry (type=directory) |
| Common Crawl | Index API | Source registry (type=commoncrawl) |

New sources are discovered from existing sources (e.g. links in crawled pages, search results) whenever technically and legally appropriate.

## B. Source registry (implemented in ORTA Core)

The `sources` table records:
- Source identity (`source_id`, unique)
- Domain, URL (`source_urls`)
- Source type (`source_type`: website/search_engine/rss/sitemap/commoncrawl/public_dataset/...)
- Discovery origin (`discovery_origin`)
- Language (`language`, default "und")
- Category (`category`)
- Access method (`access_method`: http, rss, api, ...)
- Crawl policy (`crawl_policy` JSON: rate limit, robots respect, depth)
- Last successful access (`last_successful_access`)
- Reliability (`reliability`, 0..1)
- Update frequency (`update_frequency`)
- Content volume (`content_volume`)
- Error history (`error_history` JSON)
- Active flag (`is_active`)

Idempotent by `source_id`. Source URLs dedupe by `normalized_url` + `content_hash`.

API: `POST /api/v1/sources` (idempotent), `GET /api/v1/sources`, `GET /api/v1/sources/{id}`, `PATCH /api/v1/sources/{id}`.

## C. Continuous discovery

- Scheduled discovery: Bridge `discover` job type (SearXNG search → register sources).
- New URL discovery: `_register_discovered_source` normalizes + registers.
- Source refresh: re-crawl via repeat `discover`/`crawl` jobs.
- Incremental crawling: content-hash dedupe skips unchanged content.
- Change detection: new `content_hash` → new evidence record.
- Priority queues: job `payload` carries priority hints; worker orders by `created_at`.
- Duplicate detection: content-hash + normalized_url dedupe.
- Retry/backoff: `retry_count`/`max_retries`, dead-letter after exhaustion.

## D. Scaling (prepared, not live-tested)

- Worker scaling: Bridge background worker; production should run dedicated worker processes.
- Distributed workloads: job `correlation_id` for traceability across workers.
- Crawl prioritization: `crawl_policy` per source.
- Rate limiting: `ORTA_RATE_LIMIT_DEFAULT`, per-source `crawl_policy`.
- Resource-aware concurrency: configurable max concurrent jobs.
- Storage lifecycle: retention/rotation (see BACKUP-RESTORE-REPORT.md).
- Index growth: RAGFlow dataset-bound; document volume tracked via `content_volume`.

## E. Realistic coverage (compliance)

ORTA does **not** claim to crawl the entire internet. It respects:
- `robots.txt` where applicable (via `crawl_policy`).
- Terms of service.
- API limits / rate limits.
- Copyright.
- Privacy.
- Authentication boundaries (no credentialed access without authorization).

Optimized for maximum useful and lawful coverage, not universal access.

## F. Discovery measurement (tracked in Core)

Tracked via Core records:
- Sources discovered (`sources` count)
- New domains discovered (distinct `domain`)
- URLs collected (`source_urls` count)
- Documents processed (`Evidence` count)
- Unique content (distinct `content_hash`)
- Indexed records (`Evidence.document_id` not null)
- Failed jobs (`bridge_jobs` status=failed/dead_letter)
- Discovery throughput (jobs/time)
- Source freshness (`last_successful_access`)

The source universe expands over time via discovery jobs rather than depending entirely on manual source lists.

## G. Current implementation state
- Source registry: implemented in Core (accepted by acceptance tests).
- Discovery client: `SearXNGClient.search` + `_register_discovered_source` in Bridge.
- Live discovery integration: pending SearXNG deployment (target server).
