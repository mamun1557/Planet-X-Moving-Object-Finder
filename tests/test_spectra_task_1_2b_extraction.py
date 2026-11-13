"""
SPECTRA-X / F1 — Task 1.2B Validation Test Suite
Multi-Pointing Spectral Extraction & Catalog Assembly Verification
"""

import os
import re
import json
import hashlib
import ast
import numpy as np
import pandas as pd
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SPECTRA_CSV = os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv")
COVERAGE_CSV = os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_coverage_v1.csv")
MANIFEST_JSON = os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_extraction_manifest_v1.json")
FROZEN_MODEL_PATH = os.path.join(BASE_DIR, "checkpoints", "spectra_masked_ae_v2.pt")
EXPECTED_MODEL_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()


def safe_eval_list(val_str: str):
    clean = re.sub(r"np\.float(?:32|64)\((.*?)\)", r"\1", val_str)
    return ast.literal_eval(clean)


def test_frozen_assets_unmodified():
    """Verify that protected assets such as model checkpoints are strictly unmodified."""
    assert os.path.exists(FROZEN_MODEL_PATH), "Frozen model checkpoint not found"
    actual_hash = compute_sha256(FROZEN_MODEL_PATH)
    assert actual_hash == EXPECTED_MODEL_SHA256, f"Frozen model checkpoint mutated! {actual_hash} != {EXPECTED_MODEL_SHA256}"


def test_manifest_integrity():
    """Verify extraction manifest completeness and structure."""
    assert os.path.exists(MANIFEST_JSON), "Extraction manifest JSON not found"
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        m = json.load(f)
    
    assert m["manifest_type"] == "SPECTRA_PHASE3_MULTIPOINTING_EXTRACTION_MANIFEST"
    assert m["task_id"] == "SPECTRA_TASK_1_2B"
    assert m["input_inventory_summary"]["total_fits_processed"] == 120
    assert m["input_inventory_summary"]["missing_fits_files"] == 0
    assert m["governance"]["model_training_performed"] is False
    assert m["governance"]["threshold_calibration_performed"] is False
    assert m["governance"]["blind_evaluation_performed"] is False
    assert m["extraction_results"]["total_catalog_sources"] == 37500
    assert m["extraction_results"]["total_valid_measurements"] == 184888


def test_output_files_exist_and_hashes_match():
    """Verify output artifact presence and manifest hash consistency."""
    assert os.path.exists(SPECTRA_CSV), "Spectra CSV not found"
    assert os.path.exists(COVERAGE_CSV), "Coverage CSV not found"
    
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        m = json.load(f)
        
    actual_spectra_hash = compute_sha256(SPECTRA_CSV)
    expected_spectra_hash = m["output_artifacts"]["spectra_csv"]["sha256"]
    assert actual_spectra_hash == expected_spectra_hash, "Spectra CSV hash mismatch"
    
    actual_cov_hash = compute_sha256(COVERAGE_CSV)
    expected_cov_hash = m["output_artifacts"]["coverage_csv"]["sha256"]
    assert actual_cov_hash == expected_cov_hash, "Coverage CSV hash mismatch"


