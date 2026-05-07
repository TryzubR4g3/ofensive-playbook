# FoxyProxy

Browser proxy switcher used to send web traffic through a SOCKS pivot without changing system-wide proxy settings.

## Commands Used

FoxyProxy is GUI-driven, so the reusable value is the configuration rather than a shell command.

Used on: **Wreath** - browsed internal HTTP services exposed through SSH/Chisel SOCKS pivots.

### SOCKS proxy profile

```text
Title: Wreath pivot
Proxy type: SOCKS5
Host: 127.0.0.1
Port: 1080
```

Use SOCKS4 when the tunnel is `ssh -D` and SOCKS5 when the tunnel is Chisel unless the client is configured otherwise.

## Related

- [proxychains](proxychains.md)
- [chisel](chisel.md)
- [chisel-pivoting.md](../../exploits/pivot/chisel-pivoting.md)


