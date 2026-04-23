# enum4linux

Wrapper around the Samba suite (`smbclient`, `rpcclient`, `net`, `nmblookup`) that runs the classic SMB / RPC enumeration queries in one shot. Useful on initial contact against Windows / Samba hosts to list shares, users, policy info and RID ranges.

## Commands Used

### Full run
```bash
enum4linux -a $TARGET
```
Used on: **VulnNet: Internal** — revealed the readable `\shares` SMB share and rpcbind / NFS visibility.
Used on: **SoupedeCode 01** — returned RID ranges `500–550` and `1000–1050`, confirming guest LSA access.

`-a` runs all:
- `-U` — users
- `-S` — shares
- `-G` — groups
- `-P` — password policy
- `-r` — RID cycling
- `-o` — OS info

## Partial runs (when you want noise control)

```bash
enum4linux -S $TARGET                      # just shares
enum4linux -U -u guest -p '' $TARGET       # users, authenticated as guest
enum4linux -r -R 500-1500 $TARGET          # RID cycle bounded
```

## Follow-up when enum4linux comes back thin

```bash
# Faster, modern equivalents
netexec smb $TARGET -u '' -p '' --shares
netexec smb $TARGET -u guest -p '' --rid-brute
smbclient -N -L //$TARGET/
```

## Related
- [smbclient](smbclient.md) — file-level interaction
- [netexec](netexec.md) — modern enumeration + exploitation
- [SMB anonymous enumeration](../exploits/smb-anonymous-enum.md)
- [SMB enumeration playbook](../exploits/smb-enumeration.md)
- [RID brute-force](../exploits/rid-brute-enumeration.md)
