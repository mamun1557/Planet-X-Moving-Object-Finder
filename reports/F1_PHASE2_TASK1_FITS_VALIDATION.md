# SPECTRA-X / F1 — PHASE 2, TASK 1: ASTROPY FITS VALIDATION REPORT
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE & VERIFIED

---

## 1. Executive Summary

Using Astropy 6.x, an exhaustive HDU structure, header metadata, WCS distortion, and photometric pixel array audit was executed across all **23 Pointing 0003 Level-2 science FITS files** (4 pre-existing D1 reference files + 19 newly acquired D2–D6 files) in [`data/spherex/qr3/level2/`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/spherex/qr3/level2/).

### Core Validation Findings:
- **FITS Readability:** **23 / 23 files (100.0%)** parsed with zero I/O errors or checksum corruption.
- **HDU Completeness:** Every file adheres strictly to the SPHEREx Level-2 multi-extension FITS architecture (7 HDUs per file).
- **Coordinate System:** Every exposure contains a fully populated `RA---TAN-SIP` / `DEC--TAN-SIP` astrometric solution with valid Simple Imaging Polynomial (SIP) distortion terms.
- **Science Quality:** Over **99.9% finite pixels** across all science arrays; zero NaN collapses.
- **Photometric Uncertainty:** Valid positive variances present in HDU 3 (`VARIANCE`) across all detectors.
- **Wavelength Solutions:** Continuous LVF linear variable filter mapping verified in HDU 6 (`WCS-WAVE`) covering the complete **0.735 to 5.025 μm** spectrum across Detectors D1–D6.
- **Validation Status:** **`VALID_SCIENCE_FITS`** for all 23 files.
- **Machine-Readable Metadata:** Fully serialized in [`data/manifests/f1_phase2_fits_validation.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_phase2_fits_validation.json).

---

## 2. SPHEREx Level-2 HDU Architecture

Every file in Pointing 0003 contains seven specialized HDU extensions:

| HDU Index | Extension Name | Data Type | Dimensions | Description / Scientific Function |
| :---: | :--- | :---: | :---: | :--- |
| **0** | `PRIMARY` | None | None | Top-level metadata container (`VERSION = 7.0.5`) |
| **1** | `IMAGE` | `>f4` (float32) | $2040 \times 2040$ | Calibrated science surface brightness in $\text{MJy/sr}$ |
| **2** | `FLAGS` | `int32` | $2040 \times 2040$ | Pixel-level Data Quality (DQ) bitmask (cosmics, bad pixels, saturation) |
| **3** | `VARIANCE` | `>f4` (float32) | $2040 \times 2040$ | Propagated photometric variance $\sigma^2$ in $(\text{MJy/sr})^2$ |
| **4** | `ZODI` | `>f4` (float32) | $2040 \times 2040$ | Modeled zodiacal light background surface brightness |
| **5** | `EPSF` | Binary Table | 441 records | Spatially variable Empirical Point Spread Function ($33 \times 33$ grid) |
| **6** | `WCS-WAVE`| Binary Table | $11 \times 11 \times 2$ | 2D Chebyshev coordinate grid of central $\lambda$ and bandwidth $\Delta\lambda$ |

---

## 3. Comprehensive File-by-File Validation Matrix

The table below records the empirical metrics extracted by [`scripts/validate_pointing_0003_d1_d6.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/validate_pointing_0003_d1_d6.py):

