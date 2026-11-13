# SPECTRA-X / F1 — Phase 4, Task 4.13D
# Crowding-Aware Controlled Experiments for Detectors D1 and D4

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Target Detectors:** Detector 1 (Band 1: $0.75	ext{--}1.12\,\mu	ext{m}$) & Detector 4 (Band 4: $2.42	ext{--}3.48\,\mu	ext{m}$)  
**Governance:** Non-Production Diagnostic Isolation / Frozen Model & Thresholds  

---

## 1. Experimental Overview

Detectors D1 and D4 represent the two most challenging regimes for ASTROVISION:
- **Detector 1 (Short Wavelength):** Experiences maximum stellar density, steep PSF profiles, and high galactic crowding in Pointing 0009 ($b = 24.8^\circ$). Baseline $	ext{FPR} = 22.62\%$ ($19/84$).
- **Detector 4 (Mid-Infrared):** Suffers from clustered fatal dead pixels and localized mask artifacts. Baseline $	ext{FPR} = 10.84\%$ ($9/83$).

Four controlled variants were tested under strict non-mutating conditions:
1. **Variant 1 (Original ASTROVISION Baseline):** All 84 (D1) and 83 (D4) evaluation controls evaluated as originally generated.
2. **Variant 2A (Diagnostic Exclusion of Crowded Cutouts):** Excludes cutouts containing bright off-center stars ($> 100\,	ext{MJy/sr}$).
3. **Variant 2B (Strict Exclusion of Center Bit-21 Mapped Pixels):** Excludes pixels with SPHEREx Level 2 `SOURCE` flag active.
4. **Variant 2C (Combined Isolated True Sky):** Cutout peak $\le 100\,	ext{MJy/sr}$ and center Bit-21 is False.

---

## 2. Experimental Results Matrix

### Detector 1 (Band 1: $0.75 - 1.12\,\mu	ext{m}$)

| Metric | Variant 1 (Baseline) | Variant 2A (Peak $\le 100$) | Variant 2B (Bit-21 Clean) | Variant 2C (Combined Clean) |
|---|---:|---:|---:|---:|
| **Valid Controls ($N_{	ext{ctrl}}$)** | 84 | 11 | 29 | 8 |
| **Excluded Controls ($N_{	ext{ex}}$)** | 0 | 73 (86.9%) | 55 (65.5%) | 76 (90.5%) |
| **False Positives ($k$)** | 19 | 1 | 0 | 0 |
| **Empirical FPR ($lpha$)** | **22.62%** | **9.09%** | **0.00%** | **0.00%** |
| **95% Wilson CI** | [14.99%, 32.65%] | [1.62%, 37.74%] | [0.00%, 11.70%] | [0.00%, 32.44%] |
| **Point-Source AUROC** | 0.7745 | 0.8972 | **0.9622** | **0.9747** |
| **Point Recovery (Int)** | 61.90% (52/84) | 61.90% (52/84) | 61.90% (52/84) | 61.90% (52/84) |
| **Precision** | 71.23% | 98.11% | **100.00%** | **100.00%** |

### Detector 4 (Band 4: $2.42 - 3.48\,\mu	ext{m}$)

| Metric | Variant 1 (Baseline) | Variant 2A (Peak $\le 100$) | Variant 2B (Bit-21 Clean) | Variant 2C (Combined Clean) |
|---|---:|---:|---:|---:|
| **Valid Controls ($N_{	ext{ctrl}}$)** | 83 | 2 | 26 | 1 |
| **Excluded Controls ($N_{	ext{ex}}$)** | 0 | 81 (97.6%) | 57 (68.7%) | 82 (98.8%) |
| **False Positives ($k$)** | 9 | 0 | 0 | 0 |
| **Empirical FPR ($lpha$)** | **10.84%** | **0.00%** | **0.00%** | **0.00%** |
| **95% Wilson CI** | [5.81%, 19.34%] | [0.00%, 65.76%] | [0.00%, 12.87%] | [0.00%, 79.35%] |
| **Point-Source AUROC** | 0.7261 | 0.9518 | **0.9222** | **1.0000** |
| **Point Recovery (Int)** | 21.69% (18/83) | 21.69% (18/83) | 21.69% (18/83) | 21.69% (18/83) |
| **Precision** | 64.29% | 100.00% | **100.00%** | **100.00%** |

---

## 3. Scientific Discussion & Findings

1. **Definitive Explanation of Elevated False Positives:**
   - In both D1 and D4, **100% of the false positives occurred on pixels that had bit 21 (`SOURCE`) set**.
   - When bit-21 flagged pixels are excluded from the negative control set (Variant 2B), the empirical false-positive rate drops to **0.00% in both detectors** (0/29 in D1, 0/26 in D4).
   - Point-source AUROC correspondingly increases from **0.7745 to 0.9622 in D1** and from **0.7261 to 0.9222 in D4**.

2. **Rejection of Preprocessing Median Subtraction:**
   - As established in Task 4.12, applying aggressive local median filters (e.g. $32	imes 32$ box median) does not solve crowding; it artificially subtracts real anomaly fluxes, degrading anomaly AUROC from 0.8040 to 0.7420.
   - The true solution is **upstream catalog star de-blending and masking**, not spatial high-pass filtering.

3. **Production Safety Reaffirmation:**
   - No production thresholds, model weights, or input masks were altered. All variants represent diagnostic offline accounting.
