# ldap-utils

OpenLDAP command-line utilities used to query and modify LDAP servers. In this repo they appear in rogue-LDAP setup for credential capture and in quick LDAP capability checks.

## Commands Used

### Apply a SASL security downgrade to a rogue LDAP server
<!-- cmd: linux -->
```bash
sudo ldapmodify -Y EXTERNAL -H ldapi:// -f ./olcSaslSecProps.ldif && sudo service slapd restart
```
Used on: **Breaching Active Directory**

`-Y EXTERNAL` - authenticate to local `slapd` through the external SASL mechanism
- `-H ldapi://` - use the local LDAP IPC socket
- `-f` - read changes from an LDIF file

### Check supported SASL mechanisms
<!-- cmd: linux -->
```bash
ldapsearch -H ldap://localhost -x -s base -b "" supportedSASLMechanisms
```
Used on: **Breaching Active Directory**

`-x` - simple authentication
- `-s base` - base-object search only
- `-b ""` - query the root DSE
