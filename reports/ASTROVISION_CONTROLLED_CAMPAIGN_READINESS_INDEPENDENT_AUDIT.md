# Independent Scientific Audit of Exposure-Level Leakage Remediation & Controlled Campaign Readiness
**Phase 3, Task 1.1G — Formal Independent Read-Only Readiness Audit**  
**NASA Space Apps Challenge 2026 — SPECTRA-X / F1**

---

## 1. Executive Summary & Audit Verdict

This report delivers the strictly read-only, independent scientific audit of the ASTROVISION exposure-level leakage remediation and controlled benchmark campaign preparation (Task 1.1F), inspecting:
* `scripts/validation/astrovision_injection_benchmark_v2.py`
* `scripts/validation/astrovision_controlled_campaign_driver.py`
* `tests/test_astrovision_benchmark_v2_engine.py`
* `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md`
* `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md`
* `reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json`

### Explicit Final Audit Verdict:
**`PARTIAL — REMEDIATION REQUIRED BEFORE CAMPAIGN`**

### Campaign Authorization Decision:
**CAMPAIGN EXECUTION IS BLOCKED.**  
While the core four-tier exposure-grouping architecture and dry-run safety locks represent substantial engineering progress, three specific scientific limitations must be remediated prior to campaign authorization:
1. **Geometric Separation Metric (Audit B: `PARTIAL`):** The Euclidean separation threshold of $128.0\,\text{pixels}$ permits diagonal corner overlap between $128 \times 128$ cutouts when $128.0 \le \Delta r < 181.02\,\text{pixels}$ ($\sqrt{2} \times 128$).
2. **Detector Attrition on D1 and D2 (Audit C: `PARTIAL`):** The harvesting probe filter over-rejects candidate cutouts on D1 and D2 due to tight Gaussian noise variance, yielding zero cutouts ($N=0$) for Detectors 1 and 2 in the dry-run manifest.
3. **Absence of Calibration Injections (Audit D: `PARTIAL`):** Positive injections are placed exclusively into evaluation partitions; no calibration injections exist to empirically fit the photometric transfer function ($\beta$) out-of-sample.

---

## 2. Audited Files & Cryptographic Signatures

The following authoritative files were independently verified in place via SHA-256 without modification:

| File Role | Path | Audited SHA-256 Hash | Integrity |
| :--- | :--- | :--- | :---: |
| **Model Checkpoint** | `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **FROZEN** |
| **Authoritative Catalogue** | `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **FROZEN** |
| **Benchmark Engine v2** | `scripts/validation/astrovision_injection_benchmark_v2.py` | *(Audited in-tree)* | **VERIFIED** |
| **Campaign Driver** | `scripts/validation/astrovision_controlled_campaign_driver.py` | *(Audited in-tree)* | **VERIFIED** |
| **Engine Test Suite** | `tests/test_astrovision_benchmark_v2_engine.py` | *(Audited in-tree)* | **VERIFIED** |
| **Controlled Protocol** | `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` | `764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88` | **VERIFIED** |
| **Partition Audit Report** | `reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md` | `5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18` | **VERIFIED** |
| **Historical v1 Results** | `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **FROZEN** |
| **Historical v1 Manifest**| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **FROZEN** |

---

## 3. Detailed Audit Domain Findings (Audits A through H)

### Audit A: Four-Tier Grouping Correctness
**Classification:** **`PASS`**  
**Target:** `GroupAwarePartitionManagerV2.assign_partitions` in `scripts/validation/astrovision_injection_benchmark_v2.py`

#### Verification Evidence
1. **Mathematical Disjointness:** An independent evaluation of the partition sets produced by `GroupAwarePartitionManagerV2` on Pointing 0003 metadata confirms that:
   $$\text{CALIBRATION}_{\text{obs\_ids}} \cap \text{EVALUATION}_{\text{obs\_ids}} = \emptyset$$
   $$\text{CALIBRATION}_{\text{filenames}} \cap \text{EVALUATION}_{\text{filenames}} = \emptyset$$
   $$\text{CALIBRATION}_{\text{source\_ids}} \cap \text{EVALUATION}_{\text{source\_ids}} = \emptyset$$
2. **Disjoint Set Union (DSU) Implementation:** Path compression (`parent[u] = parent[parent[u]]`) and union by root are correctly implemented. Repeated source IDs spanning multiple pointing exposures merge exposures into single connected components. Placeholder IDs (`None`, `""`, `"NONE"`, `"UNKNOWN"`) are explicitly excluded from unioning, preventing spurious cluster collapse.
3. **Defensive Rejection:** Cutouts with missing or malformed `obs_id`, `filename`, or `detector_id` raise `ValueError` under `strict_metadata=True` and are placed into `rejected_items` under lenient mode.
4. **Determinism:** Partition assignments executed across multiple processes with `seed=42` yield bitwise identical cluster memberships.

---

### Audit B: Spatial Independence and Cutout Geometry
**Classification:** **`PARTIAL`**  
**Target:** Spatial separation check in `GroupAwarePartitionManagerV2` and `harvest_stratified_safe_cutouts`

#### Technical Analysis & Finding
The codebase enforces a spatial separation rule:
```python
dist = math.hypot(cx - prev_cx, cy - prev_cy)
if dist < self.min_spatial_sep_pix: # default 128.0
    # reject
