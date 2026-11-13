# Reproducibility Instructions & Operational Protocol
## Phase 4, Task 4.19B — Controlled External Catalog Acquisition & Exact-Footprint Crossmatch
**Module:** ASTROVISION + Spatial Evidence Audit  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10 on Windows)  
**Parent Tasks:** Phase 4 Tasks 4.17, 4.18, 4.18-SKY, 4.19A, 4.19B

---

### 1. Environment Verification & Prerequisites

Ensure the active working directory is the repository root:
```powershell
Set-Location "c:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X"
```

Verify that the Python virtual environment `.venv_validation` is present and functional:
```powershell
.\.venv_validation\Scripts\python.exe --version
# Expected: Python 3.12.10
```

Verify core scientific dependencies:
```powershell
.\.venv_validation\Scripts\python.exe -c "import astropy, numpy, pandas, scipy; print('Core dependencies verified.')"
```

*Note: In accordance with Task 4.19B strict execution boundaries, no new Python packages (e.g. `pyarrow`, `fastparquet`) are installed. All caching and tabular artifacts use standard RFC 4180 CSV and JSON formats.*

---

### 2. Remote TAP Service Endpoints & Protocols

Task 4.19B queries two authoritative, publicly accessible astronomical TAP (Table Access Protocol) services:

1. **Heidelberg Astronomisches Rechen-Institut (ARI) TAP Service:**
   - **Endpoint:** `https://dc.zah.uni-heidelberg.de/tap/sync`
   - **Catalog Table:** `gaiadr3.gaia_source`
   - **Query Protocol:** ADQL 2.0 with spatial geometric constraints (`1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', ...))`).
   - **Batching Scheme:** 15 cutout footprints per synchronous TAP batch (100 batches total across 1,500 cutouts).
   - **Fields Queried:** `source_id`, `ra`, `dec`, `phot_g_mean_mag`, `phot_bp_mean_mag`, `phot_rp_mean_mag`, `pmra`, `pmdec`, `parallax`.

2. **NASA/IPAC Infrared Science Archive (IRSA) TAP Service:**
   - **Endpoint:** `https://irsa.ipac.caltech.edu/TAP/sync`
   - **Catalogs Queried:**
     - `catwise_2020` (CatWISE2020)
     - `fp_psc` (2MASS Point Source Catalog)
   - **Query Protocol:** ADQL 2.0 single-cone spatial constraints (`CONTAINS(POINT('J2000', ra, dec), CIRCLE('J2000', ...))=1`).
   - **Formatting Note:** IRSA requires uppercase `FORMAT=CSV`. Synchronous queries enforce a maximum row limit of 50,000.

---

### 3. Executing the Catalog Acquisition & Crossmatch Pipeline

The primary pipeline script is located at:
`scripts/acquisition/execute_task_4_19B_acquisition.py`

#### A. Execution from Cached Raw Catalog CSVs (Offline / Reproducible Verification):
All raw acquired catalog data are committed locally in `data/external_catalogs/task_4_19B/`:
- `gaia_dr3_raw_acquired.csv` (1,176,689 Gaia DR3 sources)
- `catwise2020_raw_fps.csv` (168,780 CatWISE2020 sources)
- `twomass_raw_fps.csv` (26,391 2MASS PSC sources)

To re-run the exact-footprint Astropy WCS crossmatching, astrometric epoch propagation, and deliverable report generation from cache:
```powershell
.\.venv_validation\Scripts\python.exe -u scripts/acquisition/execute_task_4_19B_acquisition.py
```
*Expected runtime:* ~150 to 180 seconds.

#### B. Full Remote Acquisition Execution (from Remote TAP APIs):
To re-download all external catalog batches from scratch:
1. Delete or rename the cache directory `data/external_catalogs/task_4_19B/`.
2. Run the script with network elevation:
```powershell
# Requires network access (BypassSandbox: true)
.\.venv_validation\Scripts\python.exe -u scripts/acquisition/execute_task_4_19B_acquisition.py
```
*Expected runtime:* ~8 to 12 minutes depending on network latency.

---

### 4. Deliverables & Outputs

The pipeline produces all requested tabular artifacts in `reports/phase4/task_4_19B/`:

| Deliverable File | Description |
|:---|:---|
| `catalog_acquisition_manifest.json` | Complete metadata log of all remote TAP queries executed |
| `catalog_acquisition_failures.csv` | Error log and resolution of ADQL syntax exceptions |
| `catalog_source_records.csv` | All crossmatched sources with propagated 2026.5496 coordinates |
| `exact_footprint_crossmatch.csv` | Record-level spatial join between cutout pixels and catalog sources |
| `cutout_coverage_summary.csv` | Exact-footprint counterpart counts per evaluation cutout ($N=1,500$) |
| `detector_stratified_coverage.csv` | Coverage percentages stratified across Detectors 1 through 6 |
| `catalog_combination_coverage.csv` | Venn/Boolean coverage combinations (Gaia, 2MASS, CatWISE) |
| `false_positive_external_evidence_audit.csv` | In-depth audit of all 45 baseline false-alarm cutouts |
| `task_4_19A_projection_verification.csv` | Empirical audit vs Task 4.19A projected coverage estimates |
| `geometry_reconciliation.md` | Formal mathematical audit reconciling Task 4.17 undersized cones |
| `scientific_limitations.md` | Astrometric, resolution, and completeness limitation analysis |
| `data_integrity_manifest.json` | Cryptographic SHA-256 checksums of all input and output files |
| `reproducibility_instructions.md` | This operational manual |
| `task_4_19B_closeout_report.md` | Final comprehensive audit report and certified verdict |

---

### 5. Regression Testing & Production Safety Audit

Verify that zero regression occurred and protected production model weights, checkpoints, and evaluation labels remain unaltered:

```powershell
# Run the complete test suite
.\.venv_validation\Scripts\python.exe -m pytest tests/ -q
# Expected: 270 passed in ~30s
```

Verify SHA-256 integrity of protected production assets:
```powershell
Get-FileHash -Algorithm SHA256 checkpoints/astrovision_spatial_v3.pt
# Expected: 3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99

Get-FileHash -Algorithm SHA256 checkpoints/spectra_masked_ae_v2.pt
# Expected: 6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938

Get-FileHash -Algorithm SHA256 data/processed/spectra/spectra_v2_provisional_thresholds_v1.json
# Expected: D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848
```

