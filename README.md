# Second Brain — CTF Writeups, Tools & Bug Bounty Notes

Personal knowledge base for offensive security work:

- **CTF writeups** from HackTheBox and TryHackMe, organized by difficulty.
- **Tool reference** — per-tool notes with every command I've actually used.
- **Exploits & abuses** — per-technique notes for every exploit chain, with prerequisites and commands.
- **Bug bounty flows** — reusable methodology notes (recon, discovery, exploitation patterns).

---

## Machines

### Easy

| Machine | OS | Writeup |
|---------|----|---------|
| **Silentium** | Linux | [Writeup →](Easy/Silentium_HTB_Writeup.md) |
| **Kobold** | Linux | [Writeup →](Easy/Kobold-Writeup.md) |
| **CCTV** | Linux | [Writeup →](Easy/cctv.md) |
| **MonitorsFour** | Windows (Docker) | [Writeup →](Easy/MonitorsFour.md) |

### Medium

| Machine | OS | Writeup |
|---------|----|---------|
| **DevArea** | Linux | [Writeup →](Medium/DevArea.md) |
| **Overwatch** | Windows (AD) | [Writeup →](Medium/Overwatch.md) |

### Hard

*(None yet)*

---

## Tools

Per-tool note with every command used across the writeups and a short description.

### Reconnaissance / Enumeration
- [nmap](tools/nmap.md) — port & service discovery
- [ffuf](tools/ffuf.md) — web / API fuzzing
- [gobuster](tools/gobuster.md) — vhost & directory brute-force
- [netexec](tools/netexec.md) — SMB / LDAP / MSSQL enumeration & spraying
- [smbclient](tools/smbclient.md) — SMB share access
- [impacket](tools/impacket.md) — MSSQL client, AS-REP Roast, Kerberoast
- [kerbrute](tools/kerbrute.md) — Kerberos-based password spraying

### Exploitation
- [curl](tools/curl.md) — HTTP payload delivery (JSON, SOAP, API abuse)
- [sqlmap](tools/sqlmap.md) — automated SQL injection
- [metasploit](tools/metasploit.md) — public-exploit delivery
- [responder](tools/responder.md) — NTLM hash capture
- [dnstool](tools/dnstool.md) — ADIDNS record manipulation

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

### Web Read / SQLi / Disclosure
- [Apache CXF XOP Include → LFI](exploits/apache-cxf-xop-lfi.md) — DevArea
- [ZoneMinder time-based blind SQLi](exploits/zoneminder-sqli.md) — CCTV
- [MailHog password reset](exploits/mailhog-password-reset.md) — Silentium
- [Exposed `.env` / config files](exploits/env-file-exposure.md) — MonitorsFour
- [Default credentials](exploits/default-credentials.md) — CCTV

### Active Directory / Windows
- [MSSQL linked server abuse](exploits/mssql-linked-server.md) — Overwatch
- [MSSQL enumeration cheat sheet](exploits/mssql-enumeration.md) — Overwatch
- [ADIDNS poisoning](exploits/adidns-poisoning.md) — Overwatch
- [NTLM capture & crack](exploits/ntlm-capture-crack.md) — Overwatch
- [Password spraying](exploits/password-spraying.md) — Overwatch
- [AS-REP Roast & Kerberoast](exploits/kerberos-roasting.md) — Overwatch
- [SMB anonymous enumeration](exploits/smb-anonymous-enum.md) — Overwatch
- [NSSM-wrapped service abuse](exploits/nssm-service-abuse.md) — Overwatch

### Credential Hunting
- [Binary string credentials](exploits/binary-credential-hunting.md) — Overwatch
- [systemd unit-file credentials](exploits/systemd-service-credentials.md) — DevArea
- [`/proc/*/environ` enumeration](exploits/env-variable-enum.md) — Silentium
- [Cleartext sniffing with tcpdump](exploits/tcpdump-credential-sniffing.md) — CCTV

### Privilege Escalation (Linux)
- [Docker group → root](exploits/docker-group-escape.md) — Kobold
- [Sudo + `bash` overwrite → SUID root](exploits/sudo-bash-overwrite.md) — DevArea
- [Gogs symlink write attack](exploits/gogs-symlink-attack.md) — Silentium

### Container Escape
- [Unauthenticated Docker API](exploits/docker-api-unauthenticated.md) — MonitorsFour

### Pivoting
- [SSH port forwarding](exploits/ssh-tunneling.md) — Silentium, CCTV

### Enumeration Playbooks
- [Linux post-exploitation enumeration](exploits/linux-enumeration.md) — system context, container detection, credential hunting with `find`/`grep`, SUID, cron, network

---

## Directory Structure

```
HTB/
├── README.md
├── Easy/
│   ├── Silentium_HTB_Writeup.md
│   ├── Kobold-Writeup.md
│   ├── cctv.md
│   └── MonitorsFour.md
├── Medium/
│   ├── DevArea.md
│   └── Overwatch.md
├── Hard/
├── tools/           # per-tool command notes
└── exploits/        # per-technique exploit notes
```
