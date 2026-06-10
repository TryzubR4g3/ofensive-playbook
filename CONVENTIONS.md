# File Format Conventions

This document defines the canonical structure and naming rules for every file type in
the repo. `brain` depends on these conventions to surface the right content when you
search by topic or keyword. Deviating from them makes commands unfindable.

Read this alongside `AGENTS.md` / `CLAUDE.md`. When in conflict, this file wins on
format questions; the guide files win on workflow questions.

---

## 1 — Tool Notes (`tools/`)

### Structure (strict order)

```markdown
# toolname

<One paragraph: what the tool is, what it does, when to reach for it.
Always first — never buried mid-file.>

---

## Commands Used

### <Verb phrase describing the goal>
```bash
<command>
```
Used on: **Machine1**, **Machine2**

- `-flag` — why this flag matters (omit obvious ones like `-v` for verbose)
- `--option VALUE` — what the value controls

### <Another goal-oriented heading>
...

## Related
- [exploit-name.md](../../exploits/path/exploit-name.md) — one-line context
- [technique-name.md](../../techniques/path/name.md) — one-line context
```

### Rules

**Subsection headers (`###`) describe the technique or goal, never the machine.**

| ❌ Bad (machine-named) | ✅ Good (goal-named) |
|------------------------|----------------------|
| `### Wreath Commands` | `### Pivot through SOCKS proxy` |
| `### Decryptify Commands` | `### Fetch and POST API invite token` |
| `### Kobold / CCTV — full TCP` | `### Full TCP scan with scripts (no two-phase)` |

Legacy `## Machine Commands` sections at `##` level must be migrated: fold their
commands into properly named `###` subsections under `## Commands Used`.

**`Used on:` placement and format — strict:**

```markdown
### Port forwarding to expose a bound-localhost service
```bash
ssh -L 8080:127.0.0.1:3001 user@TARGET
```
Used on: **Silentium**, **CCTV**

- `-L [local_port]:[remote_host]:[remote_port]` — bind local port to a remote-side socket
```

- `Used on:` is always on the line immediately after the closing ` ``` `
- No dash, no inline text, no extra words after the last `**`
- If there is a context sentence, it goes on a new line below `Used on:`:

```markdown
Used on: **Team**

Dale's private key was readable via the `sshd_config` LFI — classic key-reuse pattern.
```

- `Used on:` with a dash (`Used on: **X** - text`) is **wrong** — breaks the stats regex
- `Used on:` inside a code block as a comment is **wrong**

**Flag annotations:**
- Bullet list after `Used on:`, before the next `###`
- Only annotate non-obvious flags — skip `-v`, `-h`, `-o outfile` etc.
- Keep annotations to one line each

**One section, one header:**
- Only one `## Commands Used` per file — no separate `## Recon Commands` / `## Exploit Commands`
- Group related commands under one `###` subsection, not multiple `##` sections

**`## Related` is mandatory** when the tool appears in an exploit or technique note.
Link to those notes with a one-line description of the relationship.

---

## 2 — Exploit Notes (`exploits/`)

### Structure (strict order)

```markdown
# Exploit Title — Short Noun Phrase

Used on: **Machine1**, **Machine2**

<One paragraph: what the vulnerability is, why it works, what the impact is.>

## Prerequisites
- <access level, version range, reachability condition>

## How It Works
<Mechanism. Prose. No commands here — save those for Steps.>

## Steps

### 1. <First goal>
```bash
<command>
```
<One-line annotation of what to look for in the output.>

### 2. <Next goal>
...

## Variants
| Situation | Adjustment |
|-----------|------------|
| <condition> | <what changes> |

## How to Recognize It
- <recon signal — nmap banner, HTTP header, response pattern>
- <another indicator>

## Defensive Note
<One short paragraph — optional but encouraged.>

## Related
- [tool.md](../../tools/path/tool.md)
- [technique.md](../../techniques/path/technique.md)
- [other-exploit.md](../path/other-exploit.md) — when to chain
```

### Rules

- `Used on:` always on line 3 (after title blank line). Format: `Used on: **Machine**`
- Never `**Used on:**` (bold key) — only the value is bold
- Multiple machines: `Used on: **Machine1**, **Machine2**` on one line
- `## How to Recognize It` is what makes an exploit findable during recon —
  include every signal you'd see before you knew the vuln existed (nmap output,
  HTTP titles, response patterns, error strings)
