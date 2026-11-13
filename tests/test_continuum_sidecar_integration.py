"""
SPECTRA-X / F1 — Phase 4, Task 4.7
Comprehensive Continuum Sidecar Integration & Governance Test Suite

Validates integration of empirical infrared excess validation engine
(Task 4.6) with authoritative contract CONTINUUM_SIDECAR_EVIDENCE_V1
and downstream FUSION-X multimodal ranking engine (models/fusion/fusion_engine.py).

Covers all 16 required test categories from Section 9:
 1. Valid SUPPORTED_PHOTOSPHERIC_CONSISTENCY payload.
 2. Valid POSSIBLE_INFRARED_EXCESS payload.
 3. QUALITY_FLAGGED remains non-confirmatory.
 4. INSUFFICIENT_PHOTOMETRY remains non-confirmatory.
 5. AMBIGUOUS_COUNTERPART remains non-confirmatory.
 6. UNVERIFIABLE remains non-confirmatory.
 7. Missing sidecar behavior (transparent, no negative penalty).
 8. Null/invalid uncertainty fail-closed behavior.
 9. Upper-limit handling.
10. Invalid contract version rejection.
11. Source ID mismatch rejection.
12. Provenance preservation.
13. Physical unit consistency (mJy).
14. FUSION-X fail-closed behavior.
15. Temporal eligibility safety rules unchanged.
16. Backward compatibility with Phase 3 callers.
"""

import math
import pytest
from typing import Dict, Any

from spectra_engine.continuum_sidecar_interface import (
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
    ALLOWED_EVIDENCE_STATES,
    BASE_SIDECAR_LIMITATION_CODES,
)
from spectra_engine.continuum_sidecar_engine import EmpiricalContinuumSidecar
from spectra_engine.validation.infrared_excess.catalog_normalizer import (
    NormalizedSourceRecord,
    NormalizedMeasurement,
)
from models.fusion.fusion_engine import FusionEngine


@pytest.fixture
def fusion_engine():
    """Initializes standard production FusionEngine instance."""
    return FusionEngine()


@pytest.fixture
def empirical_sidecar():
    """Initializes concrete EmpiricalContinuumSidecar instance."""
    return EmpiricalContinuumSidecar()


# =============================================================================
# Category 1: Valid SUPPORTED_PHOTOSPHERIC_CONSISTENCY payload
# =============================================================================
def test_category_01_valid_photospheric_consistency_payload(fusion_engine):
    """Test Category 1: Ingestion of valid photospheric consistency evidence."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_PHOTO_001",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        color_excess_detected=False,
        excess_significance_sigma=0.45,
        primary_band="W2",
        observed_flux_mJy=10.5,
        predicted_flux_mJy=10.2,
        residual_flux_mJy=0.3,
        total_uncertainty_mJy=0.75,
        flux_unit="mJy",
        limitation_codes=list(BASE_SIDECAR_LIMITATION_CODES),
    )
    sidecar.validate()

    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_PHOTO_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.002,
        spectra_channels=102,
        continuum_sidecar=sidecar,
    )

    assert rec.validity_status == "VALID"
    assert "CONTINUUM_STATE=SUPPORTED_PHOTOSPHERIC_CONSISTENCY" in rec.evidence_summary
    assert rec.metadata["continuum_sidecar"] is not None
    assert rec.metadata["continuum_evidence_state"] == "SUPPORTED_PHOTOSPHERIC_CONSISTENCY"
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is False
    assert ";SIDECAR:SUPPORTED_PHOTOSPHERIC_CONSISTENCY" in rec.input_provenance


# =============================================================================
# Category 2: Valid POSSIBLE_INFRARED_EXCESS payload
# =============================================================================
def test_category_02_valid_possible_infrared_excess_payload(fusion_engine):
    """Test Category 2: Ingestion of valid candidate infrared excess evidence."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_EXCESS_001",
        pointing_id="P0008",
        evidence_state="POSSIBLE_INFRARED_EXCESS",
        color_excess_detected=True,
        excess_significance_sigma=4.85,
        primary_band="W2",
        observed_flux_mJy=25.0,
        predicted_flux_mJy=10.0,
        residual_flux_mJy=15.0,
        total_uncertainty_mJy=1.2,
        flux_unit="mJy",
        limitation_codes=list(BASE_SIDECAR_LIMITATION_CODES),
    )
    sidecar.validate()

    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_EXCESS_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.008,
        spectra_channels=102,
        continuum_sidecar=sidecar,
    )

    assert rec.validity_status == "VALID"
    assert "CONTINUUM_STATE=POSSIBLE_INFRARED_EXCESS" in rec.evidence_summary
    assert "excess_sig=4.85σ" in rec.evidence_summary
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is True
    assert rec.metadata["continuum_evidence_state"] == "POSSIBLE_INFRARED_EXCESS"


