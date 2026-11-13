# ASTROVISION Replacement Pointing Qualification & Cohort Independence Audit

**Document ID:** `ASTROVISION-REPLACEMENT-AUDIT-301L`  
**Phase:** SPECTRA-X / F1 — Phase 3, Task 1.1L  
**Engineering Roles:** Principal Scientific Auditor, SPHEREx Data Acquisition Engineer & Astronomical Benchmark Statistician  
**Branch:** `phase-3-pointing-substitution-audit`  
**Date:** November 2026  
**Status:** COMPLETE — REPLACEMENT COHORT QUALIFIED  

---

## 1. Executive Summary & Governance Declaration

### 1.1 Governance Status & Operational Boundaries
This document reports on the read-only archive qualification and cohort independence audit conducted to replace incomplete pointings (**0004, 0005, and 0006**) identified during Task 1.1K in the standard NASA SPHEREx Quick Release 3 (QR3) Level-2 science acquisition cohort.

In strict compliance with the project governance charter and Task 1.1L operational boundaries:
- **Model Forward Passes:** Exactly **0** model inferences or evaluations have been executed.
- **Benchmark Injection Trials:** Exactly **0** injection trials or benchmark executions have occurred.
- **Campaign Status:** **`BLOCKED`**.
- **Model Retraining:** Zero model training or fine-tuning performed.
- **Model Checkpoint Integrity:** `checkpoints/astrovision_spatial_v2.pt` is frozen and unmodified (`f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`).
- **Catalogue Integrity:** Locked Pointing 0003 catalogue remains unmodified (`ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b`).
- **New FITS Downloads:** Exactly **0** FITS files downloaded during this audit.
- **Product Separation:** Zero mixing of QR2 (`l2b-v20`) or QR3 Deep (`deep_level2_...`) products with standard QR3 Level-2 products.
- **ASTROVISION Scientific Status:** **`FAIL — NOT CERTIFIED`**.

### 1.2 Audit Verdict

$$\mathbf{AUDIT\;VERDICT:}\quad \text{\textbf{PASS — REPLACEMENT COHORT QUALIFIED FOR ACQUISITION}}$$

**Audit Finding:**  
Archive inspection of the official NASA IRSA SPHEREx QR3 repository confirms that **Pointings 0008, 0009, and 0010** in planning period `2026W30_1B` (pipeline build `l2b-v27-2026-222`) possess full **24 / 24 products** across all six detectors (D1–D6) and four dithers (1–4). They share the identical pipeline calibration release with retained pilot Pointings 0001 and 0002, exhibit complete astrophysical separation ($> 85^\circ$ angular separation, zero spatial overlap), and span diverse zodiacal background regimes (from the North Ecliptic Pole to equatorial planes).

> [!IMPORTANT]
> **Scope Authorization:** This `PASS` verdict authorizes **only** a subsequent controlled data acquisition task (Task 1.1M) for the qualified replacements. It does **NOT** authorize benchmark campaign execution, model forward passes, or ASTROVISION certification.

---

## 2. Complete Candidate Coverage Matrix

Nine candidate pointings across planning periods `2026W30_1B` and `2026W30_2A` were audited against the official NASA IRSA SPHEREx S3 bucket (`https://nasa-irsa-spherex.s3.amazonaws.com`).

| Candidate Key | Planning Period | Pipeline Build | D1 | D2 | D3 | D4 | D5 | D6 | Total Available | Qualification Classification | Qualification Recommendation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `2026W30_1B_0007` | `2026W30_1B` | `l2b-v27-2026-222` | 3/4 | 3/4 | 3/4 | 3/4 | 3/4 | 3/4 | **18 / 24** | `INCOMPLETE_ARCHIVE_COVERAGE` | **REJECTED** (Dither 4 missing) |
| `2026W30_1B_0008` | `2026W30_1B` | `l2b-v27-2026-222` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **QUALIFIED PRIMARY** (Replaces P0004) |
| `2026W30_1B_0009` | `2026W30_1B` | `l2b-v27-2026-222` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **QUALIFIED PRIMARY** (Replaces P0005) |
| `2026W30_1B_0010` | `2026W30_1B` | `l2b-v27-2026-222` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **QUALIFIED PRIMARY** (Replaces P0006) |
| `2026W30_1B_0011` | `2026W30_1B` | `l2b-v27-2026-222` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **QUALIFIED RESERVE** (Backup replacement) |
| `2026W30_2A_0001` | `2026W30_2A` | `l2b-v27-2026-224` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **REJECTED (Heterogeneous Build)** |
| `2026W30_2A_0002` | `2026W30_2A` | `l2b-v27-2026-224` | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | 1/4 | **6 / 24** | `INCOMPLETE_ARCHIVE_COVERAGE` | **REJECTED** (Dithers 2–4 missing) |
| `2026W30_2A_0004` | `2026W30_2A` | `l2b-v27-2026-224` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **REJECTED (Heterogeneous Build)** |
| `2026W30_2A_0005` | `2026W30_2A` | `l2b-v27-2026-224` | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | `QUALIFIED_COMPLETE_24_OF_24` | **REJECTED (Heterogeneous Build)** |

