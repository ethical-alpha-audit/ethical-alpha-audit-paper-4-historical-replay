#!/usr/bin/env python3
"""A03: Provenance-Tier Sensitivity Analysis — canonical-source edition.

Reports governance outcomes separately by provenance tier.

Verdict source (canonical): outputs/tables/replay_results.csv (layer=expanded, profile=moderate).
Confidence/provenance source (Tier 1): data/canonical/canonical_dataset.json.
Confidence/provenance source (Tier 2/3): data/benchmark/cases/*.json.

This is a canonical re-execution. The previous artefact used a non-committed intermediate
replay artefact whose verdicts diverged from the locked replay_results.csv on Tier 1
(Google DR). The canonical pipeline (this script) produces Tier 1 sensitivity = 0.917,
in agreement with the manuscript primary metric.

All paths are repository-relative; reviewers can re-execute from the repo root with no
environment-specific configuration.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_PATH = REPO_ROOT / "data" / "canonical" / "canonical_dataset.json"
BENCHMARK_DIR = REPO_ROOT / "data" / "benchmark" / "cases"
REPLAY_CSV = REPO_ROOT / "outputs" / "tables" / "replay_results.csv"
OUTPUT_DIR = REPO_ROOT / "inputs" / "experiment_pack" / "outputs"
PROFILE = "moderate"

CORE_12 = ['epic_sepsis', 'google_dr', 'google_flu', 'optum_health', 'compas',
           'amazon_recruiting', 'uk_alevels', 'microsoft_tay', 'gender_shades',
           'uber_av', 'ibm_watson', 'babylon']


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_verdicts_from_csv(csv_path: Path, profile: str) -> dict[str, str]:
    """Build {case_id: 'REJECT'|'APPROVE'} from replay_results.csv (layer=expanded)."""
    verdicts: dict[str, str] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["layer"] != "expanded":
                continue
            if row["profile"] != profile:
                continue
            verdicts[row["case_id"]] = "REJECT" if row["approved"] == "0" else "APPROVE"
    return verdicts


def confidence_stats(features: dict) -> tuple[float, int, dict[str, int]]:
    """Return (mean_confidence, total_features, provenance_counts)."""
    confs: list[float] = []
    prov = {"direct_evidence": 0, "rule_derived": 0,
            "imputed_from_context": 0, "uncertain_estimate": 0}
    total = 0
    for fk, fv in features.items():
        if isinstance(fv, dict) and "confidence_level" in fv:
            cl = fv["confidence_level"]
            pc = fv.get("provenance_class", "unknown")
            if cl > 0:
                confs.append(cl)
            if pc in prov:
                prov[pc] += 1
            total += 1
    mean = sum(confs) / len(confs) if confs else 0.0
    return mean, total, prov


def aggregate_stats(case_ids: list[str], features_by_case: dict[str, dict]) -> dict:
    confs: list[float] = []
    prov = {"direct_evidence": 0, "rule_derived": 0,
            "imputed_from_context": 0, "uncertain_estimate": 0}
    total = 0
    for cid in case_ids:
        feats = features_by_case[cid]
        for fk, fv in feats.items():
            if isinstance(fv, dict) and "confidence_level" in fv:
                cl = fv["confidence_level"]
                pc = fv.get("provenance_class", "unknown")
                if cl > 0:
                    confs.append(cl)
                if pc in prov:
                    prov[pc] += 1
                total += 1
    mean = sum(confs) / len(confs) if confs else 0.0
    return {"mean_conf": mean, "total_feats": total, "prov": prov}


def main() -> None:
    canonical = json.loads(CANONICAL_PATH.read_text(encoding="utf-8"))
    verdicts = load_verdicts_from_csv(REPLAY_CSV, PROFILE)

    all_cases = sorted(verdicts.keys())
    tier1_ids = [c for c in all_cases if c in CORE_12]
    tier3_ids = [c for c in all_cases if c.startswith("control_")]
    tier2_ids = [c for c in all_cases if c not in CORE_12 and not c.startswith("control_")]

    if len(tier1_ids) != 12:
        sys.exit(f"HALT: Tier 1 has {len(tier1_ids)} cases (expected 12)")
    if len(tier1_ids) + len(tier2_ids) + len(tier3_ids) != 91:
        sys.exit(f"HALT: total {len(tier1_ids) + len(tier2_ids) + len(tier3_ids)} != 91")

    # Tier 1 confidence/provenance from CANONICAL dataset
    tier1_features = {cid: canonical["cases"][cid]["features"] for cid in CORE_12}
    t1_stats = aggregate_stats(CORE_12, tier1_features)

    # Tier 2/3 confidence/provenance from benchmark
    tier2_features = {cid: json.loads((BENCHMARK_DIR / f"{cid}.json").read_text(encoding="utf-8"))["features"]
                      for cid in tier2_ids}
    tier3_features = {cid: json.loads((BENCHMARK_DIR / f"{cid}.json").read_text(encoding="utf-8"))["features"]
                      for cid in tier3_ids}
    t2_stats = aggregate_stats(tier2_ids, tier2_features)
    t3_stats = aggregate_stats(tier3_ids, tier3_features)

    # Verdict counts (from canonical replay_results.csv)
    t1_reject = sum(1 for c in tier1_ids if verdicts[c] == "REJECT")
    t1_approve = len(tier1_ids) - t1_reject
    t2_reject = sum(1 for c in tier2_ids if verdicts[c] == "REJECT")
    t2_approve = len(tier2_ids) - t2_reject
    t3_reject = sum(1 for c in tier3_ids if verdicts[c] == "REJECT")
    t3_approve = len(tier3_ids) - t3_reject

    tiers = [
        {"tier": 1, "label": "Expert-triangulated core (canonical-source verdicts)",
         "n": 12, "reject": t1_reject, "approve": t1_approve,
         "metric": t1_reject / 12, "stats": t1_stats},
        {"tier": 2, "label": "Additional documented failures",
         "n": len(tier2_ids), "reject": t2_reject, "approve": t2_approve,
         "metric": t2_reject / len(tier2_ids) if tier2_ids else 0.0,
         "stats": t2_stats},
        {"tier": 3, "label": "FDA-cleared controls",
         "n": len(tier3_ids), "reject": t3_reject, "approve": t3_approve,
         "metric": t3_approve / len(tier3_ids) if tier3_ids else 0.0,
         "stats": t3_stats},
    ]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # tier_stratified_results.csv (deterministic; LF line endings as before)
    csv_path = OUTPUT_DIR / "tier_stratified_results.csv"
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("tier,tier_label,n_cases,n_reject,n_approve,sensitivity_or_specificity,"
                "mean_confidence,pct_direct_evidence,pct_rule_derived,pct_imputed,pct_uncertain\n")
        for t in tiers:
            prov = t["stats"]["prov"]
            tot = t["stats"]["total_feats"]
            f.write(f"{t['tier']},{t['label']},{t['n']},{t['reject']},{t['approve']},"
                    f"{t['metric']:.3f},{t['stats']['mean_conf']:.3f},"
                    f"{prov['direct_evidence']/tot*100:.1f},"
                    f"{prov['rule_derived']/tot*100:.1f},"
                    f"{prov['imputed_from_context']/tot*100:.1f},"
                    f"{prov['uncertain_estimate']/tot*100:.1f}\n")

    # tier_report.md
    canonical_hash = sha256_file(CANONICAL_PATH)
    replay_hash = sha256_file(REPLAY_CSV)
    md_path = OUTPUT_DIR / "tier_report.md"
    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("# A03 Provenance-Tier Sensitivity Report\n\n")
        f.write(f"Verdict source: outputs/tables/replay_results.csv "
                f"(layer=expanded, profile={PROFILE}; sha256: {replay_hash[:16]}...)\n")
        f.write(f"Canonical source: data/canonical/canonical_dataset.json "
                f"(sha256: {canonical_hash[:16]}...)\n\n")
        for t in tiers:
            metric_name = "Sensitivity" if t["tier"] <= 2 else "Specificity"
            prov = t["stats"]["prov"]
            tot = t["stats"]["total_feats"]
            f.write(f"## Tier {t['tier']}: {t['label']} (n={t['n']})\n")
            f.write(f"- {metric_name}: {t['metric']:.3f}\n")
            f.write(f"- Mean confidence: {t['stats']['mean_conf']:.3f}\n")
            f.write(f"- Direct evidence: {prov['direct_evidence']/tot*100:.1f}%\n")
            f.write(f"- Rule-derived: {prov['rule_derived']/tot*100:.1f}%\n")
            f.write(f"- Imputed: {prov['imputed_from_context']/tot*100:.1f}%\n")
            f.write(f"- Uncertain: {prov['uncertain_estimate']/tot*100:.1f}%\n\n")

    # Console summary
    print("=== A03 (canonical-source) ===")
    for t in tiers:
        metric_name = "Sensitivity" if t["tier"] <= 2 else "Specificity"
        print(f"  Tier {t['tier']} ({t['label']}): n={t['n']}, "
              f"{metric_name}={t['metric']:.3f}, mean_conf={t['stats']['mean_conf']:.3f}")
    print(f"\nWrote {md_path}")
    print(f"Wrote {csv_path}")


if __name__ == "__main__":
    main()
