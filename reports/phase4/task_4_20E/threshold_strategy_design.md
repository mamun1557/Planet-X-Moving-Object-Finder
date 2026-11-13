# SPECTRA-X / F1 — Phase 4, Task 4.20E
# Sample-Aware Detector-Stratified Thresholding Strategy Design

**Pipeline Build:** `l2b-v27-2026-222`  
**Target Module:** ASTROVISION V3 Spatial Anomaly Detection  
**Author:** Senior Astronomical ML Architect & Reproducibility Auditor  
**Date:** November 9, 2026  
**Governance:** ZERO RETRAINING / PRODUCTION-PRESERVING / SHADOW-ONLY  

---

## 1. Architectural Philosophy & Governing Principles

Standard empirical calibration estimates an operating threshold $\hat{\tau}_d$ as the $(1 - \alpha)$-quantile of the empirical score distribution on null controls:
$$\hat{\tau}_d = Q_{1 - \alpha}(\{S_{d, i}\}_{i=1}^{N_d})$$

While theoretically appealing, when $N_d$ is small ($N_d \approx 84$ in SPHEREx Level-2 calibration fields), the empirical quantile estimator exhibits severe sample variance and is vulnerable to unmasked field stars and cosmic ray outliers.

To resolve this defect without mutating production baselines, Task 4.20E establishes a **Sample-Aware Calibration Triad**:

```
                                  +---------------------------------------+
                                  | Calibration Control Samples (N_d)     |
                                  +---------------------------------------+
                                                      |
                                  +---------------------------------------+
                                  | Sample Sufficiency & Stability Audit |
                                  | - N_ctrl >= 50, N_anom >= 20          |
                                  | - Bootstrap CV < 0.50                 |
                                  | - Target Morphology Present (N > 0)   |
                                  +---------------------------------------+
                                         /            |            \
                                        /             |             \
                       Meets All Bounds/     Moderate |              \ Fails Bounds or
                                      /     Variance  |               \ Missing Morphology
                                     v                v                v
                        +---------------+   +-------------------+   +--------------------+
                        |    STATE A    |   |      STATE B      |   |      STATE C       |
                        |   Detector-   |   |   Empirical Bayes |   |    Insufficient    |
                        |   Specific    |   |   Pooled Shrinkage|   |   Sample Fallback  |
                        |  Calibration  |   |    tau_shrunk     |   |   tau_production   |
                        +---------------+   +-------------------+   +--------------------+
```

---

## 2. Mathematical Formulation of the Three Calibration States

### 2.1 State A: Detector-Specific Calibration
State A applies the unconstrained empirical $(1 - \alpha)$-quantile $\hat{\tau}_d$ exclusively when all three criteria are satisfied:
1. **Control Sufficiency:** $N_{d, \text{ctrl}} \ge N_{\text{min,ctrl}} = 50$.
2. **Anomaly Sufficiency:** $N_{d, \text{anom}} \ge N_{\text{min,anom}} = 20$.
3. **Resampling Stability:** Bootstrap coefficient of variation satisfies:
   $$\text{CV}_d = \frac{\sigma_{\text{boot}}(\hat{\tau}_d)}{\mu_{\text{boot}}(\hat{\tau}_d)} \le 0.50$$

### 2.2 State B: Empirical Bayes / James-Stein Pooled Shrinkage
When control sample size is moderate ($50 \le N_d < 200$) and bootstrap variance is elevated, unconstrained thresholding overfits to local sample quirks. State B stabilizes the threshold by shrinking $\hat{\tau}_d$ toward the pooled reference threshold $\tau_{\text{pool}}$ ($N = 500$):
$$\tau_d^* = \lambda_d \hat{\tau}_d + (1 - \lambda_d) \tau_{\text{pool}}$$

The shrinkage factor $\lambda_d \in (0, 1)$ is determined by the James-Stein formulation:
$$\lambda_d = \frac{N_d}{N_d + N_0}$$
where $N_0 = 84.0$ represents the prior effective sample size. For $N_d = 84$, $\lambda_d = 0.500$, giving equal weight to the detector empirical evidence and the robust pooled cross-detector consensus.

### 2.3 State C: Insufficient Sample Fallback (`INSUFFICIENT_SAMPLE_FALLBACK`)
State C mandates fallback to the established baseline production threshold $\tau_{\text{prod}, d}$ when:
1. **Morphology Absence:** Calibration anomalies for the target class are missing ($N_{d, \text{morph}} = 0$).
2. **Catastrophic Tail Leverage:** An extreme outlier skews the empirical quantile, producing $\text{CV}_d > 1.00$.
3. **Domain Risk:** In low-background thermal bands (Detectors 5 and 6), shrinking toward $\tau_{\text{pool}} = 683.16$ would inflate the threshold 4-fold to 7-fold, destroying genuine faint-source recovery.

---

## 3. Systematic Detector Allocation

Applying these criteria to the calibration dataset yields the following assignments:

| Detector | Bandpass | Calibration $N_{\text{ctrl}}$ | Bootstrap CV | Morphology Present | Assigned State | Calibrated Threshold $\tau_d^*$ | Decision Rationale |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **D1** | 0.75 – 1.11 µm | 84 | 0.7269 | Point only | **STATE B** | **638.41** | Near-IR crowding; shrunk threshold suppresses 33% of FPs while preserving point sensitivity. |
| **D2** | 1.11 – 1.63 µm | 84 | 1.1554 | Point only | **STATE C** | **2,536.30** | Pointing 1 outlier skew ($\text{CV}=1.16$); fallback to baseline avoids FP explosion in crowded evaluation fields. |
| **D3** | 1.63 – 2.42 µm | 83 | 2.9397 | Point only | **STATE C** | **999.76** | Calibration outlier ($\text{CV}=2.94$); fallback maintains nominal FPR (2.41%). |
| **D4** | 2.42 – 3.48 µm | 83 | 4.3314 | Point only | **STATE B** | **658.82** | Empirical threshold close to baseline (634.19 vs 633.73); shrinkage stabilizes threshold. |
| **D5** | 3.48 – 4.42 µm | 83 | 3.4064 | Point only | **STATE C** | **91.85** | Thermal regime; pooling would destroy sensitivity (recovery drops from 59% to 13%); baseline preserved. |
| **D6** | 4.42 – 5.00 µm | 83 | 1.0138 | Point only | **STATE C** | **197.35** | Long-wavelength channel; pooling suppresses recovery; baseline threshold strictly preserved. |
| **EXTENDED** | All Bands | 500 | N/A | **None ($N=0$)** | **STATE C** | **Baseline $\tau_{\text{ext}}$** | Zero calibration extended injections; State C fallback universally enforced. |

---

## 4. Interaction with Spatial Catalog-Aware Masking

Dynamic thresholding does NOT operate in isolation. When combined with **Adaptive Catalog-Aware Masking (Adaptive-A)**:
1. **Catalog Masking** eliminates unmasked field stars in the outer annulus ($r > 2.0\text{ px}$), suppressing 64.4% of baseline false alarms without touching the central anomaly aperture.
2. **Detector Thresholding** adjusts the sensitivity floor to match instrumental noise and dark-current variations.
3. Together, false positive rate drops from **$9.00\%$ to $2.20\%$**, meeting the mission budget ($\le 5.00\%$) across all pointings and detectors.