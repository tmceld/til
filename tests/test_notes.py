"""Tests for til.notes."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from til.notes import (
    create_note,
    list_notes,
    note_filename,
    parse_front_matter,
    render_front_matter,
    slugify,
)


class TestSlugify:
    def test_lowercases(self) -> None:
        assert slugify("Hello World") == "hello-world"

    def test_strips_special_chars(self) -> None:
        assert slugify("Python f-strings the trick") == "python-f-strings-the-trick"

    def test_collapses_spaces(self) -> None:
        assert slugify("a  b   c") == "a-b-c"

    def test_strips_leading_trailing_hyphens(self) -> None:
        assert not slugify(" hello ").startswith("-")
        assert not slugify(" hello ").endswith("-")


class TestNoteFilename:
    def test_format(self) -> None:
        d = date(2024, 1, 15)
        assert note_filename("Python tips", d) == "2024-01-15-python-tips.md"

    def test_uses_today_by_default(self) -> None:
        fn = note_filename("test")
        assert fn.endswith("-test.md")
        assert fn[:10] == date.today().isoformat()


class TestFrontMatter:
    _SAMPLE = "---\ntitle: Hi\ndate: 2024-01-01\n---\n\nBody text.\n"

    def test_parse_returns_meta_and_body(self) -> None:
        meta, body = parse_front_matter(self._SAMPLE)
        assert meta["title"] == "Hi"
        assert "Body text." in body

    def test_parse_no_front_matter(self) -> None:
        meta, body = parse_front_matter("# Just markdown")
        assert meta == {}
        assert body == "# Just markdown"

    def test_render_roundtrip(self) -> None:
        meta = {"title": "Test", "date": "2024-01-01", "tags": ["a", "b"]}
        body = "Some content.\n"
        rendered = render_front_matter(meta, body)
        meta2, body2 = parse_front_matter(rendered)
        assert meta2["title"] == "Test"
        assert meta2["tags"] == ["a", "b"]
        assert "Some content." in body2


class TestCreateNote:
    def test_creates_file(self, tmp_path: Path) -> None:
        path = create_note(tmp_path, "My Note", today=date(2024, 1, 15))
        assert path.exists()
        assert path.name == "2024-01-15-my-note.md"

    def test_front_matter_fields(self, tmp_path: Path) -> None:
        path = create_note(
            tmp_path, "Test Note", tags=["python", "cli"], today=date(2024, 2, 1)
        )
        meta, _ = parse_front_matter(path.read_text())
        assert meta["title"] == "Test Note"
        assert meta["date"] == "2024-02-01"
        assert "python" in meta["tags"]
        assert meta["layout"] == "til"

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        til_d = tmp_path / "deep" / "TIL"
        path = create_note(til_d, "Deep note", today=date(2024, 3, 1))
        assert path.exists()

    def test_does_not_overwrite_existing(self, tmp_path: Path) -> None:
        path = create_note(tmp_path, "Same Note", today=date(2024, 1, 1))
        path.write_text("# custom content")
        path2 = create_note(tmp_path, "Same Note", today=date(2024, 1, 1))
        assert path == path2
        assert path.read_text() == "# custom content"

    def test_author_included_when_set(self, tmp_path: Path) -> None:
        path = create_note(tmp_path, "Auth note", author="Alice", today=date(2024, 1, 1))
        meta, _ = parse_front_matter(path.read_text())
        assert meta["author"] == "Alice"

    def test_author_omitted_when_empty(self, tmp_path: Path) -> None:
        path = create_note(tmp_path, "Anon note", author="", today=date(2024, 1, 1))
        meta, _ = parse_front_matter(path.read_text())
        assert "author" not in meta

    def test_empty_tags_list(self, tmp_path: Path) -> None:
        path = create_note(tmp_path, "No tags", today=date(2024, 1, 1))
        meta, _ = parse_front_matter(path.read_text())
        assert meta["tags"] == []


class TestListNotes:
    def test_returns_empty_for_missing_dir(self, tmp_path: Path) -> None:
        assert list_notes(tmp_path / "nonexistent") == []

    def test_lists_notes_sorted(self, tmp_path: Path) -> None:
        create_note(tmp_path, "B note", today=date(2024, 1, 2))
        create_note(tmp_path, "A note", today=date(2024, 1, 1))
        notes = list_notes(tmp_path)
        dates = [n["date"] for n in notes]
        assert dates == sorted(dates)

    def test_includes_path(self, tmp_path: Path) -> None:
        create_note(tmp_path, "Note X", today=date(2024, 1, 1))
        notes = list_notes(tmp_path)
        assert all("path" in n for n in notes)

    def test_skips_files_without_front_matter(self, tmp_path: Path) -> None:
        (tmp_path / "plain.md").write_text("# No front matter")
        create_note(tmp_path, "Real note", today=date(2024, 1, 1))
        notes = list_notes(tmp_path)
        assert len(notes) == 1
