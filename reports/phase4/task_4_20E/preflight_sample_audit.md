# SPECTRA-X / F1 — Phase 4, Task 4.20E
# Preflight Sample Availability, Calibration Cohort Census & Governance Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10)  
**Parent Tasks:** Phase 4 Tasks 4.12, 4.15, 4.16, 4.18, 4.19B, 4.19C, 4.19D, 4.20A–D  
**Target Module:** ASTROVISION V3 Spatial Anomaly Detection  
**Audit Date:** November 9, 2026  
**Governance Protocol:** STRICT READ-ONLY / BLIND EVALUATION ISOLATION / ZERO RETRAINING  

---

## 1. Executive Summary & Audit Mandate

In strict accordance with the **Phase 4, Task 4.20E** directives, a preflight sample audit and statistical census was conducted on all available Level-2 SPHEREx observations to evaluate the empirical feasibility of detector-stratified dynamic thresholding for ASTROVISION V3.

A rigorous sample-aware calibration framework requires that threshold modifications be justified by adequate statistical sample sizes, stability across resampling, and verifiable separation between calibration and evaluation data.

```
====================================================================================================
                        PREFLIGHT SAMPLE AVAILABILITY & GOVERNANCE AUDIT SUMMARY                    
====================================================================================================
  Total Available Observations in Build:             2,500 Trials Across 5 Pointings
  Separated Calibration Cohort (P0001, P0008):       1,000 Trials (500 Controls, 500 Point Injections)
  Quarantined Blind Evaluation Cohort (P0002, 9, 10): 1,500 Trials (500 Controls, 500 Point, 500 Ext)
  Zero Extended-Source Calibration Anomaly Defect:   CONFIRMED (N_cal,ext = 0; State C Fallback Mandated)
  Detector-Stratified Calibration Control Count:     D1: 84, D2: 84, D3: 83, D4: 83, D5: 83, D6: 83
  Bootstrap Stability Assessment (1,000 resamples):  ALL INDIVIDUAL DETECTORS EXHIBIT CV > 70%
  Pointing 1 Outlier Leverage in Detector 2:         CONFIRMED (P1 tau=3,322 vs P8 tau=331; 10x Disparity)
  Blind Evaluation Cohort Isolation:                 100% UNTOUCHED (Zero Blind-Label Leakage)
----------------------------------------------------------------------------------------------------
  PREFLIGHT GOVERNANCE VERDICT:                      PARTIAL_CALIBRATION_WITH_POOLED_FALLBACK
====================================================================================================
```

---

## 2. Comprehensive Cohort Census & Sample Accounting

### 2.1 Complete Dataset Census by Pointing, Role, Partition, and Detector
Every trial in the workspace has been tracked from its Level-2 FITS parent down to its detector and partition:

| Pointing | Field Designation | Pipeline Role | Partition Name | D1 | D2 | D3 | D4 | D5 | D6 | Total |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P0001** | Pilot Field 1 | CALIBRATION | CALIBRATION_CONTROL | 44 | 44 | 43 | 43 | 43 | 43 | **260** |
| **P0001** | Pilot Field 1 | CALIBRATION | CALIBRATION_INJECTION (Point) | 44 | 44 | 43 | 43 | 43 | 43 | **260** |
| **P0008** | Ecliptic Crossing | CALIBRATION | CALIBRATION_CONTROL | 40 | 40 | 40 | 40 | 40 | 40 | **240** |
| **P0008** | Ecliptic Crossing | CALIBRATION | CALIBRATION_INJECTION (Point) | 40 | 40 | 40 | 40 | 40 | 40 | **240** |
| **P0002** | Mod Galactic Extinction | EVALUATION | EVALUATION_CONTROL | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0002** | Mod Galactic Extinction | EVALUATION | EVAL_POINT_INJECTION | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0002** | Mod Galactic Extinction | EVALUATION | EVAL_EXTENDED_INJECTION | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0009** | Galactic Disk / Crowded | EVALUATION | EVALUATION_CONTROL | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0009** | Galactic Disk / Crowded | EVALUATION | EVAL_POINT_INJECTION | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0009** | Galactic Disk / Crowded | EVALUATION | EVAL_EXTENDED_INJECTION | 28 | 28 | 28 | 28 | 28 | 28 | **168** |
| **P0010** | NEP / Quiet Polar Sky | EVALUATION | EVALUATION_CONTROL | 28 | 28 | 27 | 27 | 27 | 27 | **164** |
| **P0010** | NEP / Quiet Polar Sky | EVALUATION | EVAL_POINT_INJECTION | 28 | 28 | 27 | 27 | 27 | 27 | **164** |
| **P0010** | NEP / Quiet Polar Sky | EVALUATION | EVAL_EXTENDED_INJECTION | 28 | 28 | 27 | 27 | 27 | 27 | **164** |
| **TOTAL** | — | — | — | **420** | **420** | **415** | **415** | **415** | **415** | **2,500** |

