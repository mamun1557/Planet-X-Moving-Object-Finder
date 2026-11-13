# SPECTRA-X — One-Day Scientific Readiness Sprint
## Five-Model Baseline Audit & Execution Plan

**Task Type:** STRICT READ-ONLY SCIENTIFIC & ENGINEERING AUDIT  
**Authorization:** Explicitly Granted by Project Owner  
**Module:** Full Pipeline Architecture (ASTROVISION, SPECTRA, CHRONOS-X, MOTION-X, FUSION-X)  
**Pipeline Build:** `l2b-v27-2026-222`  
**Audit Mode:** STRICT READ-ONLY (Zero Code, Weight, Data, Threshold, or Asset Modification)  
**Date:** 2026-11-07  
**Status:** **AUDIT COMPLETE — TWO 95% TARGETS IDENTIFIED, REALISTIC ONE-DAY STRATEGY ESTABLISHED**

---

## 1. Executive Summary

This independent pre-sprint scientific and engineering audit establishes an objective, evidence-grounded baseline for all five core components of the SPECTRA-X discovery pipeline. The audit was conducted strictly under read-only permissions across existing codebases, model checkpoints, raw and processed datasets, FITS headers, external catalog cross-matches, and historical audit reports.

### Key Audit Findings

1. **Model Hierarchy and Evidence Separation:**
   - **SPECTRA (Current Maturity: 92.5%):** The most mature, thoroughly verified component in the repository. Trained on Pointing 0001, calibrated on Pointing 0008, blind-evaluated on 6,419 sources across Pointings 0002, 0009, 0010, certified at Level 6 (Development Ready), and encapsulated in a standalone `spectra_engine` package with versioned contract `SPECTRA_FUSION_EVIDENCE_V1`. Selected as **Candidate #1 for the 95% target**.
   - **FUSION-X (Current Maturity: 75.5%):** A transparent, interpretable multimodal prioritization co-pilot and evidence-synthesis engine (`models/fusion/fusion_engine.py`). It enforces soft-saturation normalization, explicit missing-modality handling, and scientific QC vetoes. Because its maturation depends on architectural standardization, versioned evidence contracts, and empirical rank calibration—rather than unacquired astronomical observations—it is selected as **Candidate #2 for the 95% target**.
   - **ASTROVISION (Current Maturity: 82.0%):** Significantly improved in V3 (`checkpoints/astrovision_spatial_v3.pt`), resolving fatal detector defect bleed (AUROC on D4 recovered from 0.4776 to 0.7261) and North Ecliptic Pole background compression (Point AUROC 0.8572). However, its empirical false positive rate on the untouched evaluation cohort is **9.00%–9.20%**, exceeding the calibrated 5.0% false-alarm budget, heavily driven by short-wavelength stellar/zodiacal variance on Detector 1 (FPR = 22.6%–25.0%). Reaching **85% is feasible** via a formalized evidence adapter and stratum limitation codes; reaching **95% is scientifically blocked** without acquiring new independent sky pointings.
   - **CHRONOS-X (Current Maturity: 63.0%):** Reprojection, defect dilation, variance differencing, and dipole vetting are implemented and functional. The historical 152.2σ transient signal was proven to be a dead-pixel defect and remediated. However, **ZERO genuine multi-epoch repeat observations exist in the repository**; all 44 intra-release pairs are short-cadence dithers separated by only 2.15 to 6.45 minutes. Reaching **85% true transient recovery is scientifically blocked** by the absence of long-baseline repeat observations.
   - **MOTION-X (Current Maturity: 55.0%):** Gaia DR3 astrometric cross-matching and proper motion propagation are functional (0.08 arcsec precision). However, `match_known_minor_planets()` is currently an **unimplemented stub returning `None`**, and **ZERO known solar system small bodies fell within the field of view** of the ingested SPHEREx pointings (all targets were 41° to 120° away). Reaching **85% real asteroid recovery is scientifically blocked** by pointing geometry.

2. **One-Day Sprint Realism:**
   - Universal $\ge 85\%$ across all five models is **physically unattainable without compromising scientific integrity**, because CHRONOS-X and MOTION-X face hard observational data blockers (zero multi-month epochs; zero in-FOV asteroids).
   - Instead, the sprint establishes a scientifically defensible two-tier architecture:
     - **Tier 1 (Target $\ge 95\%$):** SPECTRA and FUSION-X.
     - **Tier 2 (Target $\ge 85\%$):** ASTROVISION (via formal engine encapsulation and limitation tagging).
     - **Tier 3 (Controlled Benchmarks & Contracts, 72–80%):** CHRONOS-X and MOTION-X (via algorithmic completion, controlled synthetic injection benchmarks, empirical null characterization, and explicit contract limitation codes).

---

## 2. Repository and Artifact Inventory

Every key scientific asset in the repository was surveyed and cryptographically cataloged directly from physical storage:

```
SPECTRA-X Repository Asset Map
├── checkpoints/
│   ├── astrovision_spatial_v3.pt          [3,436,965 B | SHA-256: 3b608e49...] (Frozen V3 Model)
│   ├── astrovision_spatial_v3.json        [    5,549 B | SHA-256: 70e99547...] (Training Provenance)
│   ├── astrovision_spatial_v2.pt          [3,438,117 B | SHA-256: f65c0f13...] (Baseline V2 Model)
│   ├── spectra_masked_ae_v2.pt            [  382,177 B | SHA-256: 6ecada80...] (Frozen V2 Checkpoint)
│   └── spectra_masked_ae_v2_training_meta.json [4,023 B | SHA-256: 80d0d65a...] (V2 Training Metadata)
├── spectra_engine/                        (Authoritative Integration Layer)
│   ├── __init__.py                        [    1,588 B | SHA-256: 81d38b8f...]
│   ├── fusion_contract.py                 [   10,754 B | SHA-256: afeab483...] (SPECTRA_FUSION_EVIDENCE_V1)
│   ├── spectra_evidence_adapter.py        [   19,651 B | SHA-256: a6f5d504...] (Deterministic Percentiles)
│   └── continuum_sidecar_interface.py     [    2,299 B | SHA-256: d24a68a8...] (CONTINUUM_SIDECAR_EVIDENCE_V1)
├── models/
│   ├── astrovision/                       (Spatial Morphology Engine: model_v3.py, train scripts)
│   ├── chronos_x/                         (Temporal Differencing: model.py, run_temporal_differencing.py)
│   ├── motion_x/                          (Astrometric Validator: model.py, validate_motion.py)
│   ├── fusion/                            (Authoritative Multimodal Engine: fusion_engine.py, config)
│   ├── fusion_x/                          (Obsolete Toy Prototype: model.py, rank_anomalies.py)
│   └── common/                            (candidate_schema.py, candidate_schema.json)
├── data/
│   ├── spherex/
│   │   ├── multipointing_pilot/level2/    (120 FITS files across Pointings 0001, 0002, 0008, 0009, 0010)
│   │   ├── qr2/level2/                    (12 FITS files, Detector 2, April 2025, Pipeline v20)
│   │   ├── qr3/level2/                    (31 FITS files, Detectors 1..6, July 2026, Pipeline v27)
│   │   ├── qr2_deep/                      (4 FITS files, South Ecliptic Pole, Detector 2)
│   │   └── qr3_deep/                      (4 FITS files, South Ecliptic Pole, Detector 1)
│   ├── external/
│   │   ├── gaia_dr3/                      (gaia_dr3_reference_stars.csv, 5,000 stars + 15 field catalogs)
│   │   ├── jpl_horizons/                  (5 ephemeris CSVs: Apophis, Ceres, Eros, Pallas, Vesta)
│   │   ├── minor_planets/                 (jpl_sbdb_asteroid_orbits.json, 2,000 orbital elements)
│   │   └── transient_catalogs/            (ztf_bright_transient_survey.csv, confirmed optical transients)
│   └── processed/
│       ├── spectra/                       (phase3_multpointing_spectra_v1.csv, calib & eval CSVs)
│       ├── pilot_results/                 (calibration_parameters_v3.json, trial results CSVs)
│       └── crossmatch/                    (pointing_0003 Gaia and AllWISE matched catalogs)
└── tests/                                 (14 test suites, 135 unit tests, 100% passing)
```

---

## 3. Five Individual Scientific Component Audits

### 3.1 ASTROVISION (Spatial Image Morphology)

- **Architecture & Implementation:** Mask-aware convolutional autoencoder (`models/astrovision/model_v3.py`) with `MaskAwareConv2d` (re-normalizes valid pixel receptive fields), `RobustLocalNormalizer` (local median and MAD scaling), and `ApertureAnomalyScorer` (circular aperture integration).
- **Model Checkpoint:** `checkpoints/astrovision_spatial_v3.pt` (3,436,965 B, SHA-256: `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99`).
- **Training Corpus:** 1,200 patches ($64 \times 64$) harvested exclusively from deep calibration exposures (`data/spherex/qr2_deep` and `qr3_deep`).
- **Validation & Calibration Cohort:** Calibrated on Pointings `0001` and `0008` (1,000 cutout trials) to set operating threshold $\alpha = 0.05$.
- **Independent Evaluation Cohort:** 1,500 untouched trials (500 point-source injections, 500 extended-source injections, 500 control nulls) across Pointings `0002` (Mid-Lat South), `0009` (Mid-Lat North), and `0010` (North Ecliptic Pole).
- **Remediated Defects:**
  - *Fatal Pixel Bleed Elimination:* On Detector 4, point AUROC rose from $0.4776$ (V2) to **$0.7261$** ($p = 4.94 \times 10^{-7}$) in V3; point recovery increased from $4.82\%$ to $21.69\%$.
  - *NEP Dynamic Range Compression:* On Pointing `0010`, point AUROC rose from $0.6143$ to **$0.8572$** ($p = 4.72 \times 10^{-29}$), extended AUROC rose from $0.4599$ to **$0.7520$**, and polar null FPR was tightly held at $0.0427$.
  - *Aperture Integration:* Point recovery surged from $18.80\%$ to **$34.80\%$** ($+85.1\%$ relative improvement, McNemar $p = 7.53 \times 10^{-10}$); precision reached $79.09\%$.
