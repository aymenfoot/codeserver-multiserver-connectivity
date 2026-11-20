# ORTA Target Server Storage Plan

**Target Server:** 83.136.252.133
**Audit Date:** 2026-11-20

---

## 1. Current Storage State

| Metric | Value |
|--------|-------|
| Physical disk | 260 GiB |
| Disklabel | GPT |
| Root filesystem | /dev/vda2 (ext4) |
| Root filesystem size | 256 GiB |
| Used | 3.0 GiB (2%) |
| Available | 243 GiB |
| Total inodes | 17,006,080 |
| Used inodes | 110,143 (1%) |
| Available inodes | 16,895,937 |

### Block Device Layout
| Device | Size | Type | Mountpoint |
|--------|------|------|------------|
| /dev/vda | 260G | disk | - |
| /dev/vda1 | 1M | part | BIOS boot |
| /dev/vda2 | 260G | part | / |

---

## 2. Persistent Storage Layout

All persistent data is stored under `/opt/orta/`:

```
/opt/orta/
├── app/            # Application source code (deployed from Git)
├── config/         # Service configuration templates
├── secrets/        # Encrypted/runtime secrets (700 permissions)
├── logs/           # Application logs (rotated daily, keep 7 days)
├── backups/        # Database and file backups (keep 7 daily, 4 weekly)
├── data/           # Persistent application data
├── postgres/       # PostgreSQL data volume
├── redis/          # Redis data volume
├── minio/          # MinIO object storage data
└── elasticsearch/  # Elasticsearch data volume
```

### Directory Permissions
| Directory | Owner | Permissions | Purpose |
|-----------|-------|-------------|---------|
| /opt/orta/ | root | 755 | Root application directory |
| /opt/orta/app/ | root | 755 | Application source code |
| /opt/orta/config/ | root | 755 | Service configuration templates |
| /opt/orta/secrets/ | root | 700 | Encrypted/runtime secrets |
| /opt/orta/logs/ | root | 755 | Application logs |
| /opt/orta/backups/ | root | 750 | Database and file backups |
| /opt/orta/data/ | root | 755 | Persistent application data |
| /opt/orta/postgres/ | root | 700 | PostgreSQL data volume |
| /opt/orta/redis/ | root | 700 | Redis data volume |
| /opt/orta/minio/ | root | 700 | MinIO object storage data |
| /opt/orta/elasticsearch/ | root | 700 | Elasticsearch data volume |

---

## 3. Docker Volume Strategy

Docker data is stored in the default location `/var/lib/docker/`. The following bind mounts map host directories to container volumes:

| Container | Host Path | Container Path | Purpose |
|-----------|-----------|----------------|---------|
| PostgreSQL | /opt/orta/postgres/ | /var/lib/postgresql/data | Database persistence |
| Redis | /opt/orta/redis/ | /data | Cache and queue persistence |
| MinIO | /opt/orta/minio/ | /data | Object storage |
| Elasticsearch | /opt/orta/elasticsearch/ | /usr/share/elasticsearch/data | Index persistence |
| ORTA Core | /opt/orta/logs/ | /app/logs | Application logs |
| ORTA Bridge | /opt/orta/logs/ | /app/logs | Application logs |
| ORTA UI | /opt/orta/logs/ | /app/logs | Application logs |

**Policy:** No important persistent data is stored in disposable container layers. All persistent data is stored in bind-mounted host directories under /opt/orta/.

---

## 4. Resource Allocation by Component

| Component | RAM | Disk | Justification |
|-----------|-----|------|---------------|
| ORTA Core | 256-512 MiB | 2-5 GiB | Python/FastAPI application |
| ORTA Bridge | 256-512 MiB | 1-2 GiB | Python/FastAPI application |
| ORTA Unified UI | 256-512 MiB | 0.5-1 GiB | Python/FastAPI application |
| PostgreSQL | 512 MiB-1 GiB | 5-10 GiB | Production database |
| Redis | 256-512 MiB | 1-2 GiB | Cache and job queue |
| SearXNG | 256-512 MiB | 2-5 GiB | Metasearch provider |
| RAGFlow + companions | 4-8 GiB | 10-30 GiB | Document processing (heaviest component) |
| Docker images | ~1 GiB | 10-20 GiB | Image layers |
| Logs | - | 5-10 GiB | Rotated daily |
| Backups | - | 10-20 GiB | 7 daily, 4 weekly |
| **Total estimated** | **~8-16 GiB** | **~50-80 GiB** | |

**Resource Warning:** The full ORTA stack with all upstream components requires approximately 8-16 GiB RAM, but this server has only 3.8 GiB total. Deployment will require careful concurrency limits and may not be able to run all components simultaneously. RAGFlow alone recommends 4 CPU / 16 GB RAM, which exceeds this server's capacity.

---

## 5. Log Rotation and Retention Policies

| Log Type | Rotation | Retention | Max Size |
|----------|----------|-----------|----------|
| Application logs | Daily | 7 days | 100 MB per file |
| Docker container logs | Daily | 5 files | 100 MB per file |
| System logs | Weekly | 4 weeks | System default |
| Database backups | Daily | 7 daily, 4 weekly | Unlimited (disk permitting) |
| ORTA temporary files | On container restart | N/A | Cleaned on restart |

---

## 6. Disk Growth Prevention

| Measure | Implementation |
|---------|----------------|
| Log rotation | logrotate for application logs |
| Docker log rotation | --log-opt max-size=100m --log-opt max-file=5 |
| Backup retention | 7 daily, 4 weekly backups |
| Temporary file cleanup | Cleaned on container restart |
| Disk usage monitoring | Alert at 80% disk usage |

---

## 7. Before/After Storage Measurements

| Measurement | Before | After | Change |
|-------------|--------|-------|--------|
| Root disk used | 3.0 GiB | 3.0 GiB | None |
| Available space | 243 GiB | 243 GiB | None |
| Swap | 0B | 2 GiB | +2 GiB |
| ORTA directories | None | Created | +10 directories |

No user data, application data, or database files were deleted. No Docker volumes were pruned. No indiscriminate filesystem cleanup was performed.
