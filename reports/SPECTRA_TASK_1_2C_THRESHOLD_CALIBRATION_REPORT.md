# SPECTRA-X / F1 — Phase 3, Task 1.2C: SPECTRA Provisional-Null Threshold Calibration Report

**Task Identifier:** `SPECTRA_TASK_1_2C`  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Timestamp:** 2026-11-07T04:26:30Z  
**Execution Status:** COMPLETED & FROZEN  
**Execution Mode:** Controlled Statistical Calibration (Strict Governance Boundary)  
**Authorization Basis:** Explicitly Authorized by Project Owner  
**Module Calibrated:** SPECTRA — 102-Channel Infrared Spectral Anomaly Detection Engine  

---

## 1. Executive Summary

Task 1.2C executed a controlled, reproducible threshold-calibration campaign for the frozen candidate checkpoint `checkpoints/spectra_masked_ae_v2.pt`. In strict adherence to the preconditions established in Tasks 1.2B-R and 1.2B-S, empirical provisional-null anomaly-score reference thresholds were derived exclusively from Pointing `0008` provisional control candidates ($N = 3,206$ sources), completely independent of both historical model training data (Pointing `0001`) and the untouched blind evaluation cohort (Pointings `0002`, `0009`, `0010`).

### Key Calibration Deliverables & Quantitative Summary

1. **Immutable Checkpoint Integrity:**  
   The frozen model checkpoint `checkpoints/spectra_masked_ae_v2.pt` was verified byte-for-byte immutable (`SHA-256: 6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938`). Zero retraining, parameter tuning, or model modification occurred.
2. **Reconciled Cohort Scoring:**  
   All **3,206** eligible Pointing `0008` provisional control candidates (`RELIABLE_ISOLATED_POINT_SOURCE` with $N_{\text{valid}} \ge 5$ channels) were scored using the audited, mask-aware, inverse-variance weighted reconstruction loss ($\text{masked\_chi2}$). Zero sources failed, produced non-finite values, or were excluded post-scoring.
3. **Detector-Pair Stratification Necessity Confirmed:**  
   Reconstruction error distributions demonstrate severe physical domain shifts between optical detector arrays:
   - Near-infrared pair (`D1+D4`, 0.74–3.85 $\mu\text{m}$): median score $0.4237$.
   - Intermediate pair (`D2+D5`, 1.09–4.44 $\mu\text{m}$): median score $0.3689$.
   - Thermal-infrared pair (`D3+D6`, 1.62–5.02 $\mu\text{m}$): median score $1.4255$ ($\approx 4\times$ higher due to spacecraft/zodiacal thermal emission in Detector D6 at 4.4–5.0 $\mu\text{m}$).
   *Conclusion:* Pooling pairs into a single global threshold would produce catastrophic false-positive inflation in D3+D6 and total sensitivity suppression in D1+D4. Pair-stratified thresholds are mandatory.
4. **Derived Empirical Thresholds & Bootstrap Confidence Intervals:**  
   Separate nominal $\alpha = 0.05$ (95th percentile) and $\alpha = 0.01$ (99th percentile) thresholds were calculated via linear quantile interpolation (Type 7) and bound by $B=2,000$ source-level bootstrap replicates:
   - **`D1+D4` ($N=1,055$):**  
     $T_{0.05} = \mathbf{4.127549}$ (95% CI: $[2.760024, 6.186414]$)  
     $T_{0.01} = \mathbf{61.267565}$ (95% CI: $[24.229503, 152.581432]$)
   - **`D2+D5` ($N=1,304$):**  
     $T_{0.05} = \mathbf{5.515796}$ (95% CI: $[4.153830, 7.292314]$)  
     $T_{0.01} = \mathbf{181.601329}$ (95% CI: $[44.371465, 913.888583]$)
   - **`D3+D6` ($N=847$):**  
     $T_{0.05} = \mathbf{19.266649}$ (95% CI: $[12.848656, 25.080652]$)  
     $T_{0.01} = \mathbf{862.972346}$ (95% CI: $[168.930601, 3668.691406]$)
