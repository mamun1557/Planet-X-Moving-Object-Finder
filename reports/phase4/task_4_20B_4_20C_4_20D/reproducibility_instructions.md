# Reproducibility Instructions & Verification Guide
## Phase 4 Combined Engineering Sprint (Tasks 4.20B + 4.20C + 4.20D)

**Pipeline Build:** `l2b-v27-2026-222`  
**Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10 on Windows)  
**Baseline Test Count:** 270 passed  
**New Sprint Test Count:** 32 passed  
**Total Target Test Count:** 302 passed  

---

### 1. Environment Verification

Ensure execution inside `.venv_validation`:
```powershell
# In PowerShell:
.\.venv_validation\Scripts\python.exe --version
# Expected: Python 3.12.10
```

---

### 2. Protected Production Asset Integrity Verification

Run the integrity verification script:
```powershell
.\.venv_validation\Scripts\python.exe -c "
import hashlib
assets = {
    'checkpoints/astrovision_spatial_v3.pt': '3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99',
    'checkpoints/spectra_masked_ae_v2.pt': '6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938',
    'data/processed/spectra/spectra_v2_provisional_thresholds_v1.json': 'D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848'
}
for path, expected in assets.items():
    h = hashlib.sha256(open(path, 'rb').read()).hexdigest().upper()
    assert h == expected, f'Checksum mismatch on {path}'
    print(f'Pristine: {path}')
print('All protected assets verified bit-for-bit identical.')
"
```

---

### 3. Targeted Test Execution (Tasks 4.20B, 4.20C, 4.20D)

Run the 32 new unit and validation tests:
```powershell
# Task 4.20B: MOTION-X Keplerian Ephemeris Engine (11 tests)
.\.venv_validation\Scripts\python.exe -m pytest tests/test_motion_x_keplerian_ephemeris.py -v

# Task 4.20C: SPECTRA Multi-Catalog Infrared Integration (10 tests)
.\.venv_validation\Scripts\python.exe -m pytest tests/test_spectra_multicatalog_integration.py -v

# Task 4.20D: CHRONOS-X Sub-Pixel Phase-Correlation Registration (11 tests)
.\.venv_validation\Scripts\python.exe -m pytest tests/test_chronos_x_subpixel_registration.py -v

# Run all 32 sprint tests together:
.\.venv_validation\Scripts\python.exe -m pytest tests/test_motion_x_keplerian_ephemeris.py tests/test_spectra_multicatalog_integration.py tests/test_chronos_x_subpixel_registration.py -v
```

---

### 4. Full Regression Suite Execution

Verify that all 302 tests pass cleanly with zero regressions:
```powershell
.\.venv_validation\Scripts\python.exe -m pytest tests/ -q
# Expected: 302 passed in ~30s
```
