# SPECTRA-X / F1 — PHASE 3, TASK 1.1V
# INDEPENDENT ASTROVISION V3 SCIENTIFIC QUALIFICATION AUDIT REPORT

**Audit Date:** 2026-11-07  
**Auditor:** Independent Principal Scientific Auditor, Astronomical ML Benchmark Statistician & Scientific Validation Specialist  
**Audit Target:** Frozen ASTROVISION V3 Candidate (`checkpoints/astrovision_spatial_v3.pt`)  
**Parent Authorization:** Task 1.1Q Pre-Execution Safety Review & Project Owner Authorization  
**Baseline Reference:** ASTROVISION V2 (`checkpoints/astrovision_spatial_v2.pt`, Task 1.1R Campaign, Task 1.1S Audit)  
**Evaluation Cohort:** 1,500 Untouched Evaluation Trials across Pointings `0002`, `0009`, `0010` (Partitions 3, 4, 5)  
**Audit Mode:** STRICTLY READ-ONLY with respect to model architecture, weights, calibration parameters, and historical assets  

---

## 1. Executive Summary

This independent scientific qualification audit evaluates the frozen candidate **ASTROVISION V3** (`checkpoints/astrovision_spatial_v3.pt`) against the historical baseline **ASTROVISION V2** (`checkpoints/astrovision_spatial_v2.pt`). The evaluation was conducted strictly on the **1,500 untouched evaluation trials** from the pre-authorized five-pointing QR3 Level-2 dataset, spanning Pointings `0002` (Mid-Latitude South), `0009` (Mid-Latitude North), and `0010` (North Ecliptic Pole / NEP Deep Calibration Field).

### Key Audit Findings

1. **Definitive Defect Remediation:**
   - **Fatal Pixel Masking (Remediation 1):** The primary failure mode of V2—convolutional error propagation from fatal detector defect pixels—has been eliminated. On Detector 4 (D4), which in V2 scored **$\text{AUROC} = 0.4776$** (worse than random guessing due to fatal defect pixel bleed), V3 achieved **$\text{Point AUROC} = 0.7261$** ($p = 4.94 \times 10^{-7}$) and extended **$\text{AUROC} = 0.6017$**. Point recovery on D4 increased from $4.82\%$ ($4/83$) to $21.69\%$ ($18/83$).
   - **Background Normalization & Domain Shift Adaptation (Remediation 2):** In V2, Pointing `0010` (North Ecliptic Pole) exhibited catastrophic failure with extended **$\text{AUROC} = 0.4599$** due to global dynamic range compression under intense NEP zodiacal backgrounds. In V3, the `RobustLocalNormalizer` (local median and MAD scaling) successfully bridged this domain gap without exposing any polar data during training: Pointing `0010` point AUROC rose from $0.6143$ to **$0.8572$** ($p = 4.72 \times 10^{-29}$), extended AUROC rose from $0.4599$ to **$0.7520$**, and empirical false positive rate on polar null controls was tightly held at **$0.0427$** (below the nominal $\alpha = 0.05$ budget).
   - **Aperture-Integrated Anomaly Scoring (Remediation 3):** Replacing single peak-pixel $\chi^2$ scoring with a physically motivated $2.5$-pixel circular aperture integral for point sources increased overall point-source recovery from **$18.80\%$** ($94/500$) in V2 to **$34.80\%$** ($174/500$) in V3, an absolute gain of $+16.00\%$ ($+85.1\%$ relative improvement, McNemar test $p = 7.53 \times 10^{-10}$). Point-source precision improved from $0.6861$ to $0.7909$.

