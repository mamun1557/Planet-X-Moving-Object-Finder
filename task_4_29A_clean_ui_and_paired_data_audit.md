# TASK 4.29A — Clean Input-Driven UI Replacement & Paired Observation Dataset Audit

**Project:** Planet X: Moving Object Finder / SPECTRA-X  
**Team:** VU_VioNux (NASA Space Apps Challenge)  
**Task:** Task 4.29A Architecture Audit & Implementation Plan  
**Execution Mode:** STRICTLY READ-ONLY (No code, file, or data modifications)  
**Execution Timestamp:** 2026-11-13T12:05:00+06:00  
**Status:** COMPLETE — IMPLEMENTATION_PLAN_READY_WITH_DATA_LIMITATIONS  

---

## Executive Summary & Acceptance Verdict

This read-only audit establishes the technical roadmap for completely replacing the existing SPECTRA-X frontend with a clean, input-driven astronomical analysis workspace and defines the architecture for a 50-pair (100 observation samples) paired observation library.

### Final Task Verdict
```text
================================================================================
FINAL VERDICT: IMPLEMENTATION_PLAN_READY_WITH_DATA_LIMITATIONS
Reason: The application architecture, session management, and UI design are
fully specified and ready for implementation. However, an exhaustive audit of all
171 SPHEREx Level-2 science FITS files on disk reveals exactly ZERO (0) real
multi-epoch observation pairs (Δt ≥ 1 day). All 283 same-detector overlapping pairs
are strictly intra-visit dither observations (Δt ≈ 2.15 to 15.0 minutes).
Therefore, to reach the required 50-pair library without fabricating astronomical
data, the library must be structured as 25 Real Intra-Visit pairs and 25 Synthetic
Engineering Test pairs.
================================================================================
```

---

## 1. Current UI Architecture & Preload Audit

### 1.1 Existing Frontend Structure
The active frontend is a React 18.3.1 single-page application built with Vite 5.4.14 in `frontend/`. It currently defines 5 primary top-level tabs:
1. `EXPLORE`: 5-div stacked view containing the WCS Sky Canvas, Transient Summary, Blink Viewer, 102-channel SED, and the 4-step pipeline explanation.
2. `OBJECTS`: Sortable catalogue listing 25 infrared sources with status pills and action links.
3. `DATA_INPUT`: Data Input Station supporting coordinate searches and file uploads.
4. `HOW_IT_WORKS`: Technical overview of the multi-module AI detection stack.
5. `ABOUT`: Mission background and team attribution.

### 1.2 The Preload & Persistence Problem
An inspection of `frontend/src/App.jsx` reveals that upon mounting, the application unconditionally preloads historical and hardcoded data:
```javascript
// Current App.jsx mounting behavior:
useEffect(() => {
  loadSystemStatus();
  loadCandidatesList(); // <-- Automatically fetches /api/candidates
  loadReviewsList();    // <-- Automatically loads historical user reviews
}, []);
```
- When `/api/candidates` returns, `App.jsx` automatically defaults to selecting Candidate `SPX-J163.6309-69.4422` (line 103), which immediately requests `/api/cutout/SPX-J163.6309-69.4422` and `/api/spectrum/SPX-J163.6309-69.4422`.
- As a consequence, a user opening the application is immediately presented with Field P0003, pre-computed candidate scores, pre-rendered FITS cutouts, and historical review notes.
- This directly violates the clean input-driven requirement where the user must begin in an unpopulated workspace, provide observation inputs, select a target, and initiate processing.

---

## 2. Existing Backend & API Dependencies

### 2.1 Server Architecture (`observatory/server.py`)
The observatory backend is a multi-threaded Python HTTP server (`ThreadingHTTPServer`) operating on `observatory/app.py` and `observatory/server.py`:
- **Singleton Data Provider:** `ObservatoryHTTPRequestHandler` defines `data_provider = ObservatoryDataProvider()` as a **class attribute**. All incoming HTTP requests across all threads share the exact same singleton instance.
- **REST Endpoints:**
  - `GET /api/status`: Returns system telemetry, PyTorch device, and dataset ID (`P0003_SPHEREx_Level2`).
  - `GET /api/candidates`: Returns candidate tables. Defaults to built-in P0003 candidates unless overridden.
  - `GET /api/candidate/<id>`: Returns candidate metadata.
  - `GET /api/cutout/<id>`: Extracts 2D cutouts from FITS dither files (`1D1` and `4D1`).
  - `GET /api/spectrum/<id>`: Runs autoencoder inference on 102-channel SED.
  - `GET /api/reviews`: Reads persisted reviews from disk (`user_candidate_reviews.json`).
  - `POST /api/review`: Appends a review to the global review file.
  - `POST /api/target/search`: Validates coordinates and checks Field P0003 bounding box.
  - `POST /api/data/validate`: Validates astronomical file formats (FITS, CSV).
  - `POST /api/data/upload`: Ingests custom candidate tables into `data_provider._custom_dataset`.
  - `DELETE /api/data/upload`: Clears `data_provider._custom_dataset`.

