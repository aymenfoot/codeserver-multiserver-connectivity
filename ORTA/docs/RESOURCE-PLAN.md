# ORTA Resource Plan

Server inspection performed 2026-11-20. All constraints are real and must govern
concurrency, storage, and retention configuration.

## 1. Actual server inspection

| Item | Value |
|------|-------|
| Hostname | 75bd0b422def |
| OS | Debian GNU/Linux 13 (trixie), Linux 7.0.0-43-generic x86_64 |
| CPU | 4 cores |
| RAM | 7.7 GiB total / ~4.7 GiB available |
| Swap | 0 B |
| Root disk | 40 G total, 6.2 G available (84% used) |
| Docker | NOT installed (`docker: command not found`) |
| Docker binaries | present at `/home/coder/workspace/docker-29.10.0.tgz` + `/home/coder/workspace/docker/` |
| Docker Compose | not installed |
| User | `coder` (uid 1000), no sudo, no root |
| /home/codeuser | does not exist — ORTA located at `/home/coder/workspace/ORTA/` (deviation documented) |
| Internet | available (github.com, api.github.com, deb.debian.org reachable) |
| User namespaces | `unprivileged_userns_clone=1`, `max_user_namespaces=26019`, BUT `unshare -U` |
|  | fails with "Operation not permitted" — unprivileged containers blocked by runtime |
| Existing ports/services | none listening (ss empty) |

### Infrastructure blocker (recorded, not worked around silently)

Docker Engine cannot be run in this environment:
- No root/sudo access to install Docker daemon or setuid `newuidmap`/`newgidmap`.
- Docker rootless mode requires `newuidmap`/`newgidmap` (setuid root) and
  `rootlesskit`/`slirp4netns`/`fuse-overlayfs`; unprivileged user namespaces are
  blocked (`unshare -U` → Operation not permitted).
- `apt-get update/install` blocked (cannot write `/var/lib/apt/lists`, no root).

Consequence: the three upstream projects (SearXNG, RAGFlow) are Docker-native and cannot
be deployed as containers here. RAGFlow v1.0.0 has no native install. SearXNG is
Docker-native (though runnable as a Python app, the official distribution is Docker).
This is an honest deployment constraint; the architecture below is the **target-state**
design, and the parts buildable natively (ORTA Core, Bridge, Unified UI) are specified as
native Python services.

## 2. Resource requirements (target-state estimates)

| Component | CPU | RAM | Disk | Notes |
|-----------|-----|-----|------|-------|
| SearXNG | 0.25–0.5 | 256–512 MiB | 2–5 GiB cache | standalone |
| RAGFlow (full) | 2–4 | 4–8 GiB | 10–30 GiB | MySQL+Valkey+Kvrocks+MinIO+ES+sandbox — EXCEEDS available RAM |
| ORTA Core (Python) | 0.5–1 | 512 MiB–1 GiB | 2–5 GiB | PostgreSQL + app |
| ORTA Bridge (Python) | 0.25–0.5 | 256–512 MiB | 1–2 GiB | job state + temp |
| ORTA Unified UI | 0.25–0.5 | 256–512 MiB | 0.5–1 GiB | frontend + API gateway |
| Databases (PostgreSQL/Redis) | 0.5 | 512 MiB–1 GiB | 5–10 GiB | shared |
| **Total target** | **~4–7** | **~7–14 GiB** | **~20–50 GiB** | **exceeds this server** |

## 3. Sensible limits for this environment

Given 4 CPU / ~4.7 GiB available / 6.2 GiB disk, a full multi-service deployment cannot
run concurrently. Limits:

- **Concurrency:** ORTA Core/Bridge workers capped at 2 concurrent jobs; SearXNG/crawler
  concurrency capped at 2–4; no parallel RAGFlow indexing (not deployable here).
- **Storage:** ORTA data root capped at ~4 GiB of the 6.2 GiB free; retention 30 days;
  rotate logs and temp job artifacts daily.
- **Retention:** evidence/documents 90 days; job state 30 days; crawl logs 14 days.
- **Rate limiting:** per-source crawl delay default 2s; SearXNG queries rate-limited to
  1–2/sec internally.
- **No large image pulls:** avoid pulling multi-GB Docker images (not possible without
  Docker anyway).

## 4. Storage layout (ORTA root: /home/coder/workspace/ORTA)

```
ORTA/
  docs/            architecture & research docs
  config/          service configs (non-secret)
  secrets/         encrypted/runtime secrets (gitignored)
  compose/         target-state compose files (reference; not runnable here)
  core/            ORTA Intelligence Core (Python service)
  bridge/          ORTA Bridge (Python service)
  ui/              ORTA Unified UI (web frontend)
  pipeline/        data pipeline orchestration
  storage/         persistent runtime volumes (evidence, jobs, uploads)
  scripts/         ops, backup, health-check scripts
  tests/           integration & acceptance tests
```

## 5. Networking plan

| Network | Purpose | Exposure |
|---------|---------|----------|
| `orta-internal` | service-to-service (Core, Bridge, DB, Redis) | internal only |
| `orta-frontend` | Unified UI + public API gateway | published ports |
| Upstream (SearXNG/RAGFlow) | target-state, internal-only | not publicly exposed |

Internal databases and admin services are never published to the host/public network.

## 6. Ports (target-state)

| Service | Internal port | Published | Binding |
|---------|---------------|-----------|---------|
| ORTA Core API | 8000 | 127.0.0.1:8000 | localhost only |
| ORTA Bridge API | 8001 | 127.0.0.1:8001 | localhost only |
| ORTA Unified UI | 3000 | 127.0.0.1:3000 | localhost only |
| PostgreSQL | 5432 | internal | internal network |
| Redis | 6379 | internal | internal network |
| SearXNG (target) | 8080 | internal | internal network |
| RAGFlow (target) | 80/9380 | internal | internal network |
