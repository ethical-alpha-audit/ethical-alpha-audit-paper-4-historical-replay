# Paper 4 — Claim traceability (historical replay)

This register maps manuscript statements in `inputs/manuscript.docx` (and overlapping supplementary context in `inputs/supplementary.pdf`) to computational artefacts in this repository. It supports RTM-style audit without altering locked engine logic.

**CLAIM EXTRACTION COMPLETE: 58 claims identified for P4.**

## Traceability legend

| Column | Meaning |
| --- | --- |
| **ID** | Stable claim handle for cross-repo references (`P4-Cxx`). |
| **Artefacts** | Notebooks, tables, figures, datasets, or config entries that materially support the claim. |
| **Status** | `verified` = asserted directly in executed notebook checks or pinned outputs; `contextual` = narrative framing or citation-backed; `external` = depends on cited literature or out-of-repo archives. |

## Claim register

| ID | Claim summary | Manuscript anchor | Primary artefacts | Status |
| --- | --- | --- | --- | --- |
| P4-C01 | Institutional frameworks (NIST AI RMF, EU AI Act, ISO/IEC 23894) provide procedural guidance but not deterministic threshold gate logic (“operationalisation gap”). | Abstract; Introduction | Narrative | contextual |
| P4-C02 | Whether conjunctive (non-compensatory) minimum thresholds would have flagged documented deployment failures is an open empirical question addressed here. | Abstract; Introduction | `notebooks/02_historical_replay_execution.ipynb` | contextual |
| P4-C03 | The evaluation system comprises a five-gate engine, structured encoding with provenance, and deterministic benchmark infrastructure with hash validation. | Abstract; Methods | `engine/corrected_public_engine_v1_1.py`, `scripts/validate_outputs.py`, `config/expected_outputs.json` | verified |
| P4-C04 | Twelve documented governance failures (multi-sector) were encoded from structured evidence. | Abstract; Methods | `data/canonical/canonical_dataset.json`, `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C05 | Evidence was drawn from 64 independent documentary objects across the 12 cases. | Methods | `data/canonical/canonical_dataset.json` (source graph) | verified |
| P4-C06 | Feature vectors use a transparent numeric rubric with confidence-weighted provenance classes. | Methods | `notebooks/01_dataset_intake.ipynb`, `outputs/tables/dataset_inventory.csv` | verified |
| P4-C07 | Parallel analyses include ablation, Monte Carlo perturbation within confidence bounds, and compensatory scoring comparison. | Abstract; Methods | `notebooks/02_historical_replay_execution.ipynb`, `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C08 | An expanded provenance-tiered benchmark (91 cases) assesses scale generalisability. | Abstract; Methods | `data/benchmark/cases/*.json`, `notebooks/02_historical_replay_execution.ipynb` | verified |
| P4-C09 | Under the **moderate** profile, the framework rejected **11/12** failures (retrospective sensitivity **91.7%** in this sample). | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` (Q1), `outputs/tables/replay_results.csv` | verified |
| P4-C10 | The **safety** gate was the most frequently binding constraint (**10/12**, **83%**) under moderate replay. | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` (Q2), Figure 1 | verified |
| P4-C11 | Every rejected case failed **≥2** independent gates; mean gate failures per rejection **≈2.6**. | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` (Q8, mean print) | verified |
| P4-C12 | **Google Flu** and **Uber AV** are rejected by non-compensatory gates but would be approved under compensatory scoring (masking critical deficiencies). | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` (Q10–Q13), Figure 4 | verified |
| P4-C13 | Monte Carlo sampling within documented confidence bounds (**200** iterations, seed **42**) yields **12/12** stable moderate-profile outcomes. | Abstract; Results | `notebooks/03_metrics_and_calibration.ipynb` (Q29), `p4_replay/run_config.py` | verified |
| P4-C14 | Expanded benchmark: **61/61** failures rejected and **30/30** controls approved under tiered routing reported in the notebook harness. | Abstract; Conclusions | `notebooks/02_historical_replay_execution.ipynb` (Q34–Q35) | verified |
| P4-C15 | Provenance tiers make evidential weight explicit (Tier 1 core vs Tier 2 bulk failures vs Tier 3 controls). | Results | `notebooks/02_historical_replay_execution.ipynb`, `outputs/tables/replay_results.csv` | verified |
| P4-C16 | Core confusion matrix vs **12** FDA-encoded controls: **TP=11, FN=1, TN=12, FP=0**; sensitivity **0.917**, specificity **1.000** (structured retrospective framing). | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` (Q1), `outputs/tables/replay_results.csv` | verified |
| P4-C17 | Expanded **91-case** confusion: **TP=61, FN=0, TN=30, FP=0**; sensitivity/specificity **1.000** under the stated tiered encoding policy. | Abstract; Results | `notebooks/02_historical_replay_execution.ipynb` | verified |
| P4-C18 | Tier mean confidences reported in text (**Tier 1 ≈0.591; Tier 2 ≈0.383; Tier 3 ≈0.380**) encode an explicit quality gradient. | Results | `notebooks/01_dataset_intake.ipynb`, benchmark metadata | verified |
| P4-C19 | The **canonical 11/12** result remains the authoritative primary metric; expanded results provide scale evidence at lower confidence. | Conclusions | `notebooks/02_historical_replay_execution.ipynb`, `repro_manifest.json` | contextual |
| P4-C20 | Findings are **not** prospective real-world validation. | Abstract; Discussion | Narrative | contextual |
| P4-C21 | “Perfect separation” under expanded conditions is a **structural** consequence of the architecture applied to encoded cohorts, not a generalised safety claim for all devices. | Results; Discussion | Narrative + `notebooks/02_historical_replay_execution.ipynb` | contextual |
| P4-C22 | Case selection spans **2014–2021** convenience sample of well-documented failures (not population representative). | Methods | `data/canonical/canonical_dataset.json` | contextual |
| P4-C23 | Five healthcare failures plus seven cross-sector cases test domain generality of multi-gate deficiency patterns. | Methods | Case list in `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C24 | Triangulation yields **57** triangulated features and **123** passthrough features (single-source) as reported. | Methods | `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C25 | Evidence timing split (**pre-deployment vs post-incident** counts) supports deployment-time vs forensic framing. | Methods | `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C26 | Dependency audit flags **20** declared overlaps consistent with the engine dependency matrix. | Methods | `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C27 | Provenance class mix across **180** encodings: **27.2% / 37.8% / 28.3% / 6.7%** direct/rule-derived/imputed/uncertain. | Results | `notebooks/01_dataset_intake.ipynb`, Figure 3 | verified |
| P4-C28 | Mean encoding confidence **0.591** (median **0.600**) across the **180** encodings. | Results | `notebooks/01_dataset_intake.ipynb`, `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C29 | Four threshold profiles evaluated: permissive, moderate, strict, very strict. | Methods | `p4_replay/datasets.py` (`STANDARD_PROFILES`), notebooks | verified |
| P4-C30 | Permissive profile rejects **8/12**; strict and very strict reject **12/12** under replay mode. | Results | `notebooks/02_historical_replay_execution.ipynb` (Q18–Q20) | verified |
| P4-C31 | **Google DR** is the sole moderate-profile approval; safety margin **0.05** vs **0.50** threshold. | Results | `notebooks/02_historical_replay_execution.ipynb` (Q9) | verified |
| P4-C32 | Gate failure incidence: bias **6/12**, calibration **5/12**, traceability **5/12**, evidence **3/12** (moderate, full cohort statistics as printed). | Results | `notebooks/02_historical_replay_execution.ipynb` (Q3–Q6) | verified |
| P4-C33 | Layer-2 core-equivalent confusion matrix: **TP=20, FN=0, TN=12, FP=0** using **20** failures (12+8) with EEE overlay routing. | Results | `notebooks/02_historical_replay_execution.ipynb` (Q15–Q17) | verified |
| P4-C34 | Non-compensatory vs compensatory agreement on **10/12** cases with **2** structured divergences. | Results | `notebooks/02_historical_replay_execution.ipynb` (Q11) | verified |
| P4-C35 | Compensatory scores at divergence: Google Flu **≈0.5675**, Uber AV **≈0.5125** (engine-reported). | Results | `notebooks/02_historical_replay_execution.ipynb` (Q12–Q13) | verified |
| P4-C36 | Ablation: **no** single-gate removal flips any outcome; pairwise removals flip specific subsets (safety+bias; safety+calibration; evidence+traceability). | Results | `outputs/tables/ablation_matrix.csv`, Figure 2, `notebooks/04_figures_and_tables.ipynb` | verified |
| P4-C37 | Dual-dataset structural invariance: normalised public schema variant yields **480/480** identical comparisons across profiles/modes as asserted. | Results | `notebooks/03_metrics_and_calibration.ipynb`, `data/canonical/public_normalised_dataset.json` | verified |
| P4-C38 | Replay vs canonical full mode: **moderate** outcomes invariant for all **12**; **permissive** shows documented abstention-related flips for three cases in full mode. | Results | `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C39 | Perturbation protocol: **±0.05** on **UC/BHI/TI** with safety/evidence held fixed; **46/48** configurations verdict-stable in evaluated sweep. | Results | `notebooks/03_metrics_and_calibration.ipynb`, `data/canonical/perturbation_dataset.json` | verified |
| P4-C40 | Permissive-only perturbation verdict flips (**Epic Sepsis**, **Babylon**) match manuscript narrative. | Results | `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C41 | Moderate-profile perturbation stability (**0** verdict flips across cases) supports robustness framing. | Results | `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C42 | Conservative simultaneous bound analysis preserves all **12** moderate verdicts (including boundary **Google DR**). | Results | `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C43 | Sensitivity perturbation **±0.20** highlights **Google DR** as the only outcome-sensitive approved case (**8** flip points / **4** features). | Results | `notebooks/03_metrics_and_calibration.ipynb` | verified |
| P4-C44 | PhysioNet external benchmark behaviour (both models fail safety under moderate profile) is reported in supplementary extended data, not recomputed in core notebooks. | Results pointer | `inputs/supplementary.pdf` | external |
| P4-C45 | Eight healthcare failures upgraded to core-equivalent methodological parity with documented feature uplift counts. | Methods | `config/core_equivalent_cases.json`, `notebooks/01_dataset_intake.ipynb` | verified |
| P4-C46 | Engine is **replay_mode** for primary claims; compensatory formula and threshold profiles are version-locked in `engine/engine_manifest.json`. | Methods | `engine/engine_manifest.json`, `engine/corrected_public_engine_v1_1.py` | verified |
| P4-C47 | Forensic correction narrative (intermediate public engine drift vs canonical) is methodological provenance, not recomputed here. | Discussion | `docs/provenance.md`, Zenodo README | contextual |
| P4-C48 | Validation hierarchy positioning (Tier 4 simulation + Tier 3 retrospective replay; Tier 2/1 outstanding) is epistemic framing. | Discussion | Narrative | contextual |
| P4-C49 | Operational feasibility timing estimates (**45–90** min primary; **10–25** min secondary) are indicative decomposition, not measured wall times from this repo. | Discussion | Narrative | contextual |
| P4-C50 | Relationship to EU AI Act Articles **9**/**17** and FDA **Jan 2025** AI device software guidance is interpretive positioning. | Discussion | Narrative | external |
| P4-C51 | DECIDE-AI reporting alignment is declared for manuscript reporting discipline. | Reporting | Manuscript | contextual |
| P4-C52 | Data/code availability points to Zenodo DOI **10.5281/zenodo.19388835** and GitHub repository URL in manuscript. | Data availability | `CITATION.cff`, `README.md` | contextual |
| P4-C53 | AI assistance disclosure (Claude for code/docs support; author retains scientific decisions) is governance transparency, not a numerical claim. | AI use | Manuscript | contextual |
| P4-C54 | Competing interests / NHS England employment disclaimer is administrative. | Competing interests | Manuscript | contextual |
| P4-C55 | Single-author encoding limitation; inter-rater reliability outstanding — acknowledged limitation. | Limitations | Manuscript | contextual |
| P4-C56 | Tier-2/Tier-3 encodings rely on lower direct-evidence rates; expanded metrics must be read with provenance transparency. | Limitations | `notebooks/01_dataset_intake.ipynb` | contextual |
| P4-C57 | EEE enrichment pipeline statistics (**39** processed, **37** triangulated, **2** blocked) are archival/supplementary claims tied to Zenodo packaging. | Supplement | `inputs/supplementary.pdf`, `inputs/experiment_pack/` | external |
| P4-C58 | Repro execution contract: `python reproduce_all.py` runs notebooks, regenerates manifest, validates pinned digests, exports HTML. | Reproducibility | `reproduce_all.py`, `repro_manifest.json`, `scripts/validate_outputs.py` | verified |

## Escalations / out-of-repo dependencies

- **Literature and regulatory citations** (references 1–21, FDA/NTSB/Ofqual sources): evidence basis for case narratives; not recomputed in code (`external`).
- **PhysioNet benchmark** and some **extended data** paragraphs: supplementary PDF; confirm separately if promoted to executable pipeline (`external` → future work).
- **Zenodo “to be provided” placeholders** in supplementary: require publication-time DOI binding per portfolio website rules (`contextual` / governance).

## Maintenance notes

- When manuscript numbering or threshold copy changes, update this table and the notebook RTM print tags (`Qxx`) together.
- Keep `config/expected_outputs.json` aligned with any newly pinned artefacts before claiming `verified` status for new rows.
