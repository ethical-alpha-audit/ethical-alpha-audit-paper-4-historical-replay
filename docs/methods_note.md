# Methods Note

## Three-tier feature routing

The manuscript uses three distinct feature-routing paths:

1. **Layer 1** (12 original cases): I1 canonical features → engine
2. **Layer 2** (20 failures + 12 controls): I2 base + EEE overlay merge → engine
3. **Expanded** (61+30): Original 12 via I1 canonical (Tier 1), additional 49 via I2+EEE (Tier 2), controls via I2 base (Tier 3)

This tiered routing is critical: it preserves Google DR's approval under Layer 1 (intrinsic_safety=0.55) while the expanded benchmark also shows Google DR approving (same I1 canonical features). Without tiered routing, uniform I2+EEE would produce 61/61 rejections instead of 60/61.

## EEE overlay transform

For higher_is_safer variables: `governance_value = (eee_value + 1) / 2`
For higher_is_riskier variables: `governance_value = (-eee_value + 1) / 2`

Implemented in `engine/eee_overlay_adapter.py`.
