# SPECTRA-X / F1 — Phase 3, Task 1.2B: Multi-Pointing Spectral Extraction & Catalog Assembly Report

**Task Identifier:** `SPECTRA_TASK_1_2B`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Timestamp:** 2026-11-07T03:29:13Z  
**Execution Mode:** Controlled Data Extraction Only (Strict Governance Boundary)  
**Governance Basis:** Explicitly Authorized by Project Owner  
**Module Audited:** SPECTRA — 102-Channel Infrared Spectral Anomaly Detection Engine  

---

## 1. Executive Summary

Task 1.2B executed the full scientific data engineering and provenance-controlled multi-pointing spectral extraction across all **120 genuine SPHEREx Level-2 science FITS files** acquired during Task 1.1M (`data/spherex/multipointing_pilot/level2/`), spanning five distinct pointings: `0001`, `0008` (Calibration Cohort), and `0002`, `0009`, `0010` (Blind Evaluation Cohort).

### Key Execution Highlights

1. **Complete File Processing Without Skipping:** All 120 expected Level-2 FITS files (24 per pointing across 6 detectors $\times$ 4 dither visits) were verified, ingested, and processed. Zero files were missing, rejected, or corrupted.
2. **Exhaustive Photometric Yield:** A total of **184,888 valid photometric measurements** were extracted from **37,500 catalog sources** (7,500 sources per pointing from `data/processed/pilot_catalogues/`).
3. **Usable Observational Sky Coverage:** Exactly **26,455 sources (70.5%)** possess confirmed observational coverage within the Level-2 active sensor footprints. The remaining 11,045 sources fall legitimately outside the detector footprints during single telescope pointings.
4. **Physical Optical Dichroic Pairing Confirmed:** Exactly **26,050 sources** demonstrate simultaneous multi-detector observations across complementary short- and long-wavelength focal plane arrays (D1+D4, D2+D5, D3+D6), providing broad multi-octave physical spectral baselines (0.74–5.02 µm) with up to 8 valid spectral channels per source.
5. **Strict Partition Isolation (Zero Contamination):** Spatial separation and cross-matching between Calibration pointings (`0001`, `0008`, $N=15,000$) and Blind Evaluation pointings (`0002`, `0009`, `0010`, $N=22,500$) confirmed **0 overlapping source IDs** and **zero partition leakage**.
6. **Immutable Governance Preserved:** The frozen candidate checkpoint `checkpoints/spectra_masked_ae_v2.pt` was confirmed byte-for-byte immutable (`SHA-256: 6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938`). Zero model retraining, zero parameter tuning, zero threshold calibration, and zero forward evaluation against ground truth were performed.

---

## 2. Input FITS Inventory and SHA-256 Checksums

The extraction driver ingested and cryptographically hashed all 120 Level-2 science FITS products. Each file represents a calibrated science observation (`HDU 1 IMAGE`, `HDU 2 FLAGS`, `HDU 3 VARIANCE`) for a specific pointing, dither step ($1\dots4$), and detector ($D1\dots D6$).

### Table 2.1: Input FITS Cohort Inventory Breakdown

| Pointing | Partition Role | Dithers | Detectors | Files Count | Matrix Dimensions | Median Observation Date | Status |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `0001` | `CALIBRATION` | 1–4 | D1–D6 | 24 | 2048 $\times$ 2048 | 2026-07-22 | Verified |
| `0008` | `CALIBRATION` | 1–4 | D1–D6 | 24 | 2048 $\times$ 2048 | 2026-07-22 | Verified |
| `0002` | `EVALUATION` | 1–4 | D1–D6 | 24 | 2048 $\times$ 2048 | 2026-07-22 | Verified |
| `0009` | `EVALUATION` | 1–4 | D1–D6 | 24 | 2048 $\times$ 2048 | 2026-07-22 | Verified |
| `0010` | `EVALUATION` | 1–4 | D1–D6 | 24 | 2048 $\times$ 2048 | 2026-07-22 | Verified |
| **Total** | — | — | — | **120** | — | — | **100% Ingested** |

All 120 individual file SHA-256 hashes are recorded in the machine-readable extraction manifest:
`data/processed/spectra/phase3_multpointing_extraction_manifest_v1.json` (`input_inventory_summary.fits_files`).

---

## 3. Extraction Implementation Review

The extraction methodology reused the core astrometric and photometric engine established in `models/spectra/assemble_spectrum.py`, adapted to ingest multi-pointing directories via explicit generalized regular expressions:

