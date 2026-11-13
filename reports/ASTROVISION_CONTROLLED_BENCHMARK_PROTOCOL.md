# ASTROVISION Controlled Benchmark Campaign Protocol
**Phase 3, Task 1.1F — Experimental Protocol & Statistical Methodology Specification**  
**NASA Space Apps Challenge 2026 — SPECTRA-X / F1**

---

## 1. Executive Protocol Summary & Governance Notice

This protocol defines the strict experimental design, exposure-level group partitioning, threshold-calibration procedure, and statistical evaluation methodology for the forthcoming **ASTROVISION Spatial Injection & Recovery Benchmark Campaign**.

### Mandatory Scientific Governance
* **Execution Status in Task 1.1F:** **STRICTLY PROHIBITED.** No model inference, campaign execution, or performance metric generation is conducted during this protocol definition task.
* **Model Checkpoint Status:** `checkpoints/astrovision_spatial_v2.pt` remains frozen and uncertified.
* **Historical Threshold:** The historical threshold $\tau = 169.10$ is treated strictly as an unvalidated historical reference. It must not be assumed valid without independent re-calibration on disjoint calibration controls.
* **Primary Objective:** Establish a reproducible, physically defensible, and statistically cluster-robust procedure for certifying the spatial anomaly detection and recovery sensitivity of ASTROVISION on genuine NASA SPHEREx Level-2 science imagery.

---

## 2. Experimental Sample Design & Exposure-Level Grouping

### 2.1 The Exposure-Level Independence Architecture
To permanently eliminate the risk of correlation leakage between calibration and evaluation data (Audit F remediation), all astronomical cutouts are partitioned using a strict grouping hierarchy:
1. **Pointing Exposure / Observation Identity (`obs_id`):**  
   Every genuine SPHEREx Level-2 science observation represents a unique spacecraft pointing with specific attitude, integration time, and background illumination. An entire exposure group (all detector cutouts from that `obs_id`) is assigned atomically to either `CALIBRATION` or `EVALUATION`. Under no circumstances may cutouts from the same `obs_id` cross partition boundaries:
   $$\mathcal{G}_{\text{CAL}} \cap \mathcal{G}_{\text{EVAL}} = \emptyset$$
2. **FITS File Identity (`filename`):**  
   All cutouts extracted from a single detector array FITS file belong strictly to the partition of its parent `obs_id`.
3. **Spatial Separation & Overlap Prevention:**  
   Cutouts extracted from the same detector array must maintain a minimum spatial center-to-center separation of:
   $$\Delta r = \sqrt{(x_1 - x_2)^2 + (y_1 - y_2)^2} \ge 128.0\,\text{pixels}$$
   Any candidate cutout violating this boundary is detected during harvesting and rejected prior to partition assignment.
4. **Source Identity Co-Grouping:**  
   In the event that repeated pointing observations target the same physical astronomical catalogue object, all observations containing that `source_id` are linked via disjoint set union into a single connected-component cluster.

### 2.2 Detector-Stratified Representation
SPHEREx employs 6 distinct detector arrays with varying spectral bands, optical cutoffs, and detector physics:
* **D1–D3 (NIR):** InGaAs arrays spanning $0.75\,\mu\text{m} - 2.42\,\mu\text{m}$ (nominal AGM gains: $0.108 - 0.117\,\text{MJy}\cdot\text{s}/(e^-\cdot\text{sr})$).
* **D4–D6 (MWIR):** MCT arrays spanning $2.42\,\mu\text{m} - 5.00\,\mu\text{m}$ (nominal AGM gains: $0.089 - 0.458\,\text{MJy}\cdot\text{s}/(e^-\cdot\text{sr})$).

The sampling protocol harvests balanced quotas (target: $N \ge 50$ cutouts per detector array, minimum 300 total cutouts across Pointing 0003) to ensure that the benchmark evaluates all 6 optical and detector regimes without NIR bias.

### 2.3 Experimental Partitions & Trial Categories

The campaign defines four mutually exclusive trial categories:

| Partition Identifier | Trial Purpose | Injection Type | SNR / Flux Grid | Counterfactual Control Member |
| :--- | :--- | :---: | :---: | :---: |
| **`CALIBRATION_CONTROL`** | Detection threshold selection & baseline false-alarm calibration | None (Zero Injection) | $S = 0.0\,\text{MJy/sr}$ | Identical un-injected background cutout |
| **`EVALUATION_CONTROL`** | Unbiased out-of-sample false-positive rate (FPR) estimation | None (Zero Injection) | $S = 0.0\,\text{MJy/sr}$ | Identical un-injected background cutout |
| **`POINT_SOURCE_INJECTION`** | Detection completeness ($C_{50}, C_{90}$), recovery, and astrometric error for unresolved sources | In-File HDU 5 ePSF profile | Nominal SNR $\in \{3, 5, 7, 10, 15, 20, 30, 50\}$ | Matched un-injected background cutout |
| **`EXTENDED_SOURCE_INJECTION`**| Extended morphology recovery & completeness across spatial scales | 2D Gaussian profile | $\text{FWHM} \in \{12'', 18'', 24'', 36''\}$; $\text{SNR} \in \{3, 5, 7, 10, 15, 20, 30, 50\}$ | Matched un-injected background cutout |

