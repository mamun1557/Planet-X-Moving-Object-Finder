# SPECTRA-X / F1 — Phase 4, Task 4.3
# Scientific Validation Environment — Architecture Options & Comparative Evaluation

**Pipeline Build:** `l2b-v27-2026-222`  
**Task Type:** STRICT READ-ONLY ENVIRONMENT AUDIT & VALIDATION INFRASTRUCTURE DESIGN  
**Project:** SPECTRA-X — Human-AI Co-Pilot for Exploring the Changing Infrared Sky  
**Audit Date:** 2026-11-07  
**Governance:** Zero Installation / Design & Comparison Only / Explicit Authorization Required  

---

## 1. Objective & Scope

This document provides a rigorous, evidence-based comparative evaluation of three architectural options for hosting the **SPECTRA-X Scientific Validation Environment** (`validation_env`):
- **Option A:** Dedicated Conda Environment (`spectra_val_env`)
- **Option B:** Isolated Python Virtual Environment (`.venv_validation`)
- **Option C:** Containerized Stack (NVIDIA AI Workbench / Docker Desktop / WSL)

The chosen environment must support independent validation across all five scientific components (ASTROVISION, SPECTRA, CHRONOS-X, MOTION-X, FUSION-X) while strictly guaranteeing:
1. Zero mutation of the existing Conda `dl` training environment.
2. Zero mutation of frozen model weights, thresholds, and checkpoints.
3. Clean access to NVIDIA GeForce RTX 5060 GPU acceleration.
4. Deterministic reproducibility and clear cohort governance.

---

## 2. Comparative Evaluation Matrix

| Evaluation Dimension | Option A: Conda (`spectra_val_env`) | Option B: Python venv (`.venv_validation`) | Option C: Container (Docker / WSL / Workbench) |
|---|---|---|---|
| **Underlying Interpreter** | Python 3.12 (via Miniconda3) | Python 3.12.10 (System Python base) | Linux Python 3.12 inside container |
| **CUDA / GPU Support** | **Full** (CUDA 13.2 / PyTorch cu132) | **Full** (Inherits native RTX 5060 CUDA 13.2) | **Fragile** (Requires WSL2 NVIDIA Container Toolkit) |
| **Project Code Compatibility** | **High** (Matches existing Conda `dl` style) | **High** (Matches active test environment) | **Moderate/Low** (Path translation Windows $\leftrightarrow$ Linux) |
| **Scientific Package Support** | **Excellent** (Pre-compiled conda-forge binaries) | **Excellent** (Pre-built Windows AMD64 PyPI wheels) | **High** (Standard Linux wheels) |
| **Storage Overhead** | $\sim 5 - 8\text{ GB}$ | $\sim 2 - 4\text{ GB}$ (Lightweight) | $\sim 15 - 25\text{ GB}$ (WSL VHDX + Docker Images) |
| **Setup Complexity** | Low to Moderate (Requires Conda in PATH) | **Minimal** (Single standard library command) | **Prohibitive** (Daemon, WSL permission blocks) |
| **Sandbox Accessibility** | Moderate (Requires binary whitelisting) | **High** (Local workspace directory) | **Blocked** (Access denied on config/daemon) |
| **Risk to Training Environment** | **Low** (Separate named environment) | **Zero** (Completely isolated directory tree) | **Low** (Isolated, but system virtualization risk) |
| **Maintenance Burden** | Moderate (Conda solver overhead) | **Low** (Pinned `requirements.txt` with hashes) | High (Docker lifecycle, port mapping, WDDM) |

---

## 3. In-Depth Analysis by Option

### 3.1 Option A: Dedicated Conda Environment (`spectra_val_env`)

- **Architecture:** Initialize a new Conda environment under `C:\Users\blues\miniconda3\envs\spectra_val_env` running Python 3.12 with pinned packages.
- **Strengths:**
  - Complete segregation from system Python site-packages.
  - Native management of C/C++ libraries (e.g., CFITSIO, WCSLIB, OpenBLAS) via `conda-forge`.
  - Consistent with the existing model-training environment `dl`.
