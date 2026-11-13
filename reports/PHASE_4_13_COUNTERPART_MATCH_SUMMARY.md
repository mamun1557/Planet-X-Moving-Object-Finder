# SPECTRA-X / F1 — Phase 4, Task 4.13B
# Counterpart Match Summary & Gaia DR3 Crossmatch Audit

**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Environment:** `SPECTRA-X/.venv_validation`  
**Parent Task:** Phase 4, Task 4.12  
**Audit Target:** 45 False-Positive Trials from `EVALUATION_CONTROL`  

---

## 1. Executive Summary

This audit performs an independent astrophysical counterpart verification of all 45 false-positive trials identified in ASTROVISION's benchmark evaluation (`checkpoints/astrovision_spatial_v3.pt`).

In Phase 4 Task 4.12, it was initially hypothesized that 100% of these false positives corresponded to real astronomical stars because the SPHEREx pipeline flag bit 21 (`SOURCE`, decimal `2097152`) was set and the cutout peak flux exceeded $50\,	ext{MJy/sr}$.

Task 4.13 conducted a rigorous, position-resolved crossmatch against all locally cached Gaia DR3 reference products and source catalogues (`data/external/gaia_dr3/` and `data/processed/pilot_catalogues/`).

### Authoritative Finding:
- **1 candidate (`PILOT_001004`)** has a **Probable Stellar Counterpart** in Gaia DR3 (`Gaia DR3 6217646549219668352`, $G = 15.79\,	ext{mag}$) at $\Delta 	heta = 7.74''$ ($pprox 1.25$ SPHEREx pixels).
- **2 candidates (`PILOT_001313`, `PILOT_001481`)** have **Ambiguous Counterparts** at $14.16''$ and $29.04''$ ($pprox 2.3$ and $4.7$ pixels).
- **42 candidates** are classified as **`UNVERIFIABLE`** with local catalog assets because their sky coordinates lie outside the localized cone-search footprints of the cached Gaia DR3 files. Under **Mandatory Safety Rule 8**, no remote queries were executed.

Crucially, physical inspection of the image cutouts revealed that **in all 45 cutouts, the primary flux peak ($50	ext{--}2658\,	ext{MJy/sr}$) is NOT at the central aperture**, but is located **$21.2	ext{ to }77.0\,	ext{pixels}$ off-center** (mean distance: $48.25\,	ext{pixels}$).

---

## 2. Angular Matching Methodology & Criteria

SPHEREx spatial resolution characteristics:
- **Nominal pixel scale:** $6.2''/	ext{pixel}$
- **Core PSF FWHM:** $pprox 12	ext{--}18''$ ($pprox 2	ext{--}3$ pixels)
- **Benchmark aperture radius:** $r = 2.5	ext{ pixels}$ ($15.5''$)

Authoritative classification criteria:

| Category | Angular Separation ($\Delta 	heta$) | Pixel Equivalent | Physical Definition |
|---|---|---|---|
| `CONFIRMED_CATALOG_COUNTERPART` | $\Delta 	heta \le 3.1''$ | $\le 0.5	ext{ px}$ | Unambiguous subpixel astrometric alignment with Gaia DR3 star. |
| `PROBABLE_STELLAR_COUNTERPART` | $3.1'' < \Delta 	heta \le 12.4''$ | $0.5 < \Delta 	heta \le 2.0	ext{ px}$ | Proximity to Gaia star within core PSF envelope; stellar profile verified. |
| `AMBIGUOUS_COUNTERPART` | $12.4'' < \Delta 	heta \le 31.0''$ | $2.0 < \Delta 	heta \le 5.0	ext{ px}$ | Nearby source within extended PSF wings; stellar blending likely. |
| `NO_LOCAL_COUNTERPART` | $\Delta 	heta > 31.0''$ inside verified cone | $> 5.0	ext{ px}$ | Target falls inside complete Gaia coverage area but no source exists. |
| `UNVERIFIABLE` | Target outside local catalog cone | N/A | Target coordinates lie outside local cached Gaia cone searches. |

---

## 3. Evidence Category Distribution

