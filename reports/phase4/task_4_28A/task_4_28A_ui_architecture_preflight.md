# SPECTRA-X / F1 — Phase 4, Task 4.28A
# Minimal Interactive Observatory MVP — UI Architecture Preflight Report

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** Windows 11, Python 3.12.10, `.venv_validation` (CUDA: NVIDIA GeForce RTX 5060)  
**Parent Task:** Phase 4, Task 4.27 Final Freeze Audit  
**Audit Date:** November 9, 2026  
**Freeze Deadline:** November 10, 2026  
**Task Type:** STRICT READ-ONLY ARCHITECTURE & IMPLEMENTATION PREFLIGHT  
**Final Verdict:** **`UI_ARCHITECTURE_READY_WITH_LIMITATIONS`**

---

## 1. Executive Summary

In response to the Phase 4, Task 4.27 Final Freeze Audit finding—which confirmed that while the machine learning backend and scientific pipeline are fully integrated and verified (309 passing tests, 100% pristine checkpoints), the user-facing interactive demonstration layer is missing—this preflight audit establishes a minimal, zero-dependency UI architecture for the **SPECTRA-X Interactive Observatory MVP**.

```
====================================================================================================
                        TASK 4.28A UI ARCHITECTURE PREFLIGHT DASHBOARD                              
====================================================================================================
  Preflight Mode:                                    STRICT READ-ONLY (Zero Code/Asset Mutation)
  Protected Checkpoint Integrity:                    100% PRISTINE (ASTROVISION V3 & SPECTRA V2)
  Protected Threshold Integrity:                     100% PRISTINE (spectra_v2_provisional_thresholds)
  Evaluated UI Frameworks:                           Streamlit, Gradio, Native Python HTTP (stdlib)
  Installed Package Audit:                           Streamlit/Gradio/FastAPI NOT INSTALLED
  Recommended UI Architecture:                       Native ThreadingHTTPServer + Jinja2 + HTML5/JS
  External Package Installation Required:            0 NEW PACKAGES (100% Freeze-Compliant)
  Backend Astronomical Data Availability:            100% READY (1,392 Candidates, 32 Level-2 FITS)
  Callable Production Model Interfaces:              VERIFIED (AstroVision, Spectra, Chronos, Fusion)
----------------------------------------------------------------------------------------------------
  PREFLIGHT ARCHITECTURAL VERDICT:                   UI_ARCHITECTURE_READY_WITH_LIMITATIONS
  NEXT IMPLEMENTATION TASK:                          TASK 4.28B (Controlled MVP Implementation)
====================================================================================================
```

---

## 2. Environment & Framework Feasibility Audit

An exhaustive package audit was performed in the active `.venv_validation` environment to evaluate the feasibility of candidate web frameworks without installing new packages:

| Candidate Framework | Installed in `.venv_validation`? | Version Detected | Feasibility for Zero-Install Freeze | Assessment & Integration Risk |
| :--- | :---: | :---: | :---: | :--- |
| **Streamlit** | **NO** | `NOT_INSTALLED` | **INCOMPATIBLE** | Requires pip installation of 30+ dependencies (`tornado`, `altair`, `pyarrow`). Reruns full script on every interaction, causing significant stuttering during stateful FITS blink loops. |
| **Gradio** | **NO** | `NOT_INSTALLED` | **INCOMPATIBLE** | Requires pip installation of 25+ dependencies (`fastapi`, `uvicorn`, `gradio_client`). Lacks native astronomical FITS canvas and synchronized dual-panel blink controls. |
| **FastAPI / Uvicorn** | **NO** | `NOT_INSTALLED` | **INCOMPATIBLE** | Requires pip installation of `fastapi`, `uvicorn`, `starlette`, `pydantic`. |
| **Native Python `http.server` + Jinja2** | **YES** | Python 3.12 stdlib<br/>`jinja2` 3.1.6 | **100% COMPATIBLE** | **RECOMMENDED.** Requires **ZERO new package installations**. Built-in `ThreadingHTTPServer` handles asynchronous local REST API requests; `jinja2` provides robust HTML templating; local client-side vanilla JavaScript executes smooth 60 FPS optical blinking and canvas rendering. |

