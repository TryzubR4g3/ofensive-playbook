# Active Directory Enumeration — Notes

## 1. Obtain Credentials

Visit the lab's credential distributor:

```
https://distributor.za.tryhackme.com/creds
```

Obtained credentials:

| Field    | Value            |
|----------|------------------|
| Username | connor.collins   |
| Password | Password1        |

---

## 2. Initial Access via SSH

```bash
ssh za.tryhackme.com\\connor.collins@thmjmp1.za.tryhackme.com
```

---

## 3. Credential Injection with Runas

From the Windows machine, inject the AD credentials into memory for network authentication:

```cmd
runas.exe /netonly /user:za.tryhackme.com\connor.collins cmd.exe
```

> The password is entered **interactively** when executing the command.

### Key Parameters

| Parameter  | Description |
|------------|-------------|
| `/netonly` | The credentials are only used for network connections, not for the local session. |
| `/user`    | Domain and user. Using FQDN is safer than NetBIOS. |
| `cmd.exe`  | The process to launch with the injected credentials. |

> ⚠️ With `/netonly`, the DC **does not validate** the password when running the command — it accepts any value. Verify it manually in the next step.

---

## 4. Configure DNS (Own Windows, not lab VM)

```powershell
$dnsip = "<DC IP>"
$index = Get-NetAdapter -Name 'Ethernet' | Select-Object -ExpandProperty 'ifIndex'
Set-DnsClientServerAddress -InterfaceIndex $index -ServerAddresses $dnsip
```

Verify resolution:

```cmd
nslookup za.tryhackme.com
```

---

## 5. Verify Credentials by Listing SYSVOL

Any domain account, no matter how unprivileged, can read SYSVOL:

```cmd
dir \\za.tryhackme.com\SYSVOL\
```

If it returns content → valid credentials and working DNS ✅

> 💡 SYSVOL can also contain **GPOs and scripts** with additional credentials. It's worth enumerating.

---

## 6. IP vs Hostname — Authentication Difference

| Method              | Authentication Used |
|---------------------|---------------------|
| `\\za.tryhackme.com\SYSVOL` | **Kerberos** (hostname in the ticket) |
| `\\<DC IP>\SYSVOL`          | **NTLM** (forces fallback) |

Using IP forces NTLM → useful for evading detection of **OverPass-the-Hash / Pass-the-Hash** attacks in red teams.

---

## 7. Enumeration with MMC + RSAT

### What is it?

Microsoft Management Console (MMC) with the **Remote Server Administration Tools (RSAT)** Snap-Ins allows a complete graphical view of the AD environment. It is launched from the CMD opened with `runas /netonly` so it uses the injected credentials.

### Install RSAT (only if using your own Windows)

`Start → Apps & Features → Manage Optional Features → Add a feature → "RSAT: Active Directory Domain Services and Lightweight Directory Tools"`

### Configure MMC

```
Start → Run → mmc
```

Once opened:

1. `File → Add/Remove Snap-in`
2. Add the **3 Active Directory Snap-ins**
3. Click through the warnings/errors to ignore them
4. Right-click on **AD Domains and Trusts** → *Change Forest* → `za.tryhackme.com`
5. Right-click on **AD Sites and Services** → *Change Forest* → `za.tryhackme.com`
6. Right-click on **AD Users and Computers** → *Change Domain* → `za.tryhackme.com`
7. Right-click on **AD Users and Computers** (left panel) → `View → Advanced Features`

### What can be enumerated

| Object         | Path in MMC                                      |
|----------------|--------------------------------------------------|
| Users          | AD Users and Computers → za → People → [dept OU] |
| Servers        | AD Users and Computers → za → Servers            |
| Workstations   | AD Users and Computers → za → Workstations       |
| Groups         | Properties of any user → Member Of               |
| Attributes     | Right-click on object → Properties               |

> 💡 With sufficient permissions, you can also **modify objects**: change passwords, add users to groups, etc.

### Pros and Cons

| ✅ Pros | ❌ Cons |
|------------|----------------|
| Holistic view of the domain | Requires GUI access to the machine |
| Fast search of objects | Does not allow massive collection of attributes |
| Direct modification of AD objects | — |

---

## 8. Enumeration with CMD — `net` command

Useful when no GUI is available, defenders monitor PowerShell, or executing from a RAT/payload.

> ⚠️ Requires a **domain-joined** machine. On a non-joined machine, it returns info from the WORKGROUP.

