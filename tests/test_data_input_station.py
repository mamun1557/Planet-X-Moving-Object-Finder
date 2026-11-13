"""
Tests for Data Input Station & Target Coordinate Selection Engine
NASA Space Apps Challenge 2026 — SPECTRA-X Interactive Observatory
Task 4.28F-CLEANUP-B Implementation Verification
"""

import os
import sys
import json
import io
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.data_provider import ObservatoryDataProvider


@pytest.fixture
def provider():
    return ObservatoryDataProvider()


def test_get_dataset_info(provider):
    info = provider.get_dataset_info()
    assert info["status"] == "SUCCESS"
    assert "SPHEREx" in info["dataset_name"]
    assert info["field_id"] == "P0003"
    assert info["field_bounds"]["ra_min"] == 163.5
    assert info["field_bounds"]["ra_max"] == 163.8
    assert info["field_bounds"]["dec_min"] == -69.6
    assert info["field_bounds"]["dec_max"] == -69.3
    assert info["sources_count"] > 0
    assert info["spectral_channels"] == 102


def test_coordinate_search_primary_candidate(provider):
    # SPX-J163.6309-69.4422 known gold candidate
    res = provider.search_target_by_coordinates(ra=163.6309, dec=-69.4422, radius_arcsec=30.0)
    assert res["status"] == "SUCCESS"
    assert res["matches_found"] >= 1
    assert "SPX-J163.6309-69.4422" in [c["candidate_id"] for c in res["candidates"]]
    assert res["primary_match"]["candidate_id"] == "SPX-J163.6309-69.4422"
    assert res["primary_match"]["distance_arcsec"] < 10.0


def test_coordinate_search_out_of_field_of_view(provider):
    # RA 180.0, Dec +25.0 is completely outside P0003 survey footprint
    res = provider.search_target_by_coordinates(ra=180.0, dec=25.0, radius_arcsec=60.0)
    assert res["status"] == "OUT_OF_FIELD_OF_VIEW"
    assert res["matches_found"] == 0
    assert len(res["candidates"]) == 0
    assert "outside the Pointing 0003 survey footprint" in res["message"]
    assert "Zero synthetic detections generated" in res["message"]


def test_coordinate_search_invalid_celestial_bounds(provider):
    # Physically impossible coordinates
    res1 = provider.search_target_by_coordinates(ra=400.0, dec=0.0)
    assert res1["status"] == "INVALID_COORDINATES"

    res2 = provider.search_target_by_coordinates(ra=163.6, dec=-95.0)
    assert res2["status"] == "INVALID_COORDINATES"

    res3 = provider.search_target_by_coordinates(ra="invalid", dec="invalid")
    assert res3["status"] == "INVALID_COORDINATES"


def test_coordinate_search_no_sources_within_tiny_radius(provider):
    # In-field coordinates, but tiny radius where no source exists
    res = provider.search_target_by_coordinates(ra=163.5100, dec=-69.5800, radius_arcsec=0.1)
    assert res["status"] == "NO_SOURCES_FOUND"
    assert res["matches_found"] == 0
    assert "nearest_source" in res


def test_validate_fits_file_astrovision_compatibility(provider):
    # Create an in-memory 2D FITS image
    data = np.random.normal(100.0, 5.0, (128, 128)).astype(np.float32)
    hdu = fits.PrimaryHDU(data=data)
    hdu.header["CRVAL1"] = 163.6309
    hdu.header["CRVAL2"] = -69.4422
    hdu.header["CTYPE1"] = "RA---TAN"
    hdu.header["CTYPE2"] = "DEC--TAN"
    hdu.header["CDELT1"] = -0.001
    hdu.header["CDELT2"] = 0.001

    buf = io.BytesIO()
    hdu.writeto(buf)
    fits_bytes = buf.getvalue()

    val = provider.validate_astronomical_file("cutout_e1.fits", fits_bytes)
    assert val["status"] == "VALID"
    assert val["format"] == "FITS"
    assert val["hdus_count"] == 1
    assert val["compatibility"]["astrovision"]["status"] == "COMPATIBLE"
    assert "2D spatial image" in val["compatibility"]["astrovision"]["notes"]
    assert val["compatibility"]["chronos_x"]["status"] == "EVALUATED_FAIL_CLOSED"
    assert val["compatibility"]["motion_x"]["status"] == "REQUIRES_MULTI_EPOCH"


def test_validate_csv_file_spectra_compatibility(provider):
    # Create CSV with 102 spectral flux channels
    cols = ["source_id", "ra", "dec"] + [f"ch_{i}" for i in range(102)]
    row = ["TEST_001", 163.63, -69.44] + list(np.random.rand(102))
    df = pd.DataFrame([row], columns=cols)
    csv_str = df.to_csv(index=False)

    val = provider.validate_astronomical_file("test_spectra.csv", csv_str)
    assert val["status"] == "VALID"
    assert val["format"] == "CSV"
    assert val["compatibility"]["spectra"]["status"] == "COMPATIBLE"
    assert "102" in val["compatibility"]["spectra"]["notes"]


