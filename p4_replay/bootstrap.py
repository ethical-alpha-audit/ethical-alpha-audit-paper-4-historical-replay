"""Resolve repository root and optional ``engine/`` import path for notebooks and scripts."""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS = Path("config") / "harness_settings.json"


def get_repo_root(start: Path | None = None) -> Path:
    """Walk upward from *start* (default: cwd) until ``config/harness_settings.json`` exists."""
    base = (start or Path.cwd()).resolve()
    for candidate in (base, *base.parents):
        if (candidate / _HARNESS).is_file():
            return candidate
    return base


def prepare_notebook(*, engine_on_path: bool = False) -> Path:
    """Ensure repo root (and optionally ``engine/``) is on ``sys.path``; return repo root."""
    root = get_repo_root()
    r = str(root)
    if r not in sys.path:
        sys.path.insert(0, r)
    if engine_on_path:
        eng = str(root / "engine")
        if eng not in sys.path:
            sys.path.insert(0, eng)
    return root
