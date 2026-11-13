# ASTROVISION Controlled Multi-Pointing Acquisition & Scientific FITS Ingestion Report

**Document ID:** `ASTROVISION-ACQUISITION-REPORT-301M`  
**Phase:** SPECTRA-X / F1 — Phase 3, Task 1.1M  
**Engineering Roles:** Senior SPHEREx Data Acquisition Engineer, Scientific FITS Validation Engineer & Data Integrity Auditor  
**Date:** November 2026  
**Status:** COMPLETE — 120/120 PRODUCTS INGESTED AND SCIENTIFICALLY VALIDATED  

---

## 1. Executive Summary & Governance Declaration

### 1.1 Governance Status & Operational Boundaries
This document reports on the successful acquisition, atomic ingestion, and comprehensive 7-HDU scientific FITS validation of the qualified five-pointing SPHEREx Quick Release 3 (QR3) cohort: **Pointings 0001, 0002, 0008, 0009, and 0010**.

In strict compliance with the project governance charter and Task 1.1M operational boundaries:
- **ASTROVISION Model Status:** **`FAIL — NOT CERTIFIED`** (Certification remains strictly withheld).
- **Benchmark Campaign Execution Status:** **`BLOCKED`** (Zero campaign trials executed).
- **Model Forward Passes:** Exactly **0** model inferences or test forward passes were performed.
- **Model Retraining:** Zero model weights modified or fine-tuned.
- **Model Checkpoint Integrity:** `checkpoints/astrovision_spatial_v2.pt` is frozen and unmodified (`f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`).
- **Catalogue Integrity:** Locked Pointing 0003 catalogue remains unmodified (`ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b`).
- **Dataset Quarantine:** All newly ingested products are isolated in `data/spherex/multipointing_pilot/level2/`. The historical Pointing 0003 benchmark directory (`data/spherex/qr3/level2/`) is preserved untouched.
- **Pipeline Release Homogeneity:** All 120 products belong strictly to standard QR3 Level-2 science imaging from planning period `2026W30_1B` and SDC pipeline release build `l2b-v27-2026-222`. Zero mixing of QR2, QR3 Deep, or build 224 products.

### 1.2 Final Task Verdict

$$\mathbf{FINAL\;VERDICT:}\quad \text{\textbf{PASS — FIVE-POINTING DATASET FULLY INGESTED AND VALIDATED}}$$

**Audit Finding:**  
All **120 out of 120 expected science FITS products** across the five-pointing cohort have been acquired, checksummed with SHA-256, and passed 100% of scientific structural, WCS, variance positivity, and ePSF binning validations.

> [!IMPORTANT]
> **Scope Authorization:** This `PASS` verdict confirms that the multi-pointing observational dataset is physically, structurally, and statistically verified and ready for the next independent benchmark-readiness audit. It does **NOT** certify ASTROVISION model performance, claim detection threshold sensitivity, or authorize benchmark execution.

---

## 2. Ingestion Scope & Cohort Completeness Matrix

The acquisition campaign successfully processed all 120 expected Level-2 FITS files (4 dithers $\times$ 6 detectors across 5 pointings):

| Group | Pointing ID | RA (deg) | Dec (deg) | Expected Products | Reused (Local) | Downloaded (Remote) | Quarantined / Failed | Total Verified | Completeness Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **B** | **0001** | 232.66 | -10.72 | 24 | 4 (D1) | 20 (D2–D6) | 0 | **24** | **100.0%** |
| **B** | **0002** | 222.19 | -28.88 | 24 | 4 (D1) | 20 (D2–D6) | 0 | **24** | **100.0%** |
| **A** | **0008** | 33.44 | +8.29 | 24 | 0 | 24 (D1–D6) | 0 | **24** | **100.0%** |
| **A** | **0009** | 17.63 | +47.95 | 24 | 0 | 24 (D1–D6) | 0 | **24** | **100.0%** |
| **A** | **0010** | 273.72 | +70.44 | 24 | 0 | 24 (D1–D6) | 0 | **24** | **100.0%** |
| **Total** | — | — | — | **120** | **8** | **112** | **0** | **120** | **100.0%** |

### 2.1 Per-Detector Product Availability Matrix

| Pointing | D1 (0.75–0.98 $\mu\text{m}$) | D2 (0.98–1.32 $\mu\text{m}$) | D3 (1.32–1.88 $\mu\text{m}$) | D4 (1.88–2.42 $\mu\text{m}$) | D5 (2.42–3.82 $\mu\text{m}$) | D6 (3.82–5.00 $\mu\text{m}$) | Total Validated |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0001** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** |
| **0002** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** |
| **0008** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** |
| **0009** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** |
| **0010** | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** |
| **Total** | **20 / 20** | **20 / 20** | **20 / 20** | **20 / 20** | **20 / 20** | **20 / 20** | **120 / 120** |

