"""Deterministic end-to-end replay: notebooks, manifest, validation, HTML export.

Reproducibility steps executed in order:
  1. Run the four notebooks (regenerates outputs/tables/, outputs/figures/, outputs/logs/).
  2. Generate logs/actual_manifest.json (per-file sha for hash-locked outputs).
  3. Validate logs/actual_manifest.json against config/expected_outputs.json (main pipeline).
  4. Validate inputs/experiment_pack/manifest.json (auxiliary pipeline).
  5. Verify auxiliary experiment scripts reproduce locked numerical content from canonical sources.
  6. Export HTML.
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def run_step(label, cmd):
    print(f"=== {label} ===")
    result = subprocess.run(cmd, cwd=BASE_DIR, text=True)
    if result.returncode != 0:
        print(f"FAIL: {label}")
        sys.exit(result.returncode)
    print(f"OK: {label}")


def validate_experiment_pack_manifest():
    """Verify all 11 hash-locked files in inputs/experiment_pack/manifest.json."""
    print("=== Experiment pack manifest validation ===")
    manifest_path = BASE_DIR / "inputs" / "experiment_pack" / "manifest.json"
    base = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures = []
    for item in manifest["files"]:
        fp = base / item["path"]
        if not fp.exists():
            failures.append(f"Missing: {item['path']}")
            continue
        h = hashlib.sha256(fp.read_bytes()).hexdigest()
        if h != item["sha256"]:
            failures.append(f"Hash mismatch: {item['path']}")
    if failures:
        print("FAIL: Experiment pack manifest validation")
        for msg in failures:
            print(f"  - {msg}")
        sys.exit(1)
    print(f"OK: Experiment pack manifest validation ({len(manifest['files'])} files)")


def main():
    settings = json.loads(
        (BASE_DIR / "config" / "harness_settings.json").read_text(encoding="utf-8")
    )
    os.environ["PYTHONHASHSEED"] = str(settings["python_hash_seed"])
    run_step("Notebook execution", [sys.executable, "scripts/notebook_runner.py"])
    run_step("Main manifest generation", [sys.executable, "scripts/hash_manifest.py"])
    run_step("Main output validation", [sys.executable, "scripts/validate_outputs.py"])
    validate_experiment_pack_manifest()
    run_step("Auxiliary A01 (perturbation) verification",
             [sys.executable, "inputs/experiment_pack/scripts/run_perturbation.py"])
    run_step("Auxiliary A04 (conservative-bound) verification",
             [sys.executable, "inputs/experiment_pack/scripts/run_conservative.py"])
    run_step("Auxiliary A03 (provenance-tier) re-render",
             [sys.executable, "inputs/experiment_pack/scripts/provenance_tier_analysis.py"])
    run_step("HTML export", [sys.executable, "scripts/export_html.py"])
    print("ALL STEPS PASSED")


if __name__ == "__main__":
    main()
