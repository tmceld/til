# til

A Python CLI to capture **Today I Learned** notes as Markdown files and
publish them to a [Jekyll](https://jekyllrb.com/) / GitHub Pages blog.

---

## Features

- `til new "<title>"` – create a timestamped Markdown note with YAML front matter
- `til list` – list all TIL notes
- `til publish` – copy notes (and referenced images) to your blog repo
- Importable `til.publish` module for scripting / automation
- Notes stored under `<notes_dir>/TIL/`, images under `<notes_dir>/images/`

---

## Installation

```bash
pip install -e .
```

Or, with the optional dev dependencies (required for running tests):

```bash
pip install -e ".[dev]"
```

---

## Quick start

### 1. Create a config file

Copy `config.example.yaml` to `~/.til/config.yaml` and edit it:

```yaml
notes_dir: ~/notes
blog_repo: ~/blog     # local clone of tmceld/blog
author: "Your Name"
```

### 2. Initialise the notes directory

```bash
til init
```

This creates `~/notes/TIL/` and `~/notes/images/`.

### 3. Capture a note

```bash
til new "Python f-strings support = alignment"
# or with tags:
til new "Git worktree" --tags git,workflow
```

The note opens in `$EDITOR` automatically (set `EDITOR` in your shell profile).

### 4. List notes

```bash
til list
```

### 5. Publish to your blog

```bash
# publish everything
til publish

# publish a single note (matched by slug / filename fragment)
til publish python-f-strings

# preview without writing files
til publish --dry-run
```

Published notes are written to `<blog_repo>/til/<filename>.md` with
Jekyll-compatible front matter.  Images are copied to
`<blog_repo>/assets/images/til/` and their Markdown paths are rewritten.

---

## Config reference

| Key | Required | Default | Description |
|---|---|---|---|
| `notes_dir` | ✅ | – | Root notes directory |
| `blog_repo` | for publish | – | Local path to blog repo |
| `til_subdir` | | `TIL` | Subdir inside `notes_dir` for notes |
| `images_subdir` | | `images` | Subdir inside `notes_dir` for images |
| `blog_til_subdir` | | `til` | Subdir inside `blog_repo` for published notes |
| `author` | | `""` | Default author name in front matter |

Config is loaded from (in order):

1. `--config <path>` CLI option
2. `TIL_CONFIG` environment variable
3. `~/.til/config.yaml`

---

## Note format

Each note is a Markdown file with YAML front matter:

```markdown
---
title: Python f-strings support = alignment
date: 2024-01-15
layout: til
tags:
  - python
---

<!-- Write your TIL note below -->
```python
name = "world"
print(f"{name:>10}")   # '     world'
print(f"{name!r}")     # "'world'"
```
```

---

## Using the publish module in a script

```python
from til.config import load_config
from til.publish import publish_all

config = load_config("~/.til/config.yaml")
published = publish_all(
    notes_dir=config["notes_dir"],
    blog_repo=config["blog_repo"],
    config=config,
)
for p in published:
    print(f"Published: {p}")
```

---

## Running the tests

```bash
pytest
```

---

## Blog repo layout

The tool is designed to work with the [tmceld/blog](https://github.com/tmceld/blog)
repository (GitHub Pages / Jekyll).  Published TIL notes land in:

```
blog/
└── til/
    └── 2024-01-15-python-f-strings.md
assets/
└── images/
    └── til/
        └── screenshot.png
```

You can configure `blog_til_subdir: _posts` if you prefer the standard Jekyll
posts layout instead.

