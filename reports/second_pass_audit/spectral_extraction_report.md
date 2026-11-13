# SPECTRA-X: Spectral WCS and Spectral Extraction Audit Report

## 1. Executive Summary and Readiness Finding

**SCIENTIFIC READINESS STATUS FOR SPECTRA**: **`BASELINE TRAINED (ON SYNTHETIC PROXY DATA) / SCIENTIFIC VALIDATION PENDING`**.

### Critical Scientific Facts Verified:
1. **Level-2 Science Exposures Cover Exactly 1 Detector per File**: In the ingested 5.195 GB dataset:
   - All 16 QR2 Level-2 files cover **Detector 2** only (`DETECTOR = 2`, Band 2: 1.25–1.87 µm).
   - All 16 QR3 Level-2 files cover **Detector 1** only (`DETECTOR = 1`, Band 1: 0.75–1.25 µm).
   - **Zero Level-2 files exist for Detectors 3, 4, 5, or 6** in the current dataset.
2. **`WCS-WAVE` in HDU 6 is a Spatial Wavelength Coordinate Grid, NOT a Source Spectrum**:
   - In QR2, HDU 6 (`WCS-WAVE`) contains an 11x11 spatial array giving wavelength as a function of detector pixel position $(X, Y)$.
   - In QR3, HDU 6 (`WCS-WAVE`) contains a 9x9 spatial array giving wavelength as a function of detector pixel position $(X, Y)$.
   - Because SPHEREx uses Linear Variable Filters (LVF), each pixel column observes a distinct narrow bandpass. An isolated source on a single exposure yields only *one* monochromatic flux measurement, not a 102-channel SED.
3. **Assembling a Complete 102-Channel Spectrum Requires Multi-Detector Coverage**:
   - A celestial source must be observed across all 6 focal plane arrays (Detectors 1 to 6) as the satellite slews to accumulate flux measurements across all 102 spectral bands (0.75 to 5.0 µm).
   - Because our downloaded dataset lacks exposures for Detectors 3–6, **full 102-channel empirical spectral extraction is physically impossible from the current dataset alone**.
4. **Existing Checkpoint Provenance**:
   - Inspection of `models/spectra/train_spectra.py` confirms that the baseline model was trained using `generate_synthetic_spectra()` (procedurally generated continua with Gaussian emission/absorption lines and random noise).
   - The model architecture and PyTorch implementation are verified and functional, but the model has **never processed real SPHEREx-extracted 102-channel SEDs**.

## 2. Standalone Spectral Calibration Products Audit