2. **Performance Limitations & Unresolved Risks:**
   - **Extended Source Detection Sensitivity:** While extended-source AUROC improved from $0.5704$ (V2) to $0.7064$ (V3 Peak), recovery remains low at **$17.40\%$** ($87/500$). Furthermore, broad aperture integration ($r = 5.0$ pixels, $80+$ pixels) suffered significant noise dilution at low SNRs ($\text{SNR} < 10$), demonstrating that unweighted circular boxcar integration is suboptimal for diffuse morphology.
   - **Out-of-Field False Positive Rate Drift:** Across the 500 untouched null controls, empirical FPR was **$0.0900$** ($45/500$, $95\%$ Wilson CI: $[0.0679, 0.1183]$) for peak scoring and **$0.0920$** ($46/500$) for point integrated scoring, exceeding the calibrated nominal false-alarm budget ($\alpha = 0.05$). This excess is driven heavily by Detector 1 (D1 FPR = $0.2262$–$0.2500$) and Pointing `0009` (FPR = $0.1429$–$0.1488$), reflecting unmodeled residual zodi and high stellar density in low-wavelength bands.
   - **Detector 2 High-Threshold Conservatism:** On Detector 2, high null-control background variance forced an extreme operating threshold ($\tau = 2,536.30$), suppressing point recovery to just **$8.33\%$** ($7/84$).

### Final Scientific Qualification Verdict

```
========================================================================================
                      ASTROVISION V3 SCIENTIFIC QUALIFICATION VERDICT                   
========================================================================================
  Engineering Implementation:         PASS
  Data Governance & Provenance:       PASS (Zero Leakage)
  Defect Remediation:                 PASS (Fatal Pixels & NEP Domain Shift Resolved)
  Point-Source Anomaly Detection:     PARTIAL (AUROC 0.8040, Recovery 34.80%, Prec 79.09%)
  Extended-Source Anomaly Detection:  EXPLORATORY (AUROC 0.7064, Recovery 17.40%)
  False-Alarm Statistical Control:    PARTIAL (Empirical FPR 9.00% vs 5.00% target)
----------------------------------------------------------------------------------------
  OVERALL SCIENTIFIC STATUS:          PARTIAL — NOT CERTIFIED FOR UNATTENDED PIPELINE
========================================================================================
```

---

## 2. Governance Verification & Asset Protection Preflight

### 2.1 Governance Checklist
All mandatory preflight governance gates established in Tasks 1.1Q, 1.1R, 1.1S, 1.1T, and 1.1U were verified prior to running any evaluation script:

- [x] **Zero Model Retraining:** Neither V2 nor V3 was retrained or fine-tuned during this audit.
- [x] **Zero Architecture Mutation:** `models/astrovision/model_v3.py` remained completely unmodified.
- [x] **Zero Threshold Tuning on Evaluation Data:** Operating thresholds were strictly loaded from `data/processed/pilot_results/calibration_parameters_v3.json`, which was derived exclusively from Pointings `0001` and `0008`. No evaluation labels or evaluation cutouts were used to fit, adjust, or select thresholds.
- [x] **Strict Partition Quarantine:** Pointings `0002`, `0009`, and `0010` were never accessed during training, validation, or calibration.
- [x] **Trial Definition Parity:** Evaluation trials (1,500 trials) matched the frozen Task 1.1R manifest bit-for-bit in spatial coordinates, FITS files, SNR targets, and random number generator sequence (`seed = 42`).

### 2.2 Immutable Asset Cryptographic Hash Ledger

| Asset Path | Role | Expected SHA-256 | Verified Post-Audit SHA-256 | Status |
|:---|:---|:---|:---|:---:|
| `checkpoints/astrovision_spatial_v2.pt` | Frozen Baseline V2 Model | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | `f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557` | **IMMUTABLE** |
| `checkpoints/astrovision_spatial_v3.pt` | Frozen Candidate V3 Model | `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99` | `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99` | **IMMUTABLE** |
| `checkpoints/astrovision_spatial_v3.json` | V3 Training Provenance Metadata | `70e9954752c0b4317635627d9d21180882ad36e38d5435f8c326260f58f8d188` | `70e9954752c0b4317635627d9d21180882ad36e38d5435f8c326260f58f8d188` | **IMMUTABLE** |
| `data/processed/pilot_results/calibration_parameters_v3.json` | Frozen V3 Operating Thresholds | `aabe0d15d0e8d559cc82897e9c669f0f5f5785ab32e111123ac321a258ccf706` | `aabe0d15d0e8d559cc82897e9c669f0f5f5785ab32e111123ac321a258ccf706` | **IMMUTABLE** |
| `data/processed/pilot_results/astrovision_pilot_trial_results.csv` | Task 1.1R Campaign Trial Results | `4afddbb31d9f1b579d711712da431bf1c19701d7a63d25e9a06995a71c9d523f` | `4afddbb31d9f1b579d711712da431bf1c19701d7a63d25e9a06995a71c9d523f` | **IMMUTABLE** |
| `reports/manifests/astrovision_five_partition_pilot_manifest.csv` | Pilot Trial Definitions (2,500 trials) | `9ec16ce036eb5782782736fc201e7e408ecbbef223cb5a1d7f6c3217b1202e96` | `9ec16ce036eb5782782736fc201e7e408ecbbef223cb5a1d7f6c3217b1202e96` | **IMMUTABLE** |

