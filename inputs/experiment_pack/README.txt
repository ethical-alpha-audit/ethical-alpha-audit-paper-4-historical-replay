Paper 4 Experiment Bundle: Encoding Robustness Analyses (A01, A03, A04)
=======================================================================

A01 — Encoding Perturbation Analysis
  300 evaluations (12 cases x 5 features x 5 deltas)
  Verdict stability: 239/240 non-baseline = 99.6%
  Sole flip: Google DR intrinsic_safety at delta=-0.10

A03 — Provenance-Tier Sensitivity
  91 cases stratified into 3 provenance tiers
  Tier 1 (12 core): sensitivity 0.917 (canonical), confidence 0.591
  Tier 2 (49 additional): sensitivity 1.000, confidence 0.383
  Tier 3 (30 controls): specificity 1.000, confidence 0.380

A04 — Conservative-Bound Analysis
  12/12 verdicts maintained under worst-case encoding bounds
  Google DR survived at exact threshold boundary under inclusive gate logic

Reproduction:
  A01/A04 require: corrected governance engine + 12 canonical case files
  A03 requires: full 91-case replay output + canonical dataset
  Engine SHA256: 875f73150fae43695ecc6659581e8e25b365ad6171c9e13629fb01e923ab311c
