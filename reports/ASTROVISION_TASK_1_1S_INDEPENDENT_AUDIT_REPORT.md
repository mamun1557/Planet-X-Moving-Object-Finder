# ASTROVISION Task 1.1S — Independent Scientific Results Audit
## Comprehensive Post-Campaign Audit of Authorized Five-Pointing Controlled Pilot Campaign (Task 1.1R)

**Project:** SPECTRA-X / F1  
**Phase:** Phase 3 — Independent Verification & Audit  
**Task:** 1.1S  
**Audit Mode:** STRICTLY READ-ONLY AUDIT  
**Auditor Roles:**
- Independent Principal Scientific Auditor
- Astronomical ML Benchmark Statistician
- Detection-Performance Reviewer
- Calibration and Statistical Integrity Auditor

**Audit Verdict:** **`AUDIT PASS`** — All trial records, calibration thresholds, exact Mann–Whitney AUROC calculations, AUPRC values, confusion matrices, and cluster-bootstrap multiset ranges have been **100% independently reproduced and verified**.  
**ASTROVISION Scientific Certification Status:** **`FAIL — NOT CERTIFIED`** (Model performance is scientifically insufficient for deployment or citizen-science discovery).

---

## 1. Executive Summary & Verdict

Following the completion of **Task 1.1R** (Authorized Execution of Restricted Five-Pointing Controlled Pilot Campaign), this independent audit evaluated the raw trial-level outputs, parameter calibrations, and statistical summaries generated across 2,500 controlled injection trials.

### Core Audit Findings
1. **Mathematical & Cryptographic Reproduction:**  
   Every summary metric published in `pilot_evaluation_metrics.json` and `calibration_parameters.json` was successfully recomputed from scratch using raw per-trial records in `astrovision_pilot_trial_results.csv`. Zero numerical discrepancies were detected.
2. **Absolute Data & Code Integrity:**  
   The frozen model checkpoint (`astrovision_spatial_v2.pt`), all 16 historical baseline assets, and 120 QR3 Level-2 FITS files were verified against their authoritative SHA-256 hashes without modification or leakage.
3. **Partition & Spatial Isolation:**  
   The five pre-planned partitions (500 trials each) were executed strictly within their designated pointing boundaries. Pointings `0001` and `0008` were exclusively utilized for calibration; Pointings `0002`, `0009`, and `0010` were strictly evaluated out-of-sample.
4. **Scientific Performance Assessment:**  
   While the campaign execution and data governance pass audit with highest rigor, ASTROVISION's underlying scientific detection capability is **critically deficient**:
   - **Point-Source Injections:** AUROC = **0.6861**, AUPRC = **0.6080**, Recovery Fraction at $\tau_d$ = **18.80% (94 / 500)**.
   - **Extended-Source Injections:** AUROC = **0.5704**, AUPRC = **0.5391**, Recovery Fraction at $\tau_d$ = **15.20% (76 / 500)**.
   - **False Positive Rate Inflation:** Empirical evaluation FPR reached **0.0860 (43 / 500)** (or **0.0900 (45 / 500)** without astrometric distance gating), statistically rejecting the nominal $\alpha = 0.05$ target ($p = 6.39 \times 10^{-4}$).
   - **Detector 4 Collapse:** Detector 4 (2.42–3.48 µm) failed completely with Point AUROC = **0.4776** (worse than random guessing) and Extended AUROC = **0.3041**.
   - **Pointing 0010 (NEP) Domain Collapse:** In the low-zodiacal North Ecliptic Pole field, Point AUROC dropped to **0.6143** and Extended AUROC collapsed to **0.4599**, demonstrating severe vulnerability to sky-background variation.

**Audit Conclusion:**  
- **Audit Verdict:** `AUDIT PASS` (Methodology, trial execution, and reported metrics verified).  
- **Model Certification:** `FAIL — NOT CERTIFIED`.

---

## 2. Campaign Integrity Audit

