# SPECTRA-X / F1 — Phase 4, Task 4.13E
# Detector 2 Threshold Calibration Safety Audit & Cohort Separation

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Target Module:** ASTROVISION Detector 2 ($1.12	ext{--}1.68\,\mu	ext{m}$)  
**Authoritative Verdict:** **PRODUCTION THRESHOLD MUST REMAIN FROZEN**  

---

## 1. Mission & Background

In the baseline benchmark, Detector 2 exhibited anomalous point-source recovery:
- **Baseline Point Recovery:** **8.33%** (only 7 of 84 injected sources recovered)
- **Production Threshold:** $	au_{	ext{peak}} = 2536.30$

This audit investigates the origin of this elevated threshold, verifies calibration cohort isolation, and evaluates the safety of potential threshold adjustments.

---

## 2. Quantitative Verification of Diagnostic Findings

| Parameter | Production Baseline | P0008 Calibration Subset |
|---|---:|---:|
| **Operating Threshold ($	au_{	ext{peak}}$)** | **2536.30** | **331.48** |
| **Point-Source Recovery** | **8.33%** (7/84) | **44.05%** (37/84) |
| **Statistical Significance (McNemar)** | Baseline | $\chi^2 = 30.0$, $p = 4.32 	imes 10^{-8}$ |
| **Evaluation Control False Positives** | 7 / 84 (8.33%) | **19 / 84 (22.62%)** |
| **Clean Control False Positives (Bit-21 Clean)** | 0 / 30 (0.00%) | **0 / 30 (0.00%)** |

### Verification of Reported Metrics:
1. **Recovery Restoration Confirmed:** Lowering $	au$ to 331.48 restores point recovery from **8.33% to 44.05%** ($\Delta = +35.72\%$).
2. **Blind-Field FPR Surge Confirmed:** At $	au = 331.48$, the empirical FPR on the unvetted blind evaluation cohort surges from **8.33% to 22.62%** (19/84 false alarms).
3. **Source-Contamination Concurrence Confirmed:** Exactly 19 of the 19 false alarms at $	au = 331.48$ possess SPHEREx Level 2 `SOURCE` flag bit 21 (`2097152`). On the 30 clean controls, FPR is **0.00%**.

---

## 3. Root Cause Analysis: Outlier Skew in Calibration

The production threshold $	au = 2536.30$ was calibrated across both Pointing 0001 and Pointing 0008.
- In Pointing 0001 (low galactic latitude, dense stellar field), several calibration cutouts contained unmasked field stars with fluxes exceeding $900\,	ext{MJy/sr}$.
- These unmasked stars generated immense reconstruction $\chi^2$ residuals (up to $21,398$), severely inflating the 95th percentile empirical threshold to $2536.30$.
- In Pointing 0008 (high galactic latitude calibration field), the 95th percentile threshold is **$	au = 331.48$**.

---

## 4. Cohort Separation & Safety Assessment

### Mandatory Safety Requirements:
1. **Production Threshold Frozen:** The production threshold $	au = 2536.30$ in `data/processed/pilot_results/calibration_parameters_v3.json` must NOT be updated.
2. **FPR Budget Protection:** Deploying $	au = 331.48$ directly into production would breach the project false alarm budget ($lpha = 5.00\%$), causing D2 FPR to surge to $22.62\%$.
3. **Prerequisite for Remediation:** Lowering D2's threshold can ONLY be approved after an active upstream catalog star mask (`is_known_gaia_star` via MOTION-X / FUSION-X) is implemented.

---

## 5. Required Additional Calibration Evidence

Prior to proposing any future D2 threshold modification:
1. **Stellar Mask Calibration Dataset:** A re-calibrated P0001/P0008 control cohort with all catalog stars masked to establish true sky noise floor.
2. **Multi-Pointing Validation:** Verification across at least three independent clean high-latitude pointings to confirm that empirical FPR $\le 5.00\%$.
