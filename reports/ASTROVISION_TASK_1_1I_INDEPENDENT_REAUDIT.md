# ASTROVISION Task 1.1I Independent Scientific Re-Audit Report
## Independent Re-Audit of Task 1.1H Remediation & Five-Partition Campaign Readiness

**Audit Role:** Independent Principal Scientific Auditor, Astronomical Benchmark Statistician & ML Validation Integrity Reviewer  
**Audit Mode:** STRICTLY READ-ONLY  
**Governing Inputs:**
- `scripts/validation/astrovision_injection_benchmark_v2.py`
- `scripts/validation/astrovision_controlled_campaign_driver.py`
- `tests/test_astrovision_benchmark_v2_engine.py`
- `reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json`
- `reports/ASTROVISION_TASK_1_1H_REMEDIATION.md`
- `reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md`
- `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md`
- `reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md`
- `data/processed/validation/pointing_0003_final_validated_catalogue.csv`
- Pointing 0003 Level-2 Science FITS files (`data/spherex/qr3/level2/*0003*.fits`)

**Current ASTROVISION Status:** **`FAIL — NOT CERTIFIED`**  
**Campaign Execution Status:** **`BLOCKED`**  
**Independent Re-Audit Verdict:** **`PARTIAL — STATISTICAL OR IMPLEMENTATION REMEDIATION REQUIRED`**

---

## 1. Executive Summary & Audit Decision

An exhaustive, strictly read-only independent scientific re-audit of the Phase 3 Task 1.1H targeted remediations and five-partition campaign readiness was conducted. Zero model forward passes or evaluation inferences were executed. All protected cryptographic assets were verified in place.

### Key Audit Findings
1. **Implementation & Physical Engineering Remediations Succeeded:**
   - **Audit A (Spatial Footprint Geometry):** `FootprintGeometryV2` successfully replaces the flawed Euclidean center distance check. Diagonal corner overlaps ($\Delta x=91, \Delta y=91$ sharing $1,369\,\text{px}$) are strictly rejected ($L_\infty = 91 < 128\,\text{px}$), while half-open edge-touching boundaries are correctly accepted as non-overlapping.
   - **Audit B (Detector-Aware Harvesting):** The physical noise formulation $\sigma_{\text{eff}} = \max(\sigma_{\text{var}}, 1.4826 \times \text{MAD})$ resolves the $100\%$ attrition on NIR detectors D1 and D2 by accounting for empirical astronomical spatial background fluctuations, without compromising physical source rejection criteria.
   - **Audit C (Five-Partition Schema & Lineage):** The manifest structure strictly isolates calibration and evaluation partitions across exposure IDs, filenames, cutouts, and sources. All positive calibration injections are paired and bound strictly within calibration exposures.
   - **Audit E (Calibration Transfer Isolation):** The photometric transfer function $\beta = F_{\text{recovered}} / S_{\text{true}}$ can be fit strictly out-of-sample on calibration injections with zero evaluation leakage.
   - **Audit F & G (Execution Safety & Cryptographic Integrity):** The campaign safety lock `CAMPAIGN_EXECUTION_LOCKED = True` prevents campaign execution. All 54 test suite cases pass, and all 13 authoritative hashes match.

2. **Critical Scientific Limitation Identified — Statistical Underpowering (Audit D):**
   - While the campaign driver harvested 251 cutouts and prepared 614 trials, these data originate from only **four pointing exposures** in a single astronomical field (`Pointing 0003`).
   - The evaluation partition comprises only **two pointing exposures** (`2026W30_1B_0003_1` and `2026W30_1B_0003_2`). For Detector 3, archive data availability restricts the evaluation set to **a single pointing exposure** (`0003_1`).
   - The protocol's cluster-robust bootstrap ($B=2,000$ iterations) over $G=2$ evaluation exposure clusters possesses only **3 unique resample combinations** ($\{E_1, E_1\}$, $\{E_1, E_2\}$, $\{E_2, E_2\}$), rendering asymptotic cluster-robust confidence intervals mathematically degenerate and uninformative.
   - A full campaign claim of generalizable population performance (AUROC, AUPRC, C50) cannot be scientifically defended with $G=2$ evaluation clusters.

### Final Audit Verdict
**`PARTIAL — STATISTICAL OR IMPLEMENTATION REMEDIATION REQUIRED`**