### 2.1 Governance & Asset Signatures
All 16 protected baseline assets and model checkpoints were independently hashed. Cryptographic comparison against pre-execution signatures confirmed zero mutation:

| Asset Path | Expected SHA-256 | Actual SHA-256 | Status |
| :--- | :--- | :--- | :--- |
| `checkpoints/astrovision_spatial_v2.pt` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **MATCH** |
| `data/processed/validation/pointing_0003_final_validated_catalogue.csv` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | `ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b` | **MATCH** |
| `data/processed/validation/astrovision_injection_manifest.csv` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | `339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978` | **MATCH** |
| `data/processed/validation/astrovision_injection_results.csv` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | `22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c` | **MATCH** |
| `reports/figures/astrovision/benchmark_metrics.json` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | `5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c` | **MATCH** |
| `reports/manifests/astrovision_task_1_1Q_authorization_review.json` | `853b08f6a828...` | `853b08f6a828...` | **MATCH** |
| `reports/manifests/astrovision_five_partition_pilot_manifest.csv` | `c1d83662b311f3f89efbe90f3c0ebd702c0ee58bcfae880dcd5d25e42eee0c0b` | `c1d83662b311f3f89efbe90f3c0ebd702c0ee58bcfae880dcd5d25e42eee0c0b` | **MATCH** |

### 2.2 Trial Reconciliation & Record Health
Independent parsing of `astrovision_pilot_trial_results.csv` established:
- **Total Rows:** Exactly 2,500 rows.
- **Unique Trial IDs:** Exactly 2,500 unique IDs (`PILOT_000001` through `PILOT_002500`). Zero duplicates.
- **Failed / Dropped Trials:** 0 (zero entries in `pilot_failed_trials.log`).
- **Data Completeness:** Critical columns (`model_target_peak_chi2`, `differential_residual_flux`, `is_detected`, `applied_threshold_tau`) exhibit **zero NaNs or infinite values**.

### 2.3 Partition Allocation & Spatial Isolation
The trial distribution across partitions and pointings conforms strictly to protocol:

```
+--------------------------------------+------+------+------+------+------+-------+
| Partition Name                       | P0001| P0002| P0008| P0009| P0010| Total |
+--------------------------------------+------+------+------+------+------+-------+
| CALIBRATION_CONTROL                  |  260 |    0 |  240 |    0 |    0 |   500 |
| CALIBRATION_INJECTION                |  260 |    0 |  240 |    0 |    0 |   500 |
| EVALUATION_CONTROL                   |    0 |  168 |    0 |  168 |  164 |   500 |
| EVALUATION_POINT_SOURCE_INJECTION    |    0 |  168 |    0 |  168 |  164 |   500 |
| EVALUATION_EXTENDED_SOURCE_INJECTION |    0 |  168 |    0 |  168 |  164 |   500 |
+--------------------------------------+------+------+------+------+------+-------+
| Total                                |  520 |  504 |  480 |  504 |  492 | 2,500 |
+--------------------------------------+------+------+------+------+------+-------+
```

Spatial disjointness between Calibration (`{0001, 0008}`) and Evaluation (`{0002, 0009, 0010}`) is absolute ($\text{overlap} = \emptyset$). Zero pointing contamination occurred.

---

## 3. Independent Detection Metric Reproduction

Detection metrics were recomputed from raw trial records using independent implementations:
- **AUROC:** Exact Mann–Whitney $U$ statistic formulation ($U / (n_1 n_2)$) and rank-sum integration.
- **Average Precision (AP):** Step-function precision-recall curve integration ($\sum (R_k - R_{k-1}) P_k$).
- **Uncertainty Intervals:** 95% Wilson score confidence intervals for all binomial proportions (Recovery and FPR).

### 3.1 Overall Pooled Metrics Reproduction Table

