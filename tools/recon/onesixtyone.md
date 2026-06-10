# onesixtyone

Fast SNMP scanner used to brute-force community strings. It takes a list of IPs and a wordlist of community strings to find valid read or write strings.

## Commands Used

### Brute-force community strings
<!-- cmd: linux -->
```bash
onesixtyone -c /usr/share/seclists/Discovery/SNMP/common-snmp-community-strings.txt $TARGET
```
Used on: **operationtakeover**

discovered the `pr1v4t3` community string which granted write access.

## Related Notes

- [snmpwalk.md](./snmpwalk.md)
- [snmpset.md](./snmpset.md)
- [nmap.md](./nmap.md)
