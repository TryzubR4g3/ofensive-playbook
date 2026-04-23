# Second Brain — CTF Writeups, Tools & Bug Bounty Notes

Personal knowledge base for offensive security work:

- **CTF writeups** from HackTheBox and TryHackMe, organized by difficulty.
- **Tool reference** — per-tool notes with every command I've actually used.
- **Exploits & abuses** — per-technique notes for every exploit chain, with prerequisites and commands.
- **Bug bounty flows** — reusable methodology notes (recon, discovery, exploitation patterns).

---

## HackTheBox Machines

### Easy

| Machine | OS | Writeup |
|---------|----|---------|
| **Silentium** | Linux | [Writeup →](HTB/Easy/Silentium_HTB_Writeup.md) |
| **Kobold** | Linux | [Writeup →](HTB/Easy/Kobold-Writeup.md) |
| **CCTV** | Linux | [Writeup →](HTB/Easy/cctv.md) |
| **MonitorsFour** | Windows (Docker) | [Writeup →](HTB/Easy/MonitorsFour.md) |

### Medium

| Machine | OS | Writeup |
|---------|----|---------|
| **DevArea** | Linux | [Writeup →](HTB/Medium/DevArea.md) |
| **Overwatch** | Windows (AD) | [Writeup →](HTB/Medium/Overwatch.md) |
| **Logging** 🚧 | Windows (AD) | [Writeup →](HTB/Medium/Logging.md) |

### Hard

*(None yet)*

---

## TryHackMe Machines

### Easy

| Machine | OS | Writeup |
|---------|----|---------|
| **Team** | Linux | [Writeup →](TRY/Easy/Team.md) |
| **IDE** | Linux | [Writeup →](TRY/Easy/Ide.md) |
| **Blueprint** | Windows (XAMPP) | [Writeup →](TRY/Easy/blueprint.md) |
| **SoupedeCode 01** | Windows (AD) | [Writeup →](TRY/Easy/soupedocde01.md) |
| **Anonforce (BSides GT)** | Linux | [Writeup →](TRY/Easy/bsidesgtanonforce.md) |
| **VulnNet: Internal** | Linux | [Writeup →](TRY/Easy/vulnnetinternal.md) |
| **Billing** | Linux (MagnusBilling) | [Writeup →](TRY/Easy/billing.md) |

### Medium

*(None yet)*

> 🚧 = writeup in progress / privilege escalation still being documented.

---

## Tools

Per-tool note with every command used across the writeups and a short description.

### Reconnaissance / Enumeration
- [nmap](tools/nmap.md) — port & service discovery
- [whatweb](tools/whatweb.md) — HTTP fingerprinting (server, CMS, redirects)
- [ffuf](tools/ffuf.md) — web / API fuzzing
- [gobuster](tools/gobuster.md) — vhost & directory brute-force
- [feroxbuster](tools/feroxbuster.md) — recursive directory brute-force
- [netexec](tools/netexec.md) — SMB / LDAP / MSSQL enumeration & spraying
- [smbclient](tools/smbclient.md) — SMB share access
- [enum4linux](tools/enum4linux.md) — SMB / RPC legacy sweep
- [showmount](tools/showmount.md) — NFS export listing
- [ftp](tools/ftp.md) — anonymous FTP triage + `mget`
- [impacket](tools/impacket.md) — MSSQL client, AS-REP Roast, Kerberoast
- [kerbrute](tools/kerbrute.md) — Kerberos-based password spraying
- [bloodhound](tools/bloodhound.md) — AD ACL / session graph collection

### Exploitation
- [curl](tools/curl.md) — HTTP payload delivery (JSON, SOAP, API abuse)
- [sqlmap](tools/sqlmap.md) — automated SQL injection
- [metasploit](tools/metasploit.md) — public-exploit delivery
- [responder](tools/responder.md) — NTLM hash capture
- [dnstool](tools/dnstool.md) — ADIDNS record manipulation
- [redis-cli](tools/redis-cli.md) — authenticated Redis enumeration
- [rsync](tools/rsync.md) — read/write file transfer via `rsync://` modules
- [mysql / mysqldump](tools/mysql.md) — DB enumeration + full-schema dump

