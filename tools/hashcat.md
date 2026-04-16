# hashcat

GPU-accelerated password cracker. Used when mode selection matters or when cracking NTLMv2 hashes captured with Responder.

## Commands Used

### Crack NTLMv2 hash (mode 5600)
```bash
hashcat -m 5600 <captured_hash> /usr/share/wordlists/rockyou.txt --force
```
Used on: **Overwatch** — produced `sqlmgmt:bIhBbzMMnB82yx`.

### Crack bcrypt hash (mode 3200)
```bash
hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt
```
Referenced in: **CCTV** (alternative to John).

## Mode Reference

| Mode | Hash |
|------|------|
| 3200 | bcrypt `$2y$` / `$2a$` |
| 5600 | NetNTLMv2 |
