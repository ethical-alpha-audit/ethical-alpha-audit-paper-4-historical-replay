#!/usr/bin/env python3
"""A04: Conservative-Bound Analysis — canonical-source verification.

Recomputes governance verdicts under conservative (worst-case) feature values
across the 12 canonical historical replay cases and verifies that the
recomputed numerical content matches the locked output `conservative_summary.csv`
byte-identically.

This is a verification script. It does NOT overwrite the locked outputs; it
exists so a reviewer can confirm that the locked conservative-bound results
can be reproduced from the committed canonical inputs and the committed engine.

Inputs (committed, repository-relative):
  data/canonical/canonical_dataset.json     -- 12 canonical cases (canonical encoding)
  engine/corrected_public_engine_v1_1.py    -- governance engine (stdlib-only)

Reference outputs (locked):
  inputs/experiment_pack/outputs/conservative_summary.csv     (DNT-18; byte-identical to recomputation)
  inputs/experiment_pack/outputs/conservative_results.json    (DNT-19; numerical content verified excluding timestamps)

Run from any working directory; paths are derived from this script's location.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "data" / "canonical" / "canonical_dataset.json"
ENGINE_PATH = REPO_ROOT / "engine" / "corrected_public_engine_v1_1.py"
LOCKED_CSV = REPO_ROOT / "inputs" / "experiment_pack" / "outputs" / "conservative_summary.csv"
LOCKED_JSON = REPO_ROOT / "inputs" / "experiment_pack" / "outputs" / "conservative_results.json"

LOCKED_ENGINE_HASH = "875f73150fae43695ecc6659581e8e25b365ad6171c9e13629fb01e923ab311c"
PROFILE = "moderate"

# Conservative direction per feature
CONSERVATIVE_KEY = {
    "intrinsic_safety": "value_low",
    "evidence_strength": "value_low",
    "bias_harm_index": "value_high",
    "uncertainty_calibration": "value_low",
    "traceability_integrity": "value_low",
}
GATE_FEATURES = list(CONSERVATIVE_KEY.keys())
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


def evaluate_one(engine_module, case_data: dict, profile: str) -> dict:
    flat = {k: float(v["value_primary"]) for k, v in case_data["features"].items()}
    return engine_module.evaluate_case(
        {"case_id": case_data["case_id"], "features": flat},
        profile_name=profile,
        mode=engine_module.MODE_REPLAY,
    )


def gates_failed_count(r: dict) -> int:
    """Count gates that failed (returned 0). The engine sets gate_* to 1 when passed."""
    return 5 - sum([
        r["gate_safety"], r["gate_evidence"], r["gate_bias"],
        r["gate_calibration"], r["gate_traceability"],
    ])


def main() -> int:
    engine_hash = sha256_file(ENGINE_PATH)
    if engine_hash != LOCKED_ENGINE_HASH:
        print(f"HALT: engine hash mismatch: {engine_hash}")
        return 1

    sys.path.insert(0, str(REPO_ROOT))
    from engine import corrected_public_engine_v1_1 as engine

    canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    cases = canonical["cases"]
    if len(cases) != 12:
        print(f"HALT: expected 12 canonical cases, got {len(cases)}")
        return 1

    cases_normalised = {}
    for cid, case_data in cases.items():
        rec = dict(case_data)
        rec["case_id"] = cid
        cases_normalised[cid] = rec

    # Baseline verdicts for original_gates_failed / boundary checks
    baseline_results: dict[str, dict] = {}
    for cid in sorted(cases_normalised.keys()):
        r = evaluate_one(engine, cases_normalised[cid], PROFILE)
        actual = "APPROVE" if r["approved"] else "REJECT"
        if actual != EXPECTED_BASELINE[cid]:
            print(f"HALT: baseline mismatch for {cid}: expected "
                  f"{EXPECTED_BASELINE[cid]}, got {actual}")
            return 1
        baseline_results[cid] = r
    print("Baseline verification: PASS")

    # Conservative evaluation
    results = []
    for cid in sorted(cases_normalised.keys()):
        original_verdict = EXPECTED_BASELINE[cid]

        # Build conservative case
        conservative_case = json.loads(json.dumps(cases_normalised[cid]))
        for feat in GATE_FEATURES:
            feat_data = conservative_case["features"][feat]
            key = CONSERVATIVE_KEY[feat]
            if key not in feat_data:
                print(f"HALT: missing {key} for {cid}.{feat}")
                return 1
            feat_data["value_primary"] = feat_data[key]

        r = evaluate_one(engine, conservative_case, PROFILE)
        conservative_verdict = "APPROVE" if r["approved"] else "REJECT"
        flipped = conservative_verdict != original_verdict

        if original_verdict == "REJECT" and conservative_verdict == "APPROVE":
            print(f"HALT: impossible REJECT->APPROVE flip for {cid}")
            return 1

        orig_gates = gates_failed_count(baseline_results[cid])
        cons_gates = gates_failed_count(r)

        results.append({
            "case_id": cid,
            "original_verdict": original_verdict,
            "conservative_verdict": conservative_verdict,
            "flipped": flipped,
            "original_gates_failed": orig_gates,
            "conservative_gates_failed": cons_gates,
        })

    # Build CSV in memory and verify byte-identity to locked artefact
    buf = io.StringIO()
    buf.write("case_id,original_verdict,conservative_verdict,flipped,"
              "original_gates_failed,conservative_gates_failed,"
              "binding_gate_original,binding_gate_conservative\n")
    for r in results:
        buf.write(f"{r['case_id']},{r['original_verdict']},"
                  f"{r['conservative_verdict']},{r['flipped']},"
                  f"{r['original_gates_failed']},{r['conservative_gates_failed']},,\n")
    new_csv_bytes = buf.getvalue().encode("utf-8")
    new_csv_sha = hashlib.sha256(new_csv_bytes).hexdigest()
    locked_csv_sha = sha256_file(LOCKED_CSV)

    if new_csv_sha != locked_csv_sha:
        print(f"HALT: recomputed conservative_summary.csv sha mismatch")
        print(f"  Recomputed: {new_csv_sha}")
        print(f"  Locked:     {locked_csv_sha}")
        return 1
    print(f"conservative_summary.csv byte-identical: PASS (sha {new_csv_sha[:16]}...)")

    # Verify numerical content of locked JSON matches recomputation
    locked_json = json.loads(LOCKED_JSON.read_text(encoding="utf-8"))
    locked_cases = locked_json["cases"]
    if len(locked_cases) != len(results):
        print(f"HALT: case count mismatch "
              f"(locked={len(locked_cases)}, recomputed={len(results)})")
        return 1
    cmp_keys = ["case_id", "original_verdict", "conservative_verdict", "flipped",
                "original_gates_failed", "conservative_gates_failed"]
    for a, b in zip(locked_cases, results):
        for k in cmp_keys:
            if a.get(k) != b.get(k):
                print(f"HALT: case[{a.get('case_id')}].{k} mismatch: "
                      f"locked={a.get(k)} vs recomputed={b.get(k)}")
                return 1
    print(f"conservative_results.json numerical content: PASS "
          f"({len(results)} cases)")

    n_maintained = sum(1 for r in results if not r["flipped"])
    n_flipped = sum(1 for r in results if r["flipped"])

    print(f"\n=== A04 verification COMPLETE ===")
    print(f"Cases: {len(results)}")
    print(f"Verdicts maintained: {n_maintained}/12")
    print(f"Verdict flips: {n_flipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
