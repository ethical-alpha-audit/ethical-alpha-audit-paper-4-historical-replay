#!/usr/bin/env python3
"""A01: Encoding Perturbation Analysis — canonical-source verification.

Recomputes governance verdicts under +/-0.10 single-feature perturbation across
the 12 canonical historical replay cases and verifies that the recomputed
evaluations match the locked output `perturbation_summary.csv` byte-identically.

This is a verification script. It does NOT overwrite the locked outputs; it
exists so a reviewer can confirm that the locked perturbation results can be
reproduced from the committed canonical inputs and the committed engine.

Inputs (committed, repository-relative):
  data/canonical/canonical_dataset.json     -- 12 canonical cases (canonical encoding)
  engine/corrected_public_engine_v1_1.py    -- governance engine (stdlib-only)

Reference outputs (locked):
  inputs/experiment_pack/outputs/perturbation_summary.csv     (DNT-16; byte-identical to recomputation)
  inputs/experiment_pack/outputs/perturbation_results.json    (DNT-17; numerical content verified excluding timestamps)

Run from any working directory; paths are derived from this script's location.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "data" / "canonical" / "canonical_dataset.json"
ENGINE_PATH = REPO_ROOT / "engine" / "corrected_public_engine_v1_1.py"
LOCKED_CSV = REPO_ROOT / "inputs" / "experiment_pack" / "outputs" / "perturbation_summary.csv"
LOCKED_JSON = REPO_ROOT / "inputs" / "experiment_pack" / "outputs" / "perturbation_results.json"

LOCKED_ENGINE_HASH = "875f73150fae43695ecc6659581e8e25b365ad6171c9e13629fb01e923ab311c"
PROFILE = "moderate"

DELTAS = [-0.10, -0.05, 0.00, +0.05, +0.10]
GATE_FEATURES = [
    "intrinsic_safety",
    "evidence_strength",
    "bias_harm_index",
    "uncertainty_calibration",
    "traceability_integrity",
]
EXPECTED_BASELINE = {
    "epic_sepsis": "REJECT", "google_dr": "APPROVE", "google_flu": "REJECT",
    "optum_health": "REJECT", "compas": "REJECT", "amazon_recruiting": "REJECT",
    "uk_alevels": "REJECT", "microsoft_tay": "REJECT", "gender_shades": "REJECT",
    "uber_av": "REJECT", "ibm_watson": "REJECT", "babylon": "REJECT",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def clamp(val: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, val))


def evaluate_one(engine_module, case_data: dict, profile: str) -> dict:
    """Evaluate one case under the moderate profile in replay mode."""
    flat = {k: float(v["value_primary"]) for k, v in case_data["features"].items()}
    return engine_module.evaluate_case(
        {"case_id": case_data["case_id"], "features": flat},
        profile_name=profile,
        mode=engine_module.MODE_REPLAY,
    )


def main() -> int:
    # 1. Engine integrity check
    engine_hash = sha256_file(ENGINE_PATH)
    if engine_hash != LOCKED_ENGINE_HASH:
        print(f"HALT: engine hash mismatch: {engine_hash}")
        return 1

    # 2. Import engine via path manipulation (repo-relative; no env-specific paths)
    sys.path.insert(0, str(REPO_ROOT))
    from engine import corrected_public_engine_v1_1 as engine

    # 3. Load canonical cases
    canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    cases = canonical["cases"]
    if len(cases) != 12:
        print(f"HALT: expected 12 canonical cases, got {len(cases)}")
        return 1

    # Reformat each case to the engine's expected shape (case_id at top level)
    cases_normalised = {}
    for cid, case_data in cases.items():
        rec = dict(case_data)
        rec["case_id"] = cid
        cases_normalised[cid] = rec

    # 4. Baseline verification
    for cid in sorted(cases_normalised.keys()):
        r = evaluate_one(engine, cases_normalised[cid], PROFILE)
        actual = "APPROVE" if r["approved"] else "REJECT"
        if actual != EXPECTED_BASELINE[cid]:
            print(f"HALT: baseline mismatch for {cid}: expected "
                  f"{EXPECTED_BASELINE[cid]}, got {actual}")
            return 1
    print("Baseline verification: PASS (11 REJECT, 1 APPROVE)")

    # 5. Perturbation execution
    evaluations = []
    for cid in sorted(cases_normalised.keys()):
        original_verdict = EXPECTED_BASELINE[cid]
        for feature in GATE_FEATURES:
            original_value = float(
                cases_normalised[cid]["features"][feature]["value_primary"]
            )
            for delta in DELTAS:
                perturbed_value = clamp(original_value + delta)
                was_clamped = (original_value + delta) != perturbed_value

                # Build perturbed case
                perturbed = json.loads(json.dumps(cases_normalised[cid]))
                perturbed["features"][feature]["value_primary"] = perturbed_value

                r = evaluate_one(engine, perturbed, PROFILE)
                perturbed_verdict = "APPROVE" if r["approved"] else "REJECT"

                evaluations.append({
                    "case_id": cid,
                    "feature": feature,
                    "delta": delta,
                    "original_value": original_value,
                    "perturbed_value": round(perturbed_value, 10),
                    "clamped": was_clamped,
                    "original_verdict": original_verdict,
                    "perturbed_verdict": perturbed_verdict,
                    "flipped": perturbed_verdict != original_verdict,
                })

    # 6. Build CSV in memory and verify byte-identity to locked artefact
    buf = io.StringIO()
    buf.write("case_id,feature,delta,original_value,perturbed_value,clamped,"
              "original_verdict,perturbed_verdict,flipped\n")
    for e in evaluations:
        buf.write(f"{e['case_id']},{e['feature']},{e['delta']},"
                  f"{e['original_value']},{e['perturbed_value']},{e['clamped']},"
                  f"{e['original_verdict']},{e['perturbed_verdict']},{e['flipped']}\n")
    new_csv_bytes = buf.getvalue().encode("utf-8")
    new_csv_sha = hashlib.sha256(new_csv_bytes).hexdigest()
    locked_csv_sha = sha256_file(LOCKED_CSV)

    if new_csv_sha != locked_csv_sha:
        print(f"HALT: recomputed perturbation_summary.csv sha mismatch")
        print(f"  Recomputed: {new_csv_sha}")
        print(f"  Locked:     {locked_csv_sha}")
        return 1
    print(f"perturbation_summary.csv byte-identical: PASS (sha {new_csv_sha[:16]}...)")

    # 7. Verify numerical content of locked JSON matches recomputation (excluding timestamps)
    locked_json = json.loads(LOCKED_JSON.read_text(encoding="utf-8"))
    locked_evals = locked_json["evaluations"]
    if len(locked_evals) != len(evaluations):
        print(f"HALT: evaluation count mismatch "
              f"(locked={len(locked_evals)}, recomputed={len(evaluations)})")
        return 1
    # Compare each evaluation's numerical fields
    cmp_keys = ["case_id", "feature", "delta", "original_value", "perturbed_value",
                "clamped", "original_verdict", "perturbed_verdict", "flipped"]
    for i, (a, b) in enumerate(zip(locked_evals, evaluations)):
        for k in cmp_keys:
            if a.get(k) != b.get(k):
                print(f"HALT: evaluation[{i}].{k} mismatch: "
                      f"locked={a.get(k)} vs recomputed={b.get(k)}")
                return 1
    # Aggregate cross-checks
    n_flips_nb = sum(1 for e in evaluations if e["delta"] != 0.0 and e["flipped"])
    if locked_json["total_flips"] != n_flips_nb:
        print(f"HALT: total_flips mismatch")
        return 1
    nb = [e for e in evaluations if e["delta"] != 0.0]
    stability = (len(nb) - n_flips_nb) / len(nb)
    if abs(locked_json["verdict_stability_rate"] - round(stability, 4)) > 1e-4:
        print(f"HALT: verdict_stability_rate mismatch")
        return 1
    print(f"perturbation_results.json numerical content: PASS "
          f"({len(evaluations)} evaluations, {n_flips_nb} flips, stability {stability:.4f})")

    print("\n=== A01 verification COMPLETE ===")
    print(f"Total evaluations: {len(evaluations)}")
    print(f"Non-baseline evaluations: {len(nb)}")
    print(f"Verdict flips: {n_flips_nb}")
    print(f"Verdict stability rate: {stability:.4f} "
          f"({len(nb) - n_flips_nb}/{len(nb)})")
    print(f"\nAll outputs reproduce from canonical inputs.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
