"""Configuration loader — reads ``config/assumptions.yaml``."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml


def get_config_dir() -> Path:
    """Return the ``config/`` directory (project root)."""
    # backend/app/core/config.py → go up 4 levels to reach project root
    return Path(__file__).resolve().parents[3] / "config"


@functools.lru_cache(maxsize=1)
def _load_assumptions() -> dict[str, Any]:
    """Load and cache ``config/assumptions.yaml``."""
    path = get_config_dir() / "assumptions.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Assumptions file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return _flatten(data)


def _flatten(data: dict, prefix: str = "") -> dict[str, Any]:
    """Flatten nested dicts using dot-separated keys.

    Leaf nodes are dicts that contain a ``value`` key.
    """
    flat: dict[str, Any] = {}
    for key, val in data.items():
        full_key = f"{prefix}.{key}" if prefix else key
        if isinstance(val, dict) and "value" not in val:
            flat.update(_flatten(val, full_key))
        else:
            flat[full_key] = val
    return flat


def get_assumption(key: str) -> dict:
    """Return the full assumption entry (value, unit, source, status, notes).

    Raises ``KeyError`` if *key* is not found.
    """
    assumptions = _load_assumptions()
    if key not in assumptions:
        raise KeyError(f"Unknown assumption key: {key!r}")
    return assumptions[key]


def get_assumption_value(key: str) -> float | int:
    """Shortcut — return only the ``value`` field of an assumption."""
    entry = get_assumption(key)
    return entry["value"]


def reload_assumptions() -> None:
    """Clear the cached assumptions — mainly for tests."""
    _load_assumptions.cache_clear()
