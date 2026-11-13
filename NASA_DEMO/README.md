# SPECTRA-X Interactive Observatory — NASA Space Apps Demo Guide
## Portable Self-Installing Windows Demonstration Package

**Project:** SPECTRA-X (NASA Space Apps Challenge 2026 — F1 Challenge Track)  
**Pipeline Build:** `l2b-v27-2026-222`  
**Target Environment:** 64-bit Windows 10/11, Python 3.12 (preferred) / 3.10+, React 18 SPA  
**Classification:** NASA Demonstration & Interactive Science Verification MVP

---

## 1. Executive Summary

**SPECTRA-X** is an autonomous multi-modal machine learning discovery pipeline engineered for the NASA SPHEREx mission. It systematically detects spatial anomalies, temporal transients, and spectral outliers across all 102 spectroscopic channels and 6 infrared detector arrays ($0.75\,\mu\text{m} - 5.0\,\mu\text{m}$).

The **SPECTRA-X Interactive Observatory** couples the frozen Python scientific backend with a high-performance React 18 user interface. This portable package allows any evaluator, researcher, or NASA judge to run the full application on any compatible Windows PC with zero manual dependency wrestling.

---

## 2. One-Click Quick Start (Any Windows PC)

### Step 1: Copy or Clone the Repository
Copy the entire `SPECTRA-X` folder to your target Windows PC (to any folder or drive, e.g. `C:\SPECTRA-X`, `D:\Projects\SPECTRA-X`).

### Step 2: Ensure Python 3.12 is Installed
The only prerequisite on the target machine is **64-bit Python 3.12** (or 3.10+).
- **Download:** [Python 3.12 Windows Installer](https://www.python.org/downloads/release/python-31210/)
- **Or via Terminal:** `winget install Python.Python.3.12`
- *Important:* Ensure the checkbox **"Add python.exe to PATH"** is selected during installation.

### Step 3: Double-Click `START_DEMO.bat`
Navigate to the `NASA_DEMO` folder and double-click:
```text
SPECTRA-X\NASA_DEMO\START_DEMO.bat
```

### What Happens Automatically
1. **Automated Bootstrap:** If `.venv_demo` does not exist, `START_DEMO.bat` automatically invokes `SETUP_ENVIRONMENT.bat`.
2. **Environment Creation:** Creates an isolated virtual environment in `.venv_demo/`.
3. **Dependency Installation:** Automatically installs all required runtime packages from `requirements-demo.txt` (requires internet access on first launch).
4. **Hardware Verification:** Verifies PyTorch, checks for NVIDIA CUDA GPU acceleration, and falls back gracefully to CPU if no GPU is present.
5. **Port Conflict Detection:** Checks if port `8050` is already in use to prevent duplicate instances.
6. **Live Backend Launch:** Boots the scientific engine (`observatory/app.py`) in a dedicated console window.
7. **Browser Launch:** Once `/api/status` returns HTTP 200 OK, the launcher automatically opens your default web browser to:
   ```text
   http://127.0.0.1:8050/
   ```

---

## 3. Package File Structure

Inside `NASA_DEMO/`:

| File / Folder | Purpose |
| :--- | :--- |
| `START_DEMO.bat` | Primary one-click launcher. Handles auto-setup, preflight, readiness checks, and browser launch. |
| `SETUP_ENVIRONMENT.bat` | Standalone setup wizard. Creates `.venv_demo`, installs dependencies, and runs verification. |
| `requirements-demo.txt` | Minimal pinned runtime dependency manifest for Python 3.12. |
| `verify_environment.py` | Standalone verification engine testing tensor math, models, checkpoints, and data providers. |
| `README.md` | This user and architecture guide. |
| `sample_inputs/` | Genuine SPHEREx Level-2 FITS images, 102-channel SED vectors, and discovery catalogs. |

---

## 4. Hardware Acceleration & CUDA vs. CPU Behavior

SPECTRA-X is engineered for universal hardware compatibility:

- **With NVIDIA CUDA GPU:**
  PyTorch detects CUDA drivers and utilizes hardware GPU acceleration for tensor inference across ASTROVISION-X spatial autoencoders and SPECTRA-X spectral models.
- **Without GPU (CPU Fallback):**
  If no compatible NVIDIA GPU or CUDA driver is found, the system automatically activates its optimized CPU fallback engine. All model weights, difference imaging algorithms, and interactive queries run natively on CPU cores with sub-second response times.

---

## 5. Judge Walkthrough & Scientific Features

Once the browser opens at `http://127.0.0.1:8050/`, you can explore the 6 core scientific modules:

1. **Diagnostic Header:** Confirms backend status (`ONLINE`), active pipeline build (`l2b-v27-2026-222`), execution device (CUDA vs CPU), and 1,392 candidate detections.
2. **Multi-Module Filters:** Filter candidate discoveries by detector array (`D1`-`D6`), module (`ASTROVISION-X`, `CHRONOS-X`, `SPECTRA-AE`, `FUSION-X`, `NEBULA-X`), or anomaly score threshold.
3. **Primary Transient Target:** Select candidate `SPX-J163.6309-69.4422` to inspect its spatial coordinates ($\text{RA}=163.6318^\circ, \text{Dec}=-69.4421^\circ$) and cross-mission crossmatches (Gaia DR3 astrometry and AllWISE infrared counterparts).
4. **Multi-Band FITS Cutout Viewer:** Inspect the synchronized 6-detector image arrays, auroral emission templates, and low Earth orbit spacecraft glow templates.
5. **102-Channel SED Interactive Spectrum:** Explore the rest-frame spectral energy distribution, comparing observed SPHEREx flux against the frozen Masked Autoencoder baseline reconstruction.
6. **Human-in-the-Loop Review Disposition:** Record peer-review dispositions (`CONFIRMED_CANDIDATE`, `FALSE_POSITIVE`, `REQUIRES_FOLLOWUP`), enter notes, and save decisions persistently to `data/human_reviews.json`.

---

## 6. How to Shut Down

To stop the Observatory application:
- Simply close the dedicated console window titled **`SPECTRA-X Observatory Backend (Port 8050)`**, or
- Press `Ctrl+C` inside that server console window.

---

## 7. Manual Maintenance & Troubleshooting

### Reinstalling or Resetting the Environment
To force a clean re-installation of `.venv_demo`:
1. Delete the `.venv_demo` directory in the repository root.
2. Double-click `NASA_DEMO\SETUP_ENVIRONMENT.bat`.

### Verifying Scientific Integrity
To run the automated verification suite directly:
```cmd
.venv_demo\Scripts\python.exe NASA_DEMO\verify_environment.py
```

### Port 8050 In Use
If another local service is using port 8050, launch on an alternative port:
```cmd
.venv_demo\Scripts\python.exe observatory\app.py --port 8080
```
Then navigate to `http://127.0.0.1:8080/`.

### Node.js Note for Evaluators
Target PCs do **NOT** require Node.js or npm. The React frontend is pre-compiled into static HTML5/CSS/JS located in `frontend/dist/` and served directly by the unified Python backend.

---

## 8. Frozen Scientific Asset Integrity

All scientific checkpoints and detection thresholds remain strictly frozen and verified:

| File | SHA-256 Hash |
| :--- | :--- |
| `checkpoints/astrovision_spatial_v3.pt` | `3b608e496f43c2648c9dc8236e1a7f5b5ed4b7906cf900468c65c67016042d99` |
| `checkpoints/spectra_masked_ae_v2.pt` | `6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938` |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848` |
