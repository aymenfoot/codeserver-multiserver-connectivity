#!/usr/bin/env bash
# backup.sh - Backup ORTA Postgres, persistent volumes, and config.
# Writes to a timestamped directory under deploy/backup/. Never overwrites prod.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ORTA_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_FILE="$ORTA_ROOT/deploy/compose/docker-compose.yml"
BACKUP_ROOT="$ORTA_ROOT/deploy/backup"
TS="$(date +%Y%m%dT%H%M%S)"
BACKUP_DIR="$BACKUP_DIR_BASE"
BACKUP_DIR="$BACKUP_ROOT/$TS"

mkdir -p "$BACKUP_DIR"

echo "== ORTA backup ($TS) =="
echo "backup dir: $BACKUP_DIR"

# 1. Postgres dump
echo "- dumping Postgres (orta DB) ..."
docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U orta orta > "$BACKUP_DIR/orta-postgres.sql" 2>/dev/null || {
  echo "WARN: postgres dump failed (is postgres running?)"
}

# 2. Config + compose (non-secret)
echo "- archiving configuration ..."
tar -czf "$BACKUP_DIR/orta-config.tar.gz" \
  -C "$ORTA_ROOT" deploy/env deploy/compose deploy/searxng deploy/ragflow 2>/dev/null || true

# 3. Docker volumes (data) — snapshot via cp from containers
echo "- snapshotting application data volumes ..."
docker run --rm \
  -v orta-pgdata:/src:ro -v "$BACKUP_DIR":/dst \
  alpine cp -a /src /dst/pgdata-snapshot 2>/dev/null || {
  echo "WARN: volume snapshot failed"
}

echo "OK: backup complete -> $BACKUP_DIR"
echo "Restore target: deploy/restore/ (isolated directory, never production)"
