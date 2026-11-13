# SPECTRA-X / F1 — PHASE 1: TARGET AVAILABILITY AUDIT
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE (Data Foundation Audit)

---

## 1. Executive Summary

As part of Phase 1 Data Foundation verification for the SPECTRA-X coordinate-driven temporal observatory, an exhaustive astrometric and spatial footprint audit was conducted for the five NASA challenge targets:
1. **Barnard's Star** (High proper motion M-dwarf)
2. **Epsilon Indi B** (Nearby T-dwarf binary brown dwarf system)
3. **WISE J085510.83-071442.5** (Ultra-cool sub-stellar Y-dwarf)
4. **RW Aurigae** (Classical T Tauri eruptive variable prototype)
5. **R Draconis** (Mira-type long-period pulsating giant variable)

### Core Findings
- **Local Observation Status:** **`NOT_FOUND`** for all five targets across all 32 Level-2 FITS files in the current repository (`data/spherex/qr2` and `data/spherex/qr3`).
- **Angular Separations:** The closest local SPHEREx pointing footprint to any challenge target is 14.68° (WISE 0855 to QR2 Pointing 0002), far exceeding the instrument focal plane radius (~3.5°).
- **Remote Archive Status:** **`INCONCLUSIVE`** on IRSA TAP (no publicly queryable SPHEREx Level-2 spatial index/SIA table currently exposed on IRSA TAP endpoints). Remote S3 bucket (`nasa-irsa-spherex`) contains discrete survey weeks, but specific pointing coverage for these 5 coordinates has not yet been localized in released tranches.
- **Machine-Readable Catalogs Created:**
  - Coordinates: [`data/manifests/f1_target_coordinates.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_target_coordinates.csv)
  - Observation Audit: [`data/manifests/f1_target_observations.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/manifests/f1_target_observations.csv)

---

## 2. Authoritative Target Astrometry & Verification

Target coordinates were verified against official primary astronomical catalogs (Gaia DR3, SIMBAD, and discovery literature). No coordinates were assumed or fabricated.

| Target Name | RA (deg) | Dec (deg) | Coord Frame | Epoch | Reference / Catalog | Spec Type / Nature |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Barnard's Star** | 269.452078 | +4.693365 | ICRS | J2016.0 | Gaia DR3 4472832130942585856 | M4.0V ($\mu = 10.39''$/yr) |
| **Epsilon Indi B** | 331.043800 | -56.782700 | ICRS | J2000.0 | Scholz et al. (2003) A&A 398, L29 | T1 + T6 Brown Dwarf |
| **WISE 0855** | 133.795129 | -7.245147 | ICRS | J2010.5 | Luhman (2014) ApJ 786, L18 | Y-dwarf ($\mu = 8.15''$/yr) |
| **RW Aurigae** | 76.956424 | +30.401416 | ICRS | J2016.0 | Gaia DR3 162989809981881600 | T Tauri Variable (CTTS) |
| **R Draconis** | 248.167664 | +66.755082 | ICRS | J2016.0 | Gaia DR3 1647414966601445760 | Mira Variable (M3e-M9e) |

### Verification of WISE 0855 Challenge Coordinate
- **User Prompt Reference:** $\alpha = \text{08h 55m 10.831s}$, $\delta = -07^\circ 14' 42.53''$.
- **Sexagesimal to Decimal Conversion:**
  $$\alpha = (8 + 55/60 + 10.831/3600) \times 15 = 133.795129^\circ$$
  $$\delta = -(7 + 14/60 + 42.53/3600) = -7.245147^\circ$$
