# snmpwalk

SNMP application that uses SNMP GETNEXT requests to query a network entity for a tree of information. It automatically performs a series of chained GETNEXT requests past the OID specified.

## Commands Used

### Walk the entire MIB tree
<!-- cmd: linux -->
```bash
snmpwalk -v2c -c pr1v4t3 $TARGET
```
Used on: **operationtakeover**

full enumeration of the device using the discovered `pr1v4t3` community string.

### Walk a specific OID subtree
<!-- cmd: linux -->
```bash
snmpwalk -v2c -c pr1v4t3 $TARGET .1.3.6.1.4.1.8072.1.3.2
```
Used on: **operationtakeover**

walked the `NET-SNMP-EXTEND-MIB` output table to trigger and read the results of an injected command.

## Related Notes

- [onesixtyone.md](./onesixtyone.md)
- [snmpset.md](./snmpset.md)
