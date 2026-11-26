"""Read inline Markdown links outside fenced code blocks."""

import re
from urllib.parse import unquote, urlsplit

FENCE = re.compile(r"^\s*(`{3,}|~{3,})(.*)$")
LINK = re.compile(r"(?<!!)\[[^\]\n]*\]\(\s*(?:<([^>\n]+)>|([^\n)]+?))\s*\)")
TITLE = re.compile(r"""\s+(?:"[^"]*"|'[^']*')$""")


def relative_links(markdown):
    fence = None
    for number, line in enumerate(markdown.splitlines(), 1):
        delimiter = FENCE.match(line)
        if delimiter:
            marker, suffix = delimiter.groups()
            if fence is None:
                fence = marker
            elif marker.startswith(fence) and not suffix.strip():
                fence = None
            continue
        if fence:
            continue
        for match in LINK.finditer(line):
            link = match[1] or TITLE.sub("", match[2])
            try:
                parsed = urlsplit(link)
            except ValueError:
                continue
            if not parsed.scheme and not parsed.netloc and parsed.path:
                yield number, unquote(parsed.path)
