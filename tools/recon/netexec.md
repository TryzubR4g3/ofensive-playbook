# netexec (nxc)

Swiss-army knife for post-exploitation against Windows/AD networks. Successor of CrackMapExec. Used for SMB/LDAP/MSSQL enumeration, authentication validation and password spraying.

## Commands Used

### Check anonymous/guest SMB shares
<!-- cmd: linux -->
```bash
netexec smb overwatch.htb -u '' -p '' --shares
netexec smb TARGET_IP -u 'guest' -p '' --shares
```
Used on: **Overwatch**

### Validate MSSQL credentials (non-standard port)
<!-- cmd: linux -->
```bash
netexec mssql TARGET_IP -u sqlsvc -p 'TI0LKcfHzZw1Vv' --port 6520
```
Used on: **Overwatch**

### Check sysadmin role via query
<!-- cmd: linux -->
```bash
netexec mssql TARGET_IP -u sqlsvc -p 'TI0LKcfHzZw1Vv' --port 6520 \
  -q "SELECT IS_SRVROLEMEMBER('sysadmin');"
```
Used on: **Overwatch**

### Retrieve domain password policy
<!-- cmd: linux -->
```bash
netexec smb TARGET_IP -u sqlsvc -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --pass-pol
```
Used on: **Overwatch**

### LDAP user enumeration
<!-- cmd: linux -->
```bash
netexec ldap TARGET_IP -u sqlsvc -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --users
```
Used on: **Overwatch**

### SMB password spraying against a user list
<!-- cmd: linux -->
```bash
netexec smb TARGET_IP -u users.txt -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --continue-on-success
```
Used on: **Overwatch**

### LDAP spraying (stealthier than SMB)
<!-- cmd: linux -->
```bash
netexec ldap TARGET_IP -u users.txt -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --continue-on-success
```
Used on: **Overwatch**



### SMB credential validation from user/password lists
<!-- cmd: linux -->
```bash
netexec smb 10.130.191.119 -u users.txt -p passwords.txt --continue-on-success
```
Used on: **coldvvars**

validated SMB credentials extracted from the web login/XPath path.

### Validate SMB credentials and list shares

<!-- cmd: linux -->
```bash
netexec smb $TARGET -u lilyle -p 'ChangeMe#1234'
netexec smb $TARGET -u lilyle -p 'ChangeMe#1234' --shares
```

Used on: **Ra**

Confirmed `lilyle:ChangeMe#1234` after password reset via security-question abuse on
`fire.windcorp.thm`. Shares output revealed `Spark 2.8.3` installers and the `Users`
share with active user directories.

### Check WinRM access before connecting

<!-- cmd: linux -->
```bash
netexec winrm $TARGET -u buse -p 'uzunLM+3131'
```

Used on: **Ra**

Verified WinRM access for `buse` after cracking the NTLMv2 hash. Confirmed
`[+] windcorp.thm\buse:uzunLM+3131 (Pwn3d!)` before launching `evil-winrm`.