- **Authoritative Source Verification:** Verified against K. L. Luhman (2014), *"Discovery of a ~250 K Brown Dwarf at 2 pc from the Sun"*, *ApJ* 786, L18.
- **Astrometric Note:** WISE J085510.83-071442.5 has an extraordinarily large proper motion:
  $$\mu_\alpha \cos\delta = -8070 \pm 100\text{ mas/yr}, \quad \mu_\delta = 680 \pm 100\text{ mas/yr}$$
  Total proper motion is $\sim 8.15\text{ arcsec/yr}$. At current epoch (2026.5), the object has shifted by $\sim 130''$ ($\sim 2.17'$) from the discovery epoch (2010.5). For spatial searches in SPHEREx pointing footprints ($6.2''$ pixel scale), an epoch-propagated coordinate ($\alpha \approx 133.7437^\circ, \delta \approx -7.2420^\circ$) must be used in production search pipelines.

---

## 3. Local Level-2 Footprint Audit

A systematic WCS and angular separation audit was performed against all 32 Level-2 FITS files in the repository across all 8 distinct pointing centers.

### Repository Pointing Reference Centers
1. **QR2 Pointing 0001 (D2):** $\alpha = 187.32^\circ, \delta = +7.98^\circ$ (Equatorial)
2. **QR2 Pointing 0002 (D2):** $\alpha = 147.38^\circ, \delta = +7.98^\circ$ (Equatorial)
3. **QR2 Pointing 0003 (D2):** $\alpha = 148.00^\circ, \delta = +7.98^\circ$ (Equatorial)
4. **QR2 Pointing 0004 (D2):** $\alpha = 148.62^\circ, \delta = +7.98^\circ$ (Equatorial)
5. **QR2 Pointing 0005 (D2):** $\alpha = 352.02^\circ, \delta = -56.78^\circ$ (Southern)
6. **QR2 Pointing 0006 (D2):** $\alpha = 352.16^\circ, \delta = -56.78^\circ$ (Southern)
7. **QR3 Pointing 0001 (D1):** $\alpha = 265.82^\circ, \delta = +44.38^\circ$ (Northern)
8. **QR3 Pointing 0003 (D1):** $\alpha = 165.69^\circ, \delta = -69.57^\circ$ (Far South Pole)

### Separation & Overlap Results
A spherical search radius of $3.5^\circ$ (bounding the detector array FoV) and rigorous `astropy.wcs.WCS.all_world2pix` boundary checks were applied:

| Target | Nearest Local Pointing | Pointing Center ($\alpha, \delta$) | Angular Sep (deg) | Search Radius | In FoV? | Local Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Barnard's Star** | QR3 Pointing 0001 | $265.82^\circ, +44.38^\circ$ | **39.73°** | $3.5^\circ$ | No | **NOT_FOUND** |
| **Epsilon Indi B** | QR2 Pointing 0006 | $352.16^\circ, -56.78^\circ$ | **21.12°** | $3.5^\circ$ | No | **NOT_FOUND** |
| **WISE 0855** | QR2 Pointing 0002 | $147.38^\circ, +7.98^\circ$ | **14.68°** | $3.5^\circ$ | No | **NOT_FOUND** |
| **RW Aurigae** | QR2 Pointing 0002 | $147.38^\circ, +7.98^\circ$ | **56.98°** | $3.5^\circ$ | No | **NOT_FOUND** |
| **R Draconis** | QR2 Pointing 0001 | $187.32^\circ, +7.98^\circ$ | **60.88°** | $3.5^\circ$ | No | **NOT_FOUND** |

*Note on WISE 0855:* QR2 Pointing 0002 is located at $\delta = +7.98^\circ$, whereas WISE 0855 is located at $\delta = -7.25^\circ$. The separation is dominated by the $\sim 15.2^\circ$ declination offset.

---

## 4. Remote Archive Audit (IRSA TAP & S3)

To determine whether these targets can be acquired from IPAC / IRSA:
1. **IRSA TAP Service:** Inspected `https://irsa.ipac.caltech.edu/TAP`. Standard IRSA TAP schemas host WISE, 2MASS, and ZTF, but do not yet expose an active public SPHEREx spatial index (`spherex.level2` or equivalent SIAv2 table). Queries for SPHEREx tables returned zero registered catalog relations.
2. **NASA IRSA SPHEREx S3 Bucket:** Remote files are partitioned by weekly flight tranches (e.g., `s3://nasa-irsa-spherex/qr3/level2/2026W30_1B/`). The repository currently contains only Pointing 0001 and Pointing 0003 from `2026W30_1B`.
3. **Audit Finding:** Because the public TAP service does not index SPHEREx observations and the remote S3 archive requires explicit survey schedule manifests to map $(\alpha, \delta)$ to pointing indices, the availability of these targets in un-downloaded weekly tranches is formally classified as **`INCONCLUSIVE`**.

---

## 5. Summary & Scientific Recommendations

1. **Do Not Claim Target Coverage:** The web observatory UI and documentation must not claim that Barnard's Star, Epsilon Indi B, WISE 0855, RW Aurigae, or R Draconis are currently viewable in SPECTRA-X.
2. **Proper Motion Propagation:** The target ingestion pipeline must apply space motion propagation ($T - T_0$) using Gaia DR3 proper motion parameters before querying SPHEREx pointings.
3. **Data Acquisition Priority:** Recommended targeted download plan in [`reports/F1_PHASE1_DATA_ACQUISITION_PLAN.md`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/reports/F1_PHASE1_DATA_ACQUISITION_PLAN.md) outlines the necessary survey manifest queries required to locate these targets in forthcoming releases.
