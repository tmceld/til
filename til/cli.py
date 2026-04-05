"""CLI entry point for til."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import click

from .config import ConfigError, images_dir, load_config, til_dir
from .notes import create_note, list_notes
from .publish import publish_all, publish_note

# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

_config_option = click.option(
    "--config",
    "-c",
    "config_path",
    default=None,
    help="Path to config file (default: ~/.til/config.yaml).",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
)


def _load(config_path: Path | None) -> dict:
    try:
        return load_config(config_path)
    except ConfigError as exc:
        raise click.ClickException(str(exc)) from exc


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option()
def cli() -> None:
    """til – capture Today I Learned notes and publish them to your blog."""


# ---------------------------------------------------------------------------
# til init
# ---------------------------------------------------------------------------

@cli.command()
@_config_option
def init(config_path: Path | None) -> None:
    """Initialise the notes directory structure.

    Creates the TIL/ and images/ subdirectories defined in the config file.
    """
    config = _load(config_path)
    td = til_dir(config)
    imgd = images_dir(config)
    td.mkdir(parents=True, exist_ok=True)
    imgd.mkdir(parents=True, exist_ok=True)
    click.echo(f"TIL dir:    {td}")
    click.echo(f"Images dir: {imgd}")
    click.echo("Initialised.")


# ---------------------------------------------------------------------------
# til new
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("title")
@click.option(
    "--tags",
    "-t",
    default="",
    help="Comma-separated list of tags, e.g. python,cli",
)
@click.option(
    "--no-edit",
    is_flag=True,
    default=False,
    help="Do not open the new note in $EDITOR.",
)
@_config_option
def new(title: str, tags: str, no_edit: bool, config_path: Path | None) -> None:
    """Create a new TIL note for TITLE.

    Opens the note in $EDITOR (when available) unless --no-edit is passed.
    """
    config = _load(config_path)
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]

    path = create_note(
        til_dir=til_dir(config),
        title=title,
        tags=tag_list,
        author=config.get("author", ""),
    )

    click.echo(f"Created: {path}")

    if not no_edit:
        editor = _find_editor()
        if editor:
            subprocess.run([editor, str(path)], check=False)
        else:
            click.echo(
                "Tip: set $EDITOR to automatically open new notes."
            )


def _find_editor() -> str | None:
    """Return the editor from $EDITOR or $VISUAL, or None."""
    return os.environ.get("EDITOR") or os.environ.get("VISUAL") or None


# ---------------------------------------------------------------------------
# til list
# ---------------------------------------------------------------------------

@cli.command(name="list")
@_config_option
def list_cmd(config_path: Path | None) -> None:
    """List all TIL notes."""
    config = _load(config_path)
    notes = list_notes(til_dir(config))

    if not notes:
        click.echo("No TIL notes found.")
        return

    for note in notes:
        tags = ", ".join(note.get("tags") or [])
        tag_str = f"  [{tags}]" if tags else ""
        click.echo(f"{note.get('date', '???')}  {note.get('title', note['path'].stem)}{tag_str}")


# ---------------------------------------------------------------------------
# til publish
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("note_slug", required=False, default=None)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be published without writing files.",
)
@_config_option
def publish(note_slug: str | None, dry_run: bool, config_path: Path | None) -> None:
    """Publish TIL notes to the blog repository.

    If NOTE_SLUG is given, publish only that note (matched by filename prefix).
    Otherwise publish all notes.
    """
    config = _load(config_path)

    if "blog_repo" not in config:
        raise click.ClickException(
            "'blog_repo' is not set in the config file.  "
            "Add the path to your local blog repository clone."
        )

    blog_repo: Path = config["blog_repo"]
    notes_dir: Path = config["notes_dir"]

    if note_slug:
        td = til_dir(config)
        matches = list(td.glob(f"*{note_slug}*.md"))
        if not matches:
            raise click.ClickException(f"No note matching '{note_slug}' found in {td}")
        if len(matches) > 1:
            click.echo("Multiple matches – publishing all of them:")
            for m in matches:
                click.echo(f"  {m.name}")

        for note_path in matches:
            dest = publish_note(
                note_path,
                blog_repo=blog_repo,
                notes_dir=notes_dir,
                config=config,
                dry_run=dry_run,
            )
            _report(note_path, dest, dry_run)
    else:
        published = publish_all(
            notes_dir=notes_dir,
            blog_repo=blog_repo,
            config=config,
            dry_run=dry_run,
        )
        if not published:
            click.echo("No notes to publish.")
        for dest in published:
            click.echo(f"{'[dry-run] ' if dry_run else ''}→ {dest}")


def _report(src: Path, dest: Path, dry_run: bool) -> None:
    prefix = "[dry-run] " if dry_run else ""
    click.echo(f"{prefix}{src.name} → {dest}")