| Metric | Reported Value | Independently Recomputed | Difference | Binomial 95% Wilson Score CI | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Evaluation FPR (Astrometric)** | 0.0860 | 0.0860 (43 / 500) | 0.0000 | $[0.0645, 0.1138]$ | **VERIFIED** |
| **Evaluation FPR (Pure $\chi^2$)** | — | 0.0900 (45 / 500) | — | $[0.0679, 0.1183]$ | **VERIFIED** |
| **Point-Source AUROC** | 0.6861 | 0.6861 | 0.0000 | Cluster Boot: $[0.6143, 0.7388]$ | **VERIFIED** |
| **Point-Source AUPRC** | 0.6080 | 0.6080 | 0.0000 | — | **VERIFIED** |
| **Point-Source Recovery** | 0.1880 | 0.1880 (94 / 500) | 0.0000 | $[0.1562, 0.2246]$ | **VERIFIED** |
| **Point-Source Precision at $\tau_d$** | — | 0.6861 (94 / 137) | — | $[0.6044, 0.7578]$ | **VERIFIED** |
| **Extended-Source AUROC** | 0.5704 | 0.5704 | 0.0000 | Cluster Boot: $[0.4599, 0.6358]$ | **VERIFIED** |
| **Extended-Source AUPRC** | 0.5391 | 0.5391 | 0.0000 | — | **VERIFIED** |
| **Extended-Source Recovery** | 0.1520 | 0.1520 (76 / 500) | 0.0000 | $[0.1232, 0.1861]$ | **VERIFIED** |
| **Extended-Source Precision at $\tau_d$**| — | 0.6387 (76 / 119) | — | $[0.5492, 0.7191]$ | **VERIFIED** |

### 3.2 Evaluation Confusion Matrices at Calibrated $\tau_d$

#### Point-Source Injections (Partition 4 vs. Partition 3 Controls)
```
                  Predicted Positive    Predicted Negative    Total
Actual Positive          94 (TP)              406 (FN)         500
Actual Negative          43 (FP)              457 (TN)         500
Total                   137                   863             1,000
```
- **Sensitivity (Recall):** $94 / 500 = 18.80\%$ ($95\%\text{ CI}: [15.62\%, 22.46\%]$)
- **Specificity:** $457 / 500 = 91.40\%$ ($95\%\text{ CI}: [88.62\%, 93.55\%]$)
- **Precision (PPV):** $94 / 137 = 68.61\%$
- **Negative Predictive Value (NPV):** $457 / 863 = 52.95\%$

#### Extended-Source Injections (Partition 5 vs. Partition 3 Controls)
```
                  Predicted Positive    Predicted Negative    Total
Actual Positive          76 (TP)              424 (FN)         500
Actual Negative          43 (FP)              457 (TN)         500
Total                   119                   881             1,000
```
- **Sensitivity (Recall):** $76 / 500 = 15.20\%$ ($95\%\text{ CI}: [12.32\%, 18.61\%]$)
- **Specificity:** $457 / 500 = 91.40\%$ ($95\%\text{ CI}: [88.62\%, 93.55\%]$)
- **Precision (PPV):** $76 / 119 = 63.87\%$
- **Negative Predictive Value (NPV):** $457 / 881 = 51.87\%$

### 3.3 Methodological Edge Cases & Sanity Checks
- **Score Directionality:** Higher peak $\chi^2$ anomaly values correctly represent more anomalous responses.
- **Label Inversion:** Verified; class 1 corresponds to injected synthetic sources, class 0 corresponds to null controls.
- **Score Ties:** Zero score ties were found among evaluated pairs.
- **Failed Trials:** Handled with zero dropped records.

---

## 4. Calibration Audit & False Positive Transfer Analysis

### 4.1 Detector Operating Threshold Reproduction
Operating thresholds $\tau_d$ were designed to enforce an empirical false-alarm rate $\alpha = 0.05$ (95th percentile) using `CALIBRATION_CONTROL` trials in Pointings `0001` and `0008`.

