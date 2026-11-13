"""
Automated Integration & Unit Tests for SPECTRA-X Interactive Observatory MVP
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline (l2b-v27-2026-222)

Tests:
1. Data Provider Candidate Catalog Loading & Indexing
2. Pagination, Search, Filter, and Sorting Operations
3. Level-2 FITS Cutout Extraction & Calibrated Difference Generation
4. Fail-Closed CHRONOS-X Temporal Governance on Dither Pairs
5. 102-Channel Spectrophotometry SED Generation & Mask Tracking
6. Rayleigh-Jeans Infrared Sidecar Integration
7. Review Submission, Validation, and JSON File Persistence
8. Static Production Bundle Verification (Vite compiled dist)
"""

import os
import sys
import json
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.data_provider import ObservatoryDataProvider


@pytest.fixture(scope="module")
def data_provider():
    """Initializes a shared instance of ObservatoryDataProvider."""
    return ObservatoryDataProvider()


def test_system_status(data_provider):
    """Verify system status reports healthy operational parameters."""
    status = data_provider.get_system_status()
    assert status["status"] == "HEALTHY"
    assert status["pipeline"] == "l2b-v27-2026-222"
    assert status["active_pointing"] == "0003"
    assert status["candidates_loaded"] == 1392
    assert "models" in status
    assert status["models"]["astrovision_spatial"] == "INSTANTIATED"
    assert status["models"]["spectra_v2"] == "INSTANTIATED"
    assert "data_paths" in status


def test_candidates_catalog_loading_and_pagination(data_provider):
    """Verify candidates pagination, schema completeness, and sorting."""
    res = data_provider.list_candidates(page=1, page_size=10, sort_by="anomaly_score", sort_order="desc")
    assert res["status"] == "SUCCESS"
    assert res["page"] == 1
    assert res["page_size"] == 10
    assert res["total"] == 1392
    assert len(res["data"]) == 10

    # Ensure schema attributes are present
    first = res["data"][0]
    required_fields = ["candidate_id", "ra_deg", "dec_deg", "spatial_score", "spectral_score", "anomaly_score", "status"]
    for field in required_fields:
        assert field in first, f"Missing required field: {field}"

    # Verify descending sort order on anomaly_score
    scores = [c["anomaly_score"] for c in res["data"]]
    assert scores == sorted(scores, reverse=True)


def test_candidates_search_and_filter(data_provider):
    """Verify search by ID substring and filtering by validation status."""
    # Search test
    search_res = data_provider.list_candidates(search="SPX-J163", page_size=20)
    assert search_res["status"] == "SUCCESS"
    assert len(search_res["data"]) > 0
    for cand in search_res["data"]:
        assert "SPX-J163" in cand["candidate_id"]

    # Filter test: WARNING
    warning_res = data_provider.list_candidates(validity="WARNING", page_size=10)
    assert warning_res["status"] == "SUCCESS"
    for cand in warning_res["data"]:
        assert cand.get("status") == "WARNING"


def test_candidate_retrieval_by_id(data_provider):
    """Verify get_candidate retrieves single candidate with correct metadata."""
    cand = data_provider.get_candidate("SPX-J163.6309-69.4422")
    assert cand is not None
    assert cand["candidate_id"] == "SPX-J163.6309-69.4422"
    assert abs(cand["ra_deg"] - 163.6309) < 0.001
    assert abs(cand["dec_deg"] - (-69.4422)) < 0.001


def test_fits_cutout_extraction_and_difference(data_provider):
    """Verify dual-epoch FITS cutout extraction, difference map, and WCS coordinates."""
    res = data_provider.get_cutout("SPX-J163.6309-69.4422")
    assert res["status"] == "SUCCESS"
    d = res["data"]

    assert "cutout_e1_base64" in d and len(d["cutout_e1_base64"]) > 100
    assert "cutout_e2_base64" in d and len(d["cutout_e2_base64"]) > 100
    assert "diff_base64" in d and len(d["diff_base64"]) > 100
    assert "sig_base64" in d and len(d["sig_base64"]) > 100
    assert d["patch_size"] == 128

    coords = d["coordinates"]
    assert "ra" in coords and "dec" in coords
    assert coords["x_pixel"] > 0
    assert coords["y_pixel"] > 0


