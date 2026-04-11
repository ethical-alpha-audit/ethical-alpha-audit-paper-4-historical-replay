"""
EEE Overlay Merge Module — Governance Engine Integration

This module provides opt-in overlay consumption logic for the governance engine.
It loads EEE triangulated features and merges them into base v3_bridge features
using the transform rules defined in the Unified Schema Specification.

Usage:
    from eee_overlay.overlay_merge import OverlayMerger

    merger = OverlayMerger("path/to/canonicalised_v1.json")
    merged_features, log = merger.merge("epic_sepsis", base_features)
"""

import json
from pathlib import Path

# SCM variable direction map
HIGHER_IS_SAFER = {
    "intrinsic_safety", "clinical_utility", "uncertainty_calibration",
    "evidence_strength", "evidence_visibility", "traceability_integrity",
    "stress_robustness", "claimed_performance",
}
HIGHER_IS_RISKIER = {
    "bias_harm_index", "drift_susceptibility", "data_shift_rate",
    "harm_severity", "adversarial_gaming_capability",
}

BLOCKED_GOVERNANCE_IDS = frozenset({
    "acclarent_trudi_navigation_reuters2026",
    "sonio_detect_prenatal_labeling_reuters2026",
})


class OverlayMerger:
    """Merges EEE triangulated overlay features into base governance features."""

    def __init__(self, canonical_path, confidence_threshold=0.70):
        self.confidence_threshold = confidence_threshold
        with open(canonical_path) as f:
            data = json.load(f)
        self._overlay_index = {}
        for case in data["cases"]:
            self._overlay_index[case["case_id"]] = case

    @staticmethod
    def transform_eee_to_governance(variable_name, eee_value):
        """Transform EEE [-1,1] value to governance [0,1] space.

        Per unified_schema_spec.json §scm_variables:
          higher_is_safer:  governance = (eee + 1) / 2
          higher_is_riskier: governance = (-eee + 1) / 2
          fallback/deployment: governance = (eee + 1) / 2
        """
        if variable_name in HIGHER_IS_SAFER:
            return (eee_value + 1) / 2
        elif variable_name in HIGHER_IS_RISKIER:
            return (-eee_value + 1) / 2
        else:
            return (eee_value + 1) / 2

    def get_overlay(self, governance_case_id):
        """Get overlay case data for a governance case_id."""
        return self._overlay_index.get(governance_case_id)

    def merge(self, governance_case_id, base_features):
        """Merge overlay into base features for a case.

        Args:
            governance_case_id: The case_id from governance repository.
            base_features: Dict of {variable_name: {value_primary, ...}} from v3_bridge.

        Returns:
            (merged_features, merge_log) tuple.

        Rules (Build Plan §7):
        1. Check if eee_feature_overlay has a value for each variable.
        2. If present AND confidence >= threshold: use transformed value.
        3. If present AND confidence < threshold: use but flag.
        4. If absent: retain base.
        5. Blocked cases: no overlay.
        """
        overlay_case = self._overlay_index.get(governance_case_id)

        if overlay_case is None:
            return dict(base_features), {
                "overlay_applied": False,
                "reason": "no_overlay_available",
            }

        if governance_case_id in BLOCKED_GOVERNANCE_IDS or \
           overlay_case["deployment_risk_class"] == "BLOCKED":
            return dict(base_features), {
                "overlay_applied": False,
                "reason": "blocked_case",
            }

        overlay_feats = overlay_case.get("eee_feature_overlay", {})
        merged = {}
        log = {"overlay_applied": True, "merged": {}, "retained": [], "flagged": []}

        for var_name, base_data in base_features.items():
            if var_name in overlay_feats:
                ef = overlay_feats[var_name]
                eee_val = ef["value_primary"]
                gov_val = self.transform_eee_to_governance(var_name, eee_val)
                conf = ef["confidence_level"]

                entry = {
                    "value_primary": round(gov_val, 6),
                    "value_low": round(self.transform_eee_to_governance(var_name, ef["value_low"]), 6),
                    "value_high": round(self.transform_eee_to_governance(var_name, ef["value_high"]), 6),
                    "confidence_level": conf,
                    "provenance_class": ef["provenance_class_governance"],
                    "encoding_rule_id": ef["encoding_rule_id"],
                    "source_refs": ef["source_refs"],
                    "excerpt_ids": ef["excerpt_ids"],
                    "overlay_source": "eee_triangulated",
                    "eee_raw_value": eee_val,
                }

                if conf < self.confidence_threshold:
                    entry["overlay_flag"] = "low_confidence_overlay"
                    log["flagged"].append(var_name)

                merged[var_name] = entry
                log["merged"][var_name] = {
                    "base": base_data.get("value_primary"),
                    "overlay": round(gov_val, 6),
                    "confidence": conf,
                }
            else:
                merged[var_name] = dict(base_data)
                merged[var_name]["overlay_source"] = "base_v3_bridge"
                log["retained"].append(var_name)

        return merged, log

    @property
    def case_ids(self):
        return set(self._overlay_index.keys())

    @property
    def stats(self):
        total = len(self._overlay_index)
        blocked = sum(1 for c in self._overlay_index.values() if c["deployment_risk_class"] == "BLOCKED")
        return {"total": total, "processed": total - blocked, "blocked": blocked}
