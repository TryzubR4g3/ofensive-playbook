# brain

Brain is a local security knowledge base for lab writeups, defensive techniques,
tool references and review playbooks. Use it to find a control, review the
evidence behind it or check published remediation details for a CVE.

## Quick start

Run these commands from the repository root. The CLI uses Python's standard
library. The test workflow uses Python 3.12.

**PowerShell**

```powershell
python brain.py defense search "mass assignment"
python brain.py defense audit
```

**Bash**

```bash
bash brain defense search "file upload" --type playbook
bash brain defense audit
```

The Bash launcher uses `python3` by default. Set `BRAIN_PYTHON` to the path
of your Python executable when it is installed under a different name or location.

## CLI reference

Use `python brain.py` in PowerShell or `bash brain` in Bash before the commands
in this table.

| Command | Result |
|---|---|
| `defense search "OpenAPI" --type tool --json` | Search tool notes and return structured results |
| `defense search CWE-434 --type technique --limit 5` | Find up to five technique notes by CWE, title or keyword |
| `defense show api-function-authorization` | Read the Markdown note for a search result ID |
| `defense advisory CVE-2021-44228` | Show official references and cached remediation details |
| `defense advisory CVE-2021-44228 --refresh --json` | Refresh public advisory data and return structured results |
| `defense audit --json` | Report coverage by platform, incomplete sources and historical link issues |
| `defense check` | Validate the catalog, writeup report blocks and their defensive references |

Search accepts multiple terms and identifiers such as `API5:2023`. It ignores
case and accents, gives title and tag matches more weight than prose, and returns
up to 20 results by default. Filters include `technique`, `tool` and
`playbook`. Search exits with 0 for matches, 1 for an empty result and 2 for a
usage or catalog read error.

Advisory refresh combines NVD version criteria and CISA KEV information with
version details from reviewed GitHub advisories. The output shows when each
source was checked. A failed refresh can fall back to that source's last cached
result. Set `BRAIN_CACHE_DIR` to override the cache directory.

## Writeups and PortSwigger coverage

Writeups live under `writeups/<platform>/`. The report block records the
platform, source status, overview, defensive takeaways and catalog references.
The lab record follows in visible Markdown. Use TryHackMe's `Ra.md` as the
presentation reference and adapt the headings to the individual case.
`Limited detail` identifies a source with incomplete evidence.

PortSwigger Web Security Academy material is under `writeups/PortSwigger/`.
The [PortSwigger coverage table](docs/defense-cli-plan.md#portswigger-coverage)
maps case topics to catalog notes for API access control, request and query
boundaries, and file upload validation. Run `defense audit` for the writeups
available in your checkout.

## Project layout

| Path | Purpose |
|---|---|
| `writeups/` | Original case material and English report blocks |
| `defense/techniques/` | Defensive observations and mitigations |
| `defense/tools/` | Tool references and evidence review workflows |
| `defense/playbooks/` | Repeatable review and remediation procedures |
| `brain_core/` | CLI, catalog, writeup audit and advisory cache |
| `tests/` | Regression tests for ranking, metadata and CLI behavior |

The older reference index uses the top-level notes directories. Its
`guide`, `topics` and `stats` commands describe that index.

## Maintaining the repository

Use `Ra.md` from TryHackMe as the report presentation reference. Follow the
[repository instructions](AGENTS.md) and
[file conventions](CONVENTIONS.md) when updating writeups or catalog notes.
The [maintenance guide](docs/defense-cli-plan.md) records review status,
architecture and the verification workflow.

```bash
python brain.py defense check
python -m unittest discover -s tests
```