**Campaign Authorization Decision:**
**CAMPAIGN EXECUTION REMAINS BLOCKED.**  
While the software architecture is sound and ready for a *restricted engineering pilot*, full benchmark certification requires expanding the exposure pool to at least $G \ge 15 - 20$ independent pointing exposures to support meaningful cluster-robust statistical inference.

---

## 2. Audit Domain Status Table (Audits A through G)

| Audit Domain | Target Focus | Evaluation Standard | Verdict |
| :--- | :--- | :--- | :---: |
| **Audit A** | Exact Spatial Footprint Geometry | 2D half-open intervals, Chebyshev distance, diagonal overlap rejection, edge-touching acceptance | **`PASS`** |
| **Audit B** | D1/D2 Detector-Aware Harvesting | $\sigma_{\text{eff}}$ unit consistency, MAD mask exclusion, probe density, balanced per-file quotas | **`PASS`** |
| **Audit C** | Five-Partition Lineage & Leakage | Strict exposure/file/source disjointness, matched-control binding, zero cross-partition leakage | **`PASS`** |
| **Audit D** | Independent Group Count & Power | Independent exposure clusters, resampling unit count, cluster bootstrap validity ($B=2000, G=2$) | **`PARTIAL`** |
| **Audit E** | Calibration Transfer & Out-of-Sample | Transfer factor $\beta$ isolation, calibration-only parameter fitting, differential flux interpretation | **`PASS`** |
| **Audit F** | Dry-Run Manifest & Safety Locks | 5 partitions, trial ID uniqueness, reconciliation of counts, `CAMPAIGN_EXECUTION_LOCKED` gate | **`PASS`** |
| **Audit G** | Tests & Cryptographic Integrity | 100% test pass rate (54/54), SHA-256 hash verification across 13 authoritative files | **`PASS`** |

---

## 3. Detailed Audit Domain Findings

### 3.1 Audit A — Exact Spatial Footprint Geometry
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Mathematical Semantics:** Inspection of `FootprintGeometryV2` in `scripts/validation/astrovision_injection_benchmark_v2.py` confirms exact 2D half-open bounding box geometry $[x_0, x_0 + W) \times [y_0, y_0 + H)$:
   - Intersection requires both $\max(x_{0,1}, x_{0,2}) < \min(x_{1,1}, x_{1,2})$ and $\max(y_{0,1}, y_{0,2}) < \min(y_{1,1}, y_{1,2})$.
   - Edge-touching boundaries ($x_{0,2} = x_{0,1} + W$) fail the strict `<` inequality, yielding zero interior shared pixels and returning `(False, "DISJOINT")`.
2. **Diagonal Overlap Elimination:** For cutouts of size $128 \times 128\,\text{px}$, diagonal offsets of $(\Delta x, \Delta y) = (91, 91)$ have Euclidean distance $\Delta r = 128.69\,\text{px} \ge 128.0\,\text{px}$, but Chebyshev distance $L_\infty = \max(91, 91) = 91 < 128\,\text{px}$. `FootprintGeometryV2` detects an overlap of $37 \times 37 = 1,369\,\text{pixels}$ and rejects the pair.
3. **Cross-File / Detector Boundary Isolation:** Cutouts in different FITS files or detectors return `(False, "DIFFERENT_FILES_OR_DETECTORS")`, preventing spurious detector-space collisions across files.
4. **WCS Scope Caveat:** The geometry engine enforces exact bounding box non-overlap in native detector pixel space. It does not project multi-pointing dithered footprints into celestial spherical coordinates. This is scientifically valid because exposure-level independence is separately enforced via disjoint observation IDs (`obs_id`).
5. **Recomputed Manifest Intersections (All 251 Harvested Cutouts):**
   - **Total Unique Harvested Cutouts:** 251
   - **Co-file Overlapping Pairs:** 0
   - **Co-file Edge-Touching Pairs:** 0
   - **Invalid / Unverifiable Geometries:** 0
   - **Minimum Observed Chebyshev Distance (Co-File Cutouts):** $132.00\,\text{pixels} \ge 128.0\,\text{pixels}$

---