def test_fail_closed_temporal_eligibility_on_dither(data_provider):
    """Verify CHRONOS-X temporal eligibility fails closed on intra-visit dither."""
    res = data_provider.get_cutout("SPX-J163.6309-69.4422")
    assert res["status"] == "SUCCESS"
    elig = res["data"]["temporal_eligibility"]

    assert elig["is_dither"] is True
    assert elig["status"] == "FALSE"
    assert elig["exclusion_reason"] == "INTRA_VISIT_DITHER"
    assert "dt_minutes" in res["data"]["dither_pair"]
    assert 1.0 < res["data"]["dither_pair"]["dt_minutes"] < 15.0


def test_102_channel_sed_extraction(data_provider):
    """Verify 102-channel spectrophotometry vector, wavelengths, and sidecar."""
    res = data_provider.get_spectrum("SPX-J163.6309-69.4422")
    assert res["status"] == "SUCCESS"
    d = res["data"]

    assert len(d["wavelengths_um"]) == 102
    assert len(d["observed_flux"]) == 102
    assert len(d["reconstructed_flux"]) == 102
    assert len(d["flux_errors"]) == 102
    assert len(d["band_labels"]) == 102

    # Check wavelength bounds (SPHEREx 0.75 - 5.00 um)
    assert d["wavelengths_um"][0] >= 0.70
    assert d["wavelengths_um"][-1] <= 5.10

    # Check metrics
    metrics = d["metrics"]
    assert "reconstruction_loss" in metrics
    assert "latent_norm" in metrics
    assert "threshold" in metrics
    assert metrics["threshold"] == 0.0450

    # Check sidecar
    assert "sidecar_excess" in d
    assert "excess_ratio" in d["sidecar_excess"]


def test_review_submission_and_persistence(data_provider):
    """Verify review saving, schema validation, and persistence to JSON."""
    test_cand_id = "SPX-J163.6309-69.4422"
    review_payload = {
        "candidate_id": test_cand_id,
        "ra_deg": 163.6309,
        "dec_deg": -69.4422,
        "disposition": "CONFIRMED_CANDIDATE",
        "confidence_pct": 95,
        "reviewer_id": "TEST_INVESTIGATOR_ALPHA",
        "notes": "Verified dither pair and 102-channel SED reconstruction."
    }

    save_res = data_provider.save_review(review_payload)
    assert save_res["status"] == "SUCCESS"

    # Retrieve reviews and verify inclusion
    reviews = data_provider.get_reviews()
    assert reviews["status"] == "SUCCESS"
    matching = [r for r in reviews["reviews"] if r.get("candidate_id") == test_cand_id and r.get("reviewer_id") == "TEST_INVESTIGATOR_ALPHA"]
    assert len(matching) > 0
    latest = matching[-1]
    assert latest["disposition"] == "CONFIRMED_CANDIDATE"
    assert latest["confidence_pct"] == 95
    assert "timestamp" in latest


def test_compiled_frontend_assets():
    """Verify production frontend/dist directory contains compiled React bundle."""
    dist_dir = os.path.join(BASE_DIR, "frontend", "dist")
    assert os.path.exists(dist_dir), "frontend/dist does not exist"

    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "frontend/dist/index.html missing"

    with open(index_html, "r", encoding="utf-8") as f:
        html = f.read()
    assert '<div id="root"></div>' in html
    assert "SPECTRA-X" in html

    assets_dir = os.path.join(dist_dir, "assets")
    assert os.path.exists(assets_dir), "frontend/dist/assets missing"
    asset_files = os.listdir(assets_dir)
    js_files = [f for f in asset_files if f.endswith(".js")]
    css_files = [f for f in asset_files if f.endswith(".css")]
    assert len(js_files) >= 1, "Compiled JS bundle missing"
    assert len(css_files) >= 1, "Compiled CSS bundle missing"