- **Critical Unresolved Failure (The Known FPR Issue):**
  - Empirical false positive rate on the 500 evaluation null controls is **$9.00\%$** ($45/500$, $95\%$ Wilson CI: $[6.79\%, 11.83\%]$) for peak scoring and **$9.20\%$** ($46/500$) for aperture-integrated scoring, failing the nominal $5.0\%$ target budget.
  - Excess false alarms are concentrated in **Detector 1 (FPR = $22.62\%$–$25.00\%$)** and **Pointing `0009` (FPR = $14.29\%$–$14.88\%$)**, driven by dense unmodeled stellar backgrounds and zodiacal gradients in the $0.75$–$1.10\ \mu\text{m}$ regime.
  - Extended source recovery remains modest at **$17.40\%$** ($87/500$).
- **Data Governance Constraint:** Pointings `0002`, `0009`, and `0010` are held-out evaluation data and **must never be reused for threshold tuning or retraining**.
- **Current Evidence Maturity:** **82.0%**.

---

### 3.2 SPECTRA (102-Channel Infrared Spectral Anomaly Detection)

- **Architecture & Implementation:** Masked autoencoder architecture (`models/spectra/model.py`) optimized with masked $\chi^2$ loss. Fully encapsulated in the authoritative standalone package `spectra_engine`.
- **Model Checkpoint:** `checkpoints/spectra_masked_ae_v2.pt` (382,177 B, SHA-256: `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938`).
- **Data Engineering & Extraction:** Extracted 11,883 genuine source SEDs across 120 Level-2 FITS files in 5 pointings under pipeline build `l2b-v27-2026-222` (Task 1.2B).
- **Partition Governance & Calibration:**
  - Training: Pointing 0001 (2,416 sources).
  - Validation: Pointing 0004 (1,249 sources).
  - Calibration: Pointing 0008 (4,220 sources; 5 Pointing 0001 overlap sources removed; zero evaluation contamination). Derived empirical provisional-null thresholds per detector pair (`D1,D4`, `D2,D5`, `D3,D6`).
  - Blind Evaluation: Pointings 0002, 0009, 0010 (6,419 sources total; zero leakage).
- **Independent Evaluation Results:**
  - Evaluated on 6,419 untouched sources and 3,000 synthetic injection trials (1,500 positive, 1,500 control nulls).
  - Narrow emission/absorption feature anomaly detection: **AUROC = 0.9995**, recovery = **99.47%** at $\alpha=0.05$.
  - Broad continuum slope sensitivity: **AUROC = 0.5238**, recovery = **12.13%** (documented physical limitation of autoencoders with normalized SED inputs).
- **Operational Integration:**
  - Finalized in Task 1.3B: `spectra_engine` is decoupled from application frameworks and `models.spectra`.
  - Normalization: Stratum-normalized empirical percentiles via right-continuous CDF lookup; IQR-scaled stratum deviations with defensive zero-IQR guard.
  - Contract: `SPECTRA_FUSION_EVIDENCE_V1` attaches mandatory limitation codes (`CONTINUUM_SENSITIVITY_LIMITED`, `PROVISIONAL_NULL_REFERENCE`, `AUTONOMOUS_SPECTRA_DISCOVERY_PROHIBITED`) to every record.
- **Current Evidence Maturity:** **92.5%**.

---

### 3.3 CHRONOS-X (Multi-Epoch Temporal Differencing & Transient Detection)

- **Architecture & Implementation:** `ChronosTemporalDifferencer` (`models/chronos_x/model.py`) executing WCS astrometric reprojection (`reproject_interp`), morphological defect dilation (`binary_dilation`), combined variance propagation, local background median matching, Gaussian PSF-smoothing, and monopolar vs. dipole candidate classification.
- **Artifact Investigation (Historical 152.2σ Signal):** Fully dissected in Task 5 audit. Proven to be an ADC saturation overflow on an unbonded dead detector pixel (`MP_NONFUNC` + `MP_OVERFLOW`, flag 655426) smeared by bilinear image interpolation while mask interpolation used nearest-neighbor sampling. Remediated by 2-pixel morphological defect dilation.
- **Observation Metadata & Baseline Audit:**
  - 12 FITS in QR2 (Detector 2, April 2025).
  - 31 FITS in QR3 (Detectors 1..6, July 2026).
  - 120 FITS in multipointing pilot (Detectors 1..6, July 2026).
  - **CRITICAL SCIENTIFIC FINDING:** All 44 intra-release candidate pairs are **short-cadence dithers separated by only 2.15 to 6.45 minutes** ($\Delta t = 0.0015$ to $0.0045$ days).
  - **ZERO genuine multi-month repeat observations of the same sky field exist in the repository.**
  - Cross-release comparison between QR2 (Leo/Ursa Major, RA 164.7°, DEC +29.1°) and QR3 (Libra/Serpens, RA 232.7°, DEC -10.7°) is completely invalid because the pointings are separated by $>70^\circ$ and processed under different pipeline builds (v20 vs v27).
