"""
SPECTRA-X / F1 — Phase 3, Task 1.3A
Comprehensive Unit and Integration Test Suite for SPECTRA-to-FUSION-X Contract & Adapter

Acceptance Criteria:
 1. Correct checkpoint and threshold hash verification.
 2. Incorrect hash causes a safe failure.
 3. Valid D1+D4 normalization.
 4. Valid D2+D5 normalization.
 5. Valid D3+D6 normalization.
 6. Cross-stratum normalization rejection.
 7. Fewer than five channels becomes UNINFORMATIVE.
 8. Zero coverage becomes NO_OBSERVATIONAL_COVERAGE.
 9. Invalid quality flags cause rejection.
10. Missing normalization reference is handled safely.
11. Provisional threshold semantics remain correct.
12. No false claim of verified FPR.
13. Limitation codes are preserved.
14. Cross-modal evidence can be absent without fabrication.
15. Deterministic contract serialization.
16. Contract schema validation.
17. Frozen asset hashes remain unchanged.
18. Existing SPECTRA tests continue passing.
"""

import os
import sys
import json
import tempfile
import pytest
import numpy as np

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from models.spectra.fusion_contract import (
    CONTRACT_VERSION,
    MODEL_ID,
    EXPECTED_CHECKPOINT_SHA256,
    EXPECTED_THRESHOLDS_SHA256,
    EXPECTED_CALIB_SCORES_SHA256,
    BASE_LIMITATION_CODES,
    EligibilityStatus,
    ThresholdExceedanceLevel,
    EvidenceStrength,
    CrossModalStatus,
    SpectraFusionEvidenceRecord,
)
from models.spectra.spectra_evidence_adapter import SpectraEvidenceAdapter
from models.spectra.continuum_sidecar_interface import (
    ContinuumSidecarInterface,
    ContinuumEvidenceRecord,
    SIDECAR_CONTRACT_VERSION,
)


@pytest.fixture
def adapter():
    """Provides an initialized SpectraEvidenceAdapter with verified assets."""
    return SpectraEvidenceAdapter()


# 1. Correct checkpoint and threshold hash verification
def test_correct_asset_hash_verification(adapter):
    res = adapter.validate_assets(raise_on_error=True)
    assert res["all_verified"] is True
    assert res["checkpoint"]["status"] == "VERIFIED_IMMUTABLE"
    assert res["thresholds"]["status"] == "VERIFIED_IMMUTABLE"
    assert res["calib_scores"]["status"] == "VERIFIED_IMMUTABLE"
    assert adapter.assets_verified is True


# 2. Incorrect hash causes a safe failure
def test_incorrect_hash_causes_safe_failure():
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write("corrupted model weights")
        corrupted_path = tf.name

    try:
        # Without raise_on_error
        bad_adapter = SpectraEvidenceAdapter(checkpoint_path=corrupted_path, auto_load=False)
        res = bad_adapter.validate_assets(raise_on_error=False)
        assert res["all_verified"] is False
        assert res["checkpoint"]["status"] == "HASH_MISMATCH"

        # With raise_on_error
        with pytest.raises(ValueError, match="Hash mismatch for checkpoint"):
            bad_adapter.validate_assets(raise_on_error=True)
    finally:
        if os.path.exists(corrupted_path):
            os.remove(corrupted_path)


# 3. Valid D1+D4 normalization
def test_valid_d1_d4_normalization(adapter):
    # D1,D4 median is ~0.4237, T05 is ~4.1275, T01 is ~61.2676
    p_med, z_med = adapter.normalize_score(0.423665, "D1,D4")
    assert 0.49 <= p_med <= 0.51
    assert -0.05 <= z_med <= 0.05

    p_t05, z_t05 = adapter.normalize_score(4.127549, "D1,D4")
    assert 0.94 <= p_t05 <= 0.96
    assert z_t05 > 7.0

    p_t01, z_t01 = adapter.normalize_score(61.267565, "D1,D4")
    assert 0.985 <= p_t01 <= 0.995
    assert z_t01 > 100.0


