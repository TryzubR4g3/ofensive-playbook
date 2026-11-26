# Athena — TryHackMe Writeup

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Medium
- **Source status** Documented

## Report overview

The observations in this case inform a review of service and share exposure and application input boundaries.

## Defensive takeaways

- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.
- Review where request data reaches queries, templates, files or internal requests. Add a regression test at each relevant boundary.

## Defensive references

- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)
- [Input validation and interpreter boundaries](../../../defense/techniques/input-boundaries.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Medium  
**OS:** Linux  
**IP:** `$TARGET`  
**Tech Stack:** Apache, Samba 4.15.13, custom ping web application

---

## Attack Chain Overview

```
Samba public share → message reveals /myrouterpanel web path
   → Ping parameter → OS command injection
   → Reverse shell as www-data
   → Enumeration → privilege escalation (TBD)
```

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Web Fuzzing](#2-web-fuzzing)
3. [Samba Enumeration](#3-samba-enumeration)
4. [Web Application — Ping Command Injection](#4-web-application--ping-command-injection)
5. [Key Takeaways](#5-key-takeaways)

---

## 1. Reconnaissance

```bash
nmap -sS -p- --min-rate 5000 -n -Pn $TARGET -oN silent
nmap -sVC -p22,80,139,445 $TARGET -oN service
```

Key services:

| Port | Service | Notes |
|------|---------|-------|
| 22 | SSH | OpenSSH |
| 80 | HTTP | Apache |
| 139/445 | SMB | Samba 4.15.13-Ubuntu |

Related notes: [nmap](../../../tools/recon/nmap.md), [silent-scan](../../../tools/recon/silent-scan.md)

---

## 2. Web Fuzzing

```bash
feroxbuster -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt
```

The HTTP root returned minimal content at this stage. The key lead came from Samba.

Related notes: [feroxbuster](../../../tools/fuzz/feroxbuster.md)

---

## 3. Samba Enumeration

Enumerated Samba shares without credentials:

```bash
enum4linux -a $TARGET
nxc smb $TARGET -u '' -p ''
nxc smb $TARGET -u '' -p '' --shares
```

**Output:**
```
SMB  10.128.153.160  445  ROUTERPANEL  public  READ
SMB  10.128.153.160  445  ROUTERPANEL  IPC$         IPC Service (Samba 4.15.13-Ubuntu)
```

The `public` share was readable anonymously. Connected and retrieved the message:

```bash
smbclient //$TARGET/public -N
get msg_for_administrator.txt
cat msg_for_administrator.txt
```

**Output:**
```
dear Administrator,
I would like to inform you that a new Ping system is being developed and
I left the corresponding application in a specific path, which can be accessed
through the following address: /myrouterpanel
Yours sincerely,
Athena
Intern
```

The Samba share revealed a hidden web path that was not discoverable through directory fuzzing.

Related notes: [enum4linux](../../../tools/recon/enum4linux.md), [smbclient](../../../tools/recon/smbclient.md), [netexec](../../../tools/recon/netexec.md)

---

## 4. Web Application — Ping Command Injection

Browsed to `http://$TARGET/myrouterpanel`. The page presented a ping utility that accepted an IP address. Ping utilities that shell out to the system `ping` command are classic command injection targets.

Tested for OS command injection by appending a second command with `;`:

```
http://$TARGET/myrouterpanel → input: 127.0.0.1; id
```

If the backend runs something like:
```php
system("ping -c 1 " . $_GET['ip']);
```
then `127.0.0.1; id` executes `id` after the ping.

Related exploit: [url-param-command-injection](../../../exploits/web-rce/url-param-command-injection.md)

> **Note:** Full exploitation output and privilege escalation steps to be documented on completion.

---

## 5. Key Takeaways

1. **Anonymous SMB shares reveal hidden application paths.** Always enumerate Samba with null auth (`-u '' -p ''`) — readable `public` shares routinely contain internal memos that leak app URLs, credentials, or architecture details.
2. **Ping utilities are command injection magnets.** Any web feature that shells out to `ping`, `traceroute`, `curl`, or similar system tools with user-supplied input is a priority injection target.
3. **feroxbuster won't find everything.** Hidden paths disclosed via SMB/IMAP/email are not crawlable — enumeration of adjacent services is always necessary before concluding that the web surface is exhausted.

---

## Related Notes

- [enum4linux](../../../tools/recon/enum4linux.md)
- [smbclient](../../../tools/recon/smbclient.md)
- [netexec](../../../tools/recon/netexec.md)
- [feroxbuster](../../../tools/fuzz/feroxbuster.md)
- [url-param-command-injection](../../../exploits/web-rce/url-param-command-injection.md)
