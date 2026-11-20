# ORTA Architecture

Target-state architecture for the ORTA Discovery and Intelligence Platform. This is the
design reference for all subsequent implementation. Deployment constraints for this
specific environment (no Docker, no root, limited disk/RAM) are documented in
RESOURCE-PLAN.md; the native-buildable components (Core, Bridge, UI) are specified for
direct implementation here.

## 1. Guiding principles

- One coherent platform called ORTA, not three independent applications.
- Use existing capabilities of the three upstream projects before building replacements.
- No unrelated upstream projects added.
- Every assertion traceable to supporting evidence (intelligence integrity).
- No `latest` image tags; versions pinned (see UPSTREAM-RESEARCH.md).
- Internal databases/admin services never publicly exposed.

## 2. Service inventory

| Service | Owner | Type | Technology | Runtime in this env |
|---------|-------|------|------------|---------------------|
| ORTA Unified UI | ORTA | frontend + API gateway | web app | native (buildable) |
| ORTA Intelligence Core | ORTA | intelligence data model & workflows | Python service | native (buildable) |
| ORTA Bridge | ORTA | integration/job/normalization layer | Python service | native (buildable) |
| ORTA Pipeline | ORTA | data pipeline orchestration | Python workers | native (buildable) |
| PostgreSQL (Core) | ORTA | evidence/entity/claim/investigation DB | PostgreSQL | native (buildable) |
| Redis | ORTA | cache + job queue | Redis | native (buildable) |
| SearXNG | upstream | metasearch + discovery provider | Docker | NOT deployable here |
| RAGFlow | upstream | document processing + indexing + retrieval | Docker | NOT deployable here |
| CROWler | upstream | discovery/crawling | unresolved (no repo) | not available |

## 3. Docker networks (target-state)

| Network | Driver | Members | Purpose |
|---------|--------|---------|---------|
| `orta-internal` | bridge | Core, Bridge, Pipeline, PostgreSQL, Redis, (SearXNG, RAGFlow target) | service-to-service |
| `orta-frontend` | bridge | Unified UI, API gateway | public API + UI |

No host port publishing for databases or admin services.

## 4. Persistent storage

| Volume | Mount | Service | Contents |
|--------|-------|---------|----------|
| `orta-pgdata` | `/var/lib/postgresql/data` | PostgreSQL | Core DB |
| `orta-redis` | `/data` | Redis | cache/queue |
| `orta-evidence` | `/data/evidence` | Core/Bridge | raw evidence + content hashes |
| `orta-jobs` | `/data/jobs` | Bridge/Pipeline | persistent job state |
| `orta-uploads` | `/data/uploads` | Bridge | staged uploads to RAGFlow |
| `searxng-cache` (target) | `/var/cache/searxng` | SearXNG | search cache |
| `ragflow-*` (target) | various | RAGFlow | MySQL/Valkey/Kvrocks/MinIO/logs |

## 5. Databases

- **PostgreSQL:** ORTA Core system of record — evidence, entities, claims, sources,
  investigations, reports, jobs, provenance.
- **Redis:** job queue, rate-limit counters, short-lived cache.

Target-state upstream databases (SearXNG cache, RAGFlow MySQL/Valkey/Kvrocks/MinIO) are
owned by their respective projects and not part of ORTA Core.

## 6. API boundaries

| Boundary | Direction | Contract |
|----------|-----------|----------|
| UI → Core API | HTTP/JSON | REST + WebSocket for investigation progress |
| Core → Bridge | HTTP/JSON + DB | job creation, sync results |
| Bridge → SearXNG (target) | HTTP/JSON | `GET /search?q=&format=json` |
| Bridge → RAGFlow (target) | HTTP/JSON + file upload | `/api/v1/` auth + document lifecycle |
| Bridge → Core | DB | write evidence/entities/claims after indexing |
| Pipeline → internal services | HTTP/JSON | orchestration |

All APIs validated; idempotent job creation; correlation IDs for traceability.

## 7. Authentication & authorization

- ORTA Core: session-based auth (or JWT) for UI/API; API keys for programmatic access.
- Bridge: internal service token for Core↔Bridge; no public exposure.
- SearXNG: `SEARXNG_SECRET` (internal only); search unauthenticated within network.
- RAGFlow: Bearer API token (target).
- Secrets stored in `ORTA/secrets/` (gitignored), never in logs or images.
- No credentials hardcoded.

## 8. Internal communication

- Service discovery via Docker network DNS (target) or `localhost` + configured ports
  (native dev).
- All inter-service traffic over the internal network; frontend reaches Core/Bridge
  through the API gateway on localhost.
- Correlation IDs propagated across Bridge → RAGFlow → Core for end-to-end traceability.

## 9. External access

- Unified UI and public API on `127.0.0.1:3000` (localhost only in this environment;
  reverse proxy in production).
- No public exposure of PostgreSQL, Redis, SearXNG admin, or RAGFlow admin.
- Firewall: only UI/API port published; everything else internal.

## 10. Data flow (pipeline)

```
Discovery (CROWler target / ORTA crawler + SearXNG)
     → ORTA Bridge (job, normalize, validate, deduplicate)
     → RAGFlow (target: upload, parse, index)
     → ORTA Core (sync evidence, entities, claims, provenance)
     → ORTA Unified UI (investigations, reports, evidence explorer)
```

- Deduplication at Bridge by content hash + canonical URL.
- Dead-letter queue for failed documents; retry with backoff.
- Reconciliation job re-processes interrupted/failed jobs on restart.

## 11. Failure handling

| Failure | Handling |
|---------|----------|
| Service restart | persistent job state in DB/Redis; resume on startup |
| Network failure | retry with exponential backoff; dead-letter after N attempts |
| API timeout | timeout per call; mark job retryable |
| Invalid document | validation at Bridge; dead-letter + alert |
| Duplicate content | content-hash dedupe; skip re-indexing |
| Interrupted job | reconciliation on restart re-claims unacknowledged jobs |
| Provider failure | circuit breaker; shift to alternate discovery source |

## 12. Startup dependencies (target-state)

1. PostgreSQL + Redis (databases first)
2. ORTA Core (migrations, then API)
3. ORTA Bridge (depends on Core)
4. ORTA Pipeline workers
5. Unified UI (depends on Core API)
6. SearXNG / RAGFlow (target-state, independent but before Bridge upstream calls)

Health checks: each service exposes `/healthz`; dependencies declare `condition:
service_healthy` (compose) or startup retry logic (native).

## 13. Health checks

| Service | Check |
|---------|-------|
| ORTA Core | `GET /healthz` → DB connectivity |
| ORTA Bridge | `GET /healthz` → Core + Redis reachable |
| ORTA UI | `GET /healthz` → Core API reachable |
| PostgreSQL | `pg_isready` |
| Redis | `redis-cli ping` |
| SearXNG (target) | `GET /healthz` |
| RAGFlow (target) | `GET /api/v1/health` (version-dependent) |

Unhealthy → restart; restart events logged and surfaced in UI System Health.
