# Python PTY Shell Stabilization

Quick upgrade for a basic Linux reverse shell into an interactive TTY-like session.

Used on: **bsidesgtthompson**, **blog**, **coldvvars**

## Commands

```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

Optional terminal-side cleanup when the shell supports it:

```bash
export TERM=xterm
stty rows 44 cols 102
```

## Notes

- Use this immediately after catching a raw reverse shell if `su`, `sudo`, editors, or job control behave badly.
- Preserve any machine-specific dimensions from the writeup when they were actually used.