# 4. Valid D2+D5 normalization
def test_valid_d2_d5_normalization(adapter):
    # D2,D5 median is ~0.3689, T05 is ~5.5158, T01 is ~181.6013
    p_med, z_med = adapter.normalize_score(0.368894, "D2,D5")
    assert 0.49 <= p_med <= 0.51
    assert -0.05 <= z_med <= 0.05

    p_t05, z_t05 = adapter.normalize_score(5.515796, "D2,D5")
    assert 0.94 <= p_t05 <= 0.96

    p_t01, z_t01 = adapter.normalize_score(181.601329, "D2,D5")
    assert 0.985 <= p_t01 <= 0.995


# 5. Valid D3+D6 normalization
def test_valid_d3_d6_normalization(adapter):
    # D3,D6 median is ~1.4255, T05 is ~19.2666, T01 is ~862.9723
    p_med, z_med = adapter.normalize_score(1.425457, "D3,D6")
    assert 0.49 <= p_med <= 0.51
    assert -0.05 <= z_med <= 0.05

    p_t05, z_t05 = adapter.normalize_score(19.266649, "D3,D6")
    assert 0.94 <= p_t05 <= 0.96

    p_t01, z_t01 = adapter.normalize_score(862.972346, "D3,D6")
    assert 0.985 <= p_t01 <= 0.995


# 6. Cross-stratum normalization rejection
def test_cross_stratum_normalization_rejection(adapter):
    # Attempting normalization with invalid stratum
    with pytest.raises(ValueError, match="Invalid detector stratum"):
        adapter.normalize_score(5.0, "INVALID_STRATUM")

    with pytest.raises(ValueError, match="Invalid detector stratum"):
        adapter.normalize_score(5.0, "GLOBAL_POOLED")


# 7. Fewer than five channels becomes UNINFORMATIVE
def test_fewer_than_five_channels_uninformative(adapter):
    for ch_count in [1, 2, 3, 4]:
        rec = adapter.create_evidence_record(
            source_id="TEST_SRC_01",
            pointing_id="2",
            detector_stratum="D1,D4",
            valid_channels_count=ch_count,
            raw_anomaly_score=10.5
        )
        assert rec.eligibility_status == EligibilityStatus.UNINFORMATIVE.value
        assert rec.raw_anomaly_score is None
        assert rec.stratum_normalized_percentile is None
        assert rec.anomaly_detected is False
        assert rec.evidence_strength == EvidenceStrength.UNINFORMATIVE.value
        assert "Insufficient channel coverage" in rec.interpretation


# 8. Zero coverage becomes NO_OBSERVATIONAL_COVERAGE
def test_zero_coverage_no_observational_coverage(adapter):
    rec = adapter.create_evidence_record(
        source_id="TEST_SRC_ZERO",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=0,
        raw_anomaly_score=None
    )
    assert rec.eligibility_status == EligibilityStatus.NO_OBSERVATIONAL_COVERAGE.value
    assert rec.raw_anomaly_score is None
    assert rec.anomaly_detected is False
    assert "Zero observed spectral channels" in rec.interpretation


# 9. Invalid quality flags cause rejection
def test_invalid_quality_flags_cause_rejection(adapter):
    # Quality flag 615 triggers fatal mask rejection
    rec = adapter.create_evidence_record(
        source_id="TEST_SRC_BAD",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=15.0,
        data_quality_flags=615
    )
    assert rec.eligibility_status == EligibilityStatus.QUALITY_REJECTED.value
    assert rec.raw_anomaly_score is None
    assert rec.anomaly_detected is False
    assert "Fatal quality flag trigger" in rec.interpretation


