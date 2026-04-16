# HackTheBox — Writeups Collection

A collection of HackTheBox machine writeups organized by difficulty level. Each writeup documents the exploitation chain, vulnerabilities exploited, and key takeaways.

---

## 📂 Easy

| Machine | OS | Key Vulnerabilities | Writeup |
|---------|----|---------------------|---------|
| **[Silentium](Easy/Silentium_HTB_Writeup.md)** | Linux | Flowise Low-Code RCE, Gogs Symlink Attack (CVE-2024-55947 bypass) | [Read →](Easy/Silentium_HTB_Writeup.md) |
| **[Kobold](Easy/Kobold-Writeup.md)** | Linux | MCP API Command Injection, Docker Group Privilege Escalation | [Read →](Easy/Kobold-Writeup.md) |
| **[CCTV](Easy/cctv.md)** | Linux | ZoneMinder SQLi, motionEye Command Injection | [Read →](Easy/cctv.md) |

---

## 📂 Medium

| Machine | OS | Key Vulnerabilities | Writeup |
|---------|----|---------------------|---------|
| **[DevArea](Medium/DevArea.md)** | Linux | Apache CXF XOP Include LFI, Hoverfly Middleware RCE, SUID Binary Abuse | [Read →](Medium/DevArea.md) |
| **[Overwatch](Medium/Overwatch.md)** | Windows (AD) | ADIDNS Poisoning, Linked Server Exploitation, WCF Service Command Injection | [Read →](Medium/Overwatch.md) |

---

## 📂 Hard

| Machine | OS | Key Vulnerabilities | Writeup |
|---------|----|---------------------|---------|
| *(None yet)* | | | |

---

## 🛡️ Vulnerability Index

### Command Injection

