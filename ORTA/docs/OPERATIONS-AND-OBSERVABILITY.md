# ORTA Operations and Observability

Status: **Health endpoints and job visibility implemented; structured logging and alerting pending production hardening.**

## A. Service health

| Service | Endpoint | What it checks |
|---------|----------|----------------|
| ORTA Core | `GET /healthz` | database connectivity (ok/unreachable) |
| ORTA Bridge | `GET /healthz` | database connectivity + Core reachable |
| ORTA UI | `GET /` | service up |
| SearXNG (target) | `GET /healthz` | returns "OK" |
| RAGFlow (target) | `GET /api/v1/system/healthz` | HTTP 200 |

Health checks declared in `deploy/compose/docker-compose.yml` with `start_period`, `interval`, `timeout`, `retries`. Unhealthy → Docker restart (`unless-stopped`).

## B. Job queue visibility
- Bridge `/api/v1/jobs` lists all jobs with status, retries, dead_letter flag, error, error_class.
- UI Processing Jobs section + dashboard job breakdown (pending/running/completed/failed/dead_letter).
- Reconciliation (`_run_reconcile`) reclaims stale `running` jobs on recovery.

## C. Error logging
- Bridge records `error` and `error_class` (transient/permanent/policy) per job.
- Uvicorn access logs to stdout.
- **No credentials logged intentionally.** Review job error text for upstream error messages before production.

## D. Storage visibility
- Core `storage/orta.db` (SQLite dev) / PostgreSQL (target).
- Bridge `storage/bridge.db` (SQLite dev).
- Persistent volumes declared in compose (`orta-pgdata`, `orta-redisdata`, `searxng-cache`, ragflow volumes).
- Backup via `deploy/scripts/backup.sh` (Postgres dump + config + volume snapshot).

## E. Source freshness
- Core `sources.last_successful_access` and `content_volume`.
- Bridge `NormalizedContent.first_seen`/`last_accessed`.
- Dashboard does not currently display freshness; planned for operations view.

## F. Operational troubleshooting
1. Service down → check `docker compose logs <service>` and healthcheck.
2. Job dead-lettered → inspect `error`/`error_class`; retry via Bridge API or UI.
3. Upstream unreachable → verify SearXNG/RAGFlow health; Bridge retries transient errors.
4. Migration needed → `deploy/scripts/migrate.sh` (alembic upgrade head).

## G. Alerting (planned, not implemented)
- No active alerting/paging in this build. Health endpoints + job dead-letter surfacing provide passive observability. Production should add metric collection (Prometheus) and alerting on: service unhealthy, dead_letter jobs, failed Core health, disk usage.
