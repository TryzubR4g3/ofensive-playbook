# raz0rblack

<!-- brain:report -->
- **Platform** TryHackMe
- **Difficulty** Medium
- **Source status** Documented

## Report overview

The observations in this case inform a review of directory identity and delegation and service and share exposure.

## Defensive takeaways

- Audit effective group membership, service identities and delegated rights against the approved access baseline.
- Confirm the intended audience for network services and shares, then compare their permissions and reachability with that policy.

## Defensive references

- [Directory identity and delegated access review](../../../defense/techniques/directory-access-review.md)
- [Exposed service and share hardening](../../../defense/techniques/service-exposure-review.md)

<!-- /brain:report -->

---


**Platform:** TryHackMe  
**Difficulty:** Medium  
**Status:** Incomplete — NFS loot and user-generation workflow documented; valid-user discovery and exploitation still need to be finished.

## Reconnaissance

```bash
nmap -sS -p- $TARGET --min-rate 5000 -Pn -n --open -oN silent
nmap -sVC -p53,88,111,135,139,389,445,464,593,636,2049,3268,3269,3389,5985,9389,47001,49664,49665,49667,49669,49670,49671,49673,49677,49697,49708 -vvv -oN service $TARGET
```

**Output**
```
PORT      STATE SERVICE       REASON          VERSION
53/tcp    open  domain        syn-ack ttl 126 Simple DNS Plus
88/tcp    open  kerberos-sec  syn-ack ttl 126 Microsoft Windows Kerberos (server time: 2026-06-16 13:52:50Z)
111/tcp   open  rpcbind       syn-ack ttl 126 2-4 (RPC #100000)
| rpcinfo: 
|   program version    port/proto  service
|   100000  2,3,4        111/tcp   rpcbind
|   100000  2,3,4        111/tcp6  rpcbind
|   100000  2,3,4        111/udp   rpcbind
|   100000  2,3,4        111/udp6  rpcbind
|   100003  2,3         2049/udp   nfs
|   100003  2,3         2049/udp6  nfs
|   100003  2,3,4       2049/tcp   nfs
|   100003  2,3,4       2049/tcp6  nfs
|   100005  1,2,3       2049/tcp   mountd
|   100005  1,2,3       2049/tcp6  mountd
|   100005  1,2,3       2049/udp   mountd
|   100005  1,2,3       2049/udp6  mountd
|   100021  1,2,3,4     2049/tcp   nlockmgr
|   100021  1,2,3,4     2049/tcp6  nlockmgr
|   100021  1,2,3,4     2049/udp   nlockmgr
|   100021  1,2,3,4     2049/udp6  nlockmgr
|   100024  1           2049/tcp   status
|   100024  1           2049/tcp6  status
|   100024  1           2049/udp   status
|_  100024  1           2049/udp6  status
135/tcp   open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
139/tcp   open  netbios-ssn   syn-ack ttl 126 Microsoft Windows netbios-ssn
389/tcp   open  ldap          syn-ack ttl 126 Microsoft Windows Active Directory LDAP (Domain: raz0rblack.thm, Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds? syn-ack ttl 126
464/tcp   open  kpasswd5?     syn-ack ttl 126
593/tcp   open  ncacn_http    syn-ack ttl 126 Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped    syn-ack ttl 126
2049/tcp  open  nlockmgr      syn-ack ttl 126 1-4 (RPC #100021)
3268/tcp  open  ldap          syn-ack ttl 126 Microsoft Windows Active Directory LDAP (Domain: raz0rblack.thm, Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped    syn-ack ttl 126
3389/tcp  open  ms-wbt-server syn-ack ttl 126 Microsoft Terminal Services
|_ssl-date: 2026-06-16T13:54:04+00:00; -6h25m47s from scanner time.
| rdp-ntlm-info: 
|   Target_Name: RAZ0RBLACK
|   NetBIOS_Domain_Name: RAZ0RBLACK
|   NetBIOS_Computer_Name: HAVEN-DC
|   DNS_Domain_Name: raz0rblack.thm
|   DNS_Computer_Name: HAVEN-DC.raz0rblack.thm
|   Product_Version: 10.0.17763
|_  System_Time: 2026-06-16T13:53:52+00:00
| ssl-cert: Subject: commonName=HAVEN-DC.raz0rblack.thm
| Issuer: commonName=HAVEN-DC.raz0rblack.thm
| Public Key type: rsa
| Public Key bits: 2048
| Signature Algorithm: sha256WithRSAEncryption
| Not valid before: 2026-06-15T13:49:25
| Not valid after:  2026-12-15T13:49:25
| MD5:     a6fc 881e 3462 30f8 eff1 47c6 a121 b1ad
| SHA-1:   57c2 718c b65b 96ba 8a07 88c6 1035 fb94 0d6a 8a4f
| SHA-256: 535e 33fa 0913 9377 a142 1df0 0dad 4426 a1d3 91dc 5fe7 f7a4 c311 0d2c a804 81d1
| -----BEGIN CERTIFICATE-----
| MIIC8jCCAdqgAwIBAgIQG0bQsmWF1KxDDftSML39rjANBgkqhkiG9w0BAQsFADAi
| MSAwHgYDVQQDExdIQVZFTi1EQy5yYXowcmJsYWNrLnRobTAeFw0yNjA2MTUxMzQ5
| MjVaFw0yNjEyMTUxMzQ5MjVaMCIxIDAeBgNVBAMTF0hBVkVOLURDLnJhejByYmxh
| Y2sudGhtMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAlMV5eAn3A2U5
| LtYTuriKJ0eTigVji4IR6/5eVCW1DWweSmoi9l47lla3HE0hhukb7kdglT9XKIfC
| muYOBD3b9cjsUl4u2EY3WTi+a9CoW2aaZs2gGIaxrAhAH9hIcfmV1MQBbMlfxR8c
| E9YOxDsVKZvtW2GgrUdfR9Jpp39BGaziRsWL1WeHdtCcQ9Qu6yAMzLAupocPEjUx
| 0S4tNyUwBV4tlLTyTFgPiiO6Cc5zTIlYVZFonhy2xHjxwpM1XXdS0rRvwciQhehy
| 7AX7IBfkmGeynSIS2THxF3HbNuCIDoqN5aZqWbFO6UpJG6uQW7YuaWcvjb+lja+b
| TfzBGPOLXQIDAQABoyQwIjATBgNVHSUEDDAKBggrBgEFBQcDATALBgNVHQ8EBAMC
| BDAwDQYJKoZIhvcNAQELBQADggEBAAoGqkekm1dr1jNj+E8PlBaiqjhLe26wFZl3
| DzRWH00HHH9v4EjZh6WUO1RXHiX4WXKSxF41Z7iqnyU5+7IuAyUhVijJSe97cAWH
| 3fv1C9AGP9V3OT8PUwVJLlqkQMSMLPli7MafYu1xkVnlzoxfFvff4300/lwcJwXf
| 8SDKuxgDW7YDnpCQ4MYN18vAS/h4l8iGSbGxQojxz/vGcu/2DErpaewU3oxJqqN6
| pTd7Z+MKhTSXj10avGSbObAJlC72dL8ueP1cLjRcH/jbZk+D9/TmndKxyDt1ZANx
| Mzc7dhLdlwz1BVxqxFROLKC1SwN99x9luQse3ExSnyGaYLOhAqg=
|_-----END CERTIFICATE-----
5985/tcp  open  http          syn-ack ttl 126 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
9389/tcp  open  mc-nmf        syn-ack ttl 126 .NET Message Framing
47001/tcp open  http          syn-ack ttl 126 Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
49664/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49665/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49667/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49669/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49670/tcp open  ncacn_http    syn-ack ttl 126 Microsoft Windows RPC over HTTP 1.0
49671/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49673/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49677/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49697/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
49708/tcp open  msrpc         syn-ack ttl 126 Microsoft Windows RPC
Service Info: Host: HAVEN-DC; OS: Windows; CPE: cpe:/o:microsoft:windows
| smb2-time: 
|   date: 2026-06-16T13:53:57
|_  start_date: N/A
|_clock-skew: mean: -6h25m48s, deviation: 1s, median: -6h25m48s
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and require
```

