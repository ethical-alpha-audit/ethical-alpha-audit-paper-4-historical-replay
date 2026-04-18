#!/usr/bin/env python3
"""A03: Provenance-Tier Sensitivity Analysis — Stage 3 Execution.

Reports governance outcomes separately by provenance tier.
Uses benchmark/cases replay output for verdicts.
Uses canonical_dataset.json for Tier 1 confidence stats (authoritative).
Uses benchmark/cases for Tier 2/3 confidence stats.

Protocol: Stage 2 locked.
"""
import json
import os
import hashlib
from datetime import datetime, timezone

REPLAY_PATH = "/home/claude/test_output/full_replay.json"
CANONICAL_PATH = "/home/claude/evidence/historical_replay/ethical-alpha-audit-paper-4-historical-replay-main/data/canonical/canonical_dataset.json"
BENCHMARK_DIR = "/home/claude/evidence/historical_replay/ethical-alpha-audit-paper-4-historical-replay-main/data/benchmark/cases"
OUTPUT_DIR = "/home/claude/experiments/A03_provenance_tier"
PROFILE = "moderate"

CORE_12 = ['epic_sepsis','google_dr','google_flu','optum_health','compas','amazon_recruiting',
           'uk_alevels','microsoft_tay','gender_shades','uber_av','ibm_watson','babylon']

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def compute_confidence_stats(features_dict):
    """Compute confidence and provenance stats from a dict of features."""
    confs = []
    prov = {"direct_evidence": 0, "rule_derived": 0, "imputed_from_context": 0, "uncertain_estimate": 0}
    total = 0
    for fk, fv in features_dict.items():
        if isinstance(fv, dict) and "confidence_level" in fv:
            cl = fv["confidence_level"]
            pc = fv.get("provenance_class", "unknown")
            if cl > 0:
                confs.append(cl)
            if pc in prov:
                prov[pc] += 1
            total += 1
    mean_conf = sum(confs) / len(confs) if confs else 0
    pcts = {k: (v / total * 100 if total > 0 else 0) for k, v in prov.items()}
    return mean_conf, total, pcts

