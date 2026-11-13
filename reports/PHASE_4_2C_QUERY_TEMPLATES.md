# SPECTRA-X / F1 — Phase 4, Task 4.2C
# External Archive Query Templates & ADQL Specifications

**Pipeline Build:** `l2b-v27-2026-222`  
**Task Type:** STRICT READ-ONLY EXTERNAL DATA ACQUISITION FEASIBILITY AUDIT  
**Module:** SPECTRA — External Photometric & Spectroscopic Validation  
**Target Calibration Cohort:** Pointing 0008 ($N = 3,206$)  
**Execution Status:** DOCUMENTATION ONLY — STRICTLY UNEXECUTED  

---

> [!IMPORTANT]
> **GOVERNANCE MANDATE:** The ADQL query templates and code snippets documented in this file are provided strictly for architectural reference and verification. In adherence to the Task 4.2C zero-download and zero-network-bypass governance policies, **none of these queries have been executed against live remote archive endpoints**.

---

## 1. ESA Gaia DR3 TAP Query Templates

### 1.1 Astrophysical Parameters & Astrometry Query (ADQL v2.0)
This query retrieves authoritative astrometric quality indicators, broadband optical magnitudes, and Apsis GSP-Phot stellar atmospheric parameters for the Pointing 0008 calibration cohort.

```sql
-- Archive: ESA Gaia Archive (https://gea.esac.esa.int/tap-server/tap)
-- Protocol: IVOA TAP v1.0 / ADQL v2.0 (Asynchronous Job Recommended)
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    gs.source_id,
    gs.ra,
    gs.dec,
    gs.parallax,
    gs.parallax_error,
    gs.pmra,
    gs.pmra_error,
    gs.pmdec,
    gs.pmdec_error,
    gs.ruwe,
    gs.astrometric_excess_noise,
    gs.phot_g_mean_mag,
    gs.phot_g_mean_flux_over_error,
    gs.phot_bp_mean_mag,
    gs.phot_rp_mean_mag,
    gs.bp_rp,
    gs.has_xp_continuous,
    gs.has_xp_sampled,
    gs.has_rvs,
    gs.phot_variable_flag,
    ap.teff_gspphot,
    ap.teff_gspphot_lower,
    ap.teff_gspphot_upper,
    ap.logg_gspphot,
    ap.logg_gspphot_lower,
    ap.logg_gspphot_upper,
    ap.mh_gspphot,
    ap.mh_gspphot_lower,
    ap.mh_gspphot_upper,
    ap.ag_gspphot,
    ap.ebpminrp_gspphot
FROM gaiadr3.gaia_source AS gs
LEFT JOIN gaiadr3.astrophysical_parameters AS ap
    ON gs.source_id = ap.source_id
WHERE gs.source_id IN (
    -- Example 5 source_ids from Pointing 0008 cohort (total batch = 3,206)
    526702672023594112,
    526703084340454528,
    526703118699933824,
    526703187419614464,
    526703221779185280
    /* ... Full list of 3,206 source_id values supplied at runtime ... */
);
```

### 1.2 Gaia XP Continuous Mean Spectra Query (ADQL v2.0)
Retrieves continuous Hermite polynomial basis coefficients (55 coefficients for BP, 55 for RP) for detailed spectrophotometric reconstruction.

```sql
-- Archive: ESA Gaia Archive (https://gea.esac.esa.int/tap-server/tap)
-- Target Table: gaiadr3.xp_continuous_mean_spectrum
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    xp.source_id,
    xp.solution_id,
    xp.bp_n_parameters,
    xp.bp_coefficients,
    xp.bp_coefficient_errors,
    xp.bp_coefficient_correlations,
    xp.bp_n_relevant_bases,
    xp.bp_relative_shrinking,
    xp.rp_n_parameters,
    xp.rp_coefficients,
    xp.rp_coefficient_errors,
    xp.rp_coefficient_correlations,
    xp.rp_n_relevant_bases,
    xp.rp_relative_shrinking
FROM gaiadr3.xp_continuous_mean_spectrum AS xp
WHERE xp.source_id IN (
    /* ... 3,206 target source_id values ... */
);
```

---

## 2. NASA/IPAC 2MASS Point Source Catalog TAP Query Templates

### 2.1 Exact Designation Match Query (ADQL v2.0)
This query directly targets the $2,624$ P0008 sources with known 2MASS designations recorded in `pointing_0008_source_catalogue.csv`.