### Available Core Libraries in `.venv_validation`
- **Scientific & Astronomical:** `astropy` (8.0.2), `scipy` (1.18.1), `numpy` (2.5.4), `pandas` (3.1.1), `photutils` (3.1.1)
- **Machine Learning & Image Processing:** `torch` (2.15.0+cu132), `torchvision` (0.29.2+cu132), `pillow` (13.0.0), `matplotlib` (3.11.2)
- **Templating & Serialization:** `jinja2` (3.1.6), `MarkupSafe` (3.0.3), `PyYAML` (6.0.3), Python standard library (`json`, `dataclasses`, `http.server`, `urllib`)

### Definitive Framework Recommendation
**Native Python Multi-Threaded HTTP Server (`http.server.ThreadingHTTPServer`) with Jinja2 Templating and an HTML5/CSS3/Vanilla JS Single-Page Application.**
- **Zero Package Installations:** Runs directly on the frozen Python 3.12 runtime without modifying environment state.
- **Zero Checkpoint/Model Risk:** Operates strictly as an external presentation sidecar that imports read-only model inference and data provider functions.
- **High Performance:** Client-side JavaScript handles real-time optical blink toggling (1–4 Hz, slider, step) smoothly without round-trip server latency.

---

## 3. Production Interfaces Available for Reuse

The preflight audit identified the exact production interfaces and functions that the UI layer will invoke without requiring any modifications to production codebase:

```
+------------------------------------------------------------------------------------+
|                                    UI LAYER                                        |
|         (Single-Page App: Celestial View, Blink Comparator, Spectrum, Review)      |
+-----------------------------------------+------------------------------------------+
                                          | REST API (JSON / Base64 Cutouts)
+-----------------------------------------v------------------------------------------+
|                       observatory/data_provider.py                                 |
+-------------------+--------------------+--------------------+----------------------+
                    |                    |                    |
+-------------------v--+ +---------------v--+ +---------------v--+ +------------------v--+
|     ASTROVISION      | |     SPECTRA      | |    CHRONOS-X      | |     FUSION-X       |
| models/astrovision/  | | models/spectra/  | | models/chronos_x/ | | models/fusion/     |
|   model_v3.py        | |   train_masked_  | |   model.py        | |   fusion_engine.py |
| dynamic_thresholds.py| |     spectra.py   | | subpixel_reg.py   | | candidate_schema.py|
+----------------------+ +------------------+ +-------------------+ +--------------------+
```

| Subsystem | Existing Production File | Callable Function / Class | Input Format | Output Format | Modification Needed? |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **Catalog & Pointings** | `scripts/inspect_fits.py` | `find_temporal_pairs(df)` / `manifests/fits_validation_catalog.csv` | Pointing ID / CSV query | Dict of pointing metadata, CRVAL1/2, MJD, FITS paths | **NONE** |
| **Candidate Ingestion** | `data/processed/candidates/` | `pointing_0003_candidates.csv` (1,392 precomputed rows) | Filter parameters (`validity_status`, min score) | Structured Pandas DataFrame / JSON records | **NONE** |
| **FITS Cutout & WCS** | `astropy.io.fits`, `astropy.wcs.WCS` | `fits.open()`, `WCS.all_world2pix()` | FITS path, RA, Dec, cutout size (e.g. 128x128) | 2D NumPy array (`float32`), pixel coordinates | **NONE** |
| **Sub-Pixel Registration** | `models/chronos_x/subpixel_registration.py` | `register_subpixel_fourier(ref, tgt)` | Two 2D NumPy cutout arrays | Shift vector $(dy, dx)$, aligned target array, correlation | **NONE** |
| **Temporal Differencing** | `models/chronos_x/model.py` | `ChronosTemporalDifferencer.align_and_difference(...)` | Two image arrays, headers, variances, flags | `difference_map`, `significance_map`, dipoles count | **NONE** |
| **Temporal Eligibility** | `models/chronos_x/temporal_eligibility.py` | `evaluate_pair_temporal_eligibility(obs1, obs2)` | Two observation metadata dicts | `TemporalEligibilityResult` (`status`, `is_dither`) | **NONE** |
| **102-Band Spectrum** | `data/processed/spectral_features/` | `independent_test_assembled_spectra.csv` | Source ID / Candidate ID | 102-channel observed flux, variance, valid mask | **NONE** |
| **Model Reconstruction** | `models/spectra/train_masked_spectra.py` | `MaskedSpectralAutoencoder.forward(flux, mask)` | PyTorch tensor `[1, 102]` flux, `[1, 102]` mask | Reconstructed SED tensor `[1, 102]`, masked $\chi^2$ | **NONE** |
| **Infrared Excess** | `spectra_engine/continuum_sidecar_engine.py` | `ContinuumSidecarEngine.evaluate_continuum(...)` | Spectral record, Gaia/CatWISE photometry | Rayleigh-Jeans baseline, IR excess significance | **NONE** |
| **Multimodal Synthesis** | `models/fusion/fusion_engine.py` | `FusionEngine.evaluate_source(...)` | Multimodal metrics, quality flags, astrometry | `CandidateRecord` (`HEURISTIC_PRIORITY_SCORE`) | **NONE** |
| **Schema & Export** | `models/common/candidate_schema.py` | `CandidateRecord.to_dict()` / `.to_json()` | Candidate parameters | Validated dictionary / JSON export string | **NONE** |

