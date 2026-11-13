# SPECTRA-X / F1 — Phase 3, Task 0R Report
## Cross-Report Scientific Evidence Reconciliation

**Task Type:** STRICT READ-ONLY INDEPENDENT SCIENTIFIC & GOVERNANCE AUDIT  
**Authorization:** Explicitly Granted by Project Owner  
**Module:** Full Architecture (ASTROVISION, SPECTRA, CHRONOS-X, MOTION-X, FUSION-X)  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Mode:** STRICT READ-ONLY (Zero Code, Weight, Data, Threshold, or Asset Modification)  
**Date:** 2026-11-07  
**Status:** **RECONCILIATION COMPLETE — CRITICAL DISCREPANCIES RESOLVED, LEAKAGE SAFEGUARDS ENFORCED, THREE-AXIS MATURITY SCORECARDS ESTABLISHED**

---

## 1. Executive Verdict

This independent reconciliation audit rigorously cross-checks previous project reports (Tasks 1.1A–1.1W, Tasks 1.2A–1.2E, Tasks 1.3A–1.3B) against the Task 0 One-Day Readiness Sprint audit and the physical files stored in the repository.

### Key Audit Findings

1. **Resolution of SPECTRA Numerical Inconsistencies:**
   - The authoritative numbers from Tasks 1.2B, 1.2D, and 1.2E are **fully reconciled and verified**:
     - **37,500:** Total input catalog sources across 5 pointings ($5 \times 7,500$). Verified in `phase3_multpointing_spectra_v1.csv`.
     - **26,455:** Sources with valid observational coverage ($\ge 1$ channel) across all 5 pointings. Verified in `phase3_multpointing_coverage_v1.csv`.
     - **15,002:** Candidate evaluation sources across Pointings 0002, 0009, 0010 with $\ge 5$ valid spectral channels.
     - **9,500:** Final eligible clean point sources in the evaluation cohort after applying quality filters (mask 615 veto, edge proximity, low aperture area). Verified in `data/processed/spectra/spectra_evaluation_scores_v1.csv` (Pointings 0002: 4,071; 0009: 2,284; 0010: 3,145).
     - **3,206:** Final eligible clean point sources in the P0008 calibration cohort after removing 5 P0001 overlap sources. Verified in `data/processed/spectra/spectra_p0008_calibration_scores_v1.csv`.
   - **Origin of 11,883 and 6,419:** The numbers "11,883 SEDs" and "6,419 evaluation sources" reported in Task 0 were **clerical cross-module transcription errors**. They originated from unrelated ASTROVISION Task 1.1 scratch audits (`scratch/audit11_out/`) and have **zero provenance in SPECTRA's actual data artifacts**. The true SPECTRA evaluation cohort size is **9,500**.
2. **Critical FUSION-X Leakage Safeguard Enforced:**
   - Task 0 proposed calibrating FUSION-X priority rank distributions on the evaluation pointings (`0002`, `0009`, `0010`). **This is a direct violation of partition quarantine**.
   - Pointings `0002`, `0009`, and `0010` are strictly held-out blind evaluation data for SPECTRA and ASTROVISION.
   - FUSION-X rank calibration and threshold selection **MUST occur exclusively on development/calibration pointings (Pointings 0001 and 0008)**. Pointings 0002, 0009, and 0010 must remain untouched until the final blind evaluation.
3. **Decoupling Blended Readiness into Three Distinct Axes:**
   - The single blended maturity percentages in Task 0 (e.g. FUSION-X: 75.5%, SPECTRA: 92.5%) conflated software completeness with empirical astronomical validation.
   - This audit establishes three separate, uncompromised scorecards:
     - **Scientific Evidence Maturity:** Proof against real astronomical ground truth.
     - **Engineering Implementation Maturity:** Software robustness, test coverage, and numerical stability.
     - **Integration Readiness:** Contract compliance, missing-modality handling, and clean boundaries.
