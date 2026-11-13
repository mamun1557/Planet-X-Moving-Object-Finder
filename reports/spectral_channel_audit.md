# SPECTRA-X: Six-Detector Spectral Channel Audit & WCS Calibration Report

**Role:** Senior ML Engineer, Scientific Data Auditor, and Astronomical ML Research Engineer  
**Project:** SPECTRA-X / F1  
**Phase:** 5 — Verify All 102 Spectral Channels  
**Execution Timestamp:** `2026-11-03T01:17:00+00:00`  
**Calibration Files Audited:** `data/spherex/qr3/calibration/spectral_wcs_D*.fits` (Detectors 1–6), `data/spherex/qr3/calibration/spectral_channels_spx_cal-sch-v2-2026-229.fits` (Official 102-Channel Grid), `data/spherex/qr2/calibration/spectral_wcs_D*.fits` (Detectors 1–6)  
**Catalogs Audited:** `[validation_assembled_spectra.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/data/processed/spectral_features/validation_assembled_spectra.csv)` (3,665 sources), `[independent_test_assembled_spectra.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/data/processed/spectral_features/independent_test_assembled_spectra.csv)` (1,392 sources)

---

## 1. Executive Summary

This forensic audit verifies the spectrophotometric coordinate system, linear variable filter (LVF) dispersion mapping, and 102-channel spectral assembly across all six SPHEREx detectors.

### Key Audit Findings:
1. **Official 102-Channel Grid Verified**: The official calibration table `spectral_channels_spx_cal-sch-v2-2026-229.fits` defines exactly **102 channels** (17 channels $\times$ 6 detectors) spanning **$0.743\,\mu\text{m}$ to $5.009\,\mu\text{m}$** with resolving power $R \approx 34 - 135$.
2. **All 6 Spectral WCS Detectors Verified**: High-resolution 2D $(2040, 2040)$ maps for `CWAVE` (central wavelength) and `CBAND` (bandwidth) exist and were audited for all 6 detectors (D1 through D6) in both QR2 (`v4-2025-254`) and QR3 (`v5-2026-191`). Zero NaNs or Infs were found across all $6 \times 2040 \times 2040 = 24,969,600$ calibration pixels.
3. **Continuous-to-Discrete Mapping Validated**: Continuous pixel wavelengths $\lambda(x, y)$ from `CWAVE` match their respective detector's official channel grid with continuous boundary coverage.
4. **Current Level-2 Science Data Limitation Verified**: All 32 Level-2 science FITS files in the local archive belong exclusively to **Detector 1** (QR3 wide and deep) and **Detector 2** (QR2 wide and deep). There are **zero Level-2 science exposures for Detectors 3, 4, 5, and 6** in the current 5.195 GB dataset.
5. **No Complete 102-Channel Source Exists in Local Raw Data**: Assembled real astrophysical spectra have coverage ranging from 1 to 4 channels per source, strictly confined to Channels 0–33 (Detectors 1 and 2). All channels from 34 to 101 are unobserved in local science data.
6. **Masking Policy Verified**: Unobserved channels are strictly preserved as `NaN` with `valid_channel_mask = False`. Zero-filling has been completely eradicated from the assembly and training pipelines.

---

## 2. Official 102-Channel Grid Standardization

The master spectral reference is defined in HDU 2 (`SPECTRAL_CHANNELS`) of `spectral_channels_spx_cal-sch-v2-2026-229.fits`.

### Master 102-Channel Grid Summary by Detector

