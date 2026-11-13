"""
SPECTRA-X / F1 — Task 1.2C Validation Test Suite
SPECTRA Provisional-Null Threshold Calibration Verification
"""

import os
import json
import hashlib
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
THRESHOLDS_JSON = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_v2_provisional_thresholds_v1.json")
SCORES_CSV = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_p0008_calibration_scores_v1.csv")
CALIB_SCRIPT = os.path.join(BASE_DIR, "scripts", "calibration", "calibrate_spectra_v2_thresholds.py")
FROZEN_MODEL_PATH = os.path.join(BASE_DIR, "checkpoints", "spectra_masked_ae_v2.pt")
EXPECTED_MODEL_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"

KNOWN_OVERLAP_IDS = {
    6316932723797678080,
    6268273836710905344,
    6316494229114061952,
    6316495122467403776,
    6316948567937380224
}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()


def test_frozen_checkpoint_integrity():
    """Verify that model checkpoint is byte-for-byte unmodified."""
    assert os.path.exists(FROZEN_MODEL_PATH), "Checkpoint missing"
    actual_hash = compute_sha256(FROZEN_MODEL_PATH)
    assert actual_hash == EXPECTED_MODEL_SHA256, f"Checkpoint modified! {actual_hash}"


def test_calibration_artifacts_exist():
    """Verify that all Task 1.2C required artifacts exist."""
    assert os.path.exists(THRESHOLDS_JSON), "Threshold JSON missing"
    assert os.path.exists(SCORES_CSV), "Scores CSV missing"
    assert os.path.exists(CALIB_SCRIPT), "Calibration script missing"


def test_p0008_cohort_enforcement_and_exclusions():
    """Verify that only P0008 sources are scored, >=5 channels, and 0 training overlaps."""
    df_scores = pd.read_csv(SCORES_CSV)
    assert len(df_scores) == 3206, f"Expected 3,206 scores, got {len(df_scores)}"
    
    # Verify pointing is strictly 8
    assert set(df_scores["pointing"].unique()) == {8}, "Non-P0008 pointing found in scores!"
    
    # Verify channels >= 5
    assert (df_scores["valid_channels_count"] < 5).sum() == 0, "Source with <5 channels found!"
    
    # Verify 0 training overlaps
    overlap_found = set(df_scores["source_id"]).intersection(KNOWN_OVERLAP_IDS)
    assert len(overlap_found) == 0, f"Training overlap sources found: {overlap_found}"
    
    # Verify no NaN or infinite scores
    assert df_scores["score"].isna().sum() == 0, "NaN scores found"
    assert np.isinf(df_scores["score"]).sum() == 0, "Infinite scores found"
    assert (df_scores["score"] < 0).sum() == 0, "Negative chi2 scores found"


def test_strata_membership_counts():
    """Verify exact counts per detector-pair stratum."""
    df_scores = pd.read_csv(SCORES_CSV)
    counts = df_scores["detector_provenance"].value_counts().to_dict()
    assert counts.get("D1,D4") == 1055, f"Expected D1,D4=1,055, got {counts.get('D1,D4')}"
    assert counts.get("D2,D5") == 1304, f"Expected D2,D5=1,304, got {counts.get('D2,D5')}"
    assert counts.get("D3,D6") == 847, f"Expected D3,D6=847, got {counts.get('D3,D6')}"


def test_threshold_artifact_schema_and_quantiles():
    """Verify JSON schema and mathematical consistency of thresholds."""
    with open(THRESHOLDS_JSON, "r", encoding="utf-8") as f:
        t = json.load(f)
        
    assert t["manifest_type"] == "SPECTRA_PROVISIONAL_NULL_THRESHOLDS"
    assert t["model_provenance"]["checkpoint_sha256"] == EXPECTED_MODEL_SHA256
    assert t["calibration_cohort_definition"]["pointing"] == "0008"
    assert t["calibration_cohort_definition"]["total_calibration_sources"] == 3206
    
    strata = t["strata_thresholds"]
    for pair in ["D1,D4", "D2,D5", "D3,D6"]:
        assert pair in strata, f"Missing stratum {pair}"
        s = strata[pair]
        
        q95 = s["threshold_alpha_0_05"]["threshold_value"]
        q99 = s["threshold_alpha_0_01"]["threshold_value"]
        assert q99 > q95, f"99th threshold ({q99}) must exceed 95th ({q95})"
        
        ci95 = s["threshold_alpha_0_05"]["bootstrap_confidence_interval_95"]
        ci99 = s["threshold_alpha_0_01"]["bootstrap_confidence_interval_95"]
        assert ci95[0] <= q95 <= ci95[1], "q95 outside bootstrap CI"
        assert ci99[0] <= q99 <= ci99[1], "q99 outside bootstrap CI"
        
        # Check empirical exceedance is approximately alpha
        exc95 = s["threshold_alpha_0_05"]["empirical_exceedance_fraction"]
        exc99 = s["threshold_alpha_0_01"]["empirical_exceedance_fraction"]
        assert 0.04 <= exc95 <= 0.06, f"Empirical alpha=0.05 exceedance out of bounds: {exc95}"
        assert 0.005 <= exc99 <= 0.015, f"Empirical alpha=0.01 exceedance out of bounds: {exc99}"


def test_blind_evaluation_firewall():
    """Verify that blind evaluation pointings (P0002, P0009, P0010) are completely absent from calibration scores."""
    df_scores = pd.read_csv(SCORES_CSV)
    assert not any(df_scores["pointing"].isin([2, 9, 10])), "Blind evaluation data accessed!"

