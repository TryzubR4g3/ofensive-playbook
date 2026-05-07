# smbmap

SMB share enumeration tool that quickly lists readable and writable shares with optional anonymous or credentialed access.

## Commands Used

### Anonymous share listing

```bash
smbmap -H $TARGET -u '' -p ''
```

Used on: **Kenobi** - confirmed the `anonymous` share was readable after Nmap SMB scripts returned nothing useful.

## Related

- [smbclient](smbclient.md)
- [../../exploits/ad/smb-enumeration.md](../../exploits/ad/smb-enumeration.md)


