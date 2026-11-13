"""
SPECTRA-X / F1 — Phase 3, Task 1.3K
Comprehensive Unit & Regression Test Suite for CHRONOS-X Temporal Eligibility & FUSION-X Safety Gate

Mandatory Test Coverage:
 1. Same-visit dither with 2.15-6.47 minute separation -> FALSE.
 2. Concurrent cross-detector pair -> FALSE.
 3. Independent pair with missing essential metadata -> UNVERIFIABLE.
 4. Independent pair with missing WCS evidence -> UNVERIFIABLE / no temporal promotion.
 5. Incompatible calibration or spectral band -> FALSE / no temporal promotion.
 6. Valid independent pair satisfying all 10 requirements -> TRUE.
 7. >5-sigma residual + no Gaia counterpart + no valid temporal evidence -> must NOT receive NEW_TRANSIENT_OR_ASTEROID_CANDIDATE.
 8. No genuine multi-epoch observations -> TEMPORAL_DATA_UNAVAILABLE.
 9. Dither pairs remain usable for registration and artifact/dipole vetting.
10. Synthetic pairs cannot be represented as real astronomical discoveries.
11. Missing metadata produces structured UNVERIFIABLE provenance instead of silent pair deletion.
12. Existing non-temporal anomaly classifications continue to work.
"""

import os
import sys
import pytest
import numpy as np
import pandas as pd

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.chronos_x.temporal_eligibility import (
    evaluate_pair_temporal_eligibility,
    determine_dataset_temporal_availability,
    TemporalEligibilityResult,
    DEFAULT_MIN_BASELINE_DAYS,
    BASELINE_POLICY_VERSION,
    ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES,
)
from models.fusion.fusion_engine import FusionEngine
from models.common.candidate_schema import (
    CandidateRecord,
    ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES as SCHEMA_TEMPORAL_STATUSES,
)
import scripts.inspect_fits as inspect_fits


# =============================================================================
# Helper Fixtures
# =============================================================================

@pytest.fixture
def fusion_engine():
    return FusionEngine()


@pytest.fixture
def base_obs_1():
    return {
        "filename": "SPHEREX_L2_PTG0010_1D1_DET1.fits",
        "obsid": "0010_1D1",
        "pointing": "0010",
        "dither": 1,
        "detector": 1,
        "channel": "BAND1",
        "release": "QR3",
        "cal_version": "v27",
        "mjd_obs": 60898.3411,
        "ra_deg": 270.00,
        "dec_deg": 66.50,
        "wcs_available": True,
        "variance_available": True,
        "flags_available": True,
        "validation_status": "VALID",
    }


@pytest.fixture
def base_obs_2():
    # 14 days later, same pointing, same detector, compatible calibration
    return {
        "filename": "SPHEREX_L2_PTG0010_1D1_DET1_REVISIT.fits",
        "obsid": "0010_REVISIT_1D1",
        "pointing": "0010",
        "dither": 1,
        "detector": 1,
        "channel": "BAND1",
        "release": "QR3",
        "cal_version": "v27",
        "mjd_obs": 60912.3411,  # dt = 14.0 days
        "ra_deg": 270.00,
        "dec_deg": 66.50,
        "wcs_available": True,
        "variance_available": True,
        "flags_available": True,
        "validation_status": "VALID",
    }


# =============================================================================
# Requirement 1: Same-Visit Dither (2.15 - 6.47 min) -> FALSE
# =============================================================================

def test_same_visit_dither_rejected(base_obs_1):
    """Test 1: Same-visit dither with 2.15-6.47 minute separation must be FALSE."""
    dither_obs = dict(base_obs_1)
    dither_obs["filename"] = "SPHEREX_L2_PTG0010_4D1_DET1.fits"
    dither_obs["obsid"] = "0010_4D1"
    dither_obs["dither"] = 4
    dither_obs["mjd_obs"] = base_obs_1["mjd_obs"] + (6.47 / 1440.0)  # dt = 6.47 minutes = 0.00449 days

    res = evaluate_pair_temporal_eligibility(base_obs_1, dither_obs)
    assert res.status == "FALSE"
    assert res.is_dither is True
    assert res.evidence_tier == "E4"  # E4 completeness is achieved independent of temporal baseline!
    assert any("below operational minimum baseline" in r.lower() for r in res.reasons)


# =============================================================================
# Requirement 2: Concurrent Cross-Detector Pair -> FALSE
# =============================================================================