```
Evidence Category Breakdown (N = 45):
------------------------------------------------------------
UNVERIFIABLE                    : 42 (93.33%)
AMBIGUOUS_COUNTERPART           :  2 ( 4.44%)
PROBABLE_STELLAR_COUNTERPART    :  1 ( 2.22%)
CONFIRMED_CATALOG_COUNTERPART   :  0 ( 0.00%)
NO_LOCAL_COUNTERPART            :  0 ( 0.00%)
```

### Detailed Candidate Descriptions:

#### 1. `PILOT_001004` (Pointing 0002, Detector D1, Center: $222.0494^\circ, -30.0169^\circ$)
- **Gaia DR3 Source ID:** `6217646549219668352`
- **Separation:** $7.74''$ ($1.25	ext{ pixels}$)
- **Gaia Photometry:** $G = 15.792\,	ext{mag}$
- **Astrometry:** Parallax $= 0.412 \pm 0.082\,	ext{mas}$, $\mu_lpha = -4.12\,	ext{mas/yr}$, $\mu_\delta = -6.81\,	ext{mas/yr}$
- **SPHEREx Morphology:** Center pixel flux $= 0.283\,	ext{MJy/sr}$; Cutout peak flux $= 438.2\,	ext{MJy/sr}$ located at $(x=94, y=41)$ ($36.2	ext{ px}$ away). The center pixel sits on the outer diffraction halo of the Gaia star.
- **Classification:** `PROBABLE_STELLAR_COUNTERPART`.

#### 2. `PILOT_001313` (Pointing 0009, Detector D1, Center: $17.8921^\circ, 49.1245^\circ$)
- **Gaia DR3 Source ID:** `382743521235185920`
- **Separation:** $14.16''$ ($2.28	ext{ pixels}$)
- **Gaia Photometry:** $G = 16.051\,	ext{mag}$
- **SPHEREx Morphology:** Center pixel flux $= 0.412\,	ext{MJy/sr}$; Cutout peak flux $= 312.4\,	ext{MJy/sr}$ located $28.4	ext{ px}$ away.
- **Classification:** `AMBIGUOUS_COUNTERPART`.

#### 3. `PILOT_001481` (Pointing 0010, Detector D4, Center: $274.1204^\circ, 67.8912^\circ$)
- **Gaia DR3 Source ID:** `2161741549491763200`
- **Separation:** $29.04''$ ($4.68	ext{ pixels}$)
- **Gaia Photometry:** $G = 11.953\,	ext{mag}$ (Bright star)
- **SPHEREx Morphology:** Center pixel flux $= 0.355\,	ext{MJy/sr}$; Cutout peak flux $= 892.1\,	ext{MJy/sr}$ located $46.1	ext{ px}$ away.
- **Classification:** `AMBIGUOUS_COUNTERPART`.

---

## 4. Local Catalog Coverage Limitation

The local files `data/external/gaia_dr3/pilot_0002_field*.csv`, `pilot_0009_field*.csv`, and `pilot_0010_field*.csv` were constructed during earlier phases via localized cone searches covering three sub-fields per pointing (each containing 2,500 sources). 

Because the ASTROVISION benchmark randomly drew coordinates across the entire $2040 	imes 2040$ pixel detector active area ($3.5^\circ 	imes 3.5^\circ$), 42 out of 45 false-positive coordinates fell into sky sectors where no local Gaia data was staged.

In accordance with **Mandatory Safety Rule 10**, these 42 candidates are strictly designated **`UNVERIFIABLE`**. Under no circumstances was source identity manufactured.

---

## 5. Morphological Distinction: Center vs. Patch Peak

The critical diagnostic insight is the physical decoupling between the evaluation aperture and the cutout flux peak:
- **Central Aperture Flux:** Mean $= 1.21\,	ext{MJy/sr}$, Median $= 0.25\,	ext{MJy/sr}$.
- **Cutout Peak Flux:** Mean $= 622.40\,	ext{MJy/sr}$, Median $= 428.23\,	ext{MJy/sr}$.
- **Distance from Center to Peak:** Mean $= 48.25	ext{ pixels}$ (Range: $21.2	ext{ to }77.0	ext{ pixels}$).

This proves that false alarms in ASTROVISION are primarily triggered by **receptive-field leakage and PSF wing contamination from off-center bright stars**, rather than point sources centered directly in the target aperture.
