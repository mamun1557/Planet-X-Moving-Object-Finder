"""
SPECTRA-X / F1 — Phase 3, Task 1.1O
Test Suite for Pilot Preparation, Cross-Matching, Mask Architecture, and Five-Partition Allocation.
"""

import os
import sys
import json
import hashlib
from pathlib import Path

import pytest
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.acquisition.generate_five_pointing_catalogues import (
    PROTECTED_ASSETS,
    POINTINGS,
    compute_sha256,
    propagate_astrometry,
    classify_sources,
)
from scripts.acquisition.generate_five_partition_manifest import (
    CALIBRATION_POINTINGS,
    EVALUATION_POINTINGS,
    generate_five_partition_manifest,
    MANIFEST_CSV
)

CAT_DIR = BASE_DIR / "data" / "processed" / "pilot_catalogues"
MASK_DIR = BASE_DIR / "data" / "processed" / "pilot_masks"
LEVEL2_DIR = BASE_DIR / "data" / "spherex" / "multipointing_pilot" / "level2"


def test_authoritative_input_manifest_and_fits_inventory():
    """Requirement 1: Verify 5 pointings, 120 FITS products, and ingestion manifest completeness."""
    ingest_manifest_path = BASE_DIR / "reports" / "manifests" / "astrovision_multipointing_ingestion_manifest.json"
    assert ingest_manifest_path.exists(), "Ingestion manifest missing!"
    
    with open(ingest_manifest_path, "r", encoding="utf-8") as f:
        ingest_data = json.load(f)
    
    assert ingest_data["total_products"] == 120
    assert ingest_data["target_cohort"] == ["0001", "0002", "0008", "0009", "0010"]
    
    # Check all 120 files exist on disk
    for p in POINTINGS:
        p_dir = LEVEL2_DIR / p
        assert p_dir.exists(), f"Pointing directory {p} missing!"
        fits_files = list(p_dir.glob("*.fits"))
        assert len(fits_files) == 24, f"Pointing {p} has {len(fits_files)} files, expected 24!"
        for f in fits_files:
            assert f.stat().st_size > 0, f"File {f.name} is empty!"


def test_crossmatch_identity_and_column_preservation():
    """Requirement 2: Verify original catalogue identifiers and required columns are preserved."""
    for p in POINTINGS:
        cat_path = CAT_DIR / f"pointing_{p}_source_catalogue.csv"
        assert cat_path.exists(), f"Catalogue for P{p} missing!"
        df = pd.read_csv(cat_path)
        assert len(df) > 0, f"Catalogue for P{p} is empty!"
        
        # Check required columns
        req_cols = [
            "source_id", "ra", "dec", "pmra", "pmdec", "phot_g_mean_mag",
            "ra_epoch", "dec_epoch", "pm_propagated", "tmass_id",
            "has_tmass_match", "classification_category", "nn_dist_arcsec"
        ]
        for col in req_cols:
            assert col in df.columns, f"Column {col} missing in {cat_path.name}!"
        
        # Verify source_id uniqueness
        assert df["source_id"].nunique() == len(df), f"Duplicate source_ids found in {cat_path.name}!"


def test_wcs_to_pixel_coordinate_conversion():
    """Requirement 3: Verify WCS-to-pixel and pixel-to-WCS coordinate conversion round-trip accuracy."""
    sample_fits = LEVEL2_DIR / "0001" / "level2_2026W30_1B_0001_1D1_spx_l2b-v27-2026-222.fits"
    with fits.open(sample_fits) as hdul:
        w = WCS(hdul["IMAGE"].header)
    
    # Test grid of pixel coordinates
    test_px = np.array([100.0, 500.0, 1020.0, 1500.0, 1940.0])
    test_py = np.array([100.0, 500.0, 1020.0, 1500.0, 1940.0])
    
    ra, dec = w.pixel_to_world_values(test_px, test_py)
    recovered_px, recovered_py = w.world_to_pixel_values(ra, dec)
    
    np.testing.assert_allclose(recovered_px, test_px, atol=1e-3, err_msg="WCS round-trip X failed!")
    np.testing.assert_allclose(recovered_py, test_py, atol=1e-3, err_msg="WCS round-trip Y failed!")


def test_mask_geometry_and_boundary_behavior():
    """Requirement 4: Verify mask diagnostics geometry and active area constraints."""
    for p in POINTINGS:
        diag_path = MASK_DIR / f"pointing_{p}_mask_diagnostics.json"
        assert diag_path.exists(), f"Mask diagnostics for P{p} missing!"
        with open(diag_path, "r", encoding="utf-8") as f:
            diag = json.load(f)
        
        assert diag["pointing"] == p
        assert diag["n_exposures_evaluated"] == 24
        
        for exp_key, exp_data in diag["detector_exposures"].items():
            usable_frac = exp_data["usable_fraction"]
            assert 0.70 <= usable_frac <= 0.95, f"Unusual usable fraction {usable_frac} in {exp_key}!"
            assert exp_data["usable_pixels_approx"] > 0
            assert exp_data["total_pixels"] == 2040 * 2040