def test_concurrent_cross_detector_rejected(base_obs_1):
    """Test 2: Concurrent cross-detector observations must be FALSE."""
    cross_det_obs = dict(base_obs_1)
    cross_det_obs["filename"] = "SPHEREX_L2_PTG0010_1D1_DET2.fits"
    cross_det_obs["detector"] = 2  # Different detector (different passband)
    cross_det_obs["mjd_obs"] = base_obs_1["mjd_obs"] + 0.0001  # simultaneous

    res = evaluate_pair_temporal_eligibility(base_obs_1, cross_det_obs)
    assert res.status == "FALSE"
    assert any("incompatible detectors" in r.lower() for r in res.reasons)
    assert res.evidence_tier != "E2"  # Cannot reach E2 with mismatched detectors


# =============================================================================
# Requirement 3: Missing Essential Metadata -> UNVERIFIABLE
# =============================================================================

def test_missing_timestamp_unverifiable(base_obs_1, base_obs_2):
    """Test 3: Missing observation timestamp produces UNVERIFIABLE with provenance."""
    obs_no_time = dict(base_obs_2)
    obs_no_time["mjd_obs"] = None

    res = evaluate_pair_temporal_eligibility(base_obs_1, obs_no_time)
    assert res.status == "UNVERIFIABLE"
    assert "MISSING_OBSERVATION_TIMESTAMPS" in res.missing_evidence


# =============================================================================
# Requirement 4: Missing WCS Evidence -> UNVERIFIABLE / No Promotion
# =============================================================================

def test_missing_wcs_unverifiable(base_obs_1, base_obs_2):
    """Test 4: Missing WCS footprint evidence produces UNVERIFIABLE."""
    obs_no_wcs = dict(base_obs_2)
    obs_no_wcs["wcs_available"] = False

    res = evaluate_pair_temporal_eligibility(base_obs_1, obs_no_wcs)
    assert res.status == "UNVERIFIABLE"
    assert "MISSING_WCS_OVERLAP_EVIDENCE" in res.missing_evidence


# =============================================================================
# Requirement 5: Incompatible Calibration or Band -> FALSE
# =============================================================================

def test_incompatible_calibration_rejected(base_obs_1, base_obs_2):
    """Test 5A: Cross-release incompatible calibration (QR2 vs QR3) is FALSE."""
    obs_qr2 = dict(base_obs_2)
    obs_qr2["release"] = "QR2"

    res = evaluate_pair_temporal_eligibility(base_obs_1, obs_qr2)
    assert res.status == "FALSE"
    assert any("incompatible pipeline releases" in r.lower() for r in res.reasons)


def test_incompatible_spectral_band_rejected(base_obs_1, base_obs_2):
    """Test 5B: Incompatible spectral channels are FALSE."""
    obs_band2 = dict(base_obs_2)
    obs_band2["channel"] = "BAND2"

    res = evaluate_pair_temporal_eligibility(base_obs_1, obs_band2)
    assert res.status == "FALSE"
    assert any("incompatible spectral channels" in r.lower() for r in res.reasons)


# =============================================================================
# Requirement 6: Valid Independent Pair -> TRUE
# =============================================================================

def test_valid_independent_pair_accepted(base_obs_1, base_obs_2):
    """Test 6: Valid independent observation pair meeting all checks receives TRUE."""
    res = evaluate_pair_temporal_eligibility(base_obs_1, base_obs_2)
    assert res.status == "TRUE"
    assert res.evidence_tier == "E4"
    assert res.is_dither is False
    assert res.dt_days == 14.0
    assert any("independent observation epochs verified" in r.lower() for r in res.reasons)


# =============================================================================
# Requirement 7: FUSION-X Safety Gate: No Transient Promotion Without TRUE
# =============================================================================

def test_fusion_blocks_transient_without_temporal_eligibility(fusion_engine):
    """Test 7A: >5-sigma residual + no Gaia star + no temporal eligibility must NOT become transient."""
    # Scenario: High temporal residual (sig=8.5) from intra-visit dither (eligibility='FALSE')
    record = fusion_engine.evaluate_source(
        candidate_id="SRC_DITHER_FALSE_001",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        chronos_score=8.5,  # > 5.0 sigma
        chronos_temporal_eligibility="FALSE",  # Dither pair
        is_known_gaia_star=False
    )
    # Must NOT be promoted to NEW_TRANSIENT_OR_ASTEROID_CANDIDATE
    assert "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE" not in record.evidence_summary
    assert "CLASSIFICATION: ANOMALOUS_RESIDUAL_REQUIRES_REVIEW" in record.evidence_summary
    assert record.metadata.get("chronos_temporal_eligibility") == "FALSE"
    assert record.temporal_eligibility == "FALSE"


