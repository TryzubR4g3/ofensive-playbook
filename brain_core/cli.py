"""Register commands and render human-readable or JSON results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import ROOT
from .terminal import configure_color

HELP = """Usage: brain [--color=auto|always|never] <command> [args]

  defense search [terms]    Search defensive techniques, tools and playbooks
  defense show <id>         Read a catalog note
  defense advisory <CVE>    Show official references and cached remediation data
  defense audit             Report writeup coverage and link issues
  defense check             Validate catalog notes and writeup reports
  guide                     Show the repository guide
  topics                    List legacy topic scopes

Use brain defense --help or open the README for examples."""


def positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def print_json(value) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def defense(root: Path, argv: list[str]) -> int:
    from .advisories import CVE_ID, format_advisory, get_advisory
    from .audit import audit_writeups
    from .catalog import NOTE_TYPES, check_notes, load_notes, normalize, rank_notes

    parser = argparse.ArgumentParser(
        prog="brain defense",
        description="Search defensive techniques, tools and playbooks.",
    )
    commands = parser.add_subparsers(dest="action")
    search = commands.add_parser("search", help="search the curated catalog")
    search.add_argument("query", nargs="*", help="search terms")
    search.add_argument("--type", choices=NOTE_TYPES, help="filter by note type")
    search.add_argument("--limit", type=positive_int, default=20, help="maximum results")
    search.add_argument("--json", action="store_true", help="print results as JSON")
    show = commands.add_parser("show", help="read a catalog note")
    show.add_argument("id", help="note ID returned by search")
    advisory = commands.add_parser("advisory", help="show sources and remediation details for a CVE")
    advisory.add_argument("cve", metavar="CVE-YYYY-NNNN")
    advisory.add_argument("--refresh", action="store_true", help="update data from public advisory services")
    advisory.add_argument("--json", action="store_true", help="print structured advisory data")
    audit = commands.add_parser("audit", help="report writeup coverage and link issues")
    audit.add_argument("--json", action="store_true", help="print a structured audit")
    commands.add_parser("check", help="validate catalog notes and writeup reports")
    args = parser.parse_args(argv)

    if args.action is None:
        parser.print_help()
        return 0
    if args.action == "advisory":
        if not CVE_ID.fullmatch(args.cve):
            advisory.error("expected a CVE identifier in CVE-YYYY-NNNN format")
        record = get_advisory(args.cve.upper(), args.refresh)
        if args.json:
            print_json(record)
        else:
            print(format_advisory(record))
            for warning in record["warnings"]:
                print(warning, file=sys.stderr)
        return int(args.refresh and not record["data"])

    try:
        notes = load_notes(root)
        if not notes:
            raise ValueError("The defensive catalog is empty")
        if args.action in {"audit", "check"}:
            report = audit_writeups(root, notes)
            if args.action == "check":
                issues = check_notes(root, notes) + report["errors"]
                issues += [f"{name} has no report header" for name in report["missing_reports"]]
                for issue in issues:
                    print(issue, file=sys.stderr)
                if not issues:
                    print(f"Validated {len(notes)} catalog notes and {report['reports']} writeup reports.")
                return int(bool(issues))
            elif args.json:
                print_json(report)
            else:
                print_audit(report)
            return 0
    except (OSError, ValueError) as error:
        print(f"Could not read the catalog or writeups ({error})", file=sys.stderr)
        return 2

    if args.action == "show":
        note = notes.get(args.id.casefold())
        if note:
            print(f"# {note.title}\n\n{note.body}")
            return 0
        print(f"Unknown note {args.id}. Use brain defense search.", file=sys.stderr)
        return 1

    query = normalize(" ".join(args.query))
    if args.query and not query:
        search.error("enter a term containing letters or numbers")
    results = rank_notes(notes.values(), query, args.type)[:args.limit]
    if args.json:
        print_json([note.metadata() for note in results])
    elif results:
        for note in results:
            print(f"[{note.type}] {note.title} ({note.id})\n  {note.summary}")
        print("\nRead a full note with brain defense show <id>.")
    else:
        print("No matches. Try fewer terms or a broader note type.")
    return 0 if results else 1


def print_audit(report: dict) -> None:
    print(f"{report['reports']} writeups have a validated report header.")
    for platform, counts in sorted(report["by_platform"].items()):
        print(f"  {platform}  {counts['reports']}/{counts['writeups']} validated")
    print(f"{report['without_legacy_links']} writeups have no original links to reusable notes.")
    for label, items in (
        ("Limited source detail", report["limited_sources"]),
        ("Missing report header", report["missing_reports"]),
        ("Invalid report metadata", report["errors"]),
    ):
        for item in items:
            print(f"{label}  {item}")
    for issue in report["broken_legacy_links"]:
        print(f"Original links to review  {issue['path']} ({issue['count']})")


def main(argv: list[str]) -> int:
    args = configure_color(argv)
    if not args or args[0] in {"--help", "-h", "help"}:
        print(HELP)
        return 0
    if args[0] in {"defense", "defensa"}:
        return defense(ROOT, args[1:])

    from .legacy import main as legacy_main

    return legacy_main(args)
