"""EEE overlay to governance feature transform.

Implements the verified transform from Stage 2 compatibility audit.
This module is the ONLY bridge between EEE [-1,1] values and the
governance engine's [0,1] input contract.

Transform rules (from unified_schema_spec.json):
  higher_is_safer variables:  governance_value = (eee_value + 1) / 2
  higher_is_riskier variables: governance_value = (-eee_value + 1) / 2
"""

HIGHER_IS_SAFER = frozenset({
    'intrinsic_safety', 'clinical_utility', 'uncertainty_calibration',
    'evidence_strength', 'evidence_visibility', 'traceability_integrity',
    'stress_robustness', 'claimed_performance', 'fallback_safety_delta',
    'deployment_volume',
})

HIGHER_IS_RISKIER = frozenset({
    'bias_harm_index', 'drift_susceptibility', 'data_shift_rate',
    'harm_severity', 'adversarial_gaming_capability',
})


def eee_to_governance(variable_name, eee_value):
    """Transform EEE [-1,1] value to governance [0,1] range."""
    if variable_name in HIGHER_IS_SAFER:
        return (eee_value + 1) / 2
    elif variable_name in HIGHER_IS_RISKIER:
        return (-eee_value + 1) / 2
    return (eee_value + 1) / 2  # default: treat as higher_is_safer


def merge_features(base_features, eee_overlay):
    """Merge I2 base features with EEE overlay where available.

    Args:
        base_features: dict of {feature_name: {value_primary: float, ...}}
        eee_overlay: dict of {feature_name: {value_primary: float, ...}}
                     from canonicalised_v1.json eee_feature_overlay

    Returns:
        dict of {feature_name: float} ready for engine consumption
    """
    merged = {}
    for fname, fobj in base_features.items():
        if fname in eee_overlay:
            merged[fname] = round(
                eee_to_governance(fname, eee_overlay[fname]['value_primary']),
                6
            )
        else:
            merged[fname] = fobj['value_primary']
    return merged