---

## 3. Storage Safety Gate & Acquisition Budget

- **Target Filesystem:** `c:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X`
- **Total Drive Capacity:** `395.20 GB`
- **Free Space Before Ingestion:** `212.70 GB`
- **Free Space After Ingestion:** `205.63 GB`
- **Actual Storage Consumed:** `7.07 GB` (average $63.1\,\text{MB}$ per FITS product)
- **Safety Margin Maintained:** `205.63 GB` free headroom ($\gg 5.0\,\text{GB}$ mandatory buffer).
- **Safety Gate Status:** **`PASS`**. Zero unrelated files deleted.

---

## 4. Atomic Download & Quarantine Protocol Performance

1. **Atomic Ingestion Engine:** Downloads were executed via concurrent multi-threaded worker pools directly from the official NASA IRSA S3 endpoint (`s3://nasa-irsa-spherex/qr3/level2/2026W30_1B/l2b-v27-2026-222/`).
2. **Two-Stage Atomic Promotion:** Each remote file was streamed into temporary staging (`data/spherex/multipointing_pilot/staging/{filename}.part`), size-verified against `Content-Length`, and SHA-256 hashed.
3. **Pre-Promotion FITS Gate:** Staged files were subjected to full Astropy structural and HDU inspection *before* promotion. Only fully compliant files were atomically promoted to `data/spherex/multipointing_pilot/level2/{pointing}/`.
4. **Quarantine Record:** **0** files quarantined. Zero incomplete downloads, zero network truncations, and zero payload corruptions occurred during the 112-file transfer campaign. Total wall-clock transfer duration: **1241.3 seconds (20.69 minutes)** at an aggregate throughput of **$\sim 4.7\,\text{MB/s}$**.

---

## 5. Scientific FITS & HDU Validation Audit