# =============================================================================
# Category 3: QUALITY_FLAGGED remains non-confirmatory
# =============================================================================
def test_category_03_quality_flagged_non_confirmatory(fusion_engine):
    """Test Category 3: QUALITY_FLAGGED state cannot be promoted to detected excess."""
    # Attempting to set color_excess_detected=True on QUALITY_FLAGGED must fail closed
    with pytest.raises(ValueError, match="Governance violation"):
        bad_sidecar = ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_FLAG_001",
            pointing_id="P0008",
            evidence_state="QUALITY_FLAGGED",
            quality_status="QUALITY_FLAGGED",
            color_excess_detected=True,
        )

    # Valid non-confirmatory QUALITY_FLAGGED payload
    valid_flagged = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_FLAG_001",
        pointing_id="P0008",
        evidence_state="QUALITY_FLAGGED",
        color_excess_detected=False,
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_FLAG_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.003,
        continuum_sidecar=valid_flagged,
    )
    assert rec.metadata["continuum_evidence_state"] == "QUALITY_FLAGGED"
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is False


# =============================================================================
# Category 4: INSUFFICIENT_PHOTOMETRY remains non-confirmatory
# =============================================================================
def test_category_04_insufficient_photometry_non_confirmatory(fusion_engine):
    """Test Category 4: INSUFFICIENT_PHOTOMETRY state cannot claim excess."""
    with pytest.raises(ValueError, match="Governance violation"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_INSUFF_001",
            pointing_id="P0008",
            evidence_state="INSUFFICIENT_PHOTOMETRY",
            quality_status="INSUFFICIENT_PHOTOMETRY",
            color_excess_detected=True,
        )

    valid_insuff = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_INSUFF_001",
        pointing_id="P0008",
        evidence_state="INSUFFICIENT_PHOTOMETRY",
        color_excess_detected=False,
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_INSUFF_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.004,
        continuum_sidecar=valid_insuff,
    )
    assert rec.metadata["continuum_evidence_state"] == "INSUFFICIENT_PHOTOMETRY"
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is False


# =============================================================================
# Category 5: AMBIGUOUS_COUNTERPART remains non-confirmatory
# =============================================================================
def test_category_05_ambiguous_counterpart_non_confirmatory(fusion_engine):
    """Test Category 5: AMBIGUOUS_COUNTERPART state and flag cannot claim excess."""
    with pytest.raises(ValueError, match="Governance violation"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_AMBIG_001",
            pointing_id="P0008",
            evidence_state="AMBIGUOUS_COUNTERPART",
            quality_status="AMBIGUOUS_COUNTERPART",
            color_excess_detected=True,
        )

    with pytest.raises(ValueError, match="counterpart_ambiguity=True cannot be promoted"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_AMBIG_001",
            pointing_id="P0008",
            evidence_state="POSSIBLE_INFRARED_EXCESS",
            color_excess_detected=True,
            counterpart_ambiguity=True,
            observed_flux_mJy=10.0,
            total_uncertainty_mJy=1.0,
        )

    valid_ambig = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_AMBIG_001",
        pointing_id="P0008",
        evidence_state="AMBIGUOUS_COUNTERPART",
        counterpart_ambiguity=True,
        color_excess_detected=False,
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_AMBIG_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.003,
        continuum_sidecar=valid_ambig,
    )
    assert "CONTINUUM_AMBIGUOUS_COUNTERPART=TRUE" in rec.evidence_summary
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is False


# =============================================================================
# Category 6: UNVERIFIABLE remains non-confirmatory
# =============================================================================
def test_category_06_unverifiable_non_confirmatory(fusion_engine):
    """Test Category 6: UNVERIFIABLE state cannot claim excess."""
    with pytest.raises(ValueError, match="Governance violation"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNVER_001",
            pointing_id="P0008",
            evidence_state="UNVERIFIABLE",
            quality_status="UNVERIFIABLE",
            color_excess_detected=True,
        )

    valid_unver = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_UNVER_001",
        pointing_id="P0008",
        evidence_state="UNVERIFIABLE",
        color_excess_detected=False,
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_UNVER_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.003,
        continuum_sidecar=valid_unver,
    )
    assert rec.metadata["continuum_evidence_state"] == "UNVERIFIABLE"
    assert rec.metadata["continuum_sidecar"]["color_excess_detected"] is False


