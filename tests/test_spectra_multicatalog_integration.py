"""
SPECTRA-X / F1 — Phase 4, Task 4.20C
Comprehensive Unit & Scientific Validation Test Suite for SPECTRA Multi-Catalog Infrared Integration

Mandatory Test Coverage:
 1. Valid multi-catalog match (Gaia DR3 + 2MASS + ALLWISE + CatWISE2020).
 2. Single-catalog match.
 3. Missing catalog behavior (INSUFFICIENT_PHOTOMETRY, fail-closed).
 4. Ambiguous crossmatch (competing counterparts > 1 -> AMBIGUOUS_COUNTERPART).
 5. Low-quality photometry (quality flag degradation -> QUALITY_FLAGGED).
 6. Upper-limit handling (never promoted to excess).
 7. Flux uncertainty propagation (Pogson error + zero-point quadrature).
 8. Epoch mismatch tracking (individual catalog epochs preserved).
 9. Missing-data behavior (never treated as zero flux).
10. Evidence provenance integrity and immutability (ReadOnlyDict / ReadOnlyList).
"""

import math
import pytest
from typing import Dict, Any

from spectra_engine.continuum_sidecar_interface import (
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    ReadOnlyDict,
    ReadOnlyList,
)
from spectra_engine.continuum_sidecar_engine import EmpiricalContinuumSidecar
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    CatalogNormalizer,
    NormalizedSourceRecord,
    NormalizedMeasurement,
)
from spectra_engine.validation.infrared_excess.zero_points import PHOTOMETRIC_BANDS


@pytest.fixture
def sidecar():
    return EmpiricalContinuumSidecar()


# ==============================================================================
# 1. Valid Multi-Catalog Match (Gaia + 2MASS + ALLWISE + CatWISE)
# ==============================================================================
def test_valid_multicatalog_match(sidecar):
    """Validates ingestion and normalization of complete multi-catalog record."""
    raw_data = {
        "source_id": 2568637734340601088,
        "ra": 27.16971,
        "dec": 7.61073,
        "phot_g_mean_mag": 11.538,
        "phot_g_mean_mag_error": 0.005,
        "has_2mass": True,
        "tmass_designation": "01484071+0736387",
        "tmass_sep_arcsec": 0.265,
        "tmass_j_m": 9.852,
        "tmass_h_m": 9.343,
        "tmass_k_m": 9.186,
        "tmass_ph_qual": "AAA",
        "has_allwise": True,
        "allwise_designation": "J014840.72+073638.5",
        "allwise_sep_arcsec": 0.132,
        "allwise_w1mpro": 9.120,
        "allwise_w2mpro": 9.216,
        "allwise_cc_flags": "0000",
        "allwise_ph_qual": "AAAU",
        "catwise_designation": "CW014840.72+073638.5",
        "catwise_sep_arcsec": 0.110,
        "catwise_w1mpro": 9.115,
        "catwise_w2mpro": 9.210,
        "gaia_ruwe": 1.02,
        "has_xp_continuous": True,
        "competing_counterparts_count": 0,
        "acquisition_status": "ACQUIRED_OFFICIAL_ARCHIVES"
    }

    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")
    assert record.source_id == 2568637734340601088
    assert "2MASS_Ks" in record.measurements
    assert "WISE_W1" in record.measurements
    assert "WISE_W2" in record.measurements
    assert "CatWISE_W1" in record.measurements
    assert "CatWISE_W2" in record.measurements
    assert "Gaia_G" in record.measurements

    # Evaluate through sidecar
    res = sidecar.evaluate_continuum(
        source_id="2568637734340601088",
        pointing_id="P0008",
        wavelengths=[1.5, 2.5, 3.5, 4.5],
        fluxes=[100.0, 80.0, 60.0, 45.0],
        uncertainties=[1.0, 1.0, 1.0, 1.0],
        valid_mask=[True, True, True, True],
        photometric_record=record
    )

    assert isinstance(res, ContinuumEvidenceRecord)
    assert res.quality_status in ["SUPPORTED_PHOTOSPHERIC_CONSISTENCY", "POSSIBLE_INFRARED_EXCESS"]
    assert "multicatalog_infrared_evidence" in res.metadata

    multi_ev = res.metadata["multicatalog_infrared_evidence"]
    assert "2MASS" in multi_ev["catalogs_evaluated"]
    assert "ALLWISE" in multi_ev["catalogs_evaluated"]
    assert "CatWISE2020" in multi_ev["catalogs_evaluated"]
    assert "Gaia_DR3" in multi_ev["catalogs_evaluated"]
    assert multi_ev["crossmatch_identifiers"]["tmass_designation"] == "01484071+0736387"
    assert multi_ev["crossmatch_identifiers"]["catwise_designation"] == "CW014840.72+073638.5"


