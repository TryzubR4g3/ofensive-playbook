# proxychains

CLI wrapper that forces a command through a SOCKS or HTTP proxy. Useful after creating SSH or Chisel tunnels into internal networks.

## Commands Used

### Run TCP tools through a SOCKS proxy

```bash
proxychains nc 172.16.0.100 23
proxychains telnet 172.16.0.100 23
```

Used on: **Wreath** - quick service reachability checks through a pivot.

### Scan through SOCKS

```bash
proxychains nmap -sT -Pn -n 10.200.180.1-255 -oN scan
```

Used on: **Wreath** - `-sT` was required because SYN scans do not work reliably through SOCKS.

### Trigger webshell commands through a pivot

```bash
proxychains curl -X POST http://10.200.180.150/web/exploit-tryzub.php --data-urlencode "a=whoami"
```

Used on: **Wreath** - executed commands on GitStack's uploaded PHP webshell through the Chisel SOCKS pivot.

## Configuration

Copy the global config locally per engagement:

```bash
cp /etc/proxychains.conf .
```

For SSH dynamic forwarding:

```ini
socks4 127.0.0.1 1337
```

For Chisel:

```ini
socks5 127.0.0.1 1080
```

When scanning with Nmap through proxychains, comment out `proxy_dns`; otherwise scans can hang.

## Related

- [chisel](chisel.md)
- [ssh](ssh.md)
- [chisel-pivoting.md](../../exploits/pivot/chisel-pivoting.md)