---

## 3. Physical Injection & Paired Residual Measurement

### 3.1 Counterfactual Paired Realization
Every trial is encapsulated as a `MatchedCutoutPairV2` sharing:
* Identical background image realization $I_{\text{control}}(x, y)$.
* Identical background noise variance $\text{Var}_{\text{control}}(x, y)$.
* Identical fatal-defect pixel mask $M(x, y)$ ($\text{mask} = ((\text{FLAGS} \ \& \ 615) == 0)$).
* Identical local detector gain $\text{AGM}(x, y)$ queried from HDU 4.

For injected trials, the synthetic profile $S_{\text{synth}}(x, y)$ is added with physical Poisson shot noise:
$$N_e(x, y) = \text{Poisson}\left(S_{\text{synth}}(x, y) \cdot \frac{t_{\text{exp}}}{\text{AGM}(x, y)}\right)$$
$$I_{\text{injected}}(x, y) = I_{\text{control}}(x, y) + N_e(x, y) \cdot \frac{\text{AGM}(x, y)}{t_{\text{exp}}}$$
$$\text{Var}_{\text{injected}}(x, y) = \text{Var}_{\text{control}}(x, y) + S_{\text{synth}}(x, y) \cdot \frac{\text{AGM}(x, y)}{t_{\text{exp}}}$$

### 3.2 Paired Residual Differencing Photometry
Both members undergo forward inference through the frozen model:
$$\hat{I}_{\text{injected}} = \mathcal{M}(I_{\text{injected}}), \quad \hat{I}_{\text{control}} = \mathcal{M}(I_{\text{control}})$$
$$R_{\text{injected}}(x, y) = \max\left(0, I_{\text{injected}}(x, y) - \hat{I}_{\text{injected}}(x, y)\right)$$
$$R_{\text{control}}(x, y) = \max\left(0, I_{\text{control}}(x, y) - \hat{I}_{\text{control}}(x, y)\right)$$

The model-response differential flux within circular aperture $\mathcal{A}$ ($r \le 3.5\,\text{pixels}$) is computed in `float64`:
$$F_{\text{recovered, model}} = \sum_{(x,y) \in \mathcal{A}} \left[R_{\text{injected}}(x, y) - R_{\text{control}}(x, y)\right] \cdot M(x, y)$$
$$S_{\text{recovered}} [\text{Jy}] = F_{\text{recovered, model}} [\text{MJy/sr}\cdot\text{pix}] \times 10^6 \times \Omega_{\text{pix}}$$

Signed differential contributions are strictly preserved across the aperture without outer positive clipping.

---

## 4. Threshold Calibration Protocol

### 4.1 Calibration-Only Sample Isolation
1. **Zero Evaluation Contamination:** The threshold selection procedure operates strictly and exclusively on the `CALIBRATION_CONTROL` partition. Evaluation controls, injected trials, and evaluation residuals are completely inaccessible during calibration.
2. **Objective Selection Rule:** Let $\{\chi^2_{\text{cal}, i}\}$ be the distribution of maximum target-aperture anomaly statistics across the $N_{\text{cal}}$ calibration control samples:
   $$\chi^2_i = \max_{r \le 2.5\,\text{px}} \chi^2(x, y)$$
3. **Target False-Alarm Criterion:** The operational threshold $\tau^*$ is chosen to enforce an empirical false-positive rate target $\alpha_{\text{target}} \le 0.05$ (5.0%) on the calibration background:
   $$\tau^* = \text{Quantile}\left(\{\chi^2_{\text{cal}}\}, 1 - \alpha_{\text{target}}\right)$$
4. **Historical Threshold Comparison:** The historical value $\tau = 169.10$ will be evaluated alongside $\tau^*$ for reporting continuity, but only $\tau^*$ calibrated under this protocol governs out-of-sample evaluation decisions.
5. **Parameter Freezing:** The calibrated threshold $\tau^*$, calibration sample IDs, detector distribution, and 95% binomial confidence bounds are frozen into a tamper-evident configuration file (`calibration_threshold_frozen.json`) prior to initiating evaluation.

---

## 5. Scientific Measurements & Performance Metrics

### 5.1 Binary Detection Criterion
A synthetic injection trial is classified as **Detected** at threshold $\tau^*$ if and only if both conditions are met:
1. **Anomaly Significance:** $\chi^2_{\text{target, peak}} \ge \tau^*$ within matching radius $r \le 2.5\,\text{pixels}$.
2. **Astrometric Localization:** Centroid position error $\Delta r \le 2.5\,\text{native pixels}$ ($15.38\,\text{arcsec}$).

