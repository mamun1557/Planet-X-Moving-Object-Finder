# ASTROVISION Multi-Pointing SPHEREx Data Acquisition & Controlled Ingestion Pilot

**Document ID:** `ASTROVISION-ACQUISITION-PILOT-301K`  
**Phase:** SPECTRA-X / F1 — Phase 3, Task 1.1K  
**Engineering Roles:** Senior Astronomical Data Acquisition Engineer, FITS Integrity Specialist & Scientific Data Provenance Auditor  
**Date:** November 2026  
**Status:** COMPLETE — STAGES A–D EXECUTED (AUDIT VERDICT ISSUED)  

---

## 1. Executive Summary & Governance Declaration

### 1.1 Governance Status & Operational Boundaries
This document reports on the execution of Stages A through D of the controlled data acquisition pilot across five candidate SPHEREx QR3 pointings: **0001, 0002, 0004, 0005, and 0006**.

In strict compliance with the task governance charter:
- **Model Forward Passes:** Exactly **0** model inferences or evaluations have been executed.
- **Benchmark Injection Trials:** Exactly **0** injection trials or benchmark executions have occurred.
- **Campaign Status:** **`BLOCKED`**.
- **Model Checkpoint:** `checkpoints/astrovision_spatial_v2.pt` is frozen and unmodified (`f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557`).
- **Catalogue:** Locked Pointing 0003 catalogue remains unmodified (`ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b`).
- **Product Type Isolation:** No QR2 products (`l2b-v20`) or QR3 Deep products (`deep_level2_...`) were mixed or substituted for standard QR3 Level-2 products.
- **ASTROVISION Scientific Status:** **`FAIL — NOT CERTIFIED`**.

### 1.2 Final Pilot Verdict

$$\mathbf{FINAL\;VERDICT:}\quad \text{\textbf{PARTIAL — ACQUISITION OR SCIENTIFIC VALIDATION INCOMPLETE}}$$

**Scientific Justification:**  
Stage A independent archive verification of the official NASA IRSA SPHEREx QR3 archive (`qr3/level2/2026W30_1B/l2b-v27-2026-222/`) revealed that only **Pointings 0001 and 0002** possess complete 24/24 product coverage across all six detectors. In contrast:
1. **Pointing 0004** possesses only 23/24 products (Detector D2 dither 3 is missing upstream from the archive).
2. **Pointing 0005** possesses only 12/24 products (Dithers 3 and 4 are missing upstream from the archive across all detectors D1–D6).
3. **Pointing 0006** possesses only 6/24 products (Dithers 2, 3, and 4 are missing upstream from the archive across all detectors D1–D6).

Pursuant to the mandatory Stage A protocol (*"If a pointing has incomplete coverage, report the missing detector products and stop that pointing's acquisition unless an explicitly approved exception exists"*), acquisition for Pointings 0004, 0005, and 0006 was halted immediately. Therefore, full 5-pointing acquisition cannot be declared complete.

---

## 2. Stage A — Independent Archive Verification Evidence

The official NASA IRSA SPHEREx S3 bucket (`https://nasa-irsa-spherex.s3.amazonaws.com`) was queried directly across all 6 detector directories (`1/` through `6/`) for planning period `2026W30_1B`, pipeline build `l2b-v27-2026-222`.

### 2.1 Five-Pointing Coverage Matrix (Expected: 24 Products / Pointing)

| Pointing ID | RA (deg) | Dec (deg) | D1 | D2 | D3 | D4 | D5 | D6 | Available / Expected | Archive Status | Acquisition Decision |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0001** | 232.66 | -10.72 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | **100% COMPLETE** | **PROCEED** |
| **0002** | 222.19 | -28.88 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | 4/4 | **24 / 24** | **100% COMPLETE** | **PROCEED** |
| **0004** | 79.01 | -55.87 | 4/4 | **3/4** | 4/4 | 4/4 | 4/4 | 4/4 | **23 / 24** | **INCOMPLETE (D2 Dither 3 missing)** | **STOP** |
| **0005** | 64.12 | -36.41 | **2/4** | **2/4** | **2/4** | **2/4** | **2/4** | **2/4** | **12 / 24** | **INCOMPLETE (Dithers 3-4 missing)** | **STOP** |
| **0006** | 55.89 | -17.20 | **1/4** | **1/4** | **1/4** | **1/4** | **1/4** | **1/4** | **6 / 24** | **INCOMPLETE (Dithers 2-4 missing)** | **STOP** |
| **Total** | — | — | 15/20 | 14/20 | 15/20 | 15/20 | 15/20 | 15/20 | **89 / 120** | **74.2% Available** | **2 Proceed / 3 Halted** |

### 2.2 Missing Product Registry

