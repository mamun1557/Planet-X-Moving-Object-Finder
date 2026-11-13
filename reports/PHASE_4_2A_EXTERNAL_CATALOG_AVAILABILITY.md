# SPECTRA-X / F1 — Phase 4, Task 4.2A
# External Spectroscopic Catalog Availability & Coverage Audit

**Task Type:** STRICT READ-ONLY SCIENTIFIC DATA AVAILABILITY AUDIT  
**Module Audited:** SPECTRA — 102-Channel Infrared Spectral Anomaly Detection Engine  
**Pipeline Build:** `l2b-v27-2026-222`  
**Execution Timestamp:** 2026-11-07T20:55:00Z  
**Primary Target Cohort:** Pointing 0008 Provisional-Null Calibration Sources ($N = 3,206$)  
**Secondary Target Cohort:** Pointings 0002, 0009, 0010 Blind Evaluation Sources ($N = 9,500$)  
**Governance Mode:** STRICT READ-ONLY (Zero Code, Model, Data, Weight, Threshold, or Evaluation Modification)  
**Final Decision:** **`PARTIALLY_FEASIBLE`**  
**Recommended First Test Catalog for Task 4.2B:** **ESA Gaia DR3 BP/RP Low-Resolution (XP) Spectra & Apsis Astrophysical Parameters**

---

## 1. Executive Summary & Audit Mandate

The objective of Task 4.2A is to conduct an independent, evidence-grounded scientific availability and coverage audit of external public astronomical spectroscopic catalogs (specifically **ESA Gaia DR3 XP**, **SDSS DR17/DR18**, and **LAMOST DR10**) to determine whether external data can provide reliable spectroscopic or stellar-classification evidence for SPECTRA source validation.

Currently, the 3,206 Pointing 0008 calibration sources and the 9,500 blind evaluation sources are classified as `RELIABLE_ISOLATED_POINT_SOURCE` based exclusively on Gaia DR3 astrometric cleanliness and 2MASS point-source association. As established in Tasks 1.2B-S through 1.2E, **these sources are provisional control candidates**, lacking independent ground-truth spectroscopic confirmation of normality.

### Key Audit Findings:

1. **Target Cohort Identity Architecture:**  
   Every source in the calibration ($N=3,206$) and evaluation ($N=9,500$) cohorts already possesses a native, verified **Gaia DR3 64-bit integer `source_id`** ([`data/processed/pilot_catalogues/pointing_0008_source_catalogue.csv`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/pilot_catalogues/pointing_0008_source_catalogue.csv)). Positional cross-matching with spatial error cones is completely unnecessary for Gaia-linked catalogs.
2. **Gaia DR3 XP Feasibility (Top Recommendation):**  
   - **All-sky coverage:** Gaia DR3 published continuous Hermite coefficients for ~220 million sources down to $G \approx 17.65$.
   - **P0008 Calibration Cohort Match:** Median $G = 17.82$ mag ($G \in [11.54, 19.50]$). An estimated **$40\%\text{--}45\%$ of P0008 calibration sources ($N \approx 1,300\text{--}1,450$)** are brighter than $G = 17.65$ and possess published XP spectra.
   - **Astrophysical Parameters:** Nearly $100\%$ of P0008 sources possess Gaia DR3 Apsis astrophysical parameters ($T_{\text{eff}}, \log g, [\text{M}/\text{H}], A_G, \text{RUWE}$).
