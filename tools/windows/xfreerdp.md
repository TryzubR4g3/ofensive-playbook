# xfreerdp

FreeRDP client for interactive RDP sessions, clipboard sharing, dynamic resolution, and drive redirection.

## Commands Used

### Basic RDP login

```bash
xfreerdp /v:IP /u:USERNAME /p:PASSWORD
```

Used on: **Wreath** - stabilized GUI access after creating a local Windows admin.

### RDP through proxychains with shared tools

```bash
proxychains xfreerdp /v:10.200.180.150 /u:tryzub /p:'Tryzub@' \
  +clipboard /dynamic-resolution \
  /drive:/usr/share/windows-resources,share \
  /cert:ignore \
  /sec:tls
```

Used on: **Wreath** - mounted Kali's Windows tooling at `\\tsclient\share`.

## Flag Notes

| Flag | Meaning |
|---|---|
| `+clipboard` | Enable clipboard sharing |
| `/dynamic-resolution` | Resize the remote desktop with the local window |
| `/drive:<path>,<name>` | Share a local directory into the RDP session |
| `/cert:ignore` | Ignore self-signed certificate warnings |
| `/sec:tls` | Force TLS security mode |

## Related

- [mimikatz](mimikatz.md)
- [windows-admin-stabilization.md](../../privesc/windows/windows-admin-stabilization.md)