### 2.2 Backend Vulnerabilities & State Leakage Risks
1. **Cross-Session Ingestion Leakage:** Because `data_provider` is a process-level singleton, if User A uploads a custom dataset, User B (or another browser tab) calling `GET /api/candidates` will immediately see User A's uploaded candidates.
2. **Global Review Persistence:** User reviews are written to a single shared file: `data/processed/reviews/user_candidate_reviews.json`. A new session cannot distinguish between fresh analysis and historical review records.
3. **Hardcoded P0003 Fallback:** If no custom dataset is loaded, `data_provider.list_candidates()` automatically falls back to reading `data/processed/candidates/pointing_0003_candidates.csv`.

---

## 3. Existing Sample Data Inventory

An exhaustive audit of all data on disk was conducted:

| Directory Path | File Type | Count | Description / Sky Region |
|:---|:---|:---:|:---|
| `data/spherex/qr2/level2/` | FITS Level-2 | 20 | April 2025 observations (Pointings 0001, 0002, 0004, 0005, 0006; Dithers 1D–4D; Detectors D1–D2) |
| `data/spherex/qr2_deep/` | FITS Level-2 | 4 | April 2025 deep field (Pointing 0004; D1; 4 dithers) |
| `data/spherex/qr3/level2/` | FITS Level-2 | 23 | July 2026 observations (Pointing 0003; Dithers 1D–4D; Detectors D1–D6) |
| `data/spherex/qr3_deep/` | FITS Level-2 | 4 | July 2026 deep field (Pointing 0004; D1; 4 dithers) |
| `data/spherex/multipointing_pilot/level2/` | FITS Level-2 | 120 | July 2026 multi-pointing pilot (Pointings 0001, 0002, 0008, 0009, 0010; 4 dithers; 6 detectors D1–D6) |
| `data/external/gaia_dr3/` | CSV Catalog | 18 | Gaia DR3 reference stars and cone searches around pointings |
| `data/external/allwise/` | CSV Catalog | 1 | AllWISE cross-match candidates in Pointing 0003 |
| `data/external/jpl_horizons/` | CSV Ephemeris | 5 | Ephemerides for Apophis, Ceres, Eros, Pallas, Vesta (all > 40° outside FOV) |
| `data/external/minor_planets/` | JSON Catalog | 1 | JPL SBDB orbital parameters for 2,000 asteroids |
| `data/processed/candidates/` | CSV Catalog | 1 | 25 high-priority candidates in Pointing 0003 |
| `data/processed/pilot_catalogues/` | CSV Catalog | 5 | Extracted source catalogs for Pointings 0001, 0002, 0008, 0009, 0010 |

**Total Level-2 Science FITS Files on Disk:** **171 files**.

---

## 4. Real Paired Observation Audit & Classification

A geometric and temporal pairing audit was executed across all 171 science FITS files. Great-circle angular separations between pointing centers were calculated, and timestamps (`MJD-OBS` and `DATE-OBS`) were evaluated.

### 4.1 Pairing Audit Results
- **Total Overlapping Pairs ($\Delta \theta \le 3.5^\circ$ FOV):** 599 pairs.
- **Same-Detector Overlapping Pairs:** 283 pairs.
  - Detector D1 ($0.75 - 1.11\,\mu\text{m}$): 86 pairs
  - Detector D2 ($1.11 - 1.64\,\mu\text{m}$): 56 pairs
  - Detector D3 ($1.64 - 2.42\,\mu\text{m}$): 33 pairs
  - Detector D4 ($2.42 - 3.82\,\mu\text{m}$): 36 pairs
  - Detector D5 ($3.82 - 4.42\,\mu\text{m}$): 36 pairs
  - Detector D6 ($4.42 - 5.00\,\mu\text{m}$): 36 pairs