- **Scientific Validation Gap:**
  - Zero confirmed astronomical transients exist in the downloaded fields.
  - Without genuine long-baseline repeat observations, transient recovery completeness and false alarm rates on real astronomical events cannot be measured.
- **Current Evidence Maturity:** **63.0%**.

---

### 3.4 MOTION-X (Astrometric Kinematics & Solar System Movement)

- **Architecture & Implementation:** `MotionXValidator` (`models/motion_x/model.py`) and crossmatch pipeline (`scripts/process_crossmatch_and_classification.py`).
- **Astrometric Cross-Matching:**
  - Gaia DR3 reference stars (5,000 stars, $G < 15.0\,\text{mag}$) in ICRS at J2016.0.
  - Proper motion epoch propagation ($J2016.0 \to J2026.55$) verified in `test_astronomical_crossmatch.py` with median astrometric accuracy of **$0.08\text{ arcsec}$**.
  - Serves as an effective stationary star veto to eliminate stellar proper motion outliers from transient queues.
- **Solar System Small Bodies Audit:**
  - JPL Horizons ephemerides available for Apophis, Ceres, Eros, Pallas, and Vesta.
  - JPL SBDB asteroid orbits available (2,000 orbits).
  - **CRITICAL SCIENTIFIC FINDING #1:** In `models/motion_x/model.py`, `match_known_minor_planets()` is currently an **unimplemented stub**:
    ```python
    def match_known_minor_planets(self, ra_deg, dec_deg, mjd, tolerance_arcsec=60.0):
        # Query matching from precomputed ephemeris table
        return None
    ```
  - **CRITICAL SCIENTIFIC FINDING #2:** Systematic coordinate evaluation proved that **ZERO known solar system bodies fell within the SPHEREx fields of view during the ingested observations**. Apophis was 41° to 98° away; Eros was 81° to 113° away; Ceres, Pallas, and Vesta were $>50^\circ$ away.
  - **Conclusion:** No empirical asteroid or NEO recovery has ever occurred in the repository. Claiming moving-object detection capability without in-FOV targets would violate scientific integrity.
- **Current Evidence Maturity:** **55.0%**.

---

### 3.5 FUSION-X (Multimodal Evidence Integration & Scientific Co-Pilot)

- **Architecture & Implementation:** `FusionEngine` (`models/fusion/fusion_engine.py`) operating on `CandidateRecord` (`models/common/candidate_schema.py`).
- **Mathematical Ranking & Normalization:**
  - Dimensionless heuristic priority score $\in [0.0, 1.0]$. Explicitly disclaimed: **NOT a calibrated probability or Bayesian posterior**.
  - Soft-saturation normalization prevents extreme single-modality scores from dominating:
    $$\tilde{S}_{\text{SPECTRA}} = 1 - e^{-\chi^2 / 0.005}, \quad \tilde{S}_{\text{ASTRO}} = 1 - e^{-\sigma / 5.0}, \quad \tilde{S}_{\text{CHRONOS}} = 1 - e^{-\sigma / 5.0}$$
  - Transparent base weights: SPECTRA ($0.35$), ASTROVISION ($0.30$), CHRONOS-X ($0.25$), MOTION-X ($0.10$).
- **Missing-Modality Handling:**
  - Active weights are renormalized across available modalities ($\sum_{m \in \mathcal{M}_{\text{avail}}} w_m$).
  - Missing measurements are **NEVER silently zeroed**.
  - A penalty factor $\gamma = 0.05$ per missing modality is applied:
    $$S_{\text{FUSED}} = S_{\text{renorm}} \times (1.0 - |\mathcal{M}_{\text{missing}}| \times 0.05)$$
- **Scientific QC Vetoes:** Rejects candidates affected by fatal detector flags (`FLAGS & 615 != 0`), CHRONOS-X subtraction dipoles, insufficient spectral channels ($N < 1$), or severe edge proximity ($< 5\text{ px}$).
- **Integration Status:**
  - `spectra_engine` is fully prepared with `SPECTRA_FUSION_EVIDENCE_V1`.
  - Evidence adapters for ASTROVISION, CHRONOS-X, and MOTION-X are not yet formalized into versioned contracts.
  - An obsolete uninitialized PyTorch model (`models/fusion_x/model.py`) exists in the repository and must be retired to prevent architectural ambiguity.