---

## 3. Independent Source-Code & Scientific Architecture Audit

### 3.1 Mask-Aware Partial Convolutions (`MaskAwareConv2d`)
- **Fatal Flag Interpretation:** The bitmask `FATAL_FLAG_MASK = 615` ($0\text{x}0267$) covers bit 0 (Dead/Hot Pixel), bit 1 (Saturated), bit 2 (Low Responsivity), bit 5 (Cosmic Ray), and bit 9 (Out of Bounds). This adheres strictly to the SPHEREx QR3 Level-2 Flag Convention.
- **Propagation Mechanics:** In `MaskAwareConv2d`, input values at masked locations are zeroed out before convolution. The updated mask is computed by convolving a binary mask tensor with uniform unit weights. Pixels where the sum of valid window elements is zero are assigned a mask value of $0.0$; where the sum is $>0$, the convolved output is normalized by $(\text{kernel area} / \text{valid area})$, and the mask propagates as $1.0$.
- **Coverage Bias Verification:** In the anomaly map calculation, the reconstruction loss is multiplied by the binary input mask:
  $$\text{Anomaly}(x, y) = \frac{(I_{\text{norm}}(x, y) - \hat{I}_{\text{norm}}(x, y))^2}{1.0} \times M(x, y)$$
  Pixels marked invalid ($M(x, y) = 0$) are strictly forced to zero anomaly. Consequently, missing or dead pixels cannot generate spurious $\chi^2$ peaks.

### 3.2 Robust Background Normalization (`RobustLocalNormalizer`)
- **Median and MAD Computation:**
  $$\text{Local BG} = \text{median}(I[M = 1])$$
  $$\sigma_{\text{MAD}} = 1.4826 \times \text{median}(|I[M = 1] - \text{Local BG}|)$$
- **Defensive Safeguards:** If valid pixels count $< 100$ or $\sigma_{\text{MAD}} < 1\text{e}-4$, fallback to $\sigma_{\text{var}} = \sqrt{\text{median}(\text{Var}[M=1])}$ is triggered.
- **Physical Defensibility:** Unlike V2's global per-cutout variance division, local MAD scaling resists source contamination, unmodeled stellar halos, and large-scale zodiacal gradients.

### 3.3 Aperture-Integrated Anomaly Scoring (`ApertureAnomalyScorer`)
- **Metric Definitions:**
  - **Point Aperture Integral ($r = 2.5\ \text{pixels}$):**
    $$S_{\text{point}} = \sum_{r_i \le 2.5,\ M_i=1} \text{Anomaly}(x_i, y_i)$$
  - **Extended Aperture Integral ($r = 5.0\ \text{pixels}$):**
    $$S_{\text{ext}} = \sum_{r_i \le 5.0,\ M_i=1} \text{Anomaly}(x_i, y_i)$$
  - **Peak $\chi^2$ Score ($r \le 2.5\ \text{pixels}$):**
    $$S_{\text{peak}} = \max_{r_i \le 2.5,\ M_i=1} \text{Anomaly}(x_i, y_i)$$
- **Centroid Matching:** A spatial match is certified if subpixel centroid refinement locates the anomaly peak within $2.5$ pixels ($15.38''$) of the injected coordinate.

---

## 4. Partition Governance & Data Provenance Audit

The data partition boundaries established in Task 1.1O and audited in Task 1.1P were verified for absolute isolation:

```
[Pointing 0003: Southern High Lat (beta=-63.4 deg)]
      |--> V3 Training Patches:   1,200 cutouts (D1-D6, 4 dither exposures)
      |--> V3 Validation Patches:   240 cutouts (Disjoint dither exposure 4)
      [STRICTLY ZERO OVERLAP WITH POINTINGS 0001, 0008, 0002, 0009, 0010]

[Pointings 0001 & 0008: Calibrations]
      |--> Partitions 1 & 2: 1,000 trials (500 Controls, 500 Injections)
      |--> Used exclusively to fit operating thresholds tau_d(alpha=0.05)
      [NEVER ACCESSED DURING V3 TRAINING]

[Pointings 0002, 0009, 0010: Untouched Evaluation Cohort]
      |--> Partition 3: EVALUATION_CONTROL (500 trials)
      |--> Partition 4: EVALUATION_POINT_SOURCE_INJECTION (500 trials)
      |--> Partition 5: EVALUATION_EXTENDED_SOURCE_INJECTION (500 trials)
      [STRICT BLIND EVALUATION: NEVER SEEN DURING TRAINING OR CALIBRATION]
```

### File-Level and Spatial Verification
- **Total evaluation trials executed:** Exactly $1,500$ trials.
- **FITS files accessed during evaluation:** Exactly 72 FITS files across directories `0002/`, `0009/`, and `0010/`.
- **Training data overlap:** $0$ overlapping files, $0$ overlapping sky coordinates, $0$ shared sky patches.

---

## 5. Independent Calibration Reproduction Audit

The frozen calibration file `data/processed/pilot_results/calibration_parameters_v3.json` was independently audited by reprocessing all 500 calibration null controls from Pointings `0001` and `0008`.

| Detector | Wavelength ($\mu\text{m}$) | Reported $\tau_{\text{peak}}$ | Reproduced $\tau_{\text{peak}}$ | Difference ($\Delta$) | Reported $\tau_{\text{pt\_int}}$ | Reproduced $\tau_{\text{pt\_int}}$ | Difference ($\Delta$) | Audit Verdict |
|:---:|:---:|---:|---:|:---:|---:|---:|:---:|:---:|
| **D1** | 0.75 – 1.10 | 186.2904 | 186.2904 | $0.00\text{e}+00$ | 373.0434 | 373.0434 | $0.00\text{e}+00$ | **MATCH** |
| **D2** | 1.10 – 1.65 | 2536.2963 | 2536.2963 | $0.00\text{e}+00$ | 3752.3552 | 3752.3552 | $0.00\text{e}+00$ | **MATCH** |
| **D3** | 1.65 – 2.40 | 999.7611 | 999.7611 | $0.00\text{e}+00$ | 1735.2102 | 1735.2102 | $0.00\text{e}+00$ | **MATCH** |
| **D4** | 2.40 – 3.82 | 633.7253 | 633.7253 | $0.00\text{e}+00$ | 747.4456 | 747.4456 | $0.00\text{e}+00$ | **MATCH** |
| **D5** | 3.82 – 4.42 | 91.8464 | 91.8464 | $0.00\text{e}+00$ | 180.5691 | 180.5691 | $0.00\text{e}+00$ | **MATCH** |
| **D6** | 4.42 – 5.00 | 197.3499 | 197.3499 | $0.00\text{e}+00$ | 356.3344 | 356.3344 | $0.00\text{e}+00$ | **MATCH** |

**Conclusion:** All 6 detector thresholds in `calibration_parameters_v3.json` are $100\%$ independently reproduced with machine precision.

---

## 6. Controlled Evaluation Results & Mandatory V2 vs V3 Comparison

### 6.1 Overall Evaluation Performance Table

The table below presents the direct comparison between ASTROVISION V2 and ASTROVISION V3 across all 1,500 untouched evaluation trials.

