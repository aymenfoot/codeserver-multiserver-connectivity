# ORTA Target Server Requirements

Minimum and recommended requirements for the separate production server.

## A. Minimum requirements

| Resource | Minimum | Notes |
|----------|---------|-------|
| OS | Linux amd64 | Debian/Ubuntu/RHEL-like |
| CPU | 4 cores | RAGFlow alone needs ~4 |
| RAM | 8 GiB | Full stack needs more |
| Disk | 50 GiB | RAGFlow + Postgres + MinIO + logs |
| Docker | Engine 24+ | daemon + root or docker group |
| Docker Compose | v2 | `docker compose` plugin |
| Network | outbound internet | for image pulls (pinned tags) |

## B. Recommended requirements

| Resource | Recommended | Notes |
|----------|-------------|-------|
| CPU | 8+ cores | concurrent crawling + indexing |
| RAM | 16+ GiB | RAGFlow + companions + ORTA |
| Disk | 100+ GiB | document/index growth, backups |
| Network | outbound internet + internal | image pulls, SearXNG/RAGFlow |

## C. Per-component resource notes
- RAGFlow (official): 4 CPU / 16 GB RAM / 50 GiB starting config — dominant consumer.
- SearXNG: ~0.5 CPU / 512 MiB RAM.
- ORTA Core + Bridge + UI: ~1.5 CPU / 2 GB RAM combined.
- PostgreSQL + Redis: ~1 CPU / 1.5 GB RAM.

## D. Build-host vs target (NOT the same)
The build/preparation host (4 CPU, 7.7 GB RAM, 6 GiB free, no Docker daemon, no root) **cannot** run the full ORTA stack. Deployment targets a separate server meeting the above. Do not attempt production deployment on the build host.

## E. Required capabilities on target
- Docker socket access (for RAGFlow sandbox parsing).
- Ability to pull images from Docker Hub (searxng, infiniflow/ragflow, postgres, redis, minio, elasticsearch, kvrocks).
- Persistent volume storage (Docker volumes or bind mounts).
- Reverse proxy (optional, for external UI access + TLS).
