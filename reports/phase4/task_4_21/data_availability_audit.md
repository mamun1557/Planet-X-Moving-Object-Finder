# SPECTRA-X / F1 — Phase 4, Task 4.21
# Comprehensive Astronomical Data Availability & Archive Census Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation` (Python 3.12.10)  
**Parent Tasks:** Phase 4 Tasks 4.12, 4.15, 4.17, 4.18, 4.19B, 4.19D, 4.20A–E  
**Audit Timestamp:** {datetime.now(timezone.utc).isoformat()}  
**Governance:** STRICT READ-ONLY / BLIND EVALUATION ISOLATION / ZERO MUTATION  

---

## 1. Executive Summary & Audit Mandate

In accordance with the **Phase 4, Task 4.21** pre-freeze directive, a comprehensive audit was executed across all internal SPHEREx data repositories and external astronomical survey archives to establish:
1. What additional real-sky observations exist within the workspace.
2. What external survey catalogs have been acquired and verified.
3. Whether sufficient suitable data exist to justify model retraining before the **November 10, 2026** hard freeze deadline.

```
====================================================================================================
                        ASTRONOMICAL DATA AVAILABILITY CENSUS SUMMARY                               
====================================================================================================
  Total Internal SPHEREx Level-2 FITS Files:         315 Files Across QR2 (v20) and QR3 (v27)
  Separated Calibration Cohort (P0001, P0008):       48 Science FITS / 1,000 Cutouts (Quarantined)
  Blind Evaluation Cohort (P0002, P0009, P0010):     72 Science FITS / 1,500 Cutouts (Quarantined)
  Eligible Training Corpus Outside Quarantine:       35 Science FITS (P0003, 0004, 0005, 1B, 4B)
  Unused / Unobserved SPHEREx Science FITS Files:    0 FILES (All 35 Eligible Files Already Utilized)
  External Catalogs Acquired (Task 4.19B):           Gaia DR3 (682,713 rows), 2MASS (18,349), CatWISE (74,489)
  External Solar System / Transient Catalogs:        JPL Horizons (5 NEOs), JPL SBDB (5,000), ZTF BTS (1,250)
  Real-Sky Ground Truth Anomaly Labels:              ZERO (Real Sky is Entirely Unlabeled)
----------------------------------------------------------------------------------------------------
  DATA AVAILABILITY VERDICT:                         INSUFFICIENT_DATA_FOR_SAFE_RETRAINING
====================================================================================================
```

---

## 2. Internal SPHEREx Product Census

The repository contains 315 multi-extension FITS files organized across builds and pointings:

| Subdirectory | Pipeline Build | File Count | Pointing Identifiers | Governance Partition Role |
| :--- | :---: | :---: | :---: | :--- |
| `data/spherex/multipointing_pilot/level2/0001` | `l2b-v27-2026-222` | 24 | P0001 (Field 1, 2, 3) | **CALIBRATION ONLY (Quarantined)** |
| `data/spherex/multipointing_pilot/level2/0008` | `l2b-v27-2026-222` | 24 | P0008 (Ecliptic Crossing) | **CALIBRATION ONLY (Quarantined)** |
| `data/spherex/multipointing_pilot/level2/0002` | `l2b-v27-2026-222` | 24 | P0002 (Mod Extinction) | **BLIND EVALUATION (Quarantined)** |
| `data/spherex/multipointing_pilot/level2/0009` | `l2b-v27-2026-222` | 24 | P0009 (Galactic Disk) | **BLIND EVALUATION (Quarantined)** |
| `data/spherex/multipointing_pilot/level2/0010` | `l2b-v27-2026-222` | 24 | P0010 (NEP Polar Field) | **BLIND EVALUATION (Quarantined)** |
| `data/spherex/qr3/level2` | `l2b-v27-2026-222` | 31 | P0003 (23), P0004 (2), P0005 (2), 1B (4) | **Eligible Training Corpus** |
| `data/spherex/qr3_deep` & `qr2_deep` | `v20 / v27` | 8 | Deep 1B, 4B Exposures | **Eligible Training Corpus** |
| `data/spherex/qr2/level2` | `l2b-v20-2025-240` | 12 | P0001, P0002 (Legacy v20) | Legacy Deprecated Build |
| Calibration Matrices (dark, nonfunc, sip, psf) | `v20 / v27` | 144 | All Detectors D1–D6 | Instrument Static Calibration |

**Critical Audit Conclusion:**  
Every single eligible Level-2 science FITS file outside the quarantined cohorts (35 files total) was already fully harvested in Task 1.1U to construct the 1,200 training patches for ASTROVISION V3. There are **zero unobserved Level-2 SPHEREx science files** remaining in the local environment.

---

## 3. External Astronomical Survey Catalogs

The external survey catalogs acquired in Tasks 4.17, 4.19B, and 4.20B-D provide comprehensive crossmatch coverage:

1. **Gaia DR3 (`gaia_dr3_raw_acquired.csv`):**  
   682,713 sources across the exact 1,500 evaluation cutout footprints. Includes high-precision astrometry ($\sigma < 0.1\text{ mas}$), $G, G_{\text{BP}}, G_{\text{RP}}$ photometry, parallax, and proper motions.
2. **2MASS PSC (`twomass_raw_fps.csv`):**  
   18,349 point sources providing $J, H, K_s$ near-infrared photometry (1.25, 1.65, 2.16 µm).
3. **CatWISE2020 (`catwise2020_raw_fps.csv`):**  
   74,489 mid-infrared sources providing $W1$ (3.4 µm) and $W2$ (4.6 µm) photometry.
4. **JPL Horizons & SBDB (`jpl_sbdb_asteroid_orbits.json`):**  
   Orbital elements for 5,000 known minor planets and high-precision topocentric ephemerides for key near-Earth asteroids.
5. **ZTF Bright Transient Survey (`ztf_bright_transient_survey.csv`):**  
   1,250 confirmed supernovae, tidal disruption events, and optical transients.

---

## 4. Ground-Truth Anomaly Label Deficit

While billions of astronomical sources exist in public archives, **zero verified ground-truth anomaly labels** exist for real SPHEREx infrared observations:
- Field stars, background galaxies, and zodiacal light gradients are unlabeled nominal sky.
- True astrophysical anomalies (e.g. ultra-cool brown dwarfs, dust-enshrouded YSOs, extreme transients) are unknown discoveries by definition.
- Existing performance benchmarks rely entirely on **synthetic anomaly injections** (400 spatial injections in ASTROVISION, 371 spectral injections in SPECTRA).

Retraining a deep neural network on unverified external catalog sources without ground-truth labels risks encoding catalog selection biases or spurious artifacts into the latent representation.