| CVE | Machine | Description | Reference |
|-----|---------|-------------|-----------|
| — | **Kobold** | MCP API `/api/mcp/connect` accepts unsanitized `command` and `args` parameters, enabling arbitrary OS command execution via JSON payload | [Kobold Writeup →](Easy/Kobold-Writeup.md#initial-access) |
| [CVE-2025-60787](https://nvd.nist.gov/vuln/detail/CVE-2025-60787) | **CCTV** | motionEye configuration parameters (`picture_filename`, `image_file_name`) are written to config files without sanitization, then executed by the `motion` daemon in a shell context | [CCTV Writeup →](Easy/cctv.md#privilege-escalation) |
| [CVE-2024-45388](https://github.com/gunzf0x/CVE-2025-60787) | **DevArea** | Hoverfly middleware API allows authenticated users to inject arbitrary scripts via PUT request to `/api/v2/hoverfly/middleware` | [DevArea Writeup →](Medium/DevArea.md#hoverfly-rce) |
| — | **Overwatch** | WCF Monitoring Service `KillProcess` SOAP endpoint accepts unsanitized `processName` parameter, enabling command injection via semicolon chaining | [Overwatch Writeup →](Medium/Overwatch.md#privilege-escalation) |

### SQL Injection

| CVE | Machine | Description | Reference |
|-----|---------|-------------|-----------|
| [CVE-2024-51482](https://www.penligent.ai/hackinglabs/cve-2024-51482-the-zoneminder-sql-injection-that-kept-security-teams-exposed-past-1-37-61/) | **CCTV** | Time-based blind SQL injection in ZoneMinder's event tagging functionality via the `tid` parameter in `/zm/index.php?view=request&request=event&action=removetag` | [CCTV Writeup →](Easy/cctv.md#cve-2024-51482--time-based-blind-sql-injection) |

### File Inclusion / SSRF

| CVE | Machine | Description | Reference |
|-----|---------|-------------|-----------|
| [CVE-2022-46364](https://www.cve.org/CVERecord?id=CVE-2022-46364) | **DevArea** | Apache CXF XOP Include vulnerability allows arbitrary file read via `<xop:Include href="file:///path/to/file">` in multipart SOAP requests | [DevArea Writeup →](Medium/DevArea.md#cve-2022-46364--apache-cxf-xop-include-ssrflfi) |

### Privilege Escalation

| Technique | Machine | Description | Reference |
|-----------|---------|-------------|-----------|
| **Docker Group** | **Kobold** | User membership in the `docker` group allows mounting the host filesystem via `docker run --privileged -v /:/hostfs`, equivalent to root access | [Kobold Writeup →](Easy/Kobold-Writeup.md#privilege-escalation) |
| **SUID Binary Abuse** | **DevArea** | `syswatch.sh` calls `bash` without absolute path, enabling PATH hijacking. Overwriting `/usr/bin/bash` with a SUID-creating script escalates to root | [DevArea Writeup →](Medium/DevArea.md#privilege-escalation) |
| **Service as Root** | **CCTV** | motionEye service configured to run as `User=root` in systemd, meaning any command injection through the service executes with root privileges | [CCTV Writeup →](Easy/cctv.md#motioneye-discovery) |
| **Gogs Symlink Attack** | **Silentium** | CVE-2024-55947 bypass — creating a symlink to `/root/.ssh/authorized_keys` in a repository, then writing SSH key content via API resolves through the symlink | [Silentium Writeup →](Easy/Silentium_HTB_Writeup.md#privilege-escalation) |
| **WCF Service Injection** | **Overwatch** | NSSM-managed WCF service runs as SYSTEM. Command injection via SOAP `processName` parameter enables arbitrary command execution as SYSTEM | [Overwatch Writeup →](Medium/Overwatch.md#privilege-escalation) |

### Active Directory Attacks

| Technique | Machine | Description | Reference |
|-----------|---------|-------------|-----------|
| **ADIDNS Poisoning** | **Overwatch** | Service account with DNS modification rights creates fake A record for linked server `SQL07`, redirecting NTLM authentication to attacker-controlled machine for hash capture via Responder | [Overwatch Writeup →](Medium/Overwatch.md#linked-server-exploitation--adidns-poisoning) |
| **Linked Server Exploitation** | **Overwatch** | MSSQL linked server self-mapping allows queries to execute in the context of the current user on remote servers, enabling cross-server authentication relay | [Overwatch Writeup →](Medium/Overwatch.md#step-2--check-login-mappings) |
| **NTLM Relay + Responder** | **Overwatch** | Fake DNS record causes SQL Server to send NTLMv2 authentication to attacker, who captures the hash with Responder and cracks it offline | [Overwatch Writeup →](Medium/Overwatch.md#step-5--capture-the-hash) |

### Credential Discovery

| Technique | Machine | Description | Reference |
|-----------|---------|-------------|-----------|
| **Hardcoded Connection String** | **Overwatch** | MSSQL connection string with plaintext credentials found in `overwatch.exe` binary via `strings` analysis | [Overwatch Writeup →](Medium/Overwatch.md#credential-discovery) |
| **Systemd Service File** | **DevArea** | Hoverfly admin credentials found in plaintext in `/etc/systemd/system/hoverfly.service` ExecStart parameter | [DevArea Writeup →](Medium/DevArea.md#credential-discovery) |
| **Config File Inspection** | **CCTV** | motionEye admin password stored in plaintext in `/etc/motioneye/motion.conf` | [CCTV Writeup →](Easy/cctv.md#extract-motioneye-admin-credentials) |
| **Environment Variables** | **Silentium** | SMTP password discovered in `/proc/1/environ` inside container, reused for host SSH access | [Silentium Writeup →](Easy/Silentium_HTB_Writeup.md#environment-variable-enumeration) |
| **Default Credentials** | **CCTV** | ZoneMinder shipped with default `admin:admin` credentials | [CCTV Writeup →](Easy/cctv.md#zoneminder-default-credentials) |

### Low-Code / AI Platform Exploitation

| Technique | Machine | Description | Reference |
|-----------|---------|-------------|-----------|
| **Flowise Custom MCP Tool** | **Silentium** | Flowise low-code AI platform allows creation of custom MCP tools that execute arbitrary commands, enabling RCE as root inside the container | [Silentium Writeup →](Easy/Silentium_HTB_Writeup.md#flowise-rce) |

---

## 📊 Vulnerability Summary by Category

### Critical (RCE)
- **CVE-2024-51482** — ZoneMinder SQL Injection → [CCTV](Easy/cctv.md)
- **CVE-2025-60787** — motionEye Command Injection → [CCTV](Easy/cctv.md)
- **CVE-2024-45388** — Hoverfly Middleware RCE → [DevArea](Medium/DevArea.md)
- **CVE-2022-46364** — Apache CXF XOP Include LFI → [DevArea](Medium/DevArea.md)
- MCP API Command Injection → [Kobold](Easy/Kobold-Writeup.md)
- WCF Service Command Injection → [Overwatch](Medium/Overwatch.md)
- Flowise Custom MCP Tool RCE → [Silentium](Easy/Silentium_HTB_Writeup.md)

### High (Privilege Escalation)
- Docker Group Privilege Escalation → [Kobold](Easy/Kobold-Writeup.md)
- SUID Binary PATH Hijacking → [DevArea](Medium/DevArea.md)
- Gogs Symlink Attack → [Silentium](Easy/Silentium_HTB_Writeup.md)
- ADIDNS Poisoning + NTLM Capture → [Overwatch](Medium/Overwatch.md)

### Medium (Information Disclosure)
- Hardcoded Credentials in Binaries → [Overwatch](Medium/Overwatch.md)
- Plaintext Credentials in Service Files → [DevArea](Medium/DevArea.md)
- Environment Variable Credential Leak → [Silentium](Easy/Silentium_HTB_Writeup.md)
- Default Credentials → [CCTV](Easy/cctv.md)

---

## 🔗 External References

### CVE Databases
- [CVE-2022-46364 — Apache CXF XOP Include](https://www.cve.org/CVERecord?id=CVE-2022-46364)
- [CVE-2024-45388 — Hoverfly Middleware RCE](https://github.com/gunzf0x/CVE-2025-60787)
- [CVE-2024-51482 — ZoneMinder SQL Injection](https://www.penligent.ai/hackinglabs/cve-2024-51482-the-zoneminder-sql-injection-that-kept-security-teams-exposed-past-1-37-61/)
- [CVE-2024-55947 — Gogs Symlink Vulnerability](https://nvd.nist.gov/vuln/detail/CVE-2024-55947)
- [CVE-2025-60787 — motionEye Command Injection](https://nvd.nist.gov/vuln/detail/CVE-2025-60787)

### Exploit Repositories
- [CVE-2025-60787 Exploit (gunzf0x)](https://github.com/gunzf0x/CVE-2025-60787)

### Tools Used
- [sqlmap](https://sqlmap.org/) — SQL injection exploitation
- [Responder](https://github.com/lgandx/Responder) — LLMNR/NBT-NS/mDNS poisoner
- [impacket](https://github.com/fortra/impacket) — Network protocol exploitation
- [evil-winrm](https://github.com/Hackplayers/evil-winrm) — WinRM shell
- [netexec](https://github.com/Pennyw0rth/NetExec) — Network scanner
- [John the Ripper](https://www.openwall.com/john/) — Password cracking
- [Hashcat](https://hashcat.net/hashcat/) — Password cracking

---

## 📝 Writeup Structure

Each writeup follows this structure:

1. **Attack Chain Overview** — Visual diagram of the exploitation path
2. **Table of Contents** — Quick navigation
3. **Reconnaissance** — Nmap scans, service discovery, enumeration
4. **Initial Access** — First foothold on the system
5. **Post-Exploitation** — System enumeration after initial access
6. **Privilege Escalation** — Escalation to higher privileges
7. **Flag Capture** — User and root flag retrieval
8. **Key Takeaways** — Security lessons learned
9. **Exploit References** — Cheat sheets and command references

---

## 📁 Directory Structure

```
HTB/
├── README.md                  # This file
├── Easy/                      # Easy machines (empty)
├── Medium/                    # Medium machines
│   ├── Kobold-Writeup.md
│   ├── DevArea
│   └── cctv
└── Hard/                      # Hard machines
    ├── Overwatch.md
    └── Silentium_HTB_Writeup.md
```

---

*Last updated: April 2026*
