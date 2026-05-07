# gpg / gpg2john

GnuPG handles PGP encryption, decryption and key management. `gpg2john` (ships with john-jumbo) converts a PGP private key into a hash that `john` can crack — the standard workflow when you recover a passphrase-protected `*.asc`.

## Commands Used

### Convert a PGP private key to a john hash
```bash
gpg2john private.asc > pgp_hash.txt
```
Used on: **Anonforce (BSides GT)**

### Crack the passphrase with john
```bash
john --wordlist=/usr/share/wordlists/rockyou.txt pgp_hash.txt
john --show pgp_hash.txt
```
Used on: **Anonforce (BSides GT)** — passphrase cracked to `xbox360`.

### Import the private key into the keyring
```bash
gpg --import private.asc
```
Used on: **Anonforce (BSides GT)** — prompts for passphrase on first use.

### Decrypt a file with the imported key
```bash
gpg --decrypt backup_encrypted.pgp > backup_decrypted.txt
```
Used on: **Anonforce (BSides GT)** — revealed `/etc/shadow` hashes.

## Useful extras (not used in the writeups yet)

### List keys in the keyring
```bash
gpg --list-keys
gpg --list-secret-keys
```

### Non-interactive decrypt (for scripting)
```bash
gpg --batch --passphrase '<pass>' --decrypt file.gpg > file.plain
```

### Delete a test key
```bash
gpg --delete-secret-keys <KEYID>
gpg --delete-keys <KEYID>
```

### GPU alternative — hashcat PGP modes
```bash
hashcat -m 17010 pgp_hash.txt /usr/share/wordlists/rockyou.txt
# modes 17010-17060 cover different GPG ciphers; hashcat autodetects or prompts
```

## Related
- [john](john.md) — the actual cracking tool
- [PGP key cracking playbook](../../exploits/creds/pgp-key-cracking.md)
