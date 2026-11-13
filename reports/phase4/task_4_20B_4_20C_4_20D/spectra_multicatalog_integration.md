# SPECTRA Multi-Catalog Infrared Evidence Integration Report
## Phase 4, Task 4.20C — Technical & Scientific Specification

**Module:** SPECTRA Continuum Sidecar (`spectra_engine/`)  
**Data Contract:** `CONTINUUM_SIDECAR_EVIDENCE_V1`  
**Task Verdict:** $\mathbf{IMPLEMENTED\_AND\_TESTED}$  
**Audit Date:** 2026-11-08  

---

### 1. Integration Scope & Contract Compliance

Task 4.20C integrates multi-catalog external infrared photometry into the authoritative `CONTINUUM_SIDECAR_EVIDENCE_V1` contract without modifying the frozen `spectra_masked_ae_v2.pt` checkpoint or provisional spectral thresholds.

Supported Astronomical Catalogs:
1. **Gaia DR3:** Broadband optical anchor ($G, BP, RP$), astrometric fidelity (RUWE, excess noise), and XP continuous spectra flags.
2. **2MASS PSC:** Near-infrared baseline ($J, H, K_s$) at $1.24 - 2.16\,\mu\text{m}$ (Cohen et al. 2003 zero points).
3. **ALLWISE:** Mid-infrared excess probes ($W1, W2, W3, W4$) at $3.35 - 22.09\,\mu\text{m}$ (Jarrett et al. 2011 zero points).
4. **CatWISE2020:** Deep mid-infrared photometry ($W1, W2$) down to $W1 \sim 17.7\text{ mag}$, $W2 \sim 17.5\text{ mag}$ (Eisenhardt et al. 2020, Marocco et al. 2021).

---

### 2. Multi-Catalog Evidence Schema in `metadata`

Every evaluated `ContinuumEvidenceRecord` now preserves a structured `multicatalog_infrared_evidence` payload:

```json
{
  "multicatalog_infrared_evidence": {
    "catalogs_evaluated": ["2MASS", "ALLWISE", "CatWISE2020", "Gaia_DR3"],
    "band_measurements": {
      "2MASS_Ks": {
        "catalog_source": "2MASS",
        "effective_wavelength_microns": 2.159,
        "magnitude": 9.186,
        "magnitude_error": 0.025,
        "flux_density_mJy": 139.75,
        "flux_uncertainty_mJy": 3.42,
        "is_upper_limit": false,
        "quality_flag": "A",
        "separation_arcsec": 0.265,
        "observation_epoch_mjd": 51500.0,
        "blending_flag": null,
        "contamination_flag": null,
        "notes": "2MASS PSC 01484071+0736387"
      },
      "WISE_W2": {
        "catalog_source": "ALLWISE",
        "effective_wavelength_microns": 4.6028,
        "magnitude": 9.216,
        "magnitude_error": 0.021,
        "flux_density_mJy": 35.53,
        "flux_uncertainty_mJy": 0.88,
        "is_upper_limit": false,
        "quality_flag": "A",
        "separation_arcsec": 0.132,
        "observation_epoch_mjd": 55300.0,
        "blending_flag": null,
        "contamination_flag": "0",
        "notes": "ALLWISE J014840.72+073638.5"
      }
    },
    "crossmatch_identifiers": {
      "gaia_source_id": "2568637734340601088",
      "tmass_designation": "01484071+0736387",
      "tmass_separation_arcsec": 0.265,
      "allwise_designation": "J014840.72+073638.5",
      "allwise_separation_arcsec": 0.132,
      "catwise_designation": "CW014840.72+073638.5",
      "catwise_separation_arcsec": 0.110
    },
    "counterpart_ambiguity": false,
    "competing_counterparts_count": 0,
    "is_spatially_isolated": true,
    "gaia_ruwe": 1.02,
    "has_xp_continuous": true
  }
}
```

---

### 3. Scientific Safeguards & Contract Enforcement

1. **Non-Zero Flux Conversion:** Missing catalog photometry is never converted to zero flux ($F_\nu = 0$). Null entries propagate as `None` fail-closed.
2. **Upper-Limit Isolation:** Upper limits (`is_upper_limit=True`) represent non-detections ($3\sigma$ bounds) and are strictly barred from triggering `color_excess_detected=True`.
3. **Quadrature Error Propagation:** Pogson magnitude uncertainties are combined with zero-point calibration fractional uncertainties in quadrature:
   $$\sigma_{F_\nu} = \left(\frac{\ln 10}{2.5}\right) F_\nu \sqrt{\sigma_m^2 + \sigma_{\rm zp}^2}$$
4. **Deep Immutability:** All collections inside `ContinuumEvidenceRecord` are frozen using `ReadOnlyDict` and `ReadOnlyList`, preventing downstream tampering.
5. **Cohort Isolation:** Preserves strict calibration allowlist (`CANONICAL_CALIBRATION_POINTING = "P0008"`). Evaluation pointings (P0002, P0009, P0010) cannot be promoted to calibration-grade excess without verified calibration baselines.

---

### 4. Test Verification Summary

10/10 tests pass in `tests/test_spectra_multicatalog_integration.py` (0.86s):
- `test_valid_multicatalog_match`: Gaia + 2MASS + ALLWISE + CatWISE.
- `test_single_catalog_match`: Mid-IR absent -> `INSUFFICIENT_PHOTOMETRY`.
- `test_missing_catalog_fail_closed`: Empty match fails closed.
- `test_ambiguous_crossmatch_veto`: Competing counterparts > 1 -> `AMBIGUOUS_COUNTERPART`.
- `test_low_quality_photometry_handling`: Quality flags -> `QUALITY_FLAGGED`.
- `test_upper_limit_never_promoted`: Contract raises ValueError on upper limit excess.
- `test_flux_uncertainty_propagation`: Verified Pogson quadrature.
- `test_epoch_mismatch_tracking`: 2MASS (~1999) vs WISE (~2010) epochs preserved.
- `test_missing_data_never_treated_as_zero`: None magnitude yields None flux.
- `test_evidence_provenance_immutability`: ReadOnlyList and ReadOnlyDict mutation prevention.