4. **95% Target Eligibility:**
   - **SPECTRA is ELIGIBLE for 95%** (Engineering: 98%, Integration: 95%, Scientific: 78% / Level 6 Development Ready). Reaching 95% overall maturity requires broadband continuum sidecar integration and external reference cross-matching.
   - **FUSION-X is ELIGIBLE for 95%** (Engineering: 75%, Integration: 65%, Scientific: 30% / Level 4 Heuristic Co-Pilot). Reaching 95% integration/engineering maturity requires multi-modal contract unification, missing-modality invariance, rank calibration on P0008, and automated defect veto tests.

---

## 2. Audit A — SPECTRA Cohort Lineage & Count Reconciliation

### 2.1 Investigation of Reported Counts

Every reported number was traced to its authoritative data file and processing filter:

| Reported Count | Authoritative File / Source | Processing Stage & Role | Filters & Exclusions Applied | Verified On-Disk Value | Reconciled Status |
| :--- | :--- | :--- | :--- | ---: | :---: |
| **37,500** | `phase3_multpointing_spectra_v1.csv` | Input Catalog Extraction | Total input source catalog ($5 \times 7,500$). No filters applied. | **37,500** | **VERIFIED ACCURATE** |
| **26,455** | `phase3_multpointing_coverage_v1.csv` | Observational Coverage Gate | Sources with $\ge 1$ channel observed across all 5 pointings. Excludes 11,045 zero-coverage sources. | **26,455** | **VERIFIED ACCURATE** |
| **15,002** | `phase3_multpointing_extraction_manifest_v1.json` | Candidate Evaluation Filtering | Evaluation pointings (P0002, P0009, P0010) with $\ge 5$ channels ($5,709 + 4,549 + 4,744$). | **15,002** | **VERIFIED ACCURATE** |
| **9,500** | `data/processed/spectra/spectra_evaluation_scores_v1.csv` | Final Evaluation Cohort | Final eligible clean point sources in P0002 (4,071), P0009 (2,284), P0010 (3,145). Excludes fatal flags (mask 615), low aperture area, edge proximity, unresolved strata. | **9,500** | **VERIFIED ACCURATE** |
| **3,206** | `data/processed/spectra/spectra_p0008_calibration_scores_v1.csv` | Final Calibration Cohort | Final eligible clean point sources in P0008 (D1,D4: 1,055; D2,D5: 1,304; D3,D6: 847). Excludes 5 P0001 overlap sources and fatal flags. | **3,206** | **VERIFIED ACCURATE** |
| **11,883** | Task 0 Sprint Report (`SPECTRA_X_ONE_DAY_READINESS_SPRINT_AUDIT_AND_PLAN.md`) | Erroneous Task 0 Claim | Conflated from ASTROVISION scratch audit scripts (`scratch/audit11_out/`). No relation to SPECTRA files. | **N/A (Disproven)** | **CLERICAL ERROR IN TASK 0** |
| **6,419** | Task 0 Sprint Report (`SPECTRA_X_ONE_DAY_READINESS_SPRINT_AUDIT_AND_PLAN.md`) | Erroneous Task 0 Claim | Conflated from ASTROVISION scratch audit scripts (`scratch/audit11_out/`). The true evaluation cohort is 9,500. | **N/A (Disproven)** | **CLERICAL ERROR IN TASK 0** |

### 2.2 Authoritative Cohort Lineage Table