$$\text{Pattern: } \texttt{level2\_2026W30\_1B\_(\textbackslash{}d\{4\})\_([1-4])D([1-6])\_spx\_l2b-v27-2026-222.fits}$$

### Key Photometric Parameters:
1. **Aperture Photometry:** Circular aperture radius $r = 3.0\text{ pixels}$ ($3.0''$), circular background annulus with inner radius $r_{\text{in}} = 6.0\text{ pixels}$ and outer radius $r_{\text{out}} = 10.0\text{ pixels}$.
2. **Defect Bitmask Screening:** Fatal flag bitmask applied to HDU 2 (FLAGS):
   $$\text{FATAL\_FLAG\_MASK} = (1 \ll 0) \mid (1 \ll 1) \mid (1 \ll 2) \mid (1 \ll 5) \mid (1 \ll 6) \mid (1 \ll 9) = 615$$
   Screening triggers rejection if the source centroid pixel contains fatal defect flags (transients, saturation, non-functional pixels, missing data) or if valid aperture area fraction falls below 70% ($\text{area} < 0.70 \times \pi r^2$).
3. **Local Background Subtraction:**
   $$F_{\text{net}} = F_{\text{raw}} - \left( B_{\text{ann}} \times A_{\text{ap}} \right)$$
   where $B_{\text{ann}}$ is the robust median background flux across unflagged annulus pixels.
4. **Rigorous Variance Propagation:**
   Variance is propagated from the calibrated Level-2 VARIANCE HDU combined with annulus background variance:
   $$\sigma_{\text{tot}}^2 = \sigma_{\text{ap}}^2 + A_{\text{ap}}^2 \left( \frac{\sigma_{\text{bkg}}^2}{\max(1, A_{\text{ann}})} \right)$$
   $$\sigma_{F} = \sqrt{\max(\sigma_{\text{tot}}^2, 10^{-10})}$$
5. **Multi-Dither Inverse-Variance Weighting:**
   When multiple dither visits observe the exact same spectral channel $c$:
   $$w_i = \frac{1}{\sigma_i^2}, \quad \bar{F}_c = \frac{\sum w_i F_i}{\sum w_i}, \quad \sigma_c = \frac{1}{\sqrt{\sum w_i}}$$

---

## 4. SPHEREx Data Provenance

Observation provenance is fully traceable from raw celestial coordinates through detector coordinates to the 102-channel SED table:

- **Official WCS Spectral Mapping:** Continuous 2D pixel-to-wavelength solutions were ingested from official QR3 calibration arrays:
  - `data/spherex/qr3/calibration/spectral_wcs_D1_spx_cal-swcs-v5-2026-191.fits`
  - `data/spherex/qr3/calibration/spectral_wcs_D2_spx_cal-swcs-v5-2026-191.fits`
  - `data/spherex/qr3/calibration/spectral_wcs_D3_spx_cal-swcs-v5-2026-191.fits`
  - `data/spherex/qr3/calibration/spectral_wcs_D4_spx_cal-swcs-v5-2026-191.fits`
  - `data/spherex/qr3/calibration/spectral_wcs_D5_spx_cal-swcs-v5-2026-191.fits`
  - `data/spherex/qr3/calibration/spectral_wcs_D6_spx_cal-swcs-v5-2026-191.fits`
- **Channel Calibration Standard:** All channel center wavelengths, wavelength bounds ($[\lambda_{\min}, \lambda_{\max}]$), and nominal bandwidths match the official 102-channel specification:
  - `data/spherex/qr3/calibration/spectral_channels_spx_cal-sch-v2-2026-229.fits`
- **Provenance Strings:** Every assembled spectrum in `phase3_multpointing_spectra_v1.csv` retains explicit string records for `detector_provenance` (e.g. `D1,D4`) and `observation_provenance` (comma-separated list of Level-2 OBSIDs).

---

## 5. 102-Channel and Detector Mapping Verification

Every detector's continuous wavelength solution was matched to its corresponding subset of the 102 channels:

### Table 5.1: Detector Channel Mapping and Wavelength Range

