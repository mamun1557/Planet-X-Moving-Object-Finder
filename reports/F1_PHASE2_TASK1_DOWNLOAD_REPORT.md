# SPECTRA-X / F1 — PHASE 2, TASK 1: LEVEL-2 SCIENCE FITS DOWNLOAD REPORT
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE & VERIFIED

---

## 1. Executive Summary

In accordance with the Phase 1 Data Acquisition Plan, Phase 2 Task 1 executed the targeted acquisition of all 19 remote Level-2 science FITS exposures for **Pointing 0003, Detectors D2–D6** from the official NASA IRSA SPHEREx S3 archive.

### Summary Metrics:
- **Expected Remote Files:** 19
- **Successfully Downloaded Files:** 19 (100.0% completion)
- **Failed / Corrupt Downloads:** 0
- **Total Downloaded Volume:** **1,215,417,600 bytes (1.132 GB)**
- **Total Download Duration:** 665.5 seconds (Mean transfer speed: ~1.83 MB/s)
- **Local Storage Path:** [`data/spherex/qr3/level2/`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/spherex/qr3/level2/)
- **Machine-Readable Manifest:** [`data/manifests/f1_phase2_download_manifest.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_phase2_download_manifest.csv)

---

## 2. Pre-Download Verification

Prior to file retrieval, an automated HTTP HEAD audit was performed against the remote S3 endpoints:
- **Base Archive URL:** `https://nasa-irsa-spherex.s3.amazonaws.com/qr3/level2/2026W30_1B/l2b-v27-2026-222/`
- **Integrity Check:** All 19 expected objects returned HTTP `200 OK` with valid `Content-Length` and `ETag` headers.
- **Flight Pipeline Verification (2D3):** An explicit HEAD request for `2D3` returned HTTP `404 Not Found`, independently verifying the Phase 1 finding that Dither 2 of Detector 3 was omitted during flight survey scheduling or quality screening.
- **Pre-existing Local Files:** Pointing 0003 had 4 pre-existing D1 science files; zero D2–D6 files were present locally.

---

## 3. Atomic Download Execution Log

Downloads were managed by [`scripts/download_pointing_0003_d2_d6.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/download_pointing_0003_d2_d6.py). Each file was streamed in 1 MB blocks to an atomic temporary `.part` file, byte-verified against remote `Content-Length`, and renamed upon complete transfer.

| Detector | Dither | Remote Object Key | File Size (Bytes) | Elapsed (s) | Transfer Rate | Status |
| :---: | :---: | :--- | :---: | :---: | :---: | :---: |
| **D2** | 1 | `2/level2_2026W30_1B_0003_1D2_spx_l2b-v27-2026-222.fits` | 66,133,440 | 49.4 | 1.28 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D2** | 2 | `2/level2_2026W30_1B_0003_2D2_spx_l2b-v27-2026-222.fits` | 61,355,520 | 36.7 | 1.60 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D2** | 3 | `2/level2_2026W30_1B_0003_3D2_spx_l2b-v27-2026-222.fits` | 61,318,080 | 25.4 | 2.30 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D2** | 4 | `2/level2_2026W30_1B_0003_4D2_spx_l2b-v27-2026-222.fits` | 61,562,880 | 19.9 | 2.95 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D3** | 1 | `3/level2_2026W30_1B_0003_1D3_spx_l2b-v27-2026-222.fits` | 67,420,800 | 26.0 | 2.48 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D3** | 3 | `3/level2_2026W30_1B_0003_3D3_spx_l2b-v27-2026-222.fits` | 63,861,120 | 27.1 | 2.24 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D3** | 4 | `3/level2_2026W30_1B_0003_4D3_spx_l2b-v27-2026-222.fits` | 63,864,000 | 56.6 | 1.08 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D4** | 1 | `4/level2_2026W30_1B_0003_1D4_spx_l2b-v27-2026-222.fits` | 66,450,240 | 26.3 | 2.41 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D4** | 2 | `4/level2_2026W30_1B_0003_2D4_spx_l2b-v27-2026-222.fits` | 59,716,800 | 21.3 | 2.67 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D4** | 3 | `4/level2_2026W30_1B_0003_3D4_spx_l2b-v27-2026-222.fits` | 59,002,560 | 44.2 | 1.27 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D4** | 4 | `4/level2_2026W30_1B_0003_4D4_spx_l2b-v27-2026-222.fits` | 59,186,880 | 27.9 | 2.02 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D5** | 1 | `5/level2_2026W30_1B_0003_1D5_spx_l2b-v27-2026-222.fits` | 68,057,280 | 37.5 | 1.73 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D5** | 2 | `5/level2_2026W30_1B_0003_2D5_spx_l2b-v27-2026-222.fits` | 63,766,080 | 43.3 | 1.41 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D5** | 3 | `5/level2_2026W30_1B_0003_3D5_spx_l2b-v27-2026-222.fits` | 63,463,680 | 25.0 | 2.42 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D5** | 4 | `5/level2_2026W30_1B_0003_4D5_spx_l2b-v27-2026-222.fits` | 63,777,600 | 32.6 | 1.86 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D6** | 1 | `6/level2_2026W30_1B_0003_1D6_spx_l2b-v27-2026-222.fits` | 68,996,160 | 33.3 | 1.97 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D6** | 2 | `6/level2_2026W30_1B_0003_2D6_spx_l2b-v27-2026-222.fits` | 65,931,840 | 42.5 | 1.48 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D6** | 3 | `6/level2_2026W30_1B_0003_3D6_spx_l2b-v27-2026-222.fits` | 65,764,800 | 37.4 | 1.68 MB/s | **`DOWNLOADED_SUCCESS`** |
| **D6** | 4 | `6/level2_2026W30_1B_0003_4D6_spx_l2b-v27-2026-222.fits` | 65,787,840 | 34.1 | 1.84 MB/s | **`DOWNLOADED_SUCCESS`** |

---

## 4. Current Pointing 0003 Physical Inventory

With the successful ingestion of these 19 files, the local Level-2 storage for Pointing 0003 contains **23 complete FITS science files**:
- **D1 (Bands 1–17):** 4 files (`1D1`, `2D1`, `3D1`, `4D1`) — 251.8 MB
- **D2 (Bands 18–34):** 4 files (`1D2`, `2D2`, `3D2`, `4D2`) — 250.4 MB
- **D3 (Bands 35–51):** 3 files (`1D3`, `3D3`, `4D3`) — 195.1 MB
- **D4 (Bands 52–68):** 4 files (`1D4`, `2D4`, `3D4`, `4D4`) — 244.4 MB
- **D5 (Bands 69–85):** 4 files (`1D5`, `2D5`, `3D5`, `4D5`) — 259.1 MB
- **D6 (Bands 86–102):** 4 files (`1D6`, `2D6`, `3D6`, `4D6`) — 266.5 MB
- **Total Pointing 0003 Physical Volume:** **1,467,272,400 bytes (1.366 GB)**

---

## 5. Audit Finding

The download phase has concluded with **zero errors, zero missing files from the manifest, and zero data corruption**. The dataset is ready for deep Astropy header and scientific array validation.