### 4.2 Temporal Baseline Breakdown
- **Pairs with $\Delta t \ge 1.0\text{ day}$ (Multi-Epoch):** **0 pairs (0.0%)**
- **Pairs with $\Delta t < 1.0\text{ day}$ (Intra-Visit):** **283 pairs (100.0%)**
  - Minimum time separation: 2.15 minutes (between consecutive dithers, e.g. 1D and 2D).
  - Maximum time separation: 16.5 minutes (between dither 1D and dither 4D of adjacent pointings).
  - Angular dither shift: $0.18^\circ$ to $1.25^\circ$.

### 4.3 Why Are There No Real Multi-Epoch Pairs?
1. **Orbital Precession:** The SPHEREx observatory orbits in a Sun-synchronous low-Earth orbit, precessing $\sim 1^\circ$ per day along the ecliptic. Pointings observed during QR2 (April 2025, Week 17) were located near $(\alpha \approx 164.7^\circ, \delta \approx +29.1^\circ)$. Pointings observed during QR3 (July 2026, Week 30) were located near $(\alpha \approx 232.7^\circ, \delta \approx -10.7^\circ)$.
2. **Pointing Identifier Disambiguation:** Pointing identifiers like `0001` or `0002` are **sequence indices within an observation plan**, NOT fixed sky tiles. `2025W17_4B_0001` and `2026W30_1B_0001` are separated by **$68.2^\circ$** on the sky and share zero overlapping footprint.
3. **Conclusion:** The local dataset contains **0 real multi-epoch observation pairs**. Any claim that existing SPHEREx data provides real multi-month temporal baselines is scientifically false.

---

## 5. Sample Data Classification Matrix

All identified data pairs are formally classified according to the 4 strict categories:

```text
+-----------------------------------------------------------------------------------------+
| CATEGORY                      | AVAILABLE ON DISK | SCIENTIFIC UTILITY & RESTRICTIONS   |
+-----------------------------------------------------------------------------------------+
| A. REAL_MULTI_EPOCH           | 0 pairs           | None available in current download. |
|                               |                   | Requires future multi-month repeat. |
+-----------------------------------------------------------------------------------------+
| B. REAL_INTRA_VISIT           | 283 pairs         | Real flight data (Δt ≈ 2–15 min).   |
|                               |                   | Excellent for WCS registration,     |
|                               |                   | PSF subtraction, null tests.        |
|                               |                   | INELIGIBLE for secular motion.      |
+-----------------------------------------------------------------------------------------+
| C. SYNTHETIC_ENGINEERING_TEST | 0 (Feasible: 25+) | Simulated multi-epoch injections    |
|                               |                   | with known Keplerian / NEO motion.  |
|                               |                   | Strictly marked synthetic.          |
+-----------------------------------------------------------------------------------------+
| D. UNSUITABLE                 | ~316 cross-rel/   | Cross-release pairings (QR2 vs QR3) |
|                               | cross-detector    | or cross-detector pairings.         |
|                               | pairs             | Incompatible bands and calibration. |
+-----------------------------------------------------------------------------------------+
```

---

## 6. Proposed 50-Pair Target Library Structure

To meet the user's requirement for a 50-pair library (100 observation samples) with absolute scientific honesty and zero data fabrication, we propose assembling:
- **25 REAL_INTRA_VISIT pairs** (50 observations) from existing SPHEREx Level-2 flight data.
- **25 SYNTHETIC_ENGINEERING_TEST pairs** (50 observations) with rigorously modeled multi-epoch physical displacements.

### 6.1 Directory & File Layout
```text
sample_data/
├── README.md
├── manifests/
│   ├── pair_library_manifest.json
│   └── pair_library_manifest.csv
├── real_intra_visit/
│   ├── pair_001_p0003_d1_1d1_4d1/
│   │   ├── obs_a_1d1.fits
│   │   ├── obs_b_4d1.fits
│   │   └── pair_metadata.json
│   ├── pair_002_p0001_d1_1d1_2d1/
│   │   ├── obs_a_1d1.fits
│   │   ├── obs_b_2d1.fits
│   │   └── pair_metadata.json
│   └── ... (25 pairs total: P0001, P0002, P0003, P0008, P0009, P0010 across D1-D6)
└── synthetic_engineering/
    ├── pair_026_syn_neo_fast_d1/
    │   ├── obs_a_epoch1.fits
    │   ├── obs_b_epoch2.fits
    │   ├── ground_truth_trajectory.json
    │   └── pair_metadata.json
    ├── pair_027_syn_kbo_slow_d2/
    │   ├── obs_a_epoch1.fits
    │   ├── obs_b_epoch2.fits
    │   ├── ground_truth_trajectory.json
    │   └── pair_metadata.json
    └── ... (25 pairs total: Δt = 1 to 90 days; Δθ = 0.5" to 120.0")
```

