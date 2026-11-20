# ORTA Target Server Audit

**Target Server:** 83.136.252.133
**Hostname:** ubuntu-2cpu-4gb-uk-lon1
**Machine ID:** 0067b314c1d04415b05974495ae664bd
**Audit Date:** 2026-11-20
**Audit Method:** SSH via ORTA GitHub Actions Bridge (port 443, strict host-key verification)
**Bridge Repository:** https://github.com/aymenfoot/orta-bridge

---

## 1. Server Identity Verification

| Field | Value | Verified |
|-------|-------|----------|
| Public IP | 83.136.252.133 | Yes |
| Private IP | 10.2.0.126 | Yes |
| IPv6 | 2a04:3541:1000:500:608a:22ff:fe5a:2559 | Yes |
| Hostname | ubuntu-2cpu-4gb-uk-lon1 | Yes |
| OS | Ubuntu 26.04.1 LTS (Resolute Raccoon) | Yes |
| OS ID | ubuntu | Yes |
| Version ID | 26.04 | Yes |
| Kernel | 7.0.0-43-generic | Yes |
| Architecture | x86_64 | Yes |
| Machine ID | 0067b314c1d04415b05974495ae664bd | Matches expected UUID |
| Current User | root (uid=0) | Yes |
| Sudo Access | OK | Yes |
| Uptime | 1 hour | Yes |
| SSH Ports | 22/tcp, 443/tcp | Yes |

**Conclusion:** The target server identity matches the expected configuration. IP 83.136.252.133, machine ID matches expected UUID 0067b314-c1d0-4415-b059-74495ae664bd.

---

## 2. Full Resource Audit

### CPU
| Item | Value |
|------|-------|
| Architecture | x86_64 |
| Vendor ID | AuthenticAMD |
| Model | AMD EPYC 9575F 64-Core Processor |
| CPU(s) | 2 |
| Thread(s) per core | 1 |
| Core(s) per socket | 2 |
| Socket(s) | 1 |
| Hypervisor | KVM (full virtualization) |

### RAM
| Item | Value |
|------|-------|
| Total | 3.8 GiB |
| Used | 543 MiB |
| Free | 2.9 GiB |
| Available | 3.2 GiB |
| Buffers/cache | 609 MiB |

### Swap
| Item | Value |
|------|-------|
| Configured | None (0B) before audit |
| After audit | 2 GiB swapfile added |

### Disk
| Item | Value |
|------|-------|
| Physical disk | 260 GiB |
| Disklabel | GPT |
| Root filesystem | /dev/vda2 (ext4) |
| Root filesystem size | 256 GiB |
| Used | 3.0 GiB (2%) |
| Available | 243 GiB |
| Free space | 243 GiB |

### Inodes
| Item | Value |
|------|-------|
| Total | 17,006,080 |
| Used | 110,143 (1%) |
| Available | 16,895,937 |

### Block Devices
| Device | Size | Type | Mountpoint |
|--------|------|------|------------|
| /dev/vda | 260G | disk | - |
| /dev/vda1 | 1M | part | (BIOS boot) |
| /dev/vda2 | 260G | part | / |

### Network
| Port | Interface | Process | Exposure |
|------|-----------|---------|----------|
| 22/tcp | 0.0.0.0, [::] | sshd | Public |
| 443/tcp | 0.0.0.0, [::] | sshd | Public |
| 53/tcp | 127.0.0.54, 127.0.0.53 | systemd-resolve | Localhost only |

### Docker and Container Runtime
| Item | Value |
|------|-------|
| Docker Engine | NOT INSTALLED |
| Docker Compose | NOT INSTALLED |
| Docker daemon | Not running |

### Databases
| Item | Value |
|------|-------|
| PostgreSQL | NOT INSTALLED (`psql: command not found`) |
| Redis | NOT INSTALLED (`redis-cli: command not found`) |

### Running System Services (20 total)
acpid, chrony, cron, dbus, getty@tty1, ModemManager, multipathd, networkd-dispatcher, polkit, rsyslog, ssh, systemd-journald, systemd-logind, systemd-networkd, systemd-resolved, systemd-udevd, udisks2, unattended-upgrades, upower, user@0

### Failed Services
0 failed services

---

## 3. Resource Allocation Plan for ORTA

