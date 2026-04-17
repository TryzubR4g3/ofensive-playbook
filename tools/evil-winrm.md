# evil-winrm

Ruby-based interactive shell over WinRM (port 5985/5986). Used to access Windows boxes once valid credentials are recovered and the user is a member of `Remote Management Users`.

## Commands Used

### Connect with plaintext credentials
```bash
evil-winrm -i TARGET_IP -u 'sqlmgmt' -p 'bIhBbzMMnB82yx'
```
Used on: **Overwatch**

- `-i` — target IP
- `-u` / `-p` — username / password

Once inside, standard PowerShell cmdlets are available (`type`, `Get-ChildItem`, `Invoke-RestMethod`, registry queries, etc.).