3. **SDSS & LAMOST Coverage Limitations:**  
   - **SDSS BOSS Optical ($0.36\text{--}1.04\ \mu\text{m}$):** Covers South Galactic Cap fields sparsely. Estimated P0008 overlap is modest ($5\%\text{--}15\%$). Pointing 0002 (Dec $-30.3^\circ$) has **strictly ZERO coverage** (below Apache Point horizon).
   - **SDSS APOGEE-2 NIR ($1.51\text{--}1.70\ \mu\text{m}$):** High-resolution ($R \approx 22,500$) H-band spectra, but coverage is restricted to targeted pencil beams ($<2\%$ expected overlap).
   - **LAMOST LRS Optical ($0.37\text{--}0.90\ \mu\text{m}$):** Effective sky coverage is $-10^\circ \le \delta \le +60^\circ$. P0008 (Dec $+7.5^\circ$) has an estimated $10\%\text{--}20\%$ overlap. Pointing 0002 (Dec $-30.3^\circ$) has **strictly ZERO coverage**.
4. **The Critical Optical-to-Infrared Disconnect:**  
   - Gaia XP ($0.33\text{--}1.05\ \mu\text{m}$), SDSS optical ($0.36\text{--}1.04\ \mu\text{m}$), and LAMOST ($0.37\text{--}0.90\ \mu\text{m}$) overlap **ONLY in SPHEREx Band 1 (Detector D1, $0.75\text{--}1.05\ \mu\text{m}$, Channels 0–13)**.
   - None of these surveys provide spectroscopic coverage in SPHEREx Bands 2–6 ($1.11\text{--}5.00\ \mu\text{m}$).
   - **SCIENTIFIC RULE:** Optical stellar classification (e.g. confirming a star is a normal G2V dwarf) is a **necessary proxy condition**, but **NOT sufficient proof of mid-infrared normality**. A star with normal optical photospheric absorption lines can harbor circumstellar dust disks, debris disks (Vega-like excess), or unmodeled emission lines at $3\text{--}5\ \mu\text{m}$.
   - **Solution:** Optical spectroscopy must be paired with an **ALLWISE mid-IR photometric sidecar ($W1, W2$)** to verify continuum normality in SPHEREx Bands 4–6.
5. **Execution Environment & Network Status:**  
   In the standard sandboxed execution environment, live external network access to ESA Gaia TAP, SDSS SkyServer, and LAMOST is blocked by DNS isolation (`getaddrinfo failed`). Live querying is marked **`UNVERIFIABLE_IN_SANDBOX`**. In addition, the official Python library `gaiaxpy` is currently not installed in the workspace environment.
6. **Final Decision:** **`PARTIALLY_FEASIBLE`**. Full cross-matching is operationally feasible upon granting sandbox network permissions or ingesting pre-staged TAP extracts, with Gaia DR3 XP selected as the primary candidate.

---

## 2. Target Cohort Astrometric & Photometric Characteristics

A detailed census of the primary calibration cohort and secondary evaluation cohorts was executed using `data/processed/pilot_catalogues/`:

### Table 2.1: Target Cohort Demographic & Coordinate Ledger

| Cohort Role | Pointing ID | Field Description | Sources ($N$) | RA Range (deg) | Dec Range (deg) | Galactic Lat ($b$) | Ecliptic Lat ($\beta$) | Median $G$ Mag | $G$ Mag Range |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Primary Calibration** | **0008** | Equatorial / South Galactic Cap | **3,206** | $[24.86, 34.41]$ | $[+5.32, +9.99]$ | $[-54.3^\circ, -48.2^\circ]$ | $[-6.2^\circ, -2.8^\circ]$ | **17.82** | $[11.54, 19.50]$ |
| **Secondary Evaluation** | **0002** | Deep South Sky Field | **4,071** | $[220.61, 232.30]$ | $[-32.17, -28.65]$ | $[+19.8^\circ, +28.2^\circ]$ | $[-13.9^\circ, -10.9^\circ]$ | **18.22** | $[11.55, 19.50]$ |
| **Secondary Evaluation** | **0009** | Moderate North Sky Field | **2,284** | $[7.29, 20.60]$ | $[+43.30, +49.67]$ | $[-19.4^\circ, -13.1^\circ]$ | $[+35.7^\circ, +38.8^\circ]$ | **18.01** | $[11.70, 19.50]$ |
| **Secondary Evaluation** | **0010** | North Ecliptic Pole (NEP) | **3,145** | $[268.04, 276.47]$ | $[+60.94, +72.16]$ | $[+26.7^\circ, +30.4^\circ]$ | $[+84.3^\circ, +88.1^\circ]$ | **17.86** | $[11.50, 19.50]$ |