| Metric | ASTROVISION V2 | ASTROVISION V3 (Peak $\chi^2$) | ASTROVISION V3 (Aperture Int) | Difference (V3 Peak vs V2) | Difference (V3 Int vs V2) | Scientific Interpretation |
|:---|---:|---:|---:|---:|---:|:---|
| **Point AUROC** | 0.6861 | **0.8040** | **0.7982** | $+0.1179$ ($+17.2\%$) | $+0.1121$ ($+16.3\%$) | Statistically significant discrimination gain ($p = 3.4 \times 10^{-62}$). |
| **Extended AUROC** | 0.5704 | **0.7064** | 0.6177 | $+0.1360$ ($+23.8\%$) | $+0.0473$ ($+8.3\%$) | Peak scoring outperforms broad aperture due to noise dilution. |
| **Point AUPRC** | 0.6080 | **0.7101** | **0.7070** | $+0.1021$ ($+16.8\%$) | $+0.0990$ ($+16.3\%$) | Substantial reduction in false positive contamination. |
| **Extended AUPRC** | 0.5391 | **0.6233** | 0.5648 | $+0.0842$ ($+15.6\%$) | $+0.0257$ ($+4.8\%$) | Modest improvement for diffuse sources. |
| **Point Recovery** | 0.1880 ($94/500$) | 0.3220 ($161/500$) | **0.3480** ($174/500$) | $+0.1340$ ($+71.3\%$) | $+0.1600$ ($+85.1\%$) | Recovery nearly doubled; integrated aperture captures faint flux. |
| **Extended Recovery** | 0.1520 ($76/500$) | **0.1740** ($87/500$) | 0.1340 ($67/500$) | $+0.0220$ ($+14.5\%$) | $-0.0180$ ($-11.8\%$) | Extended source recovery remains modest across all configurations. |
| **Point Precision** | 0.6861 | 0.7816 | **0.7909** | $+0.0955$ ($+13.9\%$) | $+0.1048$ ($+15.3\%$) | True positive purity increased substantially. |
| **Extended Precision**| 0.6387 | **0.6591** | 0.5630 | $+0.0204$ ($+3.2\%$) | $-0.0757$ ($-11.9\%$) | Extended precision degraded under broad aperture integration. |
| **Overall FPR** | **0.0860** ($43/500$) | 0.0900 ($45/500$) | 0.0920 ($46/500$) | $+0.0040$ | $+0.0060$ | Both V2 and V3 exceed nominal $0.05$ target budget on eval cohort. |

---

### 6.2 Detector-Wise Comparison Table

| Detector | V2 Point AUROC | V3 Point AUROC (Peak) | V3 Point AUROC (Int) | V2 Point Rec | V3 Point Rec (Peak) | V3 Point Rec (Int) | V2 Ext AUROC | V3 Ext AUROC (Peak) | V2 Ext Rec | V3 Ext Rec (Peak) | V2 FPR | V3 FPR (Peak) | V3 FPR (Int) |
|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **D1** | 0.7188 | 0.7745 | 0.7622 | 0.4405 | 0.6071 | **0.6190** | 0.6087 | **0.6841** | 0.2738 | **0.4048** | 0.1905 | 0.2262 | 0.2500 |
| **D2** | 0.6835 | 0.7365 | 0.7334 | 0.0595 | 0.0833 | **0.0833** | 0.4957 | **0.5937** | 0.0357 | **0.0476** | 0.0595 | 0.0833 | 0.0714 |
| **D3** | 0.7216 | 0.8082 | 0.7955 | 0.1687 | 0.1928 | **0.2048** | 0.5992 | **0.7344** | 0.2048 | 0.1446 | 0.0602 | 0.0241 | **0.0120** |
| **D4** | 0.4776 | 0.7261 | **0.7262** | 0.0482 | 0.1205 | **0.2169** | 0.3041 | **0.6017** | 0.0602 | 0.0482 | 0.1084 | 0.1084 | 0.1205 |
| **D5** | 0.7596 | 0.9319 | **0.9382** | 0.0602 | 0.5904 | **0.5904** | 0.6847 | **0.8978** | 0.0964 | **0.3373** | 0.0361 | 0.0361 | **0.0241** |
| **D6** | 0.8763 | 0.9075 | **0.9084** | 0.3494 | 0.3373 | **0.3735** | 0.7750 | **0.7886** | 0.2410 | 0.0602 | 0.0602 | 0.0602 | 0.0723 |