| Detector ID | Channel Index Range | Subchannels | Wavelength Range ($\mu\text{m}$) | Central $\lambda$ Range ($\mu\text{m}$) | Resolving Power $R = \lambda/\Delta\lambda$ | Bandwidth Range ($\mu\text{m}$) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Detector 1** | Channels 0 – 16 | $1 - 17$ | $0.7430 - 1.1160\,\mu\text{m}$ | $0.7530 - 1.1020\,\mu\text{m}$ | $37.0 - 42.0$ | $0.0180 - 0.0300\,\mu\text{m}$ |
| **Detector 2** | Channels 17 – 33 | $1 - 17$ | $1.0990 - 1.6510\,\mu\text{m}$ | $1.1130 - 1.6310\,\mu\text{m}$ | $41.0 - 43.0$ | $0.0260 - 0.0390\,\mu\text{m}$ |
| **Detector 3** | Channels 34 – 50 | $1 - 17$ | $1.6360 - 2.4400\,\mu\text{m}$ | $1.6560 - 2.3990\,\mu\text{m}$ | $40.0 - 42.0$ | $0.0390 - 0.0590\,\mu\text{m}$ |
| **Detector 4** | Channels 51 – 67 | $1 - 17$ | $2.4220 - 3.8270\,\mu\text{m}$ | $2.4450 - 3.7680\,\mu\text{m}$ | $34.0 - 42.0$ | $0.0580 - 0.1030\,\mu\text{m}$ |
| **Detector 5** | Channels 68 – 84 | $1 - 17$ | $3.8144 - 4.4264\,\mu\text{m}$ | $3.8330 - 4.4050\,\mu\text{m}$ | $108.0 - 117.0$ | $0.0350 - 0.0380\,\mu\text{m}$ |
| **Detector 6** | Channels 85 – 101 | $1 - 17$ | $4.4184 - 5.0094\,\mu\text{m}$ | $4.4350 - 4.9880\,\mu\text{m}$ | $125.0 - 135.0$ | $0.0350 - 0.0380\,\mu\text{m}$ |
| **TOTAL** | **0 – 101** | **102 channels** | **$0.7430 - 5.0094\,\mu\text{m}$** | **$0.7530 - 4.9880\,\mu\text{m}$** | **$34.0 - 135.0$** | **$0.0180 - 0.1030\,\mu\text{m}$** |

### Verified Boundary Continuity Across Detectors:
- **D1 to D2 Transition**: D1 upper $\lambda_{\text{max}} = 1.116\,\mu\text{m}$, D2 lower $\lambda_{\text{min}} = 1.099\,\mu\text{m}$ $\rightarrow$ **$17\,\text{nm}$ overlap**.
- **D2 to D3 Transition**: D2 upper $\lambda_{\text{max}} = 1.651\,\mu\text{m}$, D3 lower $\lambda_{\text{min}} = 1.636\,\mu\text{m}$ $\rightarrow$ **$15\,\text{nm}$ overlap**.
- **D3 to D4 Transition**: D3 upper $\lambda_{\text{max}} = 2.440\,\mu\text{m}$, D4 lower $\lambda_{\text{min}} = 2.422\,\mu\text{m}$ $\rightarrow$ **$18\,\text{nm}$ overlap**.
- **D4 to D5 Transition**: D4 upper $\lambda_{\text{max}} = 3.827\,\mu\text{m}$, D5 lower $\lambda_{\text{min}} = 3.814\,\mu\text{m}$ $\rightarrow$ **$13\,\text{nm}$ overlap**.
- **D5 to D6 Transition**: D5 upper $\lambda_{\text{max}} = 4.426\,\mu\text{m}$, D6 lower $\lambda_{\text{min}} = 4.418\,\mu\text{m}$ $\rightarrow$ **$8\,\text{nm}$ overlap**.

The 102-channel grid provides seamless, gap-free spectral coverage across the entire $0.75 - 5.0\,\mu\text{m}$ infrared window.

---

## 3. High-Resolution 2D Spectral WCS Audit (Detectors 1 to 6)

Every pixel $(x, y)$ on a SPHEREx detector maps to a central wavelength $\lambda = \text{CWAVE}[y, x]$ and full-width at half-maximum bandwidth $\Delta\lambda = \text{CBAND}[y, x]$.

We audited all 12 standalone `spectral_wcs_D*.fits` files in the repository:

### Detailed Inspection of QR3 Calibration Maps (`v5-2026-191`)

