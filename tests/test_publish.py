"""Tests for til.publish."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from til.notes import create_note, parse_front_matter
from til.publish import publish_all, publish_note


def _config(notes_dir: Path, blog_repo: Path) -> dict:
    return {
        "notes_dir": notes_dir,
        "blog_repo": blog_repo,
        "til_subdir": "TIL",
        "images_subdir": "images",
        "blog_til_subdir": "til",
        "author": "",
    }


class TestPublishNote:
    def test_creates_file_in_blog_repo(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        note_path = create_note(til_d, "My First TIL", today=date(2024, 1, 15))
        dest = publish_note(note_path, blog_repo, notes_dir, config)

        assert dest.exists()
        assert dest == blog_repo / "til" / note_path.name

    def test_published_front_matter_has_layout(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        note_path = create_note(til_d, "Layout Test", today=date(2024, 2, 1))
        dest = publish_note(note_path, blog_repo, notes_dir, config)

        meta, _ = parse_front_matter(dest.read_text())
        assert meta["layout"] == "til"

    def test_dry_run_does_not_create_file(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        note_path = create_note(til_d, "Dry Run Note", today=date(2024, 3, 1))
        dest = publish_note(note_path, blog_repo, notes_dir, config, dry_run=True)

        assert not dest.exists()

    def test_overwrite_on_republish(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        note_path = create_note(til_d, "Editable Note", today=date(2024, 1, 1))
        publish_note(note_path, blog_repo, notes_dir, config)

        # Edit the source note
        note_path.write_text(
            "---\ntitle: Editable Note\ndate: 2024-01-01\nlayout: til\ntags: []\n---\n\nUpdated body.\n"
        )
        dest = publish_note(note_path, blog_repo, notes_dir, config)
        assert "Updated body." in dest.read_text()

    def test_image_is_copied(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        images_src = notes_dir / "images"
        images_src.mkdir(parents=True)
        config = _config(notes_dir, blog_repo)

        # Create a fake image
        fake_img = images_src / "screenshot.png"
        fake_img.write_bytes(b"\x89PNG")

        # Create note that references the image
        til_d.mkdir(parents=True)
        note_path = til_d / "2024-01-01-img-test.md"
        note_path.write_text(
            "---\ntitle: Img Test\ndate: 2024-01-01\nlayout: til\ntags: []\n---\n\n"
            "![A screenshot](../images/screenshot.png)\n"
        )

        dest = publish_note(note_path, blog_repo, notes_dir, config)
        assert (blog_repo / "assets" / "images" / "til" / "screenshot.png").exists()
        assert "/assets/images/til/screenshot.png" in dest.read_text()

    def test_remote_image_url_unchanged(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        til_d.mkdir(parents=True)
        config = _config(notes_dir, blog_repo)

        note_path = til_d / "2024-01-01-remote.md"
        note_path.write_text(
            "---\ntitle: Remote\ndate: 2024-01-01\nlayout: til\ntags: []\n---\n\n"
            "![remote](https://example.com/img.png)\n"
        )
        dest = publish_note(note_path, blog_repo, notes_dir, config)
        assert "https://example.com/img.png" in dest.read_text()

    def test_custom_blog_til_subdir(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)
        config["blog_til_subdir"] = "_posts"

        note_path = create_note(til_d, "Posts note", today=date(2024, 1, 1))
        dest = publish_note(note_path, blog_repo, notes_dir, config)
        assert dest.parent == blog_repo / "_posts"


class TestPublishAll:
    def test_publishes_all_notes(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        create_note(til_d, "Note One", today=date(2024, 1, 1))
        create_note(til_d, "Note Two", today=date(2024, 1, 2))

        published = publish_all(notes_dir, blog_repo, config)
        assert len(published) == 2
        for dest in published:
            assert dest.exists()

    def test_empty_when_no_notes(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        config = _config(notes_dir, blog_repo)
        published = publish_all(notes_dir, blog_repo, config)
        assert published == []

    def test_dry_run_returns_paths_without_creating(self, tmp_path: Path) -> None:
        notes_dir = tmp_path / "notes"
        blog_repo = tmp_path / "blog"
        til_d = notes_dir / "TIL"
        config = _config(notes_dir, blog_repo)

        create_note(til_d, "Dry note", today=date(2024, 1, 1))
        published = publish_all(notes_dir, blog_repo, config, dry_run=True)

        assert len(published) == 1
        assert not published[0].exists()