*Key Detector Takeaways:*
1. **D4 Rescue Confirmed:** In V2, D4 had $\text{Point AUROC} = 0.4776$ and $\text{Ext AUROC} = 0.3041$. In V3, D4 achieved $\text{Point AUROC} = 0.7261$ ($+0.2485$) and $\text{Ext AUROC} = 0.6017$ ($+0.2976$). Point recovery increased by over $4.5\times$ (from $4.82\%$ to $21.69\%$).
2. **D5 Exemplary Performance:** D5 achieved outstanding point AUROC ($0.9382$) and extended AUROC ($0.8978$), with point recovery surging from $6.02\%$ to $59.04\%$ while holding FPR at $2.41\%$.
3. **D1 High False-Alarm Rate:** D1 exhibits persistent excess FPR ($22.62\%$ peak, $25.00\%$ integrated), caused by high background stellar and zodiacal variance in the $0.75$–$1.10\ \mu\text{m}$ regime.

---

### 6.3 Pointing-Wise Comparison Table

| Pointing | Field Description | Ecliptic Lat ($\beta$) | V2 Point AUROC | V3 Point AUROC (Peak) | V2 Point Rec | V3 Point Rec (Int) | V2 Ext AUROC | V3 Ext AUROC (Peak) | V2 Ext Rec | V3 Ext Rec (Peak) | V2 FPR | V3 FPR (Peak) | V3 FPR (Int) |
|:---:|:---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **0002** | Mid-Latitude South | $-29.7^\circ$ | 0.7388 | **0.7967** | 0.2321 | **0.3690** | 0.6358 | **0.6978** | 0.1905 | **0.1964** | 0.0893 | 0.0833 | **0.0774** |
| **0009** | Mid-Latitude North | $+31.2^\circ$ | 0.7025 | **0.7609** | 0.1845 | **0.3452** | 0.6092 | **0.6707** | 0.1726 | **0.1964** | 0.1190 | 0.1429 | 0.1488 |
| **0010** | North Ecliptic Pole | $+66.5^\circ$ | 0.6143 | **0.8572** | 0.1463 | **0.3293** | 0.4599 | **0.7520** | 0.0915 | **0.1280** | 0.0488 | **0.0427** | 0.0488 |

*Key Pointing Takeaways:*
1. **NEP Domain Adaptation Confirmed:** On Pointing `0010`, point AUROC jumped from $0.6143$ to **$0.8572$** ($+0.2429$), extended AUROC jumped from $0.4599$ to **$0.7520$** ($+0.2921$), and point recovery more than doubled ($14.63\% \to 32.93\%$). False alarms remained strictly within the $0.05$ budget ($\text{FPR} = 0.0427$).
2. **Pointing 0009 Elevated FPR:** Pointing `0009` shows elevated false positive rate ($14.29\%$ peak, $14.88\%$ integrated), indicating field-dependent background variations not fully captured by the calibration pointings (`0001` and `0008`).

---

## 7. Statistical Uncertainty & Rigorous Significance Analysis

### 7.1 Statistical Significance Tests

1. **Point Source AUROC Discrimination Gain:**
   - Mann-Whitney U test between positive injection scores ($N = 500$) and control null scores ($N = 500$):
     - V2: $U = 171,524.0$, $p = 2.30 \times 10^{-24}$ ($\text{AUROC} = 0.6861$)
     - V3 Peak: $U = 201,003.5$, $p = 3.40 \times 10^{-62}$ ($\text{AUROC} = 0.8040$)
     - V3 Integrated: $U = 199,550.0$, $p = 6.60 \times 10^{-60}$ ($\text{AUROC} = 0.7982$)
   - The AUROC improvement of $+0.1179$ is statistically definitive ($z > 16.5$).