- **Current Evidence Maturity:** **75.5%**.

---

## 4. Dataset and Partition Eligibility Matrix

| Dataset Identifier | Provenance & Instrument Pipeline | Pointings / Fields | File / Sample Count | Spatial / Temporal Scope | Assigned Role | Leakage Controls & Quarantines |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SPHEREx Deep Calib** | Level-2 QR2/QR3 Deep Field Exposures | NEP / SEP Fields | 8 FITS files | High redundancy calibration | **ASTROVISION Training** | Excluded from evaluation; disjoint from science pointings. |
| **SPHEREx Pointing 0001** | Level-2 QR3 `l2b-v27-2026-222` | Ecliptic Lat $+0.3^\circ$ | 24 FITS (1,200 cutouts, 2,416 SEDs) | Single pointing, 4 dithers, 6 dets | **Training & Calibration** | 5 overlap sources quarantined from P0008 calibration cohort. |
| **SPHEREx Pointing 0008** | Level-2 QR3 `l2b-v27-2026-222` | Ecliptic Lat $+0.5^\circ$ | 24 FITS (1,000 cutouts, 4,220 SEDs) | Single pointing, 4 dithers, 6 dets | **Calibration Cohort** | Strictly separated from training; 5 P0001 overlap sources excluded. |
| **SPHEREx Pointing 0002** | Level-2 QR3 `l2b-v27-2026-222` | Mid-Lat South ($\beta = -29.7^\circ$) | 24 FITS (500 cutouts, 1,675 SEDs) | Single pointing, 4 dithers, 6 dets | **Blind Evaluation** | **STRICT QUARANTINE**: Zero access during training/tuning. |
| **SPHEREx Pointing 0009** | Level-2 QR3 `l2b-v27-2026-222` | Mid-Lat North ($\beta = +31.2^\circ$) | 24 FITS (500 cutouts, 2,752 SEDs) | Single pointing, 4 dithers, 6 dets | **Blind Evaluation** | **STRICT QUARANTINE**: Zero access during training/tuning. |
| **SPHEREx Pointing 0010** | Level-2 QR3 `l2b-v27-2026-222` | North Ecliptic Pole ($\beta = +66.5^\circ$) | 24 FITS (500 cutouts, 1,992 SEDs) | NEP deep field, 4 dithers, 6 dets | **Blind Evaluation** | **STRICT QUARANTINE**: Zero access during training/tuning. |
| **Gaia DR3 Reference** | ESA Gaia DR3 (ICRS J2016.0) | All pilot fields | 5,000 reference stars + 15 field tables | Sky-wide astrometric standard | **Astrometric Reference** | Independent space mission standard; epoch propagated. |
| **JPL Horizons Ephem** | NASA/JPL Horizons System | Geocentric ICRF | 5 target CSVs | Solar system small bodies | **Ephemeris Reference** | Targets verified out of FOV (>40° separation). |
| **ZTF BTS Catalog** | Zwicky Transient Facility Bright Survey | Northern sky optical | Confirmed transients | Optical transient standard | **Cross-Match Standard** | Independent ground-truth optical transient catalog. |

---

## 5. Frozen Scientific Assets & Provenance Verification

Every primary frozen scientific asset was cryptographically re-verified via direct SHA-256 computation:

| Asset Description | Relative Path | Byte Size | Expected SHA-256 | Verified Post-Audit SHA-256 | Status |
| :--- | :--- | ---: | :--- | :--- | :---: |
| **ASTROVISION V3 Model** | `checkpoints/astrovision_spatial_v3.pt` | 3,436,965 | `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99` | `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99` | **IMMUTABLE** |
| **ASTROVISION V3 Metadata** | `checkpoints/astrovision_spatial_v3.json` | 5,549 | `70e9954752c0b4317635627d9d21180882ad36e38d5435f8c326260f58f8d188` | `70e9954752c0b4317635627d9d21180882ad36e38d5435f8c326260f58f8d188` | **IMMUTABLE** |
| **ASTROVISION V3 Calibration** | `data/processed/pilot_results/calibration_parameters_v3.json` | 2,263 | `aabe0d15d0e8d559cc82897e9c669f0f5f5785ab32e111123ac321a258ccf706` | `aabe0d15d0e8d559cc82897e9c669f0f5f5785ab32e111123ac321a258ccf706` | **IMMUTABLE** |
| **SPECTRA V2 Model** | `checkpoints/spectra_masked_ae_v2.pt` | 382,177 | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` | **IMMUTABLE** |
| **SPECTRA V2 Training Meta**| `checkpoints/spectra_masked_ae_v2_training_meta.json` | 4,023 | `80d0d65a00cbad8f2bde844d30a7aaa839c461789de3bc58c4fee895ca9f4f2c` | `80d0d65a00cbad8f2bde844d30a7aaa839c461789de3bc58c4fee895ca9f4f2c` | **IMMUTABLE** |
| **SPECTRA Provisional Thresholds** | `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | 12,978 | `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` | `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` | **IMMUTABLE** |
| **SPECTRA P0008 Calib Scores** | `data/processed/spectra/spectra_p0008_calibration_scores_v1.csv` | 446,446 | `7ac34d415f8132f7f164ab20c1b25fe03461bc709eb674031e838b2208e8c1a3` | `7ac34d415f8132f7f164ab20c1b25fe03461bc709eb674031e838b2208e8c1a3` | **IMMUTABLE** |
| **Multi-Pointing Master Spectra** | `data/processed/spectra/phase3_multpointing_spectra_v1.csv` | 332,189,097 | `8a96617cfe5d5152e720ee0c3890a7b8c7025ab2bfb3c682e08743affe6858e0` | `8a96617cfe5d5152e720ee0c3890a7b8c7025ab2bfb3c682e08743affe6858e0` | **IMMUTABLE** |

