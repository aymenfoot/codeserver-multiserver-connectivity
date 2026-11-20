# ORTA Scalability

Status: **Architecture prepared; no live benchmark measurements performed.**

## A. Resource expectations (design targets, not measured benchmarks)

| Component | CPU | RAM | Disk | Notes |
|-----------|-----|-----|------|-------|
| ORTA Core | 0.25–0.5 | 256–512 MiB | 2–5 GiB | Python/FastAPI + PostgreSQL |
| ORTA Bridge | 0.25–0.5 | 256–512 MiB | 1–2 GiB | job worker + clients |
| ORTA UI | 0.25–0.5 | 256–512 MiB | 0.5–1 GiB | SPA proxy |
| PostgreSQL | 0.5 | 512 MiB–1 GiB | 5–10 GiB | production DB |
| Redis | 0.25 | 256–512 MiB | 1–2 GiB | cache/queue |
| SearXNG | 0.25–0.5 | 256–512 MiB | 2–5 GiB | metasearch |
| RAGFlow + companions | 4+ | 8–16 GiB | 50+ GiB | document engine (dominant) |

**No benchmark results measured.** These are design estimates only.

## B. Scaling levers (documented, not live-tested)
- Worker scaling: run multiple Bridge worker processes behind a queue.
- Distributed workloads: `correlation_id` traces jobs across workers.
- Crawl prioritization: per-source `crawl_policy`.
- Rate limiting: `ORTA_RATE_LIMIT_DEFAULT`, per-source policy, SearXNG limiter.
- Resource-aware concurrency: configurable max concurrent jobs.
- Storage lifecycle: retention/rotation (BACKUP-RESTORE-REPORT.md).
- Index growth: RAGFlow dataset-bound; `content_volume` tracks per-source volume.

## C. Horizontal expansion
Designed for horizontal expansion where resources permit:
- Core, Bridge, UI are stateless services (scale behind a load balancer).
- PostgreSQL/Redis shared state.
- RAGFlow scales per its own clustering documentation.

## D. Retention & archival (policy, not implemented)
- Evidence/documents: configurable retention (default 90 days).
- Job state: 30 days.
- Crawl logs: 14 days.
- Rotate logs and temp job artifacts daily.

## E. Build-host constraint (not a product limit)
The build host (4 CPU, 7.7 GB RAM, 6 GiB free) cannot run the full stack (RAGFlow alone recommends 4 CPU/16 GB/50 GB). Scaling targets a separate, larger server. This is an environment limitation, not an ORTA architecture limitation.
