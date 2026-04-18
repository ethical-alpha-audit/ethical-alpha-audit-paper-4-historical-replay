#!/usr/bin/env python3
"""A04: Conservative-Bound Analysis — Stage 3 Execution.

Re-evaluates all 12 canonical cases using worst-case (least favourable)
feature values: value_low for all features except bias_harm_index which
uses value_high (higher bias = worse outcome).

Protocol: Stage 2 locked.
"""
import json
import os
import sys
import hashlib
import subprocess
import tempfile
import shutil
from datetime import datetime, timezone

ENGINE_PATH = "/home/claude/evidence/engine_patch/engine/corrected_public_engine_v1_1.py"
CASES_DIR = "/home/claude/canonical_cases"
OUTPUT_DIR = "/home/claude/experiments/A04_conservative_bound"
LOCKED_ENGINE_HASH = "875f73150fae43695ecc6659581e8e25b365ad6171c9e13629fb01e923ab311c"
PROFILE = "moderate"
MODE = "replay_mode"

# Conservative direction per feature
CONSERVATIVE_KEY = {
    "intrinsic_safety": "value_low",       # lower = worse
    "evidence_strength": "value_low",       # lower = worse
    "bias_harm_index": "value_high",        # higher = worse (more biased)
    "uncertainty_calibration": "value_low",  # lower = worse
    "traceability_integrity": "value_low",   # lower = worse
}

GATE_FEATURES = list(CONSERVATIVE_KEY.keys())

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def run_engine(cases_dir, output_path):
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

