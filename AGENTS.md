# AGENTS.md

Project guide for Codex sessions working on this second-brain repo.

---

## Repo Philosophy (READ FIRST)

This repo is **tool-, exploit- and technique-centric**, not writeup-centric.

The writeups in `writeups/HTB/` and `writeups/TRY/` are narratives — they exist so I remember what happened on a specific box. But the reusable value lives in:

- `tools/` — per-tool command notes (every flag I actually used).
- `exploits/` — raw exploit playbooks and proofs of concept.
- `privesc/` — local privilege escalation for Linux and Windows.
- `techniques/` — theory and methodology (SQLi, XSS, Stego, Crypto).
- `playbooks/` — checklists and enumeration flows.
- `payloads/` — reusable payload snippets and webshells.

When a writeup introduces something new (a command pattern, an abuse, a reverse-shell one-liner, a `find` recipe to hunt credentials), **the technique must be extracted into the appropriate reference directory** in the same change. The writeup should be a short summary + chain + links — not a dumping ground for commands.

### Why
I want to search for things from the CLI. "Give me every credential-hunting `find` I have ever used", "show me the reverse-shell one-liner I used on box X", "list every eval-bypass trick I know" — all of that comes from querying `brain`, not from re-reading writeups.

### `brain` CLI

`brain.py` + `brain` (bash wrapper) in the repo root is the search interface. **Topic-scoped**: first arg is a phase/topic (`enumeration`, `recon`, `fuzz`, `exploit`, `privesc`, `shells`, `creds`, `pivot`, `ad`, `web`, `container`, `stego`, `sqli`, `lfi`, `rce`, `reversing`, `database`), second arg is a keyword grep inside that scope. Every hit prints the file:line and, when useful, writeups that link to that note. Useful aliases: `enum`, `re` / `binary` -> `reversing`, `docker` -> `container`, `db` / `mongodb` / `sqlite` / `nosql` -> `database`.

```
./brain guide                # beginner examples: "what should I type?"
./brain <topic> [keyword]    # topic-scoped grep
./brain topics               # list every topic

./brain search <query>       # raw grep across every .md (case-insensitive)
./brain cmd    <query>       # grep inside fenced code blocks only
./brain tool   [name]        # cat a tool note (or list all)
./brain exploit [name]       # cat an exploit note (or list all)
./brain writeup [name]       # cat a writeup (or list all)
./brain list   [tools|exploits|writeups|all]
./brain used-on <Machine>    # all notes tagged "Used on: <Machine>"
./brain backrefs <note>      # writeups that link to <note>
./brain open <path>          # open in $EDITOR
```

Examples:

```
./brain enumeration find     # every `find` in enum-scoped files
./brain fuzz ffuf            # every ffuf invocation I've actually run
./brain privesc sudo         # privesc notes mentioning sudo
./brain web curl             # curl usage inside web-exploit notes
./brain ad kerberos          # AD-scoped Kerberos commands
./brain exploit bash-eval    # exact exploit name → shows full note
./brain container getcap     # in-container enumeration commands
./brain reversing objdump    # SUID reversing assembly cookbook
./brain pivot static         # static-binary container-to-host pivot pattern
./brain database mongo       # mongo enumeration commands across all notes
./brain stego npiet          # Piet/npiet steganography hits
```

Zero deps, pure Python 3. Works on Windows (Git Bash) and Linux.

Beginner-friendly Spanish aliases are supported: `guia`, `temas`, `buscar`, `comandos`, `herramienta`, `credenciales`, `privilegios`, `contenedor`, `base-datos`.

### Invariants `brain` depends on

- Every `tools/` or `exploits/` note must carry a `Used on: **<Machine>**` line — that powers `brain used-on`.
- References are one-way: writeups link to `tools/` and `exploits/`; tool and exploit notes do **not** keep `Referenced in`, `Used by`, or per-writeup backlink sections.
- Every writeup must link to the technique file by relative path (e.g. `(../../exploits/foo.md)`) — that powers `brain backrefs` without duplicating writeup references inside the notes.
- Topic membership is defined in `TOPICS` inside `brain.py`. When you add a new tool or exploit note, add its stem/substring to the relevant topic entry in the same commit so it shows up in `./brain <topic>`.

---

## Project Purpose

Personal **second brain** for offensive security work. Three jobs:

1. **CTF writeups** — HackTheBox and TryHackMe machines, organized by difficulty.
2. **Tool reference** — per-tool notes that accumulate every command I actually use across machines and engagements (the "second brain" for tools).
3. **Bug bounty flows** — reusable methodology / playbook notes for recon, vulnerability discovery and exploitation patterns I apply to real-world bug bounty targets.

Every machine I finish becomes a writeup; every new tool / technique I use gets its own page that is linked from the README and cross-referenced from the writeups. **The tool / exploit notes are the primary artefacts. The writeups are supporting narrative and should be slim.**

---

## Directory Layout

Machine narratives live under `writeups/`, grouped by platform. Reusable material stays outside writeups so the CLI can search tools, exploits, payloads, playbooks and techniques directly.

```text
Writeups/
├── README.md
├── AGENTS.md
├── brain
├── brain.py
├── writeups/
│   ├── HTB/
│   │   ├── Easy/
│   │   ├── Medium/
│   │   └── Hard/
│   └── TRY/
│       ├── Easy/
│       ├── Medium/
│       ├── Hard/
│       └── Networks/
├── tools/
├── exploits/
├── privesc/
├── techniques/
├── playbooks/
└── payloads/
```