---

## 3. Critical Data Deficiencies & Methodological Vulnerabilities

### 3.1 Defect 1: Total Absence of Extended-Source Calibration Injections ($N_{\text{cal,ext}} = 0$)
The audit revealed an asymmetry between calibration and evaluation partitions:
- **Evaluation Partition:** Contains 500 synthetic point sources AND 500 synthetic diffuse extended sources ($R_{\text{ap}} = 5.0''$).
- **Calibration Partition:** Contains 500 synthetic point sources, but **ZERO extended sources** ($N = 0$).

**Governance Consequence:**  
It is mathematically impossible to empirically calibrate an extended-source threshold per detector from calibration data without introducing unvalidated assumptions. Any attempt to invent an empirical extended-source threshold would violate scientific governance.  
**Mandated Action:** State C (`INSUFFICIENT_SAMPLE_FALLBACK`) is strictly enforced for extended-source morphology, preserving the existing baseline aperture-integrated threshold $\tau_{\text{ext\_int}}$.

### 3.2 Defect 2: High Outlier Leverage and Pointing Discrepancy in Detector 2
In Calibration controls, Detector 2 displays a 10-fold discrepancy between pointing sub-samples:
- Pointing 1 ($N=44$): 95th percentile is **$\tau = 3,322.88$**.
- Pointing 8 ($N=40$): 95th percentile is **$\tau = 331.48$**.

The extreme value in Pointing 1 was driven by an unmasked 14th-magnitude stellar core that skewed the combined empirical threshold to $\tau = 2,536.30$. Calibrating on this sample suppressed genuine point-source recovery in evaluation to $8.33\%$.

### 3.3 Defect 3: Statistical Sample Size Limitations ($N \approx 84$)
With only $N = 83$ or $84$ control cutouts per detector, a target false positive rate of $\alpha = 0.05$ corresponds to the **4th or 5th highest observation** in the sample ($84 \times 0.05 = 4.2$). Consequently:
- Every individual detector's empirical 95th percentile has a bootstrap coefficient of variation $\text{CV} > 70\%$.
- D3, D4, and D5 exhibit $\text{CV} > 250\%$ due to single outlier leverage in the tail.
- Unconstrained State A thresholding is scientifically indefensible.

---

## 4. Strict Blind-Evaluation Firewall Certification

1. **Pointings Quarantined:** Pointings `P0002`, `P0009`, and `P0010` (and all 1,500 evaluation cutouts) were strictly excluded from threshold candidate selection, parameter fitting, and shrinkage estimation.
2. **Zero Contamination:** Thresholds were calibrated exclusively using the 500 `CALIBRATION_CONTROL` trials from Pointings `P0001` and `P0008`.
3. **Shadow Evaluation Only:** All evaluation benchmarks are reported as shadow-only comparisons without mutating production parameters.

---

## 5. Preflight Conclusion & Recommended Strategy

Because sample sizes are limited ($N \approx 84$) and extended calibration data is absent ($N=0$), an unconstrained detector-stratified calibration (State A for all detectors) is rejected.

The only scientifically valid strategy is **`PARTIAL_CALIBRATION_WITH_POOLED_FALLBACK`**:
1. Detectors D1 and D4 utilize James-Stein shrinkage toward the pooled reference threshold (State B).
2. Detectors D2, D3, D5, and D6 utilize fallback to the established baseline threshold (State C) to prevent ungrounded sensitivity collapse.
3. Extended sources universally trigger State C fallback.