def main():
    start_time = datetime.now(timezone.utc).isoformat()
    
    engine_hash = sha256_file(ENGINE_PATH)
    assert engine_hash == LOCKED_ENGINE_HASH, f"HALT H8: Engine hash mismatch"
    
    case_files = sorted([f for f in os.listdir(CASES_DIR) if f.endswith(".json")])
    assert len(case_files) == 12
    
    # Load cases
    cases = {}
    for fn in case_files:
        d = json.load(open(os.path.join(CASES_DIR, fn)))
        cases[d["case_id"]] = d
    
    # Baseline control
    baseline_out = os.path.join(OUTPUT_DIR, "_baseline_check.json")
    baseline = run_engine(CASES_DIR, baseline_out)
    
    expected = {
        "epic_sepsis": "REJECT", "google_dr": "APPROVE", "google_flu": "REJECT",
        "optum_health": "REJECT", "compas": "REJECT", "amazon_recruiting": "REJECT",
        "uk_alevels": "REJECT", "microsoft_tay": "REJECT", "gender_shades": "REJECT",
        "uber_av": "REJECT", "ibm_watson": "REJECT", "babylon": "REJECT"
    }
    for cid, exp in expected.items():
        actual = baseline["results"][cid]["profiles"][PROFILE]["governance_outcome"]
        assert actual == exp, f"HALT H1: Baseline mismatch {cid}: {exp} vs {actual}"
    print("Baseline verification: PASS")
    
    # Conservative evaluation
    tmpdir = tempfile.mkdtemp()
    results = []
    
    try:
        for cid, case_data in sorted(cases.items()):
            # Create conservative case
            cons_case = json.loads(json.dumps(case_data))
            cons_features = {}
            
            for feat in GATE_FEATURES:
                feat_data = cons_case["features"][feat]
                key = CONSERVATIVE_KEY[feat]
                
                if key not in feat_data:
                    raise RuntimeError(f"HALT H4: Missing {key} for {cid}.{feat}")
                
                original_val = feat_data["value_primary"]
                conservative_val = feat_data[key]
                cons_features[feat] = {
                    "original": original_val,
                    "conservative": conservative_val,
                    "key_used": key,
                }
                feat_data["value_primary"] = conservative_val
            
            # Write and run
            single_dir = os.path.join(tmpdir, "single")
            os.makedirs(single_dir, exist_ok=True)
            for f in os.listdir(single_dir):
                os.remove(os.path.join(single_dir, f))
            
            with open(os.path.join(single_dir, f"{cid}.json"), "w") as f:
                json.dump(cons_case, f)
            
            out_path = os.path.join(tmpdir, "result.json")
            result = run_engine(single_dir, out_path)
            mod = result["results"][cid]["profiles"][PROFILE]
            
            orig_mod = baseline["results"][cid]["profiles"][PROFILE]
            orig_gates_failed = 5 - sum([orig_mod["gate_safety"], orig_mod["gate_evidence"],
                                          orig_mod["gate_bias"], orig_mod["gate_calibration"],
                                          orig_mod["gate_traceability"]])
            cons_gates_failed = 5 - sum([mod["gate_safety"], mod["gate_evidence"],
                                          mod["gate_bias"], mod["gate_calibration"],
                                          mod["gate_traceability"]])
            
            original_verdict = expected[cid]
            conservative_verdict = mod["governance_outcome"]
            flipped = conservative_verdict != original_verdict
            
            # Boundary notes
            boundary_note = None
            if cid == "google_dr":
                boundary_note = (
                    f"Safety: conservative={cons_features['intrinsic_safety']['conservative']}, "
                    f"threshold=0.50, gate_pass={mod['gate_safety']}. "
                    f"Calibration: conservative={cons_features['uncertainty_calibration']['conservative']}, "
                    f"threshold=0.40, gate_pass={mod['gate_calibration']}."
                )
            
            results.append({
                "case_id": cid,
                "original_verdict": original_verdict,
                "conservative_verdict": conservative_verdict,
                "flipped": flipped,
                "original_gates_failed": orig_gates_failed,
                "conservative_gates_failed": cons_gates_failed,
                "conservative_feature_values": {
                    feat: cons_features[feat]["conservative"] for feat in GATE_FEATURES
                },
                "boundary_note": boundary_note,
            })
            
            # HALT check: REJECT→APPROVE should be impossible
            if original_verdict == "REJECT" and conservative_verdict == "APPROVE":
                raise RuntimeError(f"HALT: Impossible REJECT→APPROVE flip for {cid}")
    finally:
        shutil.rmtree(tmpdir)
    
    end_time = datetime.now(timezone.utc).isoformat()
    
    # Write outputs
    output_json = {
        "experiment_id": "A04",
        "engine_hash": engine_hash,
        "profile": PROFILE,
        "start_time": start_time,
        "end_time": end_time,
        "cases": results,
    }
    with open(os.path.join(OUTPUT_DIR, "conservative_results.json"), "w") as f:
        json.dump(output_json, f, indent=2)
    
    # CSV
    with open(os.path.join(OUTPUT_DIR, "conservative_summary.csv"), "w") as f:
        f.write("case_id,original_verdict,conservative_verdict,flipped,original_gates_failed,conservative_gates_failed,binding_gate_original,binding_gate_conservative\n")
        for r in results:
            # Determine binding gate (first failed gate)
            f.write(f"{r['case_id']},{r['original_verdict']},{r['conservative_verdict']},{r['flipped']},{r['original_gates_failed']},{r['conservative_gates_failed']},,\n")
    
    # Summary
    n_maintained = sum(1 for r in results if not r["flipped"])
    n_flipped = sum(1 for r in results if r["flipped"])
    
    print(f"\n=== A04 EXECUTION COMPLETE ===")
    print(f"Cases evaluated: {len(results)}")
    print(f"Verdicts maintained: {n_maintained}/12")
    print(f"Verdict flips: {n_flipped}")
    
    for r in results:
        status = "FLIP" if r["flipped"] else "SAME"
        print(f"  {r['case_id']:<22} {r['original_verdict']:<8} → {r['conservative_verdict']:<8} [{status}]")
        if r["boundary_note"]:
            print(f"    BOUNDARY: {r['boundary_note']}")

if __name__ == "__main__":
    main()