---

## 6. Existing Validation Evidence and Limitations

| Component | Verified Observational Evidence | Synthetic Benchmark Evidence | Software & Engineering Tests | Unverified Claims & Critical Gaps |
| :--- | :--- | :--- | :--- | :--- |
| **ASTROVISION** | Evaluated on 500 real control null cutouts across P0002, P0009, P0010. | 1,000 synthetic injections (500 point, 500 extended); Point AUROC 0.8040, Ext AUROC 0.7064. | 4 test suites, 35 unit tests (mask propagation, local normalizer, aperture scorer). | **FPR = 9.0% vs 5.0% target**; D1 stellar/zodi sensitivity; extended recovery only 17.4%. |
| **SPECTRA** | Evaluated on 6,419 untouched real source SEDs across 3 pointings; zero leakage. | 3,000 synthetic injections; narrow line AUROC 0.9995; continuum tilt AUROC 0.5238 (12.13% rec). | 6 test suites, 61 unit tests (invariance, calibration, adapter, boundary). | Continuum slope sensitivity limited (requires broadband color sidecar). |
| **CHRONOS-X** | Evaluated on 44 short-cadence dither pairs; 152.2σ dead-pixel defect remediated. | Gaussian PSF-smoothing regularizes sub-pixel pointing jitter. | Unit differencing test; variance propagation verified ($\chi^2/\text{dof} \approx 1.08$). | **Zero multi-month repeat observations**; zero confirmed astronomical transients; completeness unmeasured. |
| **MOTION-X** | Gaia DR3 proper motion propagation verified on 5,000 stars (0.08 arcsec error). | None yet executed in repository. | Unit test for coordinate propagation and Haversine separation. | **Zero in-FOV asteroids**; `match_known_minor_planets()` is an unimplemented stub returning `None`. |
| **FUSION-X** | Evaluated on deterministic benchmark candidates; missing-modality penalties active. | Soft-saturation tested against extreme synthetic input values. | Unit tests for schema compliance and candidate record serialization. | Multimodal weights are heuristic; no supervised training data exists. |

---

## 7. Transparent Readiness Scorecard

The evidence maturity of each model is evaluated across seven rigorous dimensions (scored 0% to 100%):
1. **Data Provenance & Integrity (Weight: 15%)**
2. **Implementation & Reproducibility (Weight: 15%)**
3. **Training & Partition Governance (Weight: 15%)**
4. **Calibration & Uncertainty (Weight: 15%)**
5. **Independent Scientific Evaluation (Weight: 15%)**
6. **Generalization & Artifact Rejection (Weight: 15%)**
7. **Operational Integration & Evidence Provenance (Weight: 10%)**

```
========================================================================================================================
                                      SPECTRA-X EVIDENCE-MATURITY SCORECARD                                      
========================================================================================================================
Dimension (Weight)                     ASTROVISION      SPECTRA        CHRONOS-X       MOTION-X        FUSION-X         
------------------------------------------------------------------------------------------------------------------------
1. Data Provenance & Integrity (15%)      95.0%          98.0%           85.0%          80.0%           88.0%           
2. Implementation & Repro (15%)           90.0%          96.0%           78.0%          55.0%           82.0%           
3. Training & Partition Gov (15%)         95.0%          98.0%           60.0%          65.0%           75.0%           
4. Calibration & Uncertainty (15%)        75.0%          90.0%           65.0%          60.0%           70.0%           
5. Independent Scientific Eval (15%)      85.0%          90.0%           45.0%          35.0%           65.0%           
6. Generalization & Artifact (15%)        65.0%          82.0%           55.0%          50.0%           78.0%           
7. Operational Integration (10%)          70.0%          95.0%           50.0%          40.0%           70.0%           
========================================================================================================================
COMPOSITE EVIDENCE MATURITY               82.0%          92.5%           63.0%          55.0%           75.5%           
------------------------------------------------------------------------------------------------------------------------
Feasible 85% in 1-Day Sprint?             YES            YES (Exceeded)  BLOCKED        BLOCKED         YES             
Feasible 95% in 1-Day Sprint?             NO             YES (Target #1) NO             NO              YES (Target #2) 
========================================================================================================================
```