# =============================================================================
# Category 7: Missing sidecar behavior (transparent, no negative penalty)
# =============================================================================
def test_category_07_missing_sidecar_behavior(fusion_engine):
    """Test Category 7: Absence of sidecar is transparent and causes zero penalty."""
    rec_none = fusion_engine.evaluate_source(
        candidate_id="SRC_TRANS_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.005,
        continuum_sidecar=None,
    )
    rec_default = fusion_engine.evaluate_source(
        candidate_id="SRC_TRANS_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.005,
    )

    assert rec_none.anomaly_score == rec_default.anomaly_score
    assert rec_none.validity_status == rec_default.validity_status
    assert rec_none.metadata["continuum_sidecar"] is None
    assert rec_none.metadata["continuum_evidence_state"] is None
    assert "missing_modalities" in rec_none.metadata
    assert "sidecar" not in rec_none.metadata["missing_modalities"]


# =============================================================================
# Category 8: Null/invalid uncertainty fail-closed behavior
# =============================================================================
def test_category_08_null_invalid_uncertainty_fail_closed():
    """Test Category 8: Invalid or non-positive uncertainties fail closed."""
    # Negative uncertainty
    with pytest.raises(ValueError, match="total_uncertainty_mJy must be non-negative"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNC_001",
            pointing_id="P0008",
            total_uncertainty_mJy=-0.5,
        )

    # NaN uncertainty
    with pytest.raises(ValueError, match="total_uncertainty_mJy must be non-negative"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNC_001",
            pointing_id="P0008",
            total_uncertainty_mJy=float("nan"),
        )

    # Missing uncertainty on empirical excess detection
    with pytest.raises(ValueError, match="Empirical color_excess_detected=True requires valid positive total_uncertainty_mJy"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UNC_001",
            pointing_id="P0008",
            color_excess_detected=True,
            observed_flux_mJy=15.0,
            total_uncertainty_mJy=None,
        )


# =============================================================================
# Category 9: Upper-limit handling
# =============================================================================
def test_category_09_upper_limit_handling(fusion_engine):
    """Test Category 9: Upper-limits cannot claim excess and are documented."""
    # is_upper_limit=True with color_excess_detected=True must fail closed
    with pytest.raises(ValueError, match="is_upper_limit=True cannot be promoted"):
        ContinuumEvidenceRecord(
            contract_version=SIDECAR_CONTRACT_VERSION,
            source_id="SRC_UL_001",
            pointing_id="P0008",
            color_excess_detected=True,
            is_upper_limit=True,
            observed_flux_mJy=5.0,
            total_uncertainty_mJy=0.5,
        )

    # Valid upper-limit payload
    valid_ul = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_UL_001",
        pointing_id="P0008",
        color_excess_detected=False,
        is_upper_limit=True,
        observed_flux_mJy=5.0,
        total_uncertainty_mJy=0.5,
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_UL_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.003,
        continuum_sidecar=valid_ul,
    )
    assert "CONTINUUM_UPPER_LIMIT=TRUE" in rec.evidence_summary
    assert rec.metadata["continuum_sidecar"]["is_upper_limit"] is True


# =============================================================================
# Category 10: Invalid contract version rejection
# =============================================================================
def test_category_10_invalid_contract_version_rejection(fusion_engine):
    """Test Category 10: Reject payloads with invalid contract versions."""
    with pytest.raises(ValueError, match="Invalid contract_version"):
        ContinuumEvidenceRecord(
            contract_version="INVALID_VERSION_V99",
            source_id="SRC_BAD_VER",
            pointing_id="P0008",
        )

    bad_dict = {
        "contract_version": "INVALID_CONTRACT_2026",
        "source_id": "SRC_BAD_VER",
        "pointing_id": "P0008",
    }
    with pytest.raises(ValueError, match="Invalid continuum sidecar contract_version"):
        fusion_engine.evaluate_source(
            candidate_id="SRC_BAD_VER",
            ra=270.0,
            dec=66.5,
            observation_id="OBS_001",
            observation_time="2026-11-08T00:00:00Z",
            continuum_sidecar=bad_dict,
        )


# =============================================================================
# Category 11: Source ID mismatch rejection
# =============================================================================
def test_category_11_source_id_mismatch_rejection(fusion_engine):
    """Test Category 11: Reject sidecars where source_id does not match candidate_id."""
    mismatched_sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_ACTUAL_A",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        color_excess_detected=False,
    )
    with pytest.raises(ValueError, match="Continuum sidecar source_id mismatch"):
        fusion_engine.evaluate_source(
            candidate_id="SRC_DIFFERENT_B",
            ra=270.0,
            dec=66.5,
            observation_id="OBS_001",
            observation_time="2026-11-08T00:00:00Z",
            continuum_sidecar=mismatched_sidecar,
        )


