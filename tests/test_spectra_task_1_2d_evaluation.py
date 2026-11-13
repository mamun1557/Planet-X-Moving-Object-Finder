"""
SPECTRA-X / F1 — Phase 3, Task 1.2D
Automated Independent Blind Scientific Evaluation Test Suite
"""

import os
import json
import hashlib
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

EXPECTED_CHECKPOINT_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"
EXPECTED_THRESHOLDS_SHA256 = "d40292972aafb9d3948249bd402a178eeadb20de5e37c02c227ac841974ab848"
EXPECTED_CALIB_SCORES_SHA256 = "7ac34d415f8132f7f164ab20c1b25fe03461bc709eb674031e838b2208e8c1a3"

EVAL_SCORES_CSV = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_evaluation_scores_v1.csv")
EVAL_INJECTIONS_CSV = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_evaluation_synthetic_injections_v1.csv")
EVAL_METRICS_JSON = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_v2_blind_evaluation_metrics_v1.json")


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()


def test_frozen_model_and_calibration_integrity():
    """Verify frozen model checkpoint and calibration thresholds remain immutable."""
    ckpt_path = os.path.join(BASE_DIR, "checkpoints", "spectra_masked_ae_v2.pt")
    thresh_path = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_v2_provisional_thresholds_v1.json")
    calib_scores_path = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_p0008_calibration_scores_v1.csv")

    assert os.path.exists(ckpt_path), f"Checkpoint missing: {ckpt_path}"
    assert compute_sha256(ckpt_path) == EXPECTED_CHECKPOINT_SHA256, "Checkpoint SHA-256 altered!"

    assert os.path.exists(thresh_path), f"Thresholds missing: {thresh_path}"
    assert compute_sha256(thresh_path) == EXPECTED_THRESHOLDS_SHA256, "Provisional thresholds SHA-256 altered!"

    assert os.path.exists(calib_scores_path), f"Calibration scores missing: {calib_scores_path}"
    assert compute_sha256(calib_scores_path) == EXPECTED_CALIB_SCORES_SHA256, "Calibration scores SHA-256 altered!"


def test_evaluation_scores_cohort_composition():
    """Verify evaluation scores cohort size, pointings, detector strata, and clean data."""
    assert os.path.exists(EVAL_SCORES_CSV), f"Missing evaluation scores CSV: {EVAL_SCORES_CSV}"
    df = pd.read_csv(EVAL_SCORES_CSV)

    # Exactly 9,500 real evaluation sources
    assert len(df) == 9500, f"Expected 9,500 evaluation sources, found {len(df)}"

    # Zero nulls or NaNs in scores
    assert df["score"].isna().sum() == 0, "NaN scores detected in evaluation set"
    assert np.all(np.isfinite(df["score"])), "Non-finite scores detected"
    assert np.all(df["score"] >= 0.0), "Negative reconstruction scores detected"

    # Strict pointing isolation: only pointings 2, 9, 10
    pointings = set(df["pointing"].unique())
    assert pointings == {2, 9, 10}, f"Unexpected pointings in evaluation set: {pointings}"
    assert 1 not in pointings, "CRITICAL LEAKAGE: P0001 present in evaluation set!"
    assert 8 not in pointings, "CRITICAL LEAKAGE: P0008 present in evaluation set!"

    # Pointing counts
    assert len(df[df["pointing"] == 2]) == 4071
    assert len(df[df["pointing"] == 9]) == 2284
    assert len(df[df["pointing"] == 10]) == 3145

    # Stratum counts
    assert len(df[df["detector_provenance"] == "D1,D4"]) == 3580
    assert len(df[df["detector_provenance"] == "D2,D5"]) == 3410
    assert len(df[df["detector_provenance"] == "D3,D6"]) == 2510

    # Ensure all sources have >= 5 valid channels
    assert (df["valid_channels_count"] < 5).sum() == 0, "Found sources with < 5 valid channels"


