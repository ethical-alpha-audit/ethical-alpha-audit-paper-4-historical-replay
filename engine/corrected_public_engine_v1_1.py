"""
Corrected Public Governance Engine v1.1

Deterministic transformation of the canonical historical-replay-governance-simulation
engine (GovernancePolicyEngine + CompensatoryPolicyEngine) for the ethical-alpha-public
repository.

Canonical source: historical-replay-governance-simulation/src/policy/governance_engine.py
Transformation:   stdlib-only (no numpy/pandas); JSON case dicts; deterministic output.

v1.1 changes from v1.0:
  - Added dual-mode evaluation:
      replay_mode (default):        5-gate + compensatory only (static historical replay)
      canonical_full_mode:          5-gate + compensatory + SCM abstention/fallback override
  - SCM abstention formula embedded (verified 12/12 against canonical stored results)
  - Fallback adequacy check (fallback_safety_delta >= 0.3)

CBS_v1 cross-validation: 48/48 gate+compensatory configurations matched.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any

# ============================================================
# CANONICAL PARAMETERS (locked from CBS_v1 baseline)
# ============================================================

#: The 5 features used for gate evaluation and compensatory scoring.
GATE_FEATURES = (
    "intrinsic_safety",         # G1 Safety          direction: >= threshold
    "evidence_strength",        # G2 Evidence         direction: >= threshold
    "bias_harm_index",          # G3 Bias/Equity      direction: <= threshold (INVERTED)
    "uncertainty_calibration",  # G4 Calibration      direction: >= threshold
    "traceability_integrity",   # G5 Traceability     direction: >= threshold
)

#: Gate-to-feature mapping: (feature_name, comparison_direction, profile_key).
GATE_SPEC = {
    "gate_safety":       ("intrinsic_safety",        ">=", "safety_gate"),
    "gate_evidence":     ("evidence_strength",       ">=", "evidence_gate"),
    "gate_bias":         ("bias_harm_index",          "<=", "bias_gate"),
    "gate_calibration":  ("uncertainty_calibration",  ">=", "calibration_gate"),
    "gate_traceability": ("traceability_integrity",   ">=", "traceability_gate"),
}

#: Compensatory weights (canonical, sum = 1.00).
COMP_WEIGHTS = {
    "safety":       0.30,
    "evidence":     0.20,
    "bias":         0.20,   # applied to (1 - bias_harm_index)
    "calibration":  0.15,
    "traceability": 0.15,
}

#: Canonical threshold profiles (from historical-replay-governance-simulation).
CANONICAL_THRESHOLD_PROFILES = {
    "permissive": {
        "safety_gate":       0.30,
        "evidence_gate":     0.30,
        "bias_gate":         0.70,
        "calibration_gate":  0.30,
        "traceability_gate": 0.30,
    },
    "moderate": {
        "safety_gate":       0.50,
        "evidence_gate":     0.50,
        "bias_gate":         0.50,
        "calibration_gate":  0.40,
        "traceability_gate": 0.40,
    },
    "strict": {
        "safety_gate":       0.70,
        "evidence_gate":     0.70,
        "bias_gate":         0.30,
        "calibration_gate":  0.60,
        "traceability_gate": 0.60,
    },
    "very_strict": {
        "safety_gate":       0.80,
        "evidence_gate":     0.80,
        "bias_gate":         0.20,
        "calibration_gate":  0.70,
        "traceability_gate": 0.70,
    },
}

#: Valid evaluation modes.
MODE_REPLAY = "replay_mode"
MODE_CANONICAL_FULL = "canonical_full_mode"
VALID_MODES = (MODE_REPLAY, MODE_CANONICAL_FULL)

# ============================================================
# SCM ABSTENTION PARAMETERS (from scm_functions.yaml)
# ============================================================

#: Abstention rate SCM formula parameters.
#: abstention_rate = 1 / (1 + exp(-SENSITIVITY * (CUTOFF - uncertainty_calibration)))
SCM_ABSTENTION_CUTOFF = 0.5
SCM_ABSTENTION_SENSITIVITY = 5.0

#: Abstention trigger threshold (strict >).
#: From governance_engine.py: (abstention > 0.5).astype(int)
ABSTENTION_TRIGGER_THRESHOLD = 0.5

#: Fallback adequacy threshold (>=).
#: From governance_engine.py: (fallback_safe >= 0.3).astype(int)
FALLBACK_ADEQUACY_THRESHOLD = 0.3


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_gate_value(features: dict[str, Any], feature_name: str) -> float:
    """Extract a numeric gate feature value from a case's feature dict.

    Handles both flat values (``{"intrinsic_safety": 0.55}``) and
    structured values (``{"intrinsic_safety": {"value_primary": 0.55, ...}}``).

    Raises ``KeyError`` if the feature is missing, ``TypeError`` if
    the value cannot be converted to float.
    """
    raw = features[feature_name]
    if isinstance(raw, dict):
        return float(raw["value_primary"])
    return float(raw)


# ============================================================
# SCM-DERIVED COMPUTATIONS (canonical_full_mode only)
# ============================================================

def compute_abstention_rate(uncertainty_calibration: float) -> float:
    """Compute SCM-derived abstention rate from uncertainty_calibration.

    Formula (from scm_functions.yaml, verified 12/12 against stored results)::

        abstention_rate = 1 / (1 + exp(-5.0 * (0.5 - uncertainty_calibration)))

    Poorly calibrated systems (low UC) produce high abstention rates.
    """
    exponent = -SCM_ABSTENTION_SENSITIVITY * (SCM_ABSTENTION_CUTOFF - uncertainty_calibration)
    return 1.0 / (1.0 + math.exp(exponent))


def compute_fallback_adequate(features: dict[str, Any]) -> bool:
    """Check whether fallback safety is adequate.

    From governance_engine.py::

        fallback_safe = df.get('observed_fallback_safety_delta',
                               df.get('fallback_safety_delta', ...)).values
        results['fallback_adequate'] = (fallback_safe >= 0.3).astype(int)

    Returns True if fallback_safety_delta >= 0.3, False otherwise.
    Defaults to 1.0 (adequate) if the feature is absent.
    """
    try:
        fsd = extract_gate_value(features, "fallback_safety_delta")
    except KeyError:
        return True  # canonical default: pd.Series(np.ones(n))
    return fsd >= FALLBACK_ADEQUACY_THRESHOLD


# ============================================================
# NON-COMPENSATORY GATE ENGINE
# ============================================================

def evaluate_gates(
    features: dict[str, Any],
    profile: dict[str, float],
) -> dict[str, Any]:
    """Evaluate non-compensatory governance gates for a single case.

    Parameters
    ----------
    features : dict
        Case feature dict (may be flat or structured with ``value_primary``).
    profile : dict
        Threshold profile (keys: ``safety_gate``, ``evidence_gate``, etc.).

    Returns
    -------
    dict with keys:
        gate_safety, gate_evidence, gate_bias, gate_calibration,
        gate_traceability (each 0 or 1), all_gates_pass (0 or 1),
        binding_constraints (list of failed gate names).
    """
    result: dict[str, Any] = {}
    binding: list[str] = []

    for gate_name, (feat_name, direction, profile_key) in GATE_SPEC.items():
        value = extract_gate_value(features, feat_name)
        threshold = profile[profile_key]

        if direction == ">=":
            passed = 1 if value >= threshold else 0
        else:  # "<="
            passed = 1 if value <= threshold else 0

        result[gate_name] = passed
        if not passed:
            binding.append(gate_name)

    result["all_gates_pass"] = 1 if not binding else 0
    result["binding_constraints"] = binding
    return result


# ============================================================
# COMPENSATORY SCORING ENGINE
# ============================================================

def compute_compensatory_score(features: dict[str, Any]) -> float:
    """Compute weighted compensatory score (canonical formula).

    Formula::

        score = 0.30 * intrinsic_safety
              + 0.20 * evidence_strength
              + 0.20 * (1 - bias_harm_index)     ← BIAS INVERTED
              + 0.15 * uncertainty_calibration
              + 0.15 * traceability_integrity

    Returns a float in [0.0, 1.0].
    """
    s = extract_gate_value(features, "intrinsic_safety")
    e = extract_gate_value(features, "evidence_strength")
    b = extract_gate_value(features, "bias_harm_index")
    c = extract_gate_value(features, "uncertainty_calibration")
    t = extract_gate_value(features, "traceability_integrity")

    score = (
        COMP_WEIGHTS["safety"]       * s
        + COMP_WEIGHTS["evidence"]   * e
        + COMP_WEIGHTS["bias"]       * (1.0 - b)   # ← CANONICAL INVERSION
        + COMP_WEIGHTS["calibration"] * c
        + COMP_WEIGHTS["traceability"] * t
    )
    return round(score, 6)


def compute_compensatory_threshold(profile: dict[str, float]) -> float:
    """Canonical compensatory threshold: mean of (safety, evidence, bias) thresholds.

    Reproduces ``np.mean(list(self.thresholds.values())[:3])`` from the canonical
    ``CompensatoryPolicyEngine``.
    """
    vals = [
        profile["safety_gate"],
        profile["evidence_gate"],
        profile["bias_gate"],
    ]
    return round(sum(vals) / len(vals), 6)


def evaluate_compensatory(
    features: dict[str, Any],
    profile: dict[str, float],
) -> dict[str, Any]:
    """Evaluate compensatory scoring for a single case.

    Returns dict with ``compensatory_score``, ``compensatory_threshold``,
    and ``compensatory_approved``.
    """
    score = compute_compensatory_score(features)
    threshold = compute_compensatory_threshold(profile)
    return {
        "compensatory_score": score,
        "compensatory_threshold": threshold,
        "compensatory_approved": 1 if score >= threshold else 0,
    }


# ============================================================
# FINAL VERDICT LOGIC
# ============================================================

def compute_final_verdict(
    all_gates_pass: int,
    features: dict[str, Any],
    mode: str,
) -> dict[str, Any]:
    """Compute the final approved/rejected verdict.

    Parameters
    ----------
    all_gates_pass : int
        1 if all 5 gates passed, 0 otherwise.
    features : dict
        Case feature dict (needed for SCM derivation in canonical_full_mode).
    mode : str
        One of ``replay_mode`` or ``canonical_full_mode``.

    Returns
    -------
    dict with ``approved``, ``mode``, and mode-specific fields.

    In **replay_mode** (default):
        ``approved = all_gates_pass``
        No abstention/fallback logic applied.

    In **canonical_full_mode**:
        ``abstention_rate = SCM_logistic(uncertainty_calibration)``
        ``abstention_triggered = abstention_rate > 0.5``
        ``fallback_adequate = fallback_safety_delta >= 0.3``
        ``approved = all_gates_pass AND (NOT abstention_triggered OR fallback_adequate)``
    """
    verdict: dict[str, Any] = {"mode": mode}

    if mode == MODE_REPLAY:
        verdict["approved"] = all_gates_pass
        verdict["abstention_applied"] = False
        return verdict

    # canonical_full_mode
    uc = extract_gate_value(features, "uncertainty_calibration")
    abstention_rate = compute_abstention_rate(uc)
    abstention_triggered = 1 if abstention_rate > ABSTENTION_TRIGGER_THRESHOLD else 0
    fallback_adequate = 1 if compute_fallback_adequate(features) else 0

    if all_gates_pass:
        approved = 1 if (not abstention_triggered or fallback_adequate) else 0
    else:
        approved = 0

    verdict["approved"] = approved
    verdict["abstention_applied"] = True
    verdict["abstention_rate"] = round(abstention_rate, 6)
    verdict["abstention_triggered"] = abstention_triggered
    verdict["fallback_adequate"] = fallback_adequate
    return verdict


# ============================================================
# FULL CASE EVALUATION
# ============================================================

def evaluate_case(
    case: dict[str, Any],
    profile_name: str = "moderate",
    profiles: dict[str, dict[str, float]] | None = None,
    mode: str = MODE_REPLAY,
) -> dict[str, Any]:
    """Evaluate a single case under a named threshold profile.

    Parameters
    ----------
    case : dict
        Must contain ``case_id`` (str) and ``features`` (dict).
    profile_name : str
        One of: permissive, moderate, strict, very_strict.
    profiles : dict, optional
        Custom profiles dict.  Defaults to ``CANONICAL_THRESHOLD_PROFILES``.
    mode : str
        ``"replay_mode"`` or ``"canonical_full_mode"``.

    Returns
    -------
    dict with gate results, compensatory results, final verdict, and metadata.
    """
    if mode not in VALID_MODES:
        raise ValueError(f"Invalid mode {mode!r}. Must be one of {VALID_MODES}")

    if profiles is None:
        profiles = CANONICAL_THRESHOLD_PROFILES

    profile = profiles[profile_name]
    features = case["features"]

    gates = evaluate_gates(features, profile)
    comp = evaluate_compensatory(features, profile)
    verdict = compute_final_verdict(gates["all_gates_pass"], features, mode)

    outcome = "APPROVE" if verdict["approved"] else "REJECT"

    result = {
        "case_id": case["case_id"],
        "profile_name": profile_name,
        "mode": mode,
        "governance_outcome": outcome,
        "gate_safety":       gates["gate_safety"],
        "gate_evidence":     gates["gate_evidence"],
        "gate_bias":         gates["gate_bias"],
        "gate_calibration":  gates["gate_calibration"],
        "gate_traceability": gates["gate_traceability"],
        "all_gates_pass":    gates["all_gates_pass"],
        "binding_constraints": gates["binding_constraints"],
        "compensatory_score":     comp["compensatory_score"],
        "compensatory_threshold": comp["compensatory_threshold"],
        "compensatory_approved":  comp["compensatory_approved"],
        "approved": verdict["approved"],
    }

    # Add abstention/fallback fields in canonical_full_mode
    if mode == MODE_CANONICAL_FULL:
        result["abstention_rate"]      = verdict["abstention_rate"]
        result["abstention_triggered"] = verdict["abstention_triggered"]
        result["fallback_adequate"]    = verdict["fallback_adequate"]

    return result


def evaluate_batch(
    cases: list[dict[str, Any]],
    profile_names: list[str] | None = None,
    profiles: dict[str, dict[str, float]] | None = None,
    mode: str = MODE_REPLAY,
) -> dict[str, Any]:
    """Evaluate a batch of cases across one or more profiles.

    Returns a dict keyed by case_id, each containing a ``profiles`` sub-dict.
    """
    if profile_names is None:
        profile_names = list(CANONICAL_THRESHOLD_PROFILES.keys())
    if profiles is None:
        profiles = CANONICAL_THRESHOLD_PROFILES

    results: dict[str, Any] = {}
    for case in cases:
        cid = case["case_id"]
        results[cid] = {"case_id": cid, "profiles": {}}
        for pname in profile_names:
            results[cid]["profiles"][pname] = evaluate_case(case, pname, profiles, mode)

    return results


# ============================================================
# DETERMINISTIC HASHING
# ============================================================

def canonical_json(obj: Any) -> str:
    """Canonical JSON serialisation (sorted keys, compact separators)."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def hash_output(obj: Any) -> str:
    """SHA-256 hash of canonical JSON serialisation."""
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