| Detector | Channel Index Range | Nominal Bandpass ($\mu\text{m}$) | Observed Minimum ($\mu\text{m}$) | Observed Maximum ($\mu\text{m}$) | Resolving Power $R$ |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **D1** | Channels 0 – 16 (17 ch) | 0.75 – 1.11 | 0.73703 | 1.12134 | $R \approx 41$ |
| **D2** | Channels 17 – 33 (17 ch) | 1.11 – 1.64 | 1.08943 | 1.66082 | $R \approx 41$ |
| **D3** | Channels 34 – 50 (17 ch) | 1.64 – 2.42 | 1.62059 | 2.42768 | $R \approx 41$ |
| **D4** | Channels 51 – 67 (17 ch) | 2.42 – 3.82 | 2.40146 | 3.84812 | $R \approx 35$ |
| **D5** | Channels 68 – 84 (17 ch) | 3.82 – 4.42 | 3.80315 | 4.43673 | $R \approx 110$ |
| **D6** | Channels 85 – 101 (17 ch) | 4.42 – 5.00 | 4.40505 | 5.01931 | $R \approx 130$ |

All observed wavelengths strictly fall within the official channel boundaries. Zero invalid wavelength solutions, out-of-range channel indices, or negative channel indices were encountered.

---

## 6. Multi-Pointing Extraction Results

### Table 6.1: Pointing-by-Pointing Extraction Statistics

| Pointing | Role | Total Catalog Sources | Observed Sources | Zero Coverage | Valid Measurements | Mean Observed Channels | Max Channels | Rejections (Flags / Edges / Area) |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `0001` | `CALIBRATION` | 7,500 | 3,398 (45.3%) | 4,102 | 23,597 | 3.11 | 8 | 275 / 2,322 / 10 |
| `0008` | `CALIBRATION` | 7,500 | 5,979 (79.7%) | 1,521 | 38,438 | 4.94 | 8 | 575 / 1,599 / 15 |
| `0002` | `EVALUATION` | 7,500 | 5,772 (77.0%) | 1,728 | 45,212 | 5.95 | 8 | 478 / 376 / 17 |
| `0009` | `EVALUATION` | 7,500 | 5,749 (76.7%) | 1,751 | 38,913 | 4.97 | 8 | 502 / 1,079 / 20 |
| `0010` | `EVALUATION` | 7,500 | 5,557 (74.1%) | 1,943 | 38,728 | 5.09 | 8 | 566 / 1,479 / 44 |
| **Total** | — | **37,500** | **26,455 (70.5%)** | **11,045** | **184,888** | **4.81** | **8** | **2,396 / 6,855 / 106** |

### Table 6.2: Detector Measurement Yield Across All Pointings

| Detector | FITS Files | Unique Sources Observed | Valid Photometric Measurements | Observed Wavelength Range ($\mu\text{m}$) | Rejected Centroid Flags |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **D1** | 20 | 9,030 | 31,739 | 0.73703 – 1.12134 | 471 |
| **D2** | 20 | 9,943 | 35,203 | 1.08943 – 1.66082 | 487 |
| **D3** | 20 | 7,170 | 25,188 | 1.62059 – 2.42768 | 412 |
| **D4** | 20 | 9,100 | 32,003 | 2.40146 – 3.84812 | 439 |
| **D5** | 20 | 10,002 | 35,313 | 3.80315 – 4.43673 | 311 |
| **D6** | 20 | 7,260 | 25,442 | 4.40505 – 5.01931 | 276 |
| **Total** | **120** | — | **184,888** | **0.73703 – 5.01931** | **2,396** |

---

## 7. Source Matching and Duplicate Governance

1. **Astrometric Precision:** Forced aperture photometry used the high-precision Gaia DR3 / 2MASS coordinates directly from `data/processed/pilot_catalogues/pointing_{ptg}_source_catalogue.csv`. Centroids were mapped onto FITS coordinates using full TAN-SIP / standard astrometric WCS solutions.
2. **Cross-Detector Association:** Detectors within a pointing observe physically separated sky footprints, with the exception of the optical dichroic pairs (D1/D4, D2/D5, D3/D6). Matching across detectors was strictly coordinate-based ($\Delta \theta \le 2.0''$), never based on detector array indices.
3. **No Double Counting:** Dithered observations of the same source falling into the same channel were combined via inverse-variance weighting ($\sum_{i=1}^k w_i = \sigma_{\text{comb}}^{-2}$). Exactly 4,462 repeated channel visits across the 5 pointings were combined without double-counting degrees of freedom.
4. **Pointing Disjointness:** Sources from different pointings were strictly isolated by their unique `source_id` and pointing identifier.

---

## 8. Calibration/Evaluation Partition Isolation

