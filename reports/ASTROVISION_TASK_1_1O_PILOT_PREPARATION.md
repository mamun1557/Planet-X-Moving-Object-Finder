# SPECTRA-X / F1 — PHASE 3, TASK 1.1O REPORT
## Five-Pointing Controlled Pilot Benchmark Preparation, Source Catalogue Generation & Partition Governance

**Engineering Roles:** Principal Astronomical Data Scientist, SPHEREx Scientific Validation Engineer, Cross-Matching Specialist & Benchmark Governance Architect  
**Task Type:** Implementation & Benchmark Protocol Preparation  
**Parent Framework:** Task 1.1M Ingestion Pilot & Task 1.1N Independent Dataset Audit  
**Authoritative Cohort:** Pointings `0001`, `0002`, `0008`, `0009`, `0010` (120 FITS products)  
**Pipeline Build:** `l2b-v27-2026-222` | **Planning Period:** `2026W30_1B`  
**ASTROVISION Scientific Status:** `FAIL — NOT CERTIFIED`  
**Benchmark Campaign Execution Status:** `STRICTLY BLOCKED`  

---

## 1. Executive Summary & Verdict

Under Phase 3, Task 1.1O, the data foundation and governance architecture for the five-pointing ASTROVISION controlled pilot benchmark have been fully implemented, rigorously tested, and locked.

Key achievements delivered:
1. **Authoritative Input Verification:** All 120 QR3 Level-2 FITS products across the five target pointings (`0001`, `0002`, `0008`, `0009`, `0010`) were verified against the Task 1.1M ingestion manifest and Task 1.1N audit deliverables. All 16 historical protected assets match their SHA-256 signatures with zero mutations.
2. **Multi-Pointing Astrometric Catalogues:** Extracted 7,500 Gaia DR3 sources for each pointing (37,500 total) covering all 3 detector field centers. Propagated proper motions to the SPHEREx observation epoch ($2026.5496$, MJD 61241.018) with $98.4\% - 99.3\%$ coverage. Cross-matched with 2MASS PSC/XSC ($62.2\% - 81.9\%$ counterpart recovery).
3. **Scientifically Defensible Source Masks:** Developed spatial masks classifying sources into: `RELIABLE_ISOLATED_POINT_SOURCE`, `BLENDED_CROWDED`, `SATURATED_OR_CONTAMINATED`, `EXTENDED`, and `UNCERTAIN_OR_LOW_QUALITY`. Empirically verified detector usable area fractions ($84.6\% - 90.3\%$, mean $87.7\%$) across all 24 exposures per pointing.
4. **Frozen Five-Partition Allocation:** Created a deterministic 2,500-trial manifest (`seed = 42`) strictly isolating Calibration (`0001`, `0008`) from Evaluation (`0002`, `0009`, `0010`), guaranteeing zero cross-boundary spatial leakage.
5. **Statistical Limitations Formulated:** Explicitly documented calibration feasibility and the exact cluster-bootstrap degeneracy ($P_{\text{eval}} = 3, G_{\text{eval}} = 3$, yielding only 10 unique multisets). Refuted any claims of guaranteed narrow confidence intervals.
6. **Controlled Pilot Protocol v3.0:** Authored and frozen `reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md`.
7. **Comprehensive Verification Suite:** Added 10 targeted unit tests in `tests/test_pilot_preparation_and_partitioning.py`. Executed the entire repository test suite (**74/74 passed**, 0 failures).

```
========================================================================================
TASK 1.1O VERDICT:
PASS — PILOT PREPARATION COMPLETE; READY FOR INDEPENDENT AUDIT
========================================================================================
```

> [!CAUTION]
> **Governance Notice:** A `PASS` verdict authorizes **ONLY** a subsequent independent scientific audit of this preparation. It does NOT authorize model inference, injection trials, campaign execution, model retraining, or ASTROVISION scientific certification.

---

## 2. Independent Input and Provenance Verification (Task A)

All authoritative files were audited and verified prior to any processing:
- **Authoritative Dataset:** 120 FITS products in `data/spherex/multipointing_pilot/level2/{0001,0002,0008,0009,0010}/`
- **Ingestion Manifest:** `reports/manifests/astrovision_multipointing_ingestion_manifest.json` (`SHA-256: 0e2b4c69dd6cfb9aa132b8f8d5eb77e0d3e278c3e286de6a8ec1aa690eeb0a33`)
- **Independent Audit Report:** `reports/ASTROVISION_TASK_1_1N_INDEPENDENT_DATASET_AUDIT.md` (`SHA-256: a580e0452fa63a4da95e7d6b4849057fba7723badbad6bc0ba36fba87c11f9ed`)
- **HDU Layout:** Verified empty primary stub HDU 0 ($NAXIS=0$) and 293 metadata cards in HDU 1 (`IMAGE`).
- **ePSF Binning Layout:** Confirmed D1, D2, D4, D5, D6 use $21 \times 21 = 441$ bins; D3 uses authentic $11 \times 41 = 451$ bins.

