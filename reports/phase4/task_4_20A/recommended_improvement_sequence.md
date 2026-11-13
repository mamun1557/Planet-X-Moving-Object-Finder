# Recommended Engineering Improvement Sequence
## Phase 4, Task 4.20A — Operational Roadmap (Nov 8 – Nov 10, 2026)

**Target:** Systematic Execution of Prioritized Engineering Refinements  
**Objective:** Advance SPECTRA-X Overall Capability from $47.0\\%$ to $\\ge 60.0\\%$  
**Deadline:** November 10, 2026  

---

### Phase 1: High-ROI Algorithmic Implementations (Nov 9 Morning, 08:00 – 13:00)

#### Task 1.1: MOTION-X Minor Planet Ephemeris Engine Implementation (Est: 4.5 hrs)
- **File:** `models/motion_x/model.py`
- **Objective:** Replace the `return None` stub in `match_known_minor_planets()` with a vectorized 2-body Keplerian orbital propagator.
- **Implementation:**
  - Cache orbital elements ($a, e, i, \\Omega, \\omega, M_0, t_0$) for top 5,000 known asteroids and NEOs in `data/external/ephemeris/`.
  - Propagate orbital state vectors to observation MJD.
  - Compute topocentric celestial coordinates $(\\alpha, \\delta)$ from SPHEREx spacecraft ephemeris.
  - Return spatial separation and catalog identification.
- **Expected Impact:** MOTION-X capability: $20.0\\% \\to 35.0\\%$.

#### Task 1.2: SPECTRA Continuum Sidecar External IR Flux Ingestion (Est: 3.5 hrs)
- **File:** `spectra_engine/continuum_sidecar_engine.py` & `models/spectra/continuum_sidecar_interface.py`
- **Objective:** Automate direct ingestion of 2MASS ($J, H, K_s$) and CatWISE2020 ($W1, W2$) photometry from Task 4.19B tables.
- **Implementation:**
  - Ingest crossmatch fluxes into `ContinuumEvidenceRecord`.
  - Evaluate Rayleigh-Jeans photospheric excess $\\chi^2_{\\rm excess}$ across near-to-mid infrared bands.
  - Emit versioned `SPECTRA_FUSION_EVIDENCE_V1` record.
- **Expected Impact:** SPECTRA capability: $65.0\\% \\to 72.0\\%$.

---

### Phase 2: Signal Quality & Image Differencing Refinements (Nov 9 Afternoon, 14:00 – 19:00)

#### Task 2.1: CHRONOS-X Sub-Pixel Alignment & Dipole Filter (Est: 4.0 hrs)
- **File:** `models/chronos_x/model.py`
- **Objective:** Eliminate false subtraction dipoles caused by intra-visit dither pointing jitter.
- **Implementation:**
  - Compute 2D Fourier phase-correlation between reference and science cutouts.
  - Apply sub-pixel Fourier shift theorem to register images prior to variance differencing.
  - Enforce positive/negative flux symmetry veto to eliminate residual dipole alerts.
- **Expected Impact:** CHRONOS-X capability: $35.0\\% \\to 42.0\\%$.

#### Task 2.2: ASTROVISION Detector-Stratified Threshold Loader (Est: 2.5 hrs)
- **File:** `models/astrovision/model_v3.py`
- **Objective:** Formalize detector-stratified anomaly thresholds $\\tau_d$ in production inference.
- **Implementation:**
  - Load pre-calibrated detector thresholds from `calibration_parameters_v3.json` ($D1: 186.29, D2: 2536.3, D3: 999.76, D4: 633.73, D5: 91.85, D6: 197.35$).
  - Enforce detector-aware thresholding in `ApertureAnomalyScorer`.
  - Expose `CATALOG_MASKED_SPATIAL_EVIDENCE_V1` shadow adapter.
- **Expected Impact:** ASTROVISION capability: $55.0\\% \\to 62.0\\%$.

---

### Phase 3: Calibration, Provenance & Multimodal Synthesis (Nov 10 Morning, 08:00 – 13:00)

#### Task 3.1: FUSION-X Empirical Score Calibration Engine (Est: 3.5 hrs)
- **File:** `models/fusion/fusion_engine.py`
- **Objective:** Calibrate raw heterogeneous module anomaly scores into monotonic percentile ranks.
- **Implementation:**
  - Fit empirical CDF / isotonic scaling on calibration partition scores (P0001, P0008).
  - Transform raw $\\chi^2$ scores into standardized $[0, 1]$ anomaly confidence metrics.
  - Implement missing-modality dynamic reweighting with variance preservation.
- **Expected Impact:** FUSION-X capability: $60.0\\% \\to 72.0\\%$.

#### Task 3.2: Multimodal Provenance Serialization & Candidate Ranking (Est: 2.5 hrs)
- **File:** `models/common/candidate_schema.py` & `models/fusion_x/rank_anomalies.py`
- **Objective:** Standardize end-to-end evidence serialization for top candidate anomalies.
- **Implementation:**
  - Populate complete audit trail (input FITS, detector ID, catalog source IDs, channel masks) in `CandidateRecord`.
  - Export ranked candidate tables with human-readable scientific rationale.
- **Expected Impact:** FUSION-X capability: $72.0\\% \\to 75.0\\%$.

---

### Phase 4: Full Pipeline Regression Testing & Certification (Nov 10 Afternoon, 14:00 – 18:00)

#### Task 4.1: End-to-End Regression & Verification
- Execute full test suite (`pytest tests/ -q`) to certify zero regression across all 270 baseline tests.
- Verify that protected production asset SHA-256 hashes remain pristine.
- Validate that all five modules execute synchronously within the end-to-end candidate ranking workflow.

#### Task 4.2: Final Capability Milestone Verification
- Compute verified overall capability score across the five modules.
- Formally document transition from $47.0\\%$ baseline to $\\ge 60.0\\%$ target milestone.