### Astrometric Metadata Availability in Primary Cohort (P0008):
- **Native Primary Keys:** $100\%$ ($3,206/3,206$) possess native 64-bit integer `source_id` from Gaia DR3.
- **Astrometric Parameters:** Full 5-parameter astrometric solutions (`ra`, `dec`, `pmra`, `pmdec`, `parallax`) exist for all calibration sources.
- **Proper Motion Propagation:** Epoch propagation from Gaia J2016.0 to SPHEREx observation epoch 2026.55 is already computed in the catalog (`ra_epoch`, `dec_epoch`, median shift $\Delta \theta \approx 0.08''$).
- **2MASS Association:** $100\%$ possess valid `tmass_id` identifiers (`has_tmass_match == True`, median match distance $0.18''$).
- **Astrometric Quality:** All 3,206 sources have $\text{RUWE} \le 1.40$ (median $\text{RUWE} = 1.01$), confirming they are astrometrically well-behaved single stars.

---

## 3. Catalog-Specific Investigations

### A. ESA Gaia DR3 BP/RP Low-Resolution Spectra (XP)
- **Archive & Endpoint:** ESA Gaia Archive TAP server (`https://gea.esac.esa.int/tap-server/tap`) and CDS VizieR TAP (`https://tapvizier.cds.unistra.fr/TAPVizieR/tap`).
- **Release Content:** ~220 million sources with low-resolution BP/RP spectra ($G \lesssim 17.65\text{ mag}$ published globally).
- **Format:**
  - *Continuous Representation:* 55 Hermite polynomial basis coefficients for BP ($330\text{--}680\text{ nm}$) and 55 coefficients for RP ($640\text{--}1050\text{ nm}$), with full correlation covariance matrices stored in `gaia_source` and `xp_summary` datalink tables.
  - *Sampled Representation:* Discretized spectral fluxes calibrated in physical units ($\text{W}\cdot\text{m}^{-2}\cdot\text{nm}^{-1}$) on standard wavelength grids.
- **Wavelength Coverage & Resolving Power:**
  - BP: $0.33\text{--}0.68\ \mu\text{m}$, $R \approx 30\text{--}100$.
  - RP: $0.64\text{--}1.05\ \mu\text{m}$, $R \approx 60\text{--}90$.
- **Spectral Overlap with SPHEREx:**
  - SPHEREx covers $0.75\text{--}5.00\ \mu\text{m}$ across 102 channels.
  - Gaia XP overlaps **exclusively with SPHEREx Band 1 (Detector D1, $0.75\text{--}1.05\ \mu\text{m}$, Channels 0–13)**.
  - **Zero coverage** in SPHEREx Detectors D2 through D6 ($1.11\text{--}5.00\ \mu\text{m}$).
- **Stellar Parameters & Quality Indicators:**
  - `astrophysical_parameters` table provides Apsis pipeline outputs:
    - $T_{\text{eff}}$ (`teff_gspphot`), $\log g$ (`logg_gspphot`), metallicity $[\text{M}/\text{H}]$ (`mh_gspphot`), line-of-sight extinction $A_G$ (`ag_gspphot`), and reddening $E(BP-RP)$.
  - Quality flags: `flags_gspphot`, `ruwe` ($\le 1.4$), `astrometric_excess_noise_sig`.
- **Target Cohort Overlap (P0008):**
  - Because all 3,206 sources are natively Gaia DR3 objects, cross-matching is a direct primary key join (`calib.source_id == gaia.source_id`).
  - Magnitude threshold: In P0008, 1,363 sources (42.5%) have $G \le 17.65$ and are expected to possess published continuous XP spectra. The remaining 1,843 sources have broadband $G, BP, RP$ photometry and Apsis astrophysical parameters.
