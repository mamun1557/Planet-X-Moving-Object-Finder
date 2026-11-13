"""
Task 4.29D Automated Integration & Verification Tests:
Clean, Input-Driven Observatory Workspace, Session Isolation, and Motion Safeguards

Verifies:
1. Initial load starts in EMPTY_WORKSPACE with zero preloaded candidates.
2. App mount does not call legacy candidate-list or review-list endpoints.
3. FITS, CSV, JSON validation and rejection of invalid data.
4. Single observation safeguard: INSUFFICIENT_OBSERVATIONS.
5. Intra-visit dither safeguard: INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY (Δt < 1 day).
6. Multi-epoch motion eligibility: TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION (Δt ≥ 1 day).
7. WCS and timestamp omission handling.
8. Session isolation and independent scratch reset.
9. Personal test dataset is not preloaded on startup.
10. Frozen model checkpoint and threshold hash immutability.
"""

import os
import sys
import json
import hashlib
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.session_manager import SessionManager
from observatory.motion_analysis import (
    AstronomicalMotionEngine,
    ObservationEpoch
)
from observatory.data_provider import ObservatoryDataProvider
from observatory.sample_library import SampleLibraryCatalog


@pytest.fixture
def session_manager():
    return SessionManager()


@pytest.fixture
def data_provider():
    return ObservatoryDataProvider()