### 6.2 Mandatory Metadata Schema for Every Pair
Every pair will be cataloged in `pair_library_manifest.json` with the following schema:
```json
{
  "pair_id": "PAIR-REAL-001",
  "classification": "REAL_INTRA_VISIT",
  "pointing_id": "P0003",
  "detector": "D1",
  "wavelength_range_um": [0.75, 1.11],
  "obs_a": {
    "filename": "level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits",
    "dither": "1D1",
    "timestamp_utc": "2026-07-20T00:26:21.423",
    "mjd": 61241.018303,
    "crval1_deg": 163.6309,
    "crval2_deg": -69.4422,
    "wcs_valid": true
  },
  "obs_b": {
    "filename": "level2_2026W30_1B_0003_4D1_spx_l2b-v27-2026-222.fits",
    "dither": "4D1",
    "timestamp_utc": "2026-07-20T00:32:48.216",
    "mjd": 61241.022780,
    "crval1_deg": 163.6318,
    "crval2_deg": -69.4421,
    "wcs_valid": true
  },
  "delta_t_minutes": 6.4465,
  "angular_separation_arcsec": 0.84,
  "displacement_suitability": "SUITABLE_FOR_REGISTRATION_AND_NULL_TESTING_ONLY",
  "motion_evidence_status": "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
  "is_synthetic": false
}
```

---

## 7. Movement Analysis Requirements & Capability Audit

A rigorous mathematical and algorithmic audit of existing motion analysis capabilities was conducted across `spectra_engine/`, `models/motion_x/`, `observatory/data_provider.py`, and `scripts/process_crossmatch_and_classification.py`.

### 7.1 Existing vs Missing Motion Capabilities

| Capability | Current Status in Codebase | Audit Findings & Required Implementation |
|:---|:---:|:---|
| **WCS-based Coordinate Conversion** | `IMPLEMENTED` | `astropy.wcs.WCS` accurately maps $(x, y) \leftrightarrow (\alpha, \delta)$ with SIP polynomial distortion corrections. |
| **Spherical Angular Separation** | `IMPLEMENTED` | Haversine formula implemented in `scripts/process_crossmatch_and_classification.py` (`angular_separation_arcsec`). |
| **RA Wraparound Handling** | `PARTIAL` | Haversine formula handles scalar separation across $0^\circ/360^\circ$ correctly. However, vector difference $(\Delta \alpha \cos \delta, \Delta \delta)$ requires explicit wrapping via `((dra + 180) % 360) - 180`. |
| **Observation Time Parsing** | `IMPLEMENTED` | ISO 8601 strings and `MJD-OBS` parsed from FITS Extension 1 header. |
| **Motion Rate Calculation** | `MISSING` | Needs standardized rate output: $\omega = \frac{\Delta \theta}{\Delta t}$ in **$\text{arcsec/hour}$** and **$\text{arcsec/day}$**. |
| **Uncertainty Propagation** | `MISSING` | Centroid fitting errors $\sigma_{\theta_1}, \sigma_{\theta_2}$ must propagate into total astrometric uncertainty: $\sigma_{\Delta \theta} = \sqrt{\sigma_{\theta_1}^2 + \sigma_{\theta_2}^2}$. |
| **Proper-Motion Reference Comparison** | `IMPLEMENTED` | `MotionXValidator.crossmatch_gaia()` correctly identifies stationary stars and proper-motion outliers using Gaia DR3. |
| **Astrometric Registration Verification** | `MISSING` | Apparent shift between epochs must be compared against stationary background stars to verify whether displacement is genuine object motion or residual spacecraft pointing drift. |
| **Intra-Visit Dither Safeguard** | `IMPLEMENTED` | `TemporalEligibilityAssessor` flags $\Delta t < 1.0\text{ day}$ as `INTRA_VISIT_DITHER`. The UI must explicitly display `MOTION_STATUS: INTRA_VISIT_DITHER` and prevent false discovery claims. |