# 10. Missing normalization reference handled safely
def test_missing_normalization_reference_handled_safely():
    unloaded_adapter = SpectraEvidenceAdapter(auto_load=False)
    elig, reasons = unloaded_adapter.evaluate_eligibility(valid_channels_count=8, detector_stratum="D1,D4")
    assert elig == EligibilityStatus.NORMALIZATION_UNAVAILABLE
    assert "Calibration reference not loaded" in reasons[0]


# 11. Provisional threshold semantics remain correct
def test_provisional_threshold_semantics(adapter):
    # Nominal below T05
    rec_nom = adapter.create_evidence_record(
        source_id="SRC_NOMINAL",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=1.0
    )
    assert rec_nom.threshold_exceedance_level == ThresholdExceedanceLevel.NONE.value
    assert rec_nom.anomaly_detected is False

    # Exceeds T05 but below T01
    rec_t05 = adapter.create_evidence_record(
        source_id="SRC_T05",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=10.0
    )
    assert rec_t05.threshold_exceedance_level == ThresholdExceedanceLevel.EXCEEDS_T05.value
    assert rec_t05.anomaly_detected is True
    assert rec_t05.evidence_strength == EvidenceStrength.MARGINAL.value
    assert "provisional 95th percentile" in rec_t05.interpretation

    # Exceeds T01
    rec_t01 = adapter.create_evidence_record(
        source_id="SRC_T01",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=100.0
    )
    assert rec_t01.threshold_exceedance_level == ThresholdExceedanceLevel.EXCEEDS_T01.value
    assert rec_t01.anomaly_detected is True
    assert rec_t01.evidence_strength == EvidenceStrength.STRONG.value
    assert "provisional 99th percentile" in rec_t01.interpretation


# 12. No false claim of verified FPR
def test_no_false_claim_of_verified_fpr(adapter):
    rec = adapter.create_evidence_record(
        source_id="SRC_AUDIT",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=50.0
    )
    # Check that interpretation never claims verified FPR or confirmed astronomical discovery
    assert "verified false positive rate" not in rec.interpretation.lower()
    assert "certified fpr" not in rec.interpretation.lower()
    assert "confirmed astronomical discovery" not in rec.interpretation.lower()
    assert "autonomous discovery prohibited" in rec.interpretation.lower()


# 13. Limitation codes are preserved
def test_limitation_codes_preserved(adapter):
    rec_d1 = adapter.create_evidence_record(
        source_id="SRC_D1",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=2.0
    )
    for code in BASE_LIMITATION_CODES:
        assert code in rec_d1.limitation_codes

    # D3,D6 must also include D3_D6_REDUCED_SENSITIVITY
    rec_d3 = adapter.create_evidence_record(
        source_id="SRC_D3",
        pointing_id="10",
        detector_stratum="D3,D6",
        valid_channels_count=8,
        raw_anomaly_score=25.0
    )
    assert "D3_D6_REDUCED_SENSITIVITY" in rec_d3.limitation_codes


# 14. Cross-modal evidence can be absent without fabrication
def test_cross_modal_evidence_absence_without_fabrication(adapter):
    rec = adapter.create_evidence_record(
        source_id="SRC_UNIMODAL",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=3.0
    )
    assert rec.cross_modal_corroboration_status == CrossModalStatus.NO_CROSS_MODAL_DATA.value
    assert rec.astrovision_corroboration is None
    assert rec.chronos_corroboration is None
    assert rec.continuum_sidecar_corroboration is None

    # When supplied, it updates properly
    rec_corrob = adapter.create_evidence_record(
        source_id="SRC_CORROB",
        pointing_id="2",
        detector_stratum="D1,D4",
        valid_channels_count=8,
        raw_anomaly_score=15.0,
        astrovision_corroboration={"astrovision_score": 4.2, "morphology": "POINT_SOURCE"}
    )
    assert rec_corrob.cross_modal_corroboration_status == CrossModalStatus.CORROBORATED.value
    assert rec_corrob.astrovision_corroboration["morphology"] == "POINT_SOURCE"


