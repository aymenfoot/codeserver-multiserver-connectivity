# ORTA Docker Compose usage
#
# Prerequisites (target server): Docker Engine 24+, Docker Compose v2.
#
# 1. cp deploy/env/env.example .env   # edit .env with real secrets
# 2. bash deploy/scripts/verify-config.sh
# 3. bash deploy/scripts/deploy.sh
# 4. bash deploy/scripts/healthcheck.sh
#
# Services publish only to localhost (127.0.0.1). Place a reverse proxy
# (nginx/traefik) in front of the UI port (3000) for external access.
#
# Pinned versions: see docs/UPSTREAM-VERSION-MATRIX.md
#
# CROWler is NOT included (no official verifiable repository). When an
# official CROWler image is identified, add it to this compose file and the
# version matrix, then wire it into the Bridge discovery pipeline.