To maintain strict scientific integrity, the calibration and evaluation cohorts were processed with rigorous separation:

### Table 8.1: Partition Isolation Audit

| Attribute | Calibration Cohort | Blind Evaluation Cohort | Isolation Verification |
|:---|:---:|:---:|:---:|
| **Pointings** | `0001`, `0008` | `0002`, `0009`, `0010` | Disjoint sets |
| **Level-2 FITS Files** | 48 files | 72 files | 100% separate paths |
| **Total Catalog Sources** | 15,000 | 22,500 | Sum = 37,500 |
| **Sources with Observed Coverage** | 9,377 (62.5%) | 17,078 (75.9%) | Sum = 26,455 |
| **Multi-Detector Sources** | 9,160 | 16,890 | Sum = 26,050 |
| **Single-Detector Sources** | 217 | 188 | Sum = 405 |
| **Zero-Coverage Sources** | 5,623 | 5,422 | Sum = 11,045 |
| **Valid Photometric Measurements** | 62,035 | 122,853 | Sum = 184,888 |
| **Source ID Overlap Count** | **0** | **0** | **Strict Zero Leakage** |
| **Spatial Overlap Detected** | **False** | **False** | **Independent Fields** |

---

## 9. Spectral Coverage and Sparsity Analysis

As identified in Task 1.2A, SPHEREx single-visit observations produce sparse SED vectors because each detector focal plane array observes an instantaneous narrow bandpass.

### Table 9.1: Valid Channel Distribution (Sparsity Profile)

| Valid Channels Count | Number of Sources | Percentage of Total Catalog | Scientific Status |
|:---:|:---:|:---:|:---|
| **0 Channels** | 11,045 | 29.45% | Outside sensor field of view during pointing |
| **1 Channel** | 248 | 0.66% | Single-detector boundary fringe detection |
| **2 Channels** | 2,057 | 5.49% | Partial dither or edge-fringe overlap |
| **3 – 4 Channels** | 2,101 | 5.60% | Complete 4-dither single-detector SED |
| **5 – 10 Channels (5–8 ch)** | **22,049** | **58.80%** | **Simultaneous Dichroic Multi-Detector SED (D1+D4, D2+D5, D3+D6)** |
| **> 10 Channels** | 0 | 0.00% | Single telescope pointing cannot span $>2$ detectors |
| **Total** | **37,500** | **100.00%** | — |

### Physical Interpretation of Dichroic Multi-Detector Coverage

In contrast to initial concerns that single-pointing data would only yield 4 channels from a single detector:
- The SPHEREx optical bench houses two focal plane assemblies fed by a dichroic beamsplitter:
  - **Focal Plane 1 (NIR):** Detectors D1 (0.75–1.11 $\mu\text{m}$), D2 (1.11–1.64 $\mu\text{m}$), D3 (1.64–2.42 $\mu\text{m}$).
  - **Focal Plane 2 (MWIR):** Detectors D4 (2.42–3.82 $\mu\text{m}$), D5 (3.82–4.42 $\mu\text{m}$), D6 (4.42–5.00 $\mu\text{m}$).
- D1 and D4 share the same sky field of view simultaneously.
- D2 and D5 share the same sky field of view simultaneously.
- D3 and D6 share the same sky field of view simultaneously.
- As a result, **22,049 sources (83.3% of all observed sources)** possess between 5 and 8 valid channels spanning both the NIR and MWIR regimes, providing true multi-octave physical color baselines.

---

## 10. Uncertainty and Quality-Flag Audit

1. **Systematic Error Floor:** The documented 1.93% ($\sigma_{\text{sys}} = 0.0193$) systematic error floor was tracked as an extraction metadata parameter and was not added redundantly to the Level-2 FITS variance arrays.
2. **Fatal Quality Flags:** Centroid defect screening successfully rejected 2,396 contaminated evaluations where bad pixels, saturation, or telemetry dropouts affected the aperture centroid.
3. **Edge Proximity Screening:** 6,855 source evaluations within 15 pixels of the detector frame edges were excluded to avoid truncated aperture profiles.
4. **Aperture Area Screening:** 106 evaluations with $<70\%$ valid aperture area due to intersecting bad pixels were rejected.
5. **No NaN Flux Leakage:** Zero NaN or infinite values were allowed to enter valid-channel records; unobserved or rejected channels remain explicitly masked with `valid_channel_mask = False` and `flux = None`.

---

## 11. Extraction Test Results

