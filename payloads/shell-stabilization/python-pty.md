# Python PTY Shell Stabilization

Quick upgrade for a basic Linux reverse shell into an interactive TTY-like session.

Used on: **bsidesgtthompson**, **blog**, **coldvvars**

## Commands

Stabilise:
```bash
# What it does: spawn an interactive bash shell using Python.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

Optional terminal-side cleanup when the shell supports it:

```bash
export TERM=xterm
stty rows 44 cols 102
```

## Notes

- Use this immediately after catching a raw reverse shell if `su`, `sudo`, editors, or job control behave badly.
- Preserve any machine-specific dimensions from the writeup when they were actually used.

