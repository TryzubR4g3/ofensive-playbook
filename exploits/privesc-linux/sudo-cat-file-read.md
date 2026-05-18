# Sudo `cat` Arbitrary File Read

NOPASSWD `sudo` access to `/bin/cat` can read root-owned files, including flags and credential stores.

Used on: **bsidesgtdav**

## Why It Works

If `sudo -l` allows a low-privileged user to run `/bin/cat` as root without a password, the user can read any file that root can read.

## Prerequisites

- Shell as the low-privileged user.
- `sudo -l` grants `/bin/cat` with `NOPASSWD`.

## Steps

```bash
sudo -l
/bin/cat /etc/shadow
/bin/cat /root/root.txt
```

## Notes

- This is file-read privilege escalation, not necessarily an interactive root shell.
- Pair with credential cracking if `/etc/shadow` hashes are useful.