| Component | RAM | Disk | Notes |
|-----------|-----|------|-------|
| ORTA Core (Python/FastAPI) | 256-512 MiB | 2-5 GiB | Python service |
| ORTA Bridge (Python/FastAPI) | 256-512 MiB | 1-2 GiB | Python service |
| ORTA Unified UI (Python/FastAPI) | 256-512 MiB | 0.5-1 GiB | Python service |
| PostgreSQL | 512 MiB-1 GiB | 5-10 GiB | Production database |
| Redis | 256-512 MiB | 1-2 GiB | Cache and job queue |
| SearXNG (Docker) | 256-512 MiB | 2-5 GiB | Metasearch provider |
| RAGFlow + companions (Docker) | 4-8 GiB | 10-30 GiB | Document processing (MySQL, Kvrocks, MinIO, Elasticsearch, sandbox) |
| Docker overhead | ~512 MiB | 10-20 GiB | Images and container storage |
| Logs and backups | - | 10-20 GiB | Log rotation, backup retention |
| **Total estimated** | **~8-16 GiB** | **~50-80 GiB** | **Exceeds available RAM (3.8 GiB)** |

**Resource Warning:** The full ORTA stack with all upstream components requires approximately 8-16 GiB RAM, but this server has only 3.8 GiB total. Deployment will require careful concurrency limits and may not be able to run all components simultaneously. RAGFlow alone recommends 4 CPU / 16 GB RAM, which exceeds this server's capacity.

---

## 4. Storage Preparation Plan

### Directory Structure (/opt/orta/)
```
/opt/orta/
├── app/            # Application source code
├── config/         # Service configuration templates
├── secrets/        # Encrypted/runtime secrets (700 permissions)
├── logs/           # Application logs
├── backups/        # Database and file backups
├── data/           # Persistent application data
├── postgres/       # PostgreSQL data volume
├── redis/          # Redis data volume
├── minio/          | MinIO object storage data
└── elasticsearch/  # Elasticsearch data volume
```

### Docker Volume Strategy
- Docker data stored in /var/lib/docker/ (default)
- PostgreSQL data mapped to /opt/orta/postgres/
- Redis data mapped to /opt/orta/redis/
- MinIO data mapped to /opt/orta/minio/
- Elasticsearch data mapped to /opt/orta/elasticsearch/
- Application logs mapped to /opt/orta/logs/
- Backups stored in /opt/orta/backups/

### Retention Policies
- Application logs: Rotate daily, keep 7 days
- Docker logs: Rotate at 100MB, keep 5 files
- Backups: Keep 7 daily, 4 weekly
- Temporary files: Cleaned on container restart

---

## 5. Safe Cleanup Results

| Category | Before | After | Action |
|----------|--------|-------|--------|
| Root disk used | 3.0 GiB | 3.0 GiB | No cleanup needed (fresh server) |
| Swap | 0B | 2 GiB | Added swapfile |
| ORTA directories | None | Created | /opt/orta/ structure created |

No user data, application data, or database files were deleted. No Docker volumes were pruned. No indiscriminate filesystem cleanup was performed.

---

## 6. Security Hardening Results

### Firewall (UFW)
| Setting | Before | After |
|---------|--------|-------|
| Status | inactive | active |
| Default incoming | allow | deny |
| Default outgoing | allow | allow |
| Port 22/tcp | open | ALLOW IN |
| Port 443/tcp | open | ALLOW IN |
| Port 80/tcp | open | ALLOW IN |

### SSH Configuration
| Setting | Before | After |
|---------|--------|-------|
| PermitRootLogin | yes | yes (only admin account) |
| KbdInteractiveAuthentication | no | no |
| UsePAM | yes | yes |
| X11Forwarding | yes | **no** |
| PrintMotd | no | no |
| Backup created | No | Yes (/etc/ssh/sshd_config.bak.<timestamp>) |

### Security Deficiencies Remaining
| Item | Risk | Mitigation |
|------|------|------------|
| Root SSH login permitted | MEDIUM | Only admin account; consider creating dedicated admin user |
| Password authentication possibly enabled | MEDIUM | Verify key-based auth, then disable password auth |
| No ORTA-specific security config | HIGH | Not yet deployed |

---

## 7. Access and Recovery

### SSH Access
- Port: 22/tcp and 443/tcp
- Authentication: Public key (id_ed25519_new_project)
- Admin account: root (uid=0)
- Backup config: /etc/ssh/sshd_config.bak.<timestamp>

### Recovery Procedures
- If SSH access is lost: Use UpCloud console (not available in this environment)
- If UFW blocks SSH: Connect via alternative method and disable UFW
- If sshd_config is broken: Restore from /etc/ssh/sshd_config.bak.*

### Access Recovery Contact
- Repository: https://github.com/aymenfoot/orta-bridge
- Bridge tool: /home/coder/workspace/orta-bridge

---

## 8. Conclusion

The target server is a clean Ubuntu 26.04.1 LTS installation with:
- 2 CPU cores, 3.8 GiB RAM, 260 GiB disk (243 GiB available)
- SSH access on ports 22 and 443
- No Docker, no databases, no ORTA components installed
- UFW firewall now active with ports 22, 443, 80 allowed
- 2 GiB swap file added
- /opt/orta/ directory structure created
- X11Forwarding disabled in SSH config

The server is ready for Docker installation and ORTA deployment.
