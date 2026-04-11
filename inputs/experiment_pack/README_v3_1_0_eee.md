# Operator Guide — v3.1.0-eee Build

## Overview

This release integrates the Evidence Enrichment Engine (EEE) v1.2 triangulated
evidence overlay into the AI Governance Benchmark Repository v3.0 as a sidecar.
It implements pipeline Stages 9–12 as defined in the Claude Enriched AI Governance
Build Plan v1.

## Prerequisites

- Python 3.10+ with `pyyaml` installed
- The governance repository v3 (this directory)
- Data files in `data_staging/` (or specify with `--data-dir`):
  - `canonicalised_dataset_v1.json` (required)
  - `replay_exports_v1.json` (required)
  - `EEE_v1_2_enriched_dataset_UPGRADED.json` (for evidence archive)
  - `EEE_v1_2_triangulation_run_output.json` (for evidence archive)
  - `EEE_v1_2_case_confidence_summary.csv` (for evidence archive)
  - `canonicalisation_mapping_table.csv` (for evidence archive)

## Running the Build

```bash
# Full build (recommended)
python run_v3_1_0_eee_build.py --data-dir ../data_staging

# Skip engine execution (overlay insertion + packaging only)
python run_v3_1_0_eee_build.py --data-dir ../data_staging --skip-engine
```

## What the Build Does

### Stage 9: Repository Overlay Insertion
1. Creates `benchmark_repository/releases/v3.1.0-eee/` with:
   - `eee_overlay/` — canonical sidecar + replay exports + manifest
   - `engine/cases/` — verbatim copy of v3.0 base cases
   - `config/` — frozen config snapshot
   - `schemas/` — frozen schema snapshot
2. Creates `benchmark_repository/eee_evidence/` archive
3. Extends `governance.db` with `eee_canonical_overlay` table (39 rows)

### Stage 10: Governance Engine Execution
- Loads base v3_bridge features for all 91 cases
- Merges EEE overlay where available (39 of 91 cases)
- Transforms EEE [-1,1] values to governance [0,1] space
- Evaluates non-compensatory gates across all threshold profiles
- Writes results to `engine_results/overlay_engine_results.json`

### Stage 11: Release Packaging
- Computes SHA-256 hashes for all release files
- Writes `manifest.json` with full file inventory
- Writes `CHANGELOG.md`

### Stage 12: Validation
- Verifies 39 canonical cases inserted
- Verifies 2 blocked cases preserved (H34, H35)
- Verifies 0 FK violations
- Verifies base case JSONs unmodified
- Verifies hash chain consistency
- Writes `validation_report.txt`

## Deterministic Re-run

To verify reproducibility:

```bash
# Clean release (preserves base repo)
rm -rf benchmark_repository/releases/v3.1.0-eee
rm -rf benchmark_repository/eee_evidence

# Re-run
python run_v3_1_0_eee_build.py --data-dir ../data_staging
```

The build is deterministic given identical input data files. The only non-deterministic
elements are timestamps in `inserted_at`, `generated_timestamp`, and `release_timestamp`.

## Database Queries

```sql
-- Get overlay for a specific case
SELECT * FROM eee_canonical_overlay WHERE case_id = 'epic_sepsis';

-- All HIGH_CONFIDENCE cases
SELECT case_id, eee_case_id, triangulated_confidence
FROM eee_canonical_overlay
WHERE deployment_risk_class = 'HIGH_CONFIDENCE';

-- Cases with fragile triangulation
SELECT case_id, eee_case_id
FROM eee_canonical_overlay
WHERE audit_flags_json LIKE '%fragile_triangulation%';

-- Join with base case info
SELECT c.case_id, c.title, o.triangulated_confidence,
       o.deployment_risk_class, o.evidence_grade
FROM cases c
JOIN eee_canonical_overlay o ON c.case_id = o.case_id
ORDER BY o.triangulated_confidence DESC;
```

## Using the Overlay Merge in Code

```python
from src.eee_overlay.overlay_merge import OverlayMerger

merger = OverlayMerger("benchmark_repository/releases/v3.1.0-eee/eee_overlay/canonicalised_v1.json")

# Merge for a specific case
merged, log = merger.merge("epic_sepsis", base_case["features"])
```

## Hash Chain

```
EEE v1.1 (parent): b77e10eccb2dde7f...
    └── EEE v1.2 (current): f9d181ca3859cb7e...
        └── Triangulation run: derived from f9d181ca...
            └── Canonical dataset: c3ed7b93d68a0a89... (declared)
                └── Release manifest: computed at build time
```

## Hard Fail Conditions

The build will abort if:
- Base case JSONs are modified
- Existing DB tables are altered
- H34/H35 receive overlay feature values
- FK violations exist
- Required data files are missing