### Users

```cmd
net user /domain
```
Lists all users in the domain.

```cmd
net user <username> /domain
```
Details of a user: account status, password policy, groups (up to 10).

### Groups

```cmd
net group /domain
```
Lists all groups in the domain.

```cmd
net group "Tier 1 Admins" /domain
```
Lists the members of a specific group.

### Password Policy

```cmd
net accounts /domain
```

Returns key information for planning **password spraying**:

| Field                        | Relevance for attack                          |
|------------------------------|-----------------------------------------------|
| Lockout threshold            | Max attempts before locking account           |
| Lockout duration             | Lockout time if threshold is exceeded         |
| Minimum password length      | Guide for building wordlists                  |
| Maximum password age         | Indicates if passwords rotate                 |
| Password history             | How many old passwords are not reused         |

### Pros and Cons

| ✅ Pros | ❌ Cons |
|------------|----------------|
| No external tools, often unmonitored | Only works from a domain-joined machine |
| Does not require GUI | Groups truncated to 10 in user details |
| Compatible with VBScript/phishing macros | — |

---

## 9. Enumeration with PowerShell — AD-RSAT cmdlets

Access from CMD with: `powershell`

> Cmdlets are installed automatically with RSAT (Task 3). They allow targeting a specific domain/server without being joined to the domain.

### Users

```powershell
# Full detail of a user
Get-ADUser -Identity gordon.stevens -Server za.tryhackme.com -Properties *

# Filter users by name
Get-ADUser -Filter 'Name -like "*stevens"' -Server za.tryhackme.com | Format-Table Name,SamAccountName -A
```

| Parameter     | Description                                      |
|---------------|--------------------------------------------------|
| `-Identity`   | Account name to query                            |
| `-Properties` | Attributes to display (`*` = all)                |
| `-Server`     | DC to query (necessary without domain-join)      |
| `-Filter`     | Search filter with `-like`, `-gt` operators      |

### Groups

```powershell
# Group info
Get-ADGroup -Identity Administrators -Server za.tryhackme.com

# Group members
Get-ADGroupMember -Identity Administrators -Server za.tryhackme.com
```

### Generic AD Objects

```powershell
# Objects modified after a date
$ChangeDate = New-Object DateTime(2022, 02, 28, 12, 00, 00)
Get-ADObject -Filter 'whenChanged -gt $ChangeDate' -includeDeletedObjects -Server za.tryhackme.com

# Accounts with bad password attempts (useful before password spraying)
Get-ADObject -Filter 'badPwdCount -gt 0' -Server za.tryhackme.com
```

> 💡 Filtering `badPwdCount -gt 0` before spraying prevents locking out accounts that already have accumulated failed attempts.

### Domain

```powershell
Get-ADDomain -Server za.tryhackme.com
```

Returns domain containers, DNS root, DC container, etc.

### Modifying Objects (Exploitation, not enumeration)

```powershell
# Force password change
Set-ADAccountPassword -Identity gordon.stevens -Server za.tryhackme.com `
  -OldPassword (ConvertTo-SecureString -AsPlaintext "old" -force) `
  -NewPassword (ConvertTo-SecureString -AsPlainText "new" -Force)
```

### Pros and Cons

| ✅ Pros | ❌ Cons |
|------------|----------------|
| Much more info than CMD's `net` | PowerShell is more heavily monitored by Blue Teams |
| Works from non-domain-joined machine with `-Server` | Requires installing RSAT or external scripts |
| Allows creating/modifying AD objects | — |

---

## 10. Enumeration with BloodHound + SharpHound

### Key Concept

> "Defenders think in lists, Attackers think in graphs."

BloodHound visualizes the AD environment as a **graph of nodes and edges**, revealing attack paths that traditional lists do not show. It uses **Neo4j** as a backend database.

**SharpHound** is the data collector → **BloodHound** is the visualization GUI.

### Collector Types (SharpHound)

| Collector            | Description |
|----------------------|-------------|
| `SharpHound.exe`     | Windows executable. The most common |
| `SharpHound.ps1`     | PS script. Loadable in memory (evades AV on disk). Deprecated |
| `AzureHound.ps1`     | For Azure / AAD environments |

> ⚠️ BloodHound and SharpHound versions **must match**. This lab uses **v4.1.0**.

### Run SharpHound

