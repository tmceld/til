"""Tests for til.config."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
import yaml

from til.config import ConfigError, images_dir, load_config, til_dir


def _write_config(tmp_path: Path, data: dict) -> Path:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(yaml.dump(data))
    return cfg


class TestLoadConfig:
    def test_loads_valid_config(self, tmp_path: Path) -> None:
        notes = tmp_path / "notes"
        cfg = _write_config(tmp_path, {"notes_dir": str(notes)})
        config = load_config(cfg)
        assert config["notes_dir"] == notes.resolve()

    def test_resolves_tilde_in_notes_dir(self, tmp_path: Path) -> None:
        cfg = _write_config(tmp_path, {"notes_dir": "~/notes"})
        config = load_config(cfg)
        assert "~" not in str(config["notes_dir"])

    def test_resolves_blog_repo_path(self, tmp_path: Path) -> None:
        blog = tmp_path / "blog"
        cfg = _write_config(tmp_path, {"notes_dir": str(tmp_path), "blog_repo": str(blog)})
        config = load_config(cfg)
        assert config["blog_repo"] == blog.resolve()

    def test_raises_when_file_missing(self, tmp_path: Path) -> None:
        with pytest.raises(ConfigError, match="not found"):
            load_config(tmp_path / "nonexistent.yaml")

    def test_raises_when_notes_dir_missing(self, tmp_path: Path) -> None:
        cfg = _write_config(tmp_path, {"author": "me"})
        with pytest.raises(ConfigError, match="notes_dir"):
            load_config(cfg)

    def test_defaults_are_set(self, tmp_path: Path) -> None:
        cfg = _write_config(tmp_path, {"notes_dir": str(tmp_path)})
        config = load_config(cfg)
        assert config["til_subdir"] == "TIL"
        assert config["images_subdir"] == "images"
        assert config["blog_til_subdir"] == "til"
        assert config["author"] == ""

    def test_env_var_override(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        cfg = _write_config(tmp_path, {"notes_dir": str(tmp_path)})
        monkeypatch.setenv("TIL_CONFIG", str(cfg))
        config = load_config()  # no explicit path
        assert config["notes_dir"] == tmp_path.resolve()

    def test_explicit_path_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cfg1 = _write_config(tmp_path, {"notes_dir": str(tmp_path / "a")})
        sub = tmp_path / "sub"
        sub.mkdir()
        cfg2 = _write_config(sub, {"notes_dir": str(tmp_path / "b")})
        monkeypatch.setenv("TIL_CONFIG", str(cfg1))
        config = load_config(cfg2)
        assert str(config["notes_dir"]).endswith("b")


class TestDirHelpers:
    def test_til_dir(self, tmp_path: Path) -> None:
        cfg = _write_config(tmp_path, {"notes_dir": str(tmp_path)})
        config = load_config(cfg)
        assert til_dir(config) == tmp_path / "TIL"

    def test_images_dir(self, tmp_path: Path) -> None:
        cfg = _write_config(tmp_path, {"notes_dir": str(tmp_path)})
        config = load_config(cfg)
        assert images_dir(config) == tmp_path / "images"

    def test_custom_subdir(self, tmp_path: Path) -> None:
        cfg = _write_config(
            tmp_path,
            {"notes_dir": str(tmp_path), "til_subdir": "my_til", "images_subdir": "pics"},
        )
        config = load_config(cfg)
        assert til_dir(config) == tmp_path / "my_til"
        assert images_dir(config) == tmp_path / "pics"
