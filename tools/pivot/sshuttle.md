# sshuttle

Transparent subnet tunneling over SSH. It behaves like a lightweight VPN when you have SSH access to a pivot host.

## Commands Used

### Route an internal subnet through SSH

<!-- cmd: linux -->
```bash
sshuttle -r user@PIVOT_HOST 172.16.0.0/24
```

Used on: **Wreath**

documented as an alternative to Chisel/SSH SOCKS for routing internal networks.

### Use a private key

<!-- cmd: linux -->
```bash
sshuttle --ssh-cmd "ssh -i KEYFILE" -r user@PIVOT_HOST 172.16.0.0/24
```

### Auto-detect subnets

<!-- cmd: linux -->
```bash
sshuttle -r user@PIVOT_HOST -N
```

## Notes

- Requires SSH access to the pivot.
- Linux-to-Linux is the sweet spot.
- If sessions die with `Broken pipe`, add SSH keepalives in `--ssh-cmd`.

## Related

- [ssh](ssh.md)
- [chisel](chisel.md)
- [ssh-tunneling.md](../../techniques/pivot/ssh-tunneling.md)