| Detector | Bandpass (µm) | $N_{\text{cal}}$ | Reported $\tau_{95}$ | Independently Recomputed $\tau_{95}$ | Reported $\tau_{99}$ | Independently Recomputed $\tau_{99}$ | Error | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | 0.75 – 1.11 | 84 | 399.0363 | 399.0363 | 5,895.2400 | 5,895.2400 | 0.0 | **PASS** |
| **D2** | 1.11 – 1.63 | 84 | 2,120.0993 | 2,120.0993 | 8,796.9244 | 8,796.9244 | 0.0 | **PASS** |
| **D3** | 1.63 – 2.42 | 83 | 614.3817 | 614.3817 | 11,710.4187 | 11,710.4187 | 0.0 | **PASS** |
| **D4** | 2.42 – 3.48 | 83 | 1,007.3037 | 1,007.3037 | 5,838.7821 | 5,838.7821 | 0.0 | **PASS** |
| **D5** | 3.48 – 4.42 | 83 | 358.4182 | 358.4182 | 25,378.3256 | 25,378.3256 | 0.0 | **PASS** |
| **D6** | 4.42 – 5.00 | 83 | 183.7052 | 183.7052 | 886.6809 | 886.6809 | 0.0 | **PASS** |

### 4.2 Calibration Isolation & Quantile Methodology
1. **Calibration Control Isolation:** Auditing confirmed that only null controls from Partition 1 were used to fit $\tau_d$. Calibration injections (Partition 2) were utilized solely to fit transfer curves ($C_{50}, C_{90}$), with zero influence on threshold selection.
2. **Evaluation Blindness:** Evaluation trials (Partitions 3, 4, 5) were strictly excluded during calibration.
3. **Quantile Method:** Quantiles were calculated via linear interpolation (`numpy.percentile`), matching standard continuous empirical CDF definitions.

### 4.3 Out-of-Sample False Positive Inflation Analysis
On the unseen evaluation cohort (Pointings `0002`, `0009`, `0010`), the empirical false positive rate inflated to:
$$\widehat{\text{FPR}} = \frac{43}{500} = 8.60\% \quad (95\%\text{ Wilson CI: } [6.45\%, 11.38\%])$$

#### Investigation of FPR Inflation Root Causes:
1. **Statistical Significance (Not Finite-Sample Noise):**  
   A two-sided exact binomial test comparing $43 / 500$ against the null hypothesis $H_0: p = 0.05$ yields:
   $$p = 6.392 \times 10^{-4} \quad (\ll 0.001)$$
   The 95% confidence interval strictly excludes 0.05. Therefore, the observed elevation is **not a statistical fluctuation**, but an empirical failure of calibration transfer.
2. **Astrometric Gating Effect:**  
   In the evaluation driver, a trial was marked `is_detected = True` only if both $\chi^2 \ge \tau_d$ **and** centroid error $\le 2.5$ pixels.
   - Without astrometric gating (pure $\chi^2 \ge \tau_d$): $45 / 500 = 9.00\%$.
   - Two control cutouts (`PILOT_001085` on D1 and `PILOT_001216` on D6) produced noise spikes with $\chi^2 > \tau_d$ but had peak centroids at distances of $2.71''$ and $2.88''$ from the cutout center, thereby evading classification.
3. **Domain Shift in Detectors 1 & 4:**  
   - In **D1**, the 95th percentile of evaluation controls was $\chi^2 = 2,714.90$ (compared to $\tau_{95} = 399.04$ in calibration), causing the D1 evaluation FPR to explode to **19.05% (16 / 84)**.
   - In **D4**, the 95th percentile of evaluation controls was $\chi^2 = 1,814.69$ (compared to $\tau_{95} = 1,007.30$ in calibration), driving the D4 evaluation FPR to **10.84% (9 / 83)**.
   - This proves that a single static threshold per detector cannot accommodate inter-pointing spatial background fluctuations.

---

## 5. Statistical Uncertainty & Cluster Bootstrap Audit

### 5.1 Pointing Cluster Resampling Assessment
The evaluation dataset contains exactly $G_{\text{eval}} = 3$ independent pointing clusters (`0002`, `0009`, `0010`).

In accordance with survey cluster bootstrap theory, resampling must be conducted at the pointing cluster level (preserving all intra-cluster spatial and detector correlations), rather than drawing individual trials independently.