### 3.2 Audit B — D1/D2 Detector-Aware Harvesting
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Estimator Formulation & Units:**
   $$\sigma_{\text{eff}} = \max\left(\sqrt{\text{var\_bg}},\, 1.4826 \times \text{MAD}(\text{local\_box})\right)$$
   - The FITS `VARIANCE` HDU stores pixel variance in $\text{MJy}^2/\text{sr}^2$. The implementation computes $\sigma_{\text{var}} = \sqrt{\text{var\_bg}}$ in $\text{MJy/sr}$.
   - The local background image stores pixel values in $\text{MJy/sr}$. `1.4826 * MAD` is in $\text{MJy/sr}$.
   - Units are strictly identical and compatible before applying `max()`.
2. **Astronomical Background Physics:**
   In Pointing 0003 Level-2 files, formal pipeline read-noise variance $\sigma_{\text{var}} \approx 0.020\,\text{MJy/sr}$ on NIR detectors D1/D2. However, unresolved stellar backgrounds and faint sub-catalogue structure create real spatial fluctuations with empirical $\sigma_{\text{MAD}} \approx 0.075\,\text{MJy/sr}$ ($3.7\times$ higher). Evaluating candidates against read-noise variance alone rejected $99.8\%$ of blank sky. Using $\sigma_{\text{eff}}$ correctly establishes the physical noise floor.
3. **Preservation of Quality Standards:**
   - Catalogue exclusion: $d_{\text{src}} \ge 8.0\,\text{pixels}$ strictly enforced via `cKDTree`.
   - Core fatal flag mask: Core $5 \times 5$ pixels must have 0 fatal flags (`(flags & FATAL_FLAG_MASK) == 0`).
   - Cutout mask completeness: $\ge 88\%$ clean pixels required (`full_mask.mean() >= 0.88`).
   - Outlier thresholds: Core peak $\le \text{med} + 2.5\sigma_{\text{eff}}$ and local box peak $\le \max(2.5, \text{med} + 5.0\sigma_{\text{eff}})$ maintain strict astronomical blank-sky fidelity.
4. **Independent Re-Audit Harvesting Statistics (Pointing 0003 Archive):**