---

## 8. Two Proposed 95% Target Components with Justification

### Proposed Component 1: SPECTRA (Current: 92.5% $\to$ Target: 95.0%)
- **Scientific Justification:** SPECTRA is already the highest-evidence module in the repository. Its masked autoencoder architecture, frozen weights, provisional-null calibration (P0008), blind evaluation on 6,419 sources (P0002/0009/0010), Level 6 qualification, and decoupled `spectra_engine` package provide an unshakeable foundation.
- **Path to $\ge 95\%$ in One Day:**
  1. Complete external catalog cross-validation: Correlate top SPECTRA anomaly scores on P0002/0009/0010 against known astronomical objects in Gaia DR3 and AllWISE to verify what astrophysical sources SPECTRA flags as outliers.
  2. Implement broadband continuum sidecar prototype (`ContinuumSidecar` implementing `ContinuumSidecarInterface`) utilizing Band 1 / Band 6 flux ratios to address the documented 12.13% continuum tilt recovery without modifying frozen SPECTRA V2 weights.
  3. Formally certify end-to-end integration between `spectra_engine` and `fusion_engine`.

### Proposed Component 2: FUSION-X (Current: 75.5% $\to$ Target: 95.0%)
- **Scientific Justification:** FUSION-X is the central evidence-synthesis engine and decision-maker of SPECTRA-X. Advancing FUSION-X to $\ge 95\%$ directly elevates the entire project's coherence and scientific defensibility. Unlike CHRONOS-X and MOTION-X, FUSION-X does not depend on waiting for unacquired telescope observations (asteroids or multi-month transients); its maturity is governed by contract formalization, missing-data handling, rank calibration, and artifact screening.
- **Path to $\ge 95\%$ in One Day:**
  1. Standardize versioned integration contracts for ASTROVISION, CHRONOS-X, and MOTION-X modeled on `SPECTRA_FUSION_EVIDENCE_V1`.
  2. Implement empirical percentile rank calibration for fused priority scores across the 6,419 evaluation sources.
  3. Wire `spectra_engine` directly into `fusion_engine`.
  4. Implement automated regression tests proving that instrumental defects (fatal flags, subtraction dipoles) are deterministically vetoed and can never leak to the top of the discovery queue.
  5. Retire the obsolete uninitialized prototype in `models/fusion_x/` and unify the codebase under authoritative `models/fusion/fusion_engine.py`.

---

## 9. Per-Component 85% Feasibility Assessment

1. **SPECTRA:** **FEASIBLE ($\ge 95\%$)**  
   Already exceeds 85% at 92.5%. Advancing to 95% is fully within reach during the one-day sprint.
2. **FUSION-X:** **FEASIBLE ($\ge 95\%$)**  
   Currently at 75.5%. Reaching 85% is readily achievable by midday; completing full contract integration and rank calibration advances it to $\ge 95\%$ by end-of-day.
3. **ASTROVISION:** **FEASIBLE ($\ge 85\%$, Target: 86–88%) | 95% BLOCKED**  
   Currently at 82.0%. Attaining $\ge 85\%$ is feasible by creating a formalized `astrovision_engine` evidence adapter, attaching explicit detector stratum limitation codes (`DETECTOR_1_HIGH_FPR`), adding local background stationarity diagnostics, and enforcing human review. Advancing to 95% is **BLOCKED** because the 9.0% empirical FPR cannot be remediated without retraining/recalibrating on new sky pointings; reusing the quarantined evaluation pointings (`0002`, `0009`, `0010`) is strictly prohibited.
4. **CHRONOS-X:** **BLOCKED FROM $\ge 85\%$ (Attainable: 76–80%)**  
   Currently at 63.0%. Can advance to ~78% via a controlled synthetic transient injection benchmark, empirical null characterization, and a formalized `chronos_engine` adapter. However, claiming $\ge 85\%$ true transient discovery readiness is **HARD BLOCKED** by the complete absence of multi-month repeat observations in the repository. Claiming 85% on 2-minute dither pairs would be scientifically dishonest.
5. **MOTION-X:** **BLOCKED FROM $\ge 85\%$ (Attainable: 72–75%)**  
   Currently at 55.0%. Can advance to ~74% by implementing the actual minor planet ephemeris interpolation algorithm (replacing the `return None` stub), executing a synthetic moving-target injection benchmark, and formalizing a `motion_engine` adapter. However, claiming $\ge 85\%$ real-world asteroid recovery readiness is **HARD BLOCKED** because zero solar system small bodies were present in the ingested fields of view.

---

## 10. One-Day Prioritized Execution Schedule

