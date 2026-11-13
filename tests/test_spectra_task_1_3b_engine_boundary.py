"""
SPECTRA-X / F1 — Phase 3, Task 1.3B Test Suite
Authoritative Engine Boundary, Dependency Direction, and Mathematical Semantics Verification

Validates:
1. Authoritative location of contract and evidence adapter in spectra_engine
2. Strict dependency direction: spectra_engine does NOT import models.spectra
3. Absence of application framework dependencies (FastAPI, SQLite, etc.)
4. Full backward compatibility of models.spectra re-export shims (object identity 'is')
5. Mathematical semantics and invariance of empirical percentile and IQR-scaled deviation
6. Defensive guard against non-positive IQR
7. Immutability of frozen scientific assets
"""

import sys
import os
import subprocess
import pytest
import numpy as np

# Ensure repository root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def test_authoritative_package_location():
    """Verify that spectra_engine exposes authoritative symbols directly."""
    import spectra_engine as se
    from spectra_engine.fusion_contract import SpectraFusionEvidenceRecord, CONTRACT_VERSION
    from spectra_engine.spectra_evidence_adapter import SpectraEvidenceAdapter
    from spectra_engine.continuum_sidecar_interface import ContinuumSidecarInterface, ContinuumEvidenceRecord

    assert se.CONTRACT_VERSION == "SPECTRA_FUSION_EVIDENCE_V1"
    assert se.MODEL_ID == "SPECTRA_Masked_AE_v2"
    assert se.MODEL_VERSION == "v2.1"
    assert se.SpectraEvidenceAdapter is SpectraEvidenceAdapter
    assert se.SpectraFusionEvidenceRecord is SpectraFusionEvidenceRecord
    assert se.ContinuumSidecarInterface is ContinuumSidecarInterface
    assert se.ContinuumEvidenceRecord is ContinuumEvidenceRecord