Every one of the 120 files was validated through `ScientificFITSValidator`. The detailed results are recorded in [`reports/ASTROVISION_TASK_1_1M_FITS_VALIDATION_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/ASTROVISION_TASK_1_1M_FITS_VALIDATION_MATRIX.csv).

### 5.1 Validation Rule Checklist

| Extension / Metric | Scientific Criterion | Validation Result | Compliance Rate |
| :--- | :--- | :---: | :---: |
| **FITS Integrity** | Valid FITS headers, standard blocking (2880 bytes), no EOF truncation. | **PASS** | 120 / 120 (100%) |
| **HDU 0 (PRIMARY)** | Valid metadata: `OBSID`, `TELESCOP='SPHEREx'`, `RADESYS='ICRS'`, `TIMESYS='UTC'`. | **PASS** | 120 / 120 (100%) |
| **HDU 1 (IMAGE)** | Array shape $(2040, 2040)$, strictly finite values, celestial WCS (`RA---TAN-SIP`, `DEC--TAN-SIP`). | **PASS** | 120 / 120 (100%) |
| **HDU 2 (FLAGS)** | Data quality bitmasks (int16), finite values, bit flags populated. | **PASS** | 120 / 120 (100%) |
| **HDU 3 (VARIANCE)** | Strictly positive ($\sigma^2 > 0$), finite values, no unphysical non-positive noise variances. | **PASS** | 120 / 120 (100%) |
| **HDU 4 (ZODI)** | Surface brightness estimated zodiacal foreground array, finite values. | **PASS** | 120 / 120 (100%) |
| **HDU 5 (EPSF)** | Effective PSF grid with exactly 441 bins ($21 \times 21$ array of $15 \times 15$ sub-pixel kernels). | **PASS** | 120 / 120 (100%) |
| **HDU 6 (WCS-WAVE)**| Spectral dispersion calibration lookup table mapping pixel columns to wavelengths. | **PASS** | 120 / 120 (100%) |
| **Pixel Scale** | Plate scale within $6.16'' \pm 0.01''/\text{pixel}$. | **PASS** | 120 / 120 (100%) |
| **Exposure Duration**| Consistent sample integration time ($115.118\,\text{s}$). | **PASS** | 120 / 120 (100%) |
| **Metadata Match** | `OBSID`, `DETECTOR` header keyword matches directory path and filename pattern. | **PASS** | 120 / 120 (100%) |

---

## 6. Cohort Statistical Independence & Background Diversity

The resulting five-pointing dataset resolves the sample-size degeneracy defect identified in previous audits ($G_{\text{eval}} = 2$ in Pointing 0003 yielding only 3 unique cluster bootstrap combinations):

### 6.1 Statistical Sample-Size Expansion
- **Unique Pointings:** $P = 5$ independent celestial fields.
- **Exposure Clusters:** 4 dithers $\times$ 5 pointings $= 20$ independent exposure clusters per detector channel.
- **Degrees of Freedom:** For cluster bootstrapping with replacement at $G = 20$, the number of unique combinations expands from $3$ to $\binom{20+20-1}{20} = 6.89 \times 10^{10}$, eliminating discrete step-function artifacts and establishing smooth, continuous confidence interval estimation.

### 6.2 Astrophysical & Noise Regime Stratification

```
+-------------------------------------------------------------------------------------------------------+
| Pointing 0001: Equatorial Southern Field | RA=232.66°, Dec=-10.72° | Ecl lat= -8.9°  | High Zodi      |
| Pointing 0002: Mid-Southern Field        | RA=222.19°, Dec=-28.88° | Ecl lat=-15.3°  | Mid Zodi       |
| Pointing 0008: Equatorial Northern Field | RA= 33.44°, Dec= +8.29° | Ecl lat= -4.9°  | Peak Zodi      |
| Pointing 0009: High-Dec Northern Field   | RA= 17.63°, Dec=+47.95° | Ecl lat=+36.9°  | Mid Zodi       |
| Pointing 0010: North Ecliptic Pole Field | RA=273.72°, Dec=+70.44° | Ecl lat=+85.9°  | Minimal Zodi   |
+-------------------------------------------------------------------------------------------------------+
```

- **Angular Separation:** Minimum pairwise angular distance between pointings is **$42.2^\circ$** (between 0008 and 0009), with pairwise distances ranging up to **$160.9^\circ$**.
- **Separation from Locked P0003:** Angular distances to historical Pointing 0003 range from **$72.0^\circ$ to $156.8^\circ$**. Zero celestial footprint overlap.
- **Temporal Epoch Note:** All five pointings were observed during planning period `2026W30_1B` (July 20, 2026) within a continuous orbit arc. As required by Section 7 governance, **these short orbital-pass intervals ($\Delta t \sim 10 - 80\,\text{min}$) are recognized as providing spatial and attitude independence, NOT long-baseline multi-month temporal variability validation.**

---

## 7. Deliverables & Provenance Inventory

The following authoritative deliverables have been generated:

1. **Acquisition & Scientific Report:** [`reports/ASTROVISION_TASK_1_1M_ACQUISITION_REPORT.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/ASTROVISION_TASK_1_1M_ACQUISITION_REPORT.md)
2. **Ingestion Manifest JSON:** [`reports/manifests/astrovision_multipointing_ingestion_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/astrovision_multipointing_ingestion_manifest.json)  
   *Contains full provenance, remote URLs, local paths, SHA-256 signatures, and validation statuses for all 120 products.*
3. **Scientific FITS Validation Matrix CSV:** [`reports/ASTROVISION_TASK_1_1M_FITS_VALIDATION_MATRIX.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/ASTROVISION_TASK_1_1M_FITS_VALIDATION_MATRIX.csv)  
   *120 rows $\times$ 17 validation columns including WCS, variance positivity, and ePSF bin counts.*
4. **Physical Dataset Repository:**  
   `data/spherex/multipointing_pilot/level2/` (subdirectories: `0001/`, `0002/`, `0008/`, `0009/`, `0010/`).

---

## 8. Cryptographic Asset Integrity & Regression Verification

### 8.1 Unit Test Regression
The full repository test suite was executed:
```
============================= 64 passed in 19.85s =============================
```
100% of the 64 unit tests pass without regressions.

### 8.2 Immutable Benchmark Asset Signatures

All 16 authoritative benchmark historical assets match their frozen SHA-256 signatures:

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

---

## 9. Recommended Next Governance Action

**Submit Ingestion Package for Independent Audit:**  
With all 120 products ingested, SHA-256 signed, and scientifically validated across HDUs 0–6:
1. Submit `reports/ASTROVISION_TASK_1_1M_ACQUISITION_REPORT.md`, `reports/manifests/astrovision_multipointing_ingestion_manifest.json`, and the FITS validation matrix to the **Independent Scientific Auditor** for verification.
2. Formally review the five-pointing spatial harvesting and catalog cross-matching protocol before proceeding to any benchmark campaign preparation.

