# SPECTRA-X / F1 — Phase 4, Task 4.2B
# Gaia XP + ALLWISE Local Cross-Match Pilot & Infrared Excess Validation Design Report

**Pipeline Build:** `l2b-v27-2026-222`  
**Task Type:** STRICT READ-ONLY SCIENTIFIC DATA AUDIT  
**Module:** SPECTRA + External Photometric Cross-Match Validation  
**Target Calibration Cohort:** Pointing 0008 ($N = 3,206$ sources)  
**Audit Date:** 2026-11-07  
**Governance:** Zero Modification Policy — Frozen Assets Verified  
**Final Audit Verdict:** `NOT_FEASIBLE_WITH_CURRENT_LOCAL_DATA`

---

## 1. Executive Summary & Audit Mandate

Under the governance of **Phase 4, Task 4.2B**, this independent scientific audit investigated whether external catalog data—specifically **ESA Gaia DR3 BP/RP (XP) low-resolution spectra**, **Gaia Apsis GSP-Phot stellar astrophysical parameters**, **2MASS Point Source Catalog photometry ($J, H, K_s$)**, and **ALLWISE mid-infrared photometry ($W1, W2$)**—are genuinely available locally and scientifically usable for the Pointing 0008 calibration cohort ($N = 3,206$).

The primary scientific objective was to establish the feasibility and complete methodological design of an external-catalog-assisted infrared excess validation pathway for the **SPECTRA** 102-channel infrared anomaly engine.

### Definitive Audit Finding
The audit revealed a fundamental distinction between **astrometric cross-match keys** and **actual physical flux measurements**:
1. **Astrometric Cross-Match Keys:** Complete and verified locally. Exactly 3,206 sources ($100.0\%$) possess native 64-bit Gaia DR3 identifiers (`source_id`), sub-milliarcsecond astrometry ($ra, dec, pmra, pmdec, \varpi$), and Gaia optical broadband magnitudes ($G, BP, RP$). Additionally, 2,624 sources ($81.85\%$) possess pre-matched 2MASS PSC designations (`tmass_id`) with a median astrometric separation of $0.151''$.
2. **Physical Spectrophotometric and Infrared Measurements:** **Completely absent from the local repository.** Zero continuous or sampled Gaia XP spectra, zero Gaia Apsis astrophysical parameters ($T_{\text{eff}}, \log g, \text{[M/H]}, A_G$), zero 2MASS calibrated flux measurements ($j\_m, h\_m, ks\_m$), and zero ALLWISE records exist in local files for Pointing 0008.

Consequently, while the cohort is exceptionally well-conditioned astrometrically, computing empirical infrared excesses or selecting confirmed photospheric control stars cannot be performed using current local data alone. The final audit verdict is **`NOT_FEASIBLE_WITH_CURRENT_LOCAL_DATA`**.

---

## 2. Pilot Scope, Cohort Integrity & Baseline Definition

The audit evaluated the frozen calibration cohort of **Pointing 0008**, established in Task 1.2C:
- **Authoritative Score File:** `data/processed/spectra/spectra_p0008_calibration_scores_v1.csv` ($3,206$ sources).
- **Authoritative Source Catalog:** `data/processed/pilot_catalogues/pointing_0008_source_catalogue.csv` ($7,500$ candidates, of which $3,206$ form the calibration cohort).
- **Astrometric Sub-Catalogs:** `data/external/gaia_dr3/pilot_0008_field1_gaia_dr3.csv`, `field2`, `field3` ($2,500$ rows each).

### Cohort Purity Verification
Cross-referencing the $3,206$ calibration sources against the Pointing 0008 source catalogue confirmed:
- **Cohort Completeness:** Exactly $3,206/3,206$ ($100.0\%$) unique matches.
- **Classification Category:** $3,206/3,206$ ($100.0\%$) are classified as `RELIABLE_ISOLATED_POINT_SOURCE`.
- **Field Distribution:** Field 1 ($1,098$ sources, $34.2\%$), Field 2 ($1,048$ sources, $32.7\%$), Field 3 ($1,060$ sources, $33.1\%$).
- **Blind Evaluation Isolation:** Zero sources from blind evaluation pointings (P0002, P0009, P0010) were inspected or utilized, strictly preserving blind cohort integrity.

---

## 3. Catalog Cross-Match Existence vs. Physical Measurement Availability Census

The table below delineates the local availability status for all examined parameters across the $3,206$ calibration sources:

