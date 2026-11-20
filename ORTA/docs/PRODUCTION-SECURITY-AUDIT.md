# ORTA Production Security Audit Report

**Target Server:** 83.136.252.133 (ORTA)
**UUID:** 0067b314-c1d0-4415-b059-74495ae664bd
**Audit Date:** 2026-11-20
**Audit Method:** SSH via ORTA GitHub Actions Bridge (port 443, strict host-key verification)
**Bridge Repository:** https://github.com/aymenfoot/orta-bridge

---

## Executive Summary

**The target server has critical security deficiencies.** No ORTA-specific security configuration exists because no ORTA services are deployed. The base server has no firewall, permits root login via SSH, and may allow password authentication. These issues must be remediated before any ORTA components are deployed.

---

## 1. Authentication and Authorization

| Item | Value | Status | Risk |
|------|-------|--------|------|
| SSH service | active | Verified | — |
| SSH ports | 22, 443 | Verified | Both exposed to all interfaces |
| PermitRootLogin | `yes` | **SECURITY RISK** | Root can log in directly |
| PasswordAuthentication | Not explicitly set (default: yes) | **POTENTIAL RISK** | Password-based SSH may be allowed |
| PubkeyAuthentication | Not explicitly set | UNVERIFIED | Cannot confirm public key auth is enforced |
| X11Forwarding | `yes` | **UNNECESSARY** | X11 forwarding on a server is not required |

**Finding:** Root login is permitted via SSH. No explicit confirmation that public-key-only authentication is enforced. Password authentication may be active by default on Ubuntu.

---

## 2. Network Exposure

### Listening Ports (All Interfaces)
| Port | Interface | Process | Exposure | Risk |
|------|-----------|---------|----------|------|
| 22/tcp | 0.0.0.0, [::] | sshd | Public internet | SSH exposed globally |
| 443/tcp | 0.0.0.0, [::] | sshd | Public internet | SSH on HTTPS port exposed globally |
| 53/tcp | 127.0.0.54, 127.0.0.53 | systemd-resolve | Localhost only | Acceptable (local only) |

**Finding:** SSH is exposed on both ports 22 and 443 to all network interfaces (0.0.0.0 and [::]). There is no firewall restricting access to specific IP ranges.

---

## 3. Firewall Configuration

| Item | Value | Status | Risk |
|------|-------|--------|------|
| UFW | `Status: inactive` | **NOT CONFIGURED** | All ports open to public internet |
| Firewall rules | None | **NOT CONFIGURED** | No port filtering |

**Finding:** UFW (Uncomplicated Firewall) is installed but inactive. No firewall rules are in place. All server ports are accessible from the public internet.

---

## 4. Database and Internal Service Exposure

| Service | Installed | Listening Port | Exposure |
|---------|-----------|----------------|----------|
| PostgreSQL | NOT INSTALLED | N/A | N/A |
| Redis | NOT INSTALLED | N/A | N/A |
| ORTA Core | NOT DEPLOYED | N/A | N/A |
| ORTA Bridge | NOT DEPLOYED | N/A | N/A |
| ORTA UI | NOT DEPLOYED | N/A | N/A |
| SearXNG | NOT DEPLOYED | N/A | N/A |
| RAGFlow | NOT DEPLOYED | N/A | N/A |

**Finding:** No databases or internal services are installed. No exposure risk exists for ORTA services because none are deployed.

---

## 5. Secrets and Environment Variables

| Item | Status | Evidence |
|------|--------|----------|
| ORTA environment variables | NOT CONFIGURED | No ORTA deployment exists |
| Secret files | NOT FOUND | No `/opt/orta/secrets/` or similar |
| GitHub Secrets (bridge repo) | CONFIGURED | ORTA_SSH_PRIVATE_KEY, ORTA_SSH_HOST, ORTA_SSH_USER, ORTA_BOOTSTRAP_PORT, ORTA_SSH_PORT |
| Private key exposure | NONE | Private key never logged or printed |

**Finding:** No ORTA secrets exist on the server because ORTA is not deployed. The GitHub repository secrets are properly configured (private key, host, user, ports) and were never exposed in logs or reports.

