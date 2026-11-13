# SPECTRA-X / F1 — Product Integration & Web Application Audit
**Audit Date:** 2026-11-03  
**Auditor:** Lead Scientific Software Auditor & ML Engineering Agent  
**Audit Scope:** End-to-End Product Integration across the Five Core User Pages  
**Status:** Architecture Audited / UI Implementation Status: `MISSING` (Data Ready)  

---

## 1. Executive Summary & Audit Finding

The prompt requires verifying whether the five core operational discovery pages function with real backend astronomical data:
1. **Observatory** (Sky viewing, pointing footprints, telescope telemetry)
2. **Candidate Explorer** (Faceted search, priority sorting, multi-modal filters)
3. **Evidence Inspector** (MEF FITS cutout viewer, 102-channel SED graph, blink comparator)
4. **Human Review** (Astronomer triage interface, verification verdicts, notes persistence)
5. **Reports** (Scientific metrics dashboard, markdown audit viewer, export engine)

### Critical Ground-Truth Status:
> **CORE FINDING:**  
> The web application layer (frontend user interface, backend REST API, and review database) has **NOT BEEN IMPLEMENTED** in the current repository codebase.  
> - Frontend source code (`.jsx`, `.tsx`, `.html`, `.css`): **0 files exist**.
> - Backend REST API (`FastAPI`, `Flask`, `express`): **0 endpoints exist**.
> - Persistent database schema (`sqlite`, `postgresql`, `models.py`): **0 migrations exist**.
> 
> **HOWEVER**, all required **backend scientific datasets, candidate catalogs, FITS files, and metadata pipelines are fully operational, verified on disk, and ready for API ingestion.**

---

## 2. Page-by-Page Integration Status & Readiness Matrix

```mermaid
graph TD
    subgraph Operational Scientific Backend
        A["32 Level-2 FITS Files<br/>(data/spherex/)"]
        B["1,392 Candidate Records<br/>(pointing_0003_candidates.csv)"]
        C["Assembled 102-Band SEDs<br/>(independent_test_assembled_spectra.csv)"]
        D["19 Audit & Evaluation Reports<br/>(reports/)"]
    end
    subgraph Web Application Layer (MISSING)
        API["Backend API Service<br/>(FastAPI / Uvicorn)"]
        DB["SQLite / PostgreSQL<br/>(Review Persistence)"]
        P1["1. Observatory Page"]
        P2["2. Candidate Explorer"]
        P3["3. Evidence Inspector"]
        P4["4. Human Review"]
        P5["5. Reports Dashboard"]
    end
    A & B & C & D -.->|Needs Ingestion| API
    API --> P1 & P2 & P3 & P4 & P5
    DB <--> P4
```

| Page Name | Operational Status | Underlying Backend Data Status | Available Real Data Source | Required Implementation Action |
| :--- | :---: | :---: | :--- | :--- |
| **1. Observatory** | **`MISSING`** | **`VERIFIED`** | 32 Level-2 FITS files in `data/spherex/` with verified WCS, CRVAL, timestamps, and footprints. | Implement sky projection canvas (Aladin-Lite or Three.js celestial sphere) with pointing polygon overlays. |
| **2. Candidate Explorer** | **`MISSING`** | **`VERIFIED`** | [`pointing_0003_candidates.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/candidates/pointing_0003_candidates.csv) (1,392 evaluated rows with schema compliance). | Build faceted datatable with sorting by `HEURISTIC_PRIORITY_SCORE`, filtering by validity status and co-pilot tags. |
| **3. Evidence Inspector** | **`MISSING`** | **`VERIFIED`** | FITS cutouts ($128 \times 128$), SED flux tables, and CHRONOS difference maps. | Implement multi-extension FITS stamp viewer (JS9/FITS.js), 102-band Plotly SED visualizer, and dither blink comparator. |
| **4. Human Review** | **`MISSING`** | **`VERIFIED`** | Candidate evidence summaries and diagnostic rejection flags ready for review. | Build astronomer review form with verdict radio options (`CONFIRMED`, `FALSE_POSITIVE`, `REQUIRES_FOLLOWUP`), tags, and SQLite persistence. |
| **5. Reports** | **`MISSING`** | **`VERIFIED`** | 19 Markdown audit reports and JSON metric summaries in `reports/`. | Create report index viewer with Markdown renderer and CSV/JSON export buttons. |

---

## 3. Data Integration & Verification Rules

To maintain scientific integrity during product development:
1. **Zero Mock Data Representation:**
   - Synthetic or randomized candidates (such as the legacy 25 random samples from `models/fusion_x/rank_anomalies.py`) must **NEVER** be displayed in the Candidate Explorer as real astronomical observations.
   - All candidate listings must be populated directly from verified pipeline runs (`data/processed/candidates/pointing_0003_candidates.csv`).
2. **Real FITS Loading:**
   - Cutout displays must be generated dynamically from actual FITS science files (`IMAGE`, `VARIANCE`, `FLAGS` extensions) rather than pre-rendered static placeholders.
3. **Blink & Difference Visualization:**
   - The blink comparator must alternate between real reprojected dither frames (e.g. 1D1 and 4D1) and display the calibrated difference map with dipole defect overlays.
4. **Astronomer Review Persistence:**
   - Astronomer verification verdicts must be persisted into a structured SQLite/PostgreSQL database with timestamp, user ID, decision tag, and rationale notes.

---

## 4. Backend API Specification (Target Architecture)

To bridge the operational ML backend with the web frontend, the following lightweight REST API service must be built:

| Endpoint | Method | Input Parameters | Output Payload | Backend Data Source |
| :--- | :---: | :--- | :--- | :--- |
| `/api/pointings` | GET | `release` (optional) | List of pointings with RA, Dec, MJD, detectors, footprints | `manifests/fits_validation_catalog.csv` |
| `/api/candidates` | GET | `validity_status`, `copilot_tag`, `min_score`, `limit`, `offset` | Paginated list of candidate records conforming to candidate schema | `data/processed/candidates/pointing_0003_candidates.csv` |
| `/api/candidates/{id}` | GET | `candidate_id` | Full candidate record, metadata, and evidence breakdown | `pointing_0003_candidates.csv` |
| `/api/candidates/{id}/sed` | GET | `candidate_id` | 102-band wavelengths, observed fluxes, uncertainties, reconstructed fluxes, masks | `data/processed/spectral_features/independent_test_assembled_spectra.csv` |
| `/api/candidates/{id}/cutout` | GET | `candidate_id`, `extension` (`IMAGE`/`DIFF`/`RESIDUAL`) | PNG / Array data of $128 \times 128$ stamp | Dynamic FITS extraction from `data/spherex/qr3/level2/` |
| `/api/reviews` | POST | `candidate_id`, `verdict`, `reviewer_name`, `notes` | Confirmation status and review timestamp | `db/reviews.sqlite` |
| `/api/reports` | GET | `report_id` | Rendered Markdown text and metric tables | `reports/*.md` |
