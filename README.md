# 🧠 brain — Offensive Security Second Brain

78 tools · 89 exploits · 36 privesc · 31 techniques · 9 playbooks · 11 payloads · 71 writeups

This repository is **tool-, exploit- and technique-centric**. Writeups exist as narratives, but the real value lives in the reusable playbooks and command references, instantly searchable via the `brain` CLI.

## Quick Start

The `./brain` (or `python brain.py`) CLI is the primary way to interact with this repository.

```bash
./brain guide                            # beginner examples and recipes
./brain recon nmap                       # every nmap command I've ever run
./brain privesc sudo                     # privilege escalation exploits matching "sudo"

# Global Search
./brain search "bash -i"                 # broad text search across the entire repo
./brain cmd  "find /"                    # grep only inside fenced code blocks

# Inline File Search (New)
./brain tool metasploit search route     # grep a keyword inside a specific tool note
./brain exploit eternalblue search nmap  # grep a keyword inside a specific exploit note
./brain writeup Billing search nc        # grep a keyword inside a specific writeup

# Listing & Viewing
./brain list all                         # list all tools, exploits, payloads, writeups
./brain tool nmap                        # show the full nmap tool note
```

## Available Topics

Search by topic to limit results to a specific phase or domain (`./brain <topic> <keyword>`).

| Topic         | Aliases                          | Description |
|---------------|----------------------------------|-------------|
| `recon`       | `reconnaissance`                 | Port scanning, banner grabbing, service discovery |
| `enumeration` | `enum`                           | Post-foothold system, AD, and network enumeration |
| `fuzz`        |                                  | Directory, vhost, and parameter fuzzing |
| `exploit`     |                                  | Raw exploit playbooks and PoCs |
| `privesc`     | `escalation`                     | Local privilege escalation (Linux + Windows) |
| `shells`      | `shell`, `reverse-shell`         | Reverse-shell one-liners and listener setups |
| `payloads`    | `payload`                        | Reusable payload snippets and shell stabilization |
| `creds`       | `credentials`, `password`        | Credential hunting, extraction, and cracking |
| `ad`          | `active-directory`, `kerberos`   | Active Directory, Kerberos, SMB, LDAP |
| `web`         | `http`                           | Web vulnerability exploitation |
| `webdav`      |                                  | WebDAV enumeration and exploitation |
| `xss`         | `cross-site-scripting`           | Cross-site scripting techniques |
| `container`   | `docker`, `k8s`                  | Container, Docker, and orchestration abuse |
| `stego`       | `steganography`                  | Steganography and metadata loot |
| `sqli`        | `sql`                            | SQL injection techniques |
| `lfi`         |                                  | Local File Inclusion and arbitrary read |
| `rce`         |                                  | Remote Code Execution chains |
| `reversing`   | `reverse`, `binary`, `re`        | Binary reverse engineering (SUID, custom bins) |
| `database`    | `db`, `mongodb`, `nosql`         | Backend DB enumeration & abuse |
| `crypto`      | `padding`, `oracle`              | Token prediction, padding oracles, weak crypto |
| `pivot`       | `pivoting`, `tunnel`             | Port forwarding, tunnelling, pivots |

## Architecture

* **`tools/`**: Command references. "What exact flag did I use"
* **`exploits/`**: Real exploitation chains: CVEs, RCEs, auth bypasses.
* **`privesc/`**: Local privilege escalation for Linux and Windows.
* **`techniques/`**: Theory and methodology (SQLi, XSS, Stego, Crypto).
* **`playbooks/`**: Checklists and enumeration flows.
* **`payloads/`**: Reusable code (webshells, persistence scripts).
* **`writeups/`**: Machine walkthroughs (`HTB/`, `TRY/`, `OffSec/`, `Webverselabs/`).

Writeups link to the techniques. The CLI reverse-indexes those links to show exactly which boxes a technique was used on.