### Non-Mutation Audit of 16 Historical Protected Assets:
| Protected Asset Path | Expected SHA-256 Signature | Actual SHA-256 Signature | Status |
|---|---|---|---|
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5...` | `f65c0f139a5e1fa5...` | **MATCH** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe...` | `ce1416bb0d5fcffe...` | **MATCH** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0...` | `339d5c58a12122f0...` | **MATCH** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f0131...` | `22ecaf448e1f0131...` | **MATCH** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f0...` | `5f8fd6bc1313b8f0...` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d...` | `dd42430dbff8849d...` | **MATCH** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece...` | `5cb9888f3ce42ece...` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md` | `db9aba61098b520d...` | `db9aba61098b520d...` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md` | `d3c529c951803023...` | `d3c529c951803023...` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md` | `13b0f22088067a81...` | `13b0f22088067a81...` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` | `764631f2abaf8ca8...` | `764631f2abaf8ca8...` | **MATCH** |
| `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md` | `5c26abb6da8f72b3...` | `5c26abb6da8f72b3...` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md` | `22c9e464c30b2204...` | `22c9e464c30b2204...` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1H_REMEDIATION.md` | `950e361cccdb4c34...` | `950e361cccdb4c34...` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md` | `74653153b17f110b...` | `74653153b17f110b...` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1I_INDEPENDENT_REAUDIT.md` | `7db57a54de5d9346...` | `7db57a54de5d9346...` | **MATCH** |

---

## 3. Gaia DR3 and 2MASS Cross-Matching (Task B)

### 3.1 Sky Footprints & Multi-Detector Focal Plane Geometry
SPHEREx features two optical channels separated by a dichroic:
- Channel 1 (D1, D2, D3 for 0.75 – 2.42 µm)
- Channel 2 (D4, D5, D6 for 2.42 – 5.0 µm)
Consequently, detectors (D1, D4) share the same sky field, (D2, D5) share the adjacent field, and (D3, D6) share the third field.

Each pointing's focal-plane footprint was covered by 3 cone queries ($R = 2.50^\circ$, covering the full $3.49^\circ \times 3.49^\circ$ detector field plus edge margin) centered on:
- Field 1 (D1/D4)
- Field 2 (D2/D5)
- Field 3 (D3/D6)

### 3.2 Astrometric Epoch Propagation
- SPHEREx Observation Epoch: $T_{\text{SPX}} = 2026.5496$ (MJD 61241.018)
- Gaia DR3 Reference Epoch: $T_{\text{Gaia}} = 2016.0$
- Baseline: $\Delta t = 10.5496$ years
- Coordinate transformation:
  $$\Delta\alpha = \frac{\mu_{\alpha*} \times 10^{-3} \times \Delta t}{3600 \times \cos\delta}, \quad \Delta\delta = \frac{\mu_\delta \times 10^{-3} \times \Delta t}{3600}$$
  $$\alpha_{2026.5} = (\alpha + \Delta\alpha) \pmod{360}, \quad \delta_{2026.5} = \delta + \Delta\delta$$

### 3.3 Cross-Match & Astrometric Recovery Statistics:
| Pointing | Total Gaia Sources | PM Propagated Count (%) | 2MASS Matched Count (%) | Mean $G$ Mag | Median Nearest Neighbor |
|---|---|---|---|---|---|
| `0001` | 7,500 | 7,450 (99.3%) | 4,803 (64.0%) | 17.58 mag | 43.12 arcsec |
| `0002` | 7,500 | 7,443 (99.2%) | 4,665 (62.2%) | 17.72 mag | 28.54 arcsec |
| `0008` | 7,500 | 7,381 (98.4%) | 6,141 (81.9%) | 17.29 mag | 36.19 arcsec |
| `0009` | 7,500 | 7,442 (99.2%) | 5,214 (69.5%) | 17.91 mag | 21.05 arcsec |
| `0010` | 7,500 | 7,435 (99.1%) | 5,615 (74.9%) | 17.65 mag | 33.72 arcsec |

All source catalogues are preserved under `data/processed/pilot_catalogues/pointing_{0001,0002,0008,0009,0010}_source_catalogue.csv`.

---

## 4. Scientifically Defensible Source Masks (Task C)

### 4.1 Mask Geometry & Classification Rules
Each source is evaluated for crowding, saturation, extent, and astrometric quality:
- `RELIABLE_ISOLATED_POINT_SOURCE`: $G \in [13.0, 19.5]$, $d_{\text{nn}} > 12.0''$ (no blend within 2 SPHEREx pixels), $\text{RUWE} \le 1.40$, astrometric excess noise $\le 2.0$, distance to nearest saturated star $> 185''$.
- `BLENDED_CROWDED`: Nearest neighbor $d_{\text{nn}} \le 12.0''$ ($R_{\text{mask}} = 6$ pixels / $37.0''$).
- `SATURATED_OR_CONTAMINATED`: $G < 11.5$ mag ($R_{\text{mask}} = 30$ pixels / $184.7''$).
- `EXTENDED`: Astrometric excess noise $> 2.0$ or 2MASS extended source ($R_{\text{mask}} = 15$ pixels / $92.3''$).
- `UNCERTAIN_OR_LOW_QUALITY`: High astrometric noise ($\text{RUWE} > 1.40$), near detector margins, or $G > 19.5$.

### 4.2 Source Classification Breakdown by Pointing:
| Pointing | Isolated Point Sources | Blended/Crowded | Saturated/Contaminated | Extended Sources | Uncertain/Low Quality |
|---|---|---|---|---|---|
| `0001` | 5,685 | 813 | 38 | 107 | 857 |
| `0002` | 5,377 | 1,254 | 28 | 93 | 748 |
| `0008` | 5,695 | 556 | 97 | 149 | 1,003 |
| `0009` | 3,728 | 1,975 | 50 | 146 | 1,601 |
| `0010` | 4,736 | 1,174 | 67 | 156 | 1,367 |

### 4.3 Detector-Wise Mask Diagnostics Summary:
| Pointing | Evaluated Exposures | Usable Area Fraction Range | Mean Usable Fraction | Mean Source Density | Mean Sources on Detector |
|---|---|---|---|---|---|
| `0001` | 24 | 0.8711 – 0.9029 | **0.8887 (88.9%)** | 89.3 sources/deg² | 1,086.8 |
| `0002` | 24 | 0.8571 – 0.8928 | **0.8772 (87.7%)** | 157.8 sources/deg² | 1,920.0 |
| `0008` | 24 | 0.8565 – 0.8788 | **0.8714 (87.1%)** | 138.9 sources/deg² | 1,690.8 |
| `0009` | 24 | 0.8465 – 0.8856 | **0.8726 (87.3%)** | 138.6 sources/deg² | 1,687.0 |
| `0010` | 24 | 0.8594 – 0.8976 | **0.8742 (87.4%)** | 139.5 sources/deg² | 1,697.4 |

Diagnostics are preserved in `data/processed/pilot_masks/pointing_{0001,0002,0008,0009,0010}_mask_diagnostics.json`.

---

## 5. Formal Five-Partition Allocation (Task D)

The five-partition allocation is frozen in:
`reports/manifests/astrovision_five_partition_pilot_manifest.csv`  
**SHA-256:** `c1d83662b311f3f89efbe90f3c0ebd702c0ee58bcfae880dcd5d25e42eee0c0b`

### 5.1 Partition Breakdown & Trial Allocation:
| Partition Name | Target Role | Pointings Assigned | FITS Files | Total Trials | Trial IDs | Target SNR |
|---|---|---|---|---|---|---|
| `CALIBRATION_CONTROL` | Calibration | `0001`, `0008` | 48 | 500 | `PILOT_000001`–`PILOT_000500` | 0.0 (Null) |
| `CALIBRATION_INJECTION` | Calibration | `0001`, `0008` | 48 | 500 | `PILOT_000501`–`PILOT_001000` | 3.0–20.0 |
| `EVALUATION_CONTROL` | Evaluation | `0002`, `0009`, `0010` | 72 | 500 | `PILOT_001001`–`PILOT_001500` | 0.0 (Null) |
| `EVALUATION_POINT_SOURCE_INJECTION` | Evaluation | `0002`, `0009`, `0010` | 72 | 500 | `PILOT_001501`–`PILOT_002000` | 3.0–25.0 |
| `EVALUATION_EXTENDED_SOURCE_INJECTION` | Evaluation | `0002`, `0009`, `0010` | 72 | 500 | `PILOT_002001`–`PILOT_002500` | 3.0–25.0 |

### 5.2 Pointing-by-Partition Cross-Tabulation:
```
pointing                              0001  0002  0008  0009  0010  Total
partition                                                                
CALIBRATION_CONTROL                    260     0   240     0     0    500
CALIBRATION_INJECTION                  260     0   240     0     0    500
EVALUATION_CONTROL                       0   168     0   168   164    500
EVALUATION_EXTENDED_SOURCE_INJECTION     0   168     0   168   164    500
EVALUATION_POINT_SOURCE_INJECTION        0   168     0   168   164    500
Total                                  520   504   480   504   492   2500
```
- **Zero Cross-Boundary Leakage:** The intersection of Calibration pointings $\{0001, 0008\}$ and Evaluation pointings $\{0002, 0009, 0010\}$ is exactly $\emptyset$.
- **FITS File Disjointness:** 48 calibration FITS files $\cap$ 72 evaluation FITS files = $\emptyset$.
- **Dither Groupings:** All 4 dithers for each pointing exposure are preserved in identical partition families.

---

## 6. Calibration Feasibility & Statistical Limitations (Task E)

### 6.1 Calibration Support Assessment
- **Null Control Sample Size:** 500 calibration control cutouts across 48 calibration FITS files yields an average of $\sim 42$ independent control cutouts per detector.
- **Empirical Transfer Curves $\beta(\text{SNR}, \text{det})$:** 500 injection trials across 6 detectors yield $\sim 83$ trials per detector spanning SNR grid $[3.0, 5.0, 7.0, 10.0, 15.0, 20.0]$ ($\sim 14$ trials per SNR bin per detector).
- **Feasibility Verdict:** Sufficient for pilot-level threshold exploration and initial curve fitting, but lacks the high-density support ($> 200$ trials/det) required for flight-certified operational thresholds.

### 6.2 Strict Cluster-Bootstrap Degeneracy ($G_{\text{eval}} = 3$)
When evaluating performance across pointings, spatial correlation dictates clustering at the pointing level. Resampling $G_{\text{eval}} = 3$ clusters (`0002`, `0009`, `0010`) with replacement yields exactly:
$$N_{\text{multisets}} = \binom{G + G - 1}{G} = \binom{3 + 3 - 1}{3} = \binom{5}{3} = 10 \text{ unique bootstrap multisets}$$

Specifically:
1. $\{0002, 0002, 0002\}$
2. $\{0002, 0002, 0009\}$
3. $\{0002, 0002, 0010\}$
4. $\{0002, 0009, 0009\}$
5. $\{0002, 0009, 0010\}$
6. $\{0002, 0010, 0010\}$
7. $\{0009, 0009, 0009\}$
8. $\{0009, 0009, 0010\}$
9. $\{0009, 0010, 0010\}$
10. $\{0010, 0010, 0010\}$

> [!WARNING]
> **Definitive Finding:** A discrete set of 10 multisets cannot support asymptotic normality or arbitrarily narrow confidence intervals (e.g. AUROC CI half-width $\pm 0.03$). Any confidence interval derived from this pilot cohort will reflect coarse, step-like uncertainty. The benchmark protocol explicitly disclaims narrow confidence guarantees. Flight-level certification requires $G \ge 15-20$ independent pointings.

---

## 7. Versioned Benchmark Protocol v3.0 (Task F)

The complete benchmark rules are codified in:
`reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md`  
**SHA-256:** `77200d92421a3cd80b41fd8ba5f38d5e8dab7ce410cccd17e541bc447f44a1b2`

Key protocol mandates:
1. Historical threshold $\tau = 169.10$ is explicitly deprecated and forbidden from evaluation scoring.
2. Detector thresholds $\tau_d$ must be derived exclusively from Partition 1.
3. Transfer curves $\beta_d(\text{SNR})$ must be fitted exclusively on Partition 2.
4. Final performance metrics (AUROC, AUPRC, $C_{50}, C_{90}$, standardized precision) must be evaluated exclusively on Partitions 3, 4, 5.
5. All rejected trials must be logged with rejection taxonomy.

---

## 8. Verification & Regression Test Suite (Task G)

A dedicated test suite was implemented in `tests/test_pilot_preparation_and_partitioning.py`:
- `test_authoritative_input_manifest_and_fits_inventory`: Verified 5 pointings, 120 FITS products, and ingestion manifest.
- `test_crossmatch_identity_and_column_preservation`: Verified column integrity and uniqueness in all 5 catalogues.
- `test_wcs_to_pixel_coordinate_conversion`: Verified sub-milli-pixel round-trip accuracy on real FITS WCS.
- `test_mask_geometry_and_boundary_behavior`: Verified usable area fraction ($0.70 \le f_{\text{usable}} \le 0.95$).
- `test_ambiguous_and_blended_source_classification`: Tested isolated, blended, saturated, and extended categorization.
- `test_calibration_evaluation_strict_disjointness`: Verified zero cross-boundary leakage.
- `test_pointing_level_dither_grouping`: Verified valid detector/dither mapping.
- `test_deterministic_partition_manifest_generation`: Verified 100% deterministic reproducibility with `seed = 42`.
- `test_invalid_or_missing_catalogue_handling`: Verified defensive error handling.
- `test_provenance_and_checksum_integrity`: Verified all 16 historical assets match SHA-256 signatures.

### Test Execution Results:
```
tests/test_astronomical_crossmatch.py .................. [  7 passed ]
tests/test_astrovision_benchmark_v2_engine.py .......... [ 32 passed ]
tests/test_astrovision_injection_benchmark.py .......... [ 11 passed ]
tests/test_multipointing_acquisition_pilot.py .......... [ 10 passed ]
tests/test_pilot_preparation_and_partitioning.py ....... [ 10 passed ]
tests/test_spectra_v2_mask_benchmark.py ................ [  4 passed ]
======================================================================
TOTAL: 74 passed in 41.69s (100% PASS RATE, 0 REGRESSIONS)
======================================================================
```

---

## 9. Strict Governance Audit & Non-Execution Confirmation

As mandated by project governance:
- **Model Forward Passes:** 0
- **Model Inference Trials:** 0
- **Synthetic Injection Trials Executed:** 0
- **Benchmark Campaign Driver Invocations:** 0
- **Model Retraining or Checkpoint Modifications:** 0 (`checkpoints/astrovision_spatial_v2.pt` frozen)
- **P0003 Historical Catalogue Modifications:** 0 (`ce1416bb0d5fcffe...` intact)
- **Status of ASTROVISION:** `FAIL — NOT CERTIFIED`
- **Status of Benchmark Campaign:** `BLOCKED`

---

## 10. Deliverables Manifest

| Deliverable Description | Relative File Path | Format / SHA-256 |
|---|---|---|
| Preparation Summary Report | `reports/ASTROVISION_TASK_1_1O_PILOT_PREPARATION.md` | Markdown |
| Machine-Readable Manifest | `reports/manifests/astrovision_task_1_1O_pilot_preparation.json` | JSON |
| Pointing 0001 Catalogue | `data/processed/pilot_catalogues/pointing_0001_source_catalogue.csv` | `10ffce68f8018dd0...` |
| Pointing 0002 Catalogue | `data/processed/pilot_catalogues/pointing_0002_source_catalogue.csv` | `90ac516056851bbc...` |
| Pointing 0008 Catalogue | `data/processed/pilot_catalogues/pointing_0008_source_catalogue.csv` | `c2831981623291de...` |
| Pointing 0009 Catalogue | `data/processed/pilot_catalogues/pointing_0009_source_catalogue.csv` | `52e0fc53088100ca...` |
| Pointing 0010 Catalogue | `data/processed/pilot_catalogues/pointing_0010_source_catalogue.csv` | `33830db045a67d18...` |
| Pointing 0001 Mask Diag | `data/processed/pilot_masks/pointing_0001_mask_diagnostics.json` | `d5b5c1f2e3cc0b59...` |
| Pointing 0002 Mask Diag | `data/processed/pilot_masks/pointing_0002_mask_diagnostics.json` | `2f280cbdd634816c...` |
| Pointing 0008 Mask Diag | `data/processed/pilot_masks/pointing_0008_mask_diagnostics.json` | `17398584c54e5e91...` |
| Pointing 0009 Mask Diag | `data/processed/pilot_masks/pointing_0009_mask_diagnostics.json` | `bf4ace351df5a690...` |
| Pointing 0010 Mask Diag | `data/processed/pilot_masks/pointing_0010_mask_diagnostics.json` | `7e17d7c1b84b6ad8...` |
| Frozen Five-Partition Manifest | `reports/manifests/astrovision_five_partition_pilot_manifest.csv` | `c1d83662b311f3f8...` |
| Pilot Benchmark Protocol v3.0 | `reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md` | `77200d92421a3cd8...` |
| Targeted Test Suite | `tests/test_pilot_preparation_and_partitioning.py` | Python / Pytest |

---

## 11. Concluding Recommendation

Task 1.1O is complete. All preparation requirements, catalogues, masks, partitions, protocols, and tests are verified and locked.

In accordance with strict governance guidelines, execution of the benchmark campaign remains **BLOCKED**. An independent scientific audit (Task 1.1P) must be performed to inspect and validate these deliverables before any future benchmark execution can be authorized.