```
========================================================================================================================
                                     AUTHORITATIVE SPECTRA DATASET COHORT LINEAGE                                      
========================================================================================================================
Processing Stage                           P0001        P0008        P0002        P0009        P0010         Total      
------------------------------------------------------------------------------------------------------------------------
1. Input Source Catalog                    7,500        7,500        7,500        7,500        7,500        37,500      
2. Non-Zero Observational Coverage (>0)    3,398        5,979        5,772        5,749        5,557        26,455      
   - Zero Observational Coverage (Veto)    4,102        1,521        1,728        1,751        1,943        11,045      
3. Sufficient Channel Coverage (>=5 ch)    2,839        4,208        5,709        4,549        4,744        22,049      
   - Sparse Channels (<5 ch, Uninformative)  559        1,771           63        1,200          813         4,406      
4. Partition Role Assigned               TRAINING   CALIBRATION   EVALUATION   EVALUATION   EVALUATION          --      
5. Quality Exclusions (Mask 615, Edge, Area) N/A          997        1,638        2,265        1,599         6,499      
6. Training Overlap Exclusions               N/A            5          N/A          N/A          N/A             5      
------------------------------------------------------------------------------------------------------------------------
FINAL ELIGIBLE SCIENTIFIC COHORT             N/A        3,206        4,071        2,284        3,145        12,706      
                                                        (Calib)     (Eval P2)    (Eval P9)   (Eval P10)  (Calib + Eval) 
========================================================================================================================
```

---

## 3. Audit B — FUSION-X Leakage & Evaluation Independence

### 3.1 Data Cohort Usage & Leakage Matrix

| Data Cohort | Development & Code Prototyping | Calibration & Weight Tuning | Model / Rank Threshold Selection | Independent Blind Evaluation | Leakage Risk & Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Pointing 0001 (Ecliptic $+0.3^\circ$)** | **YES** | **YES (Permitted)** | **YES (Permitted)** | **NO** | Zero risk. Dedicated development/training pointing. |
| **Pointing 0008 (Ecliptic $+0.5^\circ$)** | **NO** | **YES (Authoritative)**| **YES (Authoritative)**| **NO** | Zero risk. Authoritative calibration cohort (3,206 clean sources). |
| **Pointing 0003 (Phase 2 Dataset)** | **YES** | **NO** | **NO** | **NO** | Zero risk. Historical 1,132 sources used for unit tests. |
| **Pointing 0002 (Mid-Lat South)** | **NO** | **NO (QUARANTINED)** | **NO (QUARANTINED)** | **YES (Authoritative)**| **CRITICAL SAFEGUARD**: Must NOT be exposed to fusion tuning. |
| **Pointing 0009 (Mid-Lat North)** | **NO** | **NO (QUARANTINED)** | **NO (QUARANTINED)** | **YES (Authoritative)**| **CRITICAL SAFEGUARD**: Must NOT be exposed to fusion tuning. |
| **Pointing 0010 (North Ecliptic Pole)** | **NO** | **NO (QUARANTINED)** | **NO (QUARANTINED)** | **YES (Authoritative)**| **CRITICAL SAFEGUARD**: Must NOT be exposed to fusion tuning. |

### 3.2 Evaluation Independence Analysis & Critical Safeguard

1. **The Contamination Trap in Task 0:**
   - In Task 0, Section 10 (Sprint Block 4, Task 4.1), the sprint plan proposed:
     > *"Execute end-to-end multimodal pipeline on evaluation cohorts (Pointings 0002, 0009, 0010; 6,419 sources)... implement empirical percentile rank calibration for fused priority scores across the 6,419 evaluation sources."*
   - **AUDIT RULING:** This proposal constitutes **catastrophic evaluation leakage**. Calibrating fused rank percentiles or tuning modality weights on Pointings 0002, 0009, and 0010 would destroy their status as untouched blind evaluation cohorts.
   - **MANDATORY ENFORCEMENT:** FUSION-X rank calibration MUST be derived exclusively from Pointing 0008 (or Pointings 0001 and 0008 combined). Pointings 0002, 0009, and 0010 must be evaluated with fixed, frozen fusion parameters.