def main():
    start_time = datetime.now(timezone.utc).isoformat()
    
    # Verify inputs
    replay_hash = sha256_file(REPLAY_PATH)
    canonical_hash = sha256_file(CANONICAL_PATH)
    print(f"Replay hash: {replay_hash[:16]}...")
    print(f"Canonical hash: {canonical_hash[:16]}...")
    
    replay = json.load(open(REPLAY_PATH))
    canonical = json.load(open(CANONICAL_PATH))
    
    # Classify cases into tiers
    all_cases = list(replay["results"].keys())
    tier1_ids = [c for c in all_cases if c in CORE_12]
    tier3_ids = [c for c in all_cases if c.startswith("control_")]
    tier2_ids = [c for c in all_cases if c not in CORE_12 and not c.startswith("control_")]
    
    assert len(tier1_ids) == 12, f"Expected 12 Tier 1, got {len(tier1_ids)}"
    assert len(tier1_ids) + len(tier2_ids) + len(tier3_ids) == 91, f"Total != 91"
    
    print(f"\nTier 1: {len(tier1_ids)} cases")
    print(f"Tier 2: {len(tier2_ids)} cases")
    print(f"Tier 3: {len(tier3_ids)} cases")
    
    # --- Tier 1: Verdicts from replay, confidence from CANONICAL ---
    t1_reject = sum(1 for c in tier1_ids if replay["results"][c]["profiles"][PROFILE]["governance_outcome"] == "REJECT")
    t1_approve = len(tier1_ids) - t1_reject
    
    # Confidence from canonical
    all_t1_features = {}
    for cid in CORE_12:
        for fk, fv in canonical["cases"][cid]["features"].items():
            if cid not in all_t1_features:
                all_t1_features[cid] = {}
            all_t1_features[cid][fk] = fv
    
    t1_confs = []
    t1_prov = {"direct_evidence": 0, "rule_derived": 0, "imputed_from_context": 0, "uncertain_estimate": 0}
    t1_total = 0
    for cid in CORE_12:
        mc, tot, pcts = compute_confidence_stats(canonical["cases"][cid]["features"])
        for fk, fv in canonical["cases"][cid]["features"].items():
            if isinstance(fv, dict) and "confidence_level" in fv:
                cl = fv["confidence_level"]
                pc = fv.get("provenance_class", "unknown")
                if cl > 0:
                    t1_confs.append(cl)
                if pc in t1_prov:
                    t1_prov[pc] += 1
                t1_total += 1
    
    t1_mean_conf = sum(t1_confs) / len(t1_confs) if t1_confs else 0
    
    # Verify matches manuscript claim
    assert abs(t1_mean_conf - 0.591) < 0.001, f"HALT: Tier 1 mean confidence {t1_mean_conf} != 0.591"
    print(f"\nTier 1 mean confidence: {t1_mean_conf:.3f} (manuscript: 0.591) ✓")
    
    # --- Tier 2: Verdicts from replay, confidence from benchmark ---
    t2_reject = sum(1 for c in tier2_ids if replay["results"][c]["profiles"][PROFILE]["governance_outcome"] == "REJECT")
    t2_approve = len(tier2_ids) - t2_reject
    
    t2_confs = []
    t2_prov = {"direct_evidence": 0, "rule_derived": 0, "imputed_from_context": 0, "uncertain_estimate": 0}
    t2_total = 0
    for cid in tier2_ids:
        fp = os.path.join(BENCHMARK_DIR, f"{cid}.json")
        d = json.load(open(fp))
        for fk, fv in d.get("features", {}).items():
            if isinstance(fv, dict) and "confidence_level" in fv:
                cl = fv["confidence_level"]
                pc = fv.get("provenance_class", "unknown")
                if cl > 0:
                    t2_confs.append(cl)
                if pc in t2_prov:
                    t2_prov[pc] += 1
                t2_total += 1
    
    t2_mean_conf = sum(t2_confs) / len(t2_confs) if t2_confs else 0
    
    # --- Tier 3: Same from benchmark ---
    t3_reject = sum(1 for c in tier3_ids if replay["results"][c]["profiles"][PROFILE]["governance_outcome"] == "REJECT")
    t3_approve = len(tier3_ids) - t3_reject
    
    t3_confs = []
    t3_prov = {"direct_evidence": 0, "rule_derived": 0, "imputed_from_context": 0, "uncertain_estimate": 0}
    t3_total = 0
    for cid in tier3_ids:
        fp = os.path.join(BENCHMARK_DIR, f"{cid}.json")
        d = json.load(open(fp))
        for fk, fv in d.get("features", {}).items():
            if isinstance(fv, dict) and "confidence_level" in fv:
                cl = fv["confidence_level"]
                pc = fv.get("provenance_class", "unknown")
                if cl > 0:
                    t3_confs.append(cl)
                if pc in t3_prov:
                    t3_prov[pc] += 1
                t3_total += 1
    
    t3_mean_conf = sum(t3_confs) / len(t3_confs) if t3_confs else 0
    
    end_time = datetime.now(timezone.utc).isoformat()
    
    # --- Write CSV ---
    tiers = [
        {"tier": 1, "label": "Expert-triangulated core", "n": 12,
         "reject": t1_reject, "approve": t1_approve,
         "metric": t1_reject / 12,  # sensitivity
         "mean_conf": t1_mean_conf, "total_feats": t1_total, "prov": t1_prov},
        {"tier": 2, "label": "Additional documented failures", "n": len(tier2_ids),
         "reject": t2_reject, "approve": t2_approve,
         "metric": t2_reject / len(tier2_ids) if tier2_ids else 0,  # sensitivity
         "mean_conf": t2_mean_conf, "total_feats": t2_total, "prov": t2_prov},
        {"tier": 3, "label": "FDA-cleared controls", "n": len(tier3_ids),
         "reject": t3_reject, "approve": t3_approve,
         "metric": t3_approve / len(tier3_ids) if tier3_ids else 0,  # specificity
         "mean_conf": t3_mean_conf, "total_feats": t3_total, "prov": t3_prov},
    ]
    
    with open(os.path.join(OUTPUT_DIR, "tier_stratified_results.csv"), "w") as f:
        f.write("tier,tier_label,n_cases,n_reject,n_approve,sensitivity_or_specificity,mean_confidence,pct_direct_evidence,pct_rule_derived,pct_imputed,pct_uncertain\n")
        for t in tiers:
            prov = t["prov"]
            tot = t["total_feats"]
            f.write(f"{t['tier']},{t['label']},{t['n']},{t['reject']},{t['approve']},"
                    f"{t['metric']:.3f},{t['mean_conf']:.3f},"
                    f"{prov['direct_evidence']/tot*100:.1f},"
                    f"{prov['rule_derived']/tot*100:.1f},"
                    f"{prov['imputed_from_context']/tot*100:.1f},"
                    f"{prov['uncertain_estimate']/tot*100:.1f}\n")
    
    # --- Write report ---
    with open(os.path.join(OUTPUT_DIR, "tier_report.md"), "w") as f:
        f.write("# A03 Provenance-Tier Sensitivity Report\n\n")
        f.write(f"Replay source hash: {replay_hash[:16]}...\n")
        f.write(f"Canonical source hash: {canonical_hash[:16]}...\n\n")
        for t in tiers:
            f.write(f"## Tier {t['tier']}: {t['label']} (n={t['n']})\n")
            metric_name = "Sensitivity" if t["tier"] <= 2 else "Specificity"
            f.write(f"- {metric_name}: {t['metric']:.3f}\n")
            f.write(f"- Mean confidence: {t['mean_conf']:.3f}\n")
            prov = t["prov"]; tot = t["total_feats"]
            f.write(f"- Direct evidence: {prov['direct_evidence']/tot*100:.1f}%\n")
            f.write(f"- Rule-derived: {prov['rule_derived']/tot*100:.1f}%\n")
            f.write(f"- Imputed: {prov['imputed_from_context']/tot*100:.1f}%\n")
            f.write(f"- Uncertain: {prov['uncertain_estimate']/tot*100:.1f}%\n\n")
    
    # --- Print summary ---
    print(f"\n=== A03 EXECUTION COMPLETE ===")
    for t in tiers:
        metric_name = "Sensitivity" if t["tier"] <= 2 else "Specificity"
        print(f"  Tier {t['tier']} ({t['label']}): n={t['n']}, {metric_name}={t['metric']:.3f}, mean_conf={t['mean_conf']:.3f}")

if __name__ == "__main__":
    main()