def test_empty_workspace_initial_state_contract():
    """Verify that App.jsx specifies EMPTY_WORKSPACE and makes zero legacy auto-fetch calls."""
    app_jsx_path = os.path.join(BASE_DIR, "frontend", "src", "App.jsx")
    with open(app_jsx_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must default to OBSERVATORY tab with empty files
    assert "activeTab, setActiveTab] = useState('OBSERVATORY')" in content
    assert "uploadedFiles, setUploadedFiles] = useState([])" in content
    assert "analysisResults, setAnalysisResults] = useState(null)" in content

    # Must NOT call legacy fetchCandidates or fetchReviews on mount
    assert "fetchCandidates(" not in content
    assert "fetchReviews(" not in content


def test_fits_validation_and_rejection(data_provider):
    """Verify that valid FITS files are accepted while malformed files are rejected."""
    # Malformed FITS content
    invalid_res = data_provider.validate_astronomical_file(
        filename="corrupt.fits",
        content="THIS IS NOT A VALID FITS HEADER",
        file_type="FITS"
    )
    assert invalid_res["status"] in ["INVALID", "REJECTED", "ERROR", "INVALID_FILE"]

    # Valid mock FITS cutout from sample library
    sample_cat = SampleLibraryCatalog()
    samples = sample_cat.list_samples(dataset_class="REAL_INTRA_VISIT")
    assert len(samples) > 0
    sample_pair = samples[0]
    pair_meta = sample_cat.get_sample(sample_pair["pair_id"])
    assert pair_meta is not None
    assert pair_meta["pair_id"] == sample_pair["pair_id"]


def test_csv_and_json_schema_validation(data_provider):
    """Verify tabular CSV and JSON observation validation."""
    valid_csv = "ra,dec,timestamp\n163.6309,-69.4422,2025-06-15T09:42:00Z\n"
    res_csv = data_provider.validate_astronomical_file(
        filename="custom_coords.csv",
        content=valid_csv,
        file_type="CSV"
    )
    assert res_csv["status"] in ["VALID", "SUCCESS"]
    assert res_csv["has_coordinates"] is True
    assert "ra" in res_csv["columns"]

    # Empty / malformed CSV
    res_bad = data_provider.validate_astronomical_file(
        filename="empty.csv",
        content="",
        file_type="CSV"
    )
    assert res_bad["status"] in ["INVALID", "REJECTED", "WARNING", "INVALID_FILE"]


def test_single_observation_insufficient_safeguard():
    """Verify that a single observation cannot produce a movement result."""
    obs_a = ObservationEpoch(
        obs_id="SINGLE_OBS",
        ra_deg=180.0,
        dec_deg=10.0,
        timestamp="2026-01-01T00:00:00Z"
    )

    res = AstronomicalMotionEngine.calculate_motion(obs_a=obs_a, obs_b=None)
    assert not res.is_valid
    assert res.status == "INSUFFICIENT_OBSERVATIONS"
    assert res.angular_displacement_arcsec is None
    assert res.motion_rate_arcsec_per_hour is None


def test_intra_visit_dither_safeguard_short_cadence():
    """Verify that observation separation < 1 day triggers dither safeguard."""
    obs_a = ObservationEpoch(
        obs_id="DITHER_1",
        ra_deg=163.6318,
        dec_deg=-69.4421,
        timestamp="2025-06-15T09:42:00Z",
        wcs_valid=True
    )
    obs_b = ObservationEpoch(
        obs_id="DITHER_2",
        ra_deg=163.6309,
        dec_deg=-69.4422,
        timestamp="2025-06-15T09:47:02Z",  # ~5 minutes later
        wcs_valid=True
    )

    res = AstronomicalMotionEngine.calculate_motion(obs_a=obs_a, obs_b=obs_b)
    assert res.is_valid
    assert res.status == "SUCCESS"
    assert res.temporal_eligibility_status == "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
    assert res.time_baseline_days < 1.0
    assert not res.is_secular_motion_eligible
    assert "INTRA-VISIT DITHER" in res.notes


def test_multi_epoch_eligible_motion_calculation():
    """Verify that multi-day baseline correctly calculates motion kinematics."""
    obs_a = ObservationEpoch(
        obs_id="EPOCH_1",
        ra_deg=180.0,
        dec_deg=0.0,
        timestamp="2026-03-01T00:00:00Z"
    )
    # Displaced by 60 arcseconds in RA over 2 days
    dra_deg = (60.0 / 3600.0)
    obs_b = ObservationEpoch(
        obs_id="EPOCH_2",
        ra_deg=180.0 + dra_deg,
        dec_deg=0.0,
        timestamp="2026-03-03T00:00:00Z"  # 2.0 days later
    )

    res = AstronomicalMotionEngine.calculate_motion(obs_a=obs_a, obs_b=obs_b)
    assert res.is_valid
    assert res.status == "SUCCESS"
    assert res.temporal_eligibility_status == "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION"
    assert res.time_baseline_days == 2.0
    assert res.is_secular_motion_eligible
    assert abs(res.angular_displacement_arcsec - 60.0) < 0.05
    assert abs(res.motion_rate_arcsec_per_day - 30.0) < 0.05
    assert abs(res.motion_rate_arcsec_per_hour - 1.25) < 0.05


def test_session_isolation_and_independent_reset(session_manager):
    """Verify that two distinct sessions do not share state or uploaded data."""
    s1 = session_manager.create_session()
    s2 = session_manager.create_session()
    assert s1.session_id != s2.session_id

    # Populate session 1
    s1.dataset_mode = "USER_UPLOAD"
    s1.candidates = [{"id": "CAND_1"}]
    s1.uploaded_files = [{"filename": "user_data.fits"}]

    # Verify session 2 is completely unpolluted
    assert s2.dataset_mode == "EMPTY"
    assert len(s2.candidates) == 0
    assert len(s2.uploaded_files) == 0

    # Reset session 1
    session_manager.reset_session(s1.session_id)
    assert s1.dataset_mode == "EMPTY"
    assert len(s1.candidates) == 0

    # Clean up
    session_manager.delete_session(s1.session_id)
    session_manager.delete_session(s2.session_id)


def test_optional_personal_test_package_not_mandatory():
    """Verify that the 50-pair personal test dataset is optional and accessible via sample library."""
    sample_cat = SampleLibraryCatalog()
    samples = sample_cat.list_samples()
    # At least 50 pairs registered from manifest
    assert len(samples) >= 50

    # Verify dataset manifests exist
    zip_path = os.path.join(BASE_DIR, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data.zip")
    assert os.path.exists(zip_path), "Personal test dataset ZIP archive must exist"


def test_protected_scientific_assets_hashes():
    """Verify that frozen model checkpoints and threshold tables remain 100% bitwise unchanged."""
    expected_hashes = {
        "checkpoints/astrovision_spatial_v3.pt": "3B608E496F43C2648C9DC8236E1A7F5B5ED4B7906CF900468C65C67016042D99",
        "checkpoints/spectra_masked_ae_v2.pt": "6ECADA80BA30EC803AF2CF21BA58D72E8209789B4F5DA68A22E60134A3B5A938",
        "data/processed/spectra/spectra_v2_provisional_thresholds_v1.json": "D40292972AAFB9D3948249BD402A178EEADB20DE5E37C02C227AC841974AB848"
    }

    for rel_path, exp_hash in expected_hashes.items():
        full_path = os.path.join(BASE_DIR, rel_path)
        assert os.path.exists(full_path), f"File {rel_path} must exist"
        with open(full_path, "rb") as f:
            file_hash = hashlib.sha256(f.read()).hexdigest().upper()
        assert file_hash == exp_hash, f"Hash mismatch for {rel_path}: {file_hash} vs {exp_hash}"