| Catalog Domain | Parameter / Measurement | Local Availability Status | Available Count ($N=3,206$) | Coverage (%) | Scientific Role / Usability |
|---|---|---|---:|---:|---|
| **Gaia DR3 Astrometry** | `source_id` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Primary 64-bit integer join key |
| **Gaia DR3 Astrometry** | `ra`, `dec` (ICRS J2016.0) | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Sub-mas astrometric coordinates |
| **Gaia DR3 Astrometry** | `pmra`, `pmdec` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Median PM: $-0.49, -3.21\text{ mas/yr}$ |
| **Gaia DR3 Astrometry** | `parallax` ($\varpi$) | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Positive for 3,084 sources (96.19%) |
| **Gaia DR3 Astrometry** | `ruwe` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Single-star astrometric filter |
| **Gaia DR3 Astrometry** | `astrometric_excess_noise` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Median $0.00\text{ mas}$; binarity screen |
| **Gaia DR3 Photometry** | `phot_g_mean_mag` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Range $[11.54, 19.50]$; optical anchor |
| **Gaia DR3 Photometry** | `phot_bp_mean_mag` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Range $[11.87, 21.59]$; optical color |
| **Gaia DR3 Photometry** | `phot_rp_mean_mag` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Range $[10.74, 19.49]$; optical color |
| **SPHEREx Propagation** | `ra_epoch`, `dec_epoch` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Propagated to SPHEREx epoch 2026.55 |
| **SPHEREx Isolation** | `nn_dist_arcsec` | `LOCALLY_AVAILABLE` | 3,206 | 100.00% | Min $12.04''$; median $50.73''$ |
| **Gaia DR3 XP Spectra** | Continuous Hermite Basis | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Absent from local repository |
| **Gaia DR3 XP Spectra** | Sampled Spectral Vectors | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Absent from local repository |
| **Gaia DR3 Apsis** | $T_{\text{eff\_gspphot}}$ | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Stellar effective temperature absent |
| **Gaia DR3 Apsis** | $\log g_{\text{gspphot}}$ | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Surface gravity absent |
| **Gaia DR3 Apsis** | $\text{[M/H]}_{\text{gspphot}}$ | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Metallicity absent |
| **Gaia DR3 Apsis** | $A_{G\text{\_gspphot}}$ / $E(BP-RP)$ | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Extinction / reddening absent |
| **2MASS PSC** | `tmass_id` (Designation) | `LOCALLY_AVAILABLE` | 2,624 | 81.85% | 2MASS cross-match designation |
| **2MASS PSC** | `tmass_dist_arcsec` | `LOCALLY_AVAILABLE` | 2,624 | 81.85% | Median separation $0.151''$ |
| **2MASS PSC** | $J, H, K_s$ Magnitudes & Errors | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Calibrated NIR fluxes absent |
| **2MASS PSC** | `ph_qual` Flags | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Detection quality flags absent |
| **ALLWISE** | $W1, W2, W3, W4$ Magnitudes | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Zero ALLWISE records for P0008 |
| **ALLWISE** | `cc_flags`, `ext_flg`, `var_flg` | `NOT_LOCALLY_AVAILABLE` | 0 | 0.00% | Artifact & confusion flags absent |

---

## 4. Gaia DR3 XP Low-Resolution Spectroscopy Audit

- **Expected Data Structure:** Gaia DR3 provides mean spectra for $\sim 220$ million sources down to $G \sim 17.65\text{ mag}$ published either as continuous Hermite polynomial basis functions (55 coefficients for BP and 55 coefficients for RP) or as sampled 343-point flux vectors spanning $336 - 1020\text{ nm}$.
- **Local Census:** Detailed search of all directory trees (`data/external/gaia_dr3/`, `data/processed/`, `models/`) confirmed that **zero XP data files, continuous tables, or sampled spectrum arrays exist locally**.
- **Limiting Magnitude Analysis:** In the P0008 cohort, $1,475$ sources ($46.0\%$) have $G \le 17.65\text{ mag}$, indicating that nearly half of the cohort possesses public Gaia XP spectra in the official ESA archive. However, because these records were not included in the initial pilot staging, they are unavailable locally.
- **Scientific Consequence:** Empirical spectrophotometric continuum anchoring in the optical regime ($0.33 - 1.02\,\mu\text{m}$) cannot be executed with local assets.

---

## 5. Gaia DR3 Apsis GSP-Phot Astrophysical Parameters Audit