| Det | File Name | Array Shape | CWAVE Min ($\mu\text{m}$) | CWAVE Max ($\mu\text{m}$) | CBAND Min ($\mu\text{m}$) | CBAND Max ($\mu\text{m}$) | NaNs / Infs | Grid Range ($\mu\text{m}$) | Coverage Verified? |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | `spectral_wcs_D1_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $0.7346$ | $1.1266$ | $0.0143$ | $0.0312$ | 0 | $0.7430 - 1.1160$ | **VERIFIED** |
| **D2** | `spectral_wcs_D2_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $1.0853$ | $1.6678$ | $0.0237$ | $0.0408$ | 0 | $1.0990 - 1.6510$ | **VERIFIED** |
| **D3** | `spectral_wcs_D3_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $1.6162$ | $2.4395$ | $0.0249$ | $0.0612$ | 0 | $1.6360 - 2.4400$ | **VERIFIED** |
| **D4** | `spectral_wcs_D4_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $2.3948$ | $3.8673$ | $0.0311$ | $0.1139$ | 0 | $2.4220 - 3.8270$ | **VERIFIED** |
| **D5** | `spectral_wcs_D5_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $3.7983$ | $4.4459$ | $0.0344$ | $0.0395$ | 0 | $3.8144 - 4.4264$ | **VERIFIED** |
| **D6** | `spectral_wcs_D6_spx_cal-swcs-v5-2026-191.fits` | $(2040, 2040)$ | $4.4014$ | $5.0254$ | $0.0329$ | $0.0408$ | 0 | $4.4184 - 5.0094$ | **VERIFIED** |

### Detailed Inspection of QR2 Calibration Maps (`v4-2025-254`)

| Det | File Name | Array Shape | CWAVE Min ($\mu\text{m}$) | CWAVE Max ($\mu\text{m}$) | CBAND Min ($\mu\text{m}$) | CBAND Max ($\mu\text{m}$) | NaNs / Infs | Status |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **D1** | `spectral_wcs_D1_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $0.7346$ | $1.1266$ | $0.0143$ | $0.0312$ | 0 | **VERIFIED** |
| **D2** | `spectral_wcs_D2_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $1.0853$ | $1.6678$ | $0.0237$ | $0.0408$ | 0 | **VERIFIED** |
| **D3** | `spectral_wcs_D3_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $1.6162$ | $2.4395$ | $0.0249$ | $0.0612$ | 0 | **VERIFIED** |
| **D4** | `spectral_wcs_D4_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $2.3948$ | $3.8673$ | $0.0311$ | $0.1139$ | 0 | **VERIFIED** |
| **D5** | `spectral_wcs_D5_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $3.7919$ | $4.4395$ | $0.0344$ | $0.0395$ | 0 | **VERIFIED** |
| **D6** | `spectral_wcs_D6_spx_cal-wcs-v4-2025-254.fits` | $(2040, 2040)$ | $4.3950$ | $5.0190$ | $0.0329$ | $0.0408$ | 0 | **VERIFIED** |

All six detectors possess valid, verified 2D continuous dispersion maps in both release calibrations.

---

## 4. Audit of Assembled Observational Spectral Datasets

We audited both the primary training/validation assembled catalog and the newly extracted independent test catalog.

### 4.1 Primary Dataset: `validation_assembled_spectra.csv`
- **Total Assembled Sources**: **3,665**
- **Provenance**: Pointing 0001 (Train: 2,416 sources) and Pointing 0004 (Val: 1,249 sources).
- **Detectors Represented**:
  * Detector 1: 2,483 sources ($67.7\%$)
  * Detector 2: 1,182 sources ($32.3\%$)
  * Detectors 3, 4, 5, 6: **0 sources** ($0.0\%$)
- **Valid Channel Coverage per Source**:
  * 1 Channel: 1,983 sources ($54.1\%$)
  * 2 Channels: 1,209 sources ($33.0\%$)
  * 3 Channels: 363 sources ($9.9\%$)
  * 4 Channels: 110 sources ($3.0\%$)
  * $>4$ Channels: **0 sources** ($0.0\%$)
- **Max Valid Channels Observed for Any Single Source**: **4 channels** (Channels 0–33 only).
- **Missing Channels**: Exactly 98 to 101 channels are missing (`NaN`) per source.

