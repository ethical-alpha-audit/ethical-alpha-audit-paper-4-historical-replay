# CHANGELOG — AI Governance Benchmark Repository

## v3.1.0-eee (2026-03-18)

### Added
- EEE overlay integration: 39 historical cases enriched with triangulated
  peer-reviewed evidence via the Evidence Enrichment Engine (EEE) v1.2.
- New database table: `eee_canonical_overlay` (sidecar, no existing table changes).
- Overlay-aware governance engine execution with opt-in feature merge.
- Evidence archive: full enrichment dataset, triangulation outputs, and
  validation reports preserved in `eee_evidence/`.
- Provenance hash chain: enrichment v1.1 → v1.2 → triangulation → canonical.
- Replay exports compatible with historical replay validation pipeline.

### Evidence Summary
- 37 cases processed with triangulated confidence scores (range: 0.73–0.93).
- 2 cases blocked (H34: Acclarent TruDi, H35: Sonio Detect) — insufficient evidence.
- 6 cases at HIGH_CONFIDENCE, 15 at MODERATE_CONFIDENCE, 5 at ELEVATED_CAUTION,
  8 at MODERATE_CAUTION, 3 at LOW_CONFIDENCE, 2 BLOCKED.
- 21 STRONG triangulation integrity, 16 FRAGILE, 2 BLOCKED.

### Unchanged
- All base case JSONs (v3.0) preserved verbatim.
- All existing database tables untouched.
- All existing threshold profiles, encoding rules, and schemas preserved.
- Full backward compatibility with v3.0 engine pipeline.

### Blocked Cases
- H34 (acclarent_trudi_navigation_reuters2026): INSUFFICIENT evidence, monitoring required.
- H35 (sonio_detect_prenatal_labeling_reuters2026): INSUFFICIENT evidence, monitoring required.

### Hash Chain
- EEE v1.1 parent: b77e10eccb2dde7f760444093de92019dbd2e7a3e5b16cc4343d37bdcb1b98c4
- EEE v1.2 enrichment: f9d181ca3859cb7e3b65c66a291c5da66eba47c95207a8c4ee01c5ae93ce8948
- Canonical dataset v1 (declared): c3ed7b93d68a0a898e25e1b4ce445350160c9372f709aec9479a98292ee37927
