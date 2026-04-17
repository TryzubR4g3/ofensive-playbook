# nmap

Network scanner used for port discovery, service detection and version fingerprinting. Usually the first step of every engagement to map open ports and running services on the target.

## Commands Used

### Full TCP scan with service/version detection + default scripts
```bash
nmap -sC -sV -p- TARGET_IP
```
Used on: **Kobold**, **CCTV**, **DevArea**

- `-sC` — run default NSE scripts
- `-sV` — detect service versions
- `-p-` — scan all 65535 TCP ports

### Targeted scan against specific AD ports (no ping, no DNS)
```bash
nmap -sVC -p53,88,135,139,389,445,464,593,636,3268,3269,3389,5985,6520,9389,49664,49667,49958,49959,55427,57249,59340,59343 -Pn -n TARGET_IP
```
Used on: **Overwatch**

- `-sVC` — combined service detection + default scripts
- `-Pn` — skip host discovery (treat as online)
- `-n` — no DNS resolution

### Two-phase: fast stealth discovery → targeted service scan
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

### Focused HTTP/WinRM check
```
80/tcp    open  http    nginx
5985/tcp  open  http    Microsoft HTTPAPI httpd 2.0
```
Used on: **MonitorsFour**