# ==============================================================================
# 2. Single-Catalog Match
# ==============================================================================
def test_single_catalog_match(sidecar):
    """Validates handling when only one catalog (e.g. 2MASS only, no mid-IR) is matched."""
    raw_data = {
        "source_id": 123456789,
        "ra": 30.0,
        "dec": 10.0,
        "has_2mass": True,
        "tmass_designation": "02000000+1000000",
        "tmass_k_m": 12.0,
        "tmass_ph_qual": "AAA",
        "has_allwise": False,
        "allwise_designation": "NO_ALLWISE_MATCH",
    }
    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")
    assert "2MASS_Ks" in record.measurements
    assert "WISE_W1" not in record.measurements

    res = sidecar.evaluate_continuum(
        source_id="123456789",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[10.0, 8.0, 6.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=record
    )

    # Must classify as INSUFFICIENT_PHOTOMETRY because mid-IR is missing
    assert res.quality_status == "INSUFFICIENT_PHOTOMETRY"
    assert res.color_excess_detected is False


# ==============================================================================
# 3. Missing Catalog (Empty Matches)
# ==============================================================================
def test_missing_catalog_fail_closed(sidecar):
    """Validates that a record with no catalog matches yields INSUFFICIENT_PHOTOMETRY."""
    record = NormalizedSourceRecord(
        source_id=999,
        ra_deg=45.0,
        dec_deg=0.0,
        cohort_pointing="P0008",
        measurements={},
        competing_counterparts_count=0
    )
    res = sidecar.evaluate_continuum(
        source_id="999",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[5.0, 4.0, 3.0],
        uncertainties=[0.2, 0.2, 0.2],
        valid_mask=[True, True, True],
        photometric_record=record
    )
    assert res.quality_status == "INSUFFICIENT_PHOTOMETRY"
    assert res.color_excess_detected is False


# ==============================================================================
# 4. Ambiguous Crossmatch (Competing Counterparts)
# ==============================================================================
def test_ambiguous_crossmatch_veto(sidecar):
    """Validates that competing counterparts > 1 enforce AMBIGUOUS_COUNTERPART and veto excess."""
    raw_data = {
        "source_id": 55555,
        "ra": 25.0,
        "dec": 5.0,
        "has_2mass": True,
        "tmass_designation": "01400000+0500000",
        "tmass_k_m": 10.0,
        "tmass_ph_qual": "AAA",
        "has_allwise": True,
        "allwise_designation": "J014000.00+050000.0",
        "allwise_w1mpro": 9.0,
        "allwise_w2mpro": 8.0,
        "allwise_cc_flags": "0000",
        "allwise_ph_qual": "AA00",
        "competing_counterparts_count": 3  # Ambiguous!
    }
    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")
    assert record.competing_counterparts_count == 3

    res = sidecar.evaluate_continuum(
        source_id="55555",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[20.0, 15.0, 12.0],
        uncertainties=[1.0, 1.0, 1.0],
        valid_mask=[True, True, True],
        photometric_record=record
    )
    assert res.quality_status == "AMBIGUOUS_COUNTERPART"
    assert res.counterpart_ambiguity is True
    assert res.color_excess_detected is False


# ==============================================================================
# 5. Low-Quality Photometry
# ==============================================================================
def test_low_quality_photometry_handling(sidecar):
    """Validates that low-quality flags or contamination set status to QUALITY_FLAGGED."""
    raw_data = {
        "source_id": 77777,
        "ra": 28.0,
        "dec": 7.0,
        "has_2mass": True,
        "tmass_designation": "01520000+0700000",
        "tmass_k_m": 16.0,
        "tmass_ph_qual": "ACU",  # Ks is 'U' (upper limit / low quality)
        "has_allwise": True,
        "allwise_designation": "J015200.00+070000.0",
        "allwise_w1mpro": 15.0,
        "allwise_w2mpro": 14.5,
        "allwise_cc_flags": "0000",
        "allwise_ph_qual": "AB00",
    }
    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")

    res = sidecar.evaluate_continuum(
        source_id="77777",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[1.0, 0.8, 0.6],
        uncertainties=[0.1, 0.1, 0.1],
        valid_mask=[True, True, True],
        photometric_record=record
    )
    assert res.quality_status == "QUALITY_FLAGGED"
    assert res.color_excess_detected is False


# ==============================================================================
# 6. Upper-Limit Handling
# ==============================================================================
def test_upper_limit_never_promoted(sidecar):
    """Validates that upper-limit detections are never promoted to color_excess_detected=True."""
    m_w2 = CatalogNormalizer.normalize_measurement(
        band_key="WISE_W2",
        magnitude=14.0,
        magnitude_error=None,
        quality_flag="U",
        is_upper_limit=True
    )
    assert m_w2.is_upper_limit is True
    assert m_w2.flux_uncertainty_mJy is None  # Upper limits have undefined symmetrical uncertainty

    # Contract validation check: a record with is_upper_limit=True cannot have color_excess_detected=True
    with pytest.raises(ValueError, match="Governance violation: is_upper_limit=True cannot be promoted"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="111",
            pointing_id="P0008",
            color_excess_detected=True,  # VIOLATION
            is_upper_limit=True,
            quality_status="POSSIBLE_INFRARED_EXCESS"
        )


# ==============================================================================
# 7. Flux Uncertainty Propagation
# ==============================================================================
def test_flux_uncertainty_propagation():
    """Validates Pogson error propagation and zero-point uncertainty quadrature."""
    band = PHOTOMETRIC_BANDS["2MASS_Ks"]
    # Mag = 10.0, mag_err = 0.05
    flux, flux_err = CatalogNormalizer.magnitude_to_flux(10.0, 0.05, band, is_upper_limit=False)

    expected_flux = band.zero_point_flux_mJy * (10.0 ** (-0.4 * 10.0))
    assert abs(flux - expected_flux) < 1e-4

    # sigma_eff = sqrt(0.05^2 + (0.019 * 2.5 / ln10)^2)
    zp_mag = 0.019 / (math.log(10.0) / 2.5)
    sigma_eff = math.sqrt(0.05**2 + zp_mag**2)
    expected_err = (math.log(10.0) / 2.5) * expected_flux * sigma_eff

    assert abs(flux_err - expected_err) < 1e-4


# ==============================================================================
# 8. Epoch Mismatch Tracking
# ==============================================================================
def test_epoch_mismatch_tracking(sidecar):
    """Validates that individual catalog observation epochs are preserved without silent mixing."""
    raw_data = {
        "source_id": 88888,
        "ra": 35.0,
        "dec": 15.0,
        "has_2mass": True,
        "tmass_designation": "02200000+1500000",
        "tmass_k_m": 11.0,
        "tmass_ph_qual": "AAA",
        "has_allwise": True,
        "allwise_designation": "J022000.00+150000.0",
        "allwise_w1mpro": 10.5,
        "allwise_w2mpro": 10.4,
        "allwise_cc_flags": "0000",
        "allwise_ph_qual": "AA00",
    }
    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")
    record.measurements["2MASS_Ks"].observation_epoch_mjd = 51500.0  # ~1999
    record.measurements["WISE_W1"].observation_epoch_mjd = 55300.0   # ~2010

    res = sidecar.evaluate_continuum(
        source_id="88888",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[15.0, 12.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=record
    )
    multi_ev = res.metadata["multicatalog_infrared_evidence"]
    meas = multi_ev["band_measurements"]
    assert meas["2MASS_Ks"]["observation_epoch_mjd"] == 51500.0
    assert meas["WISE_W1"]["observation_epoch_mjd"] == 55300.0


# ==============================================================================
# 9. Missing Data Fail-Closed Behavior
# ==============================================================================
def test_missing_data_never_treated_as_zero():
    """Validates that None magnitude is not converted to zero flux."""
    band = PHOTOMETRIC_BANDS["WISE_W1"]
    flux, flux_err = CatalogNormalizer.magnitude_to_flux(None, None, band)
    assert flux is None
    assert flux_err is None

    flux_nan, flux_err_nan = CatalogNormalizer.magnitude_to_flux(float("nan"), 0.05, band)
    assert flux_nan is None
    assert flux_err_nan is None


# ==============================================================================
# 10. Evidence Provenance Integrity & Deep Immutability
# ==============================================================================
def test_evidence_provenance_immutability(sidecar):
    """Validates deep immutability of ContinuumEvidenceRecord collections (Task 4.10 governance)."""
    raw_data = {
        "source_id": 44444,
        "ra": 20.0,
        "dec": 5.0,
        "has_2mass": True,
        "tmass_designation": "01200000+0500000",
        "tmass_k_m": 12.0,
        "tmass_ph_qual": "AAA",
        "has_allwise": True,
        "allwise_designation": "J012000.00+050000.0",
        "allwise_w1mpro": 11.5,
        "allwise_w2mpro": 11.5,
        "allwise_cc_flags": "0000",
        "allwise_ph_qual": "AA00",
    }
    record = CatalogNormalizer.from_multicatalog_dict(raw_data, cohort_pointing="P0008")
    res = sidecar.evaluate_continuum(
        source_id="44444",
        pointing_id="P0008",
        wavelengths=[2.0, 3.0, 4.0],
        fluxes=[8.0, 6.0, 5.0],
        uncertainties=[0.3, 0.3, 0.3],
        valid_mask=[True, True, True],
        photometric_record=record
    )

    # Immutability tests
    assert isinstance(res.limitation_codes, ReadOnlyList)
    assert isinstance(res.color_indices, ReadOnlyDict)
    assert isinstance(res.metadata, ReadOnlyDict)

    with pytest.raises(TypeError, match="ReadOnlyList does not support append"):
        res.limitation_codes.append("ILLEGAL_CODE")

    with pytest.raises(TypeError, match="ReadOnlyDict does not support item assignment"):
        res.metadata["tampered_key"] = "hacked"

