# PGP Private Key Passphrase Cracking

**Used on:** **Anonforce (BSides GT)** (TryHackMe Easy)

A password-protected PGP private key is a cracked passphrase away from being fully usable. `gpg2john` converts the key into a john-compatible hash; `john` with a wordlist then recovers the passphrase. Once the key is imported and the passphrase known, any ciphertext encrypted against the public half decrypts — typically revealing backups, credentials, or further keys.

---

## Prerequisites

- A copy of the private key (usually `*.asc`, `*.pgp`, `secring.gpg`, or `*.gpg`).
- Optionally: the matching encrypted blob (`backup.pgp`, `.gpg`, etc.).
- `john` (jumbo build — ships with `gpg2john`).
- Wordlist (rockyou.txt is the go-to default).

---

## Step 1 — Convert the Key to a John Hash

```bash
gpg2john private.asc > pgp_hash.txt
```

The output is a single line per key: `<userid>:$gpg$*1*...*...:::::::`.

For binary keys:
```bash
gpg2john ~/.gnupg/secring.gpg > pgp_hash.txt
```

---

## Step 2 — Crack

### Wordlist mode (fastest first pass)
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt pgp_hash.txt
```

### Show the result
```bash
john --show pgp_hash.txt
```

### Rules / incremental (if rockyou alone fails)
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt --rules=Jumbo pgp_hash.txt
john --incremental pgp_hash.txt
```

### GPU (hashcat) alternative — mode 17010 (GPG)
```bash
hashcat -m 17010 pgp_hash.txt /usr/share/wordlists/rockyou.txt
```
(Depending on the exact GPG cipher/hash, modes `17010`–`17060` apply — hashcat prints the right one when it fails to autodetect.)

---

## Step 3 — Import the Key and Decrypt

```bash
gpg --import private.asc
# gpg prompts for the cracked passphrase on first use

gpg --list-secret-keys

gpg --decrypt backup_encrypted.pgp > backup_decrypted.txt
```

If the blob is a tarball:
```bash
gpg --decrypt backup.tar.gpg | tar -xvf -
```

---

## Variants

- **Armored vs binary keys** — `gpg2john` handles both; no flag needed.
- **Keys without passphrase** — `gpg2john` still emits a hash line, but `john` reports "No password hashes loaded" — the key is unlocked; just import and use.
- **Smart card-protected keys** — cannot be cracked this way; the private material never leaves the device.
- **Reading without importing** — `gpg --batch --passphrase '<pass>' --decrypt <file>` decrypts non-interactively in scripts.

---

## What to Look For After Decryption

1. `/etc/shadow` or `/etc/passwd` snapshots → feed to `john` again (`-m 500/1800`).
2. SSH private keys (`id_rsa`, `id_ed25519`) → try against every known user.
3. Cleartext credential dumps, `.env`, cloud tokens.
4. Configuration backups that reveal service endpoints reachable over VPN / NFS / SMB.

---

## Defensive Notes

1. **Use long, high-entropy passphrases.** Short dictionary words crack in seconds.
2. **Never store private keys beside encrypted data.** Separate the key from what it decrypts.
3. **Don't serve system directories over FTP / SMB / rsync / NFS.** Most PGP-cracking engagements start with a misconfigured file share exposing `~/.gnupg` or custom key paths.
4. **Use passphrase-less keys only when wrapped by hardware (YubiKey, smart card).**