def test_fusion_blocks_transient_when_unverifiable(fusion_engine):
    """Test 7B: >5-sigma residual + UNVERIFIABLE temporal eligibility must NOT become transient."""
    record = fusion_engine.evaluate_source(
        candidate_id="SRC_UNVERIFIED_002",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        chronos_score=12.0,
        chronos_temporal_eligibility="UNVERIFIABLE",
        is_known_gaia_star=False
    )
    assert "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE" not in record.evidence_summary
    assert "CLASSIFICATION: ANOMALOUS_RESIDUAL_REQUIRES_REVIEW" in record.evidence_summary
    assert record.validity_status == "WARNING"


def test_fusion_promotes_transient_when_temporal_eligibility_true(fusion_engine):
    """Test 7C (Positive Path): >5-sigma residual + TRUE temporal eligibility DOES become transient."""
    record = fusion_engine.evaluate_source(
        candidate_id="SRC_GENUINE_TRANSIENT_003",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        chronos_score=9.2,
        chronos_temporal_eligibility="TRUE",
        chronos_evidence_tier="E4",
        is_known_gaia_star=False
    )
    assert "CLASSIFICATION: NEW_TRANSIENT_OR_ASTEROID_CANDIDATE" in record.evidence_summary
    assert record.metadata.get("chronos_temporal_eligibility") == "TRUE"
    assert record.temporal_eligibility == "TRUE"


def test_fusion_stellar_variability_with_gaia_and_true_eligibility(fusion_engine):
    """Test 7D (Positive Path): >5-sigma residual + TRUE temporal eligibility + Gaia star becomes flare/variability."""
    record = fusion_engine.evaluate_source(
        candidate_id="SRC_STELLAR_FLARE_004",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        chronos_score=7.0,
        chronos_temporal_eligibility="TRUE",
        is_known_gaia_star=True,
        gaia_source_id="GAIA_DR3_123456"
    )
    assert "CLASSIFICATION: STELLAR_VARIABILITY_OR_FLARE" in record.evidence_summary


# =============================================================================
# Requirement 8: Dataset-Level Availability -> TEMPORAL_DATA_UNAVAILABLE
# =============================================================================

def test_dataset_level_availability_reporting(base_obs_1):
    """Test 8: System reports TEMPORAL_DATA_UNAVAILABLE if only dithers or no TRUE pairs exist."""
    dither_obs = dict(base_obs_1)
    dither_obs["mjd_obs"] = base_obs_1["mjd_obs"] + 0.002
    dither_obs["dither"] = 2

    res_dither = evaluate_pair_temporal_eligibility(base_obs_1, dither_obs)
    assert determine_dataset_temporal_availability([res_dither]) == "TEMPORAL_DATA_UNAVAILABLE"

    # Empty list
    assert determine_dataset_temporal_availability([]) == "TEMPORAL_DATA_UNAVAILABLE"


# =============================================================================
# Requirement 9: Dither Pairs Remain Usable for Registration & Artifact Vetting
# =============================================================================

def test_dither_usable_for_registration_and_dipole_vetting(base_obs_1):
    """Test 9: Dithers achieve E4 completeness and are tagged usable for registration."""
    dither_obs = dict(base_obs_1)
    dither_obs["mjd_obs"] = base_obs_1["mjd_obs"] + 0.003
    dither_obs["dither"] = 3

    res = evaluate_pair_temporal_eligibility(base_obs_1, dither_obs)
    assert res.status == "FALSE"  # Ineligible for secular variability
    assert res.evidence_tier == "E4"  # Fully usable for registration
    assert res.metadata.get("usable_for_registration") is True
    assert res.metadata.get("usable_for_dipole_vetting") is True


# =============================================================================
# Requirement 10: Synthetic Pairs Cannot Disguise Missing Availability
# =============================================================================

def test_synthetic_pairs_do_not_fabricate_dataset_availability():
    """Test 10: Synthetic pairs are excluded from dataset-level availability."""
    synth_pair = {
        "status": "TRUE",
        "is_synthetic": True,
        "metadata": {"is_synthetic": True}
    }
    # Synthetic must not trick system into TEMPORAL_DATA_AVAILABLE
    assert determine_dataset_temporal_availability([synth_pair], exclude_synthetic=True) == "TEMPORAL_DATA_UNAVAILABLE"


# =============================================================================
# Requirement 11: Structured UNVERIFIABLE Provenance (No Silent Deletion)
# =============================================================================