```powershell
# Copy to working directory
copy C:\Tools\Sharphound.exe ~\Documents\
cd ~\Documents\

# Full execution (first time)
.\SharpHound.exe --CollectionMethods All --Domain za.tryhackme.com --ExcludeDCs

# Subsequent executions (only active sessions, faster)
.\SharpHound.exe --CollectionMethods Session --Domain za.tryhackme.com --ExcludeDCs
```

| Parameter             | Description |
|-----------------------|-------------|
| `--CollectionMethods` | `All` = everything; `Session` = only active sessions |
| `--Domain`            | Domain to enumerate |
| `--ExcludeDCs`        | Do not touch Domain Controllers → less noise/alerts |

Generates a **timestamped ZIP** with the data in the current directory.

### Transfer the ZIP to Kali

```bash
scp <user>@THMJMP1.za.tryhackme.com:C:/Users/<user>/Documents/<file.zip> .
```

### Start BloodHound (Kali/AttackBox)

```bash
neo4j console start      # Start database (port 7687)
bloodhound --no-sandbox  # In another terminal
```

Default Neo4j credentials: `neo4j:neo4j`

Import: drag the ZIP to the BloodHound GUI.

### What can be seen in BloodHound

**Node Info** (clicking on a user node):

| Section                 | What it shows |
|-------------------------|-------------|
| Overview                | Active sessions, reach to high-value targets |
| Node Properties         | Display name, title |
| Extra Properties        | Distinguished name, creation date |
| Group Membership        | User's groups |
| Local Admin Rights      | Hosts where they have local admin |
| Execution Rights        | Capability of RDP, PSRemote, etc. |
| Outbound Control Rights | AD objects this user can modify |
| Inbound Control Rights  | Objects that can modify this user |

**Analysis Queries** (pre-built):
- *Find all Domain Admins*
- *Shortest Paths to Domain Admins*
- *Find Principals with DCSync Rights*, etc.

### Attack Path Example

```
[AD User] --RDP--> THMJMP1 <--Active Session-- [T1 Admin]
                           |
                   Privilege Escalation
                           |
                        Mimikatz
                           |
                  NTLM hash T1 Admin
```

### Periodic Collection Strategy

| Time                  | Method    | Reason |
|-----------------------|-----------|--------|
| Start of assessment   | `All`     | Full domain structure |
| ~10:00 AM             | `Session` | Users starting their workday |
| ~2:00 PM              | `Session` | Users returning from lunch |

> Clean old sessions: *Database Info → Clear Session Information* before each session import.

### Pros and Cons

| ✅ Pros | ❌ Cons |
|------------|----------------|
| Full graphical view of the domain | SharpHound is noisy and detectable by AV/EDR |
| Shows attack paths automatically | — |
| Deep insights without manual queries | — |

---

## 11. Additional Enumeration Techniques

Besides those covered in this lab, other relevant techniques:

| Technique | Description | Reference |
|---------|-------------|------------|
| **LDAP Enumeration** | Any valid credential can bind to the DC via LDAP and query AD objects | [HackTricks LDAP](https://book.hacktricks.xyz/pentesting/pentesting-ldap) |
| **PowerView** | Recon script from the PowerSploit project. Allows semi-manual enumeration of AD objects | [GitHub PowerView](https://github.com/PowerShellMafia/PowerSploit/blob/master/Recon/PowerView.ps1) |
| **WMI (Windows Management Instrumentation)** | Uses the `root\directory\` provider to interact with AD from PowerShell/CMD | [WMI AD Enum](https://0xinfection.github.io/posts/wmi-ad-enum/) |

---

## 12. Mitigations and Detection

AD enumeration is hard to defend against because it mimics legitimate traffic. Some countermeasures:

- **SharpHound** generates an abnormal amount of LogOn events from a single account → detection rules can be created for this pattern.
- Create **signature/detection** rules for known binaries: SharpHound, RSAT tools, etc.
- **Monitor CMD and PowerShell usage** from unauthorized accounts.
- Defenders themselves can run these techniques periodically to **identify and fix misconfigurations** before an attacker does.

> The next step after enumeration is **privilege escalation and lateral movement** to reach a position from which to execute attacks.

---

## 13. Using Injected Credentials in Applications

With CMD opened via `runas /netonly`, **all network connections** from that process will use the injected credentials:

- SQL Server Management Studio → transparent Windows authentication
- Web applications with Windows Auth
- AD enumeration tools (BloodHound, etc.)