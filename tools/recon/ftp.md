# ftp

Interactive FTP client. Used primarily for anonymous FTP enumeration when the server is configured to expose files (sometimes the whole filesystem) without credentials.

## Commands Used

### Anonymous login
<!-- cmd: linux -->
```bash
ftp $TARGET
# Name: anonymous
# Password: <blank>
```
Used on: **Anonforce (BSides GT)**

### Listing + navigation (inside the client)
```
ls -la
pwd
cd /home
cd /notread
cd /etc
```
Used on: **Anonforce (BSides GT)**

exposed full filesystem over anonymous FTP.

### Bulk file download
```
mget crontab
mget private.asc backup_encrypted.pgp
```
Used on: **Anonforce (BSides GT)**

`mget` prompts per file unless `prompt` is toggled off.

### Disable prompting and pull everything
```
prompt
mget *
```

### Switch to binary mode (before downloading non-text files)
```
binary
get backup_encrypted.pgp
```

## Non-interactive one-shots

### curl
<!-- cmd: linux -->
```bash
curl -u 'anonymous:' ftp://$TARGET/etc/passwd -o passwd
```

### wget recursive mirror
<!-- cmd: linux -->
```bash
wget -r --no-parent -nH ftp://anonymous:@$TARGET/
```

### lftp (cleaner recursive)
<!-- cmd: linux -->
```bash
lftp -u anonymous, $TARGET -e "mirror / ./ftp_dump; bye"
```

## Related
- [Anonymous FTP enumeration playbook](../../exploits/network-services/anonymous-ftp-enumeration.md)
- [PGP key cracking](../../techniques/creds/pgp-key-cracking.md) — typical follow-up after a backup drops


