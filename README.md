# Historical Replay Evaluation of Non-Compensatory AI Governance
[![DOI](https://zenodo.org/badge/1194631776.svg)](https://doi.org/10.5281/zenodo.19388208)

> **Paper 4** of the Ethical Alpha Audit five-paper bundle
>
> Author: Walter Brown — Ethical Alpha Audit Ltd
> ORCID: [0000-0002-6050-8522](https://orcid.org/0000-0002-6050-8522)

## Reviewer quick validation (no execution required)

```bash
python scripts/validate_outputs.py
```

**Expected result:** `VALIDATION PASSED`

This checks every output file against its pinned SHA-256 digest. No notebook execution, no dependencies beyond Python stdlib. A passing result confirms the checked-in outputs are byte-identical to those produced by the deterministic pipeline.

**To re-execute the full pipeline** (requires dependencies):

```bash
pip install -r requirements.txt
python reproduce_all.py
```

## What this repository reproduces

This repository contains the complete computational pipeline for the Paper 4 manuscript. It reproduces all quantitative findings from three analytical layers:

| Layer | Cases | Key Result |
|-------|-------|------------|
| Primary (12-case) | 12 expert-triangulated failure cases | 11/12 rejected (91.7% sensitivity) |
| Confusion matrix | 20 failures + 12 controls | TP=20, FN=0, TN=12, FP=0 |
| Expanded benchmark | 61 failures + 30 controls | 60/61 rejected, 30/30 approved |

Additionally: Monte Carlo stability (12/12 stable, 200 iterations), perturbation robustness (46/48 stable), gate ablation analysis (0 single-gate changes, 3 critical pairwise combinations), and four publication-grade figures.

## Repository structure

```
engine/             Governance engine (stdlib-only, unmodified)
data/canonical/     12-case expert dataset + normalised + perturbation variants
data/benchmark/     91-case expanded benchmark + EEE overlay
notebooks/          4 Jupyter notebooks (narrative-first, code-collapsed in HTML)
scripts/            Execution harness (notebook runner, hash validator, HTML export)
config/             Determinism settings, expected outputs, trace map
outputs/            Generated tables, figures, and logs (hash-locked)
docs/html/          Static HTML exports for reading without code
```

## Notebooks

| # | Notebook | Purpose | Key assertions |
|---|----------|---------|---------------|
| 01 | Dataset Intake | Load data, validate provenance | 180 encodings, 49/68/51/12 provenance |
| 02 | Historical Replay | Execute governance engine across all layers | 11/12, TP=20, 60/61 |
| 03 | Metrics & Calibration | Stability, perturbation, invariance | 12/12 MC, 46/48 perturb, 480/480 |
| 04 | Figures & Tables | Generate manuscript figures + ablation | F1–F4, A1–A4 |

For code-free reading, see `docs/html/`.

## Interactive browsing
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ethical-alpha-audit/ethical-alpha-audit-paper-4-historical-replay.git/HEAD)

## Known annotations

- **N7**: Mean gate failures per rejection: engine computes 2.636 (29/11); manuscript reports 2.5
- **N14**: Google DR sensitivity: engine finds 7 flip points at ±0.20; manuscript reports 8 (floating-point boundary case at evidence_strength threshold)

Neither annotation affects any governance decision or figure.

## Citation

See `CITATION.cff` for machine-readable citation metadata.

## Licence

MIT — see `LICENSE`.