5. **Spatial Independence & Generalization Safeguards:**  
   Moran's I spatial autocorrelation analysis confirmed near-zero spatial dependence across Pointing `0008` (Moran's $I \approx -0.002$). However, because calibration was conducted on a single high Galactic latitude pointing ($b \approx -50^\circ$), these thresholds represent **Empirical Provisional-Null Quantiles**, NOT production-certified false-positive rates.

---

## 2. Execution Authorization and Scope

### Authorization Basis
Execution was formally authorized by the Project Owner under Phase 3 Task 1.2C following successful completion of Preflight Audit (Task 1.2A), Multi-Pointing Extraction (Task 1.2B), Calibration Readiness Audit (Task 1.2B-R), and Cohort Reconciliation (Task 1.2B-S).

### Boundaries & Restrictions
- **Zero Blind Evaluation Contact:** Pointings `0002`, `0009`, and `0010` were completely firewalled. Zero evaluation labels, spectra, scores, or performance metrics were inspected or computed.
- **Zero Model Modification:** Checkpoint weights and forward architecture were held frozen.
- **Zero Threshold Manipulation:** Thresholds were derived purely from the empirical distribution of P0008 scores without manual adjustment or tuning.

---

## 3. Frozen Model / Checkpoint Verification

Prior to inference, the model checkpoint was cryptographically verified:

```text
Path: checkpoints/spectra_masked_ae_v2.pt
SHA-256: 6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938
Architecture: MaskedSpectralAutoencoder (Linear 204->64 -> LayerNorm -> GELU -> Linear 64->64 -> GELU -> Linear 64->16 Bottleneck -> Linear 16->64 -> GELU -> Linear 64->64 -> GELU -> Linear 64->102 Decoder)
Config Parameters: num_channels=102, hidden_dim=64, latent_dim=16, f_sys=0.0193
Trained Epoch: 23, Validation Loss: 0.001044
```

The SHA-256 hash strictly matches the preflight ledger established in Task 1.2A and verified in Task 1.2B-S.

---

## 4. Dataset Provenance and Cohort Reconciliation

In accordance with Task 1.2B-S:
1. **Primary Dataset:** Extracted 102-channel SED vectors from `data/processed/spectra/phase3_multpointing_spectra_v1.csv` and Gaia DR3 astrometric classifications from `data/processed/pilot_catalogues/pointing_0008_source_catalogue.csv`.
2. **Eligibility Criteria:**
   - Telescope Pointing: `0008` only.
   - Astrometric Quality: `classification_category == 'RELIABLE_ISOLATED_POINT_SOURCE'`.
   - Spectral Completeness: `valid_channels_count >= 5`.
3. **Exact Stratum Verification:**
   - Stratum `D1,D4`: Exactly **1,055 sources**.
   - Stratum `D2,D5`: Exactly **1,304 sources**.
   - Stratum `D3,D6`: Exactly **847 sources**.
   - Total Scored: **3,206 sources**.
4. **Zero Training Overlaps:**  
   Cross-matching confirmed that zero sources in the primary P0008 cohort match the historical training dataset (`validation_assembled_spectra.csv`), confirming 100% out-of-sample null status.

---

## 5. Calibration Score-Path Audit

The exact scoring pipeline was audited from `models/spectra/train_masked_spectra.py` and `models/spectra/evaluate_spectra.py`:

### Mathematical Scoring Specification:
1. **Valid Channel Subsetting:** Let $m \in \{0, 1\}^{102}$ be the binary `valid_channel_mask`.
2. **Median Normalization:**  
   $$\text{scale} = \text{median}(\{F_j : m_j = 1\})$$
   $$x_i = \begin{cases} F_i / \text{scale} & \text{if } m_i = 1 \\ 0.0 & \text{if } m_i = 0 \end{cases}$$
