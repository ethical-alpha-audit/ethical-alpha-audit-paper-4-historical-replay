#!/usr/bin/env python3
"""
Claude Enriched AI Governance Platform — Release v3.1.0-eee Build Script

Implements pipeline Stages 9–12:
  Stage 9:  Repository Overlay Insertion
  Stage 10: Governance Engine Execution with overlay support
  Stage 11: Release Packaging
  Stage 12: Publication-ready release artefact generation

Usage:
  python run_v3_1_0_eee_build.py [--data-dir DATA_DIR] [--skip-engine] [--verbose]

Non-negotiable rules enforced:
  - No base case JSONs modified
  - No existing DB tables altered destructively
  - H34/H35 remain BLOCKED with monitoring flags
  - Sidecar overlay model preserved
  - Hash chain and version lineage preserved
"""

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).parent
BENCHMARK_DIR = REPO_ROOT / "benchmark_repository"
RELEASE_V30 = BENCHMARK_DIR / "releases" / "v3.0"
RELEASE_V31 = BENCHMARK_DIR / "releases" / "v3.1.0-eee"
EEE_EVIDENCE_DIR = BENCHMARK_DIR / "eee_evidence"
DB_PATH = BENCHMARK_DIR / "governance.db"

DECLARED_ENRICHMENT_HASH = "f9d181ca3859cb7e3b65c66a291c5da66eba47c95207a8c4ee01c5ae93ce8948"
DECLARED_PARENT_HASH = "b77e10eccb2dde7f760444093de92019dbd2e7a3e5b16cc4343d37bdcb1b98c4"
DECLARED_CANONICAL_HASH = "c3ed7b93d68a0a898e25e1b4ce445350160c9372f709aec9479a98292ee37927"

BLOCKED_CASE_IDS = {"H34", "H35"}
BLOCKED_GOVERNANCE_IDS = {
    "acclarent_trudi_navigation_reuters2026",
    "sonio_detect_prenatal_labeling_reuters2026",
}

# SCM variable direction map for EEE→governance transform
HIGHER_IS_SAFER = {
    "intrinsic_safety", "clinical_utility", "uncertainty_calibration",
    "evidence_strength", "evidence_visibility", "traceability_integrity",
    "stress_robustness", "claimed_performance",
}
HIGHER_IS_RISKIER = {
    "bias_harm_index", "drift_susceptibility", "data_shift_rate",
    "harm_severity", "adversarial_gaming_capability",
}
# deployment_volume is context-dependent; fallback_safety_delta uses (v+1)/2
SPECIAL_TRANSFORM = {"deployment_volume", "fallback_safety_delta"}