def test_spectra_csv_schema_and_counts():
    """Verify schema, row count, and column names of phase3_multpointing_spectra_v1.csv."""
    df = pd.read_csv(SPECTRA_CSV, nrows=50)
    expected_cols = [
        "source_id", "pointing", "partition_role", "ra", "dec",
        "wavelength", "bandwidth", "flux", "uncertainty",
        "detector_provenance", "observation_provenance",
        "valid_channel_mask", "valid_channels_count", "quality_summary"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    full_df = pd.read_csv(SPECTRA_CSV, usecols=["source_id", "pointing", "partition_role", "valid_channels_count"])
    assert len(full_df) == 37500, f"Expected 37,500 rows, got {len(full_df)}"
    
    # Check pointing breakdown
    ptg_counts = full_df["pointing"].astype(str).str.zfill(4).value_counts().to_dict()
    for p in ["0001", "0008", "0002", "0009", "0010"]:
        assert ptg_counts.get(p, 0) == 7500, f"Pointing {p} has {ptg_counts.get(p, 0)} rows, expected 7500"


def test_coverage_csv_schema_and_counts():
    """Verify schema and integrity of phase3_multpointing_coverage_v1.csv."""
    cov_df = pd.read_csv(COVERAGE_CSV)
    assert len(cov_df) == 37500
    expected_cols = [
        "source_id", "pointing", "partition_role", "ra", "dec",
        "D1_observations", "D2_observations", "D3_observations",
        "D4_observations", "D5_observations", "D6_observations",
        "total_detectors_observed", "total_dithers_observed", "coverage_status"
    ]
    for col in expected_cols:
        assert col in cov_df.columns, f"Missing coverage column: {col}"
        
    # Check coverage status categories
    valid_statuses = {"MULTI_DETECTOR", "SINGLE_DETECTOR", "NO_COVERAGE"}
    assert set(cov_df["coverage_status"].unique()).issubset(valid_statuses)
    
    multi_det_count = (cov_df["coverage_status"] == "MULTI_DETECTOR").sum()
    assert multi_det_count == 26050, f"Expected 26,050 multi-detector sources, got {multi_det_count}"


def test_partition_isolation():
    """Verify strict calibration and evaluation partition separation."""
    df = pd.read_csv(SPECTRA_CSV, usecols=["source_id", "pointing", "partition_role"])
    
    calib_df = df[df["partition_role"] == "CALIBRATION"]
    eval_df = df[df["partition_role"] == "EVALUATION"]
    
    assert set(calib_df["pointing"].astype(str).str.zfill(4).unique()) == {"0001", "0008"}
    assert set(eval_df["pointing"].astype(str).str.zfill(4).unique()) == {"0002", "0009", "0010"}
    
    calib_sids = set(calib_df["source_id"])
    eval_sids = set(eval_df["source_id"])
    overlap = calib_sids.intersection(eval_sids)
    assert len(overlap) == 0, f"Partition contamination detected! Overlapping source IDs: {len(overlap)}"


def test_sed_vector_102ch_consistency():
    """Sample SED vectors to ensure 102 channels, mask alignment, and physical positivity of uncertainty."""
    df = pd.read_csv(SPECTRA_CSV, nrows=200)
    for _, row in df.iterrows():
        mask = safe_eval_list(row["valid_channel_mask"])
        fluxes = safe_eval_list(row["flux"])
        uncerts = safe_eval_list(row["uncertainty"])
        waves = safe_eval_list(row["wavelength"])
        
        assert len(mask) == 102, "Mask length must be 102"
        assert len(fluxes) == 102, "Flux length must be 102"
        assert len(uncerts) == 102, "Uncertainty length must be 102"
        assert len(waves) == 102, "Wavelength length must be 102"
        
        n_valid = sum(mask)
        assert n_valid == row["valid_channels_count"], "valid_channels_count mismatch"
        
        for ch in range(102):
            if mask[ch]:
                assert fluxes[ch] is not None, f"Valid channel {ch} has None flux"
                assert uncerts[ch] is not None, f"Valid channel {ch} has None uncertainty"
                assert uncerts[ch] > 0.0, f"Valid channel {ch} has non-positive uncertainty: {uncerts[ch]}"
            else:
                assert fluxes[ch] is None, f"Invalid channel {ch} has non-None flux: {fluxes[ch]}"
                assert uncerts[ch] is None, f"Invalid channel {ch} has non-None uncertainty"


def test_detector_coverage_physical_dichroic():
    """Verify that all six detectors D1-D6 have valid measurements across the dataset."""
    cov_df = pd.read_csv(COVERAGE_CSV)
    for d in range(1, 7):
        col = f"D{d}_observations"
        n_obs = (cov_df[col] > 0).sum()
        assert n_obs > 5000, f"Detector D{d} has insufficient source coverage: {n_obs}"