3. **Systematic Error Floor & Inverse-Variance Weights:**  
   $$\sigma_{\text{norm}, i} = \sigma_i / \text{scale}$$
   $$\text{Var}_{\text{tot}, i} = \max\left(\sigma_{\text{norm}, i}^2 + (f_{\text{sys}} \cdot x_i)^2, \, 10^{-4}\right), \quad f_{\text{sys}} = 0.0193$$
   $$w_i = \begin{cases} \text{clip}\left(\frac{1}{\text{Var}_{\text{tot}, i}}, \, 0.01, \, 100.0\right) & \text{if } m_i = 1 \\ 0.0 & \text{if } m_i = 0 \end{cases}$$
4. **Autoencoder Forward Pass:**  
   $$x_{\text{in}} = [x, m] \in \mathbb{R}^{204} \implies \hat{x} = \text{Model}(x_{\text{in}}) \in \mathbb{R}^{102}$$
5. **Masked $\chi^2$ Anomaly Score:**  
   $$\text{Score} = \frac{\sum_{i=0}^{101} m_i w_i (\hat{x}_i - x_i)^2}{\sum_{i=0}^{101} m_i w_i + 10^{-6}}$$

All 3,206 sources were scored using this identical formulation on an NVIDIA GeForce RTX GPU.

---

## 6. Detector-Pair-Specific Score Distributions

### Table 6.1: Distribution Diagnostics by Detector-Pair Stratum

| Statistic / Diagnostic | Stratum `D1+D4` | Stratum `D2+D5` | Stratum `D3+D6` | Pooled (For Reference Only) |
|:---|---:|---:|---:|---:|
| **Sample Size ($N$)** | **1,055** | **1,304** | **847** | 3,206 |
| **Minimum Score** | 0.015272 | 0.003177 | 0.039759 | 0.003177 |
| **25th Percentile ($Q_1$)** | 0.252033 | 0.229166 | 0.999881 | 0.278912 |
| **Median Score ($Q_2$)** | **0.423666** | **0.368894** | **1.425457** | **0.457811** |
| **75th Percentile ($Q_3$)** | 0.696207 | 0.570793 | 2.094155 | 0.812498 |
| **Interquartile Range ($\text{IQR}$)** | 0.444174 | 0.341627 | 1.094274 | 0.533586 |
| **Mean Score** | 62.968822 | 201.051045 | 773.357579 | 306.941215 |
| **Standard Deviation** | 1,917.078152 | 4,235.502115 | 15,983.556434 | 8,683.412095 |
| **Maximum Score** | 62,277.851562 | 130,613.750000 | 410,039.187500 | 410,039.187500 |
| **90th Percentile** | 1.831552 | 1.637508 | 7.420119 | 2.114509 |
| **95th Percentile ($\alpha = 0.05$)** | **4.127549** | **5.515796** | **19.266649** | **6.678124** |
| **97.5th Percentile** | 12.015482 | 17.841509 | 78.412501 | 24.115891 |
| **99th Percentile ($\alpha = 0.01$)** | **61.267565** | **181.601329** | **862.972346** | **234.501981** |
| **Exceedance Count ($>95\text{th}$)** | 53 (5.02%) | 66 (5.06%) | 43 (5.08%) | 161 (5.02%) |
| **Exceedance Count ($>99\text{th}$)** | 11 (1.04%) | 14 (1.07%) | 9 (1.06%) | 33 (1.03%) |
| **Ties Near Threshold ($\pm 10^{-5}$)** | 0 | 0 | 0 | 0 |

### Physical Interpretation of Distribution Shift:
The median reconstruction error in D3+D6 ($1.425$) is almost four times higher than in D2+D5 ($0.369$), and the 95th percentile threshold ($19.27$) is nearly five times higher than in D1+D4 ($4.13$). This is directly attributable to the physical properties of Detector D6 (4.42–5.02 $\mu\text{m}$), where background thermal photon rates and detector dark current increase residual variance. Stratifying thresholds prevents D3+D6 from dominating the false-alarm budget.

---

## 7. 95th and 99th Percentile Thresholds

### Table 7.1: Calibrated Operational Provisional-Null Thresholds

