"""Pre-execution checks: verify all data and engine files exist."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_engine_exists():
    assert (ROOT / "engine" / "corrected_public_engine_v1_1.py").exists()
    assert (ROOT / "engine" / "engine_manifest.json").exists()
    assert (ROOT / "engine" / "eee_overlay_adapter.py").exists()


def test_canonical_data_exists():
    assert (ROOT / "data" / "canonical" / "canonical_dataset.json").exists()
    assert (ROOT / "data" / "canonical" / "public_normalised_dataset.json").exists()
    assert (ROOT / "data" / "canonical" / "perturbation_dataset.json").exists()


def test_benchmark_data_exists():
    cases = list((ROOT / "data" / "benchmark" / "cases").glob("*.json"))
    assert len(cases) == 91, f"Expected 91 case files, found {len(cases)}"
    assert (ROOT / "data" / "benchmark" / "eee_overlay" / "canonicalised_v1.json").exists()


def test_config_exists():
    assert (ROOT / "config" / "core_equivalent_cases.json").exists()
    assert (ROOT / "config" / "notebook_plan.json").exists()
    assert (ROOT / "config" / "harness_settings.json").exists()
    assert (ROOT / "config" / "expected_outputs.json").exists()
    assert (ROOT / "config" / "trace_map.json").exists()


def test_notebooks_exist():
    for nb in ["01_dataset_intake", "02_historical_replay_execution",
               "03_metrics_and_calibration", "04_figures_and_tables"]:
        assert (ROOT / "notebooks" / f"{nb}.ipynb").exists(), f"Missing {nb}.ipynb"
