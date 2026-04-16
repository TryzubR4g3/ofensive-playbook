# CLAUDE.md

Project guide for Claude Code sessions working on this HackTheBox writeup collection.

---

## Project Purpose

Personal **second brain** for offensive security work. Three jobs:

1. **CTF writeups** — HackTheBox and TryHackMe machines, organized by difficulty.
2. **Tool reference** — per-tool notes that accumulate every command I actually use across machines and engagements (the "second brain" for tools).
3. **Bug bounty flows** — reusable methodology / playbook notes for recon, vulnerability discovery and exploitation patterns I apply to real-world bug bounty targets.

Every machine I finish becomes a writeup; every new tool / technique I use gets its own page that is linked from the README and cross-referenced from the writeups.

---

## Directory Layout

The repo root is called `HTB/` for historical reasons; content is not HTB-exclusive. HTB machines currently live at `Easy/`, `Medium/`, `Hard/`. When TryHackMe or bug bounty content lands, add it as a sibling folder (see "Where New Content Goes" below) — do not rename existing HTB paths.

```
HTB/
├── README.md                  # index — links only, no CVE details, no exploit prose
├── CLAUDE.md                  # this file
├── .gitignore
│
├── Easy/                      # HTB Easy machines — one .md per machine
│   ├── Silentium_HTB_Writeup.md
│   ├── Kobold-Writeup.md
│   ├── cctv.md
│   └── MonitorsFour.md
│
├── Medium/                    # HTB Medium machines
│   ├── DevArea.md
│   └── Overwatch.md
│
├── Hard/                      # HTB Hard machines (empty for now)
│
├── TryHackMe/                 # (to be created) — one subfolder per difficulty or one .md per room
│
├── bugbounty/                 # (to be created) — methodology flows, per-target notes, recon playbooks
│
├── tools/                     # one .md per tool — commands used + short description
│   ├── nmap.md
│   ├── ffuf.md
│   ├── gobuster.md
│   ├── curl.md
│   ├── sqlmap.md
│   ├── netcat.md
│   ├── ssh.md
│   ├── docker.md
│   ├── git.md
│   ├── netexec.md
│   ├── impacket.md
│   ├── smbclient.md
│   ├── responder.md
│   ├── dnstool.md
│   ├── kerbrute.md
│   ├── evil-winrm.md
│   ├── metasploit.md
│   ├── tcpdump.md
│   ├── strings.md
│   ├── john.md
│   ├── hashcat.md
│   └── powershell.md
│
├── exploits/                  # one .md per exploit / abuse / playbook
│   ├── mcp-api-injection.md
│   ├── flowise-mcp-rce.md
│   ├── hoverfly-middleware-rce.md
│   ├── motioneye-config-injection.md
│   ├── wcf-soap-injection.md
│   ├── cacti-rce.md
│   ├── apache-cxf-xop-lfi.md
│   ├── zoneminder-sqli.md
│   ├── mailhog-password-reset.md
│   ├── env-file-exposure.md
│   ├── default-credentials.md
│   ├── mssql-linked-server.md
│   ├── mssql-enumeration.md
│   ├── adidns-poisoning.md
│   ├── ntlm-capture-crack.md
│   ├── password-spraying.md
│   ├── kerberos-roasting.md
│   ├── smb-anonymous-enum.md
│   ├── nssm-service-abuse.md
│   ├── binary-credential-hunting.md
│   ├── systemd-service-credentials.md
│   ├── env-variable-enum.md
│   ├── tcpdump-credential-sniffing.md
│   ├── docker-group-escape.md
│   ├── sudo-bash-overwrite.md
│   ├── gogs-symlink-attack.md
│   ├── docker-api-unauthenticated.md
│   ├── ssh-tunneling.md
│   └── linux-enumeration.md
│
└── reference/                 # legacy HTML reference site (not actively maintained)
    ├── index.html
    ├── style.css
    ├── linux/{exploits,ffuf,gobuster,index}.html
    └── windows/{docker-api,index,post-exploitation}.html
```

---

## Where New Content Goes