- **Trade-Offs & Bottlenecks:**
  - Conda executable is located in `C:\Users\blues\miniconda3`, which is outside the active system PATH and subject to path whitelisting in sandboxed environments.
  - Larger disk footprint ($\sim 6 - 8\text{ GB}$) due to duplicate base runtime libraries.

---

### 3.2 Option B: Isolated Python Virtual Environment (`.venv_validation`) — RECOMMENDED

- **Architecture:** Create a lightweight, isolated virtual environment directly within the project workspace or designated tools directory using the verified Python 3.12.10 interpreter:
  `python -m venv .venv_validation`
- **Strengths:**
  - **Zero Setup Friction:** Relies strictly on Python standard library `venv`, requiring zero external management tools or path reconfigurations.
  - **Native GPU Acceleration:** Seamlessly utilizes the host's NVIDIA GeForce RTX 5060 GPU and CUDA 13.2 runtime without container translation overhead.
  - **Complete Isolation:** Strictly segregated from the Conda `dl` training environment, guaranteeing zero possibility of package cross-talk or accidental retraining.
  - **Minimal Disk Footprint:** Requires only $\sim 2.5\text{ GB}$ for all additional validation packages (`reproject`, `astroquery`, `scikit-learn`, `requests`).
  - **Deterministic Pip Pinning:** Enables strict hash-checked dependency installation via `requirements_validation.txt`.
- **Trade-Offs & Bottlenecks:**
  - Depends on pre-compiled binary wheels on PyPI for Windows AMD64 (all required packages—`astropy`, `scipy`, `reproject`, `scikit-learn`—provide standard binary wheels for Windows Python 3.12).

---

### 3.3 Option C: Containerized Stack (NVIDIA AI Workbench / Docker Desktop / WSL) — REJECTED

- **Architecture:** Package the validation environment into an OCI container running on Docker Desktop or NVIDIA AI Workbench via WSL2.
- **Why Option C is Unviable for this Workstation:**
  1. **Active Permission Blocks:** Direct inspection of Docker Desktop returned access denial on `C:\Users\blues\.docker\config.json`.
  2. **WSL Service Block:** Querying WSL returned `Access is denied (Error code: Wsl/E_ACCESSDENIED)`.
  3. **Workbench Absence:** The `nvbench` CLI is not installed or configured on this machine.
  4. **Prohibitive Virtualization Overhead:** WSL2 file I/O translation across Windows drives (`/mnt/c/`) introduces severe throughput bottlenecks when reading large SPHEREx FITS images ($102\text{ spectral channels} \times 2048 \times 2048$).
  5. **Governance Constraint:** The project owner mandate explicitly orders: *"Do not attempt to repair or reinstall Workbench."*

---

## 4. Definitive Architectural Recommendation

### Primary Recommendation: **Option B (Isolated Python venv `.venv_validation`)**

#### Scientific & Engineering Justification:
1. **Proven Hardware Compatibility:** Environment 1 (System Python 3.12.10) is already verified to interface directly with the NVIDIA GeForce RTX 5060 GPU, Blackwell Compute Capability `(12, 0)`, and CUDA 13.2. A dedicated venv inherits this validated hardware interface with zero configuration risk.
2. **Impenetrable Isolation:** Housing the validation environment in `.venv_validation` completely decouples validation testing from the Conda `dl` training environment. Training pipelines, frozen autoencoder checkpoints, and existing model weights remain 100% untouched.
3. **Reproducibility via Pinned Manifests:** All dependencies will be specified with exact version numbers and SHA-256 hashes in a dedicated `requirements_validation.txt`, ensuring exact deterministic reproducibility.
4. **Zero Administrative Friction:** Unlike Docker or WSL, standard Python virtual environments execute natively on Windows AMD64 without triggering virtualization permission errors or daemon dependencies.

#### Secondary Alternative:
If the project owner prefers central Conda package management across the workstation, **Option A (`spectra_val_env`)** is fully documented as a viable secondary alternative, requiring only the invocation of `C:\Users\blues\miniconda3\condabin\conda.bat`.