| Calibration File | Type | Detector | Version | CWAVE | CBAND | Units | Notes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `data/spherex/qr2/calibration/spectral_wcs_D1_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 1 | UNKNOWN | No | No | um | Detector 1 spectral mapping |
| `data/spherex/qr2/calibration/spectral_wcs_D2_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 2 | UNKNOWN | No | No | um | Detector 2 spectral mapping |
| `data/spherex/qr2/calibration/spectral_wcs_D3_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 3 | UNKNOWN | No | No | um | Detector 3 spectral mapping |
| `data/spherex/qr2/calibration/spectral_wcs_D4_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 4 | UNKNOWN | No | No | um | Detector 4 spectral mapping |
| `data/spherex/qr2/calibration/spectral_wcs_D5_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 5 | UNKNOWN | No | No | um | Detector 5 spectral mapping |
| `data/spherex/qr2/calibration/spectral_wcs_D6_spx_cal-wcs-v4-2025-254.fits` | SPECTRAL_WCS | 6 | UNKNOWN | No | No | um | Detector 6 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D1_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 1 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 1 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D2_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 2 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 2 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D3_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 3 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 3 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D4_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 4 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 4 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D5_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 5 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 5 spectral mapping |
| `data/spherex/qr3/calibration/spectral_wcs_D6_spx_cal-swcs-v5-2026-191.fits` | SPECTRAL_WCS | 6 | 7.0.0b6.post2+g6b3a1a7 | No | No | um | Detector 6 spectral mapping |
| `data/spherex/qr3/calibration/spectral_channels_spx_cal-sch-v2-2026-229.fits` | SPECTRAL_CHANNELS | ALL | UNKNOWN | Yes | No | um | Contains 102 total spectral band definitions across detectors |

## 3. Level-2 Pointing Detector Coverage Audit

SPHEREx 102-channel spectrophotometry is partitioned across six focal plane arrays:
- **Band 1 (Detector 1)**: 0.75 – 1.25 µm (17 channels, R ≈ 41)
- **Band 2 (Detector 2)**: 1.25 – 1.87 µm (17 channels, R ≈ 41)
- **Band 3 (Detector 3)**: 1.87 – 2.80 µm (17 channels, R ≈ 41)
- **Band 4 (Detector 4)**: 2.80 – 3.82 µm (17 channels, R ≈ 35)
- **Band 5 (Detector 5)**: 3.82 – 4.42 µm (17 channels, R ≈ 110)
- **Band 6 (Detector 6)**: 4.42 – 5.00 µm (17 channels, R ≈ 130)

### Actual Pointing Coverage in Downloaded Data:
- Pointing `2025W17_4B_0001`: Detectors present = **2** (Missing: 1, 3, 4, 5, 6)
- Pointing `2025W17_4B_0002`: Detectors present = **2** (Missing: 1, 3, 4, 5, 6)
- Pointing `2025W17_4B_0004`: Detectors present = **2** (Missing: 1, 3, 4, 5, 6)
- Pointing `2025W17_4B_0005`: Detectors present = **2** (Missing: 1, 3, 4, 5, 6)
- Pointing `2025W17_4B_0006`: Detectors present = **2** (Missing: 1, 3, 4, 5, 6)
- Pointing `2026W30_1B_0001`: Detectors present = **1** (Missing: 2, 3, 4, 5, 6)
- Pointing `2026W30_1B_0002`: Detectors present = **1** (Missing: 2, 3, 4, 5, 6)
- Pointing `2026W30_1B_0003`: Detectors present = **1** (Missing: 2, 3, 4, 5, 6)
- Pointing `2026W30_1B_0004`: Detectors present = **1** (Missing: 2, 3, 4, 5, 6)

## 4. Audit of Existing SPECTRA Implementation

- **Model Class**: `SpectrophotometricAutoencoder` in `models/spectra/model.py`.
- **Input Shape**: `(Batch, 1, 102)`.
- **Training Data Source**: Procedural synthetic generator (`generate_synthetic_spectra`). No aperture photometry is performed on FITS arrays.
- **Aperture Photometry Pipeline**: Currently unbuilt. The project does not yet possess code to extract source coordinates, perform circular aperture photometry, subtract local annulus background, or query `WCS-WAVE` for effective wavelength.

## 5. Comparison with Official IRSA SPHEREx Spectrophotometry Tool

The official IRSA SPHEREx Spectrophotometry Tool produces SED tables with schema:
`[RA, DEC, OBSID, DETECTOR, WAVELENGTH, BANDWIDTH, FLUX, FLUX_ERR, VARIANCE, FLAGS, DATE-OBS]`.

### Scientific Reasons Exact Comparison Cannot Be Executed Locally Today:
1. **Archive Coverage Gap**: IRSA's tool queries the entire all-sky Level-2 archive to collect the 100+ individual exposures covering a given target across all dithers and detectors. Locally, we have isolated pointings with only 1 detector per pointing.
2. **Missing Photometry Engine**: A local aperture extraction script (`extract_sed.py`) needs to be implemented using `photutils` and the standalone `spectral_wcs_D*.fits` tables.

## 6. Corrected Scientific Rule and Action Plan

1. **Status Rule**: SPECTRA is strictly marked **`BASELINE TRAINED (ON SYNTHETIC PROXY DATA)`**. It is **NOT** ready for real-world anomaly discovery or claims of detecting PAHs, water ice, or CO2 absorption.
2. **Action Plan for Phase 2**: Build an extraction pipeline using `photutils` and the standalone calibration products to extract monochromatic fluxes from available D1 and D2 images, and acquire coordinated D1–D6 sets when the download budget is expanded.
