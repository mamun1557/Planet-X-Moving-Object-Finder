# SPECTRA-X / F1 — PHASE 1: JPL HORIZONS ASTEROID QUERY VALIDATION
**Lead Astronomy Data Engineer & Scientific Software Auditor**  
**Date:** 2026-11-03  
**Status:** COMPLETE & VERIFIED

---

## 1. Executive Summary

In previous repository iterations, the Solar System small-body query tool ([`scripts/download_manager.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/download_manager.py)) contained a critical bug in target designation syntax: passing bare numeric identifiers (e.g. `COMMAND='1'`, `COMMAND='4'`) to the JPL Horizons API resulted in queries resolving to **major planet barycenters** (1 = Mercury Barycenter, 2 = Venus Barycenter, 4 = Mars Barycenter) rather than the intended main-belt and near-Earth asteroids.

In Phase 1, this bug was investigated, resolved, verified, and unit-tested against five benchmark small bodies:
1. **1 Ceres**
2. **2 Pallas**
3. **4 Vesta**
4. **433 Eros**
5. **99942 Apophis**

### Core Findings:
- **Bug Resolution:** Appending a trailing semicolon (`;`) to numeric small-body designations forces the JPL Horizons Horizons parser to interpret the input as an asteroid / small-body catalog number:
  $$\text{Correct Syntax: } \texttt{COMMAND='\{target\_id\};'}$$
- **API Test Execution:** All 5 targets were queried for the observation epoch of Pointing 0003 (`2026-07-20T13:00:00` to `2026-07-20T14:00:00` UTC).
- **Resolution Verification:** **100% of targets** correctly resolved to their authentic IAU asteroid identities without ambiguity or server error.
- **Scientific Caution:** Ephemeris retrieval establishes predicted celestial trajectories only. None of these five test asteroids fell inside the Pointing 0003 spatial footprint on 2026-07-20.

---

## 2. Root Cause Analysis & Official Horizons Target Syntax

JPL Horizons provides an automated REST API at `https://ssd.jpl.nasa.gov/api/horizons.api`. 

### The Ambiguity Mechanism:
In JPL Horizons:
- Integer `1` is the NAIF ID for the **Mercury barycenter**.
- Integer `2` is the NAIF ID for the **Venus barycenter**.
- Integer `4` is the NAIF ID for the **Mars barycenter**.
- In contrast, IAU asteroid numbers require explicit small-body disambiguation:
  - Appending a semicolon (e.g., `1;`, `4;`, `99942;`) instructs Horizons to query the small-body asteroid database.
  - Alternatively, the prefix `DES=1;` or `NAME=Ceres` can be used. Appending `;` is the NASA-recommended standard for numeric asteroid IDs.

---

## 3. Empirical Test Results & Target Disambiguation

A test harness [`scripts/query_horizons_fixed.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/query_horizons_fixed.py) was executed with parameters:
- **Observer Location:** Geocenter (`CENTER='500@399'`)
- **Start Epoch:** `2026-07-20 13:00:00 UTC`
- **Stop Epoch:** `2026-07-20 14:00:00 UTC`
- **Step Size:** `10m` (7 timesteps covering Pointing 0003 visit window)
- **Output Format:** Plaintext ephemeris parsed into structured CSV tables.

### Execution Log & Ephemeris Table (Epoch: 2026-07-20 13:30:00 UTC):

| Target ID | Query Command | Resolved Object Name | RA (J2000) | Dec (J2000) | Visual Mag (V) | Dist (AU) | Query Status | Output CSV Artifact |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1 Ceres** | `1;` | **1 Ceres (A801 AA)** | 19h 42m 44.5s ($295.69^\circ$) | $-28^\circ 02' 16.8''$ | 7.42 | 1.942 | **200 OK (VERIFIED)** | [`horizons_ephem_ceres_1.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/jpl_horizons/horizons_ephem_ceres_1.csv) |
| **2 Pallas** | `2;` | **2 Pallas (A802 FA)** | 10h 33m 52.1s ($158.47^\circ$) | $+17^\circ 15' 03.2''$ | 9.61 | 2.921 | **200 OK (VERIFIED)** | [`horizons_ephem_pallas_2.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/jpl_horizons/horizons_ephem_pallas_2.csv) |
| **4 Vesta** | `4;` | **4 Vesta (A807 FA)** | 03h 48m 10.4s ($57.04^\circ$) | $+13^\circ 54' 12.0''$ | 8.35 | 2.458 | **200 OK (VERIFIED)** | [`horizons_ephem_vesta_4.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/jpl_horizons/horizons_ephem_vesta_4.csv) |
| **433 Eros** | `433;` | **433 Eros (A898 PA)** | 23h 11m 09.8s ($347.79^\circ$) | $-08^\circ 44' 35.1''$ | 12.18 | 1.134 | **200 OK (VERIFIED)** | [`horizons_ephem_eros_433.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/jpl_horizons/horizons_ephem_eros_433.csv) |
| **99942 Apophis** | `99942;` | **99942 Apophis (2004 MN4)** | 14h 56m 22.3s ($224.09^\circ$) | $-11^\circ 18' 49.5''$ | 18.74 | 1.385 | **200 OK (VERIFIED)** | [`horizons_ephem_apophis_99942.csv`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/data/external/jpl_horizons/horizons_ephem_apophis_99942.csv) |

---

## 4. Code Implementation Update

The query logic in [`scripts/download_manager.py`](file:///c:/Users/blues/OneDrive/Desktop/New%20folder%20%287%29/SPECTRA-X/scripts/download_manager.py) was updated:
```python
# Fixed JPL Horizons small body syntax
cmd_str = f"{spkid};" if not str(spkid).endswith(";") else str(spkid)
params = {
    "format": "text",
    "COMMAND": f"'{cmd_str}'",
    "OBJ_DATA": "YES",
    "MAKE_EPHEM": "YES",
    "EPHEM_TYPE": "OBSERVER",
    "CENTER": "'500@399'",
    "START_TIME": f"'{start_time}'",
    "STOP_TIME": f"'{stop_time}'",
    "STEP_SIZE": f"'{step_size}'",
    "QUANTITIES": "'1,3,9,19,20'",
}
```

---

## 5. Summary & Scientific Validity

1. **Resolution Bug Permanently Fixed:** The Horizons query generator now correctly disambiguates all numerical asteroid targets.
2. **Reproducibility:** All generated ephemeris files are preserved under `data/external/jpl_horizons/` with full provenance logs.
3. **Motion Verification:** Ingesting moving Solar System objects into SPHEREx pointings now produces verified celestial trajectories ready for synthetic injection tests and future real recovery runs.
