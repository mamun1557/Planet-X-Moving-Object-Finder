# Reproducibility Instructions & Operational Protocol
## Phase 4, Task 4.19D — Independent Holdout Validation & Leakage Audit

**Module:** ASTROVISION  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10 on Windows)  

---

### 1. Environment Verification
```powershell
Set-Location "c:\Users\blues\OneDrive\Desktop\New folder (7)\SPECTRA-X"
.\.venv_validation\Scripts\python.exe --version
# Expected: Python 3.12.10
```

### 2. Execute Master Holdout Audit Engine
```powershell
.\.venv_validation\Scripts\python.exe -u scripts/validation/execute_task_4_19D_holdout_audit.py
```
*Expected runtime:* ~10 to 15 seconds.

### 3. Verify Regression Suite
```powershell
.\.venv_validation\Scripts\python.exe -m pytest tests/ -q
# Expected: 270 passed in ~30s
```

### 4. Verify Cryptographic Hashes of Protected Assets
```powershell
Get-FileHash -Algorithm SHA256 checkpoints/astrovision_spatial_v3.pt
# Expected: 3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99

Get-FileHash -Algorithm SHA256 checkpoints/spectra_masked_ae_v2.pt
# Expected: 6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938

Get-FileHash -Algorithm SHA256 data/processed/spectra/spectra_v2_provisional_thresholds_v1.json
# Expected: D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848
```
