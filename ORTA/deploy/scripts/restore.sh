#!/usr/bin/env bash
# restore.sh - Restore ORTA data into an ISOLATED destination.
# NEVER overwrites production database or existing persistent data.
# Usage: restore.sh <backup-dir> <target-data-dir>
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <backup-dir> <isolated-target-data-dir>"
  echo "  backup-dir:   e.g. deploy/backup/20261120T010000"
  echo "  target-dir:   ISOLATED directory for restored data (NOT production)"
  exit 1
fi

BACKUP_DIR="$(cd "$1" && pwd)"
TARGET_DIR="$(cd "$2" && pwd)"

if [[ ! -f "$BACKUP_DIR/orta-postgres.sql" ]]; then
  echo "FAIL: backup dir missing orta-postgres.sql: $BACKUP_DIR"
  exit 1
fi

echo "== ORTA isolated restore =="
echo "backup : $BACKUP_DIR"
echo "target : $TARGET_DIR (isolated — not production)"
echo ""
echo "This restores Postgres SQL + config into $TARGET_DIR only."
echo "Production data is NOT touched."
read -r -p "Type 'restore' to continue: " confirm
[[ "$confirm" == "restore" ]] || { echo "aborted"; exit 1; }

mkdir -p "$TARGET_DIR"
cp "$BACKUP_DIR/orta-postgres.sql" "$TARGET_DIR/"
[[ -f "$BACKUP_DIR/orta-config.tar.gz" ]] && cp "$BACKUP_DIR/orta-config.tar.gz" "$TARGET_DIR/"

echo "OK: restore staged into $TARGET_DIR"
echo "Next: point a test ORTA instance at the restored Postgres and run acceptance tests."