def test_calibration_evaluation_zero_leakage():
    """Verify complete independence between P0008 calibration cohort and evaluation cohort."""
    calib_scores_path = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_p0008_calibration_scores_v1.csv")
    calib_df = pd.read_csv(calib_scores_path)
    eval_df = pd.read_csv(EVAL_SCORES_CSV)

    calib_sources = set(calib_df["source_id"].unique())
    eval_sources = set(eval_df["source_id"].unique())

    overlap = calib_sources.intersection(eval_sources)
    assert len(overlap) == 0, f"CRITICAL LEAKAGE: {len(overlap)} sources overlap between calibration and evaluation!"


def test_synthetic_injection_benchmark_structure():
    """Verify synthetic injection trials structure, sample counts, and paired original scores."""
    assert os.path.exists(EVAL_INJECTIONS_CSV), f"Missing injection CSV: {EVAL_INJECTIONS_CSV}"
    df = pd.read_csv(EVAL_INJECTIONS_CSV)

    # Exactly 6,000 injection trials
    assert len(df) == 6000, f"Expected 6,000 injection instances, found {len(df)}"

    # 1,500 negative controls and 4,500 injected anomalies
    assert (df["is_anomaly"] == 0).sum() == 1500
    assert (df["is_anomaly"] == 1).sum() == 4500

    # Verify nominal negative controls have matching original and injected scores
    neg_controls = df[df["is_anomaly"] == 0]
    assert np.allclose(neg_controls["original_score"], neg_controls["injected_score"], atol=1e-5), \
        "Negative control original and injected scores do not match!"

    # Verify injection families
    assert (df["injection_family"] == "NEGATIVE_CONTROL_NOMINAL").sum() == 1500
    assert (df["injection_family"] == "ABSORPTION_TROUGH").sum() == 1500
    assert (df["injection_family"] == "BROAD_IR_EXCESS").sum() == 1500
    assert (df["injection_family"] == "LOCALIZED_EMISSION_LINE").sum() == 1441
    assert (df["injection_family"] == "PAH_3_3UM_EMISSION").sum() == 59
    assert 1441 + 59 == 1500, "Emission line instances must sum to 1500"

    # Zero missing values
    assert df["injected_score"].isna().sum() == 0
    assert np.all(np.isfinite(df["injected_score"]))


def test_evaluation_metrics_json_schema():
    """Verify machine-readable metrics JSON file schema and numerical bounds."""
    assert os.path.exists(EVAL_METRICS_JSON), f"Missing metrics JSON: {EVAL_METRICS_JSON}"
    with open(EVAL_METRICS_JSON, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["manifest_type"] == "SPECTRA_BLIND_EVALUATION_METRICS"
    assert metrics["task_id"] == "SPECTRA_TASK_1_2D"
    assert metrics["model_provenance"]["checkpoint_sha256"] == EXPECTED_CHECKPOINT_SHA256
    assert metrics["frozen_calibration_thresholds"]["artifact_sha256"] == EXPECTED_THRESHOLDS_SHA256

    # Real exceedances
    strata = metrics["real_source_evaluation_results"]["strata_diagnostics"]
    for pair in ["D1,D4", "D2,D5", "D3,D6"]:
        assert pair in strata
        p95_rate = strata[pair]["exceedance_q95"]["proportion"]
        p99_rate = strata[pair]["exceedance_q99"]["proportion"]
        assert 0.04 <= p95_rate <= 0.10, f"Exceedance rate at 95th threshold out of reasonable transfer range: {p95_rate}"
        assert 0.005 <= p99_rate <= 0.03, f"Exceedance rate at 99th threshold out of reasonable transfer range: {p99_rate}"

    # Synthetic injection benchmark metrics
    synth = metrics["synthetic_injection_benchmark_results"]
    auroc = synth["global_auroc"]
    auprc = synth["global_auprc"]
    assert 0.65 <= auroc <= 0.85, f"Unexpected AUROC: {auroc}"
    assert 0.75 <= auprc <= 0.95, f"Unexpected AUPRC: {auprc}"

    # Verify recovery rates
    assert 0.15 <= synth["recovery_at_q95"] <= 0.25
    assert 0.02 <= synth["recovery_at_q99"] <= 0.06

    # Verify PAH 3.3um emission recovery is highest
    pah_rec = synth["family_metrics"]["PAH_3_3UM_EMISSION"]["rec_q95"]
    assert pah_rec > 0.60, f"PAH recovery at 95th threshold lower than expected: {pah_rec}"
