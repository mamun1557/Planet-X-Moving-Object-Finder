# SPECTRA-X / F1 — Phase 4, Task 4.20E
# Shadow Evaluation & False-Positive Attribution Comparison Report

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Parent Tasks:** Phase 4 Tasks 4.12, 4.15, 4.18, 4.19B, 4.19C, 4.19D, 4.20A–D  
**Target Module:** ASTROVISION V3 Spatial Anomaly Detection  
**Audit Date:** November 9, 2026  
**Governance:** SHADOW-ONLY / PRODUCTION-PRESERVING  

---

## 1. Executive Summary & Experimental Design

In shadow mode, we evaluated five operating configurations across the complete 1,500-cutout blind evaluation cohort (500 controls, 500 point injections, 500 extended injections):
1. **Mode 1: Baseline Production Thresholds** ($\tau_{\text{prod}}$ from Task 4.12).
2. **Mode 2: Raw Calibrated Thresholds (State A)** ($\hat{\tau}_d$ empirical 95th percentiles).
3. **Mode 3: Empirical Bayes Shrunk Thresholds (State B)** (all detectors shrunk toward $\tau_{\text{pool}}$).
4. **Mode 4: Sample-Aware Calibrated Strategy (Recommended)** (State B on D1/D4; State C Fallback on D2/D3/D5/D6; State C Fallback on Extended).
5. **Mode 5: Adaptive Catalog Masking + Sample-Aware Dynamic Thresholds** (Composite Shadow Pipeline).

---

## 2. Comparative Benchmark Performance Summary

| Configuration Mode | False Alarms ($/500$) | Empirical FPR (%) | 95% Wilson CI | Point Recovery (%) | 95% Wilson CI | Extended Recovery (%) | 95% Wilson CI | Overall Budget Met (<5.0%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Mode 1: Baseline Production** | 45 | 9.00% | [6.76%, 11.87%] | 32.20% | [28.25%, 36.44%] | 17.40% | [14.30%, 20.99%] | **NO (FPR = 9.00%)** |
| **Mode 2: Raw State A** | 40 | 8.00% | [5.87%, 10.78%] | 28.20% | [24.43%, 32.32%] | 13.80% | [11.02%, 17.13%] | **NO (FPR = 8.00%)** |
| **Mode 3: Shrunk State B** | 37 | 7.40% | [5.35%, 10.11%] | 17.20% | [14.12%, 20.78%] | 10.00% | [7.63%, 12.99%] | **NO (Sensitivity Collapsed)** |
| **Mode 4: Sample-Aware Recommended** | 38 | 7.60% | [5.53%, 10.33%] | 27.80% | [24.05%, 31.90%] | 17.40% | [14.30%, 20.99%] | **NO (Thresholding Alone Inadequate)** |
| **Mode 5: Masking + Dynamic Thresholds** | **11** | **2.20%** | **[1.23%, 3.90%]** | **34.80%** | **[30.76%, 39.08%]** | **17.40%** | **[14.30%, 20.99%]** | **YES (FPR = 2.20%)** |

---

## 3. Key Scientific & Physical Findings

### 3.1 Finding 1: Dynamic Thresholding Alone Cannot Solve the False-Positive Problem
As shown in Mode 4, applying sample-aware dynamic thresholds reduces false alarms from 45 to 38 ($\text{FPR} = 7.60\%$). It fails to achieve the mission budget of $\le 5.00\%$.
- **Physical Reason:** 100% of the false positives in Detector 1 and crowded fields are **unmasked catalog stars** with anomaly scores $\chi^2 > 500 - 2,000$.
- Elevating the threshold enough to eliminate these bright stars destroys sensitivity to genuine faint point sources ($S_{\text{peak}} \sim 200 - 400$).

### 3.2 Finding 2: Unconstrained Shrinkage Destroys Thermal Band Sensitivity
In Mode 3, shrinking all detectors toward the pooled reference threshold ($\tau_{\text{pool}} = 683.16$) increased the threshold in Detector 5 from $91.85$ to $389.28$.
- As a consequence, Detector 5 point-source recovery collapsed from **$59.04\%$ down to $13.25\%$**.
- This proves the necessity of **State C Fallback** in thermal regimes (Detectors 5 and 6).

### 3.3 Finding 3: Synergistic Efficacy of Catalog Masking + Dynamic Thresholding
When Adaptive Catalog-Aware Masking (Adaptive-A) is combined with dynamic thresholding (Mode 5):
- External catalog stars are masked in the input defect filter ($M_{\text{valid}} = 0$).
- Central anomaly aperture remains 100% unencroached (zero point-source loss).
- False alarms drop from 45 to 11 ($\text{FPR} = 2.20\%$).
- Point-source recovery is restored to **$34.80\%$**, and extended recovery is fully preserved at **$17.40\%$**.

---

## 4. McNemar Paired Statistical Test

Comparing Baseline Mode 1 vs Composite Mode 5 on the 500 null controls:
- **Baseline FP, Shadow Negative ($b$):** 34 cutouts remediated.
- **Baseline Negative, Shadow FP ($c$):** 0 cutouts degraded.
- **McNemar Chi-Square Statistic:**
  $$\chi^2 = \frac{(|b - c| - 1)^2}{b + c} = \frac{(34 - 1)^2}{34} = 32.03 \quad (p = 1.52 \times 10^{-8})$$

The false-positive reduction is statistically significant at $p < 10^{-7}$.