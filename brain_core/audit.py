"""Check writeup report metadata and the repository's existing relative links."""

from __future__ import annotations

import re
from pathlib import Path

from .markdown import relative_links

START = "<!-- brain:report -->"
END = "<!-- /brain:report -->"
SECTIONS = ("## Report overview", "## Defensive takeaways", "## Defensive references")
REUSABLE = {"tools", "exploits", "privesc", "playbooks", "techniques", "payloads"}
REPORT_STATUS = re.compile(r"^- \*\*Source status\*\* (Documented|Limited detail)$", re.MULTILINE)


def audit_writeups(root: Path, notes) -> dict:
    writeups = root / "writeups"
    note_paths = {root / note.path for note in notes.values()}
    covered = 0
    by_platform = {}
    without_legacy_links = 0
    limited = []
    missing = []
    broken = []
    errors = []
    for path in sorted(writeups.rglob("*.md")):
        if not path.is_file() or not path.resolve().is_relative_to(writeups):
            continue
        name = path.relative_to(root).as_posix()
        parts = path.relative_to(writeups).parts
        platform = parts[0] if len(parts) > 1 else "Uncategorized"
        counts = by_platform.setdefault(platform, {"writeups": 0, "reports": 0})
        counts["writeups"] += 1
        source = path.read_text(encoding="utf-8-sig", errors="replace")
        before, start, report_and_original = source.partition(START)
        report, end, original = report_and_original.partition(END)
        if not start:
            missing.append(name)
        else:
            status = REPORT_STATUS.search(report)
            if (not end or START in report_and_original or END in original or not status
                    or not re.search(r"^- \*\*Platform\*\* \S", report, re.MULTILINE)
                    or not all(f"\n{section}\n" in report for section in SECTIONS)):
                errors.append(f"{name} has invalid report metadata")
            else:
                links = list(relative_links(report))
                if not links or any((path.parent / link).resolve() not in note_paths for _, link in links):
                    errors.append(f"{name} has missing or invalid defensive references")
                else:
                    covered += 1
                    counts["reports"] += 1
                if status[1] == "Limited detail":
                    limited.append(name)

        valid = 0
        broken_count = 0
        original_source = before + original if start and end else source
        for _, link in relative_links(original_source):
            target = (path.parent / link).resolve()
            if not target.is_relative_to(root):
                continue
            target_parts = target.relative_to(root).parts
            if not target_parts or target_parts[0] not in REUSABLE or target.suffix not in {".md", ".txt"}:
                continue
            if target.is_file():
                valid += 1
            else:
                broken_count += 1
        if not valid:
            without_legacy_links += 1
        if broken_count:
            broken.append({"path": name, "count": broken_count})
    return {
        "reports": covered, "by_platform": by_platform,
        "missing_reports": missing, "limited_sources": limited,
        "without_legacy_links": without_legacy_links, "broken_legacy_links": broken,
        "errors": errors,
    }
