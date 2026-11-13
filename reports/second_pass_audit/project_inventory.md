# SPECTRA-X: Initial Project Inventory & Environment Audit

**Audit Execution Timestamp**: `2026-11-01T23:02:18.944031+00:00`

## 1. System and Scientific Environment

- **Operating System**: Windows (AMD64)
- **Python Version**: `3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)]`
- **PyTorch Version**: `2.11.0+cu128`
- **CUDA Available**: `True`
- **GPU Hardware**: `NVIDIA GeForce RTX 5060`
- **Astropy Version**: `8.0.2`
- **NumPy Version**: `2.5.4`
- **SciPy Version**: `1.18.1`
- **Pandas Version**: `3.1.0`
- **Reproject Version**: `0.21.0`

## 2. Quantitative Summary

- **Total Project Volume**: 5.2599 GB (5,647,795,647 bytes)
- **Total Data Directory Volume**: 5.1948 GB (5,577,836,001 bytes)
- **Total Data Files**: 205
- **Total FITS Files**: 177
- **Total Checkpoint Files**: 2
- **Total Existing Scripts Inspected**: 18
- **Total Manifest Files**: 8

## 3. Data Storage Breakdown by Release and Category

| Category | Subdirectory | File Count | Size (MB) | Size (GB) |
| :--- | :--- | :---: | :---: | :---: |
| QR2 Level-2 Wide | `data/spherex/qr2/level2/` | 12 | 819.79 | 0.8006 |
| QR2 Level-2 Deep | `data/spherex/qr2_deep/level2/` | 4 | 273.26 | 0.2669 |
| QR2 Calibration | `data/spherex/qr2/calibration/` | 74 | 1561.73 | 1.5251 |
| QR3 Level-2 Wide | `data/spherex/qr3/level2/` | 12 | 743.71 | 0.7263 |
| QR3 Level-2 Deep | `data/spherex/qr3_deep/level2/` | 4 | 252.23 | 0.2463 |
| QR3 Calibration | `data/spherex/qr3/calibration/` | 77 | 1580.17 | 1.5431 |
| QR3 Templates | `data/spherex/qr3/templates/` | 11 | 85.05 | 0.0831 |
| External Catalogs | `data/external/` | 8 | 3.50 | 0.0034 |
| Processed Data | `data/processed/` | 3 | 0.00 | 0.0000 |
| **Total Data** | `data/` | **205** | **5319.44** | **5.1948** |

## 4. Checkpoints and Model Artifacts

- `[checkpoints\astrovision_latest.pt](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/checkpoints/astrovision_latest.pt)` (3.28 MB)
- `[checkpoints\spectra_latest.pt](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/checkpoints/spectra_latest.pt)` (0.10 MB)

## 5. Existing Python Scripts and Preprocessing Pipelines

| Script Path | Lines | Size (KB) | Blanket Flag Masking (`FLAGS != 0`) |
| :--- | :---: | :---: | :---: |
| `[inspect_fits_structure.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/inspect_fits_structure.py)` | 44 | 1.2 | No |
| `[inspect_spectral_table.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/inspect_spectral_table.py)` | 63 | 1.7 | No |
| `[models/astrovision/model.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/astrovision/model.py)` | 85 | 3.4 | YES (Needs scientific refinement) |
| `[models/astrovision/train_astrovision.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/astrovision/train_astrovision.py)` | 104 | 4.0 | No |
| `[models/chronos_x/model.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/chronos_x/model.py)` | 56 | 2.4 | YES (Needs scientific refinement) |
| `[models/chronos_x/run_temporal_differencing.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/chronos_x/run_temporal_differencing.py)` | 68 | 2.8 | No |
| `[models/fusion_x/model.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/fusion_x/model.py)` | 54 | 2.0 | No |
| `[models/fusion_x/rank_anomalies.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/fusion_x/rank_anomalies.py)` | 75 | 2.7 | No |
| `[models/motion_x/model.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/motion_x/model.py)` | 55 | 2.2 | No |
| `[models/motion_x/validate_motion.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/motion_x/validate_motion.py)` | 48 | 1.5 | No |
| `[models/spectra/model.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/spectra/model.py)` | 53 | 1.8 | No |
| `[models/spectra/train_spectra.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/models/spectra/train_spectra.py)` | 76 | 2.6 | No |
| `[scratch/inspect_test.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scratch/inspect_test.py)` | 35 | 1.7 | No |
| `[scripts/download_manager.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/download_manager.py)` | 721 | 32.8 | No |
| `[scripts/generate_manifest.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/generate_manifest.py)` | 120 | 4.7 | No |
| `[scripts/inspect_fits.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/inspect_fits.py)` | 308 | 11.5 | No |
| `[scripts/storage_report.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/storage_report.py)` | 123 | 4.3 | No |
| `[scripts/verify_downloads.py](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/scripts/verify_downloads.py)` | 157 | 4.8 | No |

## 6. Manifests and Logs Inspected

- `[manifests\calibration_manifest.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/calibration_manifest.csv)` (28.5 KB)
- `[manifests\download_log.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/download_log.csv)` (59.8 KB)
- `[manifests\download_plan.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/download_plan.csv)` (83.1 KB)
- `[manifests\external_manifest.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/external_manifest.csv)` (3.6 KB)
- `[manifests\fits_validation_catalog.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/fits_validation_catalog.csv)` (59.7 KB)
- `[manifests\qr2_manifest.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/qr2_manifest.csv)` (16.6 KB)
- `[manifests\qr3_manifest.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/qr3_manifest.csv)` (19.2 KB)
- `[manifests\spherex_inventory.csv](file:///C:/Users/blues/OneDrive/Desktop/New folder (7)/SPECTRA-X/manifests/spherex_inventory.csv)` (133.0 KB)

