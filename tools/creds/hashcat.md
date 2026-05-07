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
Used on: **CCTV** (alternative to John).

### Crack raw SHA-1 (mode 100)
```bash
hashcat -m 100 hash.txt /usr/share/wordlists/rockyou.txt
```
Used on: **Billing** — MagnusBilling `pkg_user.password` column is raw SHA-1 (rockyou did not crack it; moved on to DB enumeration instead).

### Crack NTLM (mode 1000) — Windows SAM hashdump
```bash
hashcat -m 1000 hash.txt /usr/share/wordlists/rockyou.txt
```
Used on: **Blueprint** — NTLM from `hashdump`.

## Mode Reference

| Mode | Hash |
|------|------|
| 100 | raw SHA-1 (MagnusBilling) |
| 1000 | NTLM |
| 3200 | bcrypt `$2y$` / `$2a$` |
| 5600 | NetNTLMv2 |
| 13100 | Kerberos TGS (Kerberoast) |
| 18200 | Kerberos AS-REP (AS-REP Roast) |

## Useful Flags

| Flag | Purpose |
|------|---------|
| `-a 0` | Straight dictionary (default) |
| `-a 3` | Brute-force / mask attack |
| `-r <rules>` | Apply rules file (`best64.rule`, `OneRuleToRuleThemAll.rule`) |
| `--show` | Show already-cracked hashes from `.potfile` |
| `--username` | Input file has `user:hash` format |
| `-O` | Optimised kernels (faster, shorter max length) |
| `--force` | Ignore hardware warnings (VMs / no GPU) |