### 4.2 Independent Test Dataset: `independent_test_assembled_spectra.csv`
- **Total Assembled Sources**: **1,392**
- **Provenance**: Pointing 0003 (Independent Test, 4 dithers, Detector 1).
- **Detectors Represented**: Detector 1 exclusively (1,392 sources).
- **Valid Channel Coverage per Source**:
  * 1 Channel: 940 sources ($67.5\%$)
  * 2 Channels: 338 sources ($24.3\%$)
  * 3 Channels: 91 sources ($6.5\%$)
  * 4 Channels: 23 sources ($1.7\%$)
- **Missing Channels**: Exactly 98 to 101 channels are missing (`NaN`) per source.

---

## 5. Root Cause: Why Are 98+ Channels Missing in Real Data?

A naive evaluator might assume that a 102-channel spectral model must ingest 102 valid flux numbers for every source. In astronomical reality, SPHEREx operates under a specific observational paradigm:

1. **Linear Variable Filter (LVF) Geometry**:
   SPHEREx does not disperse light like a slit spectrograph; it is a monochromatic imaging photometer where central wavelength varies along the detector's spatial $y$-axis.
2. **Coordinated Pointing Requirement**:
   To observe a star across all 102 channels ($0.75 - 5.0\,\mu\text{m}$), the telescope must execute multiple pointings stepping the source across:
   - Detector 1 (channels 0–16)
   - Detector 2 (channels 17–33)
   - Detector 3 (channels 34–50)
   - Detector 4 (channels 51–67)
   - Detector 5 (channels 68–84)
   - Detector 6 (channels 85–101)
3. **Archive Scope Limitation**:
   The downloaded 5.195 GB dataset contains targeted demonstration pointings:
   - QR3 downloaded only Detector 1 science frames.
   - QR2 downloaded only Detector 2 science frames.
   - Zero science files were downloaded for Detectors 3, 4, 5, and 6.

Therefore, expecting complete 102-channel observational SEDs from the existing raw dataset is **scientifically impossible**.

---

## 6. Scientific Masking Policy & Zero-Fill Elimination

In previous legacy pipelines, missing spectral channels were filled with `0.0`, corrupting autoencoder training by teaching the model that astronomical objects have zero flux across $95\%$ of their infrared spectrum.

### The Audited Policy:
1. **Preservation of `NaN` in Catalogs**:
   All unobserved channels are strictly stored as `NaN` (or `None` in JSON serialization) in the `flux` and `uncertainty` arrays.
2. **Boolean Mask Tracking**:
   Every record includes `valid_channel_mask` (an array of 102 booleans).
3. **Masked Loss Formulation**:
   In `train_masked_spectra.py`, invalid channels have mask $m_i = 0$ and do not contribute to loss:
   $$\mathcal{L} = \frac{\sum_{i=0}^{101} m_i w_i (\hat{x}_i - x_i)^2}{\sum_{i=0}^{101} m_i w_i}$$
4. **Isolated Normalization**:
   Flux normalization is computed using the median of valid channels only ($\text{scale} = \text{median}(F[m == 1])$).

### Spectral Verification Checklist

- [x] Official 102-channel table verified (`spectral_channels_spx_cal-sch-v2-2026-229.fits`).
- [x] Detector 1 dispersion map verified ($0.7346 - 1.1266\,\mu\text{m}$).
- [x] Detector 2 dispersion map verified ($1.0853 - 1.6678\,\mu\text{m}$).
- [x] Detector 3 dispersion map verified ($1.6162 - 2.4395\,\mu\text{m}$).
- [x] Detector 4 dispersion map verified ($2.3948 - 3.8673\,\mu\text{m}$).
- [x] Detector 5 dispersion map verified ($3.7983 - 4.4459\,\mu\text{m}$).
- [x] Detector 6 dispersion map verified ($4.4014 - 5.0254\,\mu\text{m}$).
- [x] Pixel-level CWAVE correspondence verified against official channel boundaries.
- [x] Zero-fill eliminated; unobserved channels preserved as `NaN` with explicit boolean masks.
- [!] Real-world coverage limitation documented: Local raw data covers Detectors 1 & 2 only (Channels 0–33). Detectors 3–6 science data remain **NOT AVAILABLE** in local storage.