### 5.2 Enumeration of Distinct Bootstrap Multisets
For $K = 3$ clusters sampled with replacement, the number of distinct unordered multisets is given by:
$$M = \binom{K + K - 1}{K} = \binom{5}{3} = 10$$

Every multiset was audited and evaluated independently:

| Multiset Index | Resampled Cluster Combination | Point-Source AUROC | Extended-Source AUROC |
| :---: | :---: | :---: | :---: |
| 1 | `[0002, 0002, 0002]` | 0.7388 | 0.6358 |
| 2 | `[0002, 0002, 0009]` | 0.7257 | 0.6258 |
| 3 | `[0002, 0002, 0010]` | 0.7001 | 0.5783 |
| 4 | `[0002, 0009, 0009]` | 0.7136 | 0.6169 |
| 5 | `[0002, 0009, 0010]` *(Observed Sample)* | **0.6861** | **0.5704** |
| 6 | `[0002, 0010, 0010]` | 0.6586 | 0.5197 |
| 7 | `[0009, 0009, 0009]` | 0.7025 | 0.6092 |
| 8 | `[0009, 0009, 0010]` | 0.6730 | 0.5636 |
| 9 | `[0009, 0010, 0010]` | 0.6436 | 0.5139 |
| 10 | `[0010, 0010, 0010]` | 0.6143 | 0.4599 |

**Reproduction Check:**  
- Reported Point-Source Range: $[0.6143, 0.7388]$ ($\Delta = 0.1245$) — **MATCH (100%)**
- Reported Extended-Source Range: $[0.4599, 0.6358]$ ($\Delta = 0.1759$) — **MATCH (100%)**

### 5.3 Assessment of Percentile Confidence Intervals
> [!WARNING]
> **Statistical Limitation Notice:** With only $G = 3$ clusters, empirical percentile confidence intervals (e.g., attempting to extract 2.5% and 97.5% quantiles) are **statistically invalid**.
> 
> A sample of 10 discrete multisets has a minimum step size of 10% and cannot satisfy asymptotic normality or bootstrap consistency. Reporting the full multiset range $[0.6143, 0.7388]$ was methodologically appropriate and honest, but this range reflects only pointing-to-pointing heterogeneity among these three specific fields, not a survey-wide population confidence interval.

---

## 6. Detector-Wise Performance Reproduction

| Detector | Bandpass (µm) | Eval Null Count | Eval FPR | Point AUROC | Point Recovery | Extended AUROC | Extended Recovery |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | 0.75 – 1.11 | 84 | 0.1905 | 0.7188 | 0.4405 | 0.6087 | 0.2738 |
| **D2** | 1.11 – 1.63 | 84 | 0.0595 | 0.6835 | 0.0595 | 0.4957 | 0.0357 |
| **D3** | 1.63 – 2.42 | 83 | 0.0602 | 0.7216 | 0.1687 | 0.5992 | 0.2048 |
| **D4** | 2.42 – 3.48 | 83 | 0.1084 | **0.4776** | **0.0482** | **0.3041** | **0.0602** |
| **D5** | 3.48 – 4.42 | 83 | 0.0361 | 0.7596 | 0.0602 | 0.6847 | 0.0964 |
| **D6** | 4.42 – 5.00 | 83 | 0.0602 | **0.8763** | **0.3494** | **0.7750** | **0.2410** |

All recomputed values match `pilot_evaluation_metrics.json` with zero discrepancy.

---

## 7. Pointing-Wise Performance Reproduction

| Pointing | Sky Coordinates $(\alpha, \delta)$ | Zodiacal / Field Description | Eval FPR | Point AUROC | Point Recovery | Extended Recovery |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0002** | $(240.0^\circ, +4.8^\circ)$ | Equatorial Zodiacal Sky | 0.0893 | 0.7388 | 0.2321 | 0.1905 |
| **0009** | $(240.2^\circ, +7.4^\circ)$ | Mid-Latitude Survey Sky | 0.1190 | 0.7025 | 0.1845 | 0.1726 |
| **0010** | $(270.0^\circ, +66.6^\circ)$| North Ecliptic Pole (NEP Low-Zodi) | 0.0488 | **0.6143** | **0.1463** | **0.0915** |