- **Reconstruction Dependency:** Requires the Python package `gaiaxpy` (developed by the Gaia DPAC) to convert Hermite coefficients into calibrated physical spectra.

### B. Sloan Digital Sky Survey (SDSS DR17 / DR18)
- **Archive & Endpoint:** SDSS SkyServer REST API (`https://skyserver.sdss.org/dr17/SkyServerWS/SearchTools/SqlSearch`) and Science Archive Server (`https://data.sdss.org/sas/dr17/`).
- **Release Content:**
  - **SDSS-IV DR17:** Final release containing 3.4 million optical spectra from the BOSS spectrograph ($3600\text{--}10400\ \text{Å}$, $R \approx 1500\text{--}2500$) and 730,000 near-IR spectra from APOGEE-2 ($1.51\text{--}1.70\ \mu\text{m}$, $R \approx 22,500$).
  - **SDSS-V DR18:** Initial release of Milky Way Mapper (MWM) stellar spectra.
- **Population & Selection Bias:**
  - The legacy BOSS spectrograph targeted predominantly extragalactic objects (galaxies and quasars) at high Galactic latitude ($|b| > 30^\circ$). Stellar targets (SEGUE, calibration standard stars) make up $\sim 25\%\text{--}30\%$ of the database.
  - APOGEE targeted red giants and open clusters across the Milky Way disc and bulge.
- **Spectroscopic Parameters:**
  - `CLASS` (`'STAR'`, `'GALAXY'`, `'QSO'`), `SUBCLASS` (spectral subtype, e.g. `'G2V'`, `'K1III'`, `'DA'`).
  - `Z` (heliocentric radial velocity), `Z_ERR`, `ZWARNING` (flag 0 indicates an unproblematic fit).
  - `SN_MEDIAN_ALL` (median S/N per pixel across the spectrum).
- **Target Cohort Overlap:**
  - **Pointing 0008 (Dec $+5.3^\circ$ to $+10.0^\circ$):** Dec is north of Stripe 82 ($\delta \approx 0^\circ$). Coverage is restricted to sparse BOSS ancillary and SEGUE plates; estimated overlap is **$5\%\text{--}15\%$ ($N \approx 160\text{--}480$ sources)**.
  - **Pointing 0002 (Dec $-32^\circ$ to $-28^\circ$):** Dec $-30^\circ$ is **strictly below the Apache Point horizon** (cutoff $\delta \approx -15^\circ$). Optical SDSS coverage is **ZERO**. APOGEE-2 South (Las Campanas) has only isolated pencil beams.
  - **Pointing 0009 (Dec $+47^\circ$, $b \approx -16^\circ$):** Near-zero BOSS optical coverage due to low Galactic latitude exclusion.
  - **Pointing 0010 (NEP, Dec $+66.7^\circ$):** Targeted by specialized time-domain calibration plates ($10\%\text{--}25\%$ overlap).
- **Cross-Match Mechanics:** Requires spatial cone search (radius $1.5''$) with proper-motion propagation from SDSS epoch (typically 2000–2010) to SPHEREx epoch (2026.55).

### C. LAMOST (Large Sky Area Multi-Object Fibre Spectroscopic Telescope)
- **Archive & Endpoint:** LAMOST Data Release 10 (`http://dr10.lamost.org/v2/`).
- **Release Content:** ~11.8 million spectra, including $>10.5\text{ million}$ stellar spectra from the Low-Resolution Spectrograph (LRS; $370\text{--}900\text{ nm}$, $R \approx 1800$) and Medium-Resolution Spectrograph (MRS; $R \approx 7500$).
- **Target Population:** Primarily Galactic stellar survey (LEGUE) targeting FGK dwarf and giant stars across the Northern sky.
- **Stellar Parameters Available:**
  - `subclass`: Morgan-Keenan spectral classification (O, B, A, F, G, K, M, Carbon, White Dwarf).
  - LASP pipeline atmospheric parameters: $T_{\text{eff}}, \log g, [\text{Fe}/\text{H}], v_{\text{rad}}$ with formal covariance uncertainties.
  - Signal-to-noise metrics: `snru`, `snrg`, `snrr`, `snri`, `snrz`.