| Detector-Pair Stratum | Wavelength Coverage | Nominal $\alpha = 0.05$ Threshold | Nominal $\alpha = 0.01$ Threshold | Quantile Estimation Method |
|:---:|:---:|:---:|:---:|:---:|
| **`D1+D4`** | 0.74–1.12 $\mu\text{m}$ & 2.40–3.85 $\mu\text{m}$ | **`4.127549`** | **`61.267565`** | Type 7 (`numpy.percentile`, linear) |
| **`D2+D5`** | 1.09–1.66 $\mu\text{m}$ & 3.80–4.44 $\mu\text{m}$ | **`5.515796`** | **`181.601329`** | Type 7 (`numpy.percentile`, linear) |
| **`D3+D6`** | 1.62–2.43 $\mu\text{m}$ & 4.41–5.02 $\mu\text{m}$ | **`19.266649`** | **`862.972346`** | Type 7 (`numpy.percentile`, linear) |

---

## 8. Bootstrap Uncertainty Results

To assess finite-sample quantile variability, $B = 2,000$ source-level bootstrap replicates (resampling with replacement under `seed = 42`) were evaluated independently within each stratum:

### Table 8.1: Source-Level Bootstrap Confidence Intervals ($B = 2,000$)

| Stratum | Nominal Alpha | Derived Threshold | Bootstrap Median | Bootstrap 95% Confidence Interval | Bootstrap Standard Error ($\text{SE}$) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **`D1+D4`** | $\alpha = 0.05$ | 4.127549 | 4.092415 | **$[2.760024, \, 6.186414]$** | 0.848238 |
| **`D1+D4`** | $\alpha = 0.01$ | 61.267565 | 58.914210 | **$[24.229503, \, 152.581432]$** | 32.353974 |
| **`D2+D5`** | $\alpha = 0.05$ | 5.515796 | 5.487120 | **$[4.153830, \, 7.292314]$** | 0.719693 |
| **`D2+D5`** | $\alpha = 0.01$ | 181.601329 | 169.412850 | **$[44.371465, \, 913.888583]$** | 226.847887 |
| **`D3+D6`** | $\alpha = 0.05$ | 19.266649 | 19.014280 | **$[12.848656, \, 25.080652]$** | 3.637210 |
| **`D3+D6`** | $\alpha = 0.01$ | 862.972346 | 784.152400 | **$[168.930601, \, 3668.691406]$** | 725.900540 |

### Analysis of Tail Uncertainty
- At $\alpha = 0.05$, bootstrap standard errors are tight relative to the threshold magnitude ($\text{SE} / T \approx 13\%\text{--}20\%$).
- At $\alpha = 0.01$, tail sample counts are modest ($E[K] \approx 8\text{--}13$ events per stratum), leading to wide confidence intervals. This confirms the statistical risk identified in Task 1.2B-S: $\alpha = 0.01$ thresholds have non-negligible finite-sample variance.

---

## 9. Spatial Dependence Investigation and Limitations

### 9.1 Spatial Autocorrelation (Moran's I)
Using celestial coordinates $(\alpha, \delta)$ and a $k=8$ nearest-neighbor spatial weight matrix, Moran's $I$ statistic was computed for anomaly scores within each stratum:

- `D1+D4`: $I = -0.0012$ (Expected $I_0 = -0.0009$)
- `D2+D5`: $I = -0.0023$ (Expected $I_0 = -0.0008$)
- `D3+D6`: $I = -0.0030$ (Expected $I_0 = -0.0012$)

*Finding:* Moran's $I$ is within $0.002$ of its theoretical expectation under spatial randomness, indicating **negligible local spatial clustering** of anomaly scores across Pointing `0008`.

### 9.2 Spatial-Block Bootstrap Sensitivity Analysis
To test robustness against potential unmodeled large-scale background gradients, spatial block bootstrap resampling was executed across multiple plausible block dimensions ($0.5^\circ, 1.0^\circ, 2.0^\circ$):

### Table 9.2: Spatial-Block Bootstrap Sensitivity Comparison (1,000 Replicates)

