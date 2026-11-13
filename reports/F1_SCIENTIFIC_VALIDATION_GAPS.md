# SPECTRA-X / F1 — Scientific Validation Gaps & Integrity Audit
**Audit Date:** 2026-11-03  
**Auditor:** Lead Scientific Software Auditor & ML Engineering Agent  
**Scope:** Data Leakage, Independent Evaluation, Artifact Vetoes, Uncertainty Handling, and Ground-Truth Deficiencies  
**Status:** Complete Forensic Audit  

---

## 1. Executive Summary

This document provides a rigorous scientific integrity audit across the eight fundamental dimensions of machine learning validation in observational astrophysics:
1. **Data Leakage & Spatial Partitioning**
2. **Independent Test Set Isolation**
3. **Physical Uncertainty Propagation**
4. **Instrumental Artifact & Defect Rejection**
5. **Static Controls & Astrometric Baselines**
6. **Synthetic Injection vs Real Observation Separation**
7. **Candidate Provenance & Traceability**
8. **End-to-End Computational Reproducibility**

---

## 2. Scientific Integrity Audit Matrix

| Integrity Dimension | Requirement | Current Repository Status | Gap Severity | Mitigating Action Taken / Required |
| :--- | :--- | :---: | :---: | :--- |
| **1. Data Leakage** | Zero spatial, source, or preprocessing leakage between train, validation, and test sets | **VERIFIED CLEAN (v2 Models)** | None (Resolved) | Retrained ASTROVISION v2 with strict pointing quarantine. SPECTRA splits audited: 0 source ID overlap, $>33^{\circ}$ sky separation. |
| **2. Independent Evaluation** | Models evaluated on untouched test set with fixed parameters and zero post-hoc tuning | **VERIFIED CLEAN** | None (Resolved) | Evaluated on 1,392 sources from Pointing 0003; score thresholds locked prior to test inference. |
| **3. Uncertainty Propagation** | Real observational variances propagated; empirical flat-field systematic floor applied | **VERIFIED CLEAN** | None (Resolved) | Inverted variance $\sigma^2$ weighted in reconstruction loss; systematic floor $f_{\text{sys}} = 1.93\%$ incorporated. |
| **4. Artifact Rejection** | Automated vetoing of detector defects, saturation, cosmic rays, and subtraction dipoles | **VERIFIED CLEAN** | None (Resolved) | Screened fatal mask 615; edge proximity $< 5$ px; local $5 \times 5$ subtraction dipole test vetoed 1,228 false alarms. |
| **5. Static Controls** | Cross-matching against static stars to calibrate false positive rates | **PARTIAL GAP** | Medium | Local `gaia_dr3_reference_stars.csv` has only 5,000 all-sky stars (sparse). Full-density cone search around Pointing 0003 required. |
| **6. Synthetic Separation** | Strict segregation of synthetic injection benchmarks from real candidate catalogs | **VERIFIED CLEAN** | None (Resolved) | Procedural blackbody curves and synthetic injection tests are isolated in dedicated benchmark scripts; zero synthetic data in candidate tables. |
| **7. Candidate Provenance** | Full traceability of candidate ID, RA, Dec, observation ID, timestamps, and input tensors | **VERIFIED CLEAN** | None (Resolved) | Enforced via `models/common/candidate_schema.py` in `pointing_0003_candidates.csv`. |
| **8. Ground-Truth Labels** | Contemporaneous external discovery labels for evaluating real-world precision/recall | **CRITICAL SCIENTIFIC GAP** | High | **No contemporaneous ground-truth catalogs exist for 2026 Pointing 0003 observations.** Real-world discovery precision/recall must be stated as `NOT_AVAILABLE`. |

---

## 3. Deep-Dive Analysis of Validation Gaps

### 3.1 The Ground-Truth Discovery Metric Gap
In supervised machine learning, models are evaluated using Precision, Recall, ROC-AUC, and F1-score. However, in wide-field infrared astronomy:
- Pointing 0003 was observed in July 2026 at $(\alpha \approx 165.7^{\circ}, \delta \approx -69.6^{\circ})$.
- Available external transient catalogs (such as ZTF BTS) cover the Northern Hemisphere ($\delta > -30^{\circ}$) from 2018 to 2022.
- No contemporaneous ground-truth transient or moving-object catalog exists for this southern field.

> **CRITICAL SCIENTIFIC RULE ENFORCED:**  
> It is scientifically fraudulent to report an empirical discovery Precision, Recall, or F1-score on real observational data when no ground truth exists.  
> These metrics are formally recorded as **`NOT_AVAILABLE`**. Evaluation is strictly based on self-supervised reconstruction fidelity, residual distributions, and physical consistency.

### 3.2 The Multi-Month Cadence Gap
- Pointing 0003 currently contains four dither exposures (`1D1`, `2D1`, `3D1`, `4D1`) observed within **6.45 minutes** on 2026-07-20.
- While this baseline is sufficient to evaluate fast-moving asteroids and rapid stellar flares, **it cannot evaluate multi-month astronomical transients** (such as Type Ia supernovae or long-period variables).
- *Action Required:* Ingest subsequent seasonal repeat visits covering the identical celestial pointing footprint.

### 3.3 The Single-Detector Bandpass Gap
- All available Level-2 exposures for Pointing 0003 originate from Detector Array 1 (`D1`), covering wavelengths from $0.75$ to $0.98\,\mu\text{m}$ (Channels 1–17).
- Full SPHEREx discovery capability relies on the full 102 channels spanning $0.75$ to $5.0\,\mu\text{m}$ across all six detector arrays (D1 through D6).
- *Action Required:* Ingest coordinated exposures for Detectors 2 through 6 for Pointing 0003.

### 3.4 Localized Astrometric Cone Search Gap
- The existing Gaia catalog sample contains 5,000 reference stars distributed across the entire celestial sphere.
- Due to the large angular area of the sky ($41,253\,\text{deg}^2$), the nearest star in this sample is $300.2\text{ arcseconds}$ away from any Pointing 0003 source.
- *Action Required:* Download a dedicated, localized high-density Gaia DR3 cone search ($r = 2.5^{\circ}$) centered at $(\alpha = 165.7^{\circ}, \delta = -69.6^{\circ})$.
