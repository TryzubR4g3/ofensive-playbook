# bloodhound-python / BloodHound

`bloodhound-python` collects Active Directory data over LDAP + SMB and produces JSON files that BloodHound ingests. Once loaded, BloodHound renders ACL / group / session paths to valuable principals (Domain Admins, krbtgt, etc.), surfacing abuse routes that would take hours to find manually.

## Commands Used

### Full collection with a valid domain user
```bash
bloodhound-python \
  -u wallace.everette -p 'Welcome2026@' \
  -d logging.htb -dc DC01.logging.htb \
  -ns $TARGET -c All --zip
```
Used on: **Logging**

collected All  revealed `svc_recovery  GenericWrite  MSA_HEALTH$`.

### Collect with password-cracked domain user

```bash
bloodhound-python \
  -d windcorp.thm \
  -u buse \
  -p 'uzunLM+3131' \
  -ns $TARGET \
  -c All \
  --zip
```
Used on: **Ra**

Key finding: `buse` ∈ Account Operators → GenericAll over `brittanycr`.
Account Operators can reset any non-admin user's password without knowing the current one.


Flags:
- `-u` / `-p` — domain creds
- `-d` — domain FQDN
- `-dc` — DC FQDN (avoids DNS surprises)
- `-ns` — explicit DNS server (usually the DC)
- `-c All` — all collection methods (Group, LocalAdmin, Session, Trusts, ACL, ObjectProps, etc.)
- `--zip` — single zip ready to drag into the UI

### Minimal / stealthier
```bash
bloodhound-python -u <USER> -p <PASS> -d <DOMAIN> -dc <DC> -ns <DC_IP> -c Group,ACL,ObjectProps --zip
```

### Auth via hash instead of password
```bash
bloodhound-python -u <USER> --hashes ':<NT_HASH>' -d <DOMAIN> -dc <DC> -ns <DC_IP> -c All --zip
```

### Auth via Kerberos ticket
```bash
export KRB5CCNAME=$(pwd)/<USER>.ccache
bloodhound-python -k --no-pass -u <USER> -d <DOMAIN> -dc <DC> -ns <DC_IP> -c All --zip
```

## Loading in BloodHound

1. Open BloodHound, log in to the Neo4j DB.
2. Drag & drop the zip onto the window.
3. Mark owned principals: `Node Info`  _Mark User as Owned_.
4. Run built-in queries: _Shortest Paths to Domain Admins_, _Find Principals with DCSync Rights_, _Shortest Paths from Owned_.

## Useful queries surfaced during this repo

| Query | Machine | Result |
|-------|---------|--------|
| Shortest Path from Owned → DA | Logging | `svc_recovery → GenericWrite → MSA_HEALTH$ → (Shadow Creds) → DC path` |
| Principals with GenericWrite on Computers | Logging | Exposed MSA target |
| Members of Account Operators | Ra | `buse` → GenericAll over `brittanycr` |

## Related
- [Shadow Credentials playbook](../../exploits/ad/shadow-credentials.md)
- [impacket](../windows/impacket.md) — TGT handling after BloodHound picks a target
- [SharpHound + BloodHound GUI (Windows collector)](../ad/bloodhound.md)