- **Expected Data Structure:** Astrophysical parameters derived from XP spectra and broadband photometry via the Apsis GSP-Phot pipeline (`teff_gspphot`, `logg_gspphot`, `mh_gspphot`, `ag_gspphot`, `ebpminrp_gspphot`).
- **Local Census:** None of the local Gaia CSV files (`pilot_0008_field1_gaia_dr3.csv` through `field3`) contain Apsis parameter columns. The files contain exactly 13 columns strictly restricted to astrometry ($ra, dec, pmra, pmdec, \varpi$, errors) and mean magnitudes ($G, BP, RP$).
- **Scientific Consequence:** Constructing an un-degenerated synthetic stellar atmosphere model ($F_{\text{photosphere}}$) requires estimating stellar $T_{\text{eff}}$ purely from optical colors $(BP - RP)$, which suffers from strong degeneracy with interstellar reddening $E(BP - RP)$ in the absence of independent $A_G$ or spectroscopic temperature constraints.

---

## 6. 2MASS Photometry Availability & Astrometric Match Quality

### 6.1 Match Rate and Depth Limit
- Total cohort: $3,206$ sources.
- Sources with `tmass_id`: **$2,624$ ($81.85\%$)**.
- Sources lacking 2MASS match: **$582$ ($18.15\%$)**.
- *Astrophysical Reason for Missing Matches:* The 2MASS PSC has a nominal $10\sigma$ point-source sensitivity limit of $K_s \approx 14.3\text{ mag}$ and $J \approx 15.8\text{ mag}$. In the P0008 cohort, the optical magnitude reaches $G = 19.50\text{ mag}$ (median $G = 17.82\text{ mag}$). For late-type or distant solar-type stars with $G > 18.0$, near-infrared emission frequently drops below the 2MASS detection threshold.

### 6.2 Astrometric Match Quality Distribution ($N = 2,624$)
- **Minimum Separation:** $0.0026''$.
- **Median Separation:** **$0.1512''$**.
- **Mean Separation:** $0.1950''$.
- **Standard Deviation:** $0.1609''$.
- **Separation $\le 0.5''$:** $2,486$ sources (**$94.74\%$** of matches).
- **Separation in $(0.5'', 1.0'']$:** $129$ sources (**$4.92\%$** of matches).
- **Separation $> 1.0''$:** Exactly $9$ sources (**$0.34\%$** of matches; maximum $1.4822''$).
- *Conclusion on Astrometric Association:* The astrometric match between Gaia DR3 and 2MASS PSC is exceptionally clean. With $94.7\%$ of counterparts falling within $0.5''$ and median separation of $0.15''$, the cross-match keys are robust.

### 6.3 Missing Calibrated Flux Measurements
Although `tmass_id` strings (e.g., `02053507+0901329`) and match distances are recorded, **no flux measurements ($j\_m, h\_m, ks\_m$, errors, or quality flags)** are present in any repository table. Therefore, near-infrared spectral anchoring cannot be performed.

---

## 7. ALLWISE Photometry Availability & Spatial Blending Analysis

### 7.1 Complete Absence for Pointing 0008
- Investigation of `data/external/allwise/` and `data/processed/crossmatch/` revealed that ALLWISE cross-match tables exist **only for historical Pointing 0003** (`p0003_allwise_matches.csv`).
- **Zero ALLWISE data files or cross-match records exist for Pointing 0008.**

### 7.2 Spatial Resolution and Beam Confusion Assessment
The ALLWISE beam has an angular resolution (FWHM) of:
- $W1$ ($3.4\,\mu\text{m}$): $6.1''$
- $W2$ ($4.6\,\mu\text{m}$): $6.4''$
- $W3$ ($12.0\,\mu\text{m}$): $6.5''$
- $W4$ ($22.0\,\mu\text{m}$): $12.0''$

In comparison, the SPHEREx pixel scale is $\sim 6.2'' \times 6.2''$.

### 7.3 Cohort Isolation Metrics
To evaluate whether Pointing 0008 would suffer from spatial blending in the ALLWISE aperture:
- **Minimum Nearest-Neighbor Distance:** $\min(\text{nn\_dist}) = \mathbf{12.0389''}$.
- **Median Nearest-Neighbor Distance:** $\text{median}(\text{nn\_dist}) = \mathbf{50.7310''}$.
- **Sources with $\text{nn\_dist} < 6.0''$:** Exactly **$0$ ($0.0\%$)**.
- **Sources with $\text{nn\_dist} < 12.0''$:** Exactly **$0$ ($0.0\%$)**.
- **Distance to Saturated Source:** $\min(\text{dist\_to\_sat}) = \mathbf{185.35''}$ (median $534.67''$).