- Do not duplicate commands already in a `tools/` note — link to it instead
- Step headers are numbered and goal-named: `### 3. Obtain a shell as www-data`

---

## 3 — Technique Notes (`techniques/`)

Techniques are **theory and methodology** — not command references.
Commands live in `tools/`. A technique file answers "what is this and when do I use it";
a tool file answers "what exact flag did I use".

### Structure (strict order)

```markdown
# Technique Name

Used on: **Machine** ← only if learned/applied on a specific machine; omit for pure theory

<What the technique/vulnerability class is — one paragraph.>

## When to Use
- <observable condition that makes this technique applicable>
- <recon signal that suggests this path>
- <application behaviour that hints at this vuln>

## Prerequisites
- <access level needed>
- <environment condition>

## How It Works
<Mechanism explanation. Diagrams or ASCII flows welcome.>

## Payload / Steps
<Minimal representative payload or flow. Not a full command reference —
link to tools/ for that. One or two code blocks maximum.>

```sql
-- representative payload only
SELECT * FROM users WHERE id=1 UNION SELECT null,username,password FROM users--
```

See [sqlmap.md](../../tools/web/sqlmap.md) for the full command reference.

## Variants
| Variant | When | Notes |
|---------|------|-------|
| Boolean-based | Error output hidden | Slower, needs true/false delta |
| Time-based | Totally blind | Use `SLEEP()` / `WAITFOR DELAY` |

## Defensive Note
<Mitigation — short, one paragraph.>

## Related
- [tool.md](../../tools/path/tool.md) — tool used to exploit this
- [exploit.md](../../exploits/path/exploit.md) — real instance of this technique
```

### Rules

- `## When to Use` is **mandatory** — this is what `./brain sqli blind` surfaces.
  Write it as a list of observable signals, not a definition. Bad: "Use when the app
  has SQLi". Good: "Login form returns generic error but responds differently with
  `' AND 1=1--` vs `' AND 1=2--`".
- No full command references — one minimal representative snippet max, then link to `tools/`
- `Used on:` at file level only; no `Used on:` inside `## Steps`
- `## How to Recognize It` is for exploits, not techniques. Techniques use `## When to Use`.

---

## 4 — Naming Conventions

### Tool files
- Lowercase, single word or hyphenated: `nmap.md`, `netexec.md`, `burp-suite.md`
- Match the actual binary name where possible

### Exploit files
- kebab-case, descriptive: `werkzeug-debug-rce.md`, `nfs-uid-hijack.md`
- Pattern: `<target/context>-<what>-<method>.md`
- Never name after the machine: ~~`bookstore-exploit.md`~~

### Technique files
- **kebab-case only** — no CamelCase, no Mixed-Case
- Descriptive noun phrase: `blind-sql-injection.md`, `time-based-sqli.md`

Files to rename (current → correct):

| Current | Correct |
|---------|---------|
| `techniques/sqli/Blind-SQL-Injection.md` | `blind-sql-injection.md` |
| `techniques/sqli/Blind-SQLi-Bollean-Based.md` | `boolean-based-blind-sqli.md` (fix typo: "Bollean") |
| `techniques/sqli/Time-Based-Blind-SQL-Injection.md` | `time-based-blind-sqli.md` |
| `techniques/sqli/in-Band-SQLi.md` | `in-band-sqli.md` |
| `techniques/xss/Blind-XSS.md` | `blind-xss.md` |
| `techniques/xss/DOM-Based-XSS.md` | `dom-based-xss.md` |
| `techniques/xss/Reflected-XSS.md` | `reflected-xss.md` |
| `techniques/xss/Stored-XSS.md` | `stored-xss.md` |

After renaming, update:
1. `brain.py` TOPICS entries that reference these stems (check with `grep -n "blind-sql\|dom-based\|stored-xss" brain.py`)
2. Any writeup that links to these files by relative path

### Playbook files
- kebab-case: `linux-post-exploitation.md`, `ad-enumeration.md`

### Writeup files
- CamelCase matching the machine name, no suffixes: `Kobold.md`, `Silentium.md`
- Never: `Kobold-Writeup.md`, `Silentium_HTB_Writeup.md`

---

## 5 — Searchability Checklist

Before closing a note, verify:

```
[ ] Tool: description is the first paragraph, not buried
[ ] Tool: every ### header describes a technique/goal, not a machine
[ ] Tool: Used on: immediately after ```, no dash, no trailing text on same line
[ ] Tool: flag annotations are a bullet list after Used on:, not inside the code block
[ ] Exploit: Used on: is on line 3, format is Used on: **Machine**
[ ] Exploit: ## How to Recognize It section exists with at least 2 signals
[ ] Technique: ## When to Use section exists with observable conditions
[ ] Technique: filename is kebab-case
[ ] All: ## Related section links to the other relevant files
[ ] brain.py TOPICS: new file stem appears in the relevant topic entry
```

After adding or renaming any file, run:
```bash
./brain <topic> <keyword>   # verify the file appears in results
./brain tool <toolname>     # verify tool note is found
./brain exploit <name>      # verify exploit note is found
```

---

## 6 — Quick Reference: `Used on:` Format

```markdown
# ✅ Correct — tool subsection
Used on: **Machine1**, **Machine2**

# ✅ Correct — with context on next line
Used on: **Silentium**

Key reused from container environment variable `SMTP_PASSWORD`.

# ✅ Correct — exploit file header (line 3)
Used on: **Bookstore**

# ❌ Wrong — inline dash
Used on: **Bookstore** - found the hidden parameter

# ❌ Wrong — bold key
**Used on:** **Bookstore**

# ❌ Wrong — inside code block
```bash
ssh user@target  # Used on: Internal
```
```

---

## 6 — Command Marking Convention

Every **fenced code block** containing an executable command MUST be preceded by a **platform marker** so `brain` can distinguish commands from code examples and filter by OS.

### Marker Format

Precede each fenced code block with an HTML comment marker:

```markdown
<!-- cmd: platform -->
```bash
command here
```
```

### Supported Platforms

| Platform | Use When | Examples |
|----------|----------|----------|
| `linux` | bash/sh/zsh/ansible commands | `find`, `grep`, `sudo`, `curl`, `ssh` |
| `windows` | PowerShell / cmd.exe commands | `Get-ChildItem`, `whoami`, `net user` |
| `cross-platform` | Works on Linux AND Windows | Most `curl`, `python`, `ruby` scripts |
| `docker` | Docker/container-specific | `docker run`, `docker exec`, `kubectl` |
| `sql` | Database queries | `SELECT`, `INSERT`, `MySQL`, `PostgreSQL` |
| `http` | HTTP requests / API calls | Raw HTTP packets, `curl` JSON requests |
| `python` | Python scripts | Exception: marked as `python`, not `cross-platform` |

### Examples

**Linux command:**
```markdown
<!-- cmd: linux -->
```bash
find / -name "*.sh" -exec grep -l "sudo" {} \;
```
```

**Windows command:**
```markdown
<!-- cmd: windows -->
```powershell
Get-ChildItem -Recurse -Filter *.txt | Select-String "password"
```
```

**Cross-platform script:**
```markdown
<!-- cmd: cross-platform -->
```python
import requests
response = requests.get("http://target:8080/api")
print(response.text)
```
```

**Inline code in tabular format (no marker needed):**
```markdown
| Command | Purpose |
|---------|---------|
| `nmap -sT target` | TCP connect scan |
| `sqlmap -u URL --dbs` | Enumerate databases |
```

### Rules

1. **Only mark fenced code blocks** — inline `code` in paragraphs is not marked
2. **Marker goes on the line immediately before** ` ``` `
3. **One marker per block** — if a block contains multiple languages, use the primary one
4. **No marker needed for non-code blocks** — pseudocode, SQL in tables, etc. are obvious
5. **Comments inside the block are fine** — don't mark them separately:

```markdown
<!-- cmd: linux -->
```bash
# This is a comment — still part of the bash block
find / -type f -name "*.key"
```
```

### Why This Matters

- `./brain cmd find` → finds all `find` commands across the repo (searchable)
- `./brain cmd linux find` → finds only Linux usage
- `./brain privesc cmd` → shows only actual commands in privesc topic, not prose
- Colored badges in output: `[linux]`, `[windows]`, etc. for quick visual filtering

### Searchability Checklist

Before submitting a note with commands:

```
[ ] Every fenced code block has <!-- cmd: platform --> marker
[ ] Platform is one of: linux, windows, cross-platform, docker, sql, http, python
[ ] Marker is on the line directly before ```
[ ] Inline code (in paragraphs) is NOT marked
[ ] Code in tables is NOT marked
```