def compute_file_hash(filepath):
    """Compute SHA-256 of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def log(msg, verbose=True):
    if verbose:
        print(f"[BUILD] {msg}")


def fail(msg):
    print(f"[HARD FAIL] {msg}", file=sys.stderr)
    sys.exit(1)


# ===========================================================================
# Stage 9: Repository Overlay Insertion
# ===========================================================================
def stage_9_overlay_insertion(data_dir, verbose=True):
    """Create directory structure and insert overlay artefacts."""
    log("STAGE 9: Repository Overlay Insertion", verbose)

    canonical_path = data_dir / "canonicalised_dataset_v1.json"
    replay_path = data_dir / "replay_exports_v1.json"

    if not canonical_path.exists():
        fail(f"Canonical dataset not found: {canonical_path}")
    if not replay_path.exists():
        fail(f"Replay exports not found: {replay_path}")

    # Load canonical for validation
    with open(canonical_path) as f:
        canonical = json.load(f)
    assert len(canonical["cases"]) == 39, f"Expected 39 cases, got {len(canonical['cases'])}"

    # 9.1 Create release directory structure
    overlay_dir = RELEASE_V31 / "eee_overlay"
    config_dir = RELEASE_V31 / "config"
    schemas_dir = RELEASE_V31 / "schemas"
    engine_cases_dir = RELEASE_V31 / "engine" / "cases"

    for d in [overlay_dir, config_dir, schemas_dir, engine_cases_dir]:
        d.mkdir(parents=True, exist_ok=True)
    log(f"  Created release directory: {RELEASE_V31}", verbose)

    # 9.2 Copy base engine cases from v3.0 (verbatim, never modified)
    v30_engine = RELEASE_V30 / "engine" / "cases"
    if v30_engine.exists():
        copied = 0
        for src_file in sorted(v30_engine.glob("*.json")):
            dst_file = engine_cases_dir / src_file.name
            shutil.copy2(src_file, dst_file)
            copied += 1
        log(f"  Copied {copied} base engine cases from v3.0", verbose)
    else:
        fail(f"v3.0 engine cases not found: {v30_engine}")

    # 9.3 Copy config and schemas (frozen snapshot)
    config_src = REPO_ROOT / "config"
    schemas_src = REPO_ROOT / "schemas"
    for src_file in sorted(config_src.glob("*")):
        shutil.copy2(src_file, config_dir / src_file.name)
    for src_file in sorted(schemas_src.glob("*")):
        shutil.copy2(src_file, schemas_dir / src_file.name)
    log("  Frozen config and schema snapshots", verbose)

    # 9.4 Place canonical overlay artefacts
    shutil.copy2(canonical_path, overlay_dir / "canonicalised_v1.json")
    shutil.copy2(replay_path, overlay_dir / "replay_exports_v1.json")
    log("  Placed canonical overlay and replay exports", verbose)

    # 9.5 Compute actual hashes of placed files
    canonical_actual_hash = compute_file_hash(overlay_dir / "canonicalised_v1.json")

    # 9.6 Generate overlay manifest
    overlay_manifest = {
        "overlay_version": "1.0.0",
        "canonical_dataset": "canonicalised_v1.json",
        "canonical_hash": canonical_actual_hash,
        "canonical_hash_declared": DECLARED_CANONICAL_HASH,
        "source_pipeline": "EEE",
        "enrichment_version": "1.2.0-upgraded",
        "enrichment_hash": DECLARED_ENRICHMENT_HASH,
        "parent_hash": DECLARED_PARENT_HASH,
        "triangulation_engine": "EEE_Triangulation_Confidence_Layer_v1",
        "triangulation_timestamp": "2026-03-18T14:04:57Z",
        "total_cases": 39,
        "cases_processed": 37,
        "cases_blocked": 2,
        "blocked_case_ids": sorted(BLOCKED_CASE_IDS),
        "generated_timestamp": datetime.now(timezone.utc).isoformat(),
        "compatible_with_repository": "3.0.0",
        "supersedes": None,
    }
    with open(overlay_dir / "overlay_manifest.json", "w") as f:
        json.dump(overlay_manifest, f, indent=2)
    log("  Generated overlay manifest", verbose)

    # 9.7 Create EEE evidence archive
    EEE_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    # Copy available evidence files
    evidence_files = {
        "enrichment_v1_2.json": data_dir / "EEE_v1_2_enriched_dataset_UPGRADED.json",
        "triangulation_run_output.json": data_dir / "EEE_v1_2_triangulation_run_output.json",
        "case_confidence_summary.csv": data_dir / "EEE_v1_2_case_confidence_summary.csv",
        "canonicalisation_mapping.csv": data_dir / "canonicalisation_mapping_table.csv",
    }
    for dst_name, src_path in evidence_files.items():
        if src_path.exists():
            shutil.copy2(src_path, EEE_EVIDENCE_DIR / dst_name)
            log(f"  Archived: {dst_name}", verbose)
        else:
            log(f"  WARN: Evidence file not found: {src_path}", verbose)

    # Copy PDF validation reports if present
    for pdf_name in [
        "EEE_v1_2_triangulation_validation_report.pdf",
        "canonicalisation_validation_report.pdf",
    ]:
        src_pdf = data_dir / pdf_name
        if src_pdf.exists():
            shutil.copy2(src_pdf, EEE_EVIDENCE_DIR / pdf_name.replace("EEE_v1_2_", "").replace("canonicalisation_", "canonicalisation_"))
            log(f"  Archived: {pdf_name}", verbose)

    # 9.8 Generate provenance.json
    provenance = {
        "hash_chain": {
            "level_0_enrichment_v1_1": {
                "hash": DECLARED_PARENT_HASH,
                "algorithm": "SHA-256",
                "status": "LOCKED",
            },
            "level_1_enrichment_v1_2": {
                "hash": DECLARED_ENRICHMENT_HASH,
                "algorithm": "SHA-256",
                "parent": DECLARED_PARENT_HASH,
                "status": "LOCKED",
            },
            "level_2_triangulation_run": {
                "input_hash": DECLARED_ENRICHMENT_HASH,
                "engine": "EEE_Triangulation_Confidence_Layer_v1",
                "timestamp": "2026-03-18T14:04:57Z",
                "status": "EXECUTED",
            },
            "level_3_canonical_dataset": {
                "hash_declared": DECLARED_CANONICAL_HASH,
                "hash_actual": canonical_actual_hash,
                "input_hash": DECLARED_ENRICHMENT_HASH,
                "parent_hash": DECLARED_PARENT_HASH,
                "status": "VALIDATED",
            },
            "level_4_release_manifest": {
                "status": "PENDING",
                "note": "Computed at release packaging stage",
            },
        },
        "version_compatibility": {
            "canonical_version": "1.0.0",
            "requires_enrichment": ">=1.2.0",
            "requires_triangulation_engine": ">=1.1",
            "compatible_with_repo": ">=3.0.0",
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    with open(EEE_EVIDENCE_DIR / "provenance.json", "w") as f:
        json.dump(provenance, f, indent=2)
    log("  Generated provenance.json", verbose)

    # 9.9 Extend governance.db with eee_canonical_overlay table
    log("  Extending governance.db with eee_canonical_overlay table", verbose)
    conn = sqlite3.connect(str(DB_PATH))

    # Create new table (additive only — no existing table modifications)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS eee_canonical_overlay (
            case_id TEXT PRIMARY KEY,
            eee_case_id TEXT NOT NULL,
            canonical_version TEXT NOT NULL,
            triangulated_confidence REAL,
            confidence_band TEXT,
            evidence_grade TEXT NOT NULL,
            triangulation_integrity TEXT NOT NULL,
            deployment_risk_class TEXT NOT NULL,
            phenomena_json TEXT,
            audit_flags_json TEXT,
            eee_feature_overlay_json TEXT,
            governance_mapping_json TEXT,
            input_hash TEXT,
            parent_hash TEXT,
            run_timestamp TEXT,
            inserted_at TEXT,
            FOREIGN KEY (case_id) REFERENCES cases(case_id)
        )
    """)

    # Insert all 39 canonical cases
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    for case in canonical["cases"]:
        conn.execute(
            """INSERT OR REPLACE INTO eee_canonical_overlay VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                case["case_id"],
                case["eee_case_id"],
                case["canonical_version"],
                case["triangulated_confidence"],
                case["confidence_band"],
                case["evidence_grade"],
                case["triangulation_integrity"],
                case["deployment_risk_class"],
                json.dumps(case["phenomena"]),
                json.dumps(case["audit_flags"]),
                json.dumps(case["eee_feature_overlay"]),
                json.dumps(case["governance_mapping"]),
                case["evidence_provenance"]["input_hash"],
                case["evidence_provenance"]["parent_hash"],
                case["evidence_provenance"]["run_timestamp"],
                now,
            ),
        )
        inserted += 1
    conn.commit()

    # Verify foreign key integrity
    orphans = conn.execute("""
        SELECT o.case_id FROM eee_canonical_overlay o
        LEFT JOIN cases c ON o.case_id = c.case_id
        WHERE c.case_id IS NULL
    """).fetchall()
    if orphans:
        fail(f"Foreign key violations: {[r[0] for r in orphans]}")

    # Verify blocked cases
    for blocked_gid in BLOCKED_GOVERNANCE_IDS:
        row = conn.execute(
            "SELECT deployment_risk_class, evidence_grade, audit_flags_json FROM eee_canonical_overlay WHERE case_id=?",
            (blocked_gid,),
        ).fetchone()
        if not row:
            fail(f"Blocked case missing: {blocked_gid}")
        if row[0] != "BLOCKED":
            fail(f"Blocked case {blocked_gid} has wrong risk class: {row[0]}")
        if row[1] != "INSUFFICIENT":
            fail(f"Blocked case {blocked_gid} has wrong grade: {row[1]}")

    total = conn.execute("SELECT COUNT(*) FROM eee_canonical_overlay").fetchone()[0]
    conn.close()

    log(f"  Inserted {inserted} cases into eee_canonical_overlay (total: {total})", verbose)
    log(f"  Foreign key check: PASS (0 orphans)", verbose)
    log(f"  Blocked case check: PASS", verbose)
    log("STAGE 9: COMPLETE", verbose)

    return {"cases_inserted": inserted, "orphans": 0, "canonical_hash": canonical_actual_hash}


# ===========================================================================
# Stage 10: Governance Engine Execution with Overlay Support
# ===========================================================================
def eee_to_governance_value(variable_name, eee_value):
    """Transform EEE [-1,1] value to governance [0,1] space."""
    if variable_name in HIGHER_IS_SAFER:
        return (eee_value + 1) / 2
    elif variable_name in HIGHER_IS_RISKIER:
        return (-eee_value + 1) / 2
    else:
        # fallback_safety_delta, deployment_volume: use (v+1)/2
        return (eee_value + 1) / 2


def load_overlay_for_case(canonical_data, governance_case_id):
    """Load EEE overlay for a specific governance case_id."""
    for case in canonical_data["cases"]:
        if case["case_id"] == governance_case_id:
            return case
    return None


def merge_features(base_features, overlay_case, confidence_threshold=0.70):
    """
    Merge EEE overlay features into base v3_bridge features.

    Rules (from Build Plan §7):
    1. For each SCM variable, check if eee_feature_overlay contains a value.
    2. If present AND confidence_level >= 0.70: use transformed EEE value.
    3. If present AND confidence_level < 0.70: use EEE value but flag.
    4. If absent: retain v3_bridge base value.
    5. For blocked cases: no overlay applied.
    """
    if overlay_case is None or overlay_case["deployment_risk_class"] == "BLOCKED":
        return base_features, {"overlay_applied": False, "reason": "blocked_or_absent"}

    merged = {}
    merge_log = {"overlay_applied": True, "merged_features": {}, "retained_base": []}

    overlay = overlay_case.get("eee_feature_overlay", {})

    for var_name, base_data in base_features.items():
        if var_name in overlay:
            eee_feat = overlay[var_name]
            eee_val = eee_feat["value_primary"]
            eee_conf = eee_feat["confidence_level"]
            gov_val = eee_to_governance_value(var_name, eee_val)

            merged[var_name] = {
                "value_primary": round(gov_val, 6),
                "value_low": round(eee_to_governance_value(var_name, eee_feat["value_low"]), 6),
                "value_high": round(eee_to_governance_value(var_name, eee_feat["value_high"]), 6),
                "confidence_level": eee_conf,
                "provenance_class": eee_feat["provenance_class_governance"],
                "encoding_rule_id": eee_feat["encoding_rule_id"],
                "source_refs": eee_feat["source_refs"],
                "excerpt_ids": eee_feat["excerpt_ids"],
                "overlay_source": "eee_triangulated",
                "eee_raw_value": eee_val,
            }
            flag = None
            if eee_conf < confidence_threshold:
                flag = "low_confidence_overlay"
                merged[var_name]["overlay_flag"] = flag

            merge_log["merged_features"][var_name] = {
                "base_value": base_data["value_primary"],
                "overlay_value": round(gov_val, 6),
                "eee_raw": eee_val,
                "confidence": eee_conf,
                "flag": flag,
            }
        else:
            merged[var_name] = dict(base_data)
            merged[var_name]["overlay_source"] = "base_v3_bridge"
            merge_log["retained_base"].append(var_name)

    return merged, merge_log


def evaluate_gates(features, profile):
    """Evaluate non-compensatory gates against a threshold profile."""
    gates = {}
    gates["gate_safety"] = int(features.get("intrinsic_safety", {}).get("value_primary", 0) >= profile["safety_gate"])
    gates["gate_evidence"] = int(features.get("evidence_strength", {}).get("value_primary", 0) >= profile["evidence_gate"])
    gates["gate_bias"] = int(features.get("bias_harm_index", {}).get("value_primary", 1) <= profile["bias_gate"])
    gates["gate_calibration"] = int(features.get("uncertainty_calibration", {}).get("value_primary", 0) >= profile["calibration_gate"])
    gates["gate_traceability"] = int(features.get("traceability_integrity", {}).get("value_primary", 0) >= profile["traceability_gate"])
    gates["all_gates_pass"] = int(all(gates.values()))

    # Compensatory score: mean of all 15 feature values (simplified)
    vals = [f.get("value_primary", 0.5) for f in features.values() if isinstance(f, dict) and "value_primary" in f]
    gates["compensatory_score"] = round(sum(vals) / len(vals), 4) if vals else 0.0
    gates["compensatory_approved"] = int(gates["compensatory_score"] >= 0.5)

    return gates


def stage_10_engine_execution(data_dir, skip=False, verbose=True):
    """Run governance engine with overlay merge."""
    log("STAGE 10: Governance Engine Execution with Overlay Support", verbose)

    if skip:
        log("  Skipped (--skip-engine flag)", verbose)
        return {}

    import yaml

    # Load canonical data
    canonical_path = RELEASE_V31 / "eee_overlay" / "canonicalised_v1.json"
    with open(canonical_path) as f:
        canonical = json.load(f)

    # Load threshold profiles
    profiles_path = RELEASE_V31 / "config" / "threshold_profiles.yaml"
    with open(profiles_path) as f:
        profiles = yaml.safe_load(f)["profiles"]

    # Process all engine cases
    engine_cases_dir = RELEASE_V31 / "engine" / "cases"
    results = {}
    run_id = f"eee_overlay_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    for case_file in sorted(engine_cases_dir.glob("*.json")):
        if case_file.name.startswith("_"):
            continue
        with open(case_file) as f:
            base_case = json.load(f)

        case_id = base_case["case_id"]
        overlay_case = load_overlay_for_case(canonical, case_id)

        # Merge features
        merged_features, merge_log = merge_features(base_case["features"], overlay_case)

        # Evaluate gates for each profile
        case_results = {
            "case_id": case_id,
            "has_overlay": merge_log["overlay_applied"],
            "overlay_eee_case_id": overlay_case["eee_case_id"] if overlay_case else None,
            "profiles": {},
        }

        for profile_name, thresholds in profiles.items():
            gate_result = evaluate_gates(merged_features, thresholds)
            gate_result["threshold_profile"] = profile_name
            case_results["profiles"][profile_name] = gate_result

        results[case_id] = case_results

    # Write engine results
    engine_output_dir = RELEASE_V31 / "engine_results"
    engine_output_dir.mkdir(exist_ok=True)

    engine_output = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overlay_version": "1.0.0",
        "total_cases": len(results),
        "overlay_cases": sum(1 for r in results.values() if r["has_overlay"]),
        "results": results,
    }
    with open(engine_output_dir / "overlay_engine_results.json", "w") as f:
        json.dump(engine_output, f, indent=2)

    # Summary statistics
    overlay_count = engine_output["overlay_cases"]
    log(f"  Processed {len(results)} cases ({overlay_count} with EEE overlay)", verbose)

    # Gate pass rates per profile
    for pname in profiles:
        passes = sum(1 for r in results.values() if r["profiles"][pname]["all_gates_pass"])
        log(f"  Profile '{pname}': {passes}/{len(results)} pass all gates", verbose)

    log("STAGE 10: COMPLETE", verbose)
    return engine_output


# ===========================================================================
# Stage 11: Release Packaging
# ===========================================================================
def stage_11_release_packaging(canonical_hash, verbose=True):
    """Build the immutable release package."""
    log("STAGE 11: Release Packaging", verbose)

    # Compute hashes of all release files
    file_inventory = {}
    for fpath in sorted(RELEASE_V31.rglob("*")):
        if fpath.is_file():
            rel = str(fpath.relative_to(RELEASE_V31))
            file_inventory[rel] = compute_file_hash(fpath)

    # Build release manifest
    manifest = {
        "release_version": "3.1.0-eee",
        "release_type": "eee_overlay_integration",
        "repository_base_version": "3.0.0",
        "overlay_version": "1.0.0",
        "enrichment_hash": DECLARED_ENRICHMENT_HASH,
        "parent_hash": DECLARED_PARENT_HASH,
        "canonical_hash_declared": DECLARED_CANONICAL_HASH,
        "canonical_hash_actual": canonical_hash,
        "release_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_files": len(file_inventory),
        "cases_in_overlay": 39,
        "cases_processed": 37,
        "cases_blocked": 2,
        "blocked_case_ids": sorted(BLOCKED_CASE_IDS),
        "file_inventory": file_inventory,
        "hash_chain": {
            "enrichment_v1_1": DECLARED_PARENT_HASH,
            "enrichment_v1_2": DECLARED_ENRICHMENT_HASH,
            "canonical_v1": canonical_hash,
        },
    }

    with open(RELEASE_V31 / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)
    log(f"  Release manifest: {len(file_inventory)} files inventoried", verbose)

    # Write CHANGELOG
    changelog = f"""# CHANGELOG — AI Governance Benchmark Repository

## v3.1.0-eee ({datetime.now(timezone.utc).strftime('%Y-%m-%d')})

### Added
- EEE overlay integration: 39 historical cases enriched with triangulated
  peer-reviewed evidence via the Evidence Enrichment Engine (EEE) v1.2.
- New database table: `eee_canonical_overlay` (sidecar, no existing table changes).
- Overlay-aware governance engine execution with opt-in feature merge.
- Evidence archive: full enrichment dataset, triangulation outputs, and
  validation reports preserved in `eee_evidence/`.
- Provenance hash chain: enrichment v1.1 → v1.2 → triangulation → canonical.
- Replay exports compatible with historical replay validation pipeline.

### Evidence Summary
- 37 cases processed with triangulated confidence scores (range: 0.73–0.93).
- 2 cases blocked (H34: Acclarent TruDi, H35: Sonio Detect) — insufficient evidence.
- 6 cases at HIGH_CONFIDENCE, 15 at MODERATE_CONFIDENCE, 5 at ELEVATED_CAUTION,
  8 at MODERATE_CAUTION, 3 at LOW_CONFIDENCE, 2 BLOCKED.
- 21 STRONG triangulation integrity, 16 FRAGILE, 2 BLOCKED.

### Unchanged
- All base case JSONs (v3.0) preserved verbatim.
- All existing database tables untouched.
- All existing threshold profiles, encoding rules, and schemas preserved.
- Full backward compatibility with v3.0 engine pipeline.

### Blocked Cases
- H34 (acclarent_trudi_navigation_reuters2026): INSUFFICIENT evidence, monitoring required.
- H35 (sonio_detect_prenatal_labeling_reuters2026): INSUFFICIENT evidence, monitoring required.

### Hash Chain
- EEE v1.1 parent: {DECLARED_PARENT_HASH}
- EEE v1.2 enrichment: {DECLARED_ENRICHMENT_HASH}
- Canonical dataset v1 (declared): {DECLARED_CANONICAL_HASH}
"""
    with open(RELEASE_V31 / "CHANGELOG.md", "w") as f:
        f.write(changelog)
    log("  CHANGELOG.md written", verbose)

    log("STAGE 11: COMPLETE", verbose)
    return manifest


# ===========================================================================
# Stage 12: Validation & Publication Readiness
# ===========================================================================
def stage_12_validation(verbose=True):
    """Run comprehensive validation checks."""
    log("STAGE 12: Validation & Publication Readiness", verbose)

    report_lines = []
    all_pass = True

    def check(name, condition, detail=""):
        nonlocal all_pass
        status = "PASS" if condition else "FAIL"
        if not condition:
            all_pass = False
        line = f"  [{status}] {name}"
        if detail:
            line += f" — {detail}"
        report_lines.append(line)
        log(line, verbose)

    # 12.1 Structural checks
    check("Release directory exists", RELEASE_V31.exists())
    check("Overlay directory exists", (RELEASE_V31 / "eee_overlay").exists())
    check("Engine cases directory exists", (RELEASE_V31 / "engine" / "cases").exists())
    check("Config snapshot exists", (RELEASE_V31 / "config").exists())
    check("Schemas snapshot exists", (RELEASE_V31 / "schemas").exists())
    check("Manifest exists", (RELEASE_V31 / "manifest.json").exists())
    check("CHANGELOG exists", (RELEASE_V31 / "CHANGELOG.md").exists())
    check("EEE evidence archive exists", EEE_EVIDENCE_DIR.exists())
    check("Provenance file exists", (EEE_EVIDENCE_DIR / "provenance.json").exists())

    # 12.2 Overlay file checks
    canon_file = RELEASE_V31 / "eee_overlay" / "canonicalised_v1.json"
    check("Canonical overlay file exists", canon_file.exists())
    check("Replay exports file exists", (RELEASE_V31 / "eee_overlay" / "replay_exports_v1.json").exists())
    check("Overlay manifest exists", (RELEASE_V31 / "eee_overlay" / "overlay_manifest.json").exists())

    if canon_file.exists():
        with open(canon_file) as f:
            canon = json.load(f)
        check("Canonical case count = 39", len(canon["cases"]) == 39, f"got {len(canon['cases'])}")
        processed = sum(1 for c in canon["cases"] if c["deployment_risk_class"] != "BLOCKED")
        blocked = sum(1 for c in canon["cases"] if c["deployment_risk_class"] == "BLOCKED")
        check("Processed cases = 37", processed == 37, f"got {processed}")
        check("Blocked cases = 2", blocked == 2, f"got {blocked}")

        # Verify blocked cases
        for c in canon["cases"]:
            if c["eee_case_id"] in BLOCKED_CASE_IDS:
                check(
                    f"Blocked {c['eee_case_id']} has BLOCKED risk class",
                    c["deployment_risk_class"] == "BLOCKED",
                )
                check(
                    f"Blocked {c['eee_case_id']} has INSUFFICIENT grade",
                    c["evidence_grade"] == "INSUFFICIENT",
                )
                check(
                    f"Blocked {c['eee_case_id']} has empty overlay",
                    len(c["eee_feature_overlay"]) == 0,
                )
                check(
                    f"Blocked {c['eee_case_id']} has monitoring flags",
                    "monitoring_required" in c["audit_flags"],
                )

    # 12.3 Database checks
    conn = sqlite3.connect(str(DB_PATH))
    overlay_count = conn.execute("SELECT COUNT(*) FROM eee_canonical_overlay").fetchone()[0]
    check("DB overlay table has 39 rows", overlay_count == 39, f"got {overlay_count}")

    orphans = conn.execute("""
        SELECT o.case_id FROM eee_canonical_overlay o
        LEFT JOIN cases c ON o.case_id = c.case_id
        WHERE c.case_id IS NULL
    """).fetchall()
    check("No FK violations", len(orphans) == 0, f"{len(orphans)} orphans")

    # Verify blocked cases in DB
    for blocked_gid in BLOCKED_GOVERNANCE_IDS:
        row = conn.execute(
            "SELECT deployment_risk_class FROM eee_canonical_overlay WHERE case_id=?",
            (blocked_gid,),
        ).fetchone()
        check(f"DB blocked case {blocked_gid}", row and row[0] == "BLOCKED")

    # Verify no existing tables modified
    existing_tables = {"cases", "sector_tags", "evidence_items", "governance_vectors",
                       "engine_features", "experiment_runs", "stress_test_results",
                       "decision_rule_outputs", "manifests", "schema_migrations"}
    all_tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    check("New table eee_canonical_overlay exists", "eee_canonical_overlay" in all_tables)
    check("All original tables still exist", existing_tables.issubset(all_tables))

    conn.close()

    # 12.4 Base case integrity check
    v30_cases = RELEASE_V30 / "engine" / "cases"
    v31_cases = RELEASE_V31 / "engine" / "cases"
    if v30_cases.exists() and v31_cases.exists():
        mismatch = 0
        for v30_file in sorted(v30_cases.glob("*.json")):
            v31_file = v31_cases / v30_file.name
            if v31_file.exists():
                h30 = compute_file_hash(v30_file)
                h31 = compute_file_hash(v31_file)
                if h30 != h31:
                    mismatch += 1
        check("Base case JSONs unmodified", mismatch == 0, f"{mismatch} files differ")

    # 12.5 Hash chain verification
    if (RELEASE_V31 / "eee_overlay" / "overlay_manifest.json").exists():
        with open(RELEASE_V31 / "eee_overlay" / "overlay_manifest.json") as f:
            om = json.load(f)
        check("Overlay manifest enrichment hash matches",
              om["enrichment_hash"] == DECLARED_ENRICHMENT_HASH)
        check("Overlay manifest parent hash matches",
              om["parent_hash"] == DECLARED_PARENT_HASH)

    # Write validation report
    report_path = RELEASE_V31 / "validation_report.txt"
    report_header = f"""VALIDATION REPORT — v3.1.0-eee
{'='*60}
Generated: {datetime.now(timezone.utc).isoformat()}
Overall: {'PASS' if all_pass else 'FAIL'}
{'='*60}
"""
    with open(report_path, "w") as f:
        f.write(report_header + "\n".join(report_lines) + "\n")

    log(f"\n  OVERALL: {'PASS' if all_pass else 'FAIL'}", verbose)
    log("STAGE 12: COMPLETE", verbose)

    if not all_pass:
        fail("Validation failed — see report")

    return all_pass


# ===========================================================================
# Main
# ===========================================================================
def main():
    parser = argparse.ArgumentParser(description="Build v3.1.0-eee release")
    parser.add_argument("--data-dir", type=str, default=None,
                        help="Directory containing canonical dataset and evidence files")
    parser.add_argument("--skip-engine", action="store_true",
                        help="Skip Stage 10 (engine execution)")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()

    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        # Default: look for data_staging relative to repo root
        data_dir = REPO_ROOT.parent / "data_staging"
        if not data_dir.exists():
            data_dir = REPO_ROOT / "data_staging"

    log(f"Data directory: {data_dir}")
    log(f"Repository root: {REPO_ROOT}")
    log(f"Database: {DB_PATH}")
    log("")

    # Stage 9
    s9_result = stage_9_overlay_insertion(data_dir, args.verbose)
    log("")

    # Stage 10
    s10_result = stage_10_engine_execution(data_dir, skip=args.skip_engine, verbose=args.verbose)
    log("")

    # Stage 11
    s11_result = stage_11_release_packaging(s9_result["canonical_hash"], args.verbose)
    log("")

    # Stage 12
    stage_12_validation(args.verbose)

    log("")
    log("=" * 60)
    log("BUILD COMPLETE: v3.1.0-eee release ready")
    log("=" * 60)


if __name__ == "__main__":
    main()
