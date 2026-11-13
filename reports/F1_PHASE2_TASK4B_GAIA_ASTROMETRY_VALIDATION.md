# SPECTRA-X / F1 — PHASE 2, TASK 4B: GAIA ASTROMETRY VALIDATION
## Independent Audit of Proper-Motion Propagation, Astrometric Separation, & Error Covariance

**Role:** Independent Scientific Validation Engineer  
**Date:** 2026-11-04  
**Audit Status:** **VERIFIED_WITH_LIMITATIONS**  

---

## 1. Executive Summary

Phase 2, Task 4 cross-matched 1,132 SPHEREx Pointing 0003 sources against Gaia DR3 by propagating stellar positions from the Gaia DR3 catalog reference epoch (**J2016.0**) to the SPHEREx observation epoch (**2026.5496**, $\Delta t = +10.5496\,\text{years}$).

This independent forensic audit evaluates:
1. The mathematical and geometric validity of the proper-motion propagation algorithm.
2. The observation epoch derived from SPHEREx Level-2 FITS headers.
3. The numerical agreement against independent astrometric routines (Astropy `SkyCoord` and 3D great-circle motion).
4. The completeness of astrometric uncertainty propagation and the impact of omitting the Gaia $5 \times 5$ correlation matrix.
5. Discrepancies between the prose report statistics and actual database values.

---

## 2. Astrometric Epoch & Coordinate Frame Verification

### 1. Gaia Reference Epoch
- **Catalogue Reference Epoch:** **J2016.0** (TDB/ICRS). Confirmed via official ESA Gaia DR3 release specifications.

### 2. SPHEREx Observation Epoch
- Primary Level-2 FITS files in `data/spherex/qr3/level2/` (e.g. `level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits`) were inspected directly:
  ```fits
  DATE-OBS = '2026-07-20T00:26:21.423' / ISO-8601 time of observation
  MJD-OBS  =      61241.018303507 / [d] MJD of observation
  ```
- **Epoch Conversion:**
  - Gregorian day-of-year fraction: $t = 2026 + (200.0183 / 365.0) = \mathbf{2026.5480}$.
  - Julian standard epoch: $t_{\text{Julian}} = 2000.0 + (61241.0183 - 51544.5) / 365.25 = \mathbf{2026.5476}$.
  - Task 4 implemented: $t_{\text{SPX}} = \mathbf{2026.5496}$ ($\Delta t = 10.5496\,\text{yr}$).
  - **Audit Assessment:** The difference is $\Delta t_{\text{diff}} = 0.0020\,\text{yr}$ (approximately 17.5 hours). At the cohort maximum proper motion ($\mu \approx 215\,\text{mas/yr}$), this timing difference produces an offset of only $\mathbf{0.43\,\text{mas}}$ ($0.00043''$), which is less than $0.00007$ SPHEREx pixels. The epoch adopted in Task 4 is scientifically acceptable.

---

## 3. Mathematical & Geometric Formulation Audit

### 1. Proper-Motion Coordinate Shift
In Gaia DR3, proper motion in Right Ascension is reported as $\mu_{\alpha*} \equiv \mu_\alpha \cos\delta$ in units of $\text{mas/yr}$. The Task 4 implementation uses:
$$\Delta\alpha = \frac{\mu_{\alpha*} \cdot 10^{-3} \cdot \Delta t}{3600 \cdot \cos\delta_0} \quad [\text{degrees}]$$
$$\Delta\delta = \frac{\mu_\delta \cdot 10^{-3} \cdot \Delta t}{3600} \quad [\text{degrees}]$$
$$\alpha_{\text{prop}} = (\alpha_0 + \Delta\alpha) \pmod{360.0}, \quad \delta_{\text{prop}} = \delta_0 + \Delta\delta$$

**Verification:**
- The division by $\cos\delta_0$ correctly restores the angular displacement along the small circle of declination to coordinate degrees in Right Ascension.
- Sign conventions and units ($\text{mas/yr} \rightarrow \text{degrees}$) are mathematically exact.