# =============================================================================
# Category 12: Provenance preservation
# =============================================================================
def test_category_12_provenance_preservation(fusion_engine):
    """Test Category 12: Input provenance and metadata are fully preserved."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_PROV_001",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        color_excess_detected=False,
        validation_timestamp="2026-11-08T00:00:00Z",
        pipeline_build="l2b-v27-2026-222",
        metadata={"catalog_coverage": "GAIA_2MASS_ALLWISE"},
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_PROV_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.002,
        continuum_sidecar=sidecar,
    )
    assert ";SIDECAR:SUPPORTED_PHOTOSPHERIC_CONSISTENCY" in rec.input_provenance
    assert rec.metadata["continuum_sidecar"]["pipeline_build"] == "l2b-v27-2026-222"
    assert rec.metadata["continuum_sidecar"]["metadata"]["catalog_coverage"] == "GAIA_2MASS_ALLWISE"


# =============================================================================
# Category 13: Physical unit consistency (mJy)
# =============================================================================
def test_category_13_physical_unit_consistency(fusion_engine):
    """Test Category 13: Flux units are verified as mJy and values are finite."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_UNIT_001",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        color_excess_detected=False,
        observed_flux_mJy=14.2,
        predicted_flux_mJy=14.0,
        residual_flux_mJy=0.2,
        total_uncertainty_mJy=0.8,
        flux_unit="mJy",
    )
    rec = fusion_engine.evaluate_source(
        candidate_id="SRC_UNIT_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        spectra_score=0.002,
        continuum_sidecar=sidecar,
    )
    sc = rec.metadata["continuum_sidecar"]
    assert sc["flux_unit"] == "mJy"
    assert isinstance(sc["observed_flux_mJy"], (int, float))
    assert math.isfinite(sc["observed_flux_mJy"])
    assert math.isfinite(sc["total_uncertainty_mJy"])


# =============================================================================
# Category 14: FUSION-X fail-closed behavior
# =============================================================================
def test_category_14_fusion_fail_closed_behavior(fusion_engine):
    """Test Category 14: Unsupported sidecar types fail closed with TypeError."""
    with pytest.raises(TypeError, match="continuum_sidecar must be ContinuumEvidenceRecord or dict"):
        fusion_engine.evaluate_source(
            candidate_id="SRC_FAIL_001",
            ra=270.0,
            dec=66.5,
            observation_id="OBS_001",
            observation_time="2026-11-08T00:00:00Z",
            continuum_sidecar=[1, 2, 3],  # invalid type
        )


# =============================================================================
# Category 15: Temporal eligibility safety rules unchanged
# =============================================================================
def test_category_15_temporal_eligibility_safety_rules_unchanged(fusion_engine):
    """Test Category 15: Task 1.3K safety gate is completely preserved with sidecar."""
    sidecar = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_TEMP_001",
        pointing_id="P0008",
        evidence_state="SUPPORTED_PHOTOSPHERIC_CONSISTENCY",
        color_excess_detected=False,
    )

    # Ineligible temporal spike cannot be promoted even if continuum sidecar is present
    rec_blocked = fusion_engine.evaluate_source(
        candidate_id="SRC_TEMP_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        chronos_score=9.0,
        chronos_temporal_eligibility="FALSE",
        is_known_gaia_star=False,
        continuum_sidecar=sidecar,
    )
    assert "CLASSIFICATION: ANOMALOUS_RESIDUAL_REQUIRES_REVIEW" in rec_blocked.evidence_summary

    # Eligible temporal spike is promoted
    rec_promoted = fusion_engine.evaluate_source(
        candidate_id="SRC_TEMP_001",
        ra=270.0,
        dec=66.5,
        observation_id="OBS_001",
        observation_time="2026-11-08T00:00:00Z",
        chronos_score=9.0,
        chronos_temporal_eligibility="TRUE",
        is_known_gaia_star=False,
        continuum_sidecar=sidecar,
    )
    assert "CLASSIFICATION: NEW_TRANSIENT_OR_ASTEROID_CANDIDATE" in rec_promoted.evidence_summary


