# SPECTRA-X / F1 — PHASE 1: TARGETED DATA ACQUISITION PLAN
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE (Data Foundation Plan)

---

## 1. Executive Summary

Based on the empirical findings of the Phase 1 Data Foundation audits:
1. The existing 32 Level-2 FITS files in the repository provide only partial single-detector coverage (D2 for QR2, D1 for QR3).
2. Pointing 0003 is missing Detectors D2–D6, precluding true 102-band SED reconstruction.
3. Multi-month temporal repeat pairs do not exist locally, preventing end-to-end CHRONOS-X validation.
4. The 5 NASA challenge targets do not intersect local footprints.

To resolve these scientific blockers without downloading unmanageable archive volumes, this document establishes a **targeted, dependency-ordered data acquisition plan**. No bulk downloading was performed during this audit phase.

---

## 2. Priority Acquisition Tiers

```
   ┌────────────────────────────────────────────────────────┐
   │ TIER 1 (P0): Pointing 0003 D2–D6 Completion (~1.15 GB) │
   │ Purpose: Full 102-band SEDs for 1,392 sources          │
   └──────────────────────────┬─────────────────────────────┘
                              │
   ┌──────────────────────────▼─────────────────────────────┐
   │ TIER 2 (P0): Gaia DR3 Optical Reference (810 KB)       │
   │ Purpose: Astrometric alignment & cross-identification  │
   │ Status: ALREADY ACQUIRED (data/external/gaia_dr3/)     │
   └──────────────────────────┬─────────────────────────────┘
                              │
   ┌──────────────────────────▼─────────────────────────────┐
   │ TIER 3 (P1): Survey Pass 2 Pointing 0003 Revisit       │
   │ Purpose: Genuine 6-month temporal pair for CHRONOS-X   │
   └──────────────────────────┬─────────────────────────────┘
                              │
   ┌──────────────────────────▼─────────────────────────────┐
   │ TIER 4 (P2): Targeted NASA Challenge Target Pointings  │
   │ Purpose: Showcase targets (WISE 0855, Barnard's Star)  │
   └────────────────────────────────────────────────────────┘
```

---

## 3. Tier Details & Specifications

### Tier 1: Pointing 0003 D2–D6 Multi-Detector Completion (Priority: P0 - Critical)
- **Scientific Purpose:** Complete full 102-band spectrophotometric coverage ($0.75 - 5.00\,\mu\text{m}$) for the 1,392 sources in Pointing 0003. Validates the SPECTRA v2 neural classifier and Evidence Inspector on real multi-channel observations.
- **Target / Sky Region:** Center $\alpha = 165.6852^\circ, \delta = -69.5651^\circ$ (Deep South).
- **Observation Identifiers:** Tranche `2026W30_1B`, Pointing `0003`, Pipeline `l2b-v27-2026-222`.
- **Detectors & Band Coverage:**
  - D2: Bands 18–34 ($1.20 - 1.95\,\mu\text{m}$) — 4 files (`1D2`..`4D2`)
  - D3: Bands 35–51 ($1.95 - 2.80\,\mu\text{m}$) — 3 files (`1D3`, `3D3`, `4D3`)
  - D4: Bands 52–68 ($2.80 - 3.82\,\mu\text{m}$) — 4 files (`1D4`..`4D4`)
  - D5: Bands 69–85 ($3.82 - 4.42\,\mu\text{m}$) — 4 files (`1D5`..`4D5`)
  - D6: Bands 86–102 ($4.42 - 5.00\,\mu\text{m}$) — 4 files (`1D6`..`4D6`)
- **File Count:** Exactly 19 FITS files.
- **Estimated Download Size:** ~1.15 GB (~60 MB per compressed Level-2 file).
- **Download Source:** `https://nasa-irsa-spherex.s3.amazonaws.com/qr3/level2/2026W30_1B/l2b-v27-2026-222/`
- **Dependencies:** None. URLs and directory structures are verified and cataloged in [`data/manifests/f1_data_acquisition_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_data_acquisition_manifest.json).

### Tier 2: Pointing 0003 Astrometric Reference (Priority: P0 - Critical)
- **Scientific Purpose:** Precision astrometric distortion correction and photometric zero-point calibration for the web viewer.
- **Source:** Gaia DR3 cone search ($r = 2.5^\circ, G \le 20.5$).
- **File Count:** 1 CSV table (5,000 top astrometric anchors).
- **Size:** 810 KB.
- **Status:** **`ACQUIRED`** under [`data/external/gaia_dr3/gaia_pointing_0003_cone.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/gaia_dr3/gaia_pointing_0003_cone.csv).

### Tier 3: Pointing 0003 Survey Pass 2 Temporal Revisit (Priority: P1 - High)
- **Scientific Purpose:** Establish the first genuine multi-month temporal pair ($\Delta t \approx 180\text{ days}$) on identical sky coordinates to validate CHRONOS-X image differencing and transient detection without synthetic injection artifacts.
- **Target / Sky Region:** Center $\alpha \approx 165.7^\circ, \delta \approx -69.6^\circ$.
- **Observation Identifiers:** Survey Pass 2 flight period (e.g., `2027W04` / `2027W05`) covering the Southern Continuous Viewing Zone / deep ecliptic latitude.
- **Detectors & Band Coverage:** D1 and D2 (Bands 1–34) for temporal differencing.
- **File Count:** 8 FITS files (4 dithers $\times$ 2 detectors).
- **Estimated Size:** ~480 MB.
- **Download Source:** Caltech/IPAC IRSA SPHEREx Survey Pass 2 release.
- **Dependencies:** Availability of Pass 2 data tranches in IRSA archives.

### Tier 4: Challenge Target Ingestion (Priority: P2 - Medium)
- **Scientific Purpose:** Enable coordinate lookup and demonstration for the five NASA showcase targets (WISE 0855, Barnard's Star, etc.).
- **Target / Sky Region:** Pointings containing coordinates documented in [`data/manifests/f1_target_coordinates.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_target_coordinates.csv).
- **Estimated Size:** ~240 MB per target pointing visit (4 dither files per detector).
- **Dependencies:** Public release of IRSA SPHEREx pointing footprint schedule tables.

---

## 4. Machine-Readable Acquisition Manifest

All targeted remote file URLs, MD5 checksums (where available), detector mappings, and target paths have been organized into the machine-readable manifest:
[`data/manifests/f1_data_acquisition_manifest.json`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_data_acquisition_manifest.json).

An automated, rate-limited download execution script will be executed in Phase 2 using this manifest.