All recomputed values match `pilot_evaluation_metrics.json` with zero discrepancy.

---

## 8. Detector 4 In-Depth Investigation

Detector 4 exhibits catastrophic failure:
- **Point-Source AUROC:** **0.4776** (below chance / worse than coin flipping).
- **Extended-Source AUROC:** **0.3041** (strongly inverted).
- **Point Recovery Fraction:** **4.82% (4 / 83)**.

### Detailed Distribution Breakdown for D4
Independent inspection of the raw $\chi^2$ score distributions reveals the failure mechanism:

```
+------------------------------------+-------+---------+----------+------------+--------------+
| D4 Partition                       | Count | Median  | Mean     | 90th %-ile | Max Value    |
+------------------------------------+-------+---------+----------+------------+--------------+
| CALIBRATION_CONTROL                |    83 |   85.31 |   374.24 |     419.25 |    10,515.58 |
| CALIBRATION_INJECTION              |    83 |  253.34 |   374.02 |     552.76 |     3,195.35 |
| EVALUATION_CONTROL                 |    83 |  283.80 | 5,891.18 |   1,006.82 |   410,561.84 |
| EVALUATION_POINT_INJECTION         |    83 |  298.03 |   349.68 |     636.84 |     1,196.43 |
| EVALUATION_EXTENDED_INJECTION      |    83 |  154.42 |   333.51 |     570.30 |     3,105.44 |
+------------------------------------+-------+---------+----------+------------+--------------+
```

### Forensic Causes of D4 Collapse
1. **Inverted Score Distributions:**  
   In Evaluation, the median null-control anomaly score ($\text{median} = 283.80$) is **higher** than the median extended-injection score ($\text{median} = 154.42$) and virtually indistinguishable from point injections ($\text{median} = 298.03$). Because null controls routinely generate higher $\chi^2$ peaks than actual injections, the rank-sum statistic places negative examples above positive examples, driving AUROC below 0.50.
2. **Extreme Outliers in Null Backgrounds:**  
   Evaluation controls on D4 reached an extreme maximum $\chi^2$ of **410,561.84** (in Pointing 0009). The D4 bandpass (2.42–3.48 µm) coincides with thermal emission and strong atmospheric/zodiacal transition gradients. Unmasked bad pixel clusters and thermal gradient residuals produce massive false $\chi^2$ responses that overpower true transient signals.
3. **Model Feature Mismatch:**  
   The frozen spatial conv2d model was trained on pointing `0003` (where D4 noise characteristics differed). When evaluating out-of-sample fields, the paired residual differencing fails to suppress D4 systematic structure, leading to total detection collapse.

---

## 9. Pointing 0010 (NEP) Domain Shift Investigation

Pointing `0010` is centered at the North Ecliptic Pole ($\beta = +90^\circ$). It represents the darkest, lowest-zodiacal-background region in the SPHEREx mission.

### Findings on Pointing 0010 Performance
1. **Metric Degradation:**  
   - Point-Source AUROC dropped to **0.6143** (compared to 0.7388 in P0002).
   - Extended-Source AUROC collapsed to **0.4599** (worse than random guessing).
   - Recovery rates were the lowest among all pointings: **14.63%** (point) and **9.15%** (extended).
2. **Score Distribution Inversion:**  
   - Median Null Control $\chi^2$: **125.37**
   - Median Point Injection $\chi^2$: **215.72**
   - Median Extended Injection $\chi^2$: **120.01**  
   In Pointing 0010, the median null control generated a higher anomaly response than the median extended injection ($125.37 > 120.01$).