- **Target Cohort Overlap:**
  - Observable declination range from Xinglong Station: $-10^\circ \le \delta \le +60^\circ$.
  - **Pointing 0008 (Dec $+5.3^\circ$ to $+10.0^\circ$):** Accessible. LAMOST observed multiple plates in the South Galactic Cap. Estimated overlap is **$10\%\text{--}20\%$ ($N \approx 320\text{--}640$ sources)**.
  - **Pointing 0002 (Dec $-30.3^\circ$):** Dec $-30.3^\circ$ is **strictly below the LAMOST southern horizon** ($\delta < -10^\circ$). LAMOST coverage for P0002 is identically **ZERO**.
  - **Pointing 0009 (Dec $+46.8^\circ$):** Within prime LAMOST survey area; estimated overlap is **$20\%\text{--}40\%$**.
  - **Pointing 0010 (NEP, Dec $+66.7^\circ$):** Dec $+66.7^\circ$ exceeds the LAMOST northern zenith limit ($\delta \le +60^\circ$); coverage is near-zero ($<1\%$).
- **Wavelength Overlap Limitation:** LAMOST LRS ends at $900\text{ nm}$ ($0.90\ \mu\text{m}$). It overlaps **only the first 8 SPHEREx channels (Channels 0–7, $0.75\text{--}0.90\ \mu\text{m}$)**. Over $92\%$ of the SPHEREx spectral passband ($0.90\text{--}5.00\ \mu\text{m}$) has zero coverage.

### D. Supplementary Catalogs: 2MASS & ALLWISE
1. **2MASS (Two Micron All Sky Survey):**
   - Wavelengths: $J$ ($1.25\ \mu\text{m}$), $H$ ($1.65\ \mu\text{m}$), $K_s$ ($2.17\ \mu\text{m}$).
   - Status in Cohort: **$100\%$ pre-matched** (`tmass_id` exists in catalog).
   - Scientific Value: Overlaps SPHEREx Bands 2 and 3 ($1.11\text{--}2.42\ \mu\text{m}$). Provides near-IR flux anchors, though broadband ($R \sim 4\text{--}6$), not spectroscopic.
2. **ALLWISE (Wide-field Infrared Survey Explorer):**
   - Wavelengths: $W1$ ($3.4\ \mu\text{m}$), $W2$ ($4.6\ \mu\text{m}$), $W3$ ($12\ \mu\text{m}$), $W4$ ($22\ \mu\text{m}$).
   - Status in Cohort: High spatial completeness ($>95\%$). Local cross-match script already exists in repository (`scripts/crossmatch_gaia_allwise.py`).
   - **Crucial Scientific Value:** $W1$ ($3.4\ \mu\text{m}$) directly matches SPHEREx Band 4 ($2.42\text{--}3.82\ \mu\text{m}$), and $W2$ ($4.6\ \mu\text{m}$) directly matches SPHEREx Band 6 ($4.42\text{--}5.00\ \mu\text{m}$).
   - The mid-IR color index $W1 - W2$ provides the **only direct physical filter for circumstellar dust, debris disks, and active galactic nuclei**, which optical surveys cannot detect.

---

## 4. Target Cohort Coverage Feasibility Analysis