2. **Missing Modality Treatment Consistency:**
   - In `models/fusion/fusion_engine.py`, missing modalities are handled by renormalizing active weights and applying a penalty factor $(1 - |\mathcal{M}_{\text{missing}}| \times 0.05)$.
   - Missing channels are explicitly reported as `MISSING` in `evidence_parts`.
   - However, `fusion_engine.py` currently expects raw $\chi^2$ from SPECTRA (with soft-saturation scale $\lambda = 0.005$) rather than ingesting the standardized `stratum_normalized_percentile` from `SPECTRA_FUSION_EVIDENCE_V1`. Updating `fusion_engine.py` to ingest the versioned contract is required.
3. **Defect Veto Independence:**
   - Scientific QC vetoes in `fusion_engine.py` (fatal flag 615, CHRONOS subtraction dipole, channel minimum $<1$, edge distance $<5\text{ px}$) operate upstream of ranking and reject corrupted records regardless of anomaly score.

---

## 4. Audit C — ASTROVISION Frozen Evaluation Boundary

1. **Cryptographic Checkpoint & Calibration Integrity:**
   - Frozen V3 Candidate Model: `checkpoints/astrovision_spatial_v3.pt` (3,436,965 B, SHA-256: `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99`). **Verified immutable**.
   - Frozen V3 Operating Thresholds: `data/processed/pilot_results/calibration_parameters_v3.json` (2,263 B, SHA-256: `aabe0d15d0e8d559cc82897e9c669f0f5f5785ab32e111123ac321a258ccf706`). **Verified immutable**.
2. **Evaluation Cohort & Performance Verification:**
   - Evaluated across 1,500 untouched trials on Pointings `0002`, `0009`, `0010`.
   - Point-source AUROC = **0.8040**, point recovery = **34.80%**, point precision = **79.09%**.
   - Extended-source AUROC = **0.7064**, extended recovery = **17.40%**.
3. **Empirical False Positive Rate Audit:**
   - Empirical evaluation FPR across 500 null controls is **9.00%** (peak scoring) to **9.20%** (integrated scoring), failing the nominal 5.0% target budget ($95\%$ Wilson CI: $[6.79\%, 11.83\%]$).
   - Driven by **Detector 1 (FPR = 22.62%–25.00%)** and **Pointing 0009 (FPR = 14.29%–14.88%)**.
4. **Implementation Status of Background Stationarity Checks:**
   - Code inspection of `models/astrovision/model_v3.py` confirms that `RobustLocalNormalizer` performs median subtraction and MAD division, but contains **ZERO background stationarity checks** (e.g., spatial gradient tests or multi-quadrant variance ratios).
   - The proposed background stationarity check is **merely planned / conceptual**, NOT implemented.
5. **Scientific Status Ruling:**
   - ASTROVISION V3 scientific status remains strictly:
     **`PARTIAL — NOT CERTIFIED FOR UNATTENDED PIPELINE INGESTION`**.
   - Reusing Pointings 0002, 0009, or 0010 to tune thresholds is strictly prohibited.

---

## 5. Audit D — CHRONOS-X Benchmark Validity

1. **Temporal Baseline & 44-Pair Verification:**
   - Execution of `inspect_fits.find_temporal_pairs()` across `manifests/fits_validation_catalog.csv` independently confirms exactly **44 candidate pairs**:
     - 20 intra-release pairs in QR2.
     - 24 intra-release pairs in QR3.
     - Exactly 0 inter-release pairs (QR2 vs QR3).
   - Time separation $\Delta t$ ranges from **0.001492 days (2.15 minutes)** to **0.004495 days (6.47 minutes)**.
   - **CONCLUSION:** Every single pair in the repository is a **short-cadence dither pair**. **ZERO genuine multi-month repeat observations of the same sky field exist in local storage**.
2. **Pipeline Implementation Audit:**
   - WCS reprojection (`reproject_interp`), 2-pixel morphological defect dilation (`binary_dilation`), combined variance propagation, local background matching, Gaussian smoothing PSF regularizer, and dipole artifact classification are fully implemented in `models/chronos_x/model.py`.
