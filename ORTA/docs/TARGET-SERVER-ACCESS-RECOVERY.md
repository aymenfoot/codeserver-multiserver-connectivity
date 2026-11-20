# ORTA Target Server Access and Recovery

**Target Server:** 83.136.252.133
**Hostname:** ubuntu-2cpu-4gb-uk-lon1
**Machine ID:** 0067b314c1d04415b05974495ae664bd
**Document Date:** 2026-11-20

---

## 1. Authorized Administrative Access

### SSH Access Details
| Item | Value |
|------|-------|
| Primary IP | 83.136.252.133 |
| Private IP | 10.2.0.126 |
| SSH Port 1 | 22/tcp |
| SSH Port 2 | 443/tcp |
| Admin Account | root (uid=0) |
| Authentication | Public key (id_ed25519_new_project) |
| Key Fingerprint | SHA256:rTm6Fc+kw8UZMp6xMV8RKqupbaDURgDgHoD6GhFHh5k |
| Key Comment | new-project-deploy |

### Bridge Tool Access
| Item | Value |
|------|-------|
| Tool Path | /home/coder/workspace/orta-bridge |
| Repository | https://github.com/aymenfoot/orta-bridge |
| Repository Secrets | ORTA_SSH_PRIVATE_KEY, ORTA_SSH_HOST, ORTA_SSH_USER, ORTA_BOOTSTRAP_PORT, ORTA_SSH_PORT |

### Verified Access Methods
| Method | Status | Last Verified |
|--------|--------|---------------|
| SSH port 22 via bridge | Verified | 2026-11-20 |
| SSH port 443 via bridge | Verified | 2026-11-20 |
| Remote command execution | Verified | 2026-11-20 |

---

## 2. SSH Configuration

### Current sshd_config Settings
| Setting | Value |
|---------|-------|
| Include | /etc/ssh/sshd_config.d/*.conf |
| PermitRootLogin | yes |
| KbdInteractiveAuthentication | no |
| UsePAM | yes |
| X11Forwarding | no |
| PrintMotd | no |
| AcceptEnv | LANG LC_* COLORTERM NO_COLOR |
| Subsystem | sftp /usr/lib/openssh/sftp-server |

### SSH Config Backup
- Location: /etc/ssh/sshd_config.bak.<timestamp>
- Created during security hardening (2026-11-20)

---

## 3. Firewall Configuration (UFW)

| Setting | Value |
|---------|-------|
| Status | active |
| Default incoming | deny |
| Default outgoing | allow |
| Default routed | disabled |
| Logging | on (low) |
| Port 22/tcp | ALLOW IN (Anywhere) |
| Port 443/tcp | ALLOW IN (Anywhere) |
| Port 80/tcp | ALLOW IN (Anywhere) |
| Port 22/tcp (v6) | ALLOW IN (Anywhere) |
| Port 443/tcp (v6) | ALLOW IN (Anywhere) |
| Port 80/tcp (v6) | ALLOW IN (Anywhere) |

---

## 4. Recovery Procedures

### Scenario 1: SSH Key Not Working
**Symptom:** SSH key authentication fails on both ports 22 and 443.

**Recovery Steps:**
1. Verify the private key file exists: `ls -la ~/.ssh/id_ed25519_new_project`
2. Verify key fingerprint: `ssh-keygen -l -E sha256 -f ~/.ssh/id_ed25519_new_project.pub`
3. Expected fingerprint: SHA256:rTm6Fc+kw8UZMp6xMV8RKqupbaDURgDgHoD6GhFHh5k
4. If key is missing or corrupted, restore from backup or contact server owner
5. Use UpCloud console (if available) to reset SSH access

### Scenario 2: UFW Blocking SSH
**Symptom:** Connection refused on ports 22 and 443.

**Recovery Steps:**
1. Connect via alternative method (hosting provider console)
2. Disable UFW: `ufw disable`
3. Reconfigure UFW rules: `ufw allow 22/tcp && ufw allow 443/tcp && ufw enable`
4. Verify SSH connectivity

### Scenario 3: sshd_config Broken
**Symptom:** SSH service fails to start after config change.

**Recovery Steps:**
1. Connect via alternative method
2. Restore backup: `cp /etc/ssh/sshd_config.bak.<timestamp> /etc/ssh/sshd_config`
3. Restart SSH: `systemctl restart ssh`
4. Verify SSH connectivity

### Scenario 4: SSH Service Down
**Symptom:** Connection refused on ports 22 and 443, UFW allows traffic.

**Recovery Steps:**
1. Connect via alternative method
2. Check service status: `systemctl status ssh`
3. Restart service: `systemctl restart ssh`
4. Verify service is active: `systemctl is-active ssh`
5. Verify SSH connectivity

### Scenario 5: Root Account Locked
**Symptom:** Cannot log in as root via SSH.

**Recovery Steps:**
1. Connect via alternative method (hosting provider console)
2. Check root account status: `passwd -S root`
3. Unlock root if locked: `passwd -u root`
4. Verify SSH key is in /root/.ssh/authorized_keys
5. Verify SSH permissions: `chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys`

---

## 5. Authorized Administrative Account

| Item | Value |
|------|-------|
| Account Name | root |
| UID | 0 |
| GID | 0 |
| Groups | 0(root) |
| Sudo Access | Yes (root is superuser) |
| SSH Key | id_ed25519_new_project |
| SSH Key Fingerprint | SHA256:rTm6Fc+kw8UZMp6xMV8RKqupbaDURgDgHoD6GhFHh5k |

**Note:** Root is the only administrative account on this server. No dedicated admin user has been created. Creating a dedicated admin user is recommended before disabling root SSH login.

---

## 6. Emergency Contacts and Resources

| Resource | Location/Value |
|----------|----------------|
| ORTA Bridge Tool | /home/coder/workspace/orta-bridge |
| ORTA Repository | https://github.com/aymenfoot/orta-bridge |
| ORTA Documentation | /home/coder/workspace/ORTA/docs/ |
| SSH Config Backup | /etc/ssh/sshd_config.bak.<timestamp> |
| Server Access Logs | /var/log/auth.log |
| System Logs | /var/log/syslog |
| Docker Logs | /var/log/docker/ (when Docker installed) |
