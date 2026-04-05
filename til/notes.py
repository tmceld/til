"""Note creation and listing for til."""

from __future__ import annotations

import re
import textwrap
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Front-matter helpers
# ---------------------------------------------------------------------------

_FM_DELIMITER = "---"
_FM_PATTERN = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown document into front matter and body.

    Returns
    -------
    (metadata, body)
        *metadata* is the parsed YAML dict (empty if there is no front matter).
        *body* is the remaining markdown text.
    """
    m = _FM_PATTERN.match(text)
    if m:
        meta = yaml.safe_load(m.group(1)) or {}
        body = m.group(2)
        return meta, body
    return {}, text


def render_front_matter(meta: dict[str, Any], body: str) -> str:
    """Render a markdown document with YAML front matter."""
    fm = yaml.dump(meta, default_flow_style=False, allow_unicode=True).strip()
    return f"{_FM_DELIMITER}\n{fm}\n{_FM_DELIMITER}\n\n{body}"


# ---------------------------------------------------------------------------
# Slug helpers
# ---------------------------------------------------------------------------

def slugify(title: str) -> str:
    """Convert a human title to a URL-friendly slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = slug.strip("-")
    return slug


def note_filename(title: str, today: date | None = None) -> str:
    """Return the markdown filename for a note, e.g. ``2024-01-15-my-title.md``."""
    today = today or date.today()
    return f"{today.isoformat()}-{slugify(title)}.md"


# ---------------------------------------------------------------------------
# Note creation
# ---------------------------------------------------------------------------

_DEFAULT_BODY = textwrap.dedent(
    """\
    <!-- Write your TIL note below -->

    """
)


def create_note(
    til_dir: Path,
    title: str,
    tags: list[str] | None = None,
    author: str = "",
    today: date | None = None,
) -> Path:
    """Create a new TIL note in *til_dir* and return its path.

    The note is **not** overwritten if it already exists.

    Parameters
    ----------
    til_dir:
        Directory where the note file will be written.
    title:
        Human-readable title of the note.
    tags:
        Optional list of tag strings.
    author:
        Author name (written to front matter; omitted when empty).
    today:
        Override today's date (useful in tests).
    """
    today = today or date.today()
    til_dir = Path(til_dir)
    til_dir.mkdir(parents=True, exist_ok=True)

    filename = note_filename(title, today)
    path = til_dir / filename

    if path.exists():
        return path

    meta: dict[str, Any] = {
        "title": title,
        "date": today.isoformat(),
        "layout": "til",
        "tags": tags or [],
    }
    if author:
        meta["author"] = author

    content = render_front_matter(meta, _DEFAULT_BODY)
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Note listing
# ---------------------------------------------------------------------------

def list_notes(til_dir: Path) -> list[dict[str, Any]]:
    """Return a sorted list of note metadata dicts from *til_dir*.

    Each dict contains at minimum the keys returned by the front matter
    plus ``path`` (absolute :class:`~pathlib.Path`).  Notes without valid
    front matter are skipped.
    """
    til_dir = Path(til_dir)
    if not til_dir.exists():
        return []

    notes = []
    for md_file in sorted(til_dir.glob("*.md")):
        text = md_file.read_text(encoding="utf-8")
        meta, _ = parse_front_matter(text)
        if meta:
            meta["path"] = md_file
            notes.append(meta)

    return notes