def test_dependency_direction_isolation_isolated_subprocess():
    """
    Verify in a fresh isolated Python process that importing spectra_engine
    does NOT trigger any import of models or models.spectra.
    """
    code = (
        "import sys\n"
        "import spectra_engine\n"
        "models_modules = [m for m in sys.modules if m.startswith('models')]\n"
        "if models_modules:\n"
        "    print(f'FAILURE: Loaded models: {models_modules}', file=sys.stderr)\n"
        "    sys.exit(1)\n"
        "print('SUCCESS: Zero models dependencies')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )
    assert result.returncode == 0, f"Dependency isolation failed: {result.stderr}"
    assert "SUCCESS: Zero models dependencies" in result.stdout


def test_no_application_framework_dependencies():
    """Verify that spectra_engine has no imports of web/app frameworks or databases."""
    forbidden = ["fastapi", "flask", "starlette", "sqlalchemy", "sqlite3", "torch"]
    for mod in forbidden:
        code = (
            f"import sys\n"
            f"import spectra_engine\n"
            f"if '{mod}' in sys.modules:\n"
            f"    sys.exit(1)\n"
            f"sys.exit(0)\n"
        )
        res = subprocess.run([sys.executable, "-c", code], capture_output=True, cwd=BASE_DIR)
        assert res.returncode == 0, f"spectra_engine unexpectedly imported {mod}!"


def test_backward_compatibility_shims_object_identity():
    """
    Verify that importing from legacy models.spectra paths works seamlessly
    and returns identical object references (x is y).
    """
    import spectra_engine as se
    import models.spectra as ms
    from models.spectra.fusion_contract import (
        SpectraFusionEvidenceRecord as ShimRecord,
        CONTRACT_VERSION as SHIM_VERSION,
        EligibilityStatus as ShimStatus,
    )
    from models.spectra.spectra_evidence_adapter import SpectraEvidenceAdapter as ShimAdapter
    from models.spectra.continuum_sidecar_interface import (
        ContinuumSidecarInterface as ShimSidecar,
        ContinuumEvidenceRecord as ShimSidecarRecord,
    )

    # Top-level package re-exports
    assert ms.SpectraEvidenceAdapter is se.SpectraEvidenceAdapter
    assert ms.SpectraFusionEvidenceRecord is se.SpectraFusionEvidenceRecord
    assert ms.ContinuumSidecarInterface is se.ContinuumSidecarInterface
    assert ms.ContinuumEvidenceRecord is se.ContinuumEvidenceRecord
    assert ms.CONTRACT_VERSION == se.CONTRACT_VERSION

    # Submodule re-exports
    assert ShimAdapter is se.SpectraEvidenceAdapter
    assert ShimRecord is se.SpectraFusionEvidenceRecord
    assert SHIM_VERSION == se.CONTRACT_VERSION
    assert ShimStatus is se.EligibilityStatus
    assert ShimSidecar is se.ContinuumSidecarInterface
    assert ShimSidecarRecord is se.ContinuumEvidenceRecord


def test_mathematical_normalization_semantics():
    """
    Verify empirical percentile calculation and IQR-scaled deviation semantics:
    - Percentile matches empirical rank / N (right-continuous)
    - Z-score equals (raw_score - median) / IQR
    """
    from spectra_engine import SpectraEvidenceAdapter

    adapter = SpectraEvidenceAdapter(base_dir=BASE_DIR)
    assert adapter.assets_verified is True
    assert adapter.calib_loaded is True

    # Test for each stratum
    for pair in ["D1,D4", "D2,D5", "D3,D6"]:
        stats = adapter.strata_stats[pair]
        scores = adapter.sorted_calib_scores[pair]
        median = stats["median"]
        iqr = stats["iqr"]

        # 1. At median: percentile should be ~0.50, Z-score should be ~0.0
        p_med, z_med = adapter.normalize_score(median, pair)
        assert 0.49 <= p_med <= 0.51, f"Expected median percentile ~0.50, got {p_med}"
        assert abs(z_med) < 1e-6, f"Expected median Z-score 0.0, got {z_med}"

        # 2. At an arbitrary score
        test_score = median + 1.5 * iqr
        p_test, z_test = adapter.normalize_score(test_score, pair)
        assert np.isclose(z_test, 1.5, atol=1e-5), f"Expected Z-score 1.5, got {z_test}"
        expected_rank = np.searchsorted(scores, test_score, side="right")
        expected_p = expected_rank / float(len(scores))
        assert np.isclose(p_test, expected_p, atol=1e-5)


def test_zero_iqr_defensive_guard():
    """Verify that if IQR is zero or negative, normalize_score returns 0.0 for Z-score without crashing."""
    from spectra_engine import SpectraEvidenceAdapter

    adapter = SpectraEvidenceAdapter(base_dir=BASE_DIR)
    original_iqr = adapter.strata_stats["D1,D4"]["iqr"]
    try:
        adapter.strata_stats["D1,D4"]["iqr"] = 0.0
        p, z = adapter.normalize_score(10.0, "D1,D4")
        assert z == 0.0, f"Expected 0.0 for zero-IQR guard, got {z}"
    finally:
        adapter.strata_stats["D1,D4"]["iqr"] = original_iqr


def test_frozen_scientific_asset_hashes():
    """Verify that frozen scientific assets have exact expected SHA-256 hashes."""
    from spectra_engine import SpectraEvidenceAdapter
    from spectra_engine.fusion_contract import (
        EXPECTED_CHECKPOINT_SHA256,
        EXPECTED_THRESHOLDS_SHA256,
        EXPECTED_CALIB_SCORES_SHA256,
    )

    adapter = SpectraEvidenceAdapter(base_dir=BASE_DIR)
    results = adapter.validate_assets(raise_on_error=True)
    assert results["all_verified"] is True
    assert results["checkpoint"]["actual"] == EXPECTED_CHECKPOINT_SHA256
    assert results["thresholds"]["actual"] == EXPECTED_THRESHOLDS_SHA256
    assert results["calib_scores"]["actual"] == EXPECTED_CALIB_SCORES_SHA256


def test_evidence_record_generation_and_contract_compliance():
    """Verify full evidence record creation, limitation codes, and schema validation."""
    from spectra_engine import SpectraEvidenceAdapter, ThresholdExceedanceLevel, EvidenceStrength

    adapter = SpectraEvidenceAdapter(base_dir=BASE_DIR)

    # 1. Normal source below threshold
    record_norm = adapter.create_evidence_record(
        source_id="1001",
        pointing_id="P0002",
        detector_stratum="D1,D4",
        valid_channels_count=34,
        raw_anomaly_score=1.5
    )
    assert record_norm.threshold_exceedance_level == ThresholdExceedanceLevel.NONE.value
    assert record_norm.evidence_strength == EvidenceStrength.NONE.value
    assert record_norm.anomaly_detected is False
    assert record_norm.human_review_required is False
    assert "PROVISIONAL_NULL_REFERENCE" in record_norm.limitation_codes
    assert "CONTINUUM_SENSITIVITY_LIMITED" in record_norm.limitation_codes
    assert "SKY_WIDE_GENERALIZATION_UNVERIFIED" in record_norm.limitation_codes
    record_norm.validate()

    # 2. Exceeds T05 threshold
    t05 = adapter.strata_stats["D1,D4"]["threshold_05"]
    record_t05 = adapter.create_evidence_record(
        source_id="1002",
        pointing_id="P0002",
        detector_stratum="D1,D4",
        valid_channels_count=34,
        raw_anomaly_score=t05 + 0.1
    )
    assert record_t05.threshold_exceedance_level == ThresholdExceedanceLevel.EXCEEDS_T05.value
    assert record_t05.evidence_strength == EvidenceStrength.MARGINAL.value
    assert record_t05.anomaly_detected is True
    assert record_t05.human_review_required is True

    # 3. Exceeds T01 threshold
    t01 = adapter.strata_stats["D1,D4"]["threshold_01"]
    record_t01 = adapter.create_evidence_record(
        source_id="1003",
        pointing_id="P0002",
        detector_stratum="D1,D4",
        valid_channels_count=34,
        raw_anomaly_score=t01 + 0.5
    )
    assert record_t01.threshold_exceedance_level == ThresholdExceedanceLevel.EXCEEDS_T01.value
    assert record_t01.evidence_strength == EvidenceStrength.STRONG.value
    assert record_t01.anomaly_detected is True
    assert record_t01.human_review_required is True

    # 4. Coverage gate rejection (<5 channels)
    record_sparse = adapter.create_evidence_record(
        source_id="1004",
        pointing_id="P0002",
        detector_stratum="D1,D4",
        valid_channels_count=3,
        raw_anomaly_score=999.0
    )
    assert record_sparse.eligibility_status == "UNINFORMATIVE"
    assert record_sparse.raw_anomaly_score is None
    assert record_sparse.stratum_normalized_percentile is None
    assert record_sparse.evidence_strength == EvidenceStrength.UNINFORMATIVE.value
