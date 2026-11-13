# SPECTRA-X: Planet X — Moving Object Finder
### *A Human-AI Co-Pilot for Exploring the Changing Infrared Sky*

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61dafb.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-5.4-purple.svg)](https://vitejs.dev/)
[![NASA Space Apps Challenge](https://img.shields.io/badge/NASA%20Space%20Apps-2026-critical.svg)](https://www.spaceappschallenge.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Project:** Planet X: Moving Object Finder  
**Platform:** SPECTRA-X Interactive Observatory  
**Team:** VU_VioNux (Rajshahi, Bangladesh)  
**Event:** NASA Space Apps Challenge  

---

## 1. Project Overview

**SPECTRA-X** is an input-driven, general-purpose astronomical research workstation designed to detect moving solar system bodies, transients, and spectral anomalies across multi-epoch infrared sky surveys.

Unlike traditional precomputed dashboards that display static catalog detections, SPECTRA-X operates as a **clean, input-driven scientific workspace**. Every analysis session starts in an `EMPTY_WORKSPACE` state. Researchers, students, and citizen scientists supply their own calibrated astronomical observations, validate file headers, evaluate multi-module algorithm eligibility, execute kinematics calculations, and inspect verified evidence.

---

## 2. Five Scientific Analysis Modules

SPECTRA-X integrates five specialized, frozen scientific inference engines:

| Module | Full Name | Scientific Method & Role | Input Requirements |
|:---|:---|:---|:---|
| **ASTROVISION** | Spatial Morphology Anomaly Engine | Deep residual spatial anomaly detection evaluating optical point spread function (ePSF) morphology, diffraction spikes, and pixel gradients against calibrated detector noise floors. | Calibrated 2D/3D FITS raster with valid celestial WCS. |
| **SPECTRA** | 102-Channel Infrared Spectrophotometry | Masked autoencoder and continuum reconstruction evaluating 102 narrow spectral channels ($0.75 - 5.00\,\mu\text{m}$) to detect unusual emission/absorption lines and thermal excesses. | 102-channel spectrophotometric flux vector. |
| **CHRONOS-X** | Temporal Differencing & Artifact Rejection | Calibrated spatial frame subtraction with statistical significance residual mapping ($S = \Delta I / \sqrt{\sigma_1^2 + \sigma_2^2}$) and artifact rejection. | $\ge 2$ aligned observations with valid timestamps. |
| **MOTION-X** | Astrometric & Kinematics Motion Engine | High-precision spherical coordinate astrometry, Haversine angular separation, motion rates ($\text{arcsec/hour}$, $\text{arcsec/day}$), Position Angle ($PA^\circ$), and formal coordinate uncertainty propagation. | $\ge 2$ epochs with celestial coordinates ($RA, Dec$) and timestamps ($MJD$). |
| **FUSION-X** | Heuristic Multi-Evidence Integration | Multi-channel evidence ranking that integrates available module outputs into a prioritized investigation triage index. *(Heuristic ranking system; NOT a Bayesian posterior probability).* | Upstream module confidence vectors. |

---

## 3. Core Architecture: Input-Driven & Session-Isolated

- **Zero Preloaded Bias:** Application starts with zero preloaded candidates, no precomputed anomaly scores, and no historical reviews.
- **Cryptographic Session Isolation:** Every browser instance is provisioned with an isolated UUID4 token. Temporary uploads and analysis state reside in ephemeral scratch storage (`scratch/sessions/<session_id>/`) with a 2-hour TTL.
- **Fail-Closed Dither Safeguard:** For temporal separations $\Delta t < 1.0\text{ day}$, the motion engine triggers:
  ```text
  INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY
  ```
  Measured displacements are explicitly classified as spacecraft/instrument optical dither registration diagnostics, **never** as confirmed heliocentric moving objects.
- **Multi-Epoch Baseline Qualification:** Separations $\Delta t \ge 1.0\text{ day}$ qualify for:
  ```text
  TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION
  ```

---

## 4. Supported Data Formats

1. **FITS (`.fits`, `.fit`, `.fts`):** 2D/3D Multi-Extension FITS files containing calibrated science arrays (`SCI`), variance arrays (`VAR`), and data quality flags (`FLAGS`) with WCS astrometric headers (`CRVAL`, `CRPIX`, `CDELT`/`CD`/`PC`).
2. **Astrometric Catalogs (`.csv`):** Tabular catalogs containing `RA` and `Dec` (degrees, $J2000$), observation timestamps (`DATE-OBS`, `MJD-OBS`), and optional 102-channel flux columns.
3. **Observation Epochs (`.json`):** Structured multi-epoch observation vectors with coordinate uncertainties and photometric channels.

---

## 5. Quickstart & Installation

### Prerequisites
- **Python:** 3.12 or higher
- **Node.js:** v18 or higher (for frontend development/build)
- **Git**

### Installation

```bash
# 1. Clone repository
git clone https://github.com/nextlevelbuilder/SPECTRA-X-Planet-X-Moving-Object-Finder.git
cd SPECTRA-X-Planet-X-Moving-Object-Finder

# 2. Set up Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Build or serve the frontend (Optional if using pre-built dist)
cd frontend
npm install
npm run build
cd ..
```

### Launching the Observatory

```bash
# Launch the integrated Python HTTP server & Observatory workspace:
python observatory/app.py --port 8080
```
Open your browser at `http://localhost:8080` to access the interactive workspace.

---

## 6. Optional Personal Test Dataset

For testing and demonstration without external data, an optional pre-curated test dataset is available:
- **Package Archive:** `artifacts/downloadable_packages/SPECTRA-X-Personal-Test-Data.zip` (**9.53 MB**)
- **Contents (50 Pairs / 100 Samples):**
  - **25 REAL_INTRA_VISIT Pairs (50 samples):** Calibrated sub-pixel cutouts from SPHEREx Level-2 flight observations ($0.75 - 5.00\,\mu\text{m}$, $\Delta t < 15\text{ min}$).
  - **25 SYNTHETIC_ENGINEERING_TEST Pairs (50 samples):** Deterministic simulations (MBA, NEO, KBO, RA wraparound across $0^\circ/360^\circ$) with known ground-truth motion vectors.
- **Strict Quarantine:** Real flight observations never expose synthetic vectors; synthetic data is explicitly tagged `SYNTHETIC_ENGINEERING_TEST — NOT REAL SPHEREX OBSERVATION`.
- **Runtime Decoupling:** The dataset is strictly optional and is **never** preloaded on startup.

---

## 7. Verification & Scientific Integrity

- **Automated Test Suite:** **362 / 362 passing tests** (`pytest tests/`).
- **Bitwise Asset Protection:** Model weights and threshold tables remain 100% bitwise immutable:
  - `astrovision_spatial_v3.pt`: `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99`
  - `spectra_masked_ae_v2.pt`: `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938`
  - `spectra_v2_provisional_thresholds_v1.json`: `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848`
- **Scientific Caveat:** Software engineering, session isolation, and kinematics calculation are 100% verified. Real astronomical moving-object validation remains pending future long-baseline ($\Delta t \ge 1.0\text{ day}$) SPHEREx multi-visit survey releases.

---

## 8. Data Provenance & Acknowledgements

- **NASA Science Mission Directorate** and **IPAC at Caltech** for open SPHEREx survey releases and Level-2 products.
- **European Space Agency (ESA)** for the Gaia Data Release 3 (DR3) astrometric reference catalogue.
- **Astropy Project** for standard coordinate transformations and FITS WCS routines.
- Built by **Team VU_VioNux (Rajshahi, Bangladesh)** for the **NASA Space Apps Challenge**.

---

## 9. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