The validation test suite [`tests/test_spectra_task_1_2b_extraction.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_spectra_task_1_2b_extraction.py) was executed to verify all data products:

```text
tests/test_spectra_task_1_2b_extraction.py::test_frozen_assets_unmodified PASSED [ 12%]
tests/test_spectra_task_1_2b_extraction.py::test_manifest_integrity PASSED [ 25%]
tests/test_spectra_task_1_2b_extraction.py::test_output_files_exist_and_hashes_match PASSED [ 37%]
tests/test_spectra_task_1_2b_extraction.py::test_spectra_csv_schema_and_counts PASSED [ 50%]
tests/test_spectra_task_1_2b_extraction.py::test_coverage_csv_schema_and_counts PASSED [ 62%]
tests/test_spectra_task_1_2b_extraction.py::test_partition_isolation PASSED [ 75%]
tests/test_spectra_task_1_2b_extraction.py::test_sed_vector_102ch_consistency PASSED [ 87%]
tests/test_spectra_task_1_2b_extraction.py::test_detector_coverage_physical_dichroic PASSED [100%]
============================== 8 passed in 2.11s ==============================
```

Additionally, the existing benchmark test suite [`tests/test_spectra_v2_mask_benchmark.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_spectra_v2_mask_benchmark.py) passed 100% (4/4 tests).

---

## 12. Scientific Limitations

1. **Single-Visit Channel Sparsity:** While 26,050 sources have multi-detector dichroic coverage (5–8 channels), no source in a single telescope pointing possesses observations in all 6 detectors simultaneously due to the boresight separation of the three optical fields ($\sim 3.8^\circ$ and $\sim 7.7^\circ$). Full 102-channel coverage will only be achieved in all-sky survey coadds.
2. **Median Normalization Degeneracy for Sparse Sources:** For the 248 sources with only 1 valid channel, median normalization trivially yields unity ($1.0$), eliminating amplitude information. For the 2,057 sources with 2 valid channels, median normalization creates a simple two-point slope.
3. **Threshold Extrapolation Prohibition:** The thresholds derived during Phase 2 on Pointing 0003 cannot be blindly applied to the multi-pointing cohort without the calibration step scheduled for Task 1.2C.

---

## 13. Final Governance Verdict

| Governance Audit Area | Verdict | Detailed Audit Finding |
|:---|:---:|:---|
| **Input Integrity** | **PASS** | All 120 Level-2 FITS files ingested, verified, and hashed; 0 missing or corrupted. |
| **Extraction Correctness** | **PASS** | Forced aperture photometry executed with defect screening and variance propagation. |
| **Data Provenance** | **PASS** | Complete tracking of Level-2 OBSID, dither ID, detector ID, MJD, and WCS calibration. |
| **Detector Coverage** | **PASS** | All six detectors (D1–D6) confirmed with $>25,000$ valid measurements each. |
| **102-Channel Integrity** | **PASS** | Continuous WCS mapped to 102 official channels; unobserved channels explicitly masked. |
| **Source Matching** | **PASS** | Astrometric coordinate cross-matching verified; 0 cross-pointing or duplicate collisions. |
| **Partition Isolation** | **PASS** | Exactly 0 overlapping sources between Calibration and Evaluation cohorts; zero leakage. |
| **Output Reproducibility** | **PASS** | Output schemas verified; all unit and integration test assertions passed. |

### Overall Task Verdict:
$$\mathbf{PASS}\text{ — DATA EXTRACTION \& CATALOG ASSEMBLY VALIDATED}$$
$$\text{(SPECTRA MODEL CERTIFICATION DEFERRED PENDING CONTROLLED EVALUATION)}$$

---

## 14. Recommended Next Task

Proceed to **Phase 3, Task 1.2C: Multi-Pointing Null-Control Calibration & Threshold Selection**.

In Task 1.2C, the Calibration Cohort (`P0001`, `P0008`, $N=9,377$ observed sources, 62,035 measurements) will be used to:
1. Compute the empirical reconstruction error distribution of uncorrupted science sources under the frozen SPECTRA V2 model.
2. Establish formal operating thresholds at false positive rates $\alpha \in \{0.01, 0.05\}$.
3. Audit the impact of sparse-spectrum median normalization on anomaly scoring across dichroic pairs.
4. Freeze all operating thresholds prior to touching the Blind Evaluation Cohort (`P0002`, `P0009`, `P0010`) in Task 1.2D.

