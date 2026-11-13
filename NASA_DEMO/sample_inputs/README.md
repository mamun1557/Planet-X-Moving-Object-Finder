# SPECTRA-X Sample Input Package — Provenance & Architecture Guide
**NASA Space Apps Challenge 2026** | **Pipeline Build:** `l2b-v27-2026-222`

This package provides a small, curated set of genuine SPHEREx mission data and pipeline products demonstrating the multimodal anomaly detection workflow of SPECTRA-X without requiring downloading the entire multi-gigabyte mission archive.

---

## 1. Directory Structure & Inventory

```text
NASA_DEMO/sample_inputs/
├── README.md                                          # This documentation guide
├── fits/                                              # Calibrated 2D FITS images
│   ├── level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits  # Genuine SPHEREx Level-2 FITS (Dither 1D1, 66.3 MB)
│   ├── aurora_template_D1_spx_base-2026-191.fits             # Instrumental aurora foreground template (48.9 KB)
│   └── shuttle_glow_template_D5_spx_base-2026-191.fits       # Spacecraft shuttle glow background template (48.9 KB)
├── spectra/                                           # 102-channel spectrophotometry vectors
│   ├── sample_assembled_spectra.csv                   # 100 genuine assembled SED vectors (870 KB)
│   └── independent_test_assembled_spectra_sample.csv  # 10 pilot demonstration candidate SEDs (88.5 KB)
└── catalog/                                           # Astrometric candidates & crossmatches
    ├── pointing_0003_candidates.csv                   # Full Pointing 0003 demonstration catalog (N=1,392, 700 KB)
    ├── pointing_0003_gaia_dr3_candidates.csv          # Gaia DR3 astrometric crossmatch catalog (342 KB)
    └── pointing_0003_allwise_candidates.csv           # AllWISE infrared crossmatch catalog (115 KB)
```

---

## 2. Sample File Provenance & Pipeline Mapping

### 2.1 Calibrated FITS Files (`fits/`)

1. **`level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits`**
   - **Original Path:** `data/spherex/qr3/level2/level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits`
   - **Size:** 66,297,600 bytes (66.3 MB)
   - **Dimensions:** $2048 \times 2048$ pixels (SPHEREx Detector 1 Array)
   - **Provenance:** Genuine SPHEREx Level-2 Calibrated Surface Brightness Product for Pointing 0003, Dither 1 (1D1).
   - **Pipeline Purpose:** Serves as the primary reference epoch for spatial anomaly screening via ASTROVISION V3 and astrometric differential imaging. Contains `IMAGE`, `VARIANCE`, and `FLAGS` HDUs.
   - **Comparison File:** Paired with Dither 4 (`level2_2026W30_1B_0003_4D1_spx_l2b-v27-2026-222.fits`, $\Delta t = 6.45\text{ min}$) to evaluate sub-pixel difference maps $\Delta I = E_2 - E_1$ and fail-closed temporal eligibility in CHRONOS-X.

2. **`aurora_template_D1_spx_base-2026-191.fits`**
   - **Original Path:** `data/spherex/qr3/templates/aurora_template_D1_spx_base-2026-191.fits`
   - **Size:** 48,960 bytes
   - **Pipeline Purpose:** Calibration spatial template representing auroral line emission contamination across low-Earth orbit geomagnetic crossings on Detector 1.

3. **`shuttle_glow_template_D5_spx_base-2026-191.fits`**
   - **Original Path:** `data/spherex/qr3/templates/shuttle_glow_template_D5_spx_base-2026-191.fits`
   - **Size:** 48,960 bytes
   - **Pipeline Purpose:** Spacecraft surface interaction / glow template used in the foreground subtraction stage for longer wavelength channels (Detector 5).

---

### 2.2 Spectrophotometric Datasets (`spectra/`)

1. **`sample_assembled_spectra.csv`**
   - **Original Path:** `data/processed/spectral_features/sample_assembled_spectra.csv`
   - **Size:** 870,105 bytes (100 rows)
   - **Channels:** Exactly 102 discrete wavelength channels spanning $0.75\,\mu\text{m}$ to $5.00\,\mu\text{m}$.
   - **Schema:** `source_id`, `ra`, `dec`, `wavelength`, `bandwidth`, `flux`, `uncertainty`, `detector_provenance`, `observation_provenance`, `valid_channel_mask`, `valid_channels_count`, `quality_summary`.
   - **Pipeline Purpose:** Pre-flight benchmark dataset used to evaluate the reconstruction fidelity of the frozen Masked Spectral Autoencoder (`spectra_masked_ae_v2.pt`).

2. **`independent_test_assembled_spectra_sample.csv`**
   - **Source:** Extracted from `data/processed/spectral_features/independent_test_assembled_spectra.csv`
   - **Size:** 88,540 bytes (10 curated rows)
   - **Key Source Included:** `SPX-J163.6309-69.4422` (the primary pilot demonstration candidate featured in Task 4.28B/C).
   - **Pipeline Purpose:** Feeds the live SED viewer in the interactive observatory, displaying observed fluxes, measurement uncertainties, channel masks, and neural reconstruction curves.

---

### 2.3 Astrometric & Crossmatch Catalogs (`catalog/`)

1. **`pointing_0003_candidates.csv`**
   - **Original Path:** `data/processed/candidates/pointing_0003_candidates.csv`
   - **Size:** 700,057 bytes (1,392 rows)
   - **Provenance:** Authoritative demonstration catalog evaluated across all 5 modules for SPHEREx Pointing 0003.
   - **Schema Attributes:** `candidate_id`, `ra`, `dec`, `observation_id`, `observation_time`, `module_name`, `anomaly_score`, `score_type`, `validity_status`, `evidence_summary`, `spectra_chi2`, `astrovision_peak_residual`, `chronos_significance_sigma`, `is_known_gaia_star`, `copilot_classification`.
   - **Pipeline Purpose:** Drives the Candidate Explorer table, pagination, search, and sorting.

2. **`pointing_0003_gaia_dr3_candidates.csv`**
   - **Original Path:** `data/external/gaia_dr3/pointing_0003_gaia_dr3_candidates.csv`
   - **Size:** 342,267 bytes
   - **Pipeline Purpose:** Provides high-precision Gaia DR3 astrometric reference positions, proper motions ($\mu_\alpha, \mu_\delta$), and parallax flags for MOTION-X celestial kinematics screening.

3. **`pointing_0003_allwise_candidates.csv`**
   - **Original Path:** `data/external/allwise/pointing_0003_allwise_candidates.csv`
   - **Size:** 115,658 bytes
   - **Pipeline Purpose:** Provides mid-infrared photometry ($W_1, W_2, W_3, W_4$) for cross-survey continuum consistency checks and Rayleigh-Jeans sidecar slope corroboration.

---

## 3. Scientific Integrity & Checksum Verification

All files in this package are direct bit-for-bit copies of the canonical pipeline data products. No mock data or artificial noise models were introduced.

```text
Algorithm : SHA-256
Catalog (1,392 Candidates):  3CD68C5EF7A9651EFEBF0A86E64FD711F634B0B9481DF9C9FD1A041E479FF239
Level-2 FITS (1D1):          5602AC1522F5FCEF50BCFFFE865E5E973B7B4B184BEFB582D0A4FA8E5191C36B
Sample Spectra (100 rows):   07EC99E442F99B0F9F3082BE47D4C617B50BA5400BC2E6B6858DAE2F54B009DA
```