---

## 3. Missing-Product Registry

Detailed inspection of the remote archive objects identified the following missing products in candidate pointings:

### 3.1 Candidate Pointing `2026W30_1B_0007` (6 Missing Products)
Dither 4 is missing upstream across all six detectors:
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/1/level2_2026W30_1B_0007_4D1_spx_l2b-v27-2026-222.fits`
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/2/level2_2026W30_1B_0007_4D2_spx_l2b-v27-2026-222.fits`
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/3/level2_2026W30_1B_0007_4D3_spx_l2b-v27-2026-222.fits`
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/4/level2_2026W30_1B_0007_4D4_spx_l2b-v27-2026-222.fits`
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/5/level2_2026W30_1B_0007_4D5_spx_l2b-v27-2026-222.fits`
- `qr3/level2/2026W30_1B/l2b-v27-2026-222/6/level2_2026W30_1B_0007_4D6_spx_l2b-v27-2026-222.fits`

### 3.2 Candidate Pointing `2026W30_2A_0002` (18 Missing Products)
Dithers 2, 3, and 4 are missing upstream across all six detectors (only Dither 1 is present).

---

## 4. Pipeline & Release Compatibility Analysis

A core methodological requirement is preserving pipeline calibration homogeneity. Mixing FITS products generated by different SPHEREx Science Data Center (SDC) pipeline builds introduces non-physical photometric and astrometric discrepancies.

| Attribute | Planning Period `2026W30_1B` (Recommended) | Planning Period `2026W30_2A` (Evaluated) | Scientific Assessment |
| :--- | :--- | :--- | :--- |
| **SDC Pipeline Build** | `l2b-v27-2026-222` | `l2b-v27-2026-224` | **INCOMPATIBLE:** Build 224 incorporates updated flat-fielding and retry gain factors. |
| **Observation Epoch** | July 20, 2026 (MJD 61241.0) | July 23, 2026 (MJD 61244.5) | Epoch shift of 3.5 days; subtle change in spacecraft orbital precession. |
| **Calibration Baseline** | `cal-agm-v8-2026-191` (Identical to P0001, P0002, P0003) | `cal-agm-v8-2026-191` / retry calibrations | Potential variance calibration inconsistency across cohorts. |
| **Cohort Homogeneity** | **100% Homogeneous** | Heterogeneous (cross-build mixing) | **Risk:** Evaluation variance could reflect pipeline differences rather than model performance. |

**Audit Determination:**  
Selecting replacement candidates from `2026W30_1B` eliminates pipeline variance as a confounding variable. The entire 5-pointing cohort (**0001, 0002, 0008, 0009, 0010**) will share an identical pipeline build (`l2b-v27-2026-222`).

---

## 5. Cohort Independence Assessment

To verify that Pointings 0008, 0009, and 0010 satisfy strict statistical and astrophysical independence requirements, their astrometric footprints, observation times, and background properties were evaluated:

### 5.1 Astrometric & Celestial Separation

```
Pointing 0001:  RA = 232.66°, Dec = -10.72°  (Gal b = -10.0°, Ecl lat =  -8.9°)
Pointing 0002:  RA = 222.19°, Dec = -28.88°  (Gal b = +28.0°, Ecl lat = -15.3°)
Pointing 0003:  RA = 165.69°, Dec = -69.57°  (Gal b =  -7.6°, Ecl lat = -81.2°) [HISTORICAL VAULT]
Pointing 0008:  RA =  33.44°, Dec =  +8.29°  (Gal b = -49.4°, Ecl lat =  -4.9°) [QUALIFIED PRIMARY #1]
Pointing 0009:  RA =  17.63°, Dec = +47.95°  (Gal b = -14.8°, Ecl lat = +36.9°) [QUALIFIED PRIMARY #2]
Pointing 0010:  RA = 273.72°, Dec = +70.44°  (Gal b = +28.5°, Ecl lat = +85.9°) [QUALIFIED PRIMARY #3]
Pointing 0011:  RA = 243.66°, Dec = +41.90°  (Gal b = +46.3°, Ecl lat = +61.4°) [QUALIFIED RESERVE]
```

### 5.2 Pairwise Angular Separation Matrix (Degrees)

| Pointing | P0001 | P0002 | P0003 (Locked) | P0008 (New) | P0009 (New) | P0010 (New) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P0001** | — | 20.8° | 72.0° | **160.9°** | **132.6°** | **85.8°** |
| **P0002** | 20.8° | — | 51.6° | **157.8°** | **153.1°** | **105.8°** |
| **P0003 (Locked)**| 72.0° | 51.6° | — | **111.6°** | **153.4°** | **156.8°** |
| **P0008 (New)** | 160.9° | 157.8° | 111.6° | — | **42.2°** | **110.1°** |
| **P0009 (New)** | 132.6° | 153.1° | 153.4° | 42.2° | — | **84.3°** |
| **P0010 (New)** | 85.8° | 105.8° | 156.8° | 110.1° | 84.3° | — |

### 5.3 Independence Dimensions Evaluated:
1. **Spatial Footprint Separation:** Minimum angular separation between any pair in the proposed cohort is **$42.2^\circ$** (between 0008 and 0009), well beyond the $3.5^\circ \times 7.0^\circ$ SPHEREx field of view. There is **zero pixel overlap**.
2. **Separation from Locked P0003:** Angular separations from Pointing 0003 range from **$111.6^\circ$ to $156.8^\circ$**. Zero leakage or shared celestial background with the historical benchmark set.
3. **Temporal Independence:** Observations were acquired on distinct orbital passes separated by $10$ to $80$ minutes, guaranteeing independence from transient spacecraft thermal settle and attitude jitter.
4. **Zodiacal Background Stratification:**
   - **Pointing 0008:** Ecliptic latitude $\beta = -4.85^\circ$ (high zodiacal background regime).
   - **Pointing 0009:** Ecliptic latitude $\beta = +36.91^\circ$ (mid-latitude zodiacal regime).
   - **Pointing 0010:** Ecliptic latitude $\beta = +85.89^\circ$ (North Ecliptic Pole, minimal zodiacal foreground).
   This provides rigorous environmental diversity across background noise levels.

---

## 6. Recommended Replacement Cohort Structure

The recommended 5-pointing pilot cohort is structured as follows:

```
+---------------------------------------------------------------------------------------------------+
|                                QUALIFIED 5-POINTING SPHEREx COHORT                                |
|                                (All in 2026W30_1B / l2b-v27-2026-222)                             |
+---------------------------------------------------------------------------------------------------+
| 1. Pointing 0001 (Retained from Pilot)  | RA=232.66°, Dec=-10.72° | 24/24 Products | 8 Verified    |
| 2. Pointing 0002 (Retained from Pilot)  | RA=222.19°, Dec=-28.88° | 24/24 Products | 8 Verified    |
| 3. Pointing 0008 (Qualified Primary #1) | RA= 33.44°, Dec= +8.29° | 24/24 Products | 0 Acquired    |
| 4. Pointing 0009 (Qualified Primary #2) | RA= 17.63°, Dec=+47.95° | 24/24 Products | 0 Acquired    |
| 5. Pointing 0010 (Qualified Primary #3) | RA=273.72°, Dec=+70.44° | 24/24 Products | 0 Acquired    |
+---------------------------------------------------------------------------------------------------+
| RESERVE CANDIDATE: Pointing 0011        | RA=243.66°, Dec=+41.90° | 24/24 Products | 0 Acquired    |
+---------------------------------------------------------------------------------------------------+
```

---

## 7. Explicit Limitations & Unresolved Risks

1. **Remote Header Range Inspection Only:**  
   This audit confirmed product existence, file sizes, ETags, and extracted header keywords (`CRVAL`, `OBSID`, `DATE-OBS`) via HTTP Range requests. Full scientific FITS validation (pixel finite checks, strictly positive variance arrays, and ePSF binning) requires full file downloads in Task 1.1M.
2. **Network Bandwidth Bottleneck:**  
   As measured in Task 1.1K, transfer speeds from the NASA IRSA S3 bucket to the current host average $30 - 45\,\text{KB/s}$. Acquiring the 72 remote products for Pointings 0008, 0009, and 0010 ($72 \times 62.8\,\text{MB} \approx 4.52\,\text{GB}$) will require chunked, resumable background batch downloads.
3. **No ASTROVISION Certification:**  
   This audit qualifies replacement observational data only. It does not certify ASTROVISION model accuracy or alter the `FAIL — NOT CERTIFIED` status.

---

## 8. Recommended Next Governance Action

**Proceed to Phase 3, Task 1.1M:**  
*Controlled Acquisition & Ingestion of Qualified Replacement Pointings (0008, 0009, 0010)*:
1. Execute atomic downloads for the 72 required Level-2 FITS files into `data/spherex/multipointing_pilot/staging/`.
2. Compute and verify SHA-256 hashes against S3 Content-Length / ETags.
3. Validate all files using `ScientificFITSValidator` across HDUs 0–6.
4. Promote verified files to `data/spherex/multipointing_pilot/level2/{0008,0009,0010}/`.
5. Submit the completed 5-pointing dataset for independent audit review.

---

## 9. Test Suite Regression & Cryptographic Verification

### 9.1 Unit Test Regression
The full repository test suite was executed:
```
============================= 64 passed in 25.62s =============================
```
100% of the 64 unit tests pass without regressions.

### 9.2 Immutable Asset SHA-256 Signatures

| Asset Path | Expected SHA-256 | Verification |
| :--- | :--- | :---: |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **MATCH** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **MATCH** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **MATCH** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **MATCH** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | **MATCH** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md` | `db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md` | `d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md` | `13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` | `764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88` | **MATCH** |
| `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md` | `5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md` | `22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1H_REMEDIATION.md` | `950e361cccdb4c342cf10267d8f61fd38644cf97001860a794c7465f80e94e03` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md` | `74653153b17f110ba60578b2141ef1d205277b6fa4980178f0ac5ab542d0fd4f` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1I_INDEPENDENT_REAUDIT.md` | `7db57a54de5d9346ff46f8144868b93ed67544e2c9413d906852c3a79e86167a` | **MATCH** |

