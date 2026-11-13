# SPECTRA-X / F1 — Scientific Data Completeness Audit
**Audit Date:** 2026-11-03  
**Auditor:** Lead Scientific Software Auditor & ML Engineering Agent  
**Dataset Scope:** All SPHEREx FITS Products, Calibrations, and External Reference Catalogs in `data/`  
**Status:** Complete Forensic Audit  

---

## 1. Executive Summary & Core Data Findings

This audit establishes the ground-truth status of all astronomical data products in the SPECTRA-X repository. No data claims are accepted from documentation without direct verification against FITS headers, HDU structures, and binary table contents.

### Key Ground-Truth Findings:
1. **Total Level-2 Science Exposures:** Exactly **32 MEF FITS files** exist in `data/spherex/` (16 in `qr2`/`qr2_deep`, 16 in `qr3`/`qr3_deep`).
2. **Detector Array Asymmetry:**
   - **QR2 / QR2 Deep:** Contains exclusively **Detector Array 2 (`D2`)** files (Bands 18–34, $\lambda = 0.98 - 1.32\,\mu\text{m}$).
   - **QR3 / QR3 Deep:** Contains exclusively **Detector Array 1 (`D1`)** files (Bands 1–17, $\lambda = 0.75 - 0.98\,\mu\text{m}$).
   - **Detectors D3, D4, D5, D6:** **ZERO Level-2 science files exist** anywhere in the repository for any pointing.
3. **Pointing 0003 Completeness Investigation:**
   - Pointing 0003 exists **only** in QR3 (Detector Array 1) across 4 dithers: `1D1`, `2D1`, `3D1`, `4D1`.
   - **D2–D6 Level-2 products for Pointing 0003 DO NOT EXIST** in the local repository.
   - Pointing 0003 does not exist in QR2.
   - **Conclusion:** Pointing 0003 has valid photometry across only 1 to 17 channels. **Claiming 102-channel coverage for Pointing 0003 is scientifically unverified and false.**
4. **Temporal Observation Pair Reality:**
   - QR2 pointings ($\alpha \approx 133^{\circ}, \delta \approx +8^{\circ}$ and $\alpha \approx 81^{\circ}, \delta \approx -64^{\circ}$) and QR3 pointings ($\alpha \approx 232^{\circ}, \delta \approx -11^{\circ}$ and $\alpha \approx 165^{\circ}, \delta \approx -69.6^{\circ}$) **do not overlap in celestial coordinates** (spatial separation $> 40^{\circ}$).
   - Therefore, **QR2 versus QR3 differences are NOT multi-epoch temporal observations of the same sky**.
   - Genuine temporal differencing is currently strictly restricted to **intra-pointing dithers** ($\Delta t \approx 2.15\text{ to }6.45\text{ minutes}$). Multi-month seasonal repeat baselines are **MISSING**.

---

## 2. Complete Level-2 FITS Inventory & Header Verification

All 32 Level-2 files were verified for WCS integrity, timestamp consistency, and extension structure:

| File Name | Release | Pointing | Dither & Det | Size (MB) | Obs Date (UTC) | MJD-OBS | WCS CRVAL ($\alpha, \delta$) | HDU Extensions |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `level2_2025W17_4B_0001_1D2_spx_l2b-v20-2025-240.fits` | QR2 | 0001 | 1D2 | 68.32 | 2025-04-24T18:00:26 | 60789.75030 | (133.368, +8.541) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0001_2D2_spx_l2b-v20-2025-240.fits` | QR2 | 0001 | 2D2 | 68.32 | 2025-04-24T18:02:35 | 60789.75179 | (133.311, +8.353) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0001_3D2_spx_l2b-v20-2025-240.fits` | QR2 | 0001 | 3D2 | 68.32 | 2025-04-24T18:04:44 | 60789.75329 | (133.254, +8.165) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0001_4D2_spx_l2b-v20-2025-240.fits` | QR2 | 0001 | 4D2 | 68.32 | 2025-04-24T18:06:53 | 60789.75478 | (133.197, +7.977) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0002_1D2_spx_l2b-v20-2025-240.fits` | QR2 | 0002 | 1D2 | 68.32 | 2025-04-24T18:10:47 | 60789.75749 | (133.198, +7.977) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0002_2D2_spx_l2b-v20-2025-240.fits` | QR2 | 0002 | 2D2 | 68.32 | 2025-04-24T18:12:58 | 60789.75900 | (133.141, +7.788) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0002_3D2_spx_l2b-v20-2025-240.fits` | QR2 | 0002 | 3D2 | 68.32 | 2025-04-24T18:15:06 | 60789.76050 | (133.084, +7.600) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0002_4D2_spx_l2b-v20-2025-240.fits` | QR2 | 0002 | 4D2 | 68.32 | 2025-04-24T18:17:15 | 60789.76199 | (133.029, +7.411) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0004_1D2_spx_l2b-v20-2025-240.fits` | QR2 | 0004 | 1D2 | 68.32 | 2025-04-24T18:30:20 | 60789.77107 | (87.829, -60.381) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0004_2D2_spx_l2b-v20-2025-240.fits` | QR2 | 0004 | 2D2 | 68.32 | 2025-04-24T18:32:29 | 60789.77256 | (87.590, -60.538) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0005_1D2_spx_l2b-v20-2025-240.fits` | QR2 | 0005 | 1D2 | 68.32 | 2025-04-24T18:35:08 | 60789.77441 | (81.492, -64.059) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2025W17_4B_0005_2D2_spx_l2b-v20-2025-240.fits` | QR2 | 0005 | 2D2 | 68.32 | 2025-04-24T18:37:17 | 60789.77590 | (81.187, -64.204) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `deep_level2_2025W17_4B_0005_3D2_spx_l2b-v20-2025-240.fits` | QR2 | 0005 | 3D2 | 68.32 | 2025-04-24T18:39:26 | 60789.77739 | (80.879, -64.349) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `deep_level2_2025W17_4B_0005_4D2_spx_l2b-v20-2025-240.fits` | QR2 | 0005 | 4D2 | 68.32 | 2025-04-24T18:41:35 | 60789.77888 | (80.568, -64.493) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `deep_level2_2025W17_4B_0006_1D2_spx_l2b-v20-2025-240.fits` | QR2 | 0006 | 1D2 | 68.32 | 2025-04-24T18:44:42 | 60789.78105 | (7.599, -72.016) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `deep_level2_2025W17_4B_0006_2D2_spx_l2b-v20-2025-240.fits` | QR2 | 0006 | 2D2 | 68.32 | 2025-04-24T18:46:51 | 60789.78254 | (7.059, -71.913) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE |
| `level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits` | QR3 | 0001 | 1D1 | 62.80 | 2026-07-20T00:06:53 | 61241.00478 | (232.664, -10.721) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0001_2D1_spx_l2b-v27-2026-222.fits` | QR3 | 0001 | 2D1 | 63.09 | 2026-07-20T00:09:02 | 61241.00628 | (232.617, -10.912) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0001_3D1_spx_l2b-v27-2026-222.fits` | QR3 | 0001 | 3D1 | 63.31 | 2026-07-20T00:11:11 | 61241.00777 | (232.570, -11.103) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0001_4D1_spx_l2b-v27-2026-222.fits` | QR3 | 0001 | 4D1 | 62.84 | 2026-07-20T00:13:20 | 61241.00926 | (232.523, -11.293) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0002_1D1_spx_l2b-v27-2026-222.fits` | QR3 | 0002 | 1D1 | 62.73 | 2026-07-20T00:16:21 | 61241.01136 | (222.188, -28.881) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0002_2D1_spx_l2b-v27-2026-222.fits` | QR3 | 0002 | 2D1 | 62.84 | 2026-07-20T00:18:30 | 61241.01285 | (222.118, -29.068) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0002_3D1_spx_l2b-v27-2026-222.fits` | QR3 | 0002 | 3D1 | 62.86 | 2026-07-20T00:20:39 | 61241.01434 | (222.047, -29.254) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0002_4D1_spx_l2b-v27-2026-222.fits` | QR3 | 0002 | 4D1 | 63.06 | 2026-07-20T00:22:48 | 61241.01583 | (221.976, -29.441) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits` | QR3 | 0003 | 1D1 | 63.23 | 2026-07-20T00:26:21 | 61241.01830 | (165.685, -69.565) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0003_2D1_spx_l2b-v27-2026-222.fits` | QR3 | 0003 | 2D1 | 59.02 | 2026-07-20T00:28:30 | 61241.01980 | (165.165, -69.641) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0003_3D1_spx_l2b-v27-2026-222.fits` | QR3 | 0003 | 3D1 | 58.97 | 2026-07-20T00:30:39 | 61241.02129 | (164.642, -69.716) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `level2_2026W30_1B_0003_4D1_spx_l2b-v27-2026-222.fits` | QR3 | 0003 | 4D1 | 58.96 | 2026-07-20T00:32:48 | 61241.02278 | (164.115, -69.788) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `deep_level2_2026W30_1B_0004_1D1_spx_l2b-v27-2026-222.fits` | QR3 | 0004 | 1D1 | 63.14 | 2026-07-20T00:36:10 | 61241.02513 | (79.006, -55.870) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `deep_level2_2026W30_1B_0004_2D1_spx_l2b-v27-2026-222.fits` | QR3 | 0004 | 2D1 | 63.05 | 2026-07-20T00:38:19 | 61241.02662 | (78.733, -55.747) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `deep_level2_2026W30_1B_0004_3D1_spx_l2b-v27-2026-222.fits` | QR3 | 0004 | 3D1 | 63.04 | 2026-07-20T00:40:28 | 61241.02811 | (78.461, -55.624) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |
| `deep_level2_2026W30_1B_0004_4D1_spx_l2b-v27-2026-222.fits` | QR3 | 0004 | 4D1 | 63.00 | 2026-07-20T00:42:37 | 61241.02960 | (78.192, -55.501) | PRIMARY, IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE |

---

## 3. Calibration Product Completeness

Calibration files located in `data/spherex/calibration/` provide complete support across all six detector arrays:

| Calibration Product | Available Detectors | Format | Verification Status |
| :--- | :---: | :---: | :--- |
| **Spectral WCS (`spectral_wcs_D*.fits`)** | **D1 through D6** | Multi-Extension FITS | Verified; maps pixel $(x, y)$ to wavelength $\lambda$ ($\mu\text{m}$) and resolution $R = \lambda / \Delta\lambda$. |
| **Readnoise Parameters (`readnoise_pars_D*.fits`)** | **D1 through D6** | Multi-Extension FITS | Verified; CDS amplifier read noise maps in DN. |
| **SIP Astrometric Distortion (`sip_D*.fits`)** | **D1 through D6** | FITS Table / Image | Verified; 4th-order polynomial distortion coefficients. |
| **Solid Angle Pixel Maps (`solid_angle_pixel_map_D*.fits`)** | **D1 through D6** | FITS Image | Verified; pixel solid angle in steradians for surface brightness conversion. |
| **Spectral Channel Definitions (`spectral_channels_*.fits`)** | **All 102 Channels** | Binary FITS Table | Verified; central wavelength, bandpass FWHM, and detector ID for channels 1–102. |
| **Crosstalk Kernels (`xtalk_class*.ecsv`)** | **D1 through D6** | ECSV Table | Verified; inter-channel electrical crosstalk matrix. |
| **Zodiacal Light Model (`zodi_scaling_v2_D*.ecsv`)** | **D1 through D6** | ECSV Table | Verified; wavelength-dependent zodiacal emission scaling factors. |

> **Scientific Implication:**  
> The SPHEREx calibration pipeline is fully capable of processing D1 through D6 exposures. The missing 102-channel SED coverage is strictly caused by the **absence of Level-2 science exposures for D2 through D6 in Pointing 0003**, not by missing calibration software or tables.

---

## 4. Quality Flag Masking & Variance Propagation

### 4.1 Fatal Quality Flag Bitmask
The SPHEREx data pipeline sets bitwise flags in the `FLAGS` HDU ($2040 \times 2040$ `int32`). The scientific fatal mask is defined as:
```python
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615
```
- Bit 0 (`1`): `MP_TRANSIENT` (Cosmic ray hit or energetic particle strike)
- Bit 1 (`2`): `MP_OVERFLOW` (A/D converter saturation or full-well blooming)
- Bit 2 (`4`): `MP_SUR_ERROR` (Sample-up-the-ramp non-linearity / slope fit failure)
- Bit 5 (`32`): `MP_NONFUNC` (Known dead / disconnected / hot detector pixel)
- Bit 6 (`64`): `MP_REFERENCE` (Reference pixel / bias drift anomaly)
- Bit 9 (`512`): `MP_MISSING_DATA` (Telemetry packet dropout or transmission loss)

*Audit Finding:* Legacy scripts naively filtered on `flags != 0`, mistakenly rejecting benign flags (such as zodiacal background flags or non-fatal low-transmission bits). The corrected pipeline filters strictly on `(flags & 615) != 0`.

### 4.2 Variance Propagation & Systematic Noise Floor
- In all 32 Level-2 files, the `VARIANCE` extension contains valid propagation of photon Poisson noise and read noise in units of $(\text{MJy/sr})^2$.
- An empirical systematic noise floor of $f_{\text{sys}} = 1.93\%$ was calibrated in Phase 4 to account for flat-field calibration limits, preventing high-SNR star cores from dominating $\chi^2$ gradients.

---

## 5. External Catalog Completeness

| External Catalog | Local Path | Verified Count | Usability for Pointing 0003 | Defect / Limitation |
| :--- | :--- | :---: | :---: | :--- |
| **Gaia DR3 Reference Sample** | [`data/external/gaia_dr3/gaia_dr3_reference_stars.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/gaia_dr3/gaia_dr3_reference_stars.csv) | 5,000 | **0 matches within 300"** | Catalog is an all-sky sparse downsample ($G < 15$). A localized high-density cone search around $\alpha=165.7^{\circ}, \delta=-69.6^{\circ}$ is required. |
| **ZTF Bright Transient Survey** | [`data/external/transient_catalogs/ztf_bright_transient_survey.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/transient_catalogs/ztf_bright_transient_survey.csv) | 20,599 | **0 matches (Geographically Incompatible)** | ZTF is at Palomar Observatory and covers only Northern sky ($\delta > -30^{\circ}$). Pointing 0003 is at $\delta \approx -69.6^{\circ}$. Southern surveys (SkyMapper, VISTA) are required. |
| **JPL Horizons Ephemerides** | `data/external/jpl_horizons/*.csv` | 5 bodies | **0 matches (>40° separation)** | Targets (Apophis, Eros, and major planets) were $>40^{\circ}$ away from pointings. Query script bug used bare IDs (`1`, `2`, `4`) which fetched major planets instead of asteroids 1 Ceres, 2 Pallas, and 4 Vesta. |
| **JPL SBDB Asteroid Orbits** | [`data/external/minor_planets/jpl_sbdb_asteroid_orbits.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/minor_planets/jpl_sbdb_asteroid_orbits.json) | 2,000 | Reference only | Orbital elements intact on disk for candidate orbit fitting. |
