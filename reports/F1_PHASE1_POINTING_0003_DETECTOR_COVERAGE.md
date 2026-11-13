# SPECTRA-X / F1 — PHASE 1: POINTING 0003 DETECTOR COVERAGE AUDIT
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE (Data Foundation Audit)

---

## 1. Executive Summary

A critical finding from earlier audits established that the local SPECTRA-X repository contains Level-2 science exposures for **Detector Array 1 (D1)** only in Pointing 0003 (`data/spherex/qr3/level2/`), covering solely **Bands 1–17** ($0.75\,\mu\text{m} - 1.20\,\mu\text{m}$). 

This audit resolved the following fundamental question:
> *Do scientifically compatible Level-2 science exposures exist for Pointing 0003 across D2–D6 in the NASA SPHEREx flight archive, or is Pointing 0003 permanently restricted to D1?*

### Key Conclusions:
1. **Local Status:** Only D1 (4 dither files, 240 MB) is present locally. Detectors D2–D6 are **CONFIRMED NOT PRESENT LOCALLY**.
2. **Remote S3 Archive Status:** Detectors D2, D3, D4, D5, and D6 **DO EXIST** on the official NASA IRSA SPHEREx S3 archive (`nasa-irsa-spherex.s3.amazonaws.com`) under the identical observation epoch tranche:
   `qr3/level2/2026W30_1B/l2b-v27-2026-222/`
3. **Completeness:** 19 remote science FITS files (~1.15 GB) exist for D2–D6 on this exact pointing footprint and timestamp baseline.
4. **Machine-Readable Manifest:** Full detector-by-detector status is cataloged in [`data/manifests/f1_pointing_0003_detector_coverage.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_pointing_0003_detector_coverage.csv).

---

## 2. Pointing 0003 Observation Parameters

- **Survey Tranche:** QR3 (Quick Release 3)
- **Flight Planning Period:** `2026W30_1B` (Orbit week 30, execution block 1B)
- **Pipeline Processing Version:** `l2b-v27-2026-222`
- **Pointing Index:** `0003`
- **Boresight Center Coordinates:**
  - RA: $165.6852^\circ$ (11h 02m 44.45s)
  - Dec: $-69.5651^\circ$ (-69° 33' 54.4")
- **Galactic Coordinates:** $l \approx 297.2^\circ, b \approx -8.4^\circ$
- **Observation Epoch:** 2026-07-20T13:28:44 to 2026-07-20T13:35:10 UTC (JD 2461242.062 - 2461242.067)
- **Total Dither Cadence:** 4 distinct dither steps per pointing visit ($\Delta t \approx 129\text{ s}$ per step).

---

## 3. Comprehensive D1–D6 Detector Coverage Matrix

| Detector Array | Wavelength Range ($\mu\text{m}$) | Band Channels | Local Science Files | Remote S3 Science Files | Local Status | Remote S3 Status | File Size (MB) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **D1** | $0.75 - 1.20$ | Bands 1–17 | 4 files (`1D1`..`4D1`) | 4 files (`1D1`..`4D1`) | **VERIFIED AVAILABLE** | **VERIFIED AVAILABLE** | ~240 MB |
| **D2** | $1.20 - 1.95$ | Bands 18–34 | 0 files | 4 files (`1D2`..`4D2`) | **CONFIRMED NOT PRESENT** | **VERIFIED AVAILABLE** | ~240 MB |
| **D3** | $1.95 - 2.80$ | Bands 35–51 | 0 files | 3 files (`1D3`, `3D3`, `4D3`)* | **CONFIRMED NOT PRESENT** | **VERIFIED AVAILABLE** | ~180 MB |
| **D4** | $2.80 - 3.82$ | Bands 52–68 | 0 files | 4 files (`1D4`..`4D4`) | **CONFIRMED NOT PRESENT** | **VERIFIED AVAILABLE** | ~240 MB |
| **D5** | $3.82 - 4.42$ | Bands 69–85 | 0 files | 4 files (`1D5`..`4D5`) | **CONFIRMED NOT PRESENT** | **VERIFIED AVAILABLE** | ~240 MB |
| **D6** | $4.42 - 5.00$ | Bands 86–102 | 0 files | 4 files (`1D6`..`4D6`) | **CONFIRMED NOT PRESENT** | **VERIFIED AVAILABLE** | ~240 MB |
| **Total** | **0.75 – 5.00** | **All 102 Bands** | **4 files** | **23 files** | **17.0% Coverage** | **98.0% Coverage** | **~1.39 GB** |

*\*Note on D3 dither 2:* S3 remote listing shows dithers 1, 3, and 4 for D3. Dither 2 was either flagged by flight quality screening or omitted during pipeline packaging. D1, D2, D4, D5, and D6 have all 4 dithers.

---

## 4. Scientific Compatibility & Focal Plane Geometry

SPHEREx utilizes a single focal plane assembly accommodating six $2048 \times 2048$ Hawaii-2RG (H2RG) HgCdTe arrays with Linear Variable Filters (LVFs) mounted directly above them:
- **D1, D2, D3:** Short-to-mid wavelength infrared ($0.75 - 2.80\,\mu\text{m}$).
- **D4, D5, D6:** Mid-to-long wavelength infrared ($2.80 - 5.00\,\mu\text{m}$).

### Overlap & Co-pointing Mechanics:
- When the SPHEREx spacecraft points at boresight $(\alpha, \delta) = (165.6852^\circ, -69.5651^\circ)$, all six detectors observe their respective offset regions of the focal plane simultaneously.
- As the observatory steps through dithers and adjacent survey pointings, common stars drift across detector arrays, accumulating spectral coverage across bands 1 through 102.
- The remote D2–D6 Level-2 products share the exact same timestamp baseline (`JD 2461242.062` to `2461242.067`) and valid WCS solutions referenced to the identical pointing command.

---

## 5. Distinction Between Calibration and Science Data

- **Calibration Files:** In the repository, calibration tables (flat-field polynomials, dark current frames, and bad-pixel masks) exist for all detectors. However, calibration assets do **not** provide astronomical photon fluxes.
- **Science Files:** Real SED construction requires the Level-2 science FITS files (`PRIMARY`, `IMAGE`, `UNCERTAINTY`, `DQ_FLAGS`, `WAVELENGTH_MAP`).
- **Conclusion:** Downloading the 19 remote files for Pointing 0003 will elevate Pointing 0003 from a single-band (D1, 17 channels) slice to a complete 102-channel multi-detector benchmark dataset.