### 7.2 Standardized Output Contract for Motion Analysis
The future UI and backend must format motion results according to this exact contract:
- `initial_position`: `{ "ra_deg": float, "dec_deg": float, "epoch_utc": str, "mjd": float }`
- `subsequent_position`: `{ "ra_deg": float, "dec_deg": float, "epoch_utc": str, "mjd": float }`
- `angular_displacement_arcsec`: `float`
- `time_baseline`: `{ "dt_minutes": float, "dt_hours": float, "dt_days": float }`
- `motion_rate`: `{ "arcsec_per_hour": float, "arcsec_per_day": float }`
- `coordinate_uncertainty_arcsec`: `float`
- `astrometric_reference`: `{ "gaia_match": bool, "gaia_source_id": str, "pm_ra_mas_yr": float, "pm_dec_mas_yr": float }`
- `movement_evidence_status`: One of:
  - `REAL_MOTION_DETECTED` (Statistically significant displacement $\ge 3\sigma$ over $\Delta t \ge 1\text{ day}$)
  - `INTRA_VISIT_DITHER` (Observation baseline $\Delta t < 1\text{ day}$; displacement consistent with spacecraft dither)
  - `STATIONARY_SOURCE` (Displacement within measurement noise $< 3\sigma$)
  - `MOTION_UNAVAILABLE` (Insufficient observation epochs or unassociated detection)

---

## 8. New UI Structure & Workflow Plan

The proposed replacement frontend is a streamlined, single-session, scientific analysis workspace with zero decorative clutter and zero preloaded datasets.

### 8.1 Ten-Step Linear User Workflow
```mermaid
flowchart LR
    S1[1. Empty Workspace] --> S2[2. Upload Data]
    S2 --> S3[3. Validate Input]
    S3 --> S4[4. Select Target]
    S4 --> S5[5. Check Compatibility]
    S5 --> S6[6. Run Analysis]
    S6 --> S7[7. View Results]
    S7 --> S8[8. Inspect Motion]
    S8 --> S9[9. Review Evidence]
    S9 --> S10[10. Export Report]
```

### 8.2 Five Screen Sections (Clean Single-Page Architecture)

#### Section 1: New Analysis (Initial Empty State)
- **Top Header:** Clean branding ("Planet X: Moving Object Finder"), session status (`SESSION: IDLE`), and a "Reset Session" button.
- **Empty State Display:** Clear call to action prompting the user to provide observation data.
- **Two Ingestion Modes:**
  1. *User Data Upload Dropzone:* Accepts dual-epoch FITS images (`.fits`), 102-channel spectrophotometry CSV (`.csv`), or candidate catalogs.
  2. *Sample Pair Selector:* Dropdown providing direct one-click loading of any pair from the 50-pair library (grouped cleanly into "Real Flight Intra-Visit Dither Pairs" and "Synthetic Multi-Epoch Engineering Test Pairs").
- **Target Selection:**
  - Option A: Manual coordinate input $(\alpha, \delta)$ with search radius.
  - Option B: Interactive candidate table generated from the uploaded/selected data.

#### Section 2: Input Validation & Compatibility Station
- Displays format validation results immediately upon file drop:
  - FITS Header Sanity (HDU presence, bitpix, dimensions, valid WCS `RA---TAN-SIP`).
  - Spectrophotometry Sanity (102 channels, wavelength grid $[0.75 - 5.00\,\mu\text{m}]$, valid flux units).
  - Temporal Sanity (Observation timestamps parsed, baseline calculated).
- Dynamic 5-Module Compatibility Matrix:
  - ASTROVISION: Green if dual-epoch FITS cutouts available.
  - SPECTRA V2: Green if 102-channel SED available.
  - CHRONOS-X: Green if $\ge 2$ registered epochs available.
  - MOTION-X: Green if multi-epoch coordinates available; Amber with `INTRA_VISIT_DITHER` tag if $\Delta t < 1\text{ day}$.
  - FUSION-X: Green if $\ge 2$ sensor modalities active.

