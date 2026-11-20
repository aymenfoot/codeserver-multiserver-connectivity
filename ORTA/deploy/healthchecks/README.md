# ORTA health checks
#
# Per-service health check definitions (also declared in docker-compose.yml):
#
#   ORTA Core   : GET http://localhost:8000/healthz        (DB ok)
#   ORTA Bridge : GET http://localhost:8001/healthz        (DB ok + Core reachable)
#   ORTA UI     : GET http://localhost:3000/
#   SearXNG     : GET http://localhost:8080/healthz        (returns "OK")
#   RAGFlow     : GET http://localhost:9380/api/v1/system/healthz (200)
#   Postgres    : pg_isready -U orta -d orta
#   Redis       : redis-cli -a <pass> ping
#
# Run: bash deploy/scripts/healthcheck.sh
#
# Unhealthy services are restarted by Docker (restart: unless-stopped).
# Bridge dead-letter and failed jobs are surfaced in the UI Processing Jobs
# and System Health sections.