### 5.2 Completeness Modeling ($C_{50}, C_{90}$)
For each detector and morphology, empirical detection fraction as a function of injection signal-to-noise ratio $\text{SNR}$ is modeled via a two-parameter cumulative normal / logistic sigmoid:
$$C(\text{SNR}) = \frac{1}{1 + \exp\left(-k \cdot (\text{SNR} - \text{SNR}_{50})\right)}$$
* **$C_{50}$:** SNR corresponding to 50% detection completeness ($\text{SNR}_{50}$).
* **$C_{90}$:** SNR corresponding to 90% detection completeness ($\text{SNR}_{50} + \frac{\ln 9}{k}$).
* Sigmoid parameters are fitted via maximum likelihood estimation (MLE) with cluster-robust standard errors.

### 5.3 Classification Metrics
Evaluated on the out-of-sample evaluation partition:
* **False Positive Rate (FPR):** $\text{FPR} = \frac{\text{FP}}{\text{FP} + \text{TN}}$ evaluated strictly on `EVALUATION_CONTROL`.
* **Precision & Recall:** $\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}$, $\text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}$.
* **Prevalence Standardization:** Because benchmark prevalence ($\approx 67\% - 75\%$) diverges from the astrophysical prevalence of anomalous transients ($\ll 1\%$), precision must be reported alongside prevalence-standardized precision:
  $$\text{Precision}_{\text{std}}(\pi) = \frac{\text{Recall} \cdot \pi}{\text{Recall} \cdot \pi + \text{FPR} \cdot (1 - \pi)}$$
* **Discriminative Metrics:** AUROC and AUPRC computed over continuous threshold ranges using non-interpolated trapezoidal integration.

### 5.4 Astrometric Accuracy
Subpixel centroid refinement using 2D parabolic interpolation on the model's $\chi^2$ anomaly map. The distribution of radial positional errors:
$$\Delta r = \sqrt{(\hat{x} - x_{\text{true}})^2 + (\hat{y} - y_{\text{true}})^2} \quad [\text{pixels and arcseconds}]$$
is summarized by its median, 68th percentile (equivalent $1\sigma$), and 95th percentile.

### 5.5 Photometric Linearity & Transfer Calibration
The relationship between model differential residual flux $F_{\text{recovered, model}}$ and true injected flux $S_{\text{true}}$ will be characterized via linear regression across SNR bins:
$$F_{\text{recovered, model}} = \beta \cdot S_{\text{true}} + \beta_0$$
* $\beta$: Model flux transfer efficiency (fraction of source flux surviving autoencoder reconstruction).
* Linearity range and deviation from linearity at low SNR will be reported.

---

## 6. Statistical Methodology & Uncertainty Estimation

### 6.1 Cluster-Aware Bootstrap for Exposure Grouping
Standard i.i.d. bootstrap resampling underestimates uncertainty when cutouts from the same pointing exposure share correlated background structures.
* **Resampling Unit:** Complete pointing exposure groups (`obs_id`), not individual cutouts.
* **Iterations:** $B = 2,000$ cluster-bootstrap replications.
* **Confidence Intervals:** 95% percentile-based confidence intervals reported for AUROC, AUPRC, $C_{50}$, $C_{90}$, and precision.

### 6.2 Binomial Confidence Bounds
For empirical FPR and discrete detection fractions, exact Wilson score 95% confidence intervals are reported:
$$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}, \quad z = 1.96$$

### 6.3 Predefined Sample Exclusion & Boundary Guards
* Injections centered within 6 pixels of the cutout boundary ($x < 6$ or $x > W-7$) are rejected.
* Cutouts with valid pixel fraction $< 88\%$ are rejected.
* Missing-data accounting: All rejected candidates, non-convergences, and masked aperture pixels are recorded in trial metadata.

---

## 7. Protocol Summary Table

| Scientific Aspect | Protocol Specification | Quality Guard / Remediation Reference |
| :--- | :--- | :--- |
| **Exposure Grouping** | Disjoint atomic assignment of `obs_id` clusters | Resolves Audit F; eliminates background leakage |
| **Spatial Separation** | Pairwise separation $\Delta r \ge 128\,\text{pixels}$ | Prevents overlapping cutout footprint correlation |
| **Detector Coverage** | Stratified across D1–D6 | Prevents NIR D1–D3 bias on MWIR D4–D6 arrays |
| **Threshold Calibration** | Strict calibration-only controls | Prevents in-sample threshold overfitting |
| **Photometry Metric** | Paired Residual Differencing in `float64` | Resolves Audit D; eliminates baseline reconstruction artifact |
| **Uncertainty Method** | Group-aware cluster bootstrap ($B=2,000$) | Corrects for intra-exposure background correlation |
| **Provenance** | Checkpoint SHA-256 embedded in all records | Guarantees frozen checkpoint immutability |
| **Execution Governance**| Safety lock enforced; dry-run only in 1.1F | Campaign execution strictly gated to subsequent tasks |

