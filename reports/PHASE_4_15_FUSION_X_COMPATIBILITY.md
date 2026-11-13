# SPECTRA-X / F1 — Phase 4, Task 4.15
# FUSION-X Multi-Modal Evidence Compatibility Audit

**Target Component:** FUSION-X Multi-Modal Discovery Engine  
**Authoritative Input Contract:** `CATALOG_MASKED_SPATIAL_EVIDENCE_V1`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Parent Task:** Phase 4, Task 4.14 / Task 4.15  
**Governance:** Strict Production-Preserving / Zero Changes to Frozen Contracts  

---

## 1. Compatibility Audit Scope

FUSION-X (`models.fusion.fusion_engine.FusionEngine`) synthesizes multi-modal scientific evidence across four primary modules:
1. **ASTROVISION:** Spatial infrared morphology and anomaly detection.
2. **SPECTRA:** Spectral reconstruction residuals and continuum excess.
3. **CHRONOS-X:** Multi-epoch temporal photometric variability.
4. **MOTION-X:** Astrometric proper motion and ephemeris crossmatching.

This audit evaluates the backward compatibility, schema non-interference, and scientific validity of consuming `SpatialAnomalyVettedEvidence` (`CATALOG_MASKED_SPATIAL_EVIDENCE_V1`) within FUSION-X without modifying existing production inference paths.

---

## 2. Evidence Contract Mapping

FUSION-X currently evaluates candidate spatial evidence using `CandidateRecord` and `FusionEngine.evaluate_source()`. The new contract seamlessly maps into the existing structure:

| `SpatialAnomalyVettedEvidence` Field | Existing FUSION-X Candidate Field | Semantic Impact & Scientific Advancement |
|---|---|---|
| `trial_id` / `pointing_id` | `source_id` / `pointing` | 100% Identical identifier tracking |
| `detector_id` | `detector` | Stratified detector attribution (D1–D6) |
| `central_peak_chi2` | `spatial_anomaly_score` | Clean vetted anomaly score with off-center contamination removed |
| `operating_threshold_tau` | `threshold_tau` | Preserves frozen, calibrated operational threshold |
| `is_anomaly_detected` | `spatial_flag` | True if vetted peak $\chi^2 \ge \tau$ |
| `vetting_status` | `advisory_flags` | Explains false alarm suppression or catalog confidence |
| `limitation_codes` | `limitation_codes` | Propagates fail-closed evidence provenance to discovery reports |

---

## 3. Preservation of Frozen Production Contracts

1. **Zero Modifications to Production Files:**
   - `models/fusion/fusion_engine.py`: **UNTOUCHED**
   - `models/fusion_x/model.py`: **UNTOUCHED**
   - `models/common/candidate_schema.py`: **UNTOUCHED**
   - `checkpoints/astrovision_spatial_v3.pt`: **UNTOUCHED & PRISTINE**
   - `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json`: **UNTOUCHED & PRISTINE**

2. **Shadow Stage Compatibility:**
   - In Task 4.15, the masker runs strictly in shadow mode via `AstroVisionShadowAdapter` and `MotionXMaskExtractor`.
   - FUSION-X can ingest `SpatialAnomalyVettedEvidence` side-by-side with legacy candidate records during Phase 5 deployment.
   - If `vetting_status == MASK_SUPPRESSED_FALSE_ALARM`, FUSION-X avoids allocating expensive follow-up resources to an off-center stellar artifact.

---

## 4. Multi-Modal Evidence Synthesis Scenario

Consider an evaluation trial in Detector 1 where a bright 13th-magnitude star lies at $d = 12\text{ px}$ from an empty sky aperture:

1. **Legacy Pipeline (Without Masking):**
   - Convolutional receptive field leaks star flux inward.
   - Central peak $\chi^2 = 245.8 > \tau_{\text{D1}} (186.29)$.
   - `spatial_flag = True`.
   - FUSION-X receives an apparent spatial anomaly and generates an erroneous discovery candidate alert.
2. **With CatalogAwareSourceMasker (Dilation = 2 px):**
   - Star core and wings are masked ($M_{\text{eff}} = 0.0$ at star footprint).
   - Central aperture ($r \le 2.5\text{ px}$) remains unencroached.
   - Central peak $\chi^2$ drops to $14.2 \ll 186.29$.
   - `is_anomaly_detected = False`, `vetting_status = MASK_SUPPRESSED_FALSE_ALARM`.
   - FUSION-X drops the false alarm, saving pipeline discovery purity.

---

## 5. Deployment Recommendation

Phase 5 production integration should introduce an optional flag:
`fusion_config.enable_catalog_vetted_spatial_evidence = True`
allowing immediate consumption of `SpatialAnomalyVettedEvidence` without modifying downstream catalog consumers or database schemas.

