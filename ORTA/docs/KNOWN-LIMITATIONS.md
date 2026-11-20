# ORTA Known Limitations

Honest limitations and blockers. Statuses reported separately (Implemented / Installed / Configured / Deployed / Operational / Integration tested / Acceptance tested / Production ready) and never conflated.

## 1. Infrastructure blocker (build environment)
- No root/sudo, no Docker Engine/daemon, no Docker Compose plugin, user namespaces blocked, 6 GiB disk free.
- Consequence: Docker-native upstreams cannot be deployed in the build env:
  - SearXNG (official image is Docker) — not deployed here.
  - RAGFlow v1.0.0 (Docker Compose only; needs MySQL+Valkey+Kvrocks+MinIO+Elasticsearch+sandbox; 4 CPU/16 GB/50 GB recommended) — not deployed here.
- ORTA Core, Bridge, UI deployed natively (Python + SQLite) and operational + acceptance-tested (55/55).

## 2. CROWler — unresolved upstream
- No official verifiable discovery-crawler repository (GitHub org `CROWler` repos not found; name searches return unrelated/stale crawlers).
- Not substituted with an unrelated project (per mission rule).
- Bridge adapter interface prepared for future integration.

## 3. Upstream integration not live-executed
- SearXNG search + RAGFlow upload/parse/index/retrieve clients written against verified v1.0.0 route tables, but not tested against live instances.
- RAGFlow auth login body / exact response shapes unverified against a live server.

## 4. Pre-production gaps (Core/Bridge/UI dev build)
- No authentication/authorization on Core or Bridge APIs.
- CORS `allow_origins=["*"]` (localhost dev).
- SQLite instead of target PostgreSQL.
- No vulnerability scan (`pip audit`).
- Secrets not yet in `ORTA/secrets/` with restricted permissions.
- No observability alerting beyond health endpoints + dead-letter surfacing.
- Bridge background worker is an in-process daemon thread (production: dedicated worker).

## 5. What is not claimed
- ORTA does not crawl the entire internet; respects robots.txt/ToS/rate limits/copyright/privacy/auth boundaries (target-state design).
- No invented statistics in UI; every number from live Core/Bridge APIs.
- No fake data / placeholder endpoints in production paths (DB starts empty; records via API only).

## 6. What remains to reach production ready
- Deploy SearXNG, RAGFlow (target server with Docker).
- Resolve or replace CROWler path.
- Execute live integration tests against upstreams.
- Add authN/authZ, restrict CORS, run `pip audit`, secrets management.
- Run isolated backup/restore test.
- Add observability alerting; harden for production; re-run full acceptance.
