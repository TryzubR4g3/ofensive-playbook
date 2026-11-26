"""Load, validate and rank the curated defensive Markdown collection."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .markdown import relative_links

NOTE_TYPES = {"technique": "techniques", "tool": "tools", "playbook": "playbooks"}
TAGS = re.compile(r"<!-- tags: (.+) -->")
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


@dataclass(frozen=True)
class Note:
    id: str
    type: str
    title: str
    summary: str
    tags: tuple[str, ...]
    path: str
    body: str

    def metadata(self) -> dict:
        return {
            "id": self.id, "type": self.type, "title": self.title,
            "summary": self.summary, "tags": self.tags, "path": self.path,
        }


def load_notes(root: Path) -> dict[str, Note]:
    notes = {}
    for kind, folder in NOTE_TYPES.items():
        directory = root / "defense" / folder
        for path in sorted(directory.glob("*.md")):
            if not path.is_file() or path.resolve().parent != directory:
                continue
            relative_path = path.relative_to(root).as_posix()
            parts = path.read_text(encoding="utf-8-sig").strip().split("\n\n", 2)
            tag_line = TAGS.fullmatch(parts[1]) if len(parts) == 3 else None
            if not tag_line or not re.fullmatch(r"# \S[^\n]*", parts[0]):
                raise ValueError(f"{relative_path} must start with a title, tags and summary")
            if not SLUG.fullmatch(path.stem) or path.stem in notes:
                raise ValueError(f"Invalid or duplicate note ID in {relative_path}")
            title, _, body = parts
            tags = tuple(tag.strip() for tag in tag_line[1].split(","))
            summary = " ".join(body.split("\n\n", 1)[0].split())
            if not all(tags) or not summary or summary.startswith("#"):
                raise ValueError(f"Missing tags or summary in {relative_path}")
            notes[path.stem] = Note(path.stem, kind, title[2:], summary, tags, relative_path, body)
    return notes


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    folded = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[^\W_]+", folded))


def rank_notes(notes, query: str, kind: str | None = None) -> list[Note]:
    terms = set(query.split())
    ranked = []
    for note in notes:
        if kind and note.type != kind:
            continue
        title = normalize(note.title)
        slug = normalize(note.id)
        aliases = {normalize(tag) for tag in note.tags}
        titles = set((title + " " + slug).split())
        tags = set(" ".join(aliases).split())
        content = set(normalize(note.body.partition("\n## References")[0]).split())
        if not terms <= titles | tags | content:
            continue
        score = 6 * len(terms & titles) + 4 * len(terms & tags) + len(terms & content)
        if query in (title, slug):
            score += 16
        elif query and query in aliases:
            score += 8
        ranked.append((score, note))
    ranked.sort(key=lambda hit: (-hit[0], hit[1].id))
    return [note for _, note in ranked]


def check_notes(root: Path, notes) -> list[str]:
    known_paths = {root / note.path for note in notes.values()}
    errors = []
    for note in notes.values():
        path = root / note.path
        if "\n## References\n" not in note.body:
            errors.append(f"{note.path} is missing the References section")
        for _, link in relative_links(note.body):
            if (path.parent / link).resolve() not in known_paths:
                errors.append(f"{note.path} links to an unknown note ({link})")
    return errors