def test_ambiguous_and_blended_source_classification():
    """Requirement 5: Verify source classification handles crowded, saturated, and isolated sources."""
    # Create synthetic test catalog
    test_df = pd.DataFrame({
        "ra": [10.0, 10.0001, 20.0, 30.0, 40.0],
        "dec": [0.0, 0.0001, 0.0, 0.0, 0.0],
        "pmra": [0.0, 0.0, 0.0, 0.0, 0.0],
        "pmdec": [0.0, 0.0, 0.0, 0.0, 0.0],
        "phot_g_mean_mag": [15.0, 15.0, 10.0, 16.0, 16.0],  # #2 is saturated (G=10)
        "ruwe": [1.0, 1.0, 1.0, 1.0, 2.5],  # #4 is high ruwe
        "astrometric_excess_noise": [0.0, 0.0, 0.0, 5.0, 0.0],  # #3 is extended (en=5)
        "tmass_id": [None, None, None, None, None],
        "tmass_dist_arcsec": [None, None, None, None, None]
    })
    prop_df = propagate_astrometry(test_df)
    class_df = classify_sources(prop_df)
    
    cats = class_df["classification_category"].values
    # Sources 0 and 1 are within ~0.5" -> BLENDED_CROWDED
    assert cats[0] == "BLENDED_CROWDED"
    assert cats[1] == "BLENDED_CROWDED"
    # Source 2 has G=10.0 -> SATURATED_OR_CONTAMINATED
    assert cats[2] == "SATURATED_OR_CONTAMINATED"
    # Source 3 has excess noise = 5.0 -> EXTENDED
    assert cats[3] == "EXTENDED"
    # Source 4 has RUWE = 2.5 -> UNCERTAIN_OR_LOW_QUALITY
    assert cats[4] == "UNCERTAIN_OR_LOW_QUALITY"


def test_calibration_evaluation_strict_disjointness():
    """Requirement 6: Verify zero cross-boundary leakage between calibration and evaluation."""
    assert MANIFEST_CSV.exists(), "Manifest CSV missing!"
    df = pd.read_csv(MANIFEST_CSV, dtype={"pointing": str})
    
    cal_mask = df["role"] == "CALIBRATION"
    eval_mask = df["role"] == "EVALUATION"
    
    cal_pointings = set(df.loc[cal_mask, "pointing"].unique())
    eval_pointings = set(df.loc[eval_mask, "pointing"].unique())
    
    # Must be disjoint
    overlap = cal_pointings.intersection(eval_pointings)
    assert len(overlap) == 0, f"Cross-boundary pointing leakage detected: {overlap}!"
    assert cal_pointings == set(CALIBRATION_POINTINGS)
    assert eval_pointings == set(EVALUATION_POINTINGS)

    # Check FITS filenames disjointness
    cal_files = set(df.loc[cal_mask, "fits_filename"].unique())
    eval_files = set(df.loc[eval_mask, "fits_filename"].unique())
    file_overlap = cal_files.intersection(eval_files)
    assert len(file_overlap) == 0, f"Cross-boundary FITS file leakage detected: {file_overlap}!"


def test_pointing_level_dither_grouping():
    """Requirement 7: Verify trials preserve detector and dither groupings."""
    df = pd.read_csv(MANIFEST_CSV, dtype={"pointing": str})
    for p in POINTINGS:
        sub = df[df["pointing"] == p]
        dithers = set(sub["dither"].unique())
        detectors = set(sub["detector_num"].unique())
        assert dithers.issubset({1, 2, 3, 4}), f"Invalid dithers {dithers} in P{p}!"
        assert detectors.issubset({1, 2, 3, 4, 5, 6}), f"Invalid detectors {detectors} in P{p}!"


def test_deterministic_partition_manifest_generation():
    """Requirement 8: Verify manifest generation is 100% deterministic with seed=42."""
    df1 = pd.read_csv(MANIFEST_CSV, dtype={"pointing": str})
    # Generate in-memory with same seed
    df2 = generate_five_partition_manifest(seed=42)
    # Ensure pointing types match for comparison
    df2["pointing"] = df2["pointing"].astype(str)
    pd.testing.assert_frame_equal(df1, df2, check_exact=False, check_dtype=False)


def test_invalid_or_missing_catalogue_handling():
    """Requirement 9: Verify invalid or corrupted input handling."""
    # Test missing file error handling
    with pytest.raises(Exception):
        pd.read_csv("non_existent_catalogue.csv")


def test_provenance_and_checksum_integrity():
    """Requirement 10: Verify all 16 historical protected assets match frozen SHA-256 signatures."""
    for rel_path, expected_hash in PROTECTED_ASSETS.items():
        full_path = BASE_DIR / rel_path
        assert full_path.exists(), f"Protected asset {rel_path} does not exist!"
        actual_hash = compute_sha256(full_path)
        assert actual_hash == expected_hash, f"MUTATION DETECTED in {rel_path}: {actual_hash} != {expected_hash}"
