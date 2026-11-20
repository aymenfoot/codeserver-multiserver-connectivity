#!/usr/bin/env bash
# deploy.sh - Full ORTA deployment on the target server.
# Order: prep → verify → pull/build → init DB → migrate → up → health.
# Fails clearly on missing prerequisites. Never destroys existing data.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORTA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_FILE="$ORTA_ROOT/deploy/compose/docker-compose.yml"
ENV_FILE="$ORTA_ROOT/.env"

echo "== ORTA deployment =="
echo "ORTA root: $ORTA_ROOT"

# 1. Prerequisites
command -v docker >/dev/null || { echo "FAIL: docker not installed"; exit 1; }
docker info >/dev/null 2>&1 || { echo "FAIL: docker daemon not running"; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "FAIL: docker compose plugin not installed"; exit 1; }

# 2. Env
if [[ ! -f "$ENV_FILE" ]]; then
  echo "WARN: .env missing; copying deploy/env/env.example -> .env (fill secrets before production)"
  cp "$ORTA_ROOT/deploy/env/env.example" "$ENV_FILE"
fi
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a

# 3. Verify config
bash "$SCRIPT_DIR/verify-config.sh"

# 4. Pull pinned upstream images
echo "== pulling pinned upstream images =="
docker compose -f "$COMPOSE_FILE" pull searxng ragflow ragflow-mysql ragflow-redis ragflow-kvrocks ragflow-minio ragflow-elasticsearch postgres redis

# 5. Build ORTA images
echo "== building ORTA images =="
docker compose -f "$COMPOSE_FILE" build orta-core orta-bridge orta-ui

# 6. Start infrastructure first (postgres, redis), then migrate
echo "== starting infrastructure =="
docker compose -f "$COMPOSE_FILE" up -d postgres redis
docker compose -f "$COMPOSE_FILE" up -d --no-deps searxng || true

# 7. Wait for postgres healthy
echo "== waiting for postgres =="
for i in $(seq 1 30); do
  if docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U orta -d orta >/dev/null 2>&1; then
    echo "OK: postgres ready"; break
  fi
  sleep 2
done
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U orta -d orta || { echo "FAIL: postgres not ready"; exit 1; }

# 8. Run ORTA migrations (one-off, against running postgres)
echo "== running ORTA Core migrations =="
docker compose -f "$COMPOSE_FILE" run --rm \
  -e ORTA_DATABASE_URL="${ORTA_DATABASE_URL:-postgresql+psycopg2://orta:orta@postgres:5432/orta}" \
  orta-core sh -c "python3 -m alembic upgrade head"

# 9. Bring up the full stack
echo "== starting full stack =="
docker compose -f "$COMPOSE_FILE" up -d

# 10. Health verification
echo "== running health checks =="
bash "$SCRIPT_DIR/healthcheck.sh"

echo "== deployment complete =="
echo "Services: Core :8000, Bridge :8001, UI :3000 (localhost only)"
echo "Reverse proxy recommended in front of UI in production."