*Critical Scientific Finding:* The P0008 calibration cohort was deliberately constructed during pilot preparation with a strict spatial isolation threshold ($\text{nn\_dist} \ge 12.0''$). Consequently, **zero sources suffer from optical stellar crowding or companion blending inside the $6.1''$ ALLWISE beam or the $6.2''$ SPHEREx pixel**. If ALLWISE photometry were ingested, spatial confusion would not be an issue for this cohort.

---

## 8. Astrometric Reliability, Beam Disparity & Proper Motion Propagation

### 8.1 Single-Star Astrometric Purity
- **Renormalized Unit Weight Error (RUWE):**
  - Minimum: $0.8221$
  - Median: $1.0116$
  - Mean: $1.0188$
  - Maximum: $1.3958$
  - Sources with $\text{RUWE} \le 1.20$: **$3,126$ ($97.50\%$)** (optimal single stars).
  - Sources with $1.20 < \text{RUWE} \le 1.40$: **$80$ ($2.50\%$)** (acceptable astrometric fit).
  - Sources with $\text{RUWE} > 1.40$: **$0$ ($0.0\%$)** (zero problematic astrometric binaries).
- **Astrometric Excess Noise:**
  - Median: $0.0000\text{ mas}$
  - Mean: $0.1580\text{ mas}$
  - Maximum: $1.9812\text{ mas}$
  - Demonstrates that the cohort consists almost entirely of well-behaved point sources with negligible orbital wobble.

### 8.2 Proper Motion Propagation to SPHEREx Epoch 2026.55
- The catalog verifies that all $3,206$ sources underwent rigorous coordinate propagation from Gaia DR3 reference epoch $2016.0$ to SPHEREx mission epoch $2026.55$ ($\Delta t = 10.55\text{ years}$):
  - Propagated coordinates: `ra_epoch`, `dec_epoch`.
  - Proper motion displacements: `delta_ra_arcsec` (median $-0.005''$), `delta_dec_arcsec` (median $-0.034''$).
  - Maximum displacement: $0.342''$.
  - Successful propagation flag: `pm_propagated` is True for $100.0\%$ of sources.

---

## 9. Mathematical & Methodological Infrared Excess Validation Design Summary

To enable rigorous future execution, a formal mathematical framework was authored in `reports/PHASE_4_2B_IR_EXCESS_VALIDATION_DESIGN.md`. Key structural pillars include:

1. **Monochromatic Excess Metric:**
   $$S_{\text{excess}}(\lambda) = \frac{F_{\text{obs}}(\lambda) - F_{\text{photosphere}}(\lambda)}{\sqrt{\sigma_{\text{obs}}^2(\lambda) + \sigma_{\text{photosphere}}^2(\lambda) + \sigma_{\text{sys}}^2(\lambda)}}$$
   with a conservative systematic calibration floor $\sigma_{\text{sys}} / F_{\text{phot}} = 0.03$ ($3\%$).
2. **Integrated Infrared Significance:**
   $$S_{\text{IR\_total}} = \sqrt{\sum_{\lambda_i \ge 2.0\,\mu\text{m}} \left[\max\left(0, \frac{F_{\text{obs}}(\lambda_i) - F_{\text{photosphere}}(\lambda_i)}{\sigma_{\text{tot}}(\lambda_i)}\right)\right]^2}$$
   requiring $S_{\text{excess}} \ge 3.0\sigma$ in $\ge 2$ adjacent channels or $S_{\text{IR\_total}} \ge 5.0\sigma$ for positive excess confirmation.
3. **Photospheric Grid Anchoring:** Fitting synthetic BT-Settl / ATLAS9 stellar atmospheres to optical Gaia photometry ($G, BP, RP$) de-reddened via Fitzpatrick (1999) extinction laws.
4. **Systematic Screening Filters:** Rejection of blended sources ($\text{nn\_dist} < 12''$), artifact-contaminated profiles (`cc_flags != '0000'`), extended morphology (`ext_flg > 0`), and intrinsic stellar variables (`phot_variable_flag == 'VARIABLE'` or `var_flg > 5`).

---

## 10. Control Sample Eligibility & Candidate Tiering Summary

Every candidate evaluated under this framework is assigned to one of seven mutually exclusive tiers:

| Tier | Classification Category | Cohort Count ($N=3,206$) | Scientific Description & Criteria |
|---|---|---:|---|
| **Tier 1** | `CLEAN_PHOTOSPHERIC_CONTROL_CANDIDATE` | 0 | Ideal negative control; $\text{RUWE} \le 1.2$, non-variable, $|S_{\text{excess}}| < 2.0\sigma$ across all IR bands |
| **Tier 2** | `POSSIBLE_IR_EXCESS_CANDIDATE` | 0 | Genuine astrophysical excess target; $S_{\text{excess}} \ge 3.0\sigma$ in $\ge 2$ bands or $S_{\text{IR\_total}} \ge 5.0\sigma$ |
| **Tier 3** | `AMBIGUOUS_OR_BLENDED` | 0 | Crowded or artifact-contaminated profile; rejected from automated validation |
| **Tier 4** | `VARIABLE_OR_EPOCH_MISMATCH` | 0 | Significant multi-epoch or intra-visit flux variability; routed to CHRONOS-X |
| **Tier 5** | `INSUFFICIENT_PHOTOMETRY` | 0 | Missing detection or non-detection upper limit ($\text{SNR} < 5$) in critical bands |
| **Tier 6** | `INSUFFICIENT_STELLAR_PARAMETERS` | 0 | Unconstrained $T_{\text{eff}}, \log g$ preventing unique photospheric SED fitting |
| **Tier 7** | `UNVERIFIABLE` | **3,206** | **Physical flux measurements absent from local repository files** |

*Operational Audit Reality:* Because actual physical fluxes from 2MASS and ALLWISE and Gaia XP/Apsis parameters are absent from local tables, **all 3,206 sources currently reside in Tier 7 (`UNVERIFIABLE`)**.

---

## 11. Protected Asset Integrity & Regression Test Suite Verification

### 11.1 Protected Asset SHA-256 Hashes
All protected model weights, threshold registries, and checkpoints were re-verified against their authoritative cryptographic fingerprints:

| Asset Path | Expected SHA-256 Digest | Computed SHA-256 Digest | Match Verdict |
|---|---|---|---|
| `checkpoints/spectra_masked_ae_v2.pt` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | `6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938` | **PASS / UNTOUCHED** |
| `data/processed/spectra/spectra_v2_provisional_thresholds_v1.json` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | `D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848` | **PASS / UNTOUCHED** |
| `checkpoints/astrovision_spatial_v3.pt` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | `3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99` | **PASS / UNTOUCHED** |

### 11.2 Automated Regression Suite
The full repository test suite was executed:
- Command: `pytest tests/`
- Items collected: 166
- Passed: 166 (100%)
- Failed: 0
- Execution duration: 59.16 seconds

---

## 12. Definitive Scientific Verdict & Next Steps

### Final Verdict: `NOT_FEASIBLE_WITH_CURRENT_LOCAL_DATA`

### Scientific Rationale
1. **Astrometric Pre-Conditions Satisfied:** Pointing 0008 exhibits exemplary astrometric conditioning. 100% of sources possess high-precision Gaia DR3 keys and epoch-propagated coordinates; 81.85% possess clean 2MASS cross-match keys; and 100% satisfy strict spatial isolation criteria ($\text{nn\_dist} \ge 12.04''$, $\text{RUWE} \le 1.40$), eliminating spatial blending risks.
2. **Physical Data Absence:** The physical measurements required to compute infrared excess—namely calibrated fluxes for 2MASS $J, H, K_s$, ALLWISE $W1, W2$, and Gaia XP/Apsis parameters—do not exist in the local repository.
3. **Integrity Rule:** In accordance with strict scientific integrity guidelines, missing values cannot be simulated, synthesized, or imputed.

### Direct Next Steps for Pipeline Execution
When external data retrieval is authorized:
1. **Staging TAP Ingestion:** Perform targeted TAP queries against `gaiadr3.gaia_source`, 2MASS PSC, and ALLWISE using the pre-existing 3,206 `source_id` and `tmass_id` keys.
2. **Execute Validation Pipeline:** Ingest the retrieved flux tables into the formal framework specified in `reports/PHASE_4_2B_IR_EXCESS_VALIDATION_DESIGN.md`.
3. **Partition Cohort:** Populate Tiers 1 through 6, identifying clean photospheric controls to calibrate SPECTRA false-positive baselines and flagging confirmed infrared excess candidates.

