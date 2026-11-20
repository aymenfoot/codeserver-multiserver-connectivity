# ORTA Deployment Runbook

Target: separate production server with Docker Engine 24+ and Docker Compose v2.
ORTA workspace: `/home/coder/workspace/ORTA/` (build/preparation environment).
Deployable package: `/home/coder/workspace/ORTA/deploy/`.

## Prerequisites (target server)
- Linux amd64
- Docker Engine 24+
- Docker Compose v2
- 4+ CPU, 8+ GiB RAM (minimum), 16+ GiB RAM (recommended with RAGFlow)
- 50+ GiB disk
- Root or docker-group access

## Deployment commands (exact, in order)

### 1. Transfer the package to the target server
Copy the `deploy/` directory and `.env` template to the target server. Do NOT copy `storage/*.db` (build env data) unless you intend to seed the production DB.

### 2. Prepare environment
```bash
cd /path/to/orta          # ORTA project root on target
cp deploy/env/env.example .env
# Edit .env: replace every REPLACE_ME with a strong secret
# Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Verify configuration (dry parse, no data changes)
```bash
bash deploy/scripts/verify-config.sh
```
Expected: all checks OK; WARN only for placeholder secrets.

### 4. Deploy
```bash
bash deploy/scripts/deploy.sh
```
Steps performed: pull pinned images → build ORTA images → start infra → run Alembic migrations → start full stack → health checks.

### 5. Verify health
```bash
bash deploy/scripts/healthcheck.sh
```
Expected: all `OK` (Core :8000/healthz, Bridge :8001/healthz, UI :3000/, RAGFlow healthz, SearXNG healthz).

### 6. Access
- UI: http://<target>:3000 (place reverse proxy in front for external access)
- Core API: http://<target>:8000 (internal)
- Bridge API: http://<target>:8001 (internal)
- Services bind to 127.0.0.1 only in compose; reverse proxy recommended.

## Updating the platform
```bash
# Edit .env / compose as needed, then:
bash deploy/scripts/verify-config.sh
docker compose -f deploy/compose/docker-compose.yml up -d   # rolling update
bash deploy/scripts/migrate.sh                                # if schema changed
bash deploy/scripts/healthcheck.sh
```

## Backup
```bash
bash deploy/scripts/backup.sh
# Output: deploy/backup/<timestamp>/  (orta-postgres.sql, orta-config.tar.gz, pgdata-snapshot)
```

## Restore (isolated destination — NEVER overwrite production)
```bash
bash deploy/scripts/restore.sh deploy/backup/<timestamp> /tmp/orta-restore-test
# Then point a test ORTA instance at the restored Postgres and run acceptance tests.
```

## Troubleshooting
| Symptom | Action |
|---------|--------|
| Container won't start | `docker compose -f deploy/compose/docker-compose.yml logs <service>` |
| Postgres not ready | wait for `pg_isready`; check `POSTGRES_PASSWORD` matches `ORTA_DB_PASSWORD` |
| Core migration fails | verify `ORTA_DATABASE_URL` in .env; run `deploy/scripts/migrate.sh` |
| Bridge can't reach Core/RAGFlow | verify `ORTA_CORE_URL`, `ORTA_RAGFLOW_URL`, `ORTA_RAGFLOW_API_KEY` |
| Job dead-lettered | inspect `GET /api/v1/jobs/<id>` error/error_class; retry via API |
| Health check fails | `bash deploy/scripts/healthcheck.sh`; check service logs |

## What is NOT deployed by this runbook
- CROWler (no official verifiable repository). Add when identified.
- Reverse proxy / TLS termination (site-specific).
- Authentication/authorization (dev build; enable `ORTA_ENABLE_AUTH` and implement before production).