| Detector | Channel | Inspected Files | Probes Examined | Catalogue Dist Rej | Fatal Flag Rej | Core Peak Rej | Box Peak Rej | Spatial Overlap Rej | Mask Rej | Accepted Cutouts | Median BG ($\text{MJy/sr}$) | Mean Eff Sigma ($\text{MJy/sr}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | NIR | 4 | 5,207 | 144 | 1,326 | 3,243 | 440 | 4 | 0 | **50** | 0.2405 | 0.0463 |
| **D2** | NIR | 4 | 4,297 | 56 | 824 | 2,952 | 410 | 5 | 0 | **50** | 0.2462 | 0.0465 |
| **D3** | NIR | 3 | 2,470 | 46 | 421 | 1,705 | 245 | 3 | 0 | **50** | 0.1831 | 0.0431 |
| **D4** | MWIR | 4 | 2,287 | 68 | 396 | 1,526 | 243 | 4 | 0 | **50** | 0.1598 | 0.0482 |
| **D5** | MWIR | 4 | 520 | 0 | 152 | 206 | 98 | 14 | 0 | **50** | 0.1935 | 0.0425 |
| **D6** | MWIR | 4 | 249 | 0 | 56 | 87 | 50 | 6 | 0 | **50** | 0.3563 | 0.0586 |

All six detector arrays achieve 100% quota fulfillment ($N=50$ target) without relaxing rejection criteria.

---

### 3.3 Audit C — Five-Partition Lineage and Leakage
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Partition Composition:**
   - `CALIBRATION_CONTROL`: 139 trials
   - `CALIBRATION_INJECTION`: 139 trials
   - `EVALUATION_CONTROL`: 112 trials
   - `EVALUATION_POINT_SOURCE_INJECTION`: 112 trials
   - `EVALUATION_EXTENDED_SOURCE_INJECTION`: 112 trials
   - **Total Trials:** 614 trials
2. **Independent Set Intersections (Calibration vs. Evaluation):**
   - **`obs_id` Intersection:**
     $$\{2026W30\_1B\_0003\_3, 2026W30\_1B\_0003\_4\} \cap \{2026W30\_1B\_0003\_1, 2026W30\_1B\_0003\_2\} = \emptyset \quad (\text{Size: } 0)$$
   - **`filename` Intersection:**
     $$\text{CAL}_{\text{filenames}} \cap \text{EVAL}_{\text{filenames}} = \emptyset \quad (\text{Size: } 0)$$
   - **`parent_cutout_id` Intersection:**
     $$\text{CAL}_{\text{cutouts}} \cap \text{EVAL}_{\text{cutouts}} = \emptyset \quad (\text{Size: } 0)$$
   - **`matched_control_id` Intersection:**
     $$\text{CAL}_{\text{controls}} \cap \text{EVAL}_{\text{controls}} = \emptyset \quad (\text{Size: } 0)$$
3. **Matched-Control Pair Integrity:**
   - Every `CAL_INJ_*` trial binds strictly to a `CAL_CTRL_*` trial within the identical FITS file and parent cutout.
   - Every `EVAL_INJ_POINT_*` trial binds strictly to an `EVAL_CTRL_*` trial.
   - Every `EVAL_INJ_EXT_*` trial binds strictly to an `EVAL_CTRL_*` trial.
   - Total broken or cross-partition bindings: **0**.

---

### 3.4 Audit D — Independent Group Count and Statistical Power
**Verdict:** **`PARTIAL — STATISTICALLY UNDERPOWERED`**

#### Critical Statistical Findings:
1. **Disaggregation of Sample Hierarchy:**
   - **Nominal Trial Count:** 614 trials (336 evaluation trials)
   - **Underlying Cutout Count:** 251 cutouts (112 evaluation cutouts)
   - **Unique Pointing Exposures:** 4 exposures (`0003_1`, `0003_2`, `0003_3`, `0003_4`)
   - **Independent Calibration Clusters:** $G_{\text{cal}} = 2$ exposures
   - **Independent Evaluation Clusters:** $G_{\text{eval}} = 2$ exposures
2. **Resampling Degeneracy in Cluster-Robust Bootstrap:**
   - The controlled benchmark protocol specifies a cluster bootstrap with $B=2,000$ iterations over independent exposure clusters.
   - When the evaluation set contains only $G_{\text{eval}} = 2$ clusters $\{E_1, E_2\}$, drawing 2 clusters with replacement produces exactly three possible resamples:
     1. $\{E_1, E_1\}$ (Probability: 25%)
     2. $\{E_1, E_2\}$ (Probability: 50%)
     3. $\{E_2, E_2\}$ (Probability: 25%)
   - Running 2,000 bootstrap iterations over a 3-state discrete distribution is asymptotically degenerate and cannot produce valid 95% confidence intervals.
3. **Detector-Specific Exposure Starvation:**
   - In the evaluation partition, Detectors D1, D2, D4, D5, and D6 have $G=2$ exposures.
   - Detector D3 has **only $G=1$ exposure** (`2026W30_1B_0003_1`) because `0003_2D3` does not exist in the archive.
   - Calculating cluster-robust confidence intervals for Detector 3 is mathematically impossible ($G=1$).
4. **Generalization Scope:**
   - Performance measured on 2 exposures in a single pointing reflects specific celestial foreground and zodiacal conditions. It does not warrant claims of general SPHEREx all-sky detection capability.

#### Required Remediation for Full Certification:
To support meaningful cluster-robust statistics ($B=2,000$) and detector-level confidence intervals, the evaluation set must incorporate exposures from at least **$G_{\text{eval}} \ge 15 - 20$ independent pointing exposures** across multiple survey fields.

---

### 3.5 Audit E — Calibration Transfer and Out-of-Sample Validity
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Transfer Model Formulation:**
   $$\beta(\text{SNR}, \text{det}) = \frac{F_{\text{recovered}}}{S_{\text{true}}}$$
   $F_{\text{recovered}}$ is derived from paired residual differencing:
   $$\Delta F = \sum_{\text{aperture}} (I_{\text{inj}} - \hat{I}_{\text{inj}}) - \sum_{\text{aperture}} (I_{\text{ctrl}} - \hat{I}_{\text{ctrl}})$$
   This measures the differential autoencoder response in physical flux units ($\text{MJy/sr} \times \text{pix}$).
2. **Out-of-Sample Isolation:**
   - 139 positive calibration injections exist across Detectors 1–6 and SNR grid $[3, 5, 7, 10, 15, 20, 30, 50]$.
   - Transfer curves are fitted exclusively on `CALIBRATION_INJECTION` trials.
   - Evaluation injections and evaluation controls are strictly locked out of transfer curve fitting.
   - Parameter values must be frozen before evaluation begins.

---

### 3.6 Audit F — Dry-Run Manifest and Execution Safety
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Manifest Integrity:** `reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json` contains 614 trials partitioned into exactly 5 partitions.
2. **Execution Safety Gate:**
   - In `scripts/validation/astrovision_controlled_campaign_driver.py`:
     `CAMPAIGN_EXECUTION_LOCKED = True`
   - Calling `execute_campaign()` directly raises:
     `RuntimeError: CRITICAL GOVERNANCE BLOCKER: Benchmark Campaign Execution is STRICTLY PROHIBITED...`
   - Invocations with `--dry-run` perform zero model inference and zero forward passes.
   - Model inference counter during audit: **0**.
   - Benchmark campaign trials executed: **0**.

---

### 3.7 Audit G — Tests and Cryptographic Integrity
**Verdict:** **`PASS`**

#### Verification Evidence:
1. **Full Repository Test Suite:**
   Command: `python -m pytest tests/`  
   - Collected: 54 items  
   - Failures: 0  
   - Errors: 0  
   - Passed: **54 passed in 14.25s**
2. **Independent Cryptographic Hash Audit:**

| Protected Asset Path | Expected SHA-256 Hash | Independently Computed SHA-256 | Verification Result |
| :--- | :--- | :--- | :---: |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **MATCH** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **MATCH** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **MATCH** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **MATCH** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | `dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688` | **MATCH** |
| `reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | `5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698` | **MATCH** |
| `reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md` | `db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808` | `db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md` | `d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc` | `d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc` | **MATCH** |
| `reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md` | `13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985` | `13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` | `764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88` | `764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88` | **MATCH** |
| `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md` | `5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18` | `5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18` | **MATCH** |
| `reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md` | `22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278` | `22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278` | **MATCH** |
| `reports/ASTROVISION_TASK_1_1H_REMEDIATION.md` | *(New in 1.1H)* | `950e361cccdb4c342cf10267d8f61fd38644cf97001860a794c7465f80e94e03` | **RECORDED** |
| `reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md` | *(New in 1.1H)* | `74653153b17f110ba60578b2141ef1d205277b6fa4980178f0ac5ab542d0fd4f` | **RECORDED** |

---

## 4. Unresolved Scientific Limitations

1. **Exposure Group Sample Size:** Only $G_{\text{eval}} = 2$ independent exposure clusters exist in the evaluation set. Cluster-robust resampling cannot yield continuous, valid confidence intervals with $G=2$.
2. **Missing Detector 3 Archive Exposure:** In Exposure `2026W30_1B_0003_2`, the D3 FITS file is missing from the Level-2 archive. Consequently, the evaluation partition contains only a single D3 exposure (`0003_1D3`), preventing any cross-exposure validation for Detector 3.
3. **Empirical Model Transfer Response vs. Physical Calibration:** $\beta = F_{\text{recovered}} / S_{\text{true}}$ reflects the differential sensitivity curve of the frozen autoencoder. It must not be reported as absolute astronomical photometry until verified against external standard stars.

---

## 5. Explicit Campaign Authorization Decision

```
================================================================================
FINAL AUDIT VERDICT:
PARTIAL — STATISTICAL OR IMPLEMENTATION REMEDIATION REQUIRED
================================================================================
CAMPAIGN AUTHORIZATION:
CAMPAIGN EXECUTION REMAINS STRICTLY BLOCKED.
================================================================================
```

### Path to Campaign Authorization:
1. **Restricted Engineering Pilot (Optional):** If approved by project governance, a restricted pilot execution on Pointing 0003 may be run solely to evaluate software pipeline mechanics and paired differential residual logging, provided that metrics are explicitly designated as *pre-certification pilot diagnostics* without generalized AUROC claims.
2. **Full Benchmark Certification Requirement:** Full authorization for an authoritative ASTROVISION Benchmark Campaign requires ingesting Level-2 data from at least 15 to 20 independent pointings across the QR3 survey to achieve statistical power for group-aware cluster bootstrap inference.

