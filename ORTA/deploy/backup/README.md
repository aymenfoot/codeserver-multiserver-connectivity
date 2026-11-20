# ORTA backup directory
#
# Backups are written here by deploy/scripts/backup.sh as timestamped
# subdirectories (e.g. 20261120T010000/), each containing:
#   - orta-postgres.sql      (Postgres dump)
#   - orta-config.tar.gz     (compose + config templates)
#   - pgdata-snapshot/       (volume snapshot)
#
# Backups are NOT automatically rotated here. Operators should implement
# retention (e.g. keep last 7 daily, 4 weekly) per site policy.
#
# Never restore into production directly; use deploy/scripts/restore.sh into
# an isolated destination.
