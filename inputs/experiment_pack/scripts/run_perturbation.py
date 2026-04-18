#!/usr/bin/env python3
"""A01: Encoding Perturbation Analysis — Stage 3 Execution.

Evaluates governance verdict sensitivity to ±0.10 single-feature perturbation
across the 12 canonical historical replay cases.

Protocol: Stage 2 locked. No parameter modification permitted.
"""
import json
import os
import sys
import hashlib
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone

# === LOCKED PARAMETERS ===
DELTAS = [-0.10, -0.05, 0.00, +0.05, +0.10]
GATE_FEATURES = [
    "intrinsic_safety",
    "evidence_strength",
    "bias_harm_index",
    "uncertainty_calibration",
    "traceability_integrity",
]
PROFILE = "moderate"
MODE = "replay_mode"
ENGINE_PATH = "/home/claude/evidence/engine_patch/engine/corrected_public_engine_v1_1.py"
CASES_DIR = "/home/claude/canonical_cases"
OUTPUT_DIR = "/home/claude/experiments/A01_encoding_perturbation"
LOCKED_ENGINE_HASH = "875f73150fae43695ecc6659581e8e25b365ad6171c9e13629fb01e923ab311c"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def run_engine(cases_dir, output_path):
    """Run the corrected engine and return parsed results."""
    result = subprocess.run(
        [sys.executable, ENGINE_PATH,
         "--cases-dir", cases_dir,
         "--profiles", PROFILE,
         "--mode", MODE,
         "--output", output_path],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Engine failed: {result.stderr}")
    return json.load(open(output_path))

def clamp(val, lo=0.0, hi=1.0):
    return max(lo, min(hi, val))

def main():
    start_time = datetime.now(timezone.utc).isoformat()
    
    # --- Input verification ---
    engine_hash = sha256_file(ENGINE_PATH)
    assert engine_hash == LOCKED_ENGINE_HASH, f"HALT H8: Engine hash mismatch: {engine_hash}"
    
    case_files = sorted([f for f in os.listdir(CASES_DIR) if f.endswith(".json")])
    assert len(case_files) == 12, f"Expected 12 cases, got {len(case_files)}"
    
    # Load all cases
    cases = {}
    for fn in case_files:
        d = json.load(open(os.path.join(CASES_DIR, fn)))
        cases[d["case_id"]] = d
    
    # --- Baseline verification ---
    baseline_output = os.path.join(OUTPUT_DIR, "_baseline_check.json")
    baseline = run_engine(CASES_DIR, baseline_output)
    
    expected_verdicts = {
        "epic_sepsis": "REJECT", "google_dr": "APPROVE", "google_flu": "REJECT",
        "optum_health": "REJECT", "compas": "REJECT", "amazon_recruiting": "REJECT",
        "uk_alevels": "REJECT", "microsoft_tay": "REJECT", "gender_shades": "REJECT",
        "uber_av": "REJECT", "ibm_watson": "REJECT", "babylon": "REJECT"
    }
    
    for cid, expected in expected_verdicts.items():
        actual = baseline["results"][cid]["profiles"][PROFILE]["governance_outcome"]
        assert actual == expected, f"HALT H1: Baseline mismatch for {cid}: expected {expected}, got {actual}"
    
    print("Baseline verification: PASS (11 REJECT, 1 APPROVE)")
    
    # --- Perturbation execution ---
    evaluations = []
    n_executed = 0
    
    tmpdir = tempfile.mkdtemp()
    
    try:
        for cid, case_data in sorted(cases.items()):
            original_verdict = expected_verdicts[cid]
            
            for feature in GATE_FEATURES:
                original_value = case_data["features"][feature]["value_primary"]
                
                for delta in DELTAS:
                    perturbed_value = clamp(original_value + delta)
                    was_clamped = (original_value + delta) != perturbed_value
                    
                    # Create perturbed case
                    perturbed_case = json.loads(json.dumps(case_data))
                    perturbed_case["features"][feature]["value_primary"] = perturbed_value
                    
                    # Write to temp dir (single case)
                    single_dir = os.path.join(tmpdir, "single")
                    os.makedirs(single_dir, exist_ok=True)
                    
                    # Clear directory
                    for f in os.listdir(single_dir):
                        os.remove(os.path.join(single_dir, f))
                    
                    case_path = os.path.join(single_dir, f"{cid}.json")
                    with open(case_path, "w") as f:
                        json.dump(perturbed_case, f)
                    
                    # Run engine
                    out_path = os.path.join(tmpdir, "result.json")
                    result = run_engine(single_dir, out_path)
                    
                    mod = result["results"][cid]["profiles"][PROFILE]
                    perturbed_verdict = mod["governance_outcome"]
                    
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
                        "gate_safety": mod["gate_safety"],
                        "gate_evidence": mod["gate_evidence"],
                        "gate_bias": mod["gate_bias"],
                        "gate_calibration": mod["gate_calibration"],
                        "gate_traceability": mod["gate_traceability"],
                        "compensatory_score": mod["compensatory_score"],
                    })
                    n_executed += 1
    finally:
        shutil.rmtree(tmpdir)
    
    end_time = datetime.now(timezone.utc).isoformat()
    
    # --- Results compilation ---
    n_flips = sum(1 for e in evaluations if e["flipped"])
    n_baseline = sum(1 for e in evaluations if e["delta"] == 0.0)
    n_perturbed = n_executed - n_baseline
    stability_rate = (n_perturbed - n_flips + n_baseline) / n_executed  # excluding baseline from flip count
    # More precisely: among the 240 non-baseline evaluations, how many flipped?
    non_baseline = [e for e in evaluations if e["delta"] != 0.0]
    n_flips_nonbaseline = sum(1 for e in non_baseline if e["flipped"])
    verdict_stability = (len(non_baseline) - n_flips_nonbaseline) / len(non_baseline)
    
    # --- Write outputs ---
    results_json = {
        "experiment_id": "A01",
        "engine_hash": engine_hash,
        "profile": PROFILE,
        "mode": MODE,
        "n_cases": 12,
        "n_features": 5,
        "n_deltas": 5,
        "total_evaluations": n_executed,
        "start_time": start_time,
        "end_time": end_time,
        "baseline_verification": "PASS",
        "total_flips": n_flips_nonbaseline,
        "verdict_stability_rate": round(verdict_stability, 4),
        "evaluations": evaluations,
    }
    
    with open(os.path.join(OUTPUT_DIR, "perturbation_results.json"), "w") as f:
        json.dump(results_json, f, indent=2)
    
    # Write CSV summary
    with open(os.path.join(OUTPUT_DIR, "perturbation_summary.csv"), "w") as f:
        f.write("case_id,feature,delta,original_value,perturbed_value,clamped,original_verdict,perturbed_verdict,flipped\n")
        for e in evaluations:
            f.write(f"{e['case_id']},{e['feature']},{e['delta']},{e['original_value']},{e['perturbed_value']},{e['clamped']},{e['original_verdict']},{e['perturbed_verdict']},{e['flipped']}\n")
    
    # Print summary
    print(f"\n=== A01 EXECUTION COMPLETE ===")
    print(f"Total evaluations: {n_executed}")
    print(f"Baseline checks: {n_baseline} (all delta=0.00)")
    print(f"Perturbation evaluations: {len(non_baseline)}")
    print(f"Verdict flips (non-baseline): {n_flips_nonbaseline}")
    print(f"Verdict stability rate: {verdict_stability:.4f} ({(len(non_baseline)-n_flips_nonbaseline)}/{len(non_baseline)})")
    print()
    
    # Flip detail
    flipped = [e for e in evaluations if e["flipped"] and e["delta"] != 0.0]
    if flipped:
        print("=== FLIP DETAILS ===")
        for e in flipped:
            print(f"  {e['case_id']}.{e['feature']} delta={e['delta']:+.2f}: {e['original_verdict']}→{e['perturbed_verdict']} (value: {e['original_value']}→{e['perturbed_value']})")
    else:
        print("No verdict flips detected.")
    
    # Boundary cases
    print("\n=== BOUNDARY CASES (any flip at any delta) ===")
    boundary_pairs = set()
    for e in flipped:
        boundary_pairs.add((e["case_id"], e["feature"]))
    if boundary_pairs:
        for cid, feat in sorted(boundary_pairs):
            print(f"  {cid}.{feat}")
    else:
        print("  None")

if __name__ == "__main__":
    main()
