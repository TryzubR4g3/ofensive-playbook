# Windows event log review with PowerShell

<!-- tags: Windows event logs, PowerShell, Get-WinEvent, EVTX, Sysmon, audit, evidence -->

Use Get-WinEvent to read exported Windows event logs while keeping the source system and the exported log intact.

## Review workflow

Work from a local copy of a collected EVTX file. Record event identifiers and timestamps using a consistent timezone.

<!-- cmd: windows -->
```powershell
Get-WinEvent -Path .\review.evtx -MaxEvents 30 |
    Select-Object TimeCreated, Id, ProviderName, RecordId
```

Correlate relevant records with the authorized change or case timeline and retain the record IDs.

## References

- [Microsoft Get-WinEvent reference](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.diagnostics/get-winevent)
- [Windows service and task hardening](../techniques/windows-service-hardening.md)
