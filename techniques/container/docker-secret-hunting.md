# Docker Container Secret Hunting

Used on: **Internal**

After landing in a container, basic container checks plus filesystem sweeps can reveal host credentials, application notes, mounted secrets, or service tokens.

## When to Use

- You have successfully established a shell inside a container environment.
- Initial container confirmation checks (`/proc/self/status` capabilities, hex hostnames, or `overlay` mounts) are positive.
- You have read access to application paths like `/opt` or standard linux directories.
## Prerequisites

- Shell inside a container.
- Read access to application or operational paths.

## Steps

Confirm container context:

```bash
cat /proc/self/status | grep -E '^Cap'
hostname
mount | grep -E 'overlay|aufs'
```

Search for simple text loot:

```bash
find / -name "*.txt" 2>/dev/null | grep -v proc
cat /opt/note.txt
```

On Internal, `/opt/note.txt` contained reusable root credentials.

## Defensive Note

Do not store host credentials inside containers, use a secrets manager, and scope container access to the minimum needed runtime files.

## Related

- [docker-container-enumeration.md](docker-container-enumeration.md)
- [../enumeration/linux-enumeration.md](../enumeration/linux-enumeration.md)