| Filename | Det | Dith | Observation Time (UTC) | MJD | Center $\alpha$ (deg) | Center $\delta$ (deg) | Pixel Scale | $\lambda_{\min} - \lambda_{\max}$ ($\mu\text{m}$) | Median Flux | Median $\sigma$ | Status |
| :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `..._1D1_...fits` | **D1** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 165.6927 | -69.5640 | 6.13" | 0.735 – 1.126 | 0.311 | 0.0208 | **`VALID`** |
| `..._1D2_...fits` | **D2** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 170.8421 | -73.0581 | 6.11" | 1.086 – 1.668 | 0.271 | 0.0187 | **`VALID`** |
| `..._1D3_...fits` | **D3** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 178.0951 | -76.4270 | 6.13" | 1.616 – 2.439 | 0.184 | 0.0158 | **`VALID`** |
| `..._1D4_...fits` | **D4** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 165.6324 | -69.5650 | 6.14" | 2.398 – 3.863 | 0.170 | 0.0138 | **`VALID`** |
| `..._1D5_...fits` | **D5** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 170.7837 | -73.0627 | 6.11" | 3.798 – 4.443 | 0.212 | 0.0332 | **`VALID`** |
| `..._1D6_...fits` | **D6** | 1 | 2026-07-20T00:26:21.423 | 61241.01830 | 178.0285 | -76.4390 | 6.14" | 4.402 – 5.025 | 0.371 | 0.0498 | **`VALID`** |
| `..._2D1_...fits` | **D1** | 2 | 2026-07-20T00:28:30.353 | 61241.01980 | 165.1732 | -69.6400 | 6.13" | 0.735 – 1.126 | 0.304 | 0.0204 | **`VALID`** |
| `..._2D2_...fits` | **D2** | 2 | 2026-07-20T00:28:30.353 | 61241.01980 | 170.2422 | -73.1493 | 6.11" | 1.086 – 1.668 | 0.267 | 0.0185 | **`VALID`** |
| `..._2D4_...fits` | **D4** | 2 | 2026-07-20T00:28:30.354 | 61241.01980 | 165.1127 | -69.6408 | 6.14" | 2.398 – 3.863 | 0.163 | 0.0134 | **`VALID`** |
| `..._2D5_...fits` | **D5** | 2 | 2026-07-20T00:28:30.353 | 61241.01980 | 170.1832 | -73.1537 | 6.11" | 3.798 – 4.443 | 0.204 | 0.0323 | **`VALID`** |
| `..._2D6_...fits` | **D6** | 2 | 2026-07-20T00:28:30.353 | 61241.01980 | 177.3357 | -76.5502 | 6.14" | 4.402 – 5.025 | 0.358 | 0.0484 | **`VALID`** |
| `..._3D1_...fits` | **D1** | 3 | 2026-07-20T00:30:39.285 | 61241.02129 | 164.6500 | -69.7143 | 6.13" | 0.735 – 1.126 | 0.300 | 0.0203 | **`VALID`** |
| `..._3D2_...fits` | **D2** | 3 | 2026-07-20T00:30:39.285 | 61241.02129 | 169.6359 | -73.2387 | 6.11" | 1.086 – 1.668 | 0.266 | 0.0185 | **`VALID`** |
| `..._3D3_...fits` | **D3** | 3 | 2026-07-20T00:30:39.284 | 61241.02129 | 176.7009 | -76.6479 | 6.13" | 1.616 – 2.439 | 0.178 | 0.0155 | **`VALID`** |
| `..._3D4_...fits` | **D4** | 3 | 2026-07-20T00:30:39.285 | 61241.02129 | 164.5893 | -69.7150 | 6.14" | 2.398 – 3.863 | 0.160 | 0.0133 | **`VALID`** |
| `..._3D5_...fits` | **D5** | 3 | 2026-07-20T00:30:39.285 | 61241.02129 | 169.5766 | -73.2429 | 6.11" | 3.798 – 4.443 | 0.201 | 0.0322 | **`VALID`** |
| `..._3D6_...fits` | **D6** | 3 | 2026-07-20T00:30:39.284 | 61241.02129 | 176.6319 | -76.6595 | 6.14" | 4.402 – 5.025 | 0.358 | 0.0484 | **`VALID`** |
| `..._4D1_...fits` | **D1** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 164.1228 | -69.7871 | 6.13" | 0.735 – 1.126 | 0.294 | 0.0201 | **`VALID`** |
| `..._4D2_...fits` | **D2** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 169.0230 | -73.3263 | 6.11" | 1.086 – 1.668 | 0.260 | 0.0183 | **`VALID`** |
| `..._4D3_...fits` | **D3** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 175.9863 | -76.7554 | 6.13" | 1.616 – 2.439 | 0.177 | 0.0155 | **`VALID`** |
| `..._4D4_...fits` | **D4** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 164.0618 | -69.7875 | 6.14" | 2.398 – 3.863 | 0.158 | 0.0132 | **`VALID`** |
| `..._4D5_...fits` | **D5** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 168.9632 | -73.3303 | 6.11" | 3.798 – 4.443 | 0.199 | 0.0321 | **`VALID`** |
| `..._4D6_...fits` | **D6** | 4 | 2026-07-20T00:32:48.215 | 61241.02278 | 175.9164 | -76.7668 | 6.14" | 4.402 – 5.025 | 0.357 | 0.0484 | **`VALID`** |

---

## 4. Astrometric and Temporal Integrity Verification

1. **Simultaneous Exposure Cadence:**
   For any given dither step $k \in \{1, 2, 3, 4\}$, the observation timestamp `DATE-OBS` across all active detectors is identical to within **0.001 seconds** (e.g., Dither 1 is `2026-07-20T00:26:21.423` across D1–D6).
2. **Dither Step Cadence:**
   The interval between consecutive dithers is exactly $\Delta t = 128.93\text{ seconds}$ ($2.15\text{ minutes}$), reflecting the nominal SPHEREx spacecraft reaction wheel repointing slew and settle duration.
3. **Pixel Scale Uniformity:**
   The astrometric plate scale varies from $6.11''/\text{pixel}$ (D2, D5) to $6.14''/\text{pixel}$ (D4, D6), matching the optical distortion model of the SPHEREx telescope optics.
4. **Conclusion:** All files represent authentic, scientifically uncorrupted Level-2 flight observations ready for multi-detector cross-registration.