3. **Physical & Algorithmic Cause:**  
   Because the celestial background is exceptionally quiet at the NEP, photon noise is reduced. However, ASTROVISION's conv2d weights were trained on a high-background field (`0003`). In low-background regimes, faint structural differences and subtle instrument flat-field errors dominate over Poisson noise. The network cannot dynamically re-scale its convolutional activations, causing true faint extended sources to be buried beneath systematic residual artifacts.

---

## 10. Scientific Claim Assessment

In compliance with Task 1.1S audit specifications, all six candidate scientific claims are formally evaluated:

| Claim | Status | Evidence & Deficiencies |
| :--- | :---: | :--- |
| **1. ASTROVISION reliably detects injected point sources.** | **NOT SUPPORTED** | Pooled recovery at calibrated operating threshold is only **18.80% (94 / 500)**. Even at high SNR ($\text{SNR} = 25$), recovery is only **46.27%** ($<50\%$), far below the $\ge 90\%$ standard required for astronomical surveys. D4 AUROC is $0.4776$. |
| **2. ASTROVISION reliably detects extended sources.** | **NOT SUPPORTED** | Pooled recovery is only **15.20% (76 / 500)**. AUROC is **0.5704** (barely above random guessing), and drops to **0.4599** at the NEP. The network's spatial filters fail to recognize diffuse/extended transient morphologies. |
| **3. Detector-specific calibration transfers to unseen pointings.** | **NOT SUPPORTED** | The empirical evaluation FPR on unseen pointings inflated to **8.60%** (and **9.00%** un-gated), statistically rejecting the nominal 5.0% target ($p = 6.39 \times 10^{-4}$). In D1, FPR reached **19.05%**, demonstrating severe transfer breakdown. |
| **4. The model is robust across all six detectors.** | **NOT SUPPORTED** | Huge performance disparity exists: while D6 achieves Point AUROC = **0.8763**, D4 completely collapses to Point AUROC = **0.4776**. D2 recovers only **5.95%** of point sources. The model cannot be deployed uniformly. |
| **5. The model generalizes to low-background fields.** | **NOT SUPPORTED** | Pointing 0010 (NEP) showed substantial degradation: Point AUROC dropped to **0.6143** and Extended AUROC fell to **0.4599**, with control anomaly scores exceeding extended injection scores. |
| **6. The model is ready for citizen-science candidate discovery.** | **NOT SUPPORTED** | High false positive rate (8.6% per cutout) would swamp citizen-science pipelines with false alarms, while missing $>81\%$ of genuine point sources and $>84\%$ of extended sources. |

---

## 11. Confirmed Defects vs. Unresolved Concerns

### Confirmed Defects (Mathematically & Scientifically Proven)
1. **Defect 1 — Detector 4 Algorithmic Blindness:**  
   D4 AUROC ($0.4776$) is worse than a random classifier. Null-control residuals have higher median $\chi^2$ anomaly scores than injections.
2. **Defect 2 — Inability to Recover Extended Sources:**  
   Pooled AUROC of $0.5704$ confirms that the current architecture and weights cannot distinguish diffuse transient anomalies from background noise.
3. **Defect 3 — Calibration Transfer Vulnerability:**  
   Static scalar operating thresholds $\tau_d$ calibrated on two pointings fail out-of-sample, producing statistically significant FPR inflation ($p < 0.001$).
4. **Defect 4 — Low Detection Efficiency at Operating Thresholds:**  
   An overall recovery fraction of $<19\%$ at $\alpha = 0.05$ demonstrates that ASTROVISION lacks the sensitivity required for operational astronomical alerting.

### Unresolved Concerns (Requiring Future Specialized Investigations)
1. **Unresolved Concern 1 — Source-Density Mismatch:**  
   Does pointing-to-pointing variations in stellar crowding affect the residual differencing baselines differently across detectors?
2. **Unresolved Concern 2 — Impact of D4 Bandpass Physical Physics:**  
   Is D4's failure exacerbated by unflagged cosmic rays, ice-band filter transitions, or detector non-linearities in the QR3 pipeline?
