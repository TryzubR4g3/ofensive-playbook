# Second Brain — Offensive-Security Notebook

Personal, CLI-searchable knowledge base for offensive security work. The repo is **tool- and exploit-centric** — writeups are just the narrative shell. The real value is in `tools/` + `exploits/`, accessible from the terminal via the `brain` CLI.

- **`tools/`** — per-tool command notes (every flag I've actually used, tagged by machine).
- **`exploits/`** — per-technique playbooks (prerequisites, step-by-step, defensive notes).
- **`HTB/`, `TRY/`** — machine writeups that link to the reusable notes above.
- **`brain` CLI** — grep / list / recall without leaving the terminal.

---

## `brain` CLI

Topic-scoped search for tools, exploit playbooks and writeups. Tool notes do not keep writeup backlink lists; writeups link out to the reusable notes, and `brain backrefs` derives backlinks from those writeup links when you need them.

```bash
./brain guide                  # beginner examples: "what should I type?"
./brain <topic> [keyword]      # grep keyword inside a curated topic scope
./brain topics                 # list every topic with a one-line description

./brain find    <query>        # easy alias for broad search
./brain search  <query>        # case-insensitive grep across every .md
./brain cmd     <query>        # grep inside fenced code blocks only
./brain tool    [name]         # cat a tool note (or list all)
./brain exploit [name]         # cat an exploit note (or list all)
./brain writeup [name]         # cat a writeup (or list all)
./brain list    [tools|exploits|writeups|all]
./brain used-on <Machine>      # every note tagged "Used on: <Machine>"
./brain backrefs <note>        # every writeup that links to <note>
./brain open    <path>         # open in $EDITOR
```

Zero deps — pure Python 3. Works on Linux and Git Bash on Windows.

Spanish-friendly aliases exist for beginners: `guia`, `temas`, `buscar`, `comandos`, `herramienta`, `credenciales`, `privilegios`, `contenedor`, `base-datos`.

### Topics

| Topic | Covers |
|-------|--------|
| `recon` | Port scan, banner grab, directory brute |
| `enumeration` (`enum`) | Post-foothold system / AD / network enumeration |
| `fuzz` | Directory / vhost / parameter fuzzing |
| `exploit` | All exploit playbooks |
| `privesc` | Local privilege escalation (Linux + Windows) |
| `shells` | Reverse-shell one-liners and listener patterns |
| `creds` | Credential hunting, cracking, reuse |
| `pivot` | Port forwarding and tunnelling |
| `ad` | Active Directory / Kerberos / SMB / LDAP |
| `web` | Web / HTTP exploitation |
| `container` (`docker`) | Container / Docker abuse — incl. in-container enumeration |
| `stego` | Steganography / metadata loot |
| `reversing` (`re`, `binary`) | SUID / custom binary reverse engineering |
| `database` (`db`, `mongodb`, `sqlite`, `nosql`) | Backend DB enumeration & abuse (Mongo, SQLite, MySQL, Redis) |
| `sqli`, `lfi`, `rce` | Exactly what they say |

### Typical flow

```bash
./brain enumeration find              # every `find` command in enum tools/exploits
./brain fuzz ffuf                     # every ffuf invocation in fuzz-scoped files
./brain privesc sudo                  # privesc notes that mention sudo
./brain creds grep                    # credential-hunting greps
./brain ad kerberos                   # AD/Kerberos-specific commands
./brain web curl                      # curl usage in web exploits
./brain shells                        # all reverse-shell one-liners (scope list)
./brain used-on Overwatch             # every tool/exploit tagged with that machine
./brain exploit bash-eval             # exact match on an exploit note name
```

Output pattern (example - `brain enumeration find`):

```
exploits\linux-enumeration.md
  :77  find / -perm -4000 -type f 2>/dev/null      # [USED — DevArea]
  :92  ## Password & Credential Hunting with `find`
  used by:        # derived from writeup links, not stored in the tool note
    TRY\Easy\lazyadmin.md:179  Standard [Linux enumeration](exploits/enumeration/linux-enumeration.md)...
    HTB\Easy\cctv.md:210       [linux-enumeration.md](exploits/enumeration/linux-enumeration.md)
```
---