## Enumeration
```bash
# Clock skew
sudo ntpdate -u $TARGET 
# 2. Check NFS exports
showmount -e $TARGET
```
**Output**
```
Export list for 10.130.134.39:
/users (everyone)
```

### Mount the share
```bash
mkdir -p ~/mnt/nfs
sudo mount -t nfs $TARGET:/users /mnt/nfs -o nolock,vers=3
```
### Explore the share
```bash
ls /home/kali/mnt/nfs
cat sbradley.txt
sudo cp ~/mnt/nfs/employee_status.xlsx ~/Desktop/TRY/machines/raz0rblack/
sudo umount ~/mnt/nfs
```

### Extract info from the xlsx
```bash
sudo unzip -p employee_status.xlsx xl/sharedStrings.xml | grep -oP '(?<=<t>).*?(?=</t>)' > employee_status.txt
cat employee_status.txt
```

**Output**
```
HAVEN SECRET HACKER's CLUB
Name's
Role
daven port
CTF PLAYER
imogen royce
tamara vidal
arthur edwards
carl ingram
CTF PLAYER (INACTIVE)
nolan cassidy
reza zaydan
ljudmila vetrova
CTF PLAYER, DEVELOPER,ACTIVE DIRECTORY ADMIN
rico delgado
WEB SPECIALIST
tyson williams
REVERSE ENGINEERING
steven bradley
STEGO SPECIALIST
chamber lin
CTF PLAYER(INACTIVE)
```
### Generate users list
```bash
#!/bin/bash

INPUT_FILE="users_raw.txt"
OUTPUT_FILE="Brute.txt"
FQDN="@raz0rblack.thm"

echo "administrator${FQDN}" > "$OUTPUT_FILE"
echo "guest${FQDN}" >> "$OUTPUT_FILE"

while read -r first_name last_name; do
    [ -z "$first_name" ] && continue
    
    first_initial="${first_name:0:1}"
    
    first_lower=$(echo "$first_name" | tr '[:upper:]' '[:lower:]')
    last_lower=$(echo "$last_name" | tr '[:upper:]' '[:lower:]')
    first_init_lower=$(echo "$first_initial" | tr '[:upper:]' '[:lower:]')
    
    echo "${first_lower}.${last_lower}${FQDN}" >> "$OUTPUT_FILE"
    echo "${first_lower}${last_lower}${FQDN}" >> "$OUTPUT_FILE"
    echo "${first_init_lower}${last_lower}${FQDN}" >> "$OUTPUT_FILE"
    echo "${first_init_lower}-${last_lower}${FQDN}" >> "$OUTPUT_FILE"
    echo "${first_init_lower}.${last_lower}${FQDN}" >> "$OUTPUT_FILE"
done < "$INPUT_FILE"

RESULTS=$(wc -l < "$OUTPUT_FILE")
echo "Generated $RESULTS usernames."
``` 

### Kerbrute user enumeration
```bash
kerbrute userenum -d raz0rblack.thm --dc 10.130.134.39 Brute.txt --safe
```
**Output**
```

```

## Current Stopping Point

The writeup currently reaches NFS loot, extracts names from `employee_status.xlsx`, generates candidate usernames, and starts Kerberos user enumeration. It still needs valid account discovery, initial access, privilege escalation, flags, and extraction of any later reusable chain.

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [showmount](../../../tools/recon/showmount.md)
- [kerbrute](../../../tools/recon/kerbrute.md)
- [NFS share abuse](../../../exploits/network-services/nfs-share-abuse.md)