def test_structured_unverifiable_provenance():
    """Test 11: Missing metadata produces structured UNVERIFIABLE records with explicit missing fields."""
    incomplete_df = pd.DataFrame([
        {
            "filename": "FILE_A.fits",
            "release": "QR3",
            "validation_status": "VALID",
            "mjd_obs": 60898.10,
            "ra_deg": 270.0,
            "dec_deg": 66.5,
            "detector": 1,
            "wcs_available": True,
            "variance_available": True,
            "flags_available": True
        },
        {
            "filename": "FILE_B_CORRUPT_META.fits",
            "release": "QR3",
            "validation_status": "VALID",
            "mjd_obs": np.nan,  # Missing timestamp
            "ra_deg": 270.0,
            "dec_deg": 66.5,
            "detector": 1,
            "wcs_available": True,
            "variance_available": True,
            "flags_available": True
        }
    ])

    pairs = inspect_fits.find_temporal_pairs(incomplete_df, include_all_for_registration=True)
    assert len(pairs) == 1
    p = pairs[0]
    assert p["temporal_eligibility"] == "UNVERIFIABLE"
    assert "MISSING_OBSERVATION_TIMESTAMPS" in p["missing_evidence"]


# =============================================================================
# Requirement 12: Existing Non-Temporal Classifications Continue to Work
# =============================================================================

def test_non_temporal_anomaly_classifications_preserved(fusion_engine):
    """Test 12: Non-temporal anomaly classifications continue functioning unaffected."""
    # 1. Multi-modal anomaly (spectra + astrovision)
    rec_multimodal = fusion_engine.evaluate_source(
        candidate_id="SRC_MULTIMODAL_001",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        spectra_score=0.015,  # > 0.005 threshold
        astrovision_score=6.2  # > 4.0 threshold
    )
    assert "CLASSIFICATION: MULTI_MODAL_CO_PILOT_ANOMALY" in rec_multimodal.evidence_summary

    # 2. Extreme spectral outlier
    rec_spectral = fusion_engine.evaluate_source(
        candidate_id="SRC_SPECTRAL_002",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        spectra_score=0.020,
        astrovision_score=1.0
    )
    assert "CLASSIFICATION: EXTREME_SPECTRAL_OUTLIER" in rec_spectral.evidence_summary

    # 3. Extended spatial structure
    rec_spatial = fusion_engine.evaluate_source(
        candidate_id="SRC_SPATIAL_003",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        spectra_score=0.001,
        astrovision_score=5.5
    )
    assert "CLASSIFICATION: EXTENDED_OR_UNUSUAL_SPATIAL_STRUCTURE" in rec_spatial.evidence_summary

    # 4. Confirmed transient (ZTF match)
    rec_ztf = fusion_engine.evaluate_source(
        candidate_id="SRC_ZTF_004",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        spectra_score=0.001,
        is_known_transient=True,
        transient_name="ZTF25aabcyza"
    )
    assert "CLASSIFICATION: CONFIRMED_ASTRONOMICAL_TRANSIENT" in rec_ztf.evidence_summary

    # 5. Known asteroid
    rec_asteroid = fusion_engine.evaluate_source(
        candidate_id="SRC_ASTEROID_005",
        ra=270.0,
        dec=66.5,
        observation_id="0010_1D1",
        observation_time="2025-08-01T00:00:00",
        spectra_score=0.001,
        is_known_asteroid=True,
        asteroid_name="Ceres"
    )
    assert "CLASSIFICATION: KNOWN_SOLAR_SYSTEM_OBJECT" in rec_asteroid.evidence_summary


# =============================================================================
# CandidateRecord Schema & Serialization Compliance
# =============================================================================

def test_candidate_record_schema_serialization():
    """Validates schema validation and JSON round-trip serialization for temporal eligibility."""
    rec = CandidateRecord(
        candidate_id="TEST_REC_001",
        ra=180.0,
        dec=0.0,
        observation_id="OBS001",
        observation_time="2026-01-01",
        module_name="FUSION-X",
        anomaly_score=0.85,
        score_type="HEURISTIC_PRIORITY_SCORE",
        validity_status="VALID",
        evidence_summary="TEST EVIDENCE",
        input_provenance="TEST",
        temporal_eligibility="TRUE"
    )
    d = rec.to_dict()
    assert d["temporal_eligibility"] == "TRUE"

    # Round-trip
    rec_recovered = CandidateRecord.from_dict(d)
    assert rec_recovered.temporal_eligibility == "TRUE"

    # Invalid status raises ValueError
    with pytest.raises(ValueError):
        CandidateRecord(
            candidate_id="TEST_REC_INVALID",
            ra=180.0,
            dec=0.0,
            observation_id="OBS001",
            observation_time="2026-01-01",
            module_name="FUSION-X",
            anomaly_score=0.85,
            score_type="HEURISTIC_PRIORITY_SCORE",
            validity_status="VALID",
            evidence_summary="TEST",
            input_provenance="TEST",
            temporal_eligibility="INVALID_STATUS"
        )
