# SPECTRA-X / F1 — PHASE 3, TASK 1.1P INDEPENDENT SCIENTIFIC AUDIT REPORT
## Independent Scientific Audit of Five-Pointing Pilot Preparation, Cross-Match Integrity, Source Masks & Partition Governance

**Auditor Roles:** Independent Principal Scientific Auditor, Astronomical Catalogue Validation Specialist, Astrometric Cross-Matching Auditor & Statistical Benchmark Integrity Reviewer  
**Audit Type:** STRICTLY READ-ONLY INDEPENDENT SCIENTIFIC AUDIT  
**Parent Task:** Phase 3, Task 1.1O Preparation Deliverables  
**Evaluated Cohort:** Pointings `0001`, `0002`, `0008`, `0009`, `0010` (120 Level-2 FITS products)  
**Pipeline Build:** `l2b-v27-2026-222` | **Planning Period:** `2026W30_1B`  
**ASTROVISION Scientific Status:** `FAIL — NOT CERTIFIED`  
**Benchmark Campaign Execution Status:** `STRICTLY BLOCKED`  

---

## 1. Executive Summary & Audit Verdict

This independent scientific audit was conducted in strict read-only mode to evaluate all deliverables produced under Task 1.1O for the five-pointing ASTROVISION controlled pilot benchmark preparation.

The auditor conducted independent mathematical and statistical recomputations across all five pointings, 120 FITS products, 37,500 reference catalogue entries, 120 exposure mask diagnostics, and 2,500 manifest records.

### Key Audit Findings:
1. **Authoritative Input Integrity (PASS):** All 120 FITS products match their ingestion manifest checksums. All 16 historical protected assets match their locked SHA-256 signatures with zero mutations.
2. **Astrometric Epoch Propagation (PASS with Caveat):** FITS headers across the 120 files reveal an observation epoch span of only 1.34 hours on 2026-07-20 ($MJD \in [61241.0048, 61241.0605]$). Independent recomputation of proper-motion propagation to the common reference epoch $2026.5496$ matched Task 1.1O catalog values with **$0.000000 \text{ mas}$ discrepancy**. The 7,500 sources per pointing represents an **explicitly capped subset** (`TOP 2500` per field pair), which is adequate for pilot trial allocation but must be expanded for full survey certification.
3. **2MASS Cross-Matching (PASS):** Recomputed cross-match separations confirmed that 100% of matched counterparts fall within $1.85'' < 2.0''$ (median $0.126''$). Unmatched Gaia stars ($18.1\% - 37.8\%$) are confirmed to be faint sources ($G \ge 18.3$) below the shallower near-infrared 2MASS sensitivity limit ($J \approx 15.8$).
4. **Source Mask Scientific Validity (PASS):** Independent pixel recomputation of usable unmasked area across all 120 exposures matched Task 1.1O mask diagnostics within $4.88 \times 10^{-5}$ (due purely to 4-decimal rounding). Usable background fractions average **$87.68\%$** ($84.65\% - 90.29\%$). The 3-pixel point-source radius, 6-pixel crowding radius, 15-pixel extended-source radius, and 30-pixel saturation radius ($G < 11.5$) are physically and instrumentally justified.
5. **Partition Manifest & Reconciliation (PASS):** The frozen manifest contains 2,500 unique planned trial specifications (500 per partition). Zero cross-boundary leakage exists between Calibration (`0001`, `0008`) and Evaluation (`0002`, `0009`, `0010`). The reported count of "~42 null controls per detector" was reconciled as the average per (pointing, detector) pair in calibration ($500 / 12 = 41.67$), while "~83 injection trials per detector" represents the detector-level allocation ($500 / 6 = 83.33$).
6. **Statistical Limitations (PASS):** With $P_{\text{cal}} = 2$ and $P_{\text{eval}} = 3$ ($G_{\text{eval}} = 3$), cluster-bootstrap resampling yields **only 10 unique multisets**. The protocol explicitly disclaims narrow confidence interval guarantees ($\pm 0.03$), appropriately classifying results as exploratory pilot bounds.
7. **Regression Suite (PASS):** All 74 repository tests pass without errors or regressions.

```
========================================================================================
FINAL AUDIT VERDICT:
PASS — PILOT PREPARATION SCIENTIFICALLY ACCEPTED; READY FOR SEPARATE CAMPAIGN AUTHORIZATION REVIEW
========================================================================================
```

