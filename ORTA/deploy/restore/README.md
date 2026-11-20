# ORTA restore directory
#
# Isolated restore destination used by deploy/scripts/restore.sh.
# Restored Postgres SQL + config are staged here for validation against a
# test ORTA instance before any production cutover.
#
# Production data is NEVER written to or overwritten from this directory.