| Stratum | Grid Block Size | Occupied Blocks | Median Sources / Block | 95th Percentile CI ($0.05$) | 99th Percentile CI ($0.01$) |
|:---:|:---:|:---:|:---:|:---:|:---:|
| **`D1+D4`** | $0.5^\circ \times 0.5^\circ$ | 82 blocks | 11.5 | $[2.315012, \, 7.124509]$ | $[12.451082, \, 162.401928]$ |
| **`D1+D4`** | $1.0^\circ \times 1.0^\circ$ | 32 blocks | 31.0 | $[2.287163, \, 7.796109]$ | $[11.202302, \, 141.076035]$ |
| **`D1+D4`** | $2.0^\circ \times 2.0^\circ$ | 12 blocks | 85.5 | $[2.114502, \, 8.412501]$ | $[9.841520, \, 184.215091]$ |
| **`D2+D5`** | $1.0^\circ \times 1.0^\circ$ | 34 blocks | 38.0 | $[4.595621, \, 7.246753]$ | $[26.688107, \, 466.249420]$ |
| **`D3+D6`** | $1.0^\circ \times 1.0^\circ$ | 31 blocks | 27.0 | $[13.329847, \, 24.177656]$ | $[402.079882, \, 4866.225098]$ |

*Conclusion:* The 95th percentile confidence intervals under $1.0^\circ$ block bootstrap closely track the source-level bootstrap intervals ($[2.29, 7.80]$ vs $[2.76, 6.19]$ for D1+D4; $[4.60, 7.25]$ vs $[4.15, 7.29]$ for D2+D5). This confirms that local spatial correlation does not significantly bias the 95th percentile threshold.

### 9.3 Single-Pointing Generalization Constraint
Pointing `0008` is located at Galactic coordinates $(l \approx 150^\circ, b \approx -50^\circ)$ in a region of relatively low interstellar extinction and moderate zodiacal background. **These thresholds cannot be assumed to transfer perfectly to crowded Galactic plane fields or high-cirrus regions.** Between-pointing variance can only be measured during subsequent evaluation tasks.

---

## 10. Blind-Evaluation Firewall Evidence

Strict data governance boundaries were enforced throughout this task:

1. **Blind Evaluation Pointings:** Pointings `0002`, `0009`, and `0010` were completely firewalled. Zero FITS files, source catalogs, spectral vectors, or anomaly labels from these pointings were ingested.
2. **Evaluation Metrics:** Zero evaluation false positive rates, AUROC, AUPRC, or synthetic injection recoveries were calculated.
3. **Training Separation:** Pointing `0001` was excluded from primary calibration; the 5 historical training overlap sources were confirmed absent from P0008.

---

## 11. Test Suite Results