```sql
-- Archive: NASA/IPAC IRSA TAP (https://irsa.ipac.caltech.edu/TAP)
-- Target Catalog: fp_psc (2MASS Point Source Catalog)
-- Protocol: IVOA TAP v1.0 / ADQL v2.0
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    designation AS tmass_id,
    ra AS tmass_ra,
    dec AS tmass_dec,
    j_m,
    j_cmsig,
    j_snr,
    h_m,
    h_cmsig,
    h_snr,
    k_m AS ks_m,
    k_cmsig AS ks_cmsig,
    k_snr AS ks_snr,
    ph_qual AS ph_qual_2mass,
    rd_flg,
    bl_flg,
    cc_flg
FROM fp_psc
WHERE designation IN (
    -- Example designations from P0008 cohort (total batch = 2,624)
    '02053507+0901329',
    '02053723+0901083',
    '02054133+0901594',
    '02054291+0900224',
    '02054415+0902263'
    /* ... Full list of 2,624 tmass_id strings ... */
);
```

### 2.2 Spatial Cone-Search Cross-Match Query
For sources without a pre-existing designation or to verify astrometric offset within matching radius $r = 1.5''$:

```sql
-- Positional Cross-match on IRSA fp_psc using ADQL Spatial Geometry
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    designation AS tmass_id,
    ra AS tmass_ra,
    dec AS tmass_dec,
    j_m, j_cmsig, h_m, h_cmsig, k_m, k_cmsig, ph_qual
FROM fp_psc
WHERE 1 = CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', 31.42531, 9.02581, 1.5 / 3600.0)
);
```

---

## 3. NASA/IPAC ALLWISE Source Catalog TAP Query Templates

### 3.1 Positional Cone-Search Query with Epoch Propagation
ALLWISE photometry is matched using proper-motion-propagated coordinates with a search radius of $3.0''$.

```sql
-- Archive: NASA/IPAC IRSA TAP (https://irsa.ipac.caltech.edu/TAP)
-- Target Catalog: allwise_p3as_psd (AllWISE Source Catalog)
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    designation AS allwise_designation,
    ra AS allwise_ra,
    dec AS allwise_dec,
    w1mpro,
    w1sigmpro,
    w1snr,
    w1rchi2,
    w2mpro,
    w2sigmpro,
    w2snr,
    w2rchi2,
    w3mpro,
    w3sigmpro,
    w4mpro,
    w4sigmpro,
    ph_qual AS ph_qual_allwise,
    cc_flags,
    ext_flg,
    var_flg
FROM allwise_p3as_psd
WHERE 1 = CONTAINS(
    POINT('ICRS', ra, dec),
    CIRCLE('ICRS', 31.42531, 9.02581, 3.0 / 3600.0)
);
```

### 3.2 Batch Cross-Match Specification (ADQL Join)
In a dedicated validation environment with TAP table upload capabilities (`tap_upload`), the entire cohort can be matched in a single server-side spatial join:

```sql
-- Server-Side Spatial Join using TAP Uploaded Table
-- Status: UNEXECUTED DOCUMENTATION TEMPLATE

SELECT 
    cat.source_id,
    cat.ra_epoch,
    cat.dec_epoch,
    w.designation AS allwise_id,
    w.ra AS allwise_ra,
    w.dec AS allwise_dec,
    DISTANCE(POINT('ICRS', cat.ra_epoch, cat.dec_epoch), POINT('ICRS', w.ra, w.dec)) * 3600.0 AS sep_arcsec,
    w.w1mpro,
    w.w1sigmpro,
    w.w1snr,
    w.w2mpro,
    w.w2sigmpro,
    w.w2snr,
    w.ph_qual,
    w.cc_flags,
    w.ext_flg,
    w.var_flg
FROM TAP_UPLOAD.p0008_cohort AS cat
JOIN allwise_p3as_psd AS w
    ON 1 = CONTAINS(
        POINT('ICRS', w.ra, w.dec),
        CIRCLE('ICRS', cat.ra_epoch, cat.dec_epoch, 3.0 / 3600.0)
    );
```

---

## 4. Gaia XP Sampled Spectra Generation Specification (`gaiaxpy`)

In the target validation environment, calibrated sampled spectra ($336 - 1020\text{ nm}$ sampled at $2\text{ nm}$ increments across 343 channels) can be computed directly from continuous Hermite coefficients using the official ESA `gaiaxpy` package:

```python
"""
Documentary reference for gaiaxpy spectral sampling.
Status: UNEXECUTED DOCUMENTATION TEMPLATE
"""
# from gaiaxpy import calibrate, convert

def generate_sampled_xp_spectra(source_ids: list[int], output_path: str):
    """
    Downloads continuous XP coefficients and generates calibrated sampled flux vectors.
    Requires gaiaxpy and outbound network connection to ESA Gaia archive.
    """
    # Sampled spectra generated using official Hermite basis inversion
    # calibrated_spectra, sampling = calibrate(source_ids, save_file=True, output_path=output_path)
    pass
```

---

## 5. Verification & Execution Status

- **Query Correctness:** All ADQL statements conform to IVOA ADQL v2.0 standards and official table schemas for ESA Gaia DR3 and NASA/IPAC IRSA.
- **Execution State:** Strictly **UNEXECUTED**. No remote queries were submitted, and no scientific data was acquired.

