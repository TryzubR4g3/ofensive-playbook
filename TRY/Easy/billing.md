# Billing - TryHackMe Writeup

**Status:** 🚧 _Work in progress — recon captured, exploitation & privesc pending._

**Target:** `TARGET_IP` (10.128.187.240 at time of solve)
**OS:** Linux (Debian)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.62, `/mbilling` (MagnusBilling), MySQL, Asterisk Manager

---

## Attack Chain Overview

```
nmap → 22/tcp SSH, 80/tcp Apache, 3306/tcp MySQL, 5038/tcp Asterisk AMI
    ↓
whatweb → redirects to /mbilling (MagnusBilling VoIP billing app)
    ↓
feroxbuster on /mbilling/ → [content enumeration in progress]
    ↓
[WIP] exploitation path (MagnusBilling / Asterisk AMI)
    ↓
[WIP] user → root
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Triage](#2-web-triage)
3. [Initial Access (WIP)](#3-initial-access-wip)

---

## 1. Reconnaissance

Full TCP sweep then service detection on the open ports:

```bash
nmap -sS -p- -n -Pn $TARGET
nmap -sVC -p22,80,3306,5038 $TARGET -oA service
```

Results:

| Port | Service | Notes |
|------|---------|-------|
| 22/tcp | OpenSSH | Linux login |
| 80/tcp | Apache 2.4.62 (Debian) | Redirects to `/mbilling` |
| 3306/tcp | MySQL | External DB — usually not reachable on THM |
| 5038/tcp | Asterisk Call Manager (AMI) | Management socket for PBX |

The `5038` + `/mbilling` combo is the fingerprint of **MagnusBilling** — an Asterisk-based VoIP billing frontend with a history of unauthenticated RCE (e.g. CVE-2023-30258 on the `icepay` endpoint).

---

## 2. Web Triage

```bash
whatweb http://$TARGET/
# → Apache[2.4.62], HTTPServer[Debian Linux], RedirectLocation[./mbilling]
```

Confirms the landing page redirects to `/mbilling/`. Everything interesting lives inside that path.

Directory brute on the app root:

```bash
feroxbuster -u http://$TARGET/mbilling/ \
  -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
```

_(WIP — output pending)_

---

## 3. Initial Access (WIP)

Exploitation not yet captured. Candidate paths for this target class:

- **MagnusBilling CVE-2023-30258** — unauth command injection in `/mbilling/index.php?module=icepay`.
- **Asterisk AMI (port 5038)** default creds / weak creds → originate calls, read/write files via `MixMonitor`.
- **MySQL (port 3306)** external — usually filtered on THM.

See [windows-enumeration.md](../../exploits/windows-enumeration.md) if needed for any foothold pivot; for Linux post-ex see [linux-enumeration.md](../../exploits/linux-enumeration.md).

---

## Related Notes
- [nmap](../../tools/nmap.md) — port & service discovery
- [whatweb](../../tools/whatweb.md) — HTTP fingerprinting
- [feroxbuster](../../tools/feroxbuster.md) — recursive directory brute

---

_Writeup to be extended once user + root flags are captured._
