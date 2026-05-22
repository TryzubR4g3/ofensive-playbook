# SNMP Enumeration Playbook

A structured methodology for enumerating SNMP services on target machines. SNMP often leaks extensive system information, running processes, software versions, and occasionally plain text credentials. If write access is obtained, it can lead directly to remote code execution.

## 1. Initial Discovery

Scan for SNMP on UDP port 161.

```bash
# [USED]
nmap -sU -p 161 $TARGET
```

## 2. Community String Brute-force

SNMPv1 and v2c use community strings for authentication. Attempt to discover valid strings using common lists.

```bash
# [USED]
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $TARGET
```

## 3. Full MIB Walk (Read)

If a valid community string is found (e.g., `public`, `private`, `pr1v4t3`), walk the entire tree to gather system information.

```bash
# [USED]
snmpwalk -v2c -c <community_string> $TARGET
```

Review the output for:
- Operating system version and architecture (`sysDescr`)
- Running processes (`hrSWRunName`, `hrSWRunParameters`)
- Network interfaces and routing tables (`ipRouteTable`)
- Installed software (`hrSWInstalledName`)
- Hardcoded passwords or scripts in process arguments

## 4. Write Access Verification

If the community string hints at privileged access (e.g., `private`, `admin`), attempt a harmless write operation to confirm `write` privileges.

```bash
# [USED]
snmpset -v2c -c <community_string> $TARGET .1.3.6.1.2.1.1.5.0 s "TestName"
snmpget -v2c -c <community_string> $TARGET .1.3.6.1.2.1.1.5.0
```

## 5. Exploitation (NET-SNMP-EXTEND-MIB)

If write access is confirmed on a Unix/Linux target running Net-SNMP, check if `NET-SNMP-EXTEND-MIB` is loaded. This allows executing arbitrary commands.

Refer to: [snmp-extend-mib-rce.md](../../exploits/network-services/snmp-extend-mib-rce.md)