# =============================================================================
# Category 16: Backward compatibility with Phase 3 callers
# =============================================================================
def test_category_16_backward_compatibility_with_phase_3_callers(fusion_engine):
    """Test Category 16: Phase 3 positional and keyword callers remain valid."""
    p3_record = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="SRC_P3_001",
        pointing_id="2",
        color_excess_detected=True,
        continuum_anomaly_score=4.8,
        color_indices={"W1_W4_excess": 1.85},
        power_law_spectral_index=-1.2,
        excess_significance_sigma=3.9,
    )
    p3_record.validate()
    assert p3_record.observed_flux_mJy is None
    assert p3_record.primary_band is None
    assert p3_record.limitation_codes == []

    # Direct dictionary conversion works
    d = p3_record.to_dict()
    assert d["contract_version"] == SIDECAR_CONTRACT_VERSION
    assert d["color_excess_detected"] is True


# =============================================================================
# Additional EmpiricalContinuumSidecar Engine Tests
# =============================================================================
def test_empirical_sidecar_validate_assets(empirical_sidecar):
    """Verifies empirical sidecar photometric zero point calibration definitions."""
    assert empirical_sidecar.validate_sidecar_assets() is True


def test_empirical_sidecar_array_mismatch_fail_closed(empirical_sidecar):
    """Mismatched spectral array lengths fail closed with ValueError."""
    with pytest.raises(ValueError, match="Mismatched spectral array lengths"):
        empirical_sidecar.evaluate_continuum(
            source_id="SRC_001",
            pointing_id="P0008",
            wavelengths=[1.0, 2.0],
            fluxes=[10.0],
            uncertainties=[1.0, 1.0],
            valid_mask=[True, True],
        )


def test_empirical_sidecar_evaluate_continuum_blind_cohort(empirical_sidecar):
    """Blind cohort evaluations must attach BLIND_COHORT_UNVERIFIED_BASELINE."""
    rec = empirical_sidecar.evaluate_continuum(
        source_id="SRC_BLIND_001",
        pointing_id="P0002",
        wavelengths=[1.0, 2.0, 4.5],
        fluxes=[10.0, 10.0, 10.0],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=None,
    )
    assert "BLIND_COHORT_UNVERIFIED_BASELINE" in rec.limitation_codes
    assert rec.quality_status == "UNVERIFIABLE"
    assert rec.color_excess_detected is False


def test_empirical_sidecar_evaluate_continuum_with_photometric_record(empirical_sidecar):
    """Evaluates empirical sidecar with NormalizedSourceRecord."""
    norm_rec = NormalizedSourceRecord(
        source_id=12345,
        ra_deg=270.0,
        dec_deg=66.5,
        cohort_pointing="P0008",
        measurements={
            "WISE_W1": NormalizedMeasurement(
                band_name="WISE_W1",
                catalog_source="ALLWISE",
                effective_wavelength_microns=3.35,
                magnitude=12.0,
                magnitude_error=0.03,
                flux_density_mJy=9.5,
                flux_uncertainty_mJy=0.26,
                is_upper_limit=False,
                quality_flag="A",
            ),
            "WISE_W2": NormalizedMeasurement(
                band_name="WISE_W2",
                catalog_source="ALLWISE",
                effective_wavelength_microns=4.60,
                magnitude=11.5,
                magnitude_error=0.03,
                flux_density_mJy=8.8,
                flux_uncertainty_mJy=0.24,
                is_upper_limit=False,
                quality_flag="A",
            ),
            "2MASS_Ks": NormalizedMeasurement(
                band_name="2MASS_Ks",
                catalog_source="2MASS",
                effective_wavelength_microns=2.159,
                magnitude=12.5,
                magnitude_error=0.04,
                flux_density_mJy=6.7,
                flux_uncertainty_mJy=0.25,
                is_upper_limit=False,
                quality_flag="A",
            ),
        },
    )

    sidecar = empirical_sidecar.evaluate_continuum(
        source_id="12345",
        pointing_id="P0008",
        wavelengths=[4.4, 4.5, 4.6],
        fluxes=[8.5, 8.7, 8.8],
        uncertainties=[0.5, 0.5, 0.5],
        valid_mask=[True, True, True],
        photometric_record=norm_rec,
    )

    assert sidecar.contract_version == SIDECAR_CONTRACT_VERSION
    assert sidecar.source_id == "12345"
    assert sidecar.pointing_id == "P0008"
    assert sidecar.evidence_state in ALLOWED_EVIDENCE_STATES
    assert "EMPIRICAL_COLOR_BASELINE_ONLY" in sidecar.limitation_codes
    assert "INDEPENDENT_ERROR_QUADRATURE_ASSUMPTION" in sidecar.limitation_codes
    assert "PRELIMINARY_FLUX_SCALE_CONSISTENCY_CHECK" in sidecar.limitation_codes
    assert sidecar.metadata["spherex_overlap_channel_count"] == 3