---

## Where New Content Goes

| Thing I want to add | Location | Filename pattern |
|---------------------|----------|------------------|
| A new HTB machine writeup | `writeups/HTB/<Easy|Medium|Hard>/` based on HTB difficulty | `<Name>.md` (e.g. `Silentium.md`) |
| A new TryHackMe room writeup | `writeups/TRY/<Easy|Medium|Hard>/` (create on first use) | `<RoomName>.md` |
| A command-reference for a new tool | `tools/` | lowercase tool name — `<tool>.md` |
| A new exploit / abuse | `exploits/` | kebab-case descriptive name — `<what>-<how>.md` |
| A new technique or theory | `techniques/` | kebab-case descriptive name (e.g. `sqli.md`) |
| Local privilege escalation | `privesc/` | `<os>/<method>.md` |
| A post-exploitation checklist / playbook | `playbooks/` | `<topic>-playbook.md` |
| A bug bounty methodology / flow note | `bugbounty/` (create on first use) | kebab-case — `<phase>-<topic>.md` (e.g. `recon-subdomain-enumeration.md`, `idor-testing-flow.md`) |
| Per-program bug bounty scratch notes (scope, findings, payloads) | `bugbounty/programs/<program>/` | `<program>.md` plus supporting files; keep private findings out of public commits |
| External writeups / cheatsheets I only reference | do not commit to the repo |  |

After creating a file, **always** add a link to it in `README.md` under the matching section.

---

## Content Rules

### Language
- **Everything** → **English**. Writeups, tool notes, exploit notes, enumeration playbooks, AGENTS.md, README — all English.
- Conversation in chat stays in Spanish per system config.

### Editorial Cleanup
- Remove comments that only restate obvious command syntax.
- Keep comments that explain why a flag matters, what output means, or what broke.
- Make exploit/tool/enumeration notes clearer with goal-oriented headings and short `why it matters` notes.
- Never remove commands, payload code, reverse shells or proof snippets from writeups while cleaning prose.

### README
- Index only. Machines, tools, exploits — all links.
- **No** CVE tables, vulnerability descriptions, chains, or prose explanations. Everything technical belongs in the linked `.md` file.

### Writeups (`writeups/HTB/{Easy,Medium,Hard}/`, `writeups/TRY/{Easy,Medium,Hard}/`)
Expected structure (loose — don't enforce against existing files):
1. Target metadata (IP, domain, OS, difficulty, tech stack)
2. Attack Chain Overview (ASCII arrow diagram)
3. Table of Contents
4. Reconnaissance — short, link to `tools/nmap.md` etc.
5. Initial Access — one-paragraph summary + link to the exploit note (`exploits/<name>.md`)
6. User flag steps — commands that are box-specific only; anything reusable goes to `exploits/`
7. Privilege Escalation — same rule: link to the technique note
8. Root flag
9. Key Takeaways — the 4–6 lessons I want to remember next time I see this pattern
10. Related Notes section at the bottom, linking every referenced `tools/` + `exploits/` file

**Hard rule**: a writeup must NEVER be the only place a command, flag or technique lives. If it is reusable, also extract it to `tools/` or `exploits/` and link back.

**Do not remove commands from writeups just because they were extracted.** Writeups should still feel organic and readable, with the commands/code that were actually run preserved in place. Extraction means duplication into the reusable note, not deleting the command from the narrative.

### Tool Notes (`tools/`)
- One-paragraph description at the top.
- `## Commands Used` section with every command that appears in the writeups, each annotated with `Used on: **<Machine>**`.
- Do **not** add `Referenced in`, `Used by`, or writeup backlink sections. The writeup owns references to tools, not the other way around.
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

1. Before creating a new note, **search first**: `./brain guide`, `./brain <topic> <keyword>`, then `./brain search <keyword>` if you are unsure of the topic. Extend an existing note when possible.
2. When adding a new tool / exploit, update `README.md` in the same change.
3. When editing a writeup, any command that isn't box-specific must be copied into `tools/` or `exploits/` and linked back, while leaving the original command/code in the writeup so the walkthrough remains organic.
4. Every new `tools/` or `exploits/` note must carry the `Used on: **<Machine>**` line. `brain used-on` depends on it.
5. Never embed raw flag values that I didn't personally capture — use placeholders (`<CAPTURED_TOKEN>`, `ATTACKER_IP`).
6. Commits are user-initiated. Don't commit unless explicitly asked.

### Checklist when closing a machine

- [ ] Writeup created at `writeups/HTB/<Diff>/` or `writeups/TRY/<Diff>/` with the 10-section structure, short prose, links to every referenced technique.
- [ ] Every new tool used is a file in `tools/` with `Used on: **<Machine>**` and a `## Commands Used` section.
- [ ] Every new exploit / abuse is a file in `exploits/` with the standard template.
- [ ] `README.md` updated (machine row, new tool bullets, new exploit bullets, directory tree).
- [ ] `./brain used-on <Machine>` lists every relevant note — run it as a final sanity check.

---

## Non-Goals

- This repo is not a CVE encyclopedia. If I want CVE details, I'll go to NVD.
- Not a generic pentest methodology book. `exploits/` and `bugbounty/` notes capture **what I actually run**, not every known variant.
- Not a writeup archive. Writeups are the narrative shell around the real artefacts (tools/exploits). If a writeup has more content than the tools/exploits it references, something went wrong.
- `reference/` (the legacy HTML mini-site) has been removed. New content goes into the `.md` system exclusively.