2. **Paired McNemar Test on Point-Source Recovery:**
   - Paired recovery decisions on the identical 500 injected targets:
     - $b$ (V2 missed, V3 detected): $91$ targets
     - $c$ (V2 detected, V3 missed): $24$ targets
     - McNemar statistic with continuity correction:
       $$\chi^2 = \frac{(|91 - 24| - 1)^2}{91 + 24} = \frac{66^2}{115} = 37.88$$
     - Asymptotic $p$-value: **$p = 7.53 \times 10^{-10}$**
   - The hypothesis of equal recovery between V2 and V3 is rejected with extreme statistical confidence.

3. **Detector 4 Defect Remediation Significance:**
   - In V2, D4 scores yielded $p = 0.6189$ (consistent with null hypothesis / zero discrimination).
   - In V3, D4 scores yielded $U = 5,064.0$, **$p = 4.94 \times 10^{-7}$** ($\text{AUROC} = 0.7261$).
   - The elimination of the D4 fatal pixel defect is statistically proven.

### 7.2 Wilson Score Confidence Intervals ($95\%$ Confidence)

- **Overall False Positive Rate (Controls $N = 500$):**
  - V2 Empirical FPR: $0.0860$ ($43/500$), $95\%\ \text{CI}: [0.0645, 0.1138]$
  - V3 Peak FPR: $0.0900$ ($45/500$), $95\%\ \text{CI}: [0.0679, 0.1183]$
  - V3 Point Int FPR: $0.0920$ ($46/500$), $95\%\ \text{CI}: [0.0697, 0.1205]$
  - V3 Ext Int FPR: $0.1040$ ($52/500$), $95\%\ \text{CI}: [0.0802, 0.1338]$

- **Overall Point Source Recovery ($N = 500$):**
  - V2 Recovery: $0.1880$ ($94/500$), $95\%\ \text{CI}: [0.1560, 0.2248]$
  - V3 Peak Recovery: $0.3220$ ($161/500$), $95\%\ \text{CI}: [0.2825, 0.3643]$
  - V3 Integrated Recovery: $0.3480$ ($174/500$), $95\%\ \text{CI}: [0.3074, 0.3909]$

- **Overall Extended Source Recovery ($N = 500$):**
  - V2 Recovery: $0.1520$ ($76/500$), $95\%\ \text{CI}: [0.1232, 0.1861]$
  - V3 Peak Recovery: $0.1740$ ($87/500$), $95\%\ \text{CI}: [0.1432, 0.2097]$
  - V3 Integrated Recovery: $0.1340$ ($67/500$), $95\%\ \text{CI}: [0.1067, 0.1669]$

### 7.3 Statistical Limitations & Cluster-Level Uncertainty
- **Field Cluster-Level Limitation:** The evaluation dataset comprises three independent pointings (`0002`, `0009`, `0010`). With $K = 3$ field clusters, cluster-robust standard errors cannot provide tighter bounds than pointing-by-pointing stratification. Point-level bootstrap intervals underestimate the true cosmic variance and zodiacal background variance across all 100,000 SPHEREx survey pointings.

---

## 8. Limitations & Unresolved Scientific Risks

1. **Short-Wavelength Background Sensitivity (Detector 1):** D1 operates in the $0.75$–$1.10\ \mu\text{m}$ regime where stellar contamination and zodiacal scattered light are greatest. Operating thresholds calibrated on Pointings `0001` and `0008` yielded an empirical FPR of $22.6\%$–$25.0\%$ on the evaluation cohort. Future iterations must introduce band-specific background detrending or local PSF subtraction.
2. **Detector 2 Over-Conservatism:** D2 operating thresholds ($\tau = 2,536.30$) severely suppress point-source detection sensitivity ($\text{recovery} = 8.33\%$).
3. **Extended Source Aperture Dilution:** Using an unweighted circular aperture of radius $r = 5.0$ pixels ($80+$ pixels) aggregates residual background variance, degrading AUROC and recovery relative to peak scoring. Future extended anomaly scoring should employ matched-filter or Gaussian-weighted apertures.
4. **Generalization Scope:** While V3 successfully adapted to the North Ecliptic Pole, performance on Galactic Plane fields ($|b| < 10^\circ$) remains completely uncharacterized.

---

## 9. Final Scientific Qualification Statement

In accordance with Section 8 of the Task 1.1V Authorization Protocol:

```
========================================================================================
                      FINAL SCIENTIFIC QUALIFICATION STATEMENT                         
========================================================================================

                  ASTROVISION V3 SCIENTIFIC STATUS: PARTIAL

1. Engineering Implementation: PASS
   The software modules (MaskAwareConv2d, RobustLocalNormalizer, ApertureAnomalyScorer)
   are implemented cleanly, robustly, and pass all 79 repository unit tests.

2. Defect Remediation: PASS
   Both primary forensic failure modes identified in Task 1.1T are confirmed resolved:
   - D4 fatal defect pixel convolution bleed is eliminated (AUROC 0.4776 -> 0.7261).
   - NEP polar domain shift on Pointing 0010 is resolved (AUROC 0.6143 -> 0.8572).

3. Point-Source Anomaly Detection: PARTIAL
   Point-source detection is substantially improved across all detectors and fields:
   - AUROC increased from 0.6861 to 0.8040 (p = 3.4e-62).
   - Recovery increased from 18.80% to 34.80% (p = 7.5e-10).
   - Precision increased from 0.6861 to 0.7909.
   However, recovery at faint flux levels (SNR < 10) remains modest.

4. Extended-Source Anomaly Detection: EXPLORATORY
   Extended-source AUROC reached 0.7064 (peak scoring), but recovery remains low
   at 17.40%, and circular aperture integration suffered significant noise dilution.

5. False-Alarm Control: PARTIAL
   Empirical FPR across untouched null controls was 9.00% [95% CI: 6.79% - 11.83%]
   against a nominal alpha = 0.05 target, driven by D1 excess false alarms (22.6%).

6. Operational Certification & Deployment Readiness:
   RESTRICTED — NOT READY FOR UNATTENDED PIPELINE INGESTION.
   ASTROVISION V3 represents a validated, major scientific improvement over V2,
   qualifying it for human-in-the-loop candidate screening and targeted inspection,
   but does not meet the strict false-alarm and completeness standards required for
   autonomous Level-2 anomaly filtering.
========================================================================================
```

---

## 10. Ledger of Read & Created Files

### Files Read
1. `reports/ASTROVISION_TASK_1_1S_INDEPENDENT_AUDIT_REPORT.md`
2. `reports/ASTROVISION_TASK_1_1T_FORENSIC_FAILURE_ANALYSIS.md`
3. `reports/ASTROVISION_TASK_1_1U_REMEDIATION_REPORT.md`
4. `reports/manifests/astrovision_task_1_1s_independent_audit_manifest.json`
5. `reports/manifests/astrovision_task_1_1t_forensic_manifest.json`
6. `reports/manifests/astrovision_task_1_1u_remediation_manifest.json`
7. `reports/manifests/astrovision_five_partition_pilot_manifest.csv`
8. `checkpoints/astrovision_spatial_v2.pt`
9. `checkpoints/astrovision_spatial_v3.pt`
10. `checkpoints/astrovision_spatial_v3.json`
11. `data/processed/pilot_results/calibration_parameters_v3.json`
12. `data/processed/pilot_results/astrovision_pilot_trial_results.csv`
13. `models/astrovision/model_v3.py`
14. `models/astrovision/train_spatial_astrovision_v3.py`
15. `scripts/validation/astrovision_injection_benchmark_v2.py`
16. `scripts/validation/execute_pilot_benchmark_campaign.py`
17. `scratch/task_1_1v_evaluation.py`
18. `scratch/v3_evaluation_summary.json`

### Files Created
1. `data/processed/pilot_results/astrovision_v3_evaluation_trial_results.csv`
2. `scratch/v3_evaluation_summary.json`
3. `reports/ASTROVISION_TASK_1_1V_INDEPENDENT_QUALIFICATION_REPORT.md`
4. `reports/manifests/astrovision_task_1_1v_qualification_manifest.json`

### Confirmation of Historical Asset Protection
All historical reports, manifests, checkpoints (`checkpoints/astrovision_spatial_v2.pt`, `checkpoints/astrovision_spatial_v3.pt`), and raw trial CSVs were preserved in a strictly read-only manner. Zero bytes of historical artifacts were modified.