---

## 4. UI Feature Feasibility Matrix

| UI Feature Component | Existing Backend Functionality | Missing Functionality | Proposed Lightweight Implementation | Feasibility |
| :--- | :--- | :--- | :--- | :---: |
| **1. Observatory Overview** | 32 Level-2 FITS files in `data/spherex/` with verified WCS, CRVAL, timestamps. | Interactive sky projection canvas. | Pointing selector dropdown with static pointing footprint metadata, observation coordinates, and detector grid map. | **HIGH** |
| **2. Coordinate & Candidate Explorer** | 1,392 precomputed candidate rows in `pointing_0003_candidates.csv`. | Interactive search datatable with faceted sorting. | Responsive HTML table with sorting by `HEURISTIC_PRIORITY_SCORE`, filtering by `VALID`/`WARNING`/`REJECTED`, and pagination. | **HIGH** |
| **3. Two-Panel Blink Viewer** | Dither FITS pairs (1D1 vs 4D1); sub-pixel registration in `models/chronos_x/subpixel_registration.py`. | Browser optical blink toggle timer and side-by-side display. | HTML5 dual-canvas / image viewer with client-side JavaScript interval timer (1–4 Hz, play/pause, step forward/backward, opacity slider). | **HIGH** |
| **4. Difference & Significance View** | `ChronosTemporalDifferencer` computes calibrated $\Delta I$ and significance maps. | Interactive difference map visualizer. | Render difference map and $S$-map using Matplotlib colormaps (`coolwarm` / `viridis`) exported as base64 PNG data URIs. | **HIGH** |
| **5. 102-Channel Spectral Chart** | 102-band flux vectors, valid masks, and reconstructed SEDs in `data/processed/spectral_features/`. | Interactive spectral graph. | HTML5 `<canvas>` line chart using Chart.js (or SVG rendered directly by Matplotlib backend) displaying observed flux, error bars, AE reconstruction, and CatWISE IR points. | **HIGH** |
| **6. Multimodal Evidence & Limitations Panel** | Diagnostic breakdown in `CandidateRecord` (`metadata`, `evidence_summary`, veto flags). | Visual inspection cards. | Color-coded status badges: ASTROVISION peak residual, SPECTRA $\chi^2$, CHRONOS dipole veto, and prominent **Scientific Limitations Box**. | **HIGH** |
| **7. Human Review & Citizen-Science Export** | `CandidateRecord.to_dict()` and JSON schema validation. | Review verdict persistence and export action. | Review action form with radio options (`CONFIRMED_CANDIDATE`, `INSTRUMENTAL_ARTIFACT`, `NEEDS_FOLLOWUP`), reviewer notes, and one-click JSON/CSV download. | **HIGH** |

---

## 5. Frozen Baseline Protection & Checksum Audit

All three protected assets were audited to establish the immutability baseline before Task 4.28B:

| Asset Name | Relative Path | Authoritative Expected SHA-256 | Actual Verified SHA-256 | Match |
| :--- | :--- | :--- | :--- | :---: |
| **ASTROVISION V3 Checkpoint** | `checkpoints/astrovision_spatial_v3.pt` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **TRUE** |
| **SPECTRA V2 Checkpoint** | `checkpoints/spectra_masked_ae_v2.pt` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **TRUE** |
| **SPECTRA V2 Thresholds** | `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **TRUE** |

*Under zero circumstances will Task 4.28B modify or re-save these protected files.*

---

## 6. Proposed New UI Architecture & Directory Structure

To ensure strict separation of concerns, all UI code will reside in a new, self-contained directory: `observatory/`. Zero production modules or existing test files will be altered.

```
observatory/
├── __init__.py                 # Package initializer
├── app.py                      # Main entrypoint: launches server and opens local browser (localhost:8050)
├── server.py                   # ThreadingHTTPServer with REST API endpoints:
│                               #   GET  /api/pointings
│                               #   GET  /api/candidates
│                               #   GET  /api/candidate/<id>
│                               #   GET  /api/cutout/<id>
│                               #   GET  /api/spectrum/<id>
│                               #   POST /api/review
├── data_provider.py            # Read-only adapter loading FITS, SEDs, and CandidateRecords
├── static/
│   ├── css/
│   │   └── style.css           # Clean dark-mode NASA-inspired styling
│   └── js/
│       ├── app.js              # Datatable, faceted filtering, candidate selection state
│       ├── blink.js            # Dual-panel optical blink comparator engine (canvas/img toggle)
│       └── chart.js            # 102-channel spectrophotometric SED renderer
└── templates/
    └── index.html              # Jinja2 single-page application template
```

---

## 7. Risks, Limitations & Mitigation Strategies

1. **Risk: Heavy FITS Processing Causing Browser Lag**
   - *Mitigation:* `data_provider.py` will pre-cache cutouts ($128 \times 128$ pixels) and convert arrays to normalized PNG base64 strings on demand rather than streaming raw 2040x2040 FITS files over HTTP.
2. **Risk: Overstating Demo Capabilities to NASA Judges**
   - *Mitigation:* The UI will display a prominent, permanent banner:
     `"PROTOTYPE DEMONSTRATION MODE: All Level-2 pairs are intra-visit dithers (2.1–6.5 min apart). Real secular transients are unvalidated. Multimodal scores are heuristic priority ranking indices."`
3. **Risk: Accidentally Overwriting Protected Assets**
   - *Mitigation:* All write operations in the UI are strictly limited to exporting user reviews into `data/processed/candidates/user_reviews.json` or serving downloadable browser attachments. Zero production models or thresholds are touched.

---

## 8. Step-by-Step Implementation Plan for Task 4.28B

When authorized, Task 4.28B will execute the following controlled implementation sprint:

- [ ] **Step 1: Scaffold UI Package:** Create `observatory/` directory and subdirectories (`static/`, `templates/`).
- [ ] **Step 2: Implement Data Provider (`observatory/data_provider.py`):** Author read-only methods to query candidates from `pointing_0003_candidates.csv`, extract $128 \times 128$ FITS stamps from `data/spherex/`, and fetch 102-band SEDs.
- [ ] **Step 3: Implement Web Server (`observatory/server.py`):** Implement `ThreadingHTTPServer` and `BaseHTTPRequestHandler` handling JSON REST endpoints and Jinja2 template rendering.
- [ ] **Step 4: Author Single-Page Frontend (`index.html`, `style.css`, `app.js`, `blink.js`):**
  - Pointing and candidate datatable with faceted filters.
  - Optical blink comparator with play/pause, speed toggle (1–4 Hz), and manual frame slider.
  - Calibrated difference map and significance map viewer.
  - 102-channel SED graph with autoencoder reconstruction overlay.
  - Multimodal evidence badge panel and scientific limitations box.
  - Human review form with decision radio buttons, notes, and JSON/CSV export button.
- [ ] **Step 5: Author Launcher (`observatory/app.py`):** Single-command CLI launcher (`python observatory/app.py --port 8050`).
- [ ] **Step 6: Author Automated UI Smoke & Integration Tests (`tests/test_observatory_ui.py`):** Verify HTTP endpoints, JSON responses, and cutout generation.
- [ ] **Step 7: Verify Full Regression Suite & Checksum Immutability:** Confirm all 309 existing tests pass and all 3 protected hashes match.

---

## 9. Final Preflight Verdict

$$\mathbf{UI\_ARCHITECTURE\_READY\_WITH\_LIMITATIONS}$$

**Preflight Sign-Off:**
The preflight architecture is completely vetted. All underlying astronomical data and production inference interfaces exist and are callable. The native Python HTTP server architecture achieves 100% compliance with strict zero-installation freeze constraints. The project is ready to proceed to Task 4.28B.

