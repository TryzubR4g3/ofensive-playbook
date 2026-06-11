# Infrastructure Discovery Playbook

**Goal**: Map out the network infrastructure, identify live hosts, open ports, and running services on internal or external networks.

## 1. Host Discovery
Find live hosts within a CIDR range.

<!-- cmd: linux -->
```bash
# [USED]
nmap -sn 10.10.10.0/24
```

<!-- cmd: linux -->
```bash
# [USED]
netdiscover -r 10.10.10.0/24
```

## 2. Comprehensive Port Scanning
Scan all 65535 ports to find open services.

<!-- cmd: linux -->
```bash
# [USED]
nmap -p- -T4 --min-rate=1000 -v <TARGET_IP>
```

## 3. Service and Version Detection
Identify exact versions and configurations of running services.

<!-- cmd: linux -->
```bash
# [USED]
nmap -p <OPEN_PORTS> -sV -sC -A <TARGET_IP>
```

## 4. UDP Port Scanning
Identify common UDP services like SNMP, DNS, or TFTP.

<!-- cmd: linux -->
```bash
# [USED]
nmap -sU --top-ports 100 -v <TARGET_IP>
```

## 5. Vulnerability Scanning
Run nmap vulnerability scripts against discovered services.

<!-- cmd: linux -->
```bash
# [USED]
nmap -p <OPEN_PORTS> --script vuln <TARGET_IP>
```

## Related
- [nmap.md](../../tools/network/nmap.md)
