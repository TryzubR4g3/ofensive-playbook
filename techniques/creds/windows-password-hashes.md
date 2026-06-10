# Windows Password Hashes

Windows systems store user credentials locally in the SAM (Security Account Manager) database or on Domain Controllers in the `NTDS.dit` file. Passwords are theoretically not stored in plaintext, but rather as cryptographic hashes.

Used on: **eJPT / Course Reference**

## Hash Formats

### LM (LAN Manager) Hash
- Severely outdated and insecure.
- Splits passwords into two 7-character halves and hashes them independently without a salt.
- Passwords over 14 characters cannot be LM hashed.
- By default, modern Windows versions disable LM hashes (representing the LM portion as a dummy value: `aad3b435b51404eeaad3b435b51404ee`).

### NT (NTLM) Hash
- Standard hash format on modern Windows.
- Uses MD4 without a salt, making it vulnerable to dictionary attacks and rainbow tables.
- A dumped hash string usually looks like: `<USER>:<RID>:<LM_HASH>:<NT_HASH>:::`
  - Example: `Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::`

## Local Storage Locations

1. **SAM Database**: `%SystemRoot%\System32\config\SAM` (Requires `SYSTEM` privileges to access). The hashes are encrypted with the `bootkey` found in the `SYSTEM` hive.
2. **LSASS Memory**: The Local Security Authority Subsystem Service caches hashes (and sometimes plaintext credentials depending on WDigest settings) in memory for active logon sessions.

## Pass-The-Hash (PTH)

Because NT hashes are passed during NTLM network authentication as equivalent to the password, possessing the NT hash allows an attacker to authenticate over SMB, RDP (Restricted Admin), or WinRM *without ever cracking the hash*.