The following 31 products are confirmed missing upstream from NASA IRSA SPHEREx QR3 (`2026W30_1B/l2b-v27-2026-222`):

1. **Pointing 0004 (1 missing product):**
   - `level2_2026W30_1B_0004_3D2_spx_l2b-v27-2026-222.fits` (Detector D2, Dither 3)
2. **Pointing 0005 (12 missing products):**
   - Dithers 3 & 4 across all detectors D1–D6:
     - `level2_2026W30_1B_0005_3D1_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D1...`
     - `level2_2026W30_1B_0005_3D2_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D2...`
     - `level2_2026W30_1B_0005_3D3_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D3...`
     - `level2_2026W30_1B_0005_3D4_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D4...`
     - `level2_2026W30_1B_0005_3D5_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D5...`
     - `level2_2026W30_1B_0005_3D6_spx_l2b-v27-2026-222.fits`, `level2_2026W30_1B_0005_4D6...`
3. **Pointing 0006 (18 missing products):**
   - Dithers 2, 3 & 4 across all detectors D1–D6 (18 total files missing).

---

## 3. Storage Safety Gate & Acquisition Budget

- **Target Path:** `c:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X`
- **Total Disk Capacity:** `395.20 GB`
- **Current Used Space:** `181.92 GB`
- **Available Free Space:** `213.29 GB`
- **Safety Gate Rule:** Enforces required acquisition volume + minimum $5.0\,\text{GB}$ margin.
- **5-Pointing Expected Volume:** $120 \times 62.8\,\text{MB} \approx 7.54\,\text{GB}$.
- **Storage Gate Result:** **`PASS`** (Free space $213.29\,\text{GB} \gg 12.54\,\text{GB}$ requirement).

---

## 4. Stage B & C — Product Ingestion & Completeness Classification

### 4.1 Ingestion Architecture
To prevent dataset corruption:
1. All newly validated pilot files are isolated in `data/spherex/multipointing_pilot/level2/`.
2. Temporary downloads are staged with `.part` extensions.
3. Every file undergoes atomic SHA-256 computation before promotion.
4. Historical benchmark directory `data/spherex/qr3/level2/` is preserved untouched.

### 4.2 Product Classification Breakdown (120 Total Products)

| Classification | Count | Description |
| :--- | :---: | :--- |
| **`PRESENT_AND_VERIFIED`** | **8** | Local QR3 Level-2 files verified, checksummed, and promoted to pilot directory. |
| **`ARCHIVE_VERIFIED_PENDING_DOWNLOAD`** | **40** | Pointings 0001 & 0002 remote D2–D6 files verified on archive; pending network download queue. |
| **`HALTED_INCOMPLETE_COVERAGE`** | **41** | Remote files present for P0004 (23), P0005 (12), P0006 (6) whose acquisition was halted due to missing dithers. |
| **`MISSING_FROM_ARCHIVE`** | **31** | Products confirmed absent from NASA IRSA S3 bucket for planning period `2026W30_1B`. |
| **`DOWNLOAD_FAILED`** | **0** | Zero corrupt or failed downloads. |
| **Total** | **120** | Full 5-pointing pilot cohort accounted for. |

---

## 5. Stage D — Scientific FITS & HDU Validation

All 8 verified local products in the multi-pointing pilot directory were subjected to deep Astropy inspection using `ScientificFITSValidator`:

### 5.1 Verified Products Inventory

| Pointing | Dither | Detector | Filename | Size (Bytes) | SHA-256 | HDU Count | WCS Status | Variance Status | Overall Status |
| :---: | :---: | :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| `0001` | 1 | D1 | `level2_..._0001_1D1_...` | 65,851,200 | `ba5262e965b35e617283d7f772f5551966237ffb191de276a35dc07201dd092d` | 7 | VALID | VALID | **PASS** |
| `0001` | 2 | D1 | `level2_..._0001_2D1_...` | 66,150,720 | `8dc69024d51c5bc258f6dfb7f2c529808efe31df7d50de80e1ad35e96df999b9` | 7 | VALID | VALID | **PASS** |
| `0001` | 3 | D1 | `level2_..._0001_3D1_...` | 66,381,120 | `9e7872cc3747e9f0411c76dc0133ac57a448a4241eb6b608530234dc3ce0229d` | 7 | VALID | VALID | **PASS** |
| `0001` | 4 | D1 | `level2_..._0001_4D1_...` | 65,897,280 | `5a92040667f2ccc8dcd085652a9eed7b1cdb9068475dc4c5bffe7b2920bcf19c` | 7 | VALID | VALID | **PASS** |
| `0002` | 1 | D1 | `level2_..._0002_1D1_...` | 65,776,320 | `bb12de7777a4a0f752f4a1f0d325148b982fd8d395d555dfe76eed71104ed721` | 7 | VALID | VALID | **PASS** |
| `0002` | 2 | D1 | `level2_..._0002_2D1_...` | 65,891,520 | `bfecd4c9c3cd7b5abc70cb85437a9e1f7f2081c8b591e84273213ff6dedae1e4` | 7 | VALID | VALID | **PASS** |
| `0002` | 3 | D1 | `level2_..._0002_3D1_...` | 65,911,680 | `8552eb158c20f590d3af1b605de1c4db134ae8ad2ee9b8baa19c4884aa3889fb` | 7 | VALID | VALID | **PASS** |
| `0002` | 4 | D1 | `level2_..._0002_4D1_...` | 66,127,680 | `b8f399d297111ad8990fda7654d18efd6d7bb6e49b94e94a106851291af576d2` | 7 | VALID | VALID | **PASS** |

