# ORTA Target Server Security Hardening

**Target Server:** 83.136.252.133
**Hardening Date:** 2026-11-20
**Audit Source:** TARGET-SERVER-AUDIT.md

---

## 1. Security Findings Before Hardening

| Item | Before | Risk Level |
|------|--------|------------|
| UFW Firewall | inactive | HIGH - all ports open |
| PermitRootLogin | yes | MEDIUM - root can log in directly |
| X11Forwarding | yes | LOW - unnecessary on server |
| PasswordAuthentication | Not explicitly set (default yes) | MEDIUM - password auth may be active |
| PubkeyAuthentication | Not explicitly set | UNVERIFIED |
| Listening ports | 22, 443 (all interfaces), 53 (localhost) | SSH exposed globally |

---

## 2. Security Hardening Applied

### 2.1 Firewall (UFW)

| Setting | Before | After |
|---------|--------|-------|
| Status | inactive | active |
| Default incoming | allow | deny |
| Default outgoing | allow | allow |
| Port 22/tcp | open | ALLOW IN |
| Port 443/tcp | open | ALLOW IN |
| Port 80/tcp | open | ALLOW IN |

**Commands executed:**
```bash
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp
ufw allow 443/tcp
ufw allow 80/tcp
ufw --force enable
```

**Result:** Firewall is active and enabled on system startup. Ports 22, 443, and 80 are allowed for incoming traffic. All other incoming ports are denied.

---

### 2.2 SSH Configuration

| Setting | Before | After |
|---------|--------|-------|
| X11Forwarding | yes | no |
| PermitRootLogin | yes | yes (unchanged) |
| KbdInteractiveAuthentication | no | no |
| UsePAM | yes | yes |
| PrintMotd | no | no |

**Backup created:** /etc/ssh/sshd_config.bak.<timestamp>

**Commands executed:**
```bash
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%s)
sed -i 's/^X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config
systemctl restart ssh
```

**Verification:** SSH service is active after restart. SSH connectivity verified on ports 22 and 443.

---

## 3. Security Decisions Deferred (Owner Approval Required)

The following security changes were NOT applied because they require owner approval or could lock the owner out:

| Item | Current Value | Recommended | Reason for Deferral |
|------|-------------|-------------|---------------------|
| PermitRootLogin | yes | no | Root is the only admin account; disabling could lock owner out |
| PasswordAuthentication | Not explicitly set (likely yes) | no | Key-based access verified, but owner needs reliable recovery route first |
| X11Forwarding | no | no | Already applied |

### SSH Safety Procedure Followed
1. **Identified authorized administrative account:** root (uid=0, the only account with sudo)
2. **Verified sudo permissions:** sudo -n returns OK
3. **Verified working SSH key:** id_ed25519_new_project connects successfully
4. **Tested second independent SSH session:** Multiple bridge connections succeeded before and after changes
5. **Confirmed owner can still access:** SSH connectivity verified after each change

---

## 6. Additional Security Measures Applied

| Measure | Status | Details |
|---------|--------|---------|
| SSH config backup | Applied | /etc/ssh/sshd_config.bak.<timestamp> |
| UFW firewall | Applied | Deny incoming, allow outgoing, ports 22/443/80 |
| Swap file | Applied | 2 GiB swapfile at /swapfile |
| Secrets directory | Created | /opt/orta/secrets/ (700 permissions) |

---

## 7. Remaining Security Recommendations (Owner Action Required)

1. **Create dedicated admin user:** Create a non-root sudo user for daily administration
2. **Disable root SSH login:** Set PermitRootLogin no after creating admin user
3. **Disable password authentication:** Set PasswordAuthentication no after verifying key-based access for admin user
4. **Configure ORTA secrets:** Store API keys and database passwords in /opt/orta/secrets/ with 600 permissions
5. **Configure ORTA authentication:** Implement session/JWT auth for Core and Bridge APIs
6. **Configure HTTPS:** Set up reverse proxy with TLS termination for UI access
7. **Install security updates:** Run unattended-upgrades or manual apt upgrade
8. **Configure fail2ban:** Protect SSH from brute-force attacks

---

## 8. Access and Recovery Procedures

### SSH Access Details
- Primary port: 22/tcp
- Secondary port: 443/tcp
- Authentication: Public key (id_ed25519_new_project)
- Admin account: root (uid=0)

### Recovery if SSH Access is Lost
1. **SSH key not working:** Use alternative access method (if available via hosting provider)
2. **UFW blocking SSH:** Connect via alternative method and run `ufw disable`
3. **sshd_config broken:** Restore from /etc/ssh/sshd_config.bak.<timestamp>
4. **SSH service down:** Connect via alternative method and run `systemctl restart ssh`

### SSH Config Backup Locations
- /etc/ssh/sshd_config.bak.<timestamp> (created during hardening)

### Bridge Tool for Remote Access
- Tool: /home/coder/workspace/orta-bridge
- Repository: https://github.com/aymenfoot/orta-bridge
- Repository secrets: ORTA_SSH_PRIVATE_KEY, ORTA_SSH_HOST, ORTA_SSH_USER, ORTA_BOOTSTRAP_PORT, ORTA_SSH_PORT