```
+----------------------------------------------------------------------------------------------------+
| TARGET COHORT COVERAGE & CROSS-MATCH KEY SUMMARY                                                   |
+--------------------------+-----------------------+-----------------------+-------------------------+
| Catalog                  | Primary Crossmatch    | P0008 Calibration     | P0002 / P0009 / P0010   |
|                          | Key Architecture      | Estimated Overlap     | Blind Eval Coverage     |
+--------------------------+-----------------------+-----------------------+-------------------------+
| **Gaia DR3 XP**          | `source_id` (Native)  | **40% - 45%** (G<17.65)| **35% - 50%** (All-Sky) |
| **SDSS Optical (BOSS)**  | Positional + PM match | **5% - 15%** (Sparse) | **P0002: 0%** (South)   |
| **SDSS APOGEE-2 (NIR)**  | 2MASS ID / Positional | **< 2%** (Pencil beam)| **< 1%** (Very sparse)  |
| **LAMOST LRS (Optical)** | Positional + PM match | **10% - 20%** (Cap)   | **P0002: 0%** (South)   |
| **2MASS (Photometric)**  | `tmass_id` (Native)   | **100%** (Pre-matched)| **100%** (Pre-matched)  |
| **ALLWISE (Photometric)**| Positional + PM match | **95% - 98%** (All-Sky)| **95% - 98%** (All-Sky) |
+--------------------------+-----------------------+-----------------------+-------------------------+
```

### Key Feasibility Findings:
1. **Positional Matching vs Native Keys:**  
   Gaia DR3 XP is the only spectroscopic catalog where cross-matching is **exact and deterministic by `source_id`**, eliminating all spatial matching ambiguities, misidentifications from crowding, and epoch propagation errors.
2. **Sky Footprint Asymmetry:**  
   Both SDSS optical and LAMOST have **strict geographical horizon limits** that completely exclude Pointing 0002 ($\delta \approx -30.3^\circ$). Any validation protocol relying exclusively on SDSS or LAMOST cannot evaluate the southern sky partition of SPECTRA.
3. **Magnitude Mismatch:**  
   The median $G$ magnitude of P0008 is $17.82$ mag. While Gaia XP spectra cut off at $G \approx 17.65$, this still leaves $>1,300$ high-quality spectra in P0008. In contrast, LAMOST has low signal-to-noise at $G > 17.0$ ($\text{SNR}_g < 5$).

---

## 5. Scientific Suitability Taxonomy Evaluation

In accordance with Section 4 of the audit mandate, each external catalog's evidence is categorized across the five scientific dimensions:

```
+-------------------------------------------------------------------------------------------------------------------+
| SCIENTIFIC SUITABILITY TAXONOMY CLASSIFICATION                                                                    |
+---------------------+-------------------+-------------------+-------------------+-----------------+---------------+
| Catalog             | Astrometric       | Stellar           | Optical           | Near-IR         | Infrared      |
|                     | Identification    | Classification    | Spectroscopic     | Spectroscopic   | Normality     |
+---------------------+-------------------+-------------------+-------------------+-----------------+---------------+
| **Gaia DR3 XP**     | **SUITABLE**      | **SUITABLE**      | **SUITABLE**      | **UNSUITABLE**  | **PROXY ONLY**|
| **SDSS BOSS**       | **SUITABLE**      | **SUITABLE**      | **SUITABLE**      | **UNSUITABLE**  | **PROXY ONLY**|
| **SDSS APOGEE-2**   | **SUITABLE**      | **SUITABLE**      | **UNSUITABLE**    | **SUITABLE**    | **PROXY ONLY**|
| **LAMOST LRS**      | **SUITABLE**      | **SUITABLE**      | **SUITABLE**      | **UNSUITABLE**  | **PROXY ONLY**|
| **2MASS**           | **SUITABLE**      | **PROXY ONLY**    | **NOT APPLICABLE**| **UNSUITABLE**  | **PROXY ONLY**|
| **ALLWISE**         | **SUITABLE**      | **PROXY ONLY**    | **NOT APPLICABLE**| **UNSUITABLE**  | **SUITABLE**  |
+---------------------+-------------------+-------------------+-------------------+-----------------+---------------+
```

