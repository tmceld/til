"""Config loading for the til CLI.

The config file is looked up in the following order:
1. Path passed explicitly (e.g. from a CLI option).
2. ``TIL_CONFIG`` environment variable.
3. ``~/.til/config.yaml``
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

_DEFAULT_CONFIG_PATH = Path.home() / ".til" / "config.yaml"

REQUIRED_KEYS = ("notes_dir",)


class ConfigError(ValueError):
    """Raised when the config file is missing or invalid."""


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load and validate the til config file.

    Parameters
    ----------
    config_path:
        Explicit path to the config file.  When *None* the default
        search order described in the module docstring is used.

    Returns
    -------
    dict
        Parsed configuration dictionary with ``notes_dir`` resolved to
        an absolute :class:`~pathlib.Path`.

    Raises
    ------
    ConfigError
        If the config file cannot be found or is missing required keys.
    """
    if config_path is None:
        env_path = os.environ.get("TIL_CONFIG")
        config_path = Path(env_path) if env_path else _DEFAULT_CONFIG_PATH

    config_path = Path(config_path).expanduser().resolve()

    if not config_path.exists():
        raise ConfigError(
            f"Config file not found: {config_path}\n"
            "Run `til init` or create the file manually.  "
            "See config.example.yaml for reference."
        )

    with config_path.open() as fh:
        data: dict[str, Any] = yaml.safe_load(fh) or {}

    for key in REQUIRED_KEYS:
        if key not in data:
            raise ConfigError(f"Missing required config key: '{key}'")

    # Resolve paths
    data["notes_dir"] = Path(str(data["notes_dir"])).expanduser().resolve()

    if "blog_repo" in data:
        data["blog_repo"] = Path(str(data["blog_repo"])).expanduser().resolve()

    # Defaults
    data.setdefault("til_subdir", "TIL")
    data.setdefault("images_subdir", "images")
    data.setdefault("blog_til_subdir", "til")
    data.setdefault("author", "")

    return data


def til_dir(config: dict[str, Any]) -> Path:
    """Return the absolute path to the TIL notes folder."""
    return config["notes_dir"] / config["til_subdir"]


def images_dir(config: dict[str, Any]) -> Path:
    """Return the absolute path to the images folder."""
    return config["notes_dir"] / config["images_subdir"]
