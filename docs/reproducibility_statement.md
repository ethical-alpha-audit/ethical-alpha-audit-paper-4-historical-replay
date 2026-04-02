# Reproducibility Statement

## How to reproduce

From the repository root, with dependencies installed per `requirements.txt`:

```bash
python reproduce_all.py
```

This executes 4 notebooks in sequence, computes SHA-256 hashes of all 13 output files, and validates them against `config/expected_outputs.json`. A passing result (`ALL STEPS PASSED`) confirms bitwise-identical reproduction.

## Determinism guarantees

- `PYTHONHASHSEED=0` enforced by harness
- `random.seed(42)` for Monte Carlo sampling
- `matplotlib.use('Agg')` for headless rendering
- All CSV output uses fixed float precision and sorted keys
- Engine is stdlib-only with no randomness

## Validation without execution

```bash
python scripts/validate_outputs.py
```

Requires only Python stdlib. Verifies checked-in outputs match expected hashes.