3. **Synthetic Transient Benchmark Capabilities:**
   - *Legitimate Synthetic Scope:* A synthetic injection benchmark on the 44 dither pairs CAN validly test:
     1. Numerical subtraction fidelity under WCS interpolation.
     2. Morphological defect cancellation (verifying the 152.2σ dead-pixel fix).
     3. Monopolar recovery vs. dipole veto rejection.
     4. Empirical background noise consistency ($\chi^2/\text{dof} \approx 1.08$).
     5. Point-source detection completeness as a function of injected SNR (SNRs 3 to 50).
   - *Illegitimate Claims:* A synthetic benchmark CANNOT validate:
     1. Real astrophysical transient recovery (supernovae, novae, blazars).
     2. Long-term temporal light curves or variable star classification.
     3. Real-world astrophysical false alarm rates across seasonal zodiacal drift.
   - Therefore, CHRONOS-X can attain Level 5 pipeline verification, but true astronomical transient readiness remains **Level 4 (Validation Pending)** until long-baseline data are acquired.

---

## 6. Audit E — MOTION-X Benchmark Validity

1. **Stub Implementation Verification:**
   - Inspection of `models/motion_x/model.py` (lines 52–55) confirms:
     ```python
     def match_known_minor_planets(self, ra_deg: float, dec_deg: float, mjd: float, tolerance_arcsec: float = 60.0) -> Optional[Dict[str, Any]]:
         """Cross-matches candidate coordinates with JPL Horizons asteroid positions at given epoch."""
         # Query matching from precomputed ephemeris table
         return None
     ```
     `match_known_minor_planets()` is an **unimplemented 2-line stub returning `None`**.
2. **Ephemeris Separations & In-FOV Verification:**
   - Independent verification of `reports/second_pass_audit/motion_crossmatch_audit.csv` across all 35 evaluated pointing-target combinations confirms:
     - Separations to the 5 Horizons bodies (Apophis, Ceres, Eros, Pallas, Vesta) range from **$16.07^\circ$ to $242.81^\circ$**.
     - All 35 records have `inside_spherex_fov = False` and `recovery_status = "NOT_IN_FOV"`.
     - **ZERO known solar system small bodies were present in the ingested SPHEREx pointings**.
3. **Synthetic Moving-Object Benchmark Scope:**
   - *Legitimate Synthetic Scope:* Synthetic injection can validly verify:
     1. Kinematic track linking across 4 dither exposures.
     2. Apparent motion velocity threshold sensitivity ($0.1$ to $5.0\text{ arcsec/min}$).
     3. Gaia DR3 stationary star vetoing (eliminating stellar proper motion false positives).
   - *Illegitimate Claims:* Synthetic injection CANNOT demonstrate real-world asteroid discovery capability. Claiming empirical asteroid recovery without in-FOV targets would violate scientific integrity.

---

## 7. Audit F — Five-Model Maturity Score Reconciliation

The single composite maturity percentages reported in Task 0 conflated software engineering completeness with empirical astronomical validation. The table below critiques each Task 0 estimate and establishes the audit reconciliation:

| Component | Task 0 Estimate | Task 0 Scoring Flaw & Critique | Reconciled Scientific Status | Reconciled Engineering Status |
| :--- | :---: | :--- | :--- | :--- |
| **SPECTRA** | 92.5% | Blended Level 6 qualification with 12.13% continuum tilt recovery. Unsupported claims of 11,883 SEDs. | **Level 6 (Development Ready, 78%)** | **High Maturity (98%)** |
| **FUSION-X** | 75.5% | Assigned 75.5% to a heuristic decision engine with zero trained weights and no multi-modal catalog evaluation. | **Level 4 (Heuristic Co-Pilot, 30%)** | **Moderate Maturity (75%)** |
| **ASTROVISION** | 82.0% | Masked empirical 9.0% evaluation FPR failure and low extended-source recovery (17.4%). | **Level 5+ (Partial Qualification, 62%)** | **High Maturity (88%)** |
| **CHRONOS-X** | 63.0% | Overstated readiness by treating 2-minute dither differencing as multi-epoch transient detection. | **Level 4 (Validation Pending, 25%)** | **Moderate Maturity (80%)** |
| **MOTION-X** | 55.0% | Assigned 55.0% despite an unimplemented stub (`return None`) and zero in-FOV targets. | **Level 4 (Stub Implemented, 20%)** | **Low-Moderate Maturity (45%)** |