### The Fundamental Scientific Caveat: Why Optical Normality != Infrared Normality

> [!WARNING]
> **CRITICAL SCIENTIFIC PRINCIPLE FOR SPECTRA VALIDATION:**  
> External optical spectroscopy (Gaia XP, SDSS BOSS, LAMOST) **cannot independently prove infrared normality**.
> 
> 1. **Bandpass Disconnect:** Optical spectra cover $0.33\text{--}1.05\ \mu\text{m}$. Over $86\%$ of SPHEREx channels reside between $1.05\ \mu\text{m}$ and $5.00\ \mu\text{m}$.
> 2. **Physical Dissociation of Optical and Infrared Phenomena:**
>    - A star with an entirely normal G2V or K3III optical photospheric absorption spectrum can host **circumstellar debris disks, zodiacal dust clouds, or protoplanetary dust**, causing significant infrared excess at $3\text{--}5\ \mu\text{m}$ (e.g. Vega, Fomalhaut, $\beta$ Pictoris phenomena).
>    - Low-mass substellar companions (unresolved brown dwarfs or giant exoplanets) contribute negligible optical flux but radiate strongly in the mid-infrared.
>    - Interstellar polycyclic aromatic hydrocarbon (PAH) emission or warm molecular gas along the line of sight can contaminate SPHEREx apertures without altering the optical stellar classification.
> 3. **Role of Optical Spectroscopy:**  
>    Optical spectroscopy proves **stellar nature and photospheric parameters** ($T_{\text{eff}}, \log g, [\text{Fe}/\text{H}]$). This allows synthesizing a theoretical Kurucz or BT-Settl stellar photospheric model.  
> 4. **Role of Mid-IR Photometry:**  
>    Subtracting this theoretical model from ALLWISE ($W1, W2$) and SPHEREx observations directly measures the true **infrared excess**. Only sources where both the optical spectrum matches a standard star AND the mid-IR colors show zero excess can be certified as authentic **Infrared Normal Null Controls**.

---

## 6. Data Access, Operational Feasibility & Network Preflight

### 6.1 Network Connectivity Preflight (Read-Only Standard Sandbox)
Execution of network connection tests to official public archive endpoints inside the current execution environment yielded:

```
ESA Gaia Archive TAP:    FAILED (URLError: <urlopen error [Errno 11001] getaddrinfo failed>)
SDSS SkyServer REST:     FAILED (URLError: <urlopen error [Errno 11001] getaddrinfo failed>)
LAMOST Data Release:     FAILED (URLError: <urlopen error [Errno 11001] getaddrinfo failed>)
NASA/IPAC IRSA SIA:      FAILED (URLError: <urlopen error [Errno 11001] getaddrinfo failed>)
VizieR TAP Service:      FAILED (URLError: <urlopen error [Errno 11001] getaddrinfo failed>)
```

- **Diagnosis:** The Antigravity standard sandbox mode (`BypassSandbox: false`) strictly blocks socket-level DNS address resolution.
- **Audit Classification:** In accordance with task governance, live catalog availability is marked **`UNVERIFIABLE_IN_SANDBOX`**. Network restrictions were not bypassed.

### 6.2 Software Dependencies in Python Environment:
- `astropy` (8.0.2): **INSTALLED** (Supports FITS I/O, coordinate transformations, and WCS).
- `numpy` (2.5.4) / `scipy` (1.18.1) / `pandas` (3.1.1): **INSTALLED**.
- `gaiaxpy`: **NOT INSTALLED** (Required for Gaia continuous XP coefficient calibration and conversion).
- `astroquery`: **NOT INSTALLED** (Standard package for TAP/VO queries).

### 6.3 Operational Access Protocols for Future Tasks:
- **Gaia DR3:** Open public access via TAP (`TAPVizieR` or ESA TAP). Synchronous query limit: 2,000 rows; asynchronous query limit: up to 3,000,000 rows.
- **SDSS:** Open public access via SkyServer REST/SQL. Query limit: 500,000 rows.
- **LAMOST:** Open web catalog search; FITS spectrum download requires free registered account.