### 5.2 Scientific Extension Integrity
Every verified file complies with the following scientific standards:
- **HDU 0 (PRIMARY):** Contains valid `OBSID` (`2026W30_1B_0001_*`, `2026W30_1B_0002_*`), `TIMESYS = 'UTC'`, and `RADESYS = 'ICRS'`.
- **HDU 1 (IMAGE):** Conforms to dimensions $(2040, 2040)$, celestial WCS (`RA---TAN`, `DEC--TAN`), pixel scale $6.16''/\text{px}$, and effective exposure time $115.118\,\text{s}$.
- **HDU 2 (FLAGS):** Integer data quality bitmasks, finite and non-empty.
- **HDU 3 (VARIANCE):** Strictly positive, finite values (no non-physical or negative variance values).
- **HDU 4 (ZODI):** Estimated physical zodiacal foreground array in surface brightness units.
- **HDU 5 (EPSF):** Effective PSF array with 441 spatial bins ($21 \times 21$ grid across array).
- **HDU 6 (WCS-WAVE):** Linear-variable wavelength dispersion calibration mapping pixel coordinates to spectral channels ($0.75 - 0.98\,\mu\text{m}$).

---

## 6. Acquisition Test Suite Execution Results

A dedicated unit test suite (`tests/test_multipointing_acquisition_pilot.py`) was implemented to rigorously test all 10 edge cases:

```
tests/test_multipointing_acquisition_pilot.py::test_checksum_mismatch_detection PASSED   [ 10%]
tests/test_multipointing_acquisition_pilot.py::test_incomplete_download_recovery PASSED  [ 20%]
tests/test_multipointing_acquisition_pilot.py::test_duplicate_file_handling PASSED       [ 30%]
tests/test_multipointing_acquisition_pilot.py::test_fits_corruption_detection PASSED    [ 40%]
tests/test_multipointing_acquisition_pilot.py::test_missing_hdu_detection PASSED        [ 50%]
tests/test_multipointing_acquisition_pilot.py::test_incorrect_detector_metadata PASSED  [ 60%]
tests/test_multipointing_acquisition_pilot.py::test_invalid_wcs PASSED                  [ 70%]
tests/test_multipointing_acquisition_pilot.py::test_missing_or_invalid_variance PASSED  [ 80%]
tests/test_multipointing_acquisition_pilot.py::test_incorrect_pointing_identity PASSED [ 90%]
tests/test_multipointing_acquisition_pilot.py::test_safe_abort_on_insufficient_disk_space PASSED [100%]

============================= 10 passed in 1.53s ==============================
```

**Full Repository Regression Suite:**  
`64 / 64 passed` across all test modules in `25.62s`.

---

## 7. Protected Asset Hash Verification

All authoritative project assets were re-verified against their immutable hashes:

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

## 8. Unresolved Scientific Risks & Recommendations for Governance

1. **Upstream Archive Dropouts in SPHEREx QR3:**  
   The discovery that 3 out of 5 candidate pointings in planning period `2026W30_1B` suffer from missing dithers confirms that the SPHEREx Quick Release 3 archive has significant dither dropout rates. Pointings cannot be assumed to possess 24 products without explicit S3 key reconciliation.
2. **Bandwidth & Mass Download Constraint:**  
   Live testing confirmed a sustained download speed of $\sim 30 - 45\,\text{KB/s}$ from the NASA IRSA S3 endpoint to the current execution host, meaning downloading 40 products requires multi-hour batch execution.
3. **Candidate Pointing Substitution:**  
   Because Pointings 0004, 0005, and 0006 are incomplete in `2026W30_1B`, subsequent planning periods (`2026W30_2A` or `2026W31_1B`) or reserve pointings (`0007`, `0008`) must be audited to select substitution pointings that possess full 24/24 product sets prior to launching benchmark trials.