# 15. Deterministic contract serialization
def test_deterministic_contract_serialization(adapter):
    rec = adapter.create_evidence_record(
        source_id="SRC_SERIAL",
        pointing_id="9",
        detector_stratum="D2,D5",
        valid_channels_count=10,
        raw_anomaly_score=4.5
    )
    d = adapter.serialize_evidence(rec, as_json=False)
    assert isinstance(d, dict)
    assert d["source_id"] == "SRC_SERIAL"
    assert d["contract_version"] == CONTRACT_VERSION

    json_str = adapter.serialize_evidence(rec, as_json=True)
    assert isinstance(json_str, str)
    
    # Round-trip reconstruction
    rec_reconstructed = SpectraFusionEvidenceRecord.from_json(json_str)
    assert rec_reconstructed.source_id == rec.source_id
    assert rec_reconstructed.raw_anomaly_score == rec.raw_anomaly_score
    assert rec_reconstructed.stratum_normalized_percentile == rec.stratum_normalized_percentile


# 16. Contract schema validation
def test_contract_schema_validation():
    # Attempt creating record with invalid contract version
    with pytest.raises(ValueError, match="Invalid contract_version"):
        SpectraFusionEvidenceRecord(
            contract_version="INVALID_VERSION_V0",
            model_id=MODEL_ID,
            model_version="v2.1",
            checkpoint_sha256=EXPECTED_CHECKPOINT_SHA256,
            threshold_artifact_sha256=EXPECTED_THRESHOLDS_SHA256,
            pipeline_build="l2b-v27-2026-222",
            inference_timestamp="2026-11-07T00:00:00Z",
            source_id="123",
            pointing_id="2",
            detector_stratum="D1,D4",
            provenance_reference="REF",
            raw_anomaly_score=1.0,
            stratum_normalized_percentile=0.5,
            optional_stratum_z_score=0.0,
            threshold_05=4.12,
            threshold_01=61.26,
            threshold_exceedance_level="NONE",
            valid_channel_count=8,
            channel_coverage_fraction=0.08,
            spectral_feature_scope="SCOPE",
            uncertainty_available=True,
            data_quality_flags=0,
            eligibility_status="ELIGIBLE",
            limitation_codes=BASE_LIMITATION_CODES,
            calibration_reference_version="v1",
            anomaly_detected=False,
            evidence_strength="NONE",
            interpretation="TEST",
            human_review_required=False
        )


# 17. Frozen asset hashes remain unchanged
def test_frozen_asset_hashes_remain_unchanged():
    adapter = SpectraEvidenceAdapter()
    for name, p, exp in [
        ("checkpoint", adapter.checkpoint_path, EXPECTED_CHECKPOINT_SHA256),
        ("thresholds", adapter.thresholds_path, EXPECTED_THRESHOLDS_SHA256),
        ("calib_scores", adapter.calib_scores_path, EXPECTED_CALIB_SCORES_SHA256)
    ]:
        act = adapter.compute_sha256(p)
        assert act == exp, f"Asset {name} hash changed! Expected {exp}, got {act}"


# 18. Continuum sidecar interface specification test
def test_continuum_sidecar_interface_specification():
    # Verify ContinuumEvidenceRecord definition and contract version
    rec = ContinuumEvidenceRecord(
        contract_version=SIDECAR_CONTRACT_VERSION,
        source_id="TEST_CONT_SRC",
        pointing_id="2",
        color_excess_detected=True,
        continuum_anomaly_score=4.8,
        color_indices={"W1_W4_excess": 1.85},
        power_law_spectral_index=-1.2,
        excess_significance_sigma=3.9
    )
    assert rec.contract_version == "CONTINUUM_SIDECAR_EVIDENCE_V1"
    assert rec.color_excess_detected is True
    assert rec.color_indices["W1_W4_excess"] == 1.85