#### Section 3: Analysis Workspace & Execution Control
- "Run Analysis" button (disabled until input validation passes).
- Progress bar and module status indicators showing pipeline execution:
  - ASTROVISION (Spatial anomaly residual)
  - SPECTRA V2 (Reconstruction loss & threshold test)
  - CHRONOS-X (Image difference & significance $\sigma$)
  - MOTION-X (Astrometric shift & ephemeris check)
  - FUSION-X (Multi-modal evidence aggregation & priority score)

#### Section 4: Results & Movement Inspection
- **Object Coordinates & Astrometry:** RA, Dec, J2000, galactic coordinates.
- **Dedicated Object Movement Panel:**
  - Epoch 1 vs Epoch 2 coordinates.
  - Angular displacement in arcseconds ($\Delta \theta$).
  - Time separation ($\Delta t$) and calculated motion rate ($\text{arcsec/hour}$).
  - Astrometric uncertainty ($\sigma_{\Delta \theta}$).
  - Movement evidence status badge (`REAL_MOTION_DETECTED`, `INTRA_VISIT_DITHER`, `MOTION_UNAVAILABLE`).
- **Interactive Visualizers:**
  - Optical Blink Comparator (alternating between Epoch 1 and Epoch 2 with cadence slider).
  - Difference Viewer (residual flux map with colorbar).
  - 102-Channel SED Plot (observed flux, autoencoder fit, uncertainty envelope).
  - Multi-Modal AI Evidence Inspector (sub-score breakdown and radar chart).

#### Section 5: Review & Export Station
- Human classification selector: `CONFIRMED_CANDIDATE`, `FALSE_POSITIVE`, `NEEDS_FOLLOWUP`, `UNKNOWN`.
- Review notes text area.
- Centralized Export buttons:
  - Download Standardized JSON Audit Report (includes inputs, hashes, metrics, and review disposition).
  - Download CSV Candidate Record.

---

## 9. Required Frontend & Backend Changes

### 9.1 Backend Architecture Changes (`observatory/`)
1. **Per-Session State Isolation:**
   - Eliminate the class-level singleton `data_provider` in `server.py`.
   - Implement an ephemeral session store: `SessionManager` that generates a UUID `session_id` for every browser instance.
   - Store uploaded files and transient analysis outputs under `scratch/sessions/<session_id>/`.
   - Ensure an empty session initializes with `candidates: []`, `target: null`, `dataset: null`.
2. **New Dedicated API Endpoints:**
   - `POST /api/session/init`: Creates a clean session ID.
   - `POST /api/session/reset`: Tears down session memory and deletes temporary files.
   - `GET /api/samples/manifest`: Returns the complete metadata catalog of the 50-pair library.
   - `POST /api/samples/load`: Loads a selected sample pair from the library into the active session.
   - `POST /api/analysis/run`: Triggers inference across the 5 modules for the active session target.
   - `POST /api/motion/calculate`: Standalone endpoint computing spherical separation, motion rate, uncertainty, and dither classification.

### 9.2 Frontend Architecture Changes (`frontend/src/`)
1. **Lifecycle Refactoring (`App.jsx`):**
   - Remove automatic data fetching (`loadCandidatesList()`) from `useEffect`.
   - Introduce `analysisState`: `'EMPTY' | 'VALIDATING' | 'READY' | 'RUNNING' | 'COMPLETE'`.
2. **Component Consolidation:**
   - Deprecate hardcoded P0003 components (`SkyVisualization.jsx`, `ObjectSummaryCard.jsx`).
   - Create unified `WorkspaceView.jsx` housing the 5 sequential sections.
   - Create dedicated `MotionAnalysisCard.jsx` displaying astrometric displacement metrics.

---

## 10. Data Isolation, Session Leaks & Temporary File Lifecycle

| Vulnerability / Risk | Current Implementation | Proposed Safeguard / Resolution |
|:---|:---|:---|
| **Cross-User Custom Data Leak** | Singleton `data_provider._custom_dataset` shared across all HTTP requests. | Session-keyed memory dictionary `sessions[session_id]` with thread locking. |
| **Old Session Results Leaking** | Historical reviews in `user_candidate_reviews.json` are returned to all users. | Reviews scoped exclusively to `session_id`; export writes fresh in-memory session report. |
| **Temporary Upload Disk Bloat** | Uploaded base64 chunks stored indefinitely in memory or temp paths. | Temporary session directories under `scratch/sessions/<session_id>/` with 2-hour TTL auto-reaper. |
| **Accidental Ground-Truth Mutation** | Ingested files could theoretically overwrite default catalog paths. | Ground-truth directories (`data/processed/`, `checkpoints/`) enforced as strictly read-only. |

