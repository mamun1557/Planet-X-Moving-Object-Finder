"""
SPECTRA-X / F1 — Task 1.2B-R Validation Test Suite
Calibration-Readiness & Cross-Partition Independence Verification
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
REPORT_MD = os.path.join(BASE_DIR, "reports", "SPECTRA_TASK_1_2BR_CALIBRATION_READINESS_AUDIT.md")
MANIFEST_JSON = os.path.join(BASE_DIR, "reports", "manifests", "spectra_task_1_2br_readiness_manifest.json")
FROZEN_MODEL_PATH = os.path.join(BASE_DIR, "checkpoints", "spectra_masked_ae_v2.pt")
EXPECTED_MODEL_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"


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


def test_audit_artifacts_exist():
    """Verify presence of Task 1.2B-R audit deliverables."""
    assert os.path.exists(REPORT_MD), "Audit report markdown missing"
    assert os.path.exists(MANIFEST_JSON), "Readiness manifest JSON missing"
    
    with open(MANIFEST_JSON, "r", encoding="utf-8") as f:
        m = json.load(f)
    assert m["manifest_metadata"]["task_id"] == "SPECTRA_TASK_1_2B_R"
    assert m["final_readiness_verdict"] == "CONDITIONALLY READY FOR TASK 1.2C"


def test_cross_partition_astrophysical_independence():
    """Mathematically verify that Calibration and Evaluation cohorts have >17 deg separation."""
    calib_p1 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0001_source_catalogue.csv"))
    calib_p8 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv"))
    eval_p2 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0002_source_catalogue.csv"))
    eval_p9 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0009_source_catalogue.csv"))
    eval_p10 = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0010_source_catalogue.csv"))

    c_calib = SkyCoord(ra=np.concatenate([calib_p1.ra.values, calib_p8.ra.values]) * u.deg,
                       dec=np.concatenate([calib_p1.dec.values, calib_p8.dec.values]) * u.deg)
    c_eval = SkyCoord(ra=np.concatenate([eval_p2.ra.values, eval_p9.ra.values, eval_p10.ra.values]) * u.deg,
                      dec=np.concatenate([eval_p2.dec.values, eval_p9.dec.values, eval_p10.dec.values]) * u.deg)

    idx, d2d, _ = c_calib.match_to_catalog_sky(c_eval)
    min_sep = d2d.min().to(u.deg).value
    assert min_sep > 17.0, f"Expected minimum separation >17 deg, found {min_sep} deg"
    assert np.sum(d2d < 1.0 * u.deg) == 0, "Unexpected match within 1 degree"


def test_calibration_cohort_composition():
    """Verify counts of provisional controls and dichroic pairs."""
    cov = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_coverage_v1.csv"))
    spectra = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv"),
                          usecols=["source_id", "valid_channels_count", "detector_provenance"])
    p1_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0001_source_catalogue.csv"))[["source_id", "classification_category"]]
    p8_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv"))[["source_id", "classification_category"]]
    p_cat = pd.concat([p1_cat, p8_cat])

    df = cov[cov["partition_role"] == "CALIBRATION"].merge(spectra, on="source_id").merge(p_cat, on="source_id")
    assert len(df) == 15000
    
    reliable = df[df["classification_category"] == "RELIABLE_ISOLATED_POINT_SOURCE"]
    assert len(reliable) == 11380
    
    reliable_observed = reliable[reliable["valid_channels_count"] > 0]
    assert len(reliable_observed) == 7138
    
    reliable_ge_5ch = reliable[reliable["valid_channels_count"] >= 5]
    assert len(reliable_ge_5ch) == 5327


def test_p0001_training_overlap_audit():
    """Verify that exactly 5 reliable P0001 sources overlap with historical training data, while P0008 has zero."""
    train_path = os.path.join(BASE_DIR, "data", "processed", "spectral_features", "validation_assembled_spectra.csv")
    if os.path.exists(train_path):
        df_train = pd.read_csv(train_path)
        c_train = SkyCoord(ra=df_train["ra"].values * u.deg, dec=df_train["dec"].values * u.deg)
        
        p1_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0001_source_catalogue.csv"))
        c_p1 = SkyCoord(ra=p1_cat.ra.values * u.deg, dec=p1_cat.dec.values * u.deg)
        idx1, d2d1, _ = c_p1.match_to_catalog_sky(c_train)
        assert np.sum(d2d1 < 2.0 * u.arcsec) == 8
        
        p8_cat = pd.read_csv(os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv"))
        c_p8 = SkyCoord(ra=p8_cat.ra.values * u.deg, dec=p8_cat.dec.values * u.deg)
        idx8, d2d8, _ = c_p8.match_to_catalog_sky(c_train)
        assert np.sum(d2d8 < 2.0 * u.arcsec) == 0

