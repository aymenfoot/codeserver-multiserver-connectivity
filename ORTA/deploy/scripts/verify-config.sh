#!/usr/bin/env bash
# verify-config.sh - Validate compose + env before deploying.
# Fails clearly when prerequisites are missing. Does not modify data.
set -euo pipefail

COMPOSE_FILE="deploy/compose/docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE="deploy/env/env.example"

echo "== ORTA configuration verification =="

# 1. Compose file present
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "FAIL: compose file not found: $COMPOSE_FILE"
  exit 1
fi
echo "OK: compose file present: $COMPOSE_FILE"

# 2. Env file present (or example to copy from)
if [[ ! -f "$ENV_FILE" ]]; then
  if [[ -f "$ENV_EXAMPLE" ]]; then
    echo "WARN: .env not found. Copy deploy/env/env.example to .env and fill secrets."
  else
    echo "FAIL: env example not found: $ENV_EXAMPLE"
    exit 1
  fi
else
  echo "OK: .env present"
fi

# 3. Docker availability
if ! command -v docker >/dev/null 2>&1; then
  echo "FAIL: docker CLI not installed"
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "FAIL: docker daemon not running (start Docker Engine)"
  exit 1
fi
echo "OK: docker daemon reachable"

# 4. Compose plugin availability
if ! docker compose version >/dev/null 2>&1; then
  echo "FAIL: docker compose plugin not installed"
  exit 1
fi
echo "OK: docker compose plugin present"

# 5. Compose config validates (dry parse, no containers started)
if ! docker compose -f "$COMPOSE_FILE" config --quiet >/dev/null 2>&1; then
  echo "FAIL: compose file is invalid"
  docker compose -f "$COMPOSE_FILE" config || true
  exit 1
fi
echo "OK: compose file valid"

# 6. Check for placeholder secrets still present (warning only)
if grep -R "REPLACE_ME" "$ENV_FILE" deploy/env/ deploy/ragflow/ >/dev/null 2>&1; then
  echo "WARN: placeholder secrets (REPLACE_ME) still present in env files — replace before production"
fi

echo "== verification complete =="