3. **Unresolved Concern 3 — Dynamic Background Normalization:**  
   Could adaptive local-variance or robust Z-score normalization restore calibration transfer across diverse zodiacal sky backgrounds?

---

## 12. Recommended Next Experiments & Remediation Roadmap

The frozen ASTROVISION checkpoint must not be deployed in production. The following remediation path is scientifically recommended:

1. **Architecture & Preprocessing Remediation:**
   - Implement **Local Adaptive Noise Scaling (LANS)** before feeding differenced cutouts into conv2d layers, neutralizing field-to-field zodiacal background shifts.
   - Introduce multi-scale morphological pooling or dedicated extended-source kernels to recover diffuse emission.
2. **Band-Specific Retraining / Fine-Tuning:**
   - Retrain or fine-tune ASTROVISION using a stratified multi-pointing training set encompassing diverse ecliptic latitudes and zodiacal background regimes (e.g., mixing high-zodi, mid-zodi, and NEP pointings).
   - Treat Detector 4 with detector-specific loss re-weighting or retrain a dedicated D4 specialist head.
3. **Dynamic Calibration Transfer:**
   - Replace fixed scalar threshold $\tau_d$ with an **empirical Bayesian or quantile-regression threshold model** that conditions $\tau$ on local image background and aperture variance.
4. **Expanded Survey-Scale Benchmark:**
   - Authorize a larger 10-to-20 pointing controlled benchmark once a remediated candidate model (`astrovision_v3`) is frozen.

---

## 13. Reproducibility Details & Deliverable Manifests

### 13.1 Audit Manifest
A machine-readable JSON manifest recording all recomputed values, hashes, and statistical test outputs was generated:
- **Audit Manifest:** [`reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json)

### 13.2 Key Deliverable Signatures
```
checkpoints/astrovision_spatial_v2.pt:
  f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557
data/processed/pilot_results/astrovision_pilot_trial_results.csv:
  4afddbb31d9f1b579d711712da431bf1c19701d7a63d25e9a06995a71c9d523f
data/processed/pilot_results/calibration_parameters.json:
  4a5bbe8a04dffb609b507eba45f0d34a1ebb235e18d2f586bbad4906f09a46ac
data/processed/pilot_results/pilot_evaluation_metrics.json:
  688b98d123b3cd5bc942a1bda050ee88ccbf03132c038ed09605cd1a22e14393
reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json:
  (Generated and verified during Task 1.1S)
```

### 13.3 Repository Test Suite
All 74 repository regression tests were executed and confirmed passing in strictly read-only mode:
- **Command:** `pytest tests/ -q`
- **Result:** **74 passed in 16.40s**

---

## 14. Explicit Audit Limitations

1. **Exclusion of Model Retraining:**  
   In compliance with audit governance, zero model retraining, weight adjustments, or hyperparameter tuning were attempted.
2. **Evaluated Cohort Size:**  
   The evaluation was limited to the 1,500 trials in Pointings `0002`, `0009`, and `0010`. While statistically conclusive for the pilot cohort, wide-area sky performance ($>100$ pointings) cannot be extrapolated without further testing.
3. **Threshold Immutability:**  
   Operating thresholds were strictly frozen to those determined during Stage 1 calibration. No post-hoc threshold adjustment was permitted.

---

## 15. Final Governance Verdict

In accordance with Section 9 of the Task 1.1S audit specifications:

1. **Audit Process Conclusion:**  
   **`AUDIT PASS`**  
   The Task 1.1R controlled pilot campaign was executed with impeccable scientific governance, cryptographic traceability, and zero data leakage. All trial records and summary metrics published by the campaign are **100% mathematically correct and independently reproduced**.

2. **ASTROVISION Scientific Certification Status:**  
   **`FAIL — NOT CERTIFIED`**  
   Passing the independent audit confirms the scientific integrity and truthfulness of the reporting. That reporting conclusively demonstrates that **ASTROVISION spatial v2 fails to achieve reliable transient recovery** across detectors and sky backgrounds.

**Remediation is mandatory before any future benchmark execution or deployment.**

