# PowerShell (post-exploitation)

Once inside a Windows box via WinRM / evil-winrm, PowerShell is the native interface for enumeration and for interacting with local services. These are the specific cmdlets used across the Windows writeups.

## Commands Used

### Registry-based service enumeration (when `Get-Service` is restricted)
```powershell
Get-ChildItem -Path "HKLM:\SYSTEM\CurrentControlSet\Services" |
    Where-Object { $_.PSChildName -like "*nssm*" } |
    Select-Object PSChildName
```
Used on: **Overwatch**

### List every NSSM-wrapped service and its ImagePath
```powershell
Get-ChildItem -Path "HKLM:\SYSTEM\CurrentControlSet\Services" |
    ForEach-Object {
        $imagePath = (Get-ItemProperty -Path $_.PSPath -Name "ImagePath" -ErrorAction SilentlyContinue).ImagePath
        if ($imagePath -like "*nssm*") {
            Write-Host "Service: $($_.PSChildName)" -ForegroundColor Yellow
            Write-Host "ImagePath: $imagePath" -ForegroundColor White
        }
    }
```
Used on: **Overwatch**

### Dump service configuration from the registry
```powershell
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\overwatch\Parameters" | Format-List *
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\overwatch" | Format-List *
(Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\overwatch" -Name "ObjectName").ObjectName
```
Used on: **Overwatch**

### Identify the process behind a listening port
```powershell
netstat -ano | findstr ":8000"
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess
```
Used on: **Overwatch**

### Build and send a SOAP request from PowerShell
```powershell
$killSoap = @"
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <KillProcess xmlns="http://tempuri.org/">
            <processName>notepad</processName>
        </KillProcess>
    </soap:Body>
</soap:Envelope>
"@

Invoke-RestMethod -Uri "http://localhost:8000/MonitorService" `
    -Method Post `
    -ContentType "text/xml; charset=utf-8" `
    -Body $killSoap `
    -Headers @{ "SOAPAction" = "http://tempuri.org/IMonitoringService/KillProcess" }
```
Used on: **Overwatch**