The dedicated verification test suite [`tests/test_spectra_task_1_2c_calibration.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/tests/test_spectra_task_1_2c_calibration.py) was executed to validate all deliverables:

```text
tests/test_spectra_task_1_2c_calibration.py::test_frozen_checkpoint_integrity PASSED [ 16%]
tests/test_spectra_task_1_2c_calibration.py::test_calibration_artifacts_exist PASSED [ 33%]
tests/test_spectra_task_1_2c_calibration.py::test_p0008_cohort_enforcement_and_exclusions PASSED [ 50%]
tests/test_spectra_task_1_2c_calibration.py::test_strata_membership_counts PASSED [ 66%]
tests/test_spectra_task_1_2c_calibration.py::test_threshold_artifact_schema_and_quantiles PASSED [ 83%]
tests/test_spectra_task_1_2c_calibration.py::test_blind_evaluation_firewall PASSED [100%]
============================== 6 passed in 2.14s ==============================
```

Additionally, the full repository SPECTRA test suite across Tasks 1.2B, 1.2B-R, and 1.2B-S passed 100% (23/23 tests passing).

---

## 12. Artifact Paths and SHA-256 Checksums

### Table 12.1: Calibration Artifact Ledger

| Deliverable Asset | File Path | Record Count / Dimensions | SHA-256 Hash |
|:---|:---|:---:|:---:|
| **Provisional Thresholds Manifest** | `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | 3 strata | `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` |
| **Calibration Scores Table** | `data/processed/spectra/spectra_p0008_calibration_scores_v1.csv` | 3,206 rows $\times$ 11 cols | `7ac34d415f8132f7f164ab20c1b25fe03461bc709eb674031e838b2208e8c1a3` |
| **Calibration Driver Script** | `scripts/calibration/calibrate_spectra_v2_thresholds.py` | 350 lines | `4b57abf08d791fd60f7c4d51d6dd3ba4ace71d5f059d807e558c66fccc585ab6` |
| **Automated Test Suite** | `tests/test_spectra_task_1_2c_calibration.py` | 6 unit tests | (verified executable) |
| **Calibration Report** | `reports/SPECTRA_TASK_1_2C_THRESHOLD_CALIBRATION_REPORT.md` | — | (current document) |
| **Governance Manifest** | `reports/manifests/spectra_task_1_2c_calibration_manifest.json` | — | `5a47e09159951664e7a8daef2ea407c0f13388a1be52e7dfba6b0df2b8812c4f` |

---

## 13. Scientific Interpretation & Governance Rules

In strict compliance with Section 8 of the task prompt:

### Permitted Scientific Characterizations:
- The derived values are **Empirical Provisional-Null Quantiles** calculated from the **P0008 provisional calibration cohort**.
- Sources are **astrometrically selected provisional control candidates** verified clean in Gaia DR3 / 2MASS.
- Thresholds represent **nominal 5% and 1% empirical reference thresholds**.
- This constitutes **single-pointing calibration evidence**; **calibration transfer remains unverified** across different sky pointings.

### Prohibited Claims:
- These thresholds DO NOT represent a *verified 5% false-positive rate* or *certified 1% false-positive rate*.
- The model is NOT a *sky-wide calibrated detector* or a *production-ready anomaly detection system*.
- The cohort is NOT a *spectroscopically confirmed normal population*. Astrometric point-source cleanliness does not guarantee the absence of real spectral emission lines or rare astrophysical continuum shapes.

---

## 14. Component Governance Findings & Final Verdict

| Governance Dimension | Verdict | Detailed Audit Finding |
|:---|:---:|:---|
| **Data Governance** | **PASS** | Strict P0008 cohort enforcement ($N=3,206$); zero blind evaluation data touched. |
| **Model Immutability** | **PASS** | Checkpoint hash verified byte-for-byte immutable (`6ecada80ba...`). |
| **Score-Path Integrity** | **PASS** | Audited masked $\chi^2$ scoring with $1.93\%$ error floor applied deterministically. |
| **Threshold Calculation** | **PASS** | Statistically consistent Type 7 quantiles derived separately for all three strata. |
| **Statistical Uncertainty** | **PASS** | $B=2,000$ source-level bootstrap confidence intervals computed; tail limits documented. |
| **Spatial Dependence** | **PASS** | Moran's $I \approx -0.002$; block bootstrap sensitivity ($0.5^\circ, 1.0^\circ, 2.0^\circ$) audited. |
| **Reproducibility** | **PASS** | Fully deterministic under `seed = 42`; all automated tests passing. |

### Overall Task Verdict:
$$\mathbf{PASS\ —\ PROVISIONAL-NULL\ THRESHOLDS\ CALIBRATED\ \&\ FROZEN}$$
$$\text{(BLIND EVALUATION CERTIFICATION PENDING TASK 1.2D)}$$

---

## 15. Recommended Next Task

Proceed to **Phase 3, Task 1.2D: Blind Scientific Evaluation Campaign on Independent QR3 Cohort**.

Using the frozen thresholds derived in Task 1.2C:
1. Evaluate the frozen SPECTRA V2 model against the untouched Blind Evaluation Cohort (Pointings `0002`, `0009`, `0010`, $N = 17,078$ observed sources, 122,853 measurements).
2. Measure empirical false-positive rate generalization across independent sky fields.
3. Evaluate anomaly recovery against synthetic injection benchmarks without modifying calibration cutoffs.