def test_validate_csv_file_missing_channels(provider):
    # CSV with only coordinates and 3 channels
    df = pd.DataFrame([["TEST_002", 163.63, -69.44, 1.2, 1.4, 1.1]], columns=["id", "ra", "dec", "ch_0", "ch_1", "ch_2"])
    csv_str = df.to_csv(index=False)

    val = provider.validate_astronomical_file("test_short.csv", csv_str)
    assert val["status"] == "VALID"
    assert val["compatibility"]["spectra"]["status"] == "INCOMPATIBLE"
    assert "102 required" in val["compatibility"]["spectra"]["notes"]


def test_validate_unsupported_file_format(provider):
    val = provider.validate_astronomical_file("image.bmp", b"BMfakebmpheader")
    assert val["status"] == "INVALID"
    assert "Unsupported astronomical format" in val["message"]


def test_custom_dataset_session_isolation(provider):
    # Ensure baseline count
    baseline_count = len(provider._df_candidates)
    assert baseline_count > 0

    # Upload custom dataset session
    payload = {
        "name": "User_Session_Run_01",
        "sources": [{"candidate_id": "USER_SRC_01", "ra": 163.64, "dec": -69.45}]
    }
    upload_res = provider.upload_custom_dataset(payload)
    assert upload_res["status"] == "SUCCESS"
    assert upload_res["dataset_info"]["sources_count"] == 1

    # Check info reports custom active
    info = provider.get_dataset_info()
    assert info["custom_dataset_active"] is True
    assert info["custom_dataset_name"] == "User_Session_Run_01"

    # Baseline candidate catalog dataframe was NOT overwritten
    assert len(provider._df_candidates) == baseline_count

    # Clear custom dataset
    clear_res = provider.clear_custom_dataset()
    assert clear_res["status"] == "SUCCESS"
    assert provider.get_dataset_info()["custom_dataset_active"] is False


def test_server_http_routing_in_memory():
    """Verify that ObservatoryHTTPRequestHandler correctly routes Data Input Station endpoints in-memory."""
    from observatory.server import ObservatoryHTTPRequestHandler

    class DummyHandler(ObservatoryHTTPRequestHandler):
        def __init__(self, path, method="GET", body=b""):
            self.path = path
            self.command = method
            self.rfile = io.BytesIO(body)
            self.wfile = io.BytesIO()
            self.headers = {"Content-Length": str(len(body))}
            self.sent_status = None
            self.sent_headers = {}

        def send_response(self, code, message=None):
            self.sent_status = code

        def send_header(self, keyword, value):
            self.sent_headers[keyword] = value

        def end_headers(self):
            pass

    # 1. GET /api/dataset/info
    h1 = DummyHandler("/api/dataset/info", "GET")
    h1.do_GET()
    assert h1.sent_status == 200
    data1 = json.loads(h1.wfile.getvalue().decode("utf-8"))
    assert data1["status"] == "SUCCESS"
    assert data1["field_id"] == "P0003"

    # 2. POST /api/target/search
    body2 = json.dumps({"ra": 163.6309, "dec": -69.4422, "radius_arcsec": 30.0}).encode("utf-8")
    h2 = DummyHandler("/api/target/search", "POST", body2)
    h2.do_POST()
    assert h2.sent_status == 200
    data2 = json.loads(h2.wfile.getvalue().decode("utf-8"))
    assert data2["status"] == "SUCCESS"
    assert data2["primary_match"]["candidate_id"] == "SPX-J163.6309-69.4422"

    # 3. POST /api/data/validate
    body3 = json.dumps({"filename": "test.csv", "content": "id,ra,dec\nS1,163.6,-69.4", "file_type": "csv"}).encode("utf-8")
    h3 = DummyHandler("/api/data/validate", "POST", body3)
    h3.do_POST()
    assert h3.sent_status == 200
    data3 = json.loads(h3.wfile.getvalue().decode("utf-8"))
    assert data3["status"] == "VALID"
    assert "compatibility" in data3

    # 4. POST /api/data/upload
    body4 = json.dumps({"name": "Session_01", "sources": [{"candidate_id": "SRC1"}]}).encode("utf-8")
    h4 = DummyHandler("/api/data/upload", "POST", body4)
    h4.do_POST()
    assert h4.sent_status == 200
    data4 = json.loads(h4.wfile.getvalue().decode("utf-8"))
    assert data4["status"] == "SUCCESS"

    # 5. DELETE /api/data/upload
    h5 = DummyHandler("/api/data/upload", "DELETE")
    h5.do_DELETE()
    assert h5.sent_status == 200
    data5 = json.loads(h5.wfile.getvalue().decode("utf-8"))
    assert data5["status"] == "SUCCESS"