### Shells & Pivoting
- [netcat](tools/netcat.md) — listeners & reverse shells
- [ssh](tools/ssh.md) — login, key auth, local port forwarding
- [evil-winrm](tools/evil-winrm.md) — interactive WinRM shell

### Post-Exploitation
- [docker](tools/docker.md) — container-based privilege escalation
- [git](tools/git.md) — Gogs symlink push
- [tcpdump](tools/tcpdump.md) — cleartext credential sniffing
- [strings](tools/strings.md) — hardcoded credential extraction
- [powershell](tools/powershell.md) — Windows enumeration & SOAP clients

### Password Cracking
- [john](tools/john.md) — offline cracking (bcrypt, etc.)
- [hashcat](tools/hashcat.md) — GPU cracking (NetNTLMv2, bcrypt)
- [gpg / gpg2john](tools/gpg.md) — PGP passphrase + ciphertext decryption

---

## Exploits & Abuses

Per-technique note with the full chain (prereqs, commands, why it works).

### Web / Application RCE
- [MCP API injection](exploits/mcp-api-injection.md) — Kobold `/api/mcp/connect`
- [Flowise Custom MCP Tool](exploits/flowise-mcp-rce.md) — Silentium
- [Hoverfly middleware RCE](exploits/hoverfly-middleware-rce.md) — DevArea
- [motionEye config injection](exploits/motioneye-config-injection.md) — CCTV
- [WCF SOAP command injection](exploits/wcf-soap-injection.md) — Overwatch
- [Cacti graph-template RCE](exploits/cacti-rce.md) — MonitorsFour
- [Codiad 2.8.4 authenticated RCE (CVE-2018-14009)](exploits/codiad-rce.md) — IDE
- [osCommerce 2.3.4 installer unauth RCE](exploits/oscommerce-installer-rce.md) — Blueprint
- [MagnusBilling unauth RCE (CVE-2023-30258)](exploits/magnusbilling-rce.md) — Billing

### Web Read / SQLi / Disclosure
- [Apache CXF XOP Include → LFI](exploits/apache-cxf-xop-lfi.md) — DevArea
- [ZoneMinder time-based blind SQLi](exploits/zoneminder-sqli.md) — CCTV
- [MailHog password reset](exploits/mailhog-password-reset.md) — Silentium
- [Exposed `.env` / config files](exploits/env-file-exposure.md) — MonitorsFour
- [Default credentials](exploits/default-credentials.md) — CCTV, IDE
- [LFI via PHP `include()` parameter](exploits/lfi-php-parameter.md) — Team
- [Backup / old script file exposure](exploits/backup-file-exposure.md) — Team

### CI/CD & DevOps RCE
- [TeamCity super-user token → build-step RCE](exploits/teamcity-superuser-token-rce.md) — VulnNet: Internal

### Network Service Abuse (Linux)
- [Anonymous FTP enumeration](exploits/anonymous-ftp-enumeration.md) — Anonforce
- [NFS share abuse (`showmount`, `no_root_squash`)](exploits/nfs-share-abuse.md) — VulnNet: Internal
- [Redis authenticated enumeration & abuse](exploits/redis-auth-abuse.md) — VulnNet: Internal
- [rsync module abuse (read + write)](exploits/rsync-module-abuse.md) — VulnNet: Internal

### Active Directory / Windows
- [MSSQL linked server abuse](exploits/mssql-linked-server.md) — Overwatch
- [MSSQL enumeration cheat sheet](exploits/mssql-enumeration.md) — Overwatch
- [ADIDNS poisoning](exploits/adidns-poisoning.md) — Overwatch
- [NTLM capture & crack](exploits/ntlm-capture-crack.md) — Overwatch
- [Password spraying](exploits/password-spraying.md) — Overwatch, SoupedeCode 01
- [AS-REP Roast & Kerberoast](exploits/kerberos-roasting.md) — Overwatch, SoupedeCode 01
- [SMB anonymous enumeration](exploits/smb-anonymous-enum.md) — Overwatch, SoupedeCode 01
- [RID brute-force enumeration (LSA cycling)](exploits/rid-brute-enumeration.md) — SoupedeCode 01
- [Shadow Credentials → PKINIT → UnPAC-the-Hash](exploits/shadow-credentials.md) — Logging
- [NSSM-wrapped service abuse](exploits/nssm-service-abuse.md) — Overwatch

