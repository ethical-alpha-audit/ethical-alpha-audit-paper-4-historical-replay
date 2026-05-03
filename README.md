# Historical Replay Evaluation of Non-Compensatory AI Governance
[![DOI](https://zenodo.org/badge/1194631776.svg)](https://doi.org/10.5281/zenodo.19388835)

> **Paper 4** of the Ethical Alpha Audit five-paper bundle
>
> Author: Walter Brown — Ethical Alpha Audit Ltd
> ORCID: [0000-0002-6050-8522](https://orcid.org/0000-0002-6050-8522)

## Reviewer quick validation (no execution required)

```bash
python scripts/validate_outputs.py
```

**Expected result:** `VALIDATION PASSED`

This checks every output file against its pinned SHA-256 digest. No notebook execution, no
dependencies beyond Python stdlib. A passing result confirms the checked-in numerical artefacts
(CSVs, log, and calibration summary) are byte-identical to those produced by the deterministic
pipeline. Figure PNGs are visually equivalent across matplotlib versions but are not guaranteed
byte-identical (matplotlib does not provide bit-stable raster output across micro-versions).

**To re-execute the full pipeline** (requires dependencies):

```bash
pip install -r requirements.txt
python reproduce_all.py
```

The repository carries three dependency files: `requirements.txt` pins direct dependencies (8 entries, exact-version); `environment.lock` documents the validated runtime environment including Python and notebook server versions; `requirements.lock.txt` is a full `pip freeze` of the validated environment (transitive closure, 99 entries) and is provided for environments that require reproducing the complete dependency graph.

## What this repository reproduces

This repository contains the complete computational pipeline for the Paper 4 manuscript. It
reproduces all quantitative findings from three analytical layers:

| Layer | Cohort | Artefact | Manuscript metric |
|-------|--------|----------|-------------------|
| Primary 12-case | 12 expert-triangulated failures + 12 FDA-cleared controls | `outputs/tables/confusion_matrix_primary.csv` | TP=11, FN=1, TN=12, FP=0 (sensitivity 0.917, specificity 1.000) |
| Core-extended  | 12 core + 8 core-equivalent failures + 12 controls       | `outputs/tables/confusion_matrix.csv`         | TP=20, FN=0, TN=12, FP=0 (sensitivity 1.000, specificity 1.000) |
| Expanded benchmark | 61 failures + 30 controls across 3 provenance tiers   | `outputs/tables/replay_results.csv` (filter `layer=expanded`) | sensitivity 0.984 (60/61), specificity 1.000 (30/30) |

Both confusion matrices are reported in the manuscript Results section. The primary 12+12 metric
remains the authoritative primary metric; the core-extended metric is reported under the same
structural-expectation framing as the expanded benchmark. The primary 12-control cohort is
recorded deterministically in `config/primary_control_cohort.json` (7 De Novo + 4 510(k) + 1 PMA).

Additionally: Monte Carlo stability (12/12 stable, 200 iterations), perturbation robustness
(46/48 case-profile pairs stable at ±0.05; 239/240 single-feature evaluations stable at ±0.10
in experiment A01 — see `inputs/experiment_pack/`), gate ablation (0 single-gate changes;
3 critical pairwise combinations), and four publication-grade figures.

## Repository structure

```
engine/                    Governance engine (stdlib-only, unmodified)
data/canonical/            12-case expert dataset + normalised + perturbation variants
data/benchmark/            91-case expanded benchmark + EEE overlay
notebooks/                 4 Jupyter notebooks (narrative-first, code-collapsed in HTML)
scripts/                   Execution harness (notebook runner, hash validator, HTML export,
                           primary-control cohort builder)
config/                    Determinism settings, expected outputs, trace map,
                           primary_control_cohort
outputs/                   Generated tables, figures, and logs (hash-locked numerical artefacts)
inputs/experiment_pack/    Auxiliary experiments A01 (perturbation), A03 (provenance tier),
                           A04 (conservative bound). Outputs are hash-locked separately.
docs/html/                 Static HTML exports for reading without code
```

## Notebooks

| # | Notebook | Purpose | Key assertions |
|---|----------|---------|----------------|
| 01 | Dataset Intake | Load data, validate provenance | 180 encodings, 49/68/51/12 provenance |
| 02 | Historical Replay | Execute governance engine across all layers | 11/12 (primary), 20/20 (core-extended), 60/61 (expanded) |
| 03 | Metrics & Calibration | Stability, perturbation, invariance | 12/12 MC, 46/48 perturb (±0.05), 480/480 |
| 04 | Figures & Tables | Generate manuscript figures + ablation | F1–F4, A1–A4 |

For code-free reading, see `docs/html/`.

## Interactive browsing
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ethical-alpha-audit/ethical-alpha-audit-paper-4-historical-replay.git/HEAD)

## Citation

See `CITATION.cff` for machine-readable citation metadata.

## Licence

MIT — see `LICENSE`.
