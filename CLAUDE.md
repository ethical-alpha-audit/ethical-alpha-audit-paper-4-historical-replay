# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

Reproducibility package for **Paper 4** of the Ethical Alpha Audit five-paper bundle: a historical-replay evaluation of a non-compensatory AI governance engine over 91 medical-AI cases (61 historical failures + 30 FDA-cleared controls) plus a 12-case expert-triangulated subset.

The codebase is not a product — it is a **deterministic reproduction pipeline** for a manuscript. Every numerical output is pinned to a SHA-256 in [config/expected_outputs.json](config/expected_outputs.json), and the pipeline is expected to produce byte-identical CSVs/logs on any platform. Changes to engine logic, datasets, or numerical code paths will break hash validation — that is the intended safety net, not a bug.

## Commands

```bash
# Fast hash-only validation (stdlib only, no execution)
python scripts/validate_outputs.py

# Full deterministic pipeline (requires requirements.txt installed)
python reproduce_all.py

# Structural tests (paths/files exist, bootstrap works)
python -m pytest tests/ -v

# Run a single test
python -m pytest tests/test_reproducibility.py::test_benchmark_data_exists -v
```

`reproduce_all.py` runs, in order: the 4 notebooks → main manifest generation → main validation → experiment-pack manifest check → auxiliary scripts A01/A03/A04 → HTML export. It is fail-fast.

There is no lint step, no application server, and no test for engine correctness beyond the hash-locked manifest — the engine has already been validated 48/48 against the canonical baseline (CBS_v1) and is treated as immutable (see [engine/engine_manifest.json](engine/engine_manifest.json)).

## Architecture

### Pipeline shape

The pipeline is **notebook-orchestrated**, not script-orchestrated. The four notebooks in [notebooks/](notebooks/) are the source of truth for what gets computed; scripts in [scripts/](scripts/) only execute them, hash the outputs, and validate. Sequence and expected outputs are declared in [config/notebook_plan.json](config/notebook_plan.json):

1. `01_dataset_intake` → `outputs/tables/dataset_inventory.csv`
2. `02_historical_replay_execution` → `replay_results.csv`, `confusion_matrix.csv`, `replay_run_log.txt`
3. `03_metrics_and_calibration` → `metrics_summary.csv`, `calibration_summary.txt`
4. `04_figures_and_tables` → 4 figure PNGs + `ablation_matrix.csv` + manifests

PNGs are *visually* equivalent but not byte-identical across matplotlib micro-versions — only CSVs and text logs are hash-locked tightly. Auxiliary experiments (A01 perturbation, A03 provenance tier, A04 conservative bound) live under [inputs/experiment_pack/](inputs/experiment_pack/) with their own [manifest.json](inputs/experiment_pack/manifest.json) — they are validated separately by `reproduce_all.py`.

### Determinism contract

Hash-locking only works because:
- `PYTHONHASHSEED=0` is set by the harness and re-asserted in `notebook_runner.py`
- `random.seed(42)` for the 200-iteration Monte Carlo (see [p4_replay/run_config.py](p4_replay/run_config.py))
- The engine is **stdlib-only** (no numpy/pandas in `engine/`) with no internal randomness
- `matplotlib.use('Agg')` for headless rendering
- CSVs are written with fixed float precision and sorted keys
- All notebook outputs are cleared before re-execution

Touching any of these will silently invalidate every downstream hash. If a hash mismatch appears after a non-engine change, suspect a precision/formatting drift before suspecting a logic error.

### The governance engine ([engine/corrected_public_engine_v1_1.py](engine/corrected_public_engine_v1_1.py))

Two evaluation modes:
- **`replay_mode`** (default for Paper 4): 5 non-compensatory gates + weighted compensatory score
- **`canonical_full_mode`**: adds SCM abstention (logistic on `uncertainty_calibration`) and `fallback_safety_delta >= 0.3` override

The 5 gates: Safety, Evidence, Bias/Equity (inverted: `<=`), Calibration, Traceability. Compensatory weights are locked at `0.30/0.20/0.20/0.15/0.15` (bias inverted as `1 - bias_harm_index`). The four canonical threshold profiles (permissive/moderate/strict/very_strict) are hardcoded in the engine — do **not** read them from YAML or recompute them. They are the canonical authority (decision REM-2 in [docs/provenance.md](docs/provenance.md)).

### Three-tier feature routing (non-obvious, easy to break)

This is the subtle bit. The expanded benchmark layer feeds three *different* feature paths into the same engine depending on case provenance — documented in [docs/methods_note.md](docs/methods_note.md):

- **Layer 1** (12 original cases): I1 canonical features → engine directly
- **Layer 2** (20 failures + 12 controls): I2 base features merged with EEE overlay → engine
- **Expanded** (91 cases): original 12 stay on I1 (Tier 1); additional 49 go through I2+EEE (Tier 2); 30 controls via I2 base (Tier 3)

Uniform routing across all 91 cases would change the published 60/61 sensitivity to 61/61 — that is, the manuscript's reported false negative (Google DR) depends on this tiered routing. If you rewrite the data loaders, preserve the tiering or the result changes.

### EEE overlay transform ([engine/eee_overlay_adapter.py](engine/eee_overlay_adapter.py))

EEE values are in `[-1, 1]`; the engine expects `[0, 1]`. The adapter is the only sanctioned bridge:
- `higher_is_safer` variables: `(eee + 1) / 2`
- `higher_is_riskier` variables: `(-eee + 1) / 2` (sign flip)

The `HIGHER_IS_SAFER` / `HIGHER_IS_RISKIER` sets are authoritative — adding a feature requires updating one of them.

### Repo bootstrap ([p4_replay/](p4_replay/))

A small shim used by notebooks. `prepare_notebook(engine_on_path=True)` walks upward looking for `config/harness_settings.json` to locate the repo root, then puts the root (and optionally `engine/`) on `sys.path`. Notebooks should call this rather than hardcoding paths — they are executed via `nbclient` from the repo root, not from inside `notebooks/`.

## Repository conventions

- **Engine is immutable.** `engine/corrected_public_engine_v1_1.py` is a deterministic port of the canonical CBS_v1 baseline and its SHA-256 is pinned in `engine_manifest.json`. Don't refactor it.
- **Don't read thresholds from YAML.** The engine's hardcoded thresholds are canonical (REM-2). Any YAML in the broader EAA portfolio is non-authoritative for this paper.
- **No-commit-manuscripts policy** ([.gitignore](.gitignore)): `inputs/*.docx` and `inputs/*.pdf` are working-tree-only — required on disk for downstream workflows but must never enter git history. Do not `git add` manuscript files.
- **Canonical document state lives in [canonical_documents.yaml](canonical_documents.yaml)** (WS-CANONICAL-SOURCE-AUTOMATION). It records the LOCKED manuscript variant and SHAs, including which manuscript revisions have been retired and why.
- **Two confusion matrices coexist by design.** `confusion_matrix_primary.csv` (12+12, TP=11) is the manuscript's authoritative primary metric; `confusion_matrix.csv` (core-extended 20+12, TP=20) is reported alongside it. They are not duplicates — keep both, and check which one a downstream reference points at before "fixing" anything.
- **Windows quirk handled in `notebook_runner.py`:** `WindowsSelectorEventLoopPolicy()` is set to keep `nbclient`/zmq working; the deprecation warning on Python 3.14+ is intentionally suppressed.