### Credential Hunting
- [Binary string credentials](exploits/binary-credential-hunting.md) — Overwatch
- [systemd unit-file credentials](exploits/systemd-service-credentials.md) — DevArea
- [`/proc/*/environ` enumeration](exploits/env-variable-enum.md) — Silentium
- [Cleartext sniffing with tcpdump](exploits/tcpdump-credential-sniffing.md) — CCTV
- [`.bash_history` credential discovery](exploits/bash-history-credentials.md) — IDE
- [PGP private key cracking (`gpg2john`)](exploits/pgp-key-cracking.md) — Anonforce

### Privilege Escalation (Linux)
- [Docker group → root](exploits/docker-group-escape.md) — Kobold
- [Sudo + `bash` overwrite → SUID root](exploits/sudo-bash-overwrite.md) — DevArea
- [Gogs symlink write attack](exploits/gogs-symlink-attack.md) — Silentium
- [Sudo script unsanitized input injection](exploits/sudo-input-injection.md) — Team
- [Cron script group-writable abuse](exploits/cron-script-abuse.md) — Team
- [pkexec + pkttyagent authentication agent](exploits/pkexec-pkttyagent-privesc.md) — IDE
- [Sudo `fail2ban-client` → SUID bash](exploits/fail2ban-sudo-privesc.md) — Billing

### Container Escape
- [Unauthenticated Docker API](exploits/docker-api-unauthenticated.md) — MonitorsFour

### Pivoting
- [SSH port forwarding](exploits/ssh-tunneling.md) — Silentium, CCTV

### Enumeration Playbooks
- [Linux post-exploitation enumeration](exploits/linux-enumeration.md) — system context, container detection, credential hunting with `find`/`grep`, SUID, cron, network
- [Windows post-exploitation enumeration](exploits/windows-enumeration.md) — privileges, domain context, credentials on disk, services, scheduled tasks, payload transfer
- [SMB enumeration playbook](exploits/smb-enumeration.md) — banner, signing, anonymous / guest / authenticated share walks, RID brute, spraying, Kerberos roasting, PTH

---

## Directory Structure

```
.
├── README.md
├── CLAUDE.md          # project guide for Claude Code sessions
├── HTB/
│   ├── Easy/
│   │   ├── Silentium_HTB_Writeup.md
│   │   ├── Kobold-Writeup.md
│   │   ├── cctv.md
│   │   └── MonitorsFour.md
│   ├── Medium/
│   │   ├── DevArea.md
│   │   ├── Overwatch.md
│   │   └── Logging.md         # 🚧 WIP
│   └── Hard/
├── TRY/
│   ├── Easy/
│   │   ├── Team.md
│   │   ├── Ide.md
│   │   ├── blueprint.md
│   │   ├── soupedocde01.md
│   │   ├── bsidesgtanonforce.md
│   │   ├── vulnnetinternal.md
│   │   └── billing.md
│   ├── Medium/
│   └── Hard/
├── tools/             # per-tool command notes
└── exploits/          # per-technique exploit notes
```

---

## How to Use This Repo

Think of it as a three-layer knowledge base:

1. **Machine writeups** (`HTB/`, `TRY/`) tell the _story_ — what was on the box, what I tried, what worked.
2. **Tool notes** (`tools/`) list the _commands_ grouped by tool, annotated with the machine that needed them — useful when you remember "I ran nmap like _that_ on that Windows AD box" but not the exact flags.
3. **Exploit notes** (`exploits/`) capture the _techniques_ as reusable playbooks — prerequisites, step-by-step, defensive notes — so any future engagement or bug-bounty target gets the distilled version without re-reading the writeup.

Every new machine that introduces a new tool / technique triggers an update to `tools/` or `exploits/` **in the same commit**.
