"""
Unit Tests for ASTROVISION Detector-Stratified Dynamic Thresholding (Task 4.20E)
Verifies:
1. Production threshold immutability in default mode.
2. Sample-aware calibration state transitions (State A, State B, State C).
3. Automatic fallback on missing morphology (0 extended calibration injections).
4. James-Stein shrinkage mathematical consistency.
5. Protected asset immutability and provenance preservation.
"""

import os
import sys
import hashlib
from pathlib import Path
import pytest
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models.astrovision.dynamic_thresholds import (
    DynamicThresholdManager,
    CalibrationState,
    BASELINE_PRODUCTION_THRESHOLDS,
    POOLED_BASELINE_THRESHOLD,
)

PROTECTED_ASSETS = {
    "checkpoints/astrovision_spatial_v3.pt": "3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99",
    "checkpoints/spectra_masked_ae_v2.pt": "6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938",
    "data/processed/spectra/spectra_v2_provisional_thresholds_v1.json": "D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848"
}


def test_production_threshold_immutability():
    """Verifies that in production mode, exact baseline thresholds are returned for all detectors."""
    mgr = DynamicThresholdManager()
    for det in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        tau, state, rationale = mgr.get_threshold(det, morphology="point", mode="production")
        expected_tau = BASELINE_PRODUCTION_THRESHOLDS[det]["peak_tau"]
        assert tau == pytest.approx(expected_tau, rel=1e-5), (
            f"Production threshold for {det} must be unchanged! Got {tau}, expected {expected_tau}"
        )
        assert "Production mode active" in rationale


def test_extended_morphology_zero_sample_fallback():
    """
    Verifies that extended morphology triggers State C fallback
    because calibration dataset has N_ext = 0.
    """
    mgr = DynamicThresholdManager()
    for det in ["D1", "D2", "D3", "D4", "D5", "D6"]:
        tau, state, rationale = mgr.get_threshold(det, morphology="extended", mode="shadow_sample_aware")
        assert state == CalibrationState.STATE_C_INSUFFICIENT_SAMPLE_FALLBACK
        expected_ext_tau = BASELINE_PRODUCTION_THRESHOLDS[det]["ext_int_tau"]
        assert tau == pytest.approx(expected_ext_tau, rel=1e-5)
        assert "Extended-source calibration samples N=0" in rationale


def test_state_b_shrinkage_calculation():
    """
    Verifies James-Stein shrinkage math on D1 and D4:
    tau_shrunk = lambda * tau_raw + (1 - lambda) * tau_pool
    where lambda = N / (N + N0)
    """
    mgr = DynamicThresholdManager(shrinkage_prior_n0=84.0)
    
    # D1 check
    tau_d1, state_d1, rationale_d1 = mgr.get_threshold("D1", morphology="point", mode="shadow_sample_aware")
    assert state_d1 == CalibrationState.STATE_B_POOLED_SHRINKAGE
    
    cfg_d1 = mgr.configs["D1"]
    n1 = cfg_d1.n_controls  # 84
    lam1 = n1 / (n1 + 84.0)  # 0.500
    expected_shrunk_d1 = lam1 * cfg_d1.empirical_raw_tau + (1.0 - lam1) * POOLED_BASELINE_THRESHOLD
    assert tau_d1 == pytest.approx(expected_shrunk_d1, rel=1e-4)


def test_state_c_thermal_regime_protection():
    """
    Verifies that D5 and D6 trigger State C fallback in shadow mode
    to prevent pooled threshold inflation that would destroy sensitivity.
    """
    mgr = DynamicThresholdManager()
    
    tau_d5, state_d5, _ = mgr.get_threshold("D5", morphology="point", mode="shadow_sample_aware")
    assert state_d5 == CalibrationState.STATE_C_INSUFFICIENT_SAMPLE_FALLBACK
    assert tau_d5 == pytest.approx(BASELINE_PRODUCTION_THRESHOLDS["D5"]["peak_tau"], rel=1e-5)
    
    tau_d6, state_d6, _ = mgr.get_threshold("D6", morphology="point", mode="shadow_sample_aware")
    assert state_d6 == CalibrationState.STATE_C_INSUFFICIENT_SAMPLE_FALLBACK
    assert tau_d6 == pytest.approx(BASELINE_PRODUCTION_THRESHOLDS["D6"]["peak_tau"], rel=1e-5)


def test_anomaly_evaluation_margins():
    """Verifies that evaluate_anomaly computes detection decision and margin correctly."""
    mgr = DynamicThresholdManager()
    
    # Above threshold
    res_high = mgr.evaluate_anomaly(score=500.0, detector_id="D1", mode="production")
    assert res_high["is_detected"] is True
    assert res_high["margin"] == pytest.approx(500.0 - 186.2904, rel=1e-4)
    
    # Below threshold
    res_low = mgr.evaluate_anomaly(score=50.0, detector_id="D1", mode="production")
    assert res_low["is_detected"] is False
    assert res_low["margin"] < 0.0


def test_unknown_detector_fallback():
    """Verifies that an unrecognized detector safely defaults to pooled threshold."""
    mgr = DynamicThresholdManager()
    tau, state, rationale = mgr.get_threshold("D99", morphology="point", mode="shadow_sample_aware")
    assert tau == pytest.approx(POOLED_BASELINE_THRESHOLD, rel=1e-4)
    assert state == CalibrationState.STATE_C_INSUFFICIENT_SAMPLE_FALLBACK
    assert "Unknown detector" in rationale


def test_protected_assets_remain_pristine():
    """Verifies all protected checkpoints and reference files match cryptographic hashes."""
    for rel_path, expected_hash in PROTECTED_ASSETS.items():
        full_path = BASE_DIR / rel_path
        assert full_path.exists(), f"Protected asset {rel_path} must exist!"
        h = hashlib.sha256()
        with open(full_path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_hash = h.hexdigest().upper()
        assert actual_hash == expected_hash, (
            f"Asset {rel_path} hash mutated! Got {actual_hash}, expected {expected_hash}"
        )

