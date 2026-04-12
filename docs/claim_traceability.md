# Claim Traceability Matrix (P4)

**Repo:** ethical-alpha-audit-paper-4-historical-replay  
**Source manuscript:** `inputs/manuscript.docx` (plain-text extraction used for claim identification)  
**Supplementary:** `inputs/supplementary.pdf`, `inputs/supplementary.docx`  
**Updated:** 2026-04-12 (engineer remediation pass; QA session 2026-04-12)  
**CLAIM EXTRACTION COMPLETE: 40 claims identified for P4** (P4-C01–P4-C40)

This matrix maps manuscript claims to executable artefacts. Status values are descriptive; formal verification is via `python reproduce_all.py` and structural tests under `tests/`. **`VERIFIED (QA 2026-04-12)`** indicates a claim checked against outputs produced in that independent QA run (pytest + `reproduce_all.py` + fresh notebook execution).

| Claim ID | Claim (paraphrase) | Code | Notebook | Output / path | Status |
|----------|-------------------|------|----------|---------------|--------|
| P4-C01 | Institutional frameworks (NIST AI RMF, EU AI Act, ISO/IEC 23894) guide process but do not operationalise deterministic threshold gate logic. | N/A (background) | 01 (narrative) | — | narrative |
| P4-C02 | Historical replay applies a **pre-specified** five-gate non-compensatory engine; engine not modified for this analysis. | `engine/corrected_public_engine_v1_1.py` | 02 | `outputs/logs/replay_run_log.txt` | implemented |
| P4-C03 | **12** documented failure cases (2014–2021), seven sectors, **convenience** sample from strong documentary evidence. | `data/canonical/canonical_dataset.json` | 01 | `outputs/tables/dataset_inventory.csv` | implemented |
| P4-C04 | **64** independent documentary sources; **15** SCM features per case; rubric-based encoding with provenance classes. | canonical + EEE overlay | 01 | `outputs/tables/dataset_inventory.csv` | implemented |
| P4-C05 | Triangulation yields **57** triangulated and **123** passthrough features; timing: **4** pre-deployment vs **60** post-incident sources. | EEE / provenance JSON | 01 | notebook stdout / inventory | implemented |
| P4-C06 | **20** declared feature-dependency overlaps (consistent with dependency matrix). | provenance artefacts | 01 | `docs/provenance.md` | documented |
| P4-C07 | Five non-compensatory gates + four threshold profiles + parallel compensatory comparator. | `corrected_public_engine_v1_1.py` | 02–04 | `outputs/tables/replay_results.csv` | implemented |
| P4-C08 | **Eight** core-equivalent failures upgraded via EEE overlay (v1.2.0): **16** features upgraded, **8** imputations removed, **16** confidence uplifts; two cases LOW→MODERATE. | `engine/eee_overlay_adapter.py`, overlay JSON | 01–02 | `config/core_equivalent_cases.json` | implemented |
| P4-C09 | **12** FDA-cleared control devices for specificity (Extended Data 5). | benchmark cases | 02 | `outputs/tables/replay_results.csv` (layer rows) | implemented |
| P4-C10 | Manuscript headline **12 failures + 12 controls** under moderate: **TP=11, FN=1, TN=12, FP=0**; sensitivity **0.917**, specificity **1.000**. **Repo:** Layer 1 (12 failures) matches **11/12** rejections and sole approve **google_dr**; **12** FDA controls **all approve** in notebook Layer 2 block. **`confusion_matrix.csv` encodes Layer 2 only (20 failures + 12 controls): TP=20, FN=0, TN=12, FP=0** — not the 12+12 headline matrix. | engine | 02 | `notebooks/02_historical_replay_execution.ipynb` (§2.2, §2.6); `outputs/tables/confusion_matrix.csv` (Layer 2) | implemented; **VERIFIED (QA 2026-04-12)** — layer split / artefact scope |
| P4-C11 | Sole **false negative**: **google_dr** (narrow margins; safety margin **0.05**). | engine | 02–03 | `notebooks/02_historical_replay_execution.ipynb` (assertions + stdout) | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C12 | **Safety gate** binding most often: **10/12 (83%)** failures under moderate. | engine | 02, 04 | `outputs/figures/figure1_gate_failure.png`; notebook 02 stdout | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C13 | **Bias** gate **6/12**; **calibration** and **traceability** each **5/12**; **evidence** gate **3/12**. | engine | 04 | `figure1_gate_failure.png`; notebook 02 stdout | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C14 | Rejected cases average **2.6** gate failures each (**29** total across **11** rejections). | engine | 03–04 | notebook 02 stdout (mean **2.636**, total **29**) | implemented; **VERIFIED (QA 2026-04-12)** (mean rounded in manuscript) |
| P4-C15 | **Ablation:** removing **any single** gate does **not** flip a rejection to approval (12 cases). | engine | 04 | `figure2_ablation.png`, `ablation_matrix.csv` | implemented |
| P4-C16 | **Pairwise** ablation: **safety+bias** flips Optum, Gender Shades, UK A-levels; **safety+calibration** flips Google Flu & Uber AV; **evidence+traceability** flips Babylon. | engine | 04 | `figure2_ablation.png` | implemented |
| P4-C17 | Non-compensatory vs compensatory **agree on 10/12**; **two** divergences (**google_flu**, **uber_av**) where compensatory would approve. | engine | 02–04 | `figure4_compensation.png`; notebook 02 stdout / assertions | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C18 | Compensatory scores at divergence: Google Flu **~0.57** (threshold **0.50**); Uber AV **~0.51** (threshold **0.50**). | engine | 02 | notebook 02 stdout (**0.5675**, **0.5125**) | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C19 | Provenance mix across **180** encodings: **27.2%** direct, **37.8%** rule-derived, **28.3%** imputed, **6.7%** uncertain; **mean confidence 0.591**. | canonical features | 01, 04 | `figure3_provenance_stability.png` | implemented |
| P4-C20 | Monte Carlo on **[low, high]** bands: **200** iterations, seed **42** → **12/12** outcome-stable under moderate. | engine | 03 | `outputs/figures/calibration_summary.txt`; `outputs/tables/metrics_summary.csv` | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C21 | **±0.20** sensitivity: only **google_dr** shows flip points (**8** across **4** features); **11** rejections robust. | engine | 03 | `metrics_summary.csv`; `calibration_summary.txt` | implemented; **partially verified (QA 2026-04-12)** — flip-point count **7** in `calibration_summary.txt` / metrics vs manuscript **8** |
| P4-C22 | Expanded benchmark **91** cases (**61** failures, **30** controls): **100%** sensitivity & specificity; **no** misclassifications under moderate. | benchmark dir + engine | 02 | `replay_results.csv`; `outputs/logs/replay_run_log.txt` | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C23 | Tier 2 (**49** cases): lower mean confidence (**~0.383**), **4.0** mean gate failures, safety binding **100%**. | benchmark metadata | 01–02 | dataset inventory / replay | implemented |
| P4-C24 | Tier 3 (**30** FDA-authorised devices): all **APPROVE** under moderate (specificity controls). | benchmark | 02 | replay_results expanded rows | implemented |
| P4-C25 | Perfect separation on expanded set is a **structural** consequence of encoding + non-compensatory logic, **not** prospective validation. | N/A (interpretive) | 02 (markdown) | — | narrative |
| P4-C26 | **Dual dataset** structural invariance: normalised public schema vs canonical → **480/480** field comparisons identical (12×4×10). | engine | 03 | `outputs/tables/metrics_summary.csv` (`invariance,fields_matched,480`) | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C27 | **Replay vs canonical full** mode: under **moderate**, **zero** verdict change on **12** cases. | engine modes | 03 | `metrics_summary.csv` (`mode_sensitivity,moderate_divergences,0`) | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C28 | Controlled **±0.05** perturbation on calibration/bias/traceability: **46/48** verdict-stable in replay; **2** flips **permissive only** (Epic Sepsis, Babylon). | `data/canonical/perturbation_dataset.json` | 03 | `metrics_summary.csv` (`perturbation,verdicts_stable,46`; `verdict_flips,2`) | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C29 | **Moderate** profile: **zero** verdict flips under that perturbation regime; compensatory Uber AV can flip near **0.50**. | engine | 03 | `metrics_summary.csv` (`moderate_flips,0`); Uber AV score in notebook 02 | implemented; **VERIFIED (QA 2026-04-12)** (compensatory clause via 02) |
| P4-C30 | Three primary discriminative gates under expanded + core scopes: **G1, G4, G5** (manuscript framing). | engine | 02–04 | gate failure charts | implemented |
| P4-C31 | Contribution: reproducible deterministic pipeline, historical replay methodology, empirical defence-in-depth via redundant gates. | N/A | all notebooks | `reproduce_all.py` | process |
| P4-C32 | Limitations: convenience sample, tiered provenance heterogeneity, selection/survivorship bias, not representative of all deployments. | N/A | 01–02 text | — | narrative |
| P4-C33 | Ethics: retrospective computational study on public cases; no human subjects; no ethics approval required. | N/A | — | manuscript only | narrative |
| P4-C34 | Data/code availability: Zenodo DOI placeholder; GitHub URLs cited (external). | N/A | `repro_manifest.json` | inputs/ | external |
| P4-C35 | AI disclosure: Claude used for code/docs assistance; author retains scientific decisions. | N/A | — | manuscript only | narrative |
| P4-C36 | Figure 1: gate failure counts (**83%** safety, **50%** bias, **42%** cal/trace, **25%** evidence). | engine | 04 | `outputs/figures/figure1_gate_failure.png`; notebook 02 gate stdout | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C37 | Figure 2: single-gate removal stable; pairwise removals as specified. | engine | 04 | `outputs/figures/figure2_ablation.png`; `outputs/tables/ablation_matrix.csv` | implemented; **VERIFIED (QA 2026-04-12)** (artefacts present + pipeline PASS) |
| P4-C38 | Figure 3: provenance distribution + MC stability + ±0.20 sensitivity summary. | notebooks | 04 | `outputs/figures/figure3_provenance_stability.png` | implemented; **VERIFIED (QA 2026-04-12)** (figure + validation PASS) |
| P4-C39 | Figure 4: compensation effect highlighting **google_flu** and **uber_av**. | engine | 04 | `outputs/figures/figure4_compensation.png` | implemented; **VERIFIED (QA 2026-04-12)** |
| P4-C40 | PhysioNet / extended analyses referenced as **Extended Data** (not re-proven in-repo here). | external | 03 (refs) | `docs/provenance.md` | out-of-notebook scope |

## Validation commands

```text
python -m pytest tests/ -q
python reproduce_all.py
```

## Escalations / notes

- **QA 2026-04-12 (independent):** `pytest` 8 passed; `reproduce_all.py` ALL STEPS PASSED (notebooks 01–04, manifest, `validate_outputs.py`, HTML export). **P4-C10:** prior traceability pointed `confusion_matrix.csv` at the 12+12 headline; file is **Layer 2 (20+12)** — row above corrected. **P4-C21:** manuscript **8** flip points vs `calibration_summary.txt` / metrics **7** — reconcile manuscript or code (non-blocking unless that number is contractual).
- **Working tree:** after `reproduce_all.py`, expect modified notebooks, `logs/actual_manifest.json`, and `docs/html/*.html`; commit or reset per release policy. `inputs/supplementary.pdf` must remain tracked for attachment compliance.
- **system_snapshot.json:** portfolio snapshot lists P4 `commit: null`; update after P4 hardening commit is registered upstream.
- **Shared-core:** no pip lockfile; see `config/shared_core_reference.json` for portfolio commit reference. Engine code is **vendored** under `engine/`.
