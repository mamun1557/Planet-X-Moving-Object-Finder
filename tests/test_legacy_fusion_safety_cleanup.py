"""
SPECTRA-X / F1 — Phase 3, Task 1.3M
Focused Regression Tests for Legacy FUSION Prototype Safety Cleanup

Verifies:
 1. Legacy prototype (FusionRanker.classify_candidate) blocks transient promotion when temporal status is missing.
 2. Legacy prototype blocks transient promotion when temporal status is FALSE.
 3. Legacy prototype blocks transient promotion when temporal status is UNVERIFIABLE.
 4. Legacy prototype blocks transient promotion when temporal status is None.
 5. Legacy prototype blocks transient promotion when temporal status is malformed or unsupported.
 6. Legacy prototype allows transient promotion ONLY when temporal status is explicitly TRUE.
 7. Legacy prototype stellar variability gating on known stars.
 8. Legacy prototype non-temporal classification preservation.
 9. Production FusionEngine (models/fusion/fusion_engine.py) behavior remains completely unchanged.
10. Legacy prototype cannot bypass production safety contract.
"""

import os
import sys
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.fusion_x.model import FusionRanker
from models.fusion.fusion_engine import FusionEngine


# =============================================================================
# Legacy FusionRanker Safety Gate Tests
# =============================================================================

def test_legacy_prototype_status_missing():
    """Test 1: temporal_sig > 5, no known star, temporal status omitted -> No transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=8.5,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False
        # chronos_temporal_eligibility omitted -> defaults to None
    )
    assert tag != "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    assert tag == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


def test_legacy_prototype_status_false():
    """Test 2: temporal_sig > 5, status = FALSE -> No transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=9.2,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility="FALSE"
    )
    assert tag != "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    assert tag == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


def test_legacy_prototype_status_unverifiable():
    """Test 3: temporal_sig > 5, status = UNVERIFIABLE -> No transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=10.0,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility="UNVERIFIABLE"
    )
    assert tag != "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    assert tag == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


def test_legacy_prototype_status_none():
    """Test 4: temporal_sig > 5, status = None -> No transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=7.1,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility=None
    )
    assert tag != "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    assert tag == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


@pytest.mark.parametrize("invalid_status", ["INVALID", "true", "True", "UNKNOWN", 12345, ""])
def test_legacy_prototype_status_malformed(invalid_status):
    """Test 5: temporal_sig > 5, malformed/unsupported status -> No transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=8.0,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility=invalid_status
    )
    assert tag != "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"
    assert tag == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


def test_legacy_prototype_status_true_promotes():
    """Test 6: temporal_sig > 5, status = TRUE -> Permitted transient promotion."""
    tag = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=8.0,
        is_known_star=False,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility="TRUE"
    )
    assert tag == "NEW_TRANSIENT_OR_ASTEROID_CANDIDATE"


def test_legacy_prototype_stellar_variability_gate():
    """Test 7: Stellar variability gating on known stars."""
    # When TRUE -> STELLAR_VARIABILITY_OR_FLARE
    tag_true = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=8.0,
        is_known_star=True,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility="TRUE"
    )
    assert tag_true == "STELLAR_VARIABILITY_OR_FLARE"

    # When FALSE without spatial anomaly -> ANOMALOUS_RESIDUAL_REQUIRES_REVIEW
    tag_false = FusionRanker.classify_candidate(
        spatial_score=1.0,
        spectral_score=1.0,
        temporal_sig=8.0,
        is_known_star=True,
        is_known_asteroid=False,
        is_known_transient=False,
        chronos_temporal_eligibility="FALSE"
    )
    assert tag_false == "ANOMALOUS_RESIDUAL_REQUIRES_REVIEW"


def test_legacy_prototype_non_temporal_paths():
    """Test 8: Invariance of non-temporal prototype classification rules."""
    # Known asteroid
    assert FusionRanker.classify_candidate(
        spatial_score=0.5, spectral_score=0.5, temporal_sig=1.0,
        is_known_star=False, is_known_asteroid=True, is_known_transient=False
    ) == "KNOWN_SOLAR_SYSTEM_OBJECT"

    # Confirmed transient
    assert FusionRanker.classify_candidate(
        spatial_score=0.5, spectral_score=0.5, temporal_sig=1.0,
        is_known_star=False, is_known_asteroid=False, is_known_transient=True
    ) == "CONFIRMED_ASTRONOMICAL_TRANSIENT"

    # Spectral anomaly
    assert FusionRanker.classify_candidate(
        spatial_score=0.5, spectral_score=4.5, temporal_sig=1.0,
        is_known_star=False, is_known_asteroid=False, is_known_transient=False
    ) == "INFRARED_SPECTRAL_ANOMALY"

    # Spatial star structure
    assert FusionRanker.classify_candidate(
        spatial_score=4.5, spectral_score=0.5, temporal_sig=1.0,
        is_known_star=True, is_known_asteroid=False, is_known_transient=False
    ) == "STELLAR_VARIABILITY_OR_FLARE"

    # Baseline background
    assert FusionRanker.classify_candidate(
        spatial_score=0.5, spectral_score=0.5, temporal_sig=1.0,
        is_known_star=False, is_known_asteroid=False, is_known_transient=False
    ) == "BACKGROUND_OR_INSTRUMENTAL_RESIDUAL"


# =============================================================================
# Production FUSION-X Invariance Verification
# =============================================================================

def test_production_fusion_engine_unchanged():
    """Test 9: Production FusionEngine behavior remains completely unchanged."""
    fe = FusionEngine()

    # Blocked without TRUE
    rec_blocked = fe.evaluate_source(
        candidate_id="TEST_PROD_BLOCKED",
        ra=270.0, dec=66.5,
        observation_id="OBS001",
        observation_time="2025-08-01",
        chronos_score=9.0,
        chronos_temporal_eligibility="FALSE",
        is_known_gaia_star=False
    )
    assert "CLASSIFICATION: ANOMALOUS_RESIDUAL_REQUIRES_REVIEW" in rec_blocked.evidence_summary

    # Promoted with TRUE
    rec_promoted = fe.evaluate_source(
        candidate_id="TEST_PROD_PROMOTED",
        ra=270.0, dec=66.5,
        observation_id="OBS001",
        observation_time="2025-08-01",
        chronos_score=9.0,
        chronos_temporal_eligibility="TRUE",
        is_known_gaia_star=False
    )
    assert "CLASSIFICATION: NEW_TRANSIENT_OR_ASTEROID_CANDIDATE" in rec_promoted.evidence_summary