### 2. Comparison Against Independent Astropy SkyCoord & Great-Circle Motion
Task 4 applied a first-order tangent-plane Euler update. Astropy's `SkyCoord.apply_space_motion` integrates 3D space motion along a great circle.

To evaluate higher-order geometric terms (which scale as $\frac{1}{2} \mu^2 \Delta t^2 \tan\delta$), an independent 3D great-circle vector propagation script was executed over all 1,114 matched sources:
- **Maximum Vector Offset:** **$17.8\,\mu\text{as}$** ($1.78 \times 10^{-5}$ arcseconds) for the most extreme proper motion star in the field ($\mu = 215.6\,\text{mas/yr}$ at $\delta \approx -71.1^\circ$).
- **Median Vector Offset:** **$< 0.05\,\mu\text{as}$** across the cohort.
- **Angular Separation Agreement:** Independent spherical Haversine calculations reproduced `sep_prop_arcsec` to $< 10^{-11}$ arcseconds.
- **Finding:** The first-order Euler approximation introduces zero discernible bias at SPHEREx resolution ($6.2''$ pixel scale).

---

## 4. Empirical Impact of Proper-Motion Propagation

An independent audit of [`data/processed/crossmatch/pointing_0003_gaia_dr3_matches.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/crossmatch/pointing_0003_gaia_dr3_matches.csv) yields the following metrics:

| Metric | Independent Calculation | Task 4 Reported Value | Audit Status |
| :--- | :---: | :---: | :--- |
| **Matched Sources ($d \le 4.0''$)** | **1,114** | 1,114 (98.4%) | **VERIFIED** |
| **Unpropagated Sources with $d \le 0.5''$** | **579** | 579 | **VERIFIED** |
| **Propagated Sources with $d \le 0.5''$** | **640** | 640 | **VERIFIED** |
| **Net Counterparts Gained at $\le 0.5''$** | **+61** | +61 | **VERIFIED** |
| **Median Unpropagated Separation ($d_{\text{orig}}$)** | **$0.4895''$** | $0.489''$ | **VERIFIED** |
| **Median Propagated Separation ($d_{\text{prop}}$)** | **$0.4585''$** | $0.458''$ | **VERIFIED** |
| **Sources with Measurable Proper Motion** | **1,103 (97.4%)** | 1,103 (97.4%) | **VERIFIED** |
| **Sources Missing Proper Motion** | **11 (1.0%)** | 11 (1.0%) | **VERIFIED** |

### Critical Discrepancy Catches in Reported Statistics:
1. **Median Proper Motion:**
   - **Task 4 Reported:** $|\mu| = 7.84\,\text{mas/yr}$ (yielding $82.7\,\text{mas}$ displacement).
   - **Forensic Recalculation:** The median of $|\mu_{\alpha*}|$ alone is $7.80\,\text{mas/yr}$. However, the true total 2D proper motion is $|\mu| = \sqrt{\mu_{\alpha*}^2 + \mu_\delta^2}$. The **actual median total proper motion is $8.77\,\text{mas/yr}$**, and the **true median net displacement is $92.49\,\text{mas}$** ($0.0925''$). Task 4 conflated the 1D RA component with total vector velocity.
2. **Maximum Proper Motion & Displacement:**
   - **Task 4 Reported:** Maximum proper motion $118.4\,\text{mas/yr}$, maximum displacement $1.249''$.
   - **Forensic Recalculation:** The true fastest mover in the catalog is **`SPX-J165.3661-71.1267`** (Gaia DR3 `5231111669359826176`):
     - $\mu_{\alpha*} = -215.54\,\text{mas/yr}$, $\mu_\delta = +5.55\,\text{mas/yr}$.
     - Total $|\mu| = \mathbf{215.61\,\text{mas/yr}}$.
     - Net 10.55-year displacement = $\mathbf{2.2746''}$ (more than 1/3 of a SPHEREx pixel!).
     - Before propagation: $d_{\text{orig}} = 2.162''$. After propagation: $d_{\text{prop}} = \mathbf{0.361''}$ (`HIGH_CONFIDENCE`).
   - The reported maximum of $118.4\,\text{mas/yr}$ missed the true maximum by nearly a factor of two.

---

## 5. Astrometric Error Covariance & Uncertainty Propagation Audit

### 1. Theoretical Covariance Formulation
Gaia DR3 publishes a 5-parameter astrometric solution with full correlation coefficients:
$$\boldsymbol{\rho} = \{\rho(\alpha, \delta), \rho(\alpha, \varpi), \rho(\alpha, \mu_{\alpha*}), \rho(\alpha, \mu_\delta), \rho(\delta, \varpi), \rho(\delta, \mu_{\alpha*}), \rho(\delta, \mu_\delta), \rho(\varpi, \mu_{\alpha*}), \rho(\varpi, \mu_\delta), \rho(\mu_{\alpha*}, \mu_\delta)\}$$

Rigorous propagated positional variance requires the cross-covariance term:
$$\sigma_{\alpha, \text{prop}}^2 = \sigma_{\alpha, 0}^2 + (\sigma_{\mu_{\alpha*}} \Delta t)^2 + 2 \, \Delta t \, \rho(\alpha, \mu_{\alpha*}) \sigma_{\alpha, 0} \sigma_{\mu_{\alpha*}}$$
$$\sigma_{\delta, \text{prop}}^2 = \sigma_{\delta, 0}^2 + (\sigma_{\mu_\delta} \Delta t)^2 + 2 \, \Delta t \, \rho(\delta, \mu_\delta) \sigma_{\delta, 0} \sigma_{\mu_\delta}$$

### 2. Audit Findings on Implementation:
1. **Unretrieved Correlations:** The ADQL TAP query executed in `scripts/crossmatch_gaia_allwise.py` only selected `ra_error`, `dec_error`, `pmra_error`, `pmdec_error`. The correlation coefficients were not retrieved.
2. **Independence Assumption:** Task 4's reported error equations (Report lines 40–42) explicitly assumed $\rho = 0$, dropping the $2 \Delta t \operatorname{Cov}(\alpha, \mu_\alpha)$ cross-term.
3. **Omission in CSV Output:** Although error equations were detailed in the markdown report, the calculated values $\sigma_{\alpha, \text{prop}}$ and $\sigma_{\text{pos}}$ were **never saved** to `pointing_0003_gaia_dr3_matches.csv`.
4. **Physical Impact:**
   - For typical stars in the cohort, $\sigma_{\alpha, 0} \sim 0.05\,\text{mas}$ and $\sigma_\mu \sim 0.06\,\text{mas/yr}$.
   - Over 10.55 years, $\sigma_{\mu} \Delta t \sim 0.6\,\text{mas}$. Even if correlation is maximal ($\rho = \pm 1$), the cross-term affects the uncertainty by $\le 0.06\,\text{mas}$ ($0.00006''$).
   - Because the matching beam radius is $0.5'' - 4.0''$ and SPHEREx centroiding jitter is $\sim 100 - 300\,\text{mas}$, the omission of covariance is astrometrically negligible for match identification, though it remains a formal methodological limitation.

### 3. Corrected Output:
The validated dataset [`data/processed/validation/pointing_0003_gaia_dr3_matches_validated.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/processed/validation/pointing_0003_gaia_dr3_matches_validated.csv) explicitly records `ra_prop_error_mas`, `dec_prop_error_mas`, `sigma_pos_propagated_arcsec`, and documents the independent error assumption.

---

## 6. Gaia Astrometry Audit Conclusion

The astrometric cross-matching of Pointing 0003 against Gaia DR3 is fundamentally sound. The 10.55-year proper-motion correction is verified to recover 61 genuine physical matches that would have otherwise fallen outside the strict $0.5''$ matching circle.

**Overall Gaia Astrometry Status:** **VERIFIED_WITH_LIMITATIONS**  
- First-order Euler propagation: VERIFIED (error $< 18\,\mu\text{as}$).  
- Net separation reduction and 61 gained matches: VERIFIED.  
- Component vs total proper motion conflation: DOCUMENTED & CORRECTED.  
- True maximum mover ($215.6\,\text{mas/yr}$): IDENTIFIED & AUDITED.  
- Covariance omission: DOCUMENTED AS FORMAL LIMITATION.