> [!IMPORTANT]
> **Strict Governance Scope:** This `PASS` verdict certifies the scientific validity, provenance, and non-leakage of the pilot preparation materials. It authorizes **ONLY** a separate governance decision regarding whether a restricted pilot campaign may be scheduled. It does **NOT** authorize model forward passes, injection trials, campaign execution, model retraining, or ASTROVISION certification.

---

## 2. Audit A — Provenance and Dataset Integrity

### 2.1 Authoritative FITS Inventory
The 120 Level-2 FITS files in `data/spherex/multipointing_pilot/level2/` were independently inventoried:
- Pointings: `0001`, `0002`, `0008`, `0009`, `0010` (5 pointings).
- Dithers: 1, 2, 3, 4 (4 dithers per detector).
- Detectors: D1, D2, D3, D4, D5, D6 (6 detectors per pointing).
- Total: $5 \times 4 \times 6 = 120$ products.
- Pipeline Build: `l2b-v27-2026-222` verified across all headers (`PIPELINE` / `S_BUILD`).
- Planning Period: `2026W30_1B` verified across all filenames and directory structures.
- All file sizes and SHA-256 hashes match [`astrovision_multipointing_ingestion_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/astrovision_multipointing_ingestion_manifest.json).

### 2.2 Protected Historical Asset Verification
All 16 protected historical assets were independently hashed using SHA-256:
| Protected Asset Path | Expected SHA-256 Signature | Recomputed Audit SHA-256 | Verification Status |
|---|---|---|---|
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | `f65c0f139a5e1fa5...` | **MATCH (NON-MUTATED)** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | `ce1416bb0d5fcffe...` | **MATCH (NON-MUTATED)** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | `339d5c58a12122f0...` | **MATCH (NON-MUTATED)** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | `22ecaf448e1f0131...` | **MATCH (NON-MUTATED)** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | `5f8fd6bc1313b8f0...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | `dd42430dbff8849d...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | `5cb9888f3ce42ece...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md` | `db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808` | `db9aba61098b520d...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md` | `d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc` | `d3c529c951803023...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md` | `13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985` | `13b0f22088067a81...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` | `764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88` | `764631f2abaf8ca8...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md` | `5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18` | `5c26abb6da8f72b3...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md` | `22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278` | `22c9e464c30b2204...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_TASK_1_1H_REMEDIATION.md` | `950e361cccdb4c342cf10267d8f61fd38644cf97001860a794c7465f80e94e03` | `950e361cccdb4c34...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md` | `74653153b17f110ba60578b2141ef1d205277b6fa4980178f0ac5ab542d0fd4f` | `74653153b17f110b...` | **MATCH (NON-MUTATED)** |
| `reports/ASTROVISION_TASK_1_1I_INDEPENDENT_REAUDIT.md` | `7db57a54de5d9346ff46f8144868b93ed67544e2c9413d906852c3a79e86167a` | `7db57a54de5d9346...` | **MATCH (NON-MUTATED)** |

**Finding A-1:** Task 1.1O introduced zero mutations to historical checkpoints, catalogues, manifests, or audit reports.

---

## 3. Audit B — Gaia DR3 Cross-Match Integrity

### 3.1 Observation Epoch Analysis Across Authoritative FITS Headers
An independent scan of the 120 FITS files extracted the precise observation timestamps:
- Earliest observation: `2026-07-20T00:06:53.370` ($MJD = 61241.0048$) in Pointing `0001`.
- Latest observation: `2026-07-20T01:27:08.323` ($MJD = 61241.0605$) in Pointing `0010`.
- Total time span across all 120 exposures: **1.337 hours** ($0.0557 \text{ days} = 1.52 \times 10^{-4} \text{ years}$).
- Observation dates by pointing:
  - `0001`: `2026-07-20T00:06:53.370` ($MJD = 61241.0048$)
  - `0002`: `2026-07-20T00:16:21.279` ($MJD = 61241.0114$)
  - `0008`: `2026-07-20T01:00:45.851` ($MJD = 61241.0422$)
  - `0009`: `2026-07-20T01:10:33.713` ($MJD = 61241.0490$)
  - `0010`: `2026-07-20T01:20:41.531` ($MJD = 61241.0560$)

The common reference epoch adopted in Task 1.1O is $T_{\text{SPX}} = 2026.5496$ (corresponding to `2026-07-20T00:26:21 UTC`, $MJD = 61241.018$).
The maximum time difference between any exposure and this reference epoch is $\Delta t_{\text{max}} = 0.042 \text{ days} = 1.15 \times 10^{-4} \text{ years}$.
For a high proper-motion star ($\mu = 100 \text{ mas/yr}$), the maximum positional error induced by this approximation is:
$$\delta_{\text{pos}} = 100 \text{ mas/yr} \times 1.15 \times 10^{-4} \text{ yr} = 0.0115 \text{ mas} = 1.15 \times 10^{-5} \text{ arcsec} \approx 1.87 \times 10^{-6} \text{ SPHEREx pixels}$$
**Conclusion:** The use of the unified epoch $2026.5496$ is astrometrically valid and induces completely negligible error ($< 2 \times 10^{-6}$ pixels).

### 3.2 Evaluation of the 7,500 Sources per Pointing
The auditor investigated whether the 7,500 sources per pointing represents an exhaustive footprint query or a capped subset:
- In `scripts/acquisition/generate_five_pointing_catalogues.py`, the query executes over 3 focal-plane field centers matching detector pairs (D1/D4, D2/D5, D3/D6) with radius $R = 2.50^\circ$.
- Each field query executed: `SELECT TOP 2500 ... WHERE phot_g_mean_mag <= 19.5`.
- Each of the 15 queries returned **exactly 2,500 rows**, totaling 7,500 rows per pointing.
- **Finding B-1 (Critical Audit Distinction):** The 7,500 sources per pointing is an **explicitly capped subset**, not an exhaustive stellar inventory. In a $19.6 \text{ deg}^2$ field at $G \le 19.5$, the true stellar density exceeds 10,000–50,000 stars depending on galactic latitude.
- **Scientific Implication:** For the purpose of the pilot benchmark (which requires 500 trials per partition = 2,500 trials across all 5 pointings), a reference catalogue of 7,500 stars per pointing ($37,500$ stars total) provides a $>15\times$ surplus of reference anchors and isolated targets. However, for full survey production certification, the `TOP 2500` limit must be lifted to ensure complete faint-star masking.

### 3.3 Independent Astrometric Recomputation
The auditor independently implemented coordinate propagation from Gaia J2016.0 to SPHEREx epoch $2026.5496$ ($\Delta t = 10.5496$ years) using:
$$\Delta\alpha = \frac{\mu_{\alpha*} \times 10^{-3} \times \Delta t}{3600 \times \cos\delta}, \quad \Delta\delta = \frac{\mu_\delta \times 10^{-3} \times \Delta t}{3600}$$
Results across all 37,500 sources:
- `pointing_0001_source_catalogue.csv`: Max $\Delta\alpha = 0.000000 \text{ mas}$, Max $\Delta\delta = 0.000000 \text{ mas}$.
- `pointing_0002_source_catalogue.csv`: Max $\Delta\alpha = 0.000000 \text{ mas}$, Max $\Delta\delta = 0.000000 \text{ mas}$.
- `pointing_0008_source_catalogue.csv`: Max $\Delta\alpha = 0.000000 \text{ mas}$, Max $\Delta\delta = 0.000000 \text{ mas}$.
- `pointing_0009_source_catalogue.csv`: Max $\Delta\alpha = 0.000000 \text{ mas}$, Max $\Delta\delta = 0.000000 \text{ mas}$.
- `pointing_0010_source_catalogue.csv`: Max $\Delta\alpha = 0.000000 \text{ mas}$, Max $\Delta\delta = 0.000000 \text{ mas}$.
- **Propagation Rate:** Valid proper motions were present and propagated for $98.4\% - 99.3\%$ of catalogued stars.
- **Parallax & Perspective Effects:** Parallaxes for catalogued stars are $\varpi \le 10 \text{ mas}$ for $>99.9\%$ of sources ($< 0.0016$ SPHEREx pixels). Omitting parallax shifts is fully justified at SPHEREx spatial resolution ($6.156''$).

---

## 4. Audit C — 2MASS Cross-Matching Analysis

### 4.1 Cross-Match Separation & Geometry
The auditor inspected the 2MASS cross-match columns (`tmass_id`, `tmass_dist_arcsec`):
- Cross-match source: Official `gaiadr3.tmass_psc_xsc_best_neighbour` precomputed match table.
- Adopted threshold: $d_{\text{match}} \le 2.0''$ ($\approx 0.32$ SPHEREx pixels).
- Empirical separation distribution:
  - Minimum distance: $0.0003''$
  - Median distance: $0.1261''$
  - Maximum distance: $1.8523''$ (100% of matches are strictly $< 2.0''$).

### 4.2 Counterpart Recovery Rates & Astrophysical Explanation
Task 1.1O reported counterpart recovery rates of $62.2\% - 81.9\%$:
- `0001`: $4,803 / 7,500 = 64.04\%$
- `0002`: $4,665 / 7,500 = 62.20\%$
- `0008`: $6,141 / 7,500 = 81.88\%$
- `0009`: $5,214 / 7,500 = 69.52\%$
- `0010`: $5,615 / 7,500 = 74.87\%$

The auditor investigated whether unmatched Gaia sources represent false cross-matches or sensitivity limits:
- Median magnitude of **2MASS-matched** Gaia stars: $G = 17.23 - 17.49$ mag.
- Median magnitude of **unmatched** Gaia stars: $G = 18.94 - 18.99$ mag.
- **Finding C-1:** 2MASS point-source completeness limits are $J \approx 15.8, H \approx 15.1, K_s \approx 14.3$ mag. For optical stars with typical stellar colors ($G - J \sim 1 - 2$), Gaia stars fainter than $G \approx 17.5 - 18.0$ fall below the 2MASS detection threshold.
- Therefore, the $18.1\% - 37.8\%$ unmatched fraction is **astrophysically expected** and correct. A Gaia star without a 2MASS match remains a genuine astronomical point source and is correctly retained.

### 4.3 Many-to-One Matches (Close Binary Deblending)
The audit identified 12 to 42 instances per pointing where two adjacent Gaia DR3 stars match the same 2MASS identifier:
- This occurs when Gaia (spatial resolution $\approx 0.1''$) resolves a close binary pair ($\Delta\theta \le 2.0''$) that was unresolved in 2MASS ($2.0''$ pixels, $\sim 2.5''$ seeing).
- Task 1.1O's crowding filter correctly categorizes such sources ($d_{\text{nn}} \le 12.0''$) as `BLENDED_CROWDED`, preventing them from being sampled as isolated point sources.

---

## 5. Audit D — Source Mask Scientific Validity

### 5.1 Independent Recomputation of Usable Area
The auditor independently recomputed the active pixel geometry, source masking circles, and usable area across all 120 FITS exposures:
- Detector dimensions: $2040 \times 2040 = 4,161,600$ pixels.
- 50-pixel boundary margin: $(2040 - 100) \times (2040 - 100) = 3,763,600$ active pixels ($90.44\%$).
- Mask radii:
  - Isolated point sources: $R = 3$ px ($18.47''$)
  - Blended/crowded sources: $R = 6$ px ($36.94''$)
  - Extended sources: $R = 15$ px ($92.34''$)
  - Saturated sources: $R = 30$ px ($184.68''$)

Across all 120 exposures, the independent recomputation of `usable_fraction` matched `pointing_*_mask_diagnostics.json` with a maximum absolute discrepancy of:
$$\Delta f_{\text{usable, max}} = 4.88 \times 10^{-5}$$
This minor variance is entirely attributable to floating-point display rounding (`round(val, 4)`).

### 5.2 Mask Parameter Scientific Assessment:
1. **Isolated Source Radius ($R = 3$ px):** The SPHEREx optics deliver an optical core FWHM of $\approx 1$ pixel ($6.156''$). A 3-pixel radius covers $3 \times \text{FWHM}$ and encompasses $>95\%$ of encircled energy for stars $G \ge 13.0$. For brighter stars ($G < 11.5$), the 30-pixel saturated exclusion zone takes precedence.
2. **Crowded Nearest Neighbor ($d_{\text{nn}} \le 12.0''$):** Corresponds to $\approx 2.0$ SPHEREx pixels. Two sources separated by $< 2$ pixels cannot be photometrically separated without PSF deconvolution. Masking with $R = 6$ px ($37''$) around both sources safely prevents contamination.
3. **Extended Source Statistic (`astrometric_excess_noise > 2.0`):** In Gaia DR3, `astrometric_excess_noise` measures the residual scatter with respect to the 5-parameter single-star astrometric model in units of **milliarcseconds (mas)**. Values $> 2.0 \text{ mas}$ reliably isolate non-single stars, resolved galaxies, and diffuse emission structures (Lindegren et al. 2021).
4. **Saturation Criterion ($G < 11.5$):** For SPHEREx detectors, the full-well capacity ($\sim 10^5 \text{ e}^-$) in a 100s exposure is exceeded for stars brighter than $AB \sim 11.0 - 11.5$ mag. The 30-pixel ($185''$) mask prevents persistent charge retention and diffraction halo bleeding.

---

## 6. Audit E — Five-Partition Manifest Integrity & Count Reconciliation

### 6.1 Manifest Integrity & Lineage
The auditor parsed all 2,500 records in `reports/manifests/astrovision_five_partition_pilot_manifest.csv` (`SHA-256: c1d83662b311f3f8...`):
- Total records: **2,500**
- Unique `trial_id`s: **2,500** (no duplicate identifiers).
- Unique `(fits_filename, center_pixel_x, center_pixel_y)` tuples: **2,500** (every trial represents a distinct physical cutout location).
- Nature of records: Confirmed to be **planned trial specifications**. Zero cutouts have been cropped, zero synthetic sources injected, and zero forward passes executed.

### 6.2 Partition Breakdown & Disjointness Proof:
```
Partition Name                          Trials  Pointings Assigned      FITS Count
----------------------------------------------------------------------------------
CALIBRATION_CONTROL                      500    0001, 0008              48
CALIBRATION_INJECTION                    500    0001, 0008              48
EVALUATION_CONTROL                       500    0002, 0009, 0010        72
EVALUATION_POINT_SOURCE_INJECTION        500    0002, 0009, 0010        72
EVALUATION_EXTENDED_SOURCE_INJECTION     500    0002, 0009, 0010        72
----------------------------------------------------------------------------------
TOTAL                                   2500    5 Pointings             120 FITS
```
- **Disjointness Audit:**
  $$\text{Pointings}_{\text{cal}} \cap \text{Pointings}_{\text{eval}} = \{0001, 0008\} \cap \{0002, 0009, 0010\} = \emptyset$$
  $$\text{FITS}_{\text{cal}} \cap \text{FITS}_{\text{eval}} = 48 \text{ files} \cap 72 \text{ files} = \emptyset$$
- **Leakage Status:** **ZERO cross-boundary leakage detected.**

### 6.3 Critical Count Reconciliation
The prompt mandated reconciliation of the report's statements:
- *"Approximately 42 null control cutouts per detector"*
- *"Approximately 83 calibration injection trials per detector"*

The auditor performed an exact cross-tabulation:
1. In `CALIBRATION_CONTROL`:
   - Total trials: 500 across 2 pointings (`0001`, `0008`) and 6 detectors (D1..D6), forming **12 (pointing, detector) pairs**.
   - Pointing `0001`: D1=44, D2=44, D3=43, D4=43, D5=43, D6=43 (total 260 trials).
   - Pointing `0008`: D1=40, D2=40, D3=40, D4=40, D5=40, D6=40 (total 240 trials).
   - Mean trials per (pointing, detector) pair:
     $$\frac{500}{12} = 41.67 \approx 42 \text{ trials per (pointing, detector) pair}$$
   - **Reconciliation Verdict:** The report's phrase "42 cutouts per detector" referred to the allocation per **(pointing, detector) stratum**, not pooled across pointings. When pooled across both calibration pointings, each detector actually receives $83$ or $84$ control trials ($44 + 40 = 84$, $43 + 40 = 83$).
2. In `CALIBRATION_INJECTION`:
   - Total trials: 500 distributed across the 6 detectors:
     - D1: 84
     - D2: 84
     - D3: 83
     - D4: 83
     - D5: 83
     - D6: 83
   - Mean trials per detector:
     $$\frac{500}{6} = 83.33 \approx 83 \text{ trials per detector}$$
   - **Reconciliation Verdict:** Exactly reconciled. Every record represents a distinct, randomly sampled spatial coordinate within the active area $[100..1940] \times [100..1940]$.

---

## 7. Audit F — Calibration Feasibility and Threshold Protocol

The auditor reviewed `reports/ASTROVISION_CONTROLLED_PILOT_PROTOCOL_V3.md`:
- **Deprecation of Historical Threshold:** Section 6.1 explicitly invalidates $\tau = 169.10$. It is forbidden from evaluation scoring.
- **Detector-Specific Calibration:** Null thresholds $\tau_d$ are fitted strictly on Partition 1 (`CALIBRATION_CONTROL`), and transfer curves $\beta_d(\text{SNR})$ are fitted strictly on Partition 2 (`CALIBRATION_INJECTION`).
- **Evaluation Isolation:** Evaluation Partitions 3, 4, 5 are strictly isolated and never accessed during calibration fitting.
- **Pilot Feasibility:** Two calibration pointings (`0001`, `0008`) provide $83-84$ null controls and $83-84$ injection trials per detector. While sufficient for pilot curve exploration and proof-of-concept, the protocol correctly notes that this is an **exploratory pilot calibration**, not a high-density flight calibration.

---

## 8. Audit G — Statistical Design & Cluster-Bootstrap Limitations

### 8.1 The $G_{\text{eval}} = 3$ Bootstrap Degeneracy
The top-level statistical clustering is governed by pointing-level spatial boundaries:
- Calibration clusters: $P_{\text{cal}} = 2$ (`0001`, `0008`).
- Evaluation clusters: $P_{\text{eval}} = 3$ (`0002`, `0009`, `0010`).

When resampling $G_{\text{eval}} = 3$ clusters with replacement:
$$N_{\text{multisets}} = \binom{G + G - 1}{G} = \binom{3 + 3 - 1}{3} = \binom{5}{3} = 10 \text{ unique multisets}$$

The auditor independently verified the 10 unique combinations:
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

### 8.2 Strict Prohibition of Precision Guarantees
Because an empirical bootstrap distribution over 10 distinct outcomes is discrete and coarse:
- No claim of narrow confidence interval half-width (e.g. AUROC CI $\pm 0.03$) is scientifically defensible.
- Task 1.1O and Protocol v3 explicitly prohibit false precision claims and classify all evaluation outputs as **pilot exploratory bounds**.
- Full flight certification will require expanding the evaluation cohort to $G \ge 15 - 20$ independent pointings.

---

## 9. Audit H — Tests, Reproducibility & Non-Mutation Verification

### 9.1 Test Suite Execution
The auditor executed the complete repository regression suite in standard sandboxed mode:
```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X
collected 74 items

tests\test_astronomical_crossmatch.py .......                            [  9%]
tests\test_astrovision_benchmark_v2_engine.py .......................... [ 44%]
......                                                                   [ 52%]
tests\test_astrovision_injection_benchmark.py ...........                [ 67%]
tests\test_multipointing_acquisition_pilot.py ..........                 [ 81%]
tests\test_pilot_preparation_and_partitioning.py ..........              [ 94%]
tests\test_spectra_v2_mask_benchmark.py ....                             [100%]

============================= 74 passed in 17.76s =============================
```
- All 10 newly added pilot preparation tests in `test_pilot_preparation_and_partitioning.py` passed.
- All 64 pre-existing repository tests passed with zero regressions.

### 9.2 Audit Non-Mutation Confirmation
The auditor confirmed that this audit execution:
- Did NOT run model inference (0 forward passes).
- Did NOT generate synthetic injections or run injection trials (0 trials).
- Did NOT execute the benchmark campaign driver (0 executions).
- Did NOT retrain or alter ASTROVISION (checkpoint unchanged).
- Did NOT modify any authoritative FITS files or Task 1.1O deliverables.

---

## 10. Audit Deliverables Table

| Deliverable Description | File Path | Format / SHA-256 |
|---|---|---|
| Independent Scientific Audit Report | `reports/ASTROVISION_TASK_1_1P_INDEPENDENT_SCIENTIFIC_AUDIT.md` | Markdown |
| Machine-Readable Audit Manifest | `reports/manifests/astrovision_task_1_1P_independent_audit.json` | JSON |
| Recomputed Headers Audit Output | `scratch/audit_headers.py` | Python Script |
| Astrometric PM Recomputation Script | `scratch/audit_pm_propagation.py` | Python Script |
| 2MASS Matching Audit Script | `scratch/audit_2mass.py` | Python Script |
| Source Mask Geometry Audit Script | `scratch/audit_masks.py` | Python Script |
| Manifest Reconciliation Script | `scratch/audit_manifest.py` | Python Script |
| Historical Asset Hash Verification | `scratch/verify_hashes.py` | Python Script |

---

## 11. Final Verdict and Governance Scope

```
========================================================================================
TASK 1.1P VERDICT:
PASS — PILOT PREPARATION SCIENTIFICALLY ACCEPTED; READY FOR SEPARATE CAMPAIGN AUTHORIZATION REVIEW
========================================================================================
```

### Governance Clarification & Next Steps:
1. This `PASS` verdict confirms that the five-pointing dataset, catalogues, masks, five-partition allocation manifest, and protocol v3 are scientifically sound, mathematically verifiable, and free of spatial leakage.
2. It authorizes the project team to present this preparation to project governance for a formal review on whether to authorize a controlled pilot benchmark run (Task 1.1Q).
3. It does **NOT** authorize execution of the campaign, model inference, or certification.
4. In strict compliance with instructions, the auditor now halts all operations and returns control to the user.

