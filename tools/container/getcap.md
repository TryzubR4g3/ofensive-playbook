# getcap

Reads POSIX file capabilities — the per-binary fine-grained replacement for SUID. A binary with `cap_setuid+ep` can change UID; one with `cap_dac_read_search+ep` can read any file; one with `cap_sys_admin+ep` is essentially root. Always run this once you have a shell — capabilities live next to SUID and are missed by tools that only check `find -perm -4000`.

## Commands Used

### Recursive capability sweep
```bash
getcap -r / 2>/dev/null
```
Used on: **ohmyweb**

Result: `/usr/bin/python3.7 = cap_setuid+ep` -> see [linux-capabilities-privesc.md](../../privesc/linux/linux-capabilities-privesc.md). One line, root.

- `-r` -- recurse into subdirectories.
- `2>/dev/null` -- silence "Operation not supported" on filesystems that don't carry xattrs (`/proc`, `/sys`).

### Capability of a single binary
```bash
getcap /usr/bin/python3.7
# /usr/bin/python3.7 = cap_setuid+ep
```

### Set / remove capabilities (rarely useful from a low-priv shell, but good to recognise)
```bash
setcap cap_setuid+ep ./shell    # need CAP_SETFCAP / root
setcap -r ./shell               # remove
```

## What to look for

| Capability | Why it's game over |
|-----------|--------------------|
| `cap_setuid+ep` | uid-changing primitive in any scripting language -> root |
| `cap_setgid+ep` | similar, gid side |
| `cap_sys_admin+ep` | "second root" -- mount, ptrace, kernel knobs |
| `cap_sys_ptrace+ep` | inject into other procs (incl. root-owned) |
| `cap_dac_read_search+ep` | bypass file read perms -- read `/etc/shadow`, anyone's keys |
| `cap_dac_override+ep` | bypass file read **and** write perms |
| `cap_chown+ep` | change ownership of any file |
| `cap_net_raw+ep` | raw sockets -- not privesc by itself but lets you sniff / spoof |

`+ep` (effective + permitted) is the dangerous combo. `+i` (inheritable) alone is mostly noise.

## Cross-references / payloads

- Python (any version with `cap_setuid+ep`): see the exploitation note linked below.
- Perl, ruby, node -- all the same idea once `cap_setuid+ep` is present.
- GTFOBins keeps a current list: <https://gtfobins.org/#+capabilities>

## Related
- [linux-capabilities-privesc.md](../../privesc/linux/linux-capabilities-privesc.md) -- exploitation playbook
- [linux-enumeration.md](../../playbooks/enumeration/linux.md) -- where this fits in the post-foothold sweep