---

## 6. Default Credentials

| Item | Status | Evidence |
|------|--------|----------|
| Default database credentials | N/A | No database installed |
| Default admin credentials | N/A | No ORTA application deployed |
| Default SSH credentials | Password auth possibly enabled | Ubuntu default may allow password auth |

**Finding:** No application default credentials exist because no applications are deployed. SSH password authentication status is unconfirmed but likely enabled by default on Ubuntu.

---

## 7. API Access Controls

| API | Deployed | Authentication | Authorization |
|-----|----------|---------------|---------------|
| ORTA Core API | NOT DEPLOYED | N/A | N/A |
| ORTA Bridge API | NOT DEPLOYED | N/A | N/A |
| ORTA UI API | NOT DEPLOYED | N/A | N/A |
| SearXNG API | NOT DEPLOYED | N/A | N/A |
| RAGFlow API | NOT DEPLOYED | N/A | N/A |

**Finding:** No APIs are deployed. No API access controls exist because no services are running.

---

## 8. HTTPS and Reverse Proxy

| Item | Status | Evidence |
|------|--------|----------|
| HTTPS termination | NOT CONFIGURED | No web server installed |
| Reverse proxy | NOT CONFIGURED | No nginx, traefik, or similar |
| SSL/TLS certificates | NOT FOUND | No certificates on server |
| Port 443 usage | SSH only | Port 443 is used for SSH, not HTTPS |

**Finding:** No HTTPS or reverse proxy is configured. Port 443 is used for SSH access, not web traffic. No SSL/TLS certificates exist.

---

## 9. Firewall Rules (Detailed)

| Chain | Policy | Rules | Status |
|-------|--------|-------|--------|
| UFW | inactive | None | **ALL TRAFFIC ALLOWED** |

**Finding:** No firewall rules exist. The server accepts all incoming connections on all ports.

---

## 10. Logs for Secret Exposure

| Log Location | Status | Secret Exposure Found |
|--------------|--------|----------------------|
| `/var/log/auth.log` | Exists (58 KB) | No ORTA secrets (ORTA not deployed) |
| `/var/log/syslog` | Exists (334 KB) | No ORTA secrets |
| `/var/log/kern.log` | Exists (86 KB) | No ORTA secrets |
| systemd journal | 8 MB total | No ORTA secrets |

**Finding:** No secret exposure in logs because no ORTA services or secrets exist on the server.

---

## Security Deficiency Summary

| # | Deficiency | Severity | Evidence |
|---|------------|----------|----------|
| 1 | No firewall (UFW inactive) | HIGH | `ufw status verbose` → `Status: inactive` |
| 2 | Root SSH login permitted | MEDIUM | `PermitRootLogin yes` in sshd_config |
| 3 | Password auth possibly enabled | MEDIUM | Ubuntu default; not explicitly disabled |
| 4 | SSH exposed on ports 22 and 443 to all interfaces | MEDIUM | `ss -tlnp` shows 0.0.0.0:22 and 0.0.0.0:443 |
| 5 | X11 forwarding enabled | LOW | `X11Forwarding yes` in sshd_config |
| 6 | No HTTPS/reverse proxy | LOW | No web server installed |
| 7 | No swap file | LOW | `swapon --show` → empty |
| 8 | No ORTA-specific security config | HIGH | No ORTA services deployed |

---

## Security Remediation Requirements (Before ORTA Deployment)

1. **Enable UFW** with restrictive rules: allow only SSH (22, 443) from trusted IPs, block all other incoming traffic
2. **Disable root login:** Set `PermitRootLogin no` in sshd_config
3. **Disable password authentication:** Set `PasswordAuthentication no` in sshd_config
4. **Disable X11 forwarding:** Set `X11Forwarding no` in sshd_config
5. **Add swap file:** 2-4 GiB to prevent OOM kills
6. **Configure ORTA secrets** in `/opt/orta/secrets/` with restricted permissions (600)
7. **Configure ORTA API authentication** before deploying Core/Bridge/UI
8. **Set up reverse proxy** with TLS termination for UI access

**Security Status: NOT SECURE — Cannot proceed to production deployment until remediated.**