```
+----------------------------------------------------------------------------------------------------+
|                         ONE-DAY SCIENTIFIC READINESS SPRINT TIMELINE                               |
+-------------------+--------------------------------------------------------------------------------+
| Time Block        | Tasks, Milestones, and Scientific Objectives                                   |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 1    | ENGINEERING FIXES & ALGORITHM COMPLETION                                       |
| (Hours 08:00–10:00)| - Task 1.1: Implement minor planet ephemeris matching algorithm in MOTION-X   |
|                   |   (replace return None stub with Horizons ICRF interpolator).                  |
|                   | - Task 1.2: Implement ContinuumSidecar prototype in spectra_engine for         |
|                   |   broadband color-ratio excess diagnostics (Band 1 / Band 6 ratio).            |
|                   | - Task 1.3: Unify FUSION under models/fusion/fusion_engine.py; retire obsolete  |
|                   |   models/fusion_x/ toy model to eliminate architectural ambiguity.             |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 2    | CONTROLLED SYNTHETIC BENCHMARKS FOR BLOCKED MODALITIES                         |
| (Hours 10:00–12:00)| - Task 2.1: CHRONOS-X synthetic transient injection benchmark (inject variable |
|                   |   SNRs 3–50 into dither pairs; measure recovery, FPR, and dipole rejection).  |
|                   | - Task 2.2: MOTION-X synthetic asteroid track injection benchmark across dither|
|                   |   sequences (measure kinematic recovery and velocity threshold sensitivity).   |
|                   | - Task 2.3: Empirical null distribution characterization for CHRONOS-X across  |
|                   |   all 44 dither pairs (demonstrate Gaussian chi2/dof ~ 1.0 on background).     |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 3    | STANDARDIZED EVIDENCE CONTRACTS & MULTIMODAL INTEGRATION                       |
| (Hours 13:00–15:00)| - Task 3.1: Create astrovision_engine with ASTROVISION_FUSION_EVIDENCE_V1       |
|                   |   contract (attaching D1 elevated FPR and extended morphology limitations).     |
|                   | - Task 3.2: Create chronos_engine with CHRONOS_FUSION_EVIDENCE_V1 contract      |
|                   |   (attaching short-cadence dither only limitation).                            |
|                   | - Task 3.3: Create motion_engine with MOTION_FUSION_EVIDENCE_V1 contract        |
|                   |   (attaching zero in-FOV asteroid limitation).                                 |
|                   | - Task 3.4: Integrate all 4 evidence adapters into fusion_engine.              |
+-------------------+--------------------------------------------------------------------------------+
| Sprint Block 4    | MULTIMODAL QUALIFICATION, EXTERNAL VALIDATION & FINAL CERTIFICATION            |
| (Hours 15:00–17:00)| - Task 4.1: Execute end-to-end multimodal pipeline on evaluation cohorts       |
|                   |   (Pointings 0002, 0009, 0010; 6,419 sources).                                 |
|                   | - Task 4.2: External reference cross-validation of top SPECTRA and FUSION-X    |
|                   |   candidates against Gaia DR3 and AllWISE.                                     |
|                   | - Task 4.3: Automated regression test suite covering all 5 engines and vetoes. |
|                   | - Task 4.4: Author final Sprint Qualification Report and Manifest.             |
+-------------------+--------------------------------------------------------------------------------+
```

---

## 11. Risks, Blockers, and Scientific Integrity Safeguards

1. **Strict Evaluation Partition Quarantine:** Under no circumstances will Pointings `0002`, `0009`, or `0010` be used to retrain ASTROVISION, tune detection thresholds, or adjust feature scalers.
2. **Anti-Inflation Rule:** AUROC, synthetic injection recovery rate, and cross-match precision will **never be reported as evidence-maturity percentages**. Evidence maturity reflects the completeness of scientific proof across data, calibration, evaluation, and operational robustness.
3. **Transparent Limitation Tagging:** Every record generated by ASTROVISION, CHRONOS-X, and MOTION-X will carry permanent machine-readable limitation codes (`SHORT_CADENCE_DITHER_ONLY`, `NO_IN_FOV_SOLAR_SYSTEM_OBJECTS`, `DETECTOR_1_ELEVATED_FPR`).
4. **Veto Preservation:** Instrumental defects (fatal flags, subtraction dipoles, edge proximity) must remain strictly vetoed from discovery queues.

---

## 12. Exact Next Recommended Task

### Sprint Block 1, Task 1: MOTION-X Ephemeris Algorithm Implementation & Sidecar Integration
- **Objective:** Replace the `return None` stub in `models/motion_x/model.py` with the genuine ICRF ephemeris interpolation algorithm; implement the `ContinuumSidecar` prototype in `spectra_engine/continuum_sidecar.py`; and unify FUSION under `models/fusion/fusion_engine.py`.
- **Precondition:** Awaiting explicit authorization from Project Owner before writing any code.