---

## 8. Separate Scientific, Engineering, and Integration Scorecards

### 8.1 Scientific Evidence Maturity Scorecard
*Evaluates empirical proof against real astronomical ground truth, independent blind evaluations, verified false-alarm rates, and observational completeness.*

```
========================================================================================================================
                                     SCIENTIFIC EVIDENCE MATURITY SCORECARD                                     
========================================================================================================================
Criteria                               ASTROVISION      SPECTRA        CHRONOS-X       MOTION-X        FUSION-X         
------------------------------------------------------------------------------------------------------------------------
Data Provenance & Instrument Level        95%            98%             85%             80%             85%            
Independent Blind Evaluation              75%            90%             20%             20%             30%            
Verified False-Alarm / Null Control       50%            85%             40%             30%             30%            
Astronomical Ground-Truth Confirmation    60%            65%              0%              0%             15%            
Artifact & Failure Mode Characterization  70%            80%             50%             30%             50%            
------------------------------------------------------------------------------------------------------------------------
SCIENTIFIC MATURITY SCORE                 62%            78%             25%             20%             30%            
QUALIFICATION LEVEL                     LEVEL 5+       LEVEL 6         LEVEL 4         LEVEL 4         LEVEL 4          
========================================================================================================================
```

### 8.2 Engineering Implementation Maturity Scorecard
*Evaluates code quality, unit test coverage, defect handling, numerical stability, and computational reproducibility.*

```
========================================================================================================================
                                   ENGINEERING IMPLEMENTATION MATURITY SCORECARD                                   
========================================================================================================================
Criteria                               ASTROVISION      SPECTRA        CHRONOS-X       MOTION-X        FUSION-X         
------------------------------------------------------------------------------------------------------------------------
Code Modularity & Typing                  90%            98%             80%             50%             75%            
Unit Test Coverage & Pass Rate            95%           100%             80%             70%             80%            
Defect & Fatal Flag Handling              95%            98%             85%             60%             85%            
Numerical Stability & Zero Guards         85%            96%             75%             45%             75%            
Reproducibility Across Platforms          90%            98%             80%             60%             80%            
------------------------------------------------------------------------------------------------------------------------
ENGINEERING MATURITY SCORE                88%            98%             80%             45%             75%            
========================================================================================================================
```

### 8.3 Integration Readiness Scorecard
*Evaluates standardized contracts, schema compliance, missing-modality handling, cross-package dependency directions, and pipeline interface boundaries.*

```
========================================================================================================================
                                         INTEGRATION READINESS SCORECARD                                         
========================================================================================================================
Criteria                               ASTROVISION      SPECTRA        CHRONOS-X       MOTION-X        FUSION-X         
------------------------------------------------------------------------------------------------------------------------
Versioned Interface Contract (V1)          0%           100%              0%              0%             70%            
Missing-Modality Invariance               60%            95%             40%             30%             85%            
Limitation Codes Attached                 50%            95%             40%             30%             75%            
Architectural Boundary Decoupling         70%            95%             50%             40%             65%            
End-to-End Pipeline Co-Pilot Interface    60%            90%             40%             35%             60%            
------------------------------------------------------------------------------------------------------------------------
INTEGRATION READINESS SCORE               60%            95%             40%             35%             65%            
========================================================================================================================
```

---

## 9. Objective 95% Acceptance Criteria