| Thing I want to add | Location | Filename pattern |
|---------------------|----------|------------------|
| A new HTB machine writeup | `Easy/` / `Medium/` / `Hard/` based on HTB difficulty | `<Name>.md` (e.g. `Silentium.md`) |
| A new TryHackMe room writeup | `TryHackMe/<Easy|Medium|Hard>/` (create on first use) | `<RoomName>.md` |
| A command-reference for a new tool | `tools/` | lowercase tool name — `<tool>.md` |
| A new exploit / technique / abuse | `exploits/` | kebab-case descriptive name — `<what>-<how>.md` |
| A post-exploitation checklist / playbook | `exploits/` | `<os>-enumeration.md`, `<topic>-playbook.md` |
| A bug bounty methodology / flow note | `bugbounty/` (create on first use) | kebab-case — `<phase>-<topic>.md` (e.g. `recon-subdomain-enumeration.md`, `idor-testing-flow.md`) |
| Per-program bug bounty scratch notes (scope, findings, payloads) | `bugbounty/programs/<program>/` | `<program>.md` plus supporting files; keep private findings out of public commits |
| External writeups / cheatsheets I only reference | do not commit to the repo |  |

After creating a file, **always** add a link to it in `README.md` under the matching section.

---

## Content Rules

### Language
- **Writeups, tool notes, exploit notes, CLAUDE.md, README** → **English**. Hard rule, even when I ask for changes in Spanish.
- Conversation in chat stays in Spanish per system config.

### README
- Index only. Machines, tools, exploits — all links.
- **No** CVE tables, vulnerability descriptions, chains, or prose explanations. Everything technical belongs in the linked `.md` file.

### Writeups (`Easy/`, `Medium/`, `Hard/`, `TryHackMe/...`)
Expected structure (loose — don't enforce against existing files):
1. Target metadata (IP, domain, OS, difficulty)
2. Attack Chain Overview (ASCII arrow diagram)
3. Table of Contents
4. Reconnaissance
5. Initial Access
6. User flag steps
7. Privilege Escalation
8. Root flag
9. Key Takeaways / lessons learned
10. Cheat-sheet appendices (optional)

### Tool Notes (`tools/`)
- One-paragraph description at the top.
- `## Commands Used` section with every command that appears in the writeups, each annotated with `Used on: **<Machine>**`.
- Explain non-obvious flags inline.
- Do **not** invent commands that weren't actually used — tool notes reflect this repo's history, not upstream docs.

### Exploit / Abuse Notes (`exploits/`)
Template:
1. One-line summary + `Used on: **<Machine>**` list.
2. Short description of the technique and why it works.
3. Prerequisites (credentials, access, versions, network reachability).
4. Step-by-step commands (with attacker IPs / ports preserved from the writeups).
5. Variants / alternative payloads when relevant.
6. Defensive note is welcome but optional.

Cross-reference other notes by relative path (e.g. `see \`adidns-poisoning.md\``) — do not duplicate content.

### Enumeration Playbooks
- Tag each command with **[USED]** when it actually appears in a writeup, otherwise leave unmarked as "default playbook".
- Group commands by goal, not alphabetically (system context → container check → privileges → creds → cron → network → files → software).

### Bug Bounty Flow Notes (`bugbounty/`)
- Focus on **reusable methodology**, not per-target walkthroughs.
- Structure: phase (recon / discovery / exploitation / reporting) → goal → tool(s) → commands → what to look for.
- Cross-reference `tools/` and `exploits/` instead of duplicating.
- Keep program-specific scope, credentials and PoCs out of the repo if it is public — use `bugbounty/programs/` only if the git remote is private.

---

## Naming Conventions

- File names: kebab-case for exploits (`gogs-symlink-attack.md`), lowercase single word for tools (`ffuf.md`), CamelCase for machine writeups if that's what the machine already uses (consistency with existing files beats a hard rule).
- Section headers: title case.
- Inline code: fenced blocks with language hint (`\`\`\`bash`, `\`\`\`sql`, `\`\`\`powershell`, `\`\`\`json`, `\`\`\`xml`).

---

## Editing Workflow

1. Before creating a new note, grep for the topic — there might already be one to extend.
2. When adding a new tool / exploit, update `README.md` in the same change.
3. When editing a writeup, check if the commands belong in a tool or exploit note and link instead of duplicating prose.
4. Never embed raw flag values that I didn't personally capture — use placeholders (`<CAPTURED_TOKEN>`, `ATTACKER_IP`).
5. Commits are user-initiated. Don't commit unless explicitly asked.

---

## Non-Goals

- This repo is not a CVE encyclopedia. If I want CVE details, I'll go to NVD.
- Not a generic pentest methodology book. `exploits/` and `bugbounty/` notes capture **what I actually run**, not every known variant.
- `reference/` (the HTML mini-site) is legacy. Don't expand it — new content goes into the `.md` system.
