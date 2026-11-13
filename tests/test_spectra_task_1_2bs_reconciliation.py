"""
SPECTRA-X / F1 — Task 1.2B-S Validation Test Suite
Calibration Cohort Reconciliation & Statistical Count Verification
"""

import os
import json
import hashlib
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REPORT_MD = os.path.join(BASE_DIR, "reports", "SPECTRA_TASK_1_2BS_COHORT_RECONCILIATION_REPORT.md")
MANIFEST_JSON = os.path.join(BASE_DIR, "reports", "manifests", "spectra_task_1_2bs_reconciliation_manifest.json")
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


def test_frozen_checkpoint_immutable():
    """Verify that model checkpoint is byte-for-byte unmodified."""
    assert os.path.exists(FROZEN_MODEL_PATH)
    actual_hash = compute_sha256(FROZEN_MODEL_PATH)
    assert actual_hash == EXPECTED_MODEL_SHA256


def test_reconciliation_deliverables_exist():
    """Verify presence and structure of Task 1.2B-S deliverables."""
    assert os.path.exists(REPORT_MD), "Reconciliation report missing"
    assert os.path.exists(MANIFEST_JSON), "Reconciliation manifest missing"
    
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["manifest_metadata"]["task_id"] == "SPECTRA_TASK_1_2B_S"
    assert m["final_readiness_verdict"] == "CONDITIONALLY READY FOR TASK 1.2C"


def test_discrepancy_5327_exact_reconciliation():
    """Programmatically verify that reliable sources with >=5 channels sum to exactly 5,327."""
    cov = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_coverage_v1.csv"))
    spectra = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv"),
                          usecols=["source_id", "valid_channels_count", "detector_provenance", "pointing"])
    p1_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0001_source_catalogue.csv"))[["source_id", "classification_category"]]
    p8_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv"))[["source_id", "classification_category"]]
    p_cat = pd.concat([p1_cat, p8_cat])

    df = spectra[spectra["pointing"].isin([1, 8])].merge(p_cat, on="source_id")
    reliable = df[df["classification_category"] == "RELIABLE_ISOLATED_POINT_SOURCE"]
    reliable_ge5 = reliable[reliable["valid_channels_count"] >= 5]
    
    # Check overall unique count
    assert len(reliable_ge5) == 5327, f"Expected 5,327 reliable sources with >=5 ch, got {len(reliable_ge5)}"
    
    # Check pair-wise counts
    d1d4_count = len(reliable_ge5[reliable_ge5["detector_provenance"] == "D1,D4"])
    d2d5_count = len(reliable_ge5[reliable_ge5["detector_provenance"] == "D2,D5"])
    d3d6_count = len(reliable_ge5[reliable_ge5["detector_provenance"] == "D3,D6"])
    
    assert d1d4_count == 1155, f"Expected D1,D4=1,155, got {d1d4_count}"
    assert d2d5_count == 2624, f"Expected D2,D5=2,624, got {d2d5_count}"
    assert d3d6_count == 1548, f"Expected D3,D6=1,548, got {d3d6_count}"
    assert d1d4_count + d2d5_count + d3d6_count == 5327


def test_five_training_overlaps_exact_attributes():
    """Verify that all 5 training overlap sources belong to P0001, D1,D4, have 8 channels, and match training data."""
    spectra = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv"))
    train_path = os.path.join(BASE_DIR, "data", "processed", "spectral_features", "validation_assembled_spectra.csv")
    df_train = pd.read_csv(train_path)
    c_train = SkyCoord(ra=df_train["ra"].values * u.deg, dec=df_train["dec"].values * u.deg)
    
    for sid in KNOWN_OVERLAP_IDS:
        row = spectra[spectra["source_id"] == sid].iloc[0]
        assert row["pointing"] == 1, f"Expected P0001 for {sid}, got {row['pointing']}"
        assert row["detector_provenance"] == "D1,D4", f"Expected D1,D4 for {sid}, got {row['detector_provenance']}"
        assert row["valid_channels_count"] == 8, f"Expected 8 channels for {sid}, got {row['valid_channels_count']}"
        
        c_src = SkyCoord(ra=[row["ra"]] * u.deg, dec=[row["dec"]] * u.deg)
        idx, d2d, _ = c_src.match_to_catalog_sky(c_train)
        assert float(d2d.arcsec[0]) < 1.0, f"Expected match < 1 arcsec, got {float(d2d.arcsec[0])}"


def test_p0008_only_eligible_counts():
    """Verify that P0008 provides exactly 3,206 clean reliable candidates with >=5 channels."""
    spectra = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv"),
                          usecols=["source_id", "valid_channels_count", "detector_provenance", "pointing"])
    p8_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv"))[["source_id", "classification_category"]]
    
    df_p8 = spectra[spectra["pointing"] == 8].merge(p8_cat, on="source_id")
    p8_rel_ge5 = df_p8[(df_p8["classification_category"] == "RELIABLE_ISOLATED_POINT_SOURCE") & (df_p8["valid_channels_count"] >= 5)]
    
    assert len(p8_rel_ge5) == 3206, f"Expected 3,206 P0008 candidates, got {len(p8_rel_ge5)}"
    
    p8_d1d4 = len(p8_rel_ge5[p8_rel_ge5["detector_provenance"] == "D1,D4"])
    p8_d2d5 = len(p8_rel_ge5[p8_rel_ge5["detector_provenance"] == "D2,D5"])
    p8_d3d6 = len(p8_rel_ge5[p8_rel_ge5["detector_provenance"] == "D3,D6"])
    
    assert p8_d1d4 == 1055, f"Expected P0008 D1,D4=1,055, got {p8_d1d4}"
    assert p8_d2d5 == 1304, f"Expected P0008 D2,D5=1,304, got {p8_d2d5}"
    assert p8_d3d6 == 847, f"Expected P0008 D3,D6=847, got {p8_d3d6}"
    assert p8_d1d4 + p8_d2d5 + p8_d3d6 == 3206
    
    # Check zero overlap with known training IDs
    assert len(set(p8_rel_ge5["source_id"]).intersection(KNOWN_OVERLAP_IDS)) == 0


def test_detector_provenance_mutually_exclusive():
    """Verify that every source in the entire dataset has exactly one mutually exclusive detector provenance string."""
    spectra = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv"),
                          usecols=["source_id", "detector_provenance"])
    valid_provs = {"D1,D4", "D2,D5", "D3,D6", "D1", "D2", "D3", "D4", "D5", "D6", "NONE"}
    assert set(spectra["detector_provenance"].unique()).issubset(valid_provs)
    assert spectra["source_id"].duplicated().sum() == 0, "Duplicate source IDs found in spectra table"

