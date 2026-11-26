# Repository instructions

## Language and source preservation

- Write all repository prose in English. This includes writeups, documentation, note titles, CLI help, diagnostics and examples.
- Proofread English prose when adding or editing it. Correct spelling, grammar, punctuation and word choice, and check technical terms and product names for correct spelling and consistent capitalization.
- Correct spelling and unclear English in place when asked to copyedit. Preserve the author's meaning, the sequence and the detail of the existing writeup. Identify any uncertainty or missing evidence.
- Preserve every original step, explanation, command, script, output, screenshot, link and result in the visible body of the writeup. Keep code, captures and quoted material verbatim. Keep the lab record in ordinary Markdown.
- Use [Ra](writeups/TRY/Hard/Ra.md) as the presentation reference. Choose headings, numbered sections and a table of contents to fit the material in each writeup. Preserve the original observations and evidence in the sections where they belong.
- Use descriptive headings, short paragraphs and blank lines around lists and fenced blocks. Place a brief explanation beside each observation so readers can tell what the evidence shows and why it matters.
- Use inline code for parameter names and identifiers. Label fenced blocks according to what they contain. Use `text` for captured URLs and raw output, and the relevant language label for source code. Preserve the captured contents verbatim.
- Keep case-specific details in the writeup. Capture reusable defensive observations, checks and mitigations in the corresponding catalog notes under `defense/`. Distinguish verified observations from suggestions for follow-up.
- Mark incomplete source material explicitly. Record the evidence gap without inferring missing steps or outcomes.

## Writeup coverage and handoff

- Read and edit one writeup at a time. Apply the [file conventions](CONVENTIONS.md#writeup-report-blocks) by hand after reviewing that writeup in context. Use read-only checks to verify formatting, links and coverage across the repository.
- Review each diff before moving to the next writeup. Make sure every original detail and item of evidence remains visible and the section changes fit the case.
- Use the platform-specific directory and the case name. PortSwigger Web Security Academy writeups belong under `writeups/PortSwigger/`. Keep existing filenames unless a rename is part of the task.
- For a new or updated writeup, check its platform's entry in `brain defense audit` and validate its defensive references with `brain defense check`. Use `Limited detail` for a placeholder or a documented stopping point.
- Check Git status for new files before reporting completion. Describe local, tracked and published work accurately. When a group such as PortSwigger is the focus, list the files or link the directory and report that group's coverage explicitly.

## CLI

- Keep `brain.py` as a thin entry point. Put CLI parsing and display in `brain_core/cli.py`. Keep Markdown parsing, catalog ranking, writeup auditing and advisory retrieval separate from CLI output.
- Give every catalog note a unique kebab-case ID and meaningful English labels and keywords. Link related defensive notes with relative paths.
- Run `python brain.py defense check` and `python -m unittest discover -s tests` after changing catalog notes, writeup metadata or CLI behavior. See [CONVENTIONS.md](CONVENTIONS.md) for Markdown layout and [README.md](README.md) for command examples.

## Documentation

- Update the GitHub-facing [README](README.md) in the same change as user-visible CLI behavior, repository layout or writeup coverage. Keep flags and examples consistent with the implemented commands.
- Use [CONVENTIONS.md](CONVENTIONS.md) for file formats and the [maintenance guide](docs/defense-cli-plan.md) for architecture, dated audit results and verification procedures.
- Keep all new prose in English. Check relative Markdown links and validate command examples from the repository root. Use the CLI audit for live counts. Label any saved counts with their scope and date.
