# hashcat

GPU-accelerated password cracker. Used when mode selection matters or when cracking NTLMv2 hashes captured with Responder.

## Commands Used

### Crack NTLMv2 hash (mode 5600)
```bash
hashcat -m 5600 <captured_hash> /usr/share/wordlists/rockyou.txt --force
```
Used on: **Overwatch**, **Breaching Active Directory** - cracked captured NetNTLMv2 challenge/response material.

Breaching Active Directory also used:

```bash
hashcat -m 5600 hash /usr/share/wordlists/rockyou.txt --force --show
```

### Crack bcrypt hash (mode 3200)
```bash
hashcat -m 3200 hash.txt /usr/share/wordlists/rockyou.txt
```
Used on: **CCTV, marketplace** (alternative to John).

### Crack raw SHA-1 (mode 100)
```bash
hashcat -m 100 hash.txt /usr/share/wordlists/rockyou.txt
```
Used on: **Billing** â€” MagnusBilling `pkg_user.password` column is raw SHA-1 (rockyou did not crack it; moved on to DB enumeration instead).

### Crack NTLM (mode 1000) â€” Windows SAM hashdump
```bash
hashcat -m 1000 hash.txt /usr/share/wordlists/rockyou.txt
```
Used on: **Blueprint** â€” NTLM from `hashdump`.

### Crack Mozilla / Firefox saved-login material
```bash
hashcat -m 26100 mozilla-hash.txt /usr/share/wordlists/rockyou.txt -O
hashcat -m 26100 mozilla-hash.txt --show
```
Used on: **chronicle** — cracked the Firefox profile master-password-derived hash before decrypting stored site credentials.

## Mode Reference

| Mode | Hash |
|------|------|
| 100 | raw SHA-1 (MagnusBilling) |
| 1000 | NTLM |
| 26100 | Mozilla key4.db / Firefox login hash |
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


