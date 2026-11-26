"""Terminal encoding and ANSI formatting for the CLI."""

import os
import sys

# Force UTF-8 stdout on Windows consoles (cp1252 breaks on any non-ASCII)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except Exception:
        pass

_COLOR_MODE = os.environ.get("BRAIN_COLOR", "auto").lower()
_USE_COLOR = (
    os.environ.get("NO_COLOR") is None
    and _COLOR_MODE != "never"
    and (_COLOR_MODE == "always" or sys.stdout.isatty())
)

if sys.platform == "win32" and _USE_COLOR:
    os.system("")


def configure_color(argv: list[str]) -> list[str]:
    global _USE_COLOR, _COLOR_MODE
    cleaned: list[str] = []
    for arg in argv:
        if arg == "--color":
            _COLOR_MODE = "always"
        elif arg == "--no-color":
            _COLOR_MODE = "never"
        elif arg.startswith("--color="):
            _COLOR_MODE = arg.split("=", 1)[1].lower()
        else:
            cleaned.append(arg)
            continue

        if _COLOR_MODE not in {"auto", "always", "never"}:
            print("usage: brain [--color=auto|always|never] <command> [args]", file=sys.stderr)
            sys.exit(2)

        _USE_COLOR = (
            os.environ.get("NO_COLOR") is None
            and _COLOR_MODE != "never"
            and (_COLOR_MODE == "always" or sys.stdout.isatty())
        )
    return cleaned


def _c(text: str, code: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if _USE_COLOR else text
def bold(s):   return _c(s, "1")
def dim(s):    return _c(s, "2")
def green(s):  return _c(s, "32")
def yellow(s): return _c(s, "33")
def cyan(s):   return _c(s, "36")
def red(s):    return _c(s, "31")
def blue(s):   return _c(s, "34")