```

**Geometric Failure Condition:**
* SPHEREx cutouts are axis-aligned squares of dimension $S = 128 \times 128\,\text{pixels}$.
* Bounding boxes centered at $(x_c, y_c)$ extend $\pm 64\,\text{pixels}$ along each axis.
* If two cutouts are displaced along a coordinate axis ($\Delta y = 0, \Delta x = 128$), their bounding boxes touch at their outer edges ($x_1 + 64 = x_2 - 64$) with **zero interior area overlap**.
* However, if two cutout centers are displaced diagonally at an angle near $45^\circ$ ($\Delta x = 91, \Delta y = 91$):
  $$\Delta r = \sqrt{91^2 + 91^2} = \sqrt{16562} \approx 128.69\,\text{pixels} \ge 128.0\,\text{pixels}$$
  Because $\Delta r \ge 128.0$, this pair passes the Euclidean distance check!
  Yet their bounding boxes overlap:
  * Cutout 1 $X$-interval: $[-64, +64]$, $Y$-interval: $[-64, +64]$
  * Cutout 2 $X$-interval: $[91 - 64, 91 + 64] = [27, 155]$, $Y$-interval: $[27, 155]$
  * **Intersection:** $[27, 64] \times [27, 64]$ = **$37 \times 37 = 1,369\,\text{pixels}$ of shared footprint!**

**Required Remediation:**
To guarantee strictly zero geometric footprint overlap under all angular orientations, the separation criterion must use the Chebyshev ($L_\infty$) metric:
$$\max\left(|\Delta x|, |\Delta y|\right) \ge 128.0\,\text{pixels}$$
or, if Euclidean distance is retained, the threshold must be set to:
$$\Delta r_{\text{Euclidean}} \ge \sqrt{2} \times 128.0 \approx 181.02\,\text{pixels}$$

**Statistical Independence Clarification:** Geometric non-overlap prevents duplicate pixel reuse, but does **not** establish statistical background independence due to long-range diffuse zodiacal gradients. True statistical background independence is governed strictly by Tier 1 exposure grouping (`obs_id`).

---

### Audit C: Source Co-Grouping and Connected-Component Risks
**Classification:** **`PARTIAL`**  
**Target:** Graph connectivity and detector representation in `prepare_campaign_manifest`

#### Audited Component Statistics (Pointing 0003 Level-2 Dataset)
* **Total Discovered FITS Files:** 23 files across Pointing 0003
* **Unique Pointing Exposures:** 4 exposures (`2026W30_1B_0003_1`, `..._0003_2`, `..._0003_3`, `..._0003_4`)
* **Unique Catalogue Sources in Field:** 1,237 sources
* **Harvested Cutouts (Dry-Run):** 45 cutouts
* **Connected Components:** 4 independent exposure clusters
* **Cluster Allocation:**
  * CALIBRATION: 2 clusters (`2026W30_1B_0003_3`, `2026W30_1B_0003_4`) — 35 cutouts
  * EVALUATION: 2 clusters (`2026W30_1B_0003_1`, `2026W30_1B_0003_2`) — 10 cutouts

#### Detector Attrition Finding:
Inspection of `reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json` reveals:
* `CALIBRATION`: D1: 0, D2: 0, D3: 2, D4: 1, D5: 12, D6: 20
* `EVALUATION`: D1: 0, D2: 0, D3: 1, D4: 1, D5: 8, D6: 0

**Root Cause:**
In `harvest_stratified_safe_cutouts`, probe candidate centers are filtered by:
$$\max(\text{core\_img}) \le \text{med\_bg} + 2.5 \cdot \sigma_{\text{bg}}$$
On NIR detectors D1 and D2, read noise variance is low ($\sigma^2 \sim 10^{-4}\,\text{MJy}^2/\text{sr}^2 \implies \sigma \sim 0.01\,\text{MJy/sr}$). Over a 25-pixel core box ($5 \times 5$), normal Gaussian noise fluctuations naturally reach $2.5\sigma$, causing 89 of 150 probes to be rejected on D1, while the remaining 61 probes are caught by catalog distance or fatal flags. Consequently, **zero cutouts were harvested for D1 and D2**.

**Impact:** A benchmark campaign executed on this manifest would completely omit Detectors 1 and 2 ($0.75 - 1.45\,\mu\text{m}$), failing the multi-detector validation requirement.

---

### Audit D: Four-Partition Campaign Manifest
**Classification:** **`PARTIAL`**  
**Target:** `reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json`

#### Lineage & Role Assignment
* `CALIBRATION_CONTROL`: 35 trials drawn strictly from `calibration_obs_ids`.
* `EVALUATION_CONTROL`: 10 trials drawn strictly from `evaluation_obs_ids`.
* `POINT_SOURCE_INJECTION`: 10 trials drawn strictly from `evaluation_obs_ids`.
* `EXTENDED_SOURCE_INJECTION`: 10 trials drawn strictly from `evaluation_obs_ids`.

#### Independence Intersections:
* $\text{CAL\_CTRL}_{\text{obs}} \cap \text{EVAL\_CTRL}_{\text{obs}} = \emptyset$
* $\text{CAL\_CTRL}_{\text{obs}} \cap \text{POINT\_INJ}_{\text{obs}} = \emptyset$
* $\text{CAL\_CTRL}_{\text{obs}} \cap \text{EXT\_INJ}_{\text{obs}} = \emptyset$
* $\text{CAL\_CTRL}_{\text{files}} \cap \text{EVAL}_{\text{files}} = \emptyset$

#### Defect Specification:
All positive injection trials (`POINT_SOURCE_INJECTION`, `EXTENDED_SOURCE_INJECTION`) are designated as *evaluation* trials. There are **zero calibration injection trials**.
If a future task calibrates an empirical photometric transfer function ($\beta = F_{\text{recovered}} / S_{\text{true}}$), it cannot be pre-fit on calibration data. Using evaluation injections to fit the transfer curve would introduce circular in-sample parameter tuning. A dedicated `CALIBRATION_INJECTION` set is required.

---

### Audit E: Threshold Calibration and Freezing
**Classification:** **`PASS`**  
**Target:** Section 4 of `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md`

#### Verification Evidence
1. **Calibration Isolation:** Threshold selection is restricted strictly to `CALIBRATION_CONTROL` samples. Evaluation labels and residuals are completely inaccessible during calibration.
2. **Objective Pre-Defined Rule:** The threshold $\tau^*$ is selected to satisfy an empirical false-positive rate target $\alpha \le 0.05$ on calibration background cutouts:
   $$\tau^* = \text{Quantile}\left(\{\chi^2_{\text{cal, peak}}\}, 0.95\right)$$
3. **Parameter Freezing:** Freezing $\tau^*$ and its Wilson score confidence interval into `calibration_threshold_frozen.json` is mandatory prior to evaluation execution.
4. **Historical Threshold Treatment:** The historical threshold $\tau = 169.10$ is explicitly documented as uncertified and non-authoritative.

---

### Audit F: Statistical Protocol Readiness
**Classification:** **`PASS`**  
**Target:** `reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md` (Sections 5 & 6)

#### Verification Evidence
* **Cluster Bootstrap:** Resampling units are defined as atomic pointing exposure groups (`obs_id`) with $B = 2,000$ replications, properly addressing intra-exposure spatial correlation.
* **Wilson Score Bounds:** Exact Wilson binomial intervals are specified for all discrete fractions (FPR, completeness).
* **Prevalence-Standardized Precision:** The protocol includes the Bayesian prevalence correction formula:
  $$\text{Precision}_{\text{std}}(\pi) = \frac{\text{Recall} \cdot \pi}{\text{Recall} \cdot \pi + \text{FPR} \cdot (1 - \pi)}$$
* **Scientific Separation of Observables:** Differential anomaly flux $F_{\text{recovered, model}}$ is clearly defined as a model-response observable, explicitly rejecting circular claims of physical flux calibration prior to transfer curve regression.

---

### Audit G: Dry-Run and Execution Safety
**Classification:** **`PASS`**  
**Target:** `scripts/validation/astrovision_controlled_campaign_driver.py`

#### Verification Evidence
1. **Safety Lock Integrity:** `CAMPAIGN_EXECUTION_LOCKED = True` (line 54). Invoking `--execute` unconditionally triggers a `RuntimeError` (line 282). There is no bypass code path.
2. **Zero Model Inference:** The dry-run driver imports neither `AstroVisionAutoencoder` nor `AstroVisionEvaluatorV2`. Running `--dry-run` performs zero forward passes and executes zero GPU/CPU model computations.
3. **Asset Protection:** Zero authoritative FITS files, catalogues, or checkpoints were modified during dry-run execution.

---

### Audit H: Test and Cryptographic Integrity
**Classification:** **`PASS`**  
**Target:** Repository test suite and SHA-256 asset verification

#### Verification Evidence
* **Pytest Suite:** Full repository test execution (`python -m pytest tests/`):
  **47 passed in 7.28s (0 failed, 0 warnings).**
* **Cryptographic Verification:** All 12 authoritative project assets were independently hashed via SHA-256; 100% match established baseline signatures (Section 2 table).

---

## 4. Summary Table of Audit Classifications

| Audit Domain | Classification | Primary Finding & Evidence |
| :--- | :---: | :--- |
| **Audit A: Four-Tier Grouping Correctness** | **`PASS`** | Zero exposure, file, or source intersection between CALIBRATION and EVALUATION; DSU correctly resolves transitive source links. |
| **Audit B: Spatial Independence & Geometry** | **`PARTIAL`** | Euclidean separation $\Delta r \ge 128\,\text{px}$ allows up to $37 \times 37\,\text{px}$ corner overlap for cutouts aligned diagonally at $45^\circ$. Metric must be updated to $L_\infty \ge 128\,\text{px}$ or $\Delta r \ge 181.02\,\text{px}$. |
| **Audit C: Source Co-Grouping & Components** | **`PARTIAL`** | 4 independent clusters identified; however, harvesting filter over-rejects D1 and D2 candidates, resulting in $N=0$ cutouts on D1 and D2 in the dry-run manifest. |
| **Audit D: Four-Partition Manifest Lineage** | **`PARTIAL`** | No exposure leakage from calibration to evaluation, but manifest lacks `CALIBRATION_INJECTION` trials, risking in-sample tuning if transfer curves are calibrated. |
| **Audit E: Threshold Calibration & Freezing** | **`PASS`** | Calibration-only controls used; objective selection rule defined; threshold freezing enforced; historical $\tau=169.10$ treated as unvalidated. |
| **Audit F: Statistical Protocol Readiness** | **`PASS`** | Group-aware cluster bootstrap ($B=2,000$), Wilson intervals, prevalence standardization, and non-circular photometry definitions verified. |
| **Audit G: Dry-Run & Execution Safety** | **`PASS`** | Safety lock prevents execution under all flags; dry-run executes zero model inferences and touches no frozen assets. |
| **Audit H: Test & Cryptographic Integrity** | **`PASS`** | 47/47 pytest tests pass; all 12 protected assets match authoritative SHA-256 hashes. |

---

## 5. Explicit Unresolved Risks & Remediation Plan Prior to Campaign

Before authorizing the execution of the full benchmark campaign:
1. **Update Spatial Separation Metric:**  
   In `GroupAwarePartitionManagerV2` and `harvest_stratified_safe_cutouts`, update the separation check to enforce Chebyshev distance:
   $$\max\left(|x_1 - x_2|, |y_1 - y_2|\right) \ge 128.0\,\text{pixels}$$
   or Euclidean distance $\Delta r \ge 181.02\,\text{pixels}$ to guarantee zero diagonal footprint overlap.
2. **Tune Harvesting Probe Filter for Low-Variance Detectors (D1/D2):**  
   Increase candidate probe count (e.g. from 150 to 500) and relax the core-brightness test from $2.5\sigma$ to $3.5\sigma$ over the 25-pixel box, ensuring at least $N \ge 20$ cutouts are harvested per detector for D1 and D2.
3. **Introduce Calibration Injections (`CALIBRATION_INJECTION`):**  
   Update the manifest generator to create synthetic injections within the `CALIBRATION` partition so that photometric transfer calibration ($\beta$) can be fitted out-of-sample relative to evaluation injections.

---

## 6. Campaign Authorization Decision

**FINAL DECISION:** **`CAMPAIGN EXECUTION REMAINS BLOCKED`**  
**VERDICT:** **`PARTIAL — REMEDIATION REQUIRED BEFORE CAMPAIGN`**

The implementation has achieved genuine exposure-level independence and robust dry-run safety. Once the three mechanical refinements above (Chebyshev spatial metric, D1/D2 harvesting yield, and calibration injection partitioning) are applied and verified, the benchmark will be fully prepared for campaign authorization review.