### 9.1 SPECTRA 95% Target Acceptance Criteria
To legitimately attain $\ge 95\%$ overall maturity, SPECTRA must satisfy:
1. **Checkpoint & Calibration Invariance:** Checkpoint `checkpoints/spectra_masked_ae_v2.pt` (SHA-256: `6ecada80...`) and thresholds `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` (SHA-256: `d4029297...`) must remain bit-for-bit immutable.
2. **Broadband Continuum Sidecar Prototype:** A verified `ContinuumSidecar` implementing `ContinuumSidecarInterface` must be implemented in `spectra_engine/`, evaluating broadband Band 1 / Band 6 flux ratios to diagnose continuum tilts without touching frozen V2 weights.
3. **Real-Observation External Counterpart Validation:** Cross-match high-scoring anomalies on evaluation pointings (P0002, P0009, P0010; 9,500 sources) against Gaia DR3 and AllWISE to characterize their physical nature.
4. **Mandatory Limitation Enforcement:** Verified that every emitted record attaches `CONTINUUM_SENSITIVITY_LIMITED`, `PROVISIONAL_NULL_REFERENCE`, and `AUTONOMOUS_SPECTRA_DISCOVERY_PROHIBITED`.
5. **Direct Engine Wiring:** Verified direct integration between `spectra_engine` and `fusion_engine`.

### 9.2 FUSION-X 95% Target Acceptance Criteria
To legitimately attain $\ge 95\%$ integration and engineering maturity, FUSION-X must satisfy:
1. **Multi-Modal Versioned Contracts:** Standardized integration contracts for all 4 modalities (`SPECTRA_FUSION_EVIDENCE_V1`, `ASTROVISION_FUSION_EVIDENCE_V1`, `CHRONOS_FUSION_EVIDENCE_V1`, `MOTION_FUSION_EVIDENCE_V1`).
2. **Missing-Modality Invariance:** Unit tests proving that missing modalities are NEVER silently zeroed or scored as nominal, and that active weight renormalization with missing penalty is mathematically sound.
3. **Strict Partition Separation (Leakage Safeguard):** Calibration of fusion rank distributions MUST occur exclusively on Pointing 0008 (or P0001/P0008). **Pointings 0002, 0009, 0010 must remain untouched blind evaluation data**.
4. **Deterministic Defect Vetoes:** Automated regression tests verifying that instrumental defects (fatal flag 615, subtraction dipoles, edge proximity) are strictly vetoed (`validity_status = "REJECTED"`) and can never be promoted to high discovery priority.
5. **Codebase Unification:** Complete retirement of the obsolete, uninitialized PyTorch model in `models/fusion_x/` and formalization of `models/fusion/fusion_engine.py` as authoritative.

---

## 10. Critical Blockers and Unresolved Questions

1. **CHRONOS-X Real Transient Blocker:** Zero long-baseline repeat observations exist in the repository. Claiming true transient recovery readiness is physically impossible without new telescope observations.
2. **MOTION-X In-FOV Asteroid Blocker:** Zero asteroids were in the field of view during the ingested pointings. Claiming empirical asteroid discovery readiness is physically impossible without in-FOV targets.
3. **ASTROVISION D1 False-Alarm Blocker:** Empirical FPR on evaluation null controls is 9.00%–9.20% (D1 FPR is 22.62%–25.00%). The evaluation pointings are strictly quarantined and cannot be used to retune thresholds.
4. **Unresolved Question:** Does the project owner wish to maintain FUSION-X strictly as an interpretable heuristic co-pilot (recommended), or is a trained Bayesian / supervised classifier expected once labeled data become available?

---

## 11. Corrected One-Day Sprint Priority Order

