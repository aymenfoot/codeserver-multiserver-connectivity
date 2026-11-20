# ORTA Integration Architecture

Integration contracts and boundaries between the upstream projects (CROWler target / SearXNG target / RAGFlow target) and ORTA custom components (Bridge, Core, Unified UI). One coherent pipeline:

```
Discovery (CROWler target / ORTA crawler + SearXNG)
  → ORTA Bridge (job, normalize, validate, deduplicate)
  → RAGFlow (target: upload, parse, index)
  → ORTA Core (sync evidence, entities, claims, provenance)
  → ORTA Unified UI (investigations, reports, evidence explorer)
```

Service runtime addresses (dev, this environment):
- ORTA Core API: `http://127.0.0.1:8100/api/v1`
- ORTA Bridge API: `http://127.0.0.1:8101/api/v1`
- ORTA Unified UI: `http://127.0.0.1:3000` (proxies `/api/core/*`, `/api/bridge/*`)
- SearXNG (target): `http://searxng:8080/search?q=&format=json` — NOT deployable here (no Docker/root)
- RAGFlow (target): `http://ragflow:9380/api/v1/` — NOT deployable here (no Docker/root; RAM/disk)

Version pins (UPSTREAM-RESEARCH.md §6):
- `SEARXNG_IMAGE=searxng/searxng:2026.11.11-626105eec`
- `RAGFLOW_IMAGE=infiniflow/ragflow:v1.0.0`
- `CROWLER_STATUS=unresolved (no official repo)`

## 1. API boundaries

| Boundary | Direction | Contract | Auth |
|----------|-----------|----------|------|
| UI → Core | HTTP/JSON (via UI proxy `/api/core/*`) | REST; investigation progress | session/API key |
| UI → Bridge | HTTP/JSON (via UI proxy `/api/bridge/*`) | job CRUD, normalize, discover, sync | session/API key |
| Core → Bridge | HTTP/JSON + DB | job creation, sync results | service token |
| Bridge → SearXNG (target) | HTTP/JSON | `GET /search?q=&format=json` | none for search (internal net) |
| Bridge → RAGFlow (target) | HTTP/JSON + file upload | dataset → upload → parse → index → retrieve | Bearer API token |
| Bridge → Core | HTTP/JSON | write evidence/entities/claims after indexing | service token |

All requests carry correlation IDs for end-to-end traceability. All APIs validated with Pydantic. Idempotent job creation.

## 2. Internal communication

- Service discovery via Docker network DNS (target-state) or `localhost` + configured ports (native dev).
- All inter-service traffic over the internal network (`orta-internal`).
- Frontend reaches Core/Bridge through the UI API gateway on localhost (`/api/core/*`, `/api/bridge/*`).
- No host port publishing for databases or admin services.

## 3. Authentication & authorization

- ORTA Core: session-based (or JWT) auth for UI/API; API keys for programmatic access.
- Bridge: internal service token for Core↔Bridge; not publicly exposed.
- SearXNG: `SEARXNG_SECRET` protects settings/cryptography only; search unauthenticated within internal network.
- RAGFlow: Bearer API token (`Authorization: Bearer <key>`); token via `/api/v1/auth/login` or `/api/v1/system/tokens`.
- Secrets in `ORTA/secrets/` (gitignored), never in logs/images. No credentials hardcoded.

## 4. Failure handling

| Failure | Handling |
|---------|----------|
| Service restart | persistent job state (Core `jobs`, Bridge `bridge_jobs`); resume on startup; Bridge reconcile reclaims stale `running` jobs |
| Network failure | retry with exponential backoff; dead-letter after `max_retries` |
| API timeout | per-call timeout; mark job retryable (transient) |
| Invalid document | validation at Bridge; permanent error → dead-letter + alert |
| Duplicate content | content-hash dedupe at Bridge and Core evidence layer; skip re-indexing |
| Interrupted job | reconciliation on restart re-claims unacknowledged jobs |
| Provider failure | circuit breaker; shift to alternate discovery source |

Error classification: `transient` (network/timeout, retryable), `permanent` (auth/unsupported-type/invalid, not retryable), `policy` (rate limit/robots, backoff).

## 5. Startup dependencies (target-state)

1. PostgreSQL + Redis
2. ORTA Core (migrations, then API)
3. ORTA Bridge (depends on Core)
4. ORTA Pipeline workers
5. Unified UI (depends on Core API)
6. SearXNG / RAGFlow (target-state, before Bridge upstream calls)

Health checks: `/healthz` per service; dependencies declare `condition: service_healthy` (compose) or startup retry logic (native).
