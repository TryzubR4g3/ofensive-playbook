# tcpdump

## Wreath Commands

<!-- cmd: linux -->
```bash
sudo tcpdump -i tun0 icmp
```
Used on: **Wreath**

checked whether the GitStack host could reach the attacker directly before choosing a Chisel relay.

Packet sniffer. Used to capture cleartext credentials sent over the wire by scheduled tasks / cron jobs inside a compromised host.

## Commands Used

### Capture LDAP bind traffic in hex and ASCII
<!-- cmd: linux -->
```bash
sudo tcpdump -SX -i breachad tcp port 389
```
Used on: **Breaching Active Directory**

captured cleartext LDAP pass-back credentials after lowering rogue LDAP SASL requirements.

- `-S` - print absolute TCP sequence numbers
- `-X` - print packet payload in hex and ASCII
- `tcp port 389` - only LDAP traffic
### Capture all traffic on all interfaces with ASCII output
<!-- cmd: linux -->
```bash
/usr/bin/tcpdump -i any -A
```
Used on: **CCTV**

`-i any` — listen on every interface
- `-A` — print payload in ASCII (reveals credentials sent in cleartext)

Result on CCTV: a scheduled task transmitted `sa_mark:PASSWORD` in cleartext, giving lateral movement from `mark` to `sa_mark`.