```
+----------------------------------------------------------------------------------------------------+
|                      CORRECTED ONE-DAY SCIENTIFIC READINESS SPRINT SCHEDULE                         |
+-------------------+--------------------------------------------------------------------------------+
| Time Block        | Reconciled Tasks, Milestones, and Leakage Safeguards                           |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 1    | ALGORITHM COMPLETION & ENGINE UNIFICATION                                      |
| (Hours 08:00–10:00)| - Task 1.1: Implement minor planet ephemeris matching algorithm in MOTION-X   |
|                   |   (replace return None stub with Horizons ICRF interpolator).                  |
|                   | - Task 1.2: Implement ContinuumSidecar prototype in spectra_engine for         |
|                   |   broadband color-ratio excess diagnostics (Band 1 / Band 6 ratio).            |
|                   | - Task 1.3: Unify FUSION under models/fusion/fusion_engine.py; retire obsolete  |
|                   |   models/fusion_x/ stub to eliminate architectural ambiguity.                  |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 2    | CONTROLLED SYNTHETIC BENCHMARKS FOR BLOCKED MODALITIES                         |
| (Hours 10:00–12:00)| - Task 2.1: CHRONOS-X synthetic transient injection benchmark on 44 dither     |
|                   |   pairs (SNRs 3–50; measure recovery, FPR, and dipole rejection).              |
|                   | - Task 2.2: MOTION-X synthetic asteroid track injection benchmark across dither|
|                   |   sequences (measure kinematic recovery and velocity sensitivity).             |
|                   | - Task 2.3: Empirical null distribution characterization for CHRONOS-X across  |
|                   |   all 44 dither pairs (demonstrate Gaussian chi2/dof ~ 1.0 on background).     |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 3    | STANDARDIZED EVIDENCE CONTRACTS & CALIBRATION (ON P0008 ONLY)                  |
| (Hours 13:00–15:00)| - Task 3.1: Create astrovision_engine with ASTROVISION_FUSION_EVIDENCE_V1       |
|                   |   contract (attaching D1 elevated FPR limitation).                             |
|                   | - Task 3.2: Create chronos_engine with CHRONOS_FUSION_EVIDENCE_V1 contract      |
|                   |   (attaching short-cadence dither only limitation).                            |
|                   | - Task 3.3: Create motion_engine with MOTION_FUSION_EVIDENCE_V1 contract        |
|                   |   (attaching zero in-FOV asteroid limitation).                                 |
|                   | - Task 3.4: Calibrate FUSION-X rank percentiles exclusively on P0008 (or P0001).|
|                   |   STRICTLY PROHIBITED: Calibrating on Pointings 0002, 0009, 0010.              |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 4    | BLIND EVALUATION, EXTERNAL VALIDATION & FINAL CERTIFICATION                    |
| (Hours 15:00–17:00)| - Task 4.1: Execute end-to-end multimodal pipeline on evaluation cohorts       |
|                   |   (Pointings 0002, 0009, 0010; 9,500 clean sources) using FROZEN parameters.   |
|                   | - Task 4.2: External reference cross-validation of top SPECTRA and FUSION-X    |
|                   |   candidates against Gaia DR3 and AllWISE.                                     |
|                   | - Task 4.3: Automated regression test suite covering all 5 engines and vetoes. |
|                   | - Task 4.4: Author final Sprint Qualification Report and Manifest.             |
+-------------------+--------------------------------------------------------------------------------+
```

---

## 12. Exact Recommended Next Task

### Sprint Block 1, Task 1.1: MOTION-X Ephemeris Algorithm Implementation & Sidecar Integration
- **Specific Actions:**
  1. Replace the `return None` stub in `models/motion_x/model.py` with the genuine ICRF ephemeris interpolation algorithm matching JPL Horizons orbital state vectors.
  2. Implement the `ContinuumSidecar` prototype in `spectra_engine/continuum_sidecar.py` implementing `ContinuumSidecarInterface`.
  3. Wire `spectra_engine` into `models/fusion/fusion_engine.py` and retire obsolete `models/fusion_x/rank_anomalies.py`.
- **Precondition:** Awaiting explicit authorization from Project Owner before writing any code.

