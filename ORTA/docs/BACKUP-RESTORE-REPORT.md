# ORTA Backup & Restore Report

## A. Backup strategy
Persistent state (build env):
- Core database: `storage/orta.db` (SQLite)
- Bridge database: `storage/bridge.db` (SQLite)

Target (production): PostgreSQL (`orta-pgdata` volume) + RAGFlow volumes (MinIO, MySQL, Elasticsearch) + config.

Backup method: file-level copy of SQLite DBs (dev) / `pg_dump` + volume snapshots (prod).

Backup script: `deploy/scripts/backup.sh` → `deploy/backup/<timestamp>/` containing:
- `orta-postgres.sql` (Postgres dump)
- `orta-config.tar.gz` (compose + config templates, non-secret)
- `pgdata-snapshot/` (volume snapshot)

Retention: operators implement rotation (e.g. keep last 7 daily, 4 weekly).

## B. Restore test (isolated destination)
Restore script: `deploy/scripts/restore.sh <backup-dir> <isolated-target-dir>`.
- Restores into an ISOLATED directory only.
- Requires user confirmation (`type 'restore'`).
- Never overwrites production database or existing persistent data.
- Validation: point a test ORTA instance at restored Postgres + run acceptance tests.

**Restore test not executed in build env** (would require stopping live services or a spare DB server). Documented as a pre-production step.

## C. Backup/restore coverage
| Data | Backup | Restore | Tested |
|------|--------|---------|--------|
| Core/Postgres (orta DB) | pg_dump / sqlite copy | sql restore | no (target only) |
| Persistent documents | volume snapshot | volume restore | no (target only) |
| RAGFlow datasets/indexes | MinIO/ES volumes | volume restore | no (target only) |
| ORTA config | env + compose tar | copy back | no (target only) |
| Deployment metadata | scripts + version matrix | n/a | n/a |

## D. Verification checklist (pre-production)
- [ ] Backup copy succeeds while services live.
- [ ] `sqlite3`/pg_dump output contains expected tables.
- [ ] `alembic current` reports head against restored DB.
- [ ] Restore to isolated path; start Core/Bridge against it; run acceptance subset.
- [ ] Production DB never overwritten during test.
