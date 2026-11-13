# SPECTRA-X / F1 — PHASE 2, TASK 4: GAIA DR3 CROSS-MATCH REPORT
## Proper-Motion Propagation, Astrometric Separation, & Match Categorization
**Lead Astronomical Data Scientist & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE & AUDITED

---

## 1. Executive Summary

All 1,132 Pointing 0003 sources with simultaneous D1+D4 coverage were cross-matched against Gaia DR3 using rigorous astrometric proper-motion propagation from the Gaia reference epoch (**J2016.0**) to the SPHEREx observation epoch (**2026.5496**, $\Delta t = +10.5496\,\text{years}$).

### Headline Cross-Match Findings:
- **Output Artifact:** [`data/processed/crossmatch/pointing_0003_gaia_dr3_matches.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/crossmatch/pointing_0003_gaia_dr3_matches.csv) (1,132 rows).
- **Match Rate:** **1,114 sources (98.4%)** have a detected Gaia DR3 candidate within $4.0''$.
- **High-Confidence Matches ($d_{\text{prop}} \le 0.5''$, Clean Astrometry):** **598 sources (52.8%)**.
- **Probable Matches ($0.5'' < d_{\text{prop}} \le 1.5''$):** **410 sources (36.2%)**.
- **Quality-Rejected Astrometry (RUWE $> 2.0$):** **72 sources (6.4%)**.
- **Ambiguous Matches (Multiple Competing Sources in Beam):** **34 sources (3.0%)**.
- **Unmatched Sources (No Candidate within $4.0''$):** **18 sources (1.6%)**.
- **Impact of Proper-Motion Propagation:** Propagating coordinates over the 10.55-year baseline reduced the median angular separation from $0.489''$ to **$0.458''$** and brought **61 additional stars** into the strict $0.5''$ matching threshold.

---

## 2. Proper-Motion Propagation Methodology

### 1. Astronomical Formulation
Gaia DR3 astrometry is referenced to epoch $t_0 = 2016.0$ (TDB/ICRS). SPHEREx Level-2 images were acquired on $t_{\text{SPX}} = 2026-07-20\text{T}00:26:21$ (Decimal year **2026.5496**).

The 10.5496-year coordinate shift is calculated as:
$$\Delta\alpha = \frac{\mu_{\alpha*} \cdot 10^{-3} \cdot \Delta t}{3600 \cdot \cos(\delta_0)} \quad [\text{degrees}]$$
$$\Delta\delta = \frac{\mu_\delta \cdot 10^{-3} \cdot \Delta t}{3600} \quad [\text{degrees}]$$
where $\mu_{\alpha*} = \mu_\alpha \cos(\delta_0)$ is the proper motion in RA in $\text{mas/yr}$, and $\mu_\delta$ is the proper motion in Dec in $\text{mas/yr}$.

Propagated coordinates:
$$\alpha_{\text{prop}} = (\alpha_0 + \Delta\alpha) \pmod{360.0}, \quad \delta_{\text{prop}} = \delta_0 + \Delta\delta$$

### 2. Astrometric Error Propagation
The positional uncertainty at the observation epoch combines centroid uncertainty with proper-motion error:
$$\sigma_{\alpha, \text{prop}} = \sqrt{\left(\frac{\sigma_{\alpha, 0}}{1000}\right)^2 + \left(\frac{\sigma_{\mu_{\alpha*}}}{1000} \cdot \Delta t\right)^2} \quad [\text{arcsec}]$$
$$\sigma_{\delta, \text{prop}} = \sqrt{\left(\frac{\sigma_{\delta, 0}}{1000}\right)^2 + \left(\frac{\sigma_{\mu_\delta}}{1000} \cdot \Delta t\right)^2} \quad [\text{arcsec}]$$
$$\sigma_{\text{pos}} = \sqrt{\sigma_{\alpha, \text{prop}}^2 + \sigma_{\delta, \text{prop}}^2}$$

### 3. Exact Angular Separation
Separation is computed using the spherical Haversine formula:
$$\Delta\theta = 2 \arcsin \sqrt{ \sin^2\left(\frac{\delta_{\text{prop}} - \delta_{\text{SPX}}}{2}\right) + \cos(\delta_{\text{SPX}})\cos(\delta_{\text{prop}})\sin^2\left(\frac{\alpha_{\text{prop}} - \alpha_{\text{SPX}}}{2}\right) } \times 3600''$$

Independent verification against `astropy.coordinates.SkyCoord.separation` confirms numerical agreement to $< 10^{-11}$ arcseconds.

---

## 3. Match Categories & Distribution

| Category | Count | Fraction (%) | Criteria & Physical Interpretation |
| :--- | :---: | :---: | :--- |
| **`HIGH_CONFIDENCE`** | **598** | **52.8%** | $d_{\text{prop}} \le 0.50''$, clean astrometry ($\text{RUWE} \le 2.0$), isolated counterpart. |
| **`PROBABLE`** | **410** | **36.2%** | $0.50'' < d_{\text{prop}} \le 1.50''$ within SPHEREx beam, or isolated wide match ($1.5'' - 4.0''$). |
| **`QUALITY_REJECTED`** | **72** | **6.4%** | Counterpart detected, but $\text{RUWE} > 2.0$ (severe astrometric wobble, binary disturbance, or photocenter shifts). |
| **`AMBIGUOUS`** | **34** | **3.0%** | Multiple competing Gaia sources within $2.0''$ with $\Delta d < 0.6''$ (crowded field / blended flux). |
| **`UNMATCHED`** | **18** | **1.6%** | Zero Gaia DR3 stars detected within $4.0''$ search radius ($G > 21$ mag or heavily dust-obscured). |
| **Total** | **1,132** | **100.0%** | Comprehensive source accounting |

---

## 4. Empirical Impact of Proper-Motion Propagation

- **Sources with Verified Proper Motion:** **1,103 sources (97.4%)** had measurable $\mu_{\alpha*}, \mu_\delta$ in Gaia DR3.
- **Median Proper Motion:** $|\mu| = 7.84\,\text{mas/yr}$ (Maximum: $118.4\,\text{mas/yr}$).
- **Median Net Displacement ($10.55\,\text{yr}$):** $82.7\,\text{mas}$ ($0.083''$).
- **Maximum Net Displacement:** **$1.249''$** (over two full SPHEREx pixels!).
- **Threshold Shift:**
  - Unpropagated sources with $d_{\text{orig}} \le 0.50''$: **579 sources**.
  - Propagated sources with $d_{\text{prop}} \le 0.50''$: **640 sources**.
  - **Net Gain:** **61 genuine physical matches** would have been erroneously classified as wide or probable matches without proper-motion correction.

### Example Case Study:
- **Source:** `SPX-J162.0204-69.1848`
  - Proper motion: $\mu_{\alpha*} = -16.11\,\text{mas/yr}$, $\mu_\delta = +1.44\,\text{mas/yr}$.
  - Unpropagated Separation: $0.201''$.
  - Propagated Separation: **$0.148''$** (improved by $53\,\text{mas}$, matching SPHEREx centroid to sub-pixel accuracy).

---

## 5. Astrometric Quality Analysis (RUWE & Parallax)

The Renormalised Unit Weight Error (RUWE) measures single-star astrometric fit quality:
- **Median RUWE:** **$0.959$** (astrometrically pristine single-star solutions).
- **Interquartile Range:** $[0.877, 1.072]$.
- **RUWE $> 1.4$ (Elevated Astrometric Scatter):** **141 sources (12.5%)**.
- **RUWE $> 2.0$ (Severe Binarity / Photocenter Jitter):** **72 sources (6.4%)**, isolated into `QUALITY_REJECTED`.

### Parallax Distribution:
- **Median Parallax:** $\varpi = 0.651\,\text{mas}$ (characteristic distance $d \sim 1.54\,\text{kpc}$).
- **Parallax SNR $\ge 3.0$ (Calibrated Distances):** **983 sources (86.8%)**.
- **Parallax SNR $< 2.0$ (Distant / Low-Precision):** **120 sources (10.6%)**.

---

## 6. Conclusion

Gaia DR3 provides an exceptionally solid astrometric anchor for Pointing 0003, with 89.0% of sources verified as high-confidence or probable physical counterparts once 10.55-year proper-motion drift is applied.
