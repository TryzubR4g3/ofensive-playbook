# Writeup review and CLI maintenance

## Writeup format

Use [Ra](../writeups/TRY/Hard/Ra.md) as the presentation reference and the
[report block template](../CONVENTIONS.md#writeup-report-blocks) for the
metadata the CLI validates. Review and format each writeup by hand. Keep
the original lab record visible below the report block and link reusable
defensive checks and mitigations to catalog notes.

## Review snapshot

The local audit on 19 November 2026 validated 92 report blocks, including
five PortSwigger writeups. That snapshot included untracked files. The
writeups retain the original text, links, screenshots, commands and captured
output.

Seven sources have limited detail. The PortSwigger parameter-pollution writeup and TryHackMe Checkmate are short placeholders. VariaType, res, VulnNet Roasted, Royal Router and Ra2 document preliminary observations or a stopping point.

The legacy link review found eight unresolved relative references in Silentium (1), Checkpoint (2), res (2), VulnNet Internal (1) and Marketplace (2). The report headers provide current defensive references and the audit continues to report the original links. Run `brain defense audit --json` for current counts and paths.

### PortSwigger coverage

| Case topic | Catalog note | Review focus |
|---|---|---|
| Mass assignment | [API mass assignment](../defense/techniques/api-mass-assignment.md) | Permissions for writing properties |
| Interactive API documentation | [Function authorization](../defense/techniques/api-function-authorization.md) | Server-side permissions for each operation |
| Undocumented API operation | [API inventory](../defense/techniques/api-inventory.md) | Align routes, methods and versions with the contract |
| Server-side parameter pollution | [Parameter boundaries](../defense/techniques/api-parameter-pollution.md) | Typed serialization and declared cardinality |
| SQL injection in a product category filter | [Input and interpreter boundaries](../defense/techniques/input-boundaries.md) | Parameterized queries and server-side product visibility |
| File upload validation | [Upload validation and isolation](../defense/techniques/file-upload.md) | File validation and storage outside executable paths |

The parameter-pollution source is marked `Limited detail`. Its related catalog
note explains the general defensive control. The audit reports source status
and coverage for the writeups present in each checkout.

## CLI architecture

| Module | Responsibility |
|---|---|
| `brain.py` | Python entry point shared by both shell workflows |
| `brain_core/cli.py` | Dispatch, argument parsing, exit codes and output |
| `brain_core/catalog.py` | Read, validate and rank defensive Markdown notes |
| `brain_core/markdown.py` | Read relative Markdown links outside fenced blocks |
| `brain_core/audit.py` | Validate writeup metadata and report source links |
| `brain_core/advisories.py` | Fetch and cache public remediation metadata |
| `brain_core/terminal.py` | Terminal encoding and the existing color options |
| `brain_core/legacy.py`, `brain_core/legacy_topics.py` | Existing command behavior and topic definitions |

The [catalog note format](../CONVENTIONS.md#defensive-catalog-notes) describes
the inputs to the catalog loader. The audit walks `writeups/` recursively
and groups results by the first directory under that root.

## Advisory data and cache

The default advisory view reads local data. Use `--refresh` to query public
sources. NVD version criteria may depend on additional applicability
conditions. CISA KEV dates are reported when supplied by NVD. A first patched
package version is shown when a reviewed GitHub advisory supplies it. Each
source has an independent cache entry and retrieval timestamp. [NVD CVE API](https://nvd.nist.gov/developers/vulnerabilities) · [GitHub global advisory API](https://docs.github.com/en/rest/security-advisories/global-advisories)

Cache files live in `%LOCALAPPDATA%\brain-defense` on Windows when
`LOCALAPPDATA` is available and `$XDG_CACHE_HOME/brain-defense` when an XDG
cache directory is configured on other systems. The fallback is
`~/.cache/brain-defense`. Set `BRAIN_CACHE_DIR` to choose a directory.

## Verification workflow

Run the checks from the repository root.

```powershell
python brain.py defense check
$audit = python brain.py defense audit --json | ConvertFrom-Json
$audit.by_platform.PortSwigger
python -m unittest discover -s tests
```

```bash
bash brain defense check
bash brain defense audit
python3 -m unittest discover -s tests
```

When working on PortSwigger files, compare the local audit with Git's file
status before reporting completion.

```bash
git status --short --untracked-files=all -- writeups/PortSwigger/
git ls-files -- writeups/PortSwigger/
```

Use `defense audit` to review documented evidence gaps and historical links.
Review the rendered writeup and its diff after editing. `defense check`
validates catalog links and report metadata. The regression suite covers keyword
ranking, reference queries, advisory caching and CLI behavior. The
[Brain CLI workflow](../.github/workflows/brain.yml) defines checks for Windows
and Linux.
