# Provenance

## Engine
- Source: `engine/corrected_public_engine_v1_1.py` (canonical, unmodified from I1)
- Implements 5 non-compensatory gates + compensatory scoring + SCM abstention

## Data sources
- **Canonical dataset** (12 cases): Expert-triangulated, 15 SCM features each
- **Benchmark cases** (91 files): 61 historical failures + 30 FDA-cleared controls
- **EEE overlay** (39 cases): Triangulated evidence from EEE v1.2

## Canonical authority decisions
- **REM-1**: I1 engine is sole canonical engine (I2 build script excluded)
- **REM-2**: I1 hardcoded thresholds are canonical (I2 YAML excluded)
- **T5**: 8 core-equivalent cases: H17, H19–H24, H26

## Known annotations
- **N7**: Mean gate failures 2.636 vs manuscript 2.5 (editorial rounding)
- **N14**: Google DR flip points 7 vs manuscript 8 (floating-point boundary)