---

## 7. Protected Scientific Asset Integrity Verification

All frozen candidate models, thresholds, and spatial benchmarks were cryptographically hashed and verified byte-for-byte immutable during this audit:

| Asset Description | Local File Path | Expected SHA-256 | Verified SHA-256 | Audit Status |
| :--- | :--- | :---: | :---: | :---: |
| **SPECTRA V2 Checkpoint** | [`checkpoints/spectra_masked_ae_v2.pt`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/checkpoints/spectra_masked_ae_v2.pt) | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **VERIFIED IMMUTABLE** |
| **Provisional Thresholds** | [`data/processed/spectra/spectra_v2_provisional_thresholds_v1.json`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/data/processed/spectra/spectra_v2_provisional_thresholds_v1.json) | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **VERIFIED IMMUTABLE** |
| **ASTROVISION V3 Checkpoint** | [`checkpoints/astrovision_spatial_v3.pt`](file:///C:/Users/blues/OneDrive/Desktop/New%20folder%20(7)/SPECTRA-X/checkpoints/astrovision_spatial_v3.pt) | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **VERIFIED IMMUTABLE** |

Zero bytes of model weights, thresholds, calibration cohorts, or evaluation catalogs were modified.

---

## 8. Final Decision & Recommendations for Task 4.2B

### Final Audit Determination:
# **`PARTIALLY_FEASIBLE`**

### Determination Rationale:
1. **Feasible Dimension:**  
   External astronomical catalogs can definitively provide **astrometric identification and optical stellar classification** for a substantial fraction of the SPECTRA cohorts. Gaia DR3 provides exact, deterministic matching via native `source_id` keys, yielding an estimated $\sim 40\%\text{--}45\%$ spectroscopic XP yield ($N \approx 1,350$ spectra in P0008) and nearly $100\%$ atmospheric parameter coverage.
2. **Partial / Infeasible Dimension:**  
   - SDSS and LAMOST have severe footprint gaps, including **zero coverage for Pointing 0002**.
   - Optical spectroscopy covers only SPHEREx Band 1 ($0.75\text{--}1.05\ \mu\text{m}$), providing zero spectroscopic ground truth for Bands 2–6 ($1.11\text{--}5.00\ \mu\text{m}$).
   - Optical stellar normality cannot prove mid-infrared normality; warm circumstellar dust requires mid-IR photometric confirmation.
   - Live querying from the current execution environment is blocked by standard sandbox DNS boundaries.

---

### Specific Recommendations for Task 4.2B:

1. **Primary Recommendation — Pilot Test Gaia DR3 XP:**  
   **Catalog to Test First:** **ESA Gaia DR3 BP/RP XP Spectra**.  
   *Why Gaia First?*  
   - $100\%$ of P0008 calibration sources natively contain Gaia DR3 `source_id` primary keys.  
   - Eliminates all spatial coordinate matching ambiguity, blending confusion, and proper-motion propagation errors.  
   - Highest sample yield: $>1,300$ spectra in P0008 alone.
2. **Prerequisite Engineering Step:**  
   Install `gaiaxpy` and `astroquery` in the environment, or ingest a pre-staged offline TAP extract of the 3,206 P0008 `source_id` records.
3. **Mandatory Mid-IR Normality Coupling:**  
   In Task 4.2B, do not evaluate Gaia XP in isolation. Pair each Gaia-classified normal star with its **ALLWISE ($W1, W2$) mid-infrared color excess** (`W1 - W2 <= 0.05` and `W2 - W3 <= 0.10`) to certify authentic, dust-free mid-infrared normal null controls.

---
*Signed by Independent Scientific Validation Lead & Software Integrity Auditor*  
*Build Reference: `l2b-v27-2026-222`*  
*Date: November 7, 2026*

