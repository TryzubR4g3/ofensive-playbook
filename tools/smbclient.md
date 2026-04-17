# smbclient

FTP-like interactive client for SMB shares. Used for anonymous enumeration, downloading files and recursively mirroring shares like SYSVOL.

## Commands Used

### Anonymous access to a specific share
```bash
smbclient //TARGET_IP/software$ -N
```
Used on: **Overwatch**

- `-N` — no password (null session)

### Recursive download of SYSVOL
```bash
smbclient //TARGET_IP/SYSVOL -U overwatch.htb/sqlsvc%'TI0LKcfHzZw1Vv' \
  -c "recurse ON; prompt OFF; cd overwatch.htb; mget *"
```
Used on: **Overwatch**

- `-U DOMAIN/USER%PASSWORD` — inline credentials
- `-c` — run a semicolon-separated command list non-interactively
- `recurse ON; prompt OFF; mget *` — recursive mass-get without prompting
