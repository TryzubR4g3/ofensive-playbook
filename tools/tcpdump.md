# tcpdump

Packet sniffer. Used to capture cleartext credentials sent over the wire by scheduled tasks / cron jobs inside a compromised host.

## Commands Used

### Capture all traffic on all interfaces with ASCII output
```bash
/usr/bin/tcpdump -i any -A
```
Used on: **CCTV**

- `-i any` — listen on every interface
- `-A` — print payload in ASCII (reveals credentials sent in cleartext)

Result on CCTV: a scheduled task transmitted `sa_mark:PASSWORD` in cleartext, giving lateral movement from `mark` to `sa_mark`.