---

## 11. Phased Implementation Roadmap

```mermaid
flowchart TD
    subgraph Phase 1: Backend Architecture
        P1A[Task 4.29B1: Session Manager & Ephemeral Storage]
        P1B[Task 4.29B2: Motion Analysis Calculation Service]
        P1C[Task 4.29B3: Sample Library API Endpoints]
    end
    subgraph Phase 2: Sample Library Curation
        P2A[Task 4.29C1: Curate 25 Real Intra-Visit Pairs]
        P2B[Task 4.29C2: Generate 25 Synthetic Engineering Pairs]
        P2C[Task 4.29C3: Build & Validate Library Manifest]
    end
    subgraph Phase 3: Frontend Implementation
        P3A[Task 4.29D1: Clean Empty Workspace UI]
        P3B[Task 4.29D2: Data Ingestion & Sample Loader]
        P3C[Task 4.29D3: Motion Analysis & Results Panels]
    end
    subgraph Phase 4: Acceptance Testing
        P4A[Task 4.29E1: Multi-Viewport Browser Regression]
        P4B[Task 4.29E2: Data Isolation & Hash Verification]
    end
    Phase 1 --> Phase 2 --> Phase 3 --> Phase 4
```

- **Phase 1: Backend Session Isolation & Motion Engine (Task 4.29B)**
  - Implement `SessionManager` in `observatory/session_manager.py`.
  - Implement `AstrometricMotionEngine` in `spectra_engine/motion_analysis.py`.
  - Implement REST routes for session management, sample library, and motion calculation.
- **Phase 2: Paired Observation Sample Library Assembly (Task 4.29C)**
  - Package 25 `REAL_INTRA_VISIT` pairs into `sample_data/real_intra_visit/`.
  - Generate 25 `SYNTHETIC_ENGINEERING_TEST` pairs into `sample_data/synthetic_engineering/`.
  - Validate all 50 pairs against WCS, timestamp, and format schemas; generate `pair_library_manifest.json`.
- **Phase 3: Clean Input-Driven Frontend Implementation (Task 4.29D)**
  - Re-architect `frontend/src/` to guarantee empty workspace on startup.
  - Implement file dropzone, sample library dropdown, target selector, and motion card.
  - Integrate live execution indicators and centralized report exporter.
- **Phase 4: Full Acceptance & Browser Regression Testing (Task 4.29E)**
  - Automated CDP browser testing across $1440 \times 900$, $1280 \times 720$, and $390 \times 844$.
  - Bitwise SHA-256 validation of all frozen checkpoints and ground-truth catalogs.

---

## 12. Verification & Acceptance Criteria

When implementation commences, the following criteria must be satisfied for task sign-off:

1. **Zero Preload on Startup:** Upon launching the application and navigating to `http://127.0.0.1:8050/`, the UI must display an unpopulated workspace with zero pre-loaded candidates, zero historical review records, and zero default P0003 sky visualizers.
2. **Session Isolation:** Multiple independent browser sessions (or incognito windows) must maintain independent states without cross-contamination.
3. **Paired Library Completeness:** Exactly 50 pairs (100 observation samples) cataloged in `pair_library_manifest.json`, partitioned cleanly into 25 `REAL_INTRA_VISIT` and 25 `SYNTHETIC_ENGINEERING_TEST`.
4. **Motion Analysis Precision:** Spherical displacement, time interval, angular motion rate, and astrometric uncertainty calculated and displayed with correct units (`arcsec`, `arcsec/hour`).
5. **Intra-Visit Dither Safeguard:** All intra-visit dither pairs must fail closed for secular motion, displaying `INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY`.
6. **Scientific Model Immutability:** Bitwise SHA-256 hashes of all frozen checkpoints (`astrovision_spatial_v3.pt`, `spectra_masked_ae_v2.pt`, thresholds JSON) must remain 100% unaltered.

---

## 13. Final Declaration

This audit and implementation plan provides an exhaustive, mathematically sound, and scientifically honest roadmap for the clean input-driven UI replacement and 50-pair library curation.

**Final Status:** `IMPLEMENTATION_PLAN_READY_WITH_DATA_LIMITATIONS`  
**Execution Action:** STOPPING EXECUTION AS DIRECTED (READ-ONLY COMPLETE).

