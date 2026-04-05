"""Publish TIL notes to a Jekyll-style blog repository.

This module is designed to be **importable** independently of the CLI so that
it can be reused from scripts, automation pipelines, etc.

Layout assumed in the blog repo
--------------------------------
The published files land in ``<blog_repo>/<blog_til_subdir>/`` which defaults
to ``til/``.  Each file is given a Jekyll-compatible filename and front matter.

Images referenced in a note are copied from
``<notes_dir>/images/`` → ``<blog_repo>/assets/images/til/`` and the image
paths in the published markdown are rewritten accordingly.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .notes import list_notes, parse_front_matter, render_front_matter

# Where images are placed inside the blog repo
_BLOG_IMAGE_SUBDIR = Path("assets") / "images" / "til"

# Regex that matches markdown image syntax: ![alt](path)
_MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def _rewrite_images(
    body: str,
    note_path: Path,
    images_src_dir: Path,
    images_dst_dir: Path,
) -> str:
    """Copy local images and rewrite their paths in *body*.

    Remote URLs (starting with ``http://`` or ``https://``) are left unchanged.
    Relative paths are resolved relative to the note file's directory **or**
    to *images_src_dir* (the ``images/`` folder in the notes directory).
    """

    def _replace(match: re.Match) -> str:  # type: ignore[type-arg]
        alt, src = match.group(1), match.group(2)
        if src.startswith(("http://", "https://")):
            return match.group(0)

        # Try resolving relative to the note's directory, then to images_src_dir
        candidate = (note_path.parent / src).resolve()
        if not candidate.exists():
            candidate = (images_src_dir / Path(src).name).resolve()
        if not candidate.exists():
            return match.group(0)  # leave unchanged if file not found

        images_dst_dir.mkdir(parents=True, exist_ok=True)
        dest = images_dst_dir / candidate.name
        shutil.copy2(candidate, dest)

        # Rewrite path to Jekyll-friendly absolute URL path
        new_src = f"/assets/images/til/{candidate.name}"
        return f"![{alt}]({new_src})"

    return _MD_IMAGE_RE.sub(_replace, body)


def _build_jekyll_front_matter(
    meta: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Return a front matter dict suitable for a Jekyll TIL post."""
    fm: dict[str, Any] = {
        "layout": meta.get("layout", "til"),
        "title": meta.get("title", ""),
        "date": meta.get("date", ""),
        "tags": meta.get("tags", []),
    }
    if meta.get("author") or config.get("author"):
        fm["author"] = meta.get("author") or config["author"]
    # Carry through any extra keys the user added
    for key, value in meta.items():
        if key not in fm and key != "path":
            fm[key] = value
    return fm


def publish_note(
    note_path: Path,
    blog_repo: Path,
    notes_dir: Path,
    config: dict[str, Any],
    *,
    dry_run: bool = False,
) -> Path:
    """Publish a single TIL note to *blog_repo*.

    Parameters
    ----------
    note_path:
        Absolute path to the source ``.md`` file.
    blog_repo:
        Root of the blog repository.
    notes_dir:
        Root of the notes directory (used to locate ``images/``).
    config:
        Loaded config dict (see :func:`til.config.load_config`).
    dry_run:
        When *True* no files are written or copied.

    Returns
    -------
    Path
        The destination path where the note was (or would be) written.
    """
    note_path = Path(note_path)
    blog_repo = Path(blog_repo)
    notes_dir = Path(notes_dir)

    text = note_path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(text)

    images_src_dir = notes_dir / config.get("images_subdir", "images")
    images_dst_dir = blog_repo / _BLOG_IMAGE_SUBDIR

    if not dry_run:
        body = _rewrite_images(body, note_path, images_src_dir, images_dst_dir)

    jekyll_fm = _build_jekyll_front_matter(meta, config)

    dest_dir = blog_repo / config.get("blog_til_subdir", "til")
    dest_path = dest_dir / note_path.name

    if not dry_run:
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(
            render_front_matter(jekyll_fm, body), encoding="utf-8"
        )

    return dest_path


def publish_all(
    notes_dir: Path,
    blog_repo: Path,
    config: dict[str, Any],
    *,
    dry_run: bool = False,
) -> list[Path]:
    """Publish all TIL notes from *notes_dir* to *blog_repo*.

    Already-published notes whose source has changed will be overwritten,
    making re-publishing idempotent.

    Returns
    -------
    list[Path]
        Destination paths of every published note.
    """
    from .config import til_dir  # avoid circular import at module level

    src_dir = til_dir(config)

    notes = list_notes(src_dir)
    published: list[Path] = []
    for note in notes:
        dest = publish_note(
            note["path"],
            blog_repo=blog_repo,
            notes_dir=notes_dir,
            config=config,
            dry_run=dry_run,
        )
        published.append(dest)
    return published