# ============================================================
# CLI ENTRY POINT
# ============================================================

def main() -> None:
    """Run the corrected public engine against cases in a directory."""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(
        description="Corrected Public Governance Engine v1.1"
    )
    parser.add_argument(
        "--cases-dir",
        required=True,
        help="Directory containing case JSON files",
    )
    parser.add_argument(
        "--profiles",
        nargs="*",
        default=["moderate"],
        help="Threshold profiles to evaluate (default: moderate)",
    )
    parser.add_argument(
        "--mode",
        choices=list(VALID_MODES),
        default=MODE_REPLAY,
        help=f"Evaluation mode (default: {MODE_REPLAY})",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON file path",
    )
    args = parser.parse_args()

    cases_dir = Path(args.cases_dir)
    if not cases_dir.is_dir():
        raise SystemExit(f"Not a directory: {cases_dir}")

    cases: list[dict[str, Any]] = []
    for fp in sorted(cases_dir.glob("*.json")):
        with open(fp, encoding="utf-8") as f:
            cases.append(json.load(f))

    results = evaluate_batch(cases, profile_names=args.profiles, mode=args.mode)

    output = {
        "engine_version": "corrected_public_v1.1",
        "canonical_baseline": "CBS_v1",
        "mode": args.mode,
        "total_cases": len(cases),
        "profiles_evaluated": args.profiles,
        "output_hash": hash_output(results),
        "results": results,
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Evaluated {len(cases)} cases x {len(args.profiles)} profiles ({args.mode})")
    print(f"Output hash: {output['output_hash']}")
    print(f"Written to: {out_path}")


if __name__ == "__main__":
    main()
