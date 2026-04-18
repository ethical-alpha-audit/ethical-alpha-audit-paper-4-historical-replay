"""Shared dataset paths and JSON loaders for notebooks and scripts."""

from __future__ import annotations

import json
from pathlib import Path
from collections.abc import Mapping
from typing import Any

STANDARD_PROFILES: tuple[str, ...] = ("permissive", "moderate", "strict", "very_strict")


def load_json(path: Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def flat_primary_case_features(case: Mapping[str, Any]) -> dict[str, float]:
    """Return ``feature_name -> value_primary`` for a case dict containing a ``features`` object."""
    feats = case["features"]
    return {k: float(v["value_primary"]) for k, v in feats.items()}


def canonical_dataset_path(root: Path) -> Path:
    return root / "data" / "canonical" / "canonical_dataset.json"


def benchmark_cases_dir(root: Path) -> Path:
    return root / "data" / "benchmark" / "cases"


def eee_overlay_path(root: Path) -> Path:
    return root / "data" / "benchmark" / "eee_overlay" / "canonicalised_v1.json"


def core_equivalent_config_path(root: Path) -> Path:
    return root / "config" / "core_equivalent_cases.json"


def public_normalised_dataset_path(root: Path) -> Path:
    return root / "data" / "canonical" / "public_normalised_dataset.json"


def perturbation_dataset_path(root: Path) -> Path:
    return root / "data" / "canonical" / "perturbation_dataset.json"


def load_replay_bundle(root: Path) -> tuple[dict, dict, dict]:
    """Load canonical, EEE overlay, and core-equivalent config JSON objects."""
    canonical = load_json(canonical_dataset_path(root))
    eee = load_json(eee_overlay_path(root))
    core_equiv = load_json(core_equivalent_config_path(root))
    return canonical, eee, core_equiv


def load_calibration_stack(root: Path) -> tuple[dict, dict, dict]:
    """Load canonical, public-normalised, and perturbation datasets."""
    return (
        load_json(canonical_dataset_path(root)),
        load_json(public_normalised_dataset_path(root)),
        load_json(perturbation_dataset_path(root)),
    )
