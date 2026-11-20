#!/usr/bin/env bash
# migrate.sh - Run Alembic migrations for ORTA Core (+Bridge) against Postgres.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORTA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_FILE="$ORTA_ROOT/deploy/compose/docker-compose.yml"

DB_URL="${ORTA_DATABASE_URL:-postgresql+psycopg2://orta:orta@postgres:5432/orta}"

echo "== ORTA migrations =="
docker compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U orta -d orta >/dev/null || {
  echo "FAIL: postgres not reachable"; exit 1;
}

docker compose -f "$COMPOSE_FILE" run --rm -e ORTA_DATABASE_URL="$DB_URL" \
  orta-core sh -c "python3 -m alembic upgrade head"

echo "OK: migrations applied (alembic head)"
