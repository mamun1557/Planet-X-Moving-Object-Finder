"""
Unit & Integration Tests for Task 4.29B
SessionManager, Astronomical Motion Engine & Sample Library API Contract

Verifies:
1. Two independent sessions maintain strictly isolated state.
2. Cross-session file access prevention and path traversal defense.
3. Expired session rejection and TTL cleanup.
4. RA wraparound handling at 0°/360° celestial boundary.
5. Exact spherical angular separation (Haversine formula).
6. Motion rate unit conversions (arcsec/hour, arcsec/day).
7. Coordinate uncertainty propagation: sigma_delta_theta = sqrt(sigma_1^2 + sigma_2^2).
8. Missing timestamp and missing WCS fail-closed handling.
9. Strict intra-visit dither safeguard (dt < 1 day vs dt >= 1 day).
10. Synthetic versus real sample metadata separation.
11. Invalid payloads and fail-closed error contracts.
12. HTTP Server integration for session and motion endpoints.
"""

import os
import sys
import time
import math
import shutil
import unittest
import tempfile
from typing import Dict, Any

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from observatory.session_manager import SessionManager, SessionState
from observatory.motion_analysis import (
    AstronomicalMotionEngine,
    ObservationEpoch,
    MotionAnalysisResult,
    MotionEligibilityStatus,
    MotionStatusCode,
    validate_coordinates,
    normalize_ra_deg,
    compute_ra_difference_deg,
    spherical_angular_separation_arcsec,
    position_angle_deg
)
from observatory.sample_library import (
    SampleLibraryCatalog,
    SamplePairMetadata,
    SampleDatasetClass
)


class TestSessionManager(unittest.TestCase):
    """Verifies cryptographic session creation, ephemeral directory isolation, and TTL reaping."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="test_sessions_")
        self.mgr = SessionManager(sessions_dir=self.temp_dir, default_ttl_seconds=2.0)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_session_creation_and_isolation(self):
        """Verify two independent sessions have distinct UUIDs, paths, and isolated state."""
        s1 = self.mgr.create_session()
        s2 = self.mgr.create_session()

        self.assertNotEqual(s1.session_id, s2.session_id)
        self.assertTrue(os.path.exists(s1.session_dir))
        self.assertTrue(os.path.exists(s2.session_dir))
        self.assertNotEqual(s1.session_dir, s2.session_dir)

        # Mutate s1 state
        s1.candidates.append({"candidate_id": "SPX-TEST-001", "ra": 100.0, "dec": 20.0})
        s1.dataset_mode = "USER_UPLOAD"

        # Verify s2 is completely unaffected
        self.assertEqual(len(s2.candidates), 0)
        self.assertEqual(s2.dataset_mode, "EMPTY")

        # Verify retrieval
        retrieved_s1 = self.mgr.get_session(s1.session_id)
        self.assertIsNotNone(retrieved_s1)
        self.assertEqual(len(retrieved_s1.candidates), 1)

    def test_cross_session_file_access_prevention(self):
        """Verify session directories cannot write into or delete sibling session files."""
        s1 = self.mgr.create_session()
        s2 = self.mgr.create_session()

        file_s1 = os.path.join(s1.session_dir, "data_s1.csv")
        with open(file_s1, "w", encoding="utf-8") as f:
            f.write("test_data_session_1")

        # Ensure s2 directory is clean and does not contain s1 file
        file_s2 = os.path.join(s2.session_dir, "data_s1.csv")
        self.assertFalse(os.path.exists(file_s2))

        # Resetting s2 must not affect s1 files
        self.mgr.reset_session(s2.session_id)
        self.assertTrue(os.path.exists(file_s1))

        # Deleting s2 must not remove s1
        self.mgr.delete_session(s2.session_id)
        self.assertTrue(os.path.exists(file_s1))
        self.assertFalse(os.path.exists(s2.session_dir))

    def test_path_traversal_defense(self):
        """Verify defensive guards block malicious path deletion outside sessions directory."""
        dangerous_paths = [
            os.path.abspath("."),
            os.path.abspath("data"),
            os.path.abspath("checkpoints"),
            self.temp_dir,  # root directory itself cannot be deleted by helper
            os.path.join(self.temp_dir, "..", "data")
        ]
        for p in dangerous_paths:
            self.assertFalse(self.mgr._is_safe_session_path(p))

    def test_session_ttl_expiration_and_cleanup(self):
        """Verify expired sessions are rejected and swept by automatic reaper."""
        # Short TTL manager
        short_mgr = SessionManager(sessions_dir=self.temp_dir, default_ttl_seconds=0.1)
        s = short_mgr.create_session()
        s_id = s.session_id
        s_dir = s.session_dir
        self.assertTrue(os.path.exists(s_dir))

        # Wait for TTL to expire
        time.sleep(0.15)

        # Retrieval should fail closed and reap
        retrieved = short_mgr.get_session(s_id)
        self.assertIsNone(retrieved)
        self.assertFalse(os.path.exists(s_dir))

        # Test orphan sweep
        orphan_dir = os.path.join(self.temp_dir, "orphan_test_session")
        os.makedirs(orphan_dir, exist_ok=True)
        time.sleep(0.15)
        reaped = short_mgr.cleanup_expired_sessions()
        self.assertGreaterEqual(reaped, 1)
        self.assertFalse(os.path.exists(orphan_dir))


class TestCoordinateAndMotionCalculations(unittest.TestCase):
    """Verifies spherical geometry, RA wraparound, and uncertainty propagation."""

    def test_ra_wraparound_at_meridian(self):
        """Verify RA difference wraps correctly across 0°/360° boundary."""
        # 359.9° to 0.1° -> shortest separation is +0.2°
        d_ra = compute_ra_difference_deg(359.9, 0.1)
        self.assertAlmostEqual(d_ra, 0.2, places=6)

        # 0.1° to 359.9° -> shortest separation is -0.2°
        d_ra_rev = compute_ra_difference_deg(0.1, 359.9)
        self.assertAlmostEqual(d_ra_rev, -0.2, places=6)

        # Exact boundary
        self.assertAlmostEqual(compute_ra_difference_deg(360.0, 0.0), 0.0, places=6)
        self.assertAlmostEqual(compute_ra_difference_deg(0.0, 360.0), 0.0, places=6)

    def test_spherical_angular_separation(self):
        """Verify Haversine separation matches exact geometric values."""
        # 1 arcsecond in Dec
        sep_dec_1as = spherical_angular_separation_arcsec(100.0, 0.0, 100.0, 1.0 / 3600.0)
        self.assertAlmostEqual(sep_dec_1as, 1.0, places=4)

        # 1 arcsecond in RA at equator (Dec = 0)
        sep_ra_1as = spherical_angular_separation_arcsec(0.0, 0.0, 1.0 / 3600.0, 0.0)
        self.assertAlmostEqual(sep_ra_1as, 1.0, places=4)

        # Across meridian: RA 359.99° to 0.01° at Dec = 0 (0.02° = 72 arcseconds)
        sep_wrap = spherical_angular_separation_arcsec(359.99, 0.0, 0.01, 0.0)
        self.assertAlmostEqual(sep_wrap, 72.0, places=4)

    def test_coordinate_uncertainty_propagation(self):
        """Verify sigma_delta_theta = sqrt(sigma_1^2 + sigma_2^2)."""
        sig_a = 0.03
        sig_b = 0.04
        expected_sig = math.sqrt(0.03**2 + 0.04**2)  # exactly 0.05

        obs_a = ObservationEpoch(
            obs_id="OBS_A",
            ra_deg=100.0,
            dec_deg=20.0,
            timestamp="2026-07-01T00:00:00Z",
            sigma_coord_arcsec=sig_a
        )
        obs_b = ObservationEpoch(
            obs_id="OBS_B",
            ra_deg=100.001,
            dec_deg=20.001,
            timestamp="2026-07-03T00:00:00Z",
            sigma_coord_arcsec=sig_b
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.coordinate_uncertainty_arcsec, expected_sig, places=4)

    def test_motion_rate_unit_conversions(self):
        """Verify rate conversions between arcsec/hour and arcsec/day."""
        # Baseline = 2.0 days = 48.0 hours
        # Angular displacement = 24.0 arcseconds
        # Expected rate per hour = 24.0 / 48.0 = 0.5 arcsec/hour
        # Expected rate per day = 24.0 / 2.0 = 12.0 arcsec/day
        obs_a = ObservationEpoch(
            obs_id="OBS_1",
            ra_deg=180.0,
            dec_deg=0.0,
            timestamp="2026-08-01T00:00:00Z"
        )
        # Shift in RA by 24 arcseconds = 24 / 3600 degrees = 0.00666667 degrees
        delta_deg = 24.0 / 3600.0
        obs_b = ObservationEpoch(
            obs_id="OBS_2",
            ra_deg=180.0 + delta_deg,
            dec_deg=0.0,
            timestamp="2026-08-03T00:00:00Z"
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertTrue(res.is_valid)
        self.assertAlmostEqual(res.time_baseline_days, 2.0, places=4)
        self.assertAlmostEqual(res.time_baseline_hours, 48.0, places=3)
        self.assertAlmostEqual(res.angular_displacement_arcsec, 24.0, places=2)
        self.assertAlmostEqual(res.motion_rate_arcsec_per_hour, 0.5, places=3)
        self.assertAlmostEqual(res.motion_rate_arcsec_per_day, 12.0, places=2)


class TestIntraVisitSafeguardAndFailClosed(unittest.TestCase):
    """Verifies intra-visit dither exclusion and fail-closed security contracts."""

    def test_intra_visit_dither_safeguard(self):
        """Verify dt < 1.0 day triggers INTRA_VISIT_DITHER and fails closed for secular motion."""
        # 6.45 minutes dither interval (like SPHEREx 1D1 vs 4D1)
        obs_a = ObservationEpoch(
            obs_id="SPX_1D1",
            ra_deg=163.6309,
            dec_deg=-69.4422,
            timestamp="2026-07-20T00:26:21.423Z"
        )
        obs_b = ObservationEpoch(
            obs_id="SPX_4D1",
            ra_deg=163.6318,
            dec_deg=-69.4421,
            timestamp="2026-07-20T00:32:48.216Z"
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, MotionStatusCode.SUCCESS.value)
        self.assertFalse(res.is_secular_motion_eligible)
        self.assertEqual(
            res.temporal_eligibility_status,
            MotionEligibilityStatus.INTRA_VISIT_DITHER.value
        )
        self.assertIn("INTRA_VISIT_DITHER", res.limitation_codes)
        self.assertIn("SECULAR_MOTION_INELIGIBLE", res.limitation_codes)

    def test_temporally_eligible_multi_day_baseline(self):
        """Verify dt >= 1.0 day reports TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION."""
        obs_a = ObservationEpoch(
            obs_id="EP_1",
            ra_deg=120.0,
            dec_deg=15.0,
            timestamp="2026-07-01T12:00:00Z"
        )
        obs_b = ObservationEpoch(
            obs_id="EP_2",
            ra_deg=120.01,
            dec_deg=15.01,
            timestamp="2026-07-05T12:00:00Z"  # 4 days later
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertTrue(res.is_valid)
        self.assertTrue(res.is_secular_motion_eligible)
        self.assertEqual(
            res.temporal_eligibility_status,
            MotionEligibilityStatus.TEMPORALLY_ELIGIBLE.value
        )

    def test_missing_timestamp_fails_closed(self):
        """Verify unparseable or missing timestamps return INVALID_TIMESTAMP."""
        obs_a = ObservationEpoch(
            obs_id="EP_1",
            ra_deg=120.0,
            dec_deg=15.0,
            timestamp="MALFORMED_TIMESTAMP_NOT_A_DATE"
        )
        obs_b = ObservationEpoch(
            obs_id="EP_2",
            ra_deg=120.01,
            dec_deg=15.01,
            timestamp="2026-07-05T12:00:00Z"
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, MotionStatusCode.INVALID_TIMESTAMP.value)

    def test_missing_wcs_fails_closed(self):
        """Verify missing or corrupt WCS returns MISSING_WCS."""
        obs_a = ObservationEpoch(
            obs_id="EP_1",
            ra_deg=120.0,
            dec_deg=15.0,
            timestamp="2026-07-01T12:00:00Z",
            wcs_valid=False
        )
        obs_b = ObservationEpoch(
            obs_id="EP_2",
            ra_deg=120.01,
            dec_deg=15.01,
            timestamp="2026-07-05T12:00:00Z",
            wcs_valid=True
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, MotionStatusCode.MISSING_WCS.value)

    def test_invalid_coordinates_fail_closed(self):
        """Verify Dec > 90° or NaN coordinates return INVALID_COORDINATES."""
        obs_a = ObservationEpoch(
            obs_id="EP_1",
            ra_deg=120.0,
            dec_deg=95.0,  # Physical Dec out of bounds
            timestamp="2026-07-01T12:00:00Z"
        )
        obs_b = ObservationEpoch(
            obs_id="EP_2",
            ra_deg=120.01,
            dec_deg=15.01,
            timestamp="2026-07-05T12:00:00Z"
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, MotionStatusCode.INVALID_COORDINATES.value)


class TestSampleLibraryCatalog(unittest.TestCase):
    """Verifies sample catalog metadata separation between real and synthetic data."""

    def setUp(self):
        self.catalog = SampleLibraryCatalog()

    def test_real_intra_visit_has_no_synthetic_vector(self):
        """Verify REAL_INTRA_VISIT samples NEVER expose synthetic ground-truth motion vectors."""
        real_samples = self.catalog.list_samples(dataset_class=SampleDatasetClass.REAL_INTRA_VISIT.value)
        self.assertGreaterEqual(len(real_samples), 1)

        for s in real_samples:
            self.assertEqual(s["dataset_class"], SampleDatasetClass.REAL_INTRA_VISIT.value)
            self.assertFalse(s["has_ground_truth_motion"])
            self.assertIsNone(s["synthetic_ground_truth_motion"])
            self.assertEqual(
                s["scientific_eligibility"],
                "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
            )

    def test_synthetic_engineering_sample_has_explicit_ground_truth(self):
        """Verify SYNTHETIC_ENGINEERING_TEST samples clearly identify synthetic ground truth."""
        syn_samples = self.catalog.list_samples(dataset_class=SampleDatasetClass.SYNTHETIC_ENGINEERING_TEST.value)
        self.assertGreaterEqual(len(syn_samples), 1)

        for s in syn_samples:
            self.assertEqual(s["dataset_class"], SampleDatasetClass.SYNTHETIC_ENGINEERING_TEST.value)
            self.assertTrue(s["has_ground_truth_motion"])
            self.assertIsNotNone(s["synthetic_ground_truth_motion"])
            gt = s["synthetic_ground_truth_motion"]
            self.assertTrue(gt.get("is_synthetic"))
            self.assertIn("NEVER claim as real astronomical discovery", gt.get("simulation_notes", ""))


import io
import json
from observatory.server import ObservatoryHTTPRequestHandler


class MockHTTPHandler(ObservatoryHTTPRequestHandler):
    """In-memory mock HTTP handler avoiding OS socket port allocations."""
    def __init__(self, method: str, path: str, body: Any = None, headers: Dict[str, str] = None):
        self.command = method
        self.path = path
        self.headers = headers or {}
        raw_body = json.dumps(body).encode("utf-8") if body is not None else b""
        self.rfile = io.BytesIO(raw_body)
        self.wfile = io.BytesIO()
        if body is not None:
            self.headers["Content-Length"] = str(len(raw_body))
        self.status_code = None
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.status_code = code

    def send_header(self, keyword, value):
        self.response_headers[keyword] = value

    def end_headers(self):
        pass


class TestHTTPServerSessionAndMotionRoutes(unittest.TestCase):
    """Verifies HTTP REST API endpoints for session management, motion analysis, and samples."""

    def _execute_request(self, method: str, path: str, body: Any = None, headers: Dict[str, str] = None) -> tuple:
        handler = MockHTTPHandler(method, path, body, headers)
        if method == "GET":
            handler.do_GET()
        elif method == "POST":
            handler.do_POST()
        elif method == "DELETE":
            handler.do_DELETE()
        else:
            raise ValueError(f"Unsupported method {method}")

        handler.wfile.seek(0)
        res_text = handler.wfile.read().decode("utf-8")
        parsed_json = json.loads(res_text) if res_text else {}
        return parsed_json, handler.status_code

    def test_http_session_lifecycle(self):
        """Verify POST /api/session/create, GET /api/session/info, and POST /api/session/reset."""
        # 1. Create session
        res, code = self._execute_request("POST", "/api/session/create", {})
        self.assertEqual(code, 201)
        self.assertEqual(res["status"], "SUCCESS")
        session_id = res["session"]["session_id"]
        self.assertTrue(bool(session_id))

        # 2. Get session info via header
        info_res, info_code = self._execute_request("GET", "/api/session/info", headers={"X-Session-ID": session_id})
        self.assertEqual(info_code, 200)
        self.assertEqual(info_res["session"]["session_id"], session_id)
        self.assertEqual(info_res["session"]["dataset_mode"], "EMPTY")

        # 3. Isolated candidates endpoint with session_id
        cand_res, cand_code = self._execute_request("GET", f"/api/candidates?session_id={session_id}")
        self.assertEqual(cand_code, 200)
        self.assertEqual(cand_res["dataset_id"], "EMPTY_WORKSPACE")
        self.assertEqual(cand_res["total"], 0)

        # 4. Reset session
        reset_res, reset_code = self._execute_request("POST", "/api/session/reset", {"session_id": session_id})
        self.assertEqual(reset_code, 200)
        self.assertEqual(reset_res["status"], "SUCCESS")

        # 5. Delete session
        del_res, del_code = self._execute_request("DELETE", f"/api/session?session_id={session_id}")
        self.assertEqual(del_code, 200)
        self.assertEqual(del_res["status"], "SUCCESS")

    def test_http_motion_analysis_intra_visit(self):
        """Verify POST /api/motion/analyze returns intra-visit dither classification."""
        payload = {
            "obs_a": {
                "obs_id": "SPX_1D1",
                "ra": 163.6309,
                "dec": -69.4422,
                "timestamp": "2026-07-20T00:26:21.423Z",
                "wcs_valid": True,
                "sigma_arcsec": 0.05
            },
            "obs_b": {
                "obs_id": "SPX_4D1",
                "ra": 163.6318,
                "dec": -69.4421,
                "timestamp": "2026-07-20T00:32:48.216Z",
                "wcs_valid": True,
                "sigma_arcsec": 0.05
            }
        }
        res, code = self._execute_request("POST", "/api/motion/analyze", payload)
        self.assertEqual(code, 200)
        self.assertTrue(res["is_valid"])
        self.assertFalse(res["is_secular_motion_eligible"])
        self.assertEqual(
            res["temporal_eligibility_status"],
            "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
        )
        self.assertGreater(res["angular_displacement_arcsec"], 0.0)

    def test_http_motion_analysis_multi_day(self):
        """Verify POST /api/motion/analyze returns temporal eligibility for dt >= 1 day."""
        payload = {
            "obs_a": {
                "obs_id": "EP_1",
                "ra": 200.0,
                "dec": -10.0,
                "timestamp": "2026-08-01T00:00:00Z",
                "wcs_valid": True,
                "sigma_arcsec": 0.05
            },
            "obs_b": {
                "obs_id": "EP_2",
                "ra": 200.005,
                "dec": -10.005,
                "timestamp": "2026-08-03T12:00:00Z",
                "wcs_valid": True,
                "sigma_arcsec": 0.05
            }
        }
        res, code = self._execute_request("POST", "/api/motion/analyze", payload)
        self.assertEqual(code, 200)
        self.assertTrue(res["is_valid"])
        self.assertTrue(res["is_secular_motion_eligible"])
        self.assertEqual(
            res["temporal_eligibility_status"],
            "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION"
        )

    def test_http_sample_library_endpoints(self):
        """Verify GET /api/samples/list, GET /api/samples/get, and POST /api/samples/load."""
        # 1. List samples
        list_res, code = self._execute_request("GET", "/api/samples/list")
        self.assertEqual(code, 200)
        self.assertGreaterEqual(list_res["count"], 2)
        samples = list_res["samples"]
        pair_ids = [s["pair_id"] for s in samples]
        self.assertIn("PAIR-REAL-P0003-D1-1D-4D", pair_ids)

        # 2. Get specific sample
        get_res, get_code = self._execute_request("GET", "/api/samples/get?pair_id=PAIR-REAL-P0003-D1-1D-4D")
        self.assertEqual(get_code, 200)
        self.assertEqual(get_res["sample"]["pair_id"], "PAIR-REAL-P0003-D1-1D-4D")

        # 3. Create session and load sample
        s_res, _ = self._execute_request("POST", "/api/session/create", {})
        session_id = s_res["session"]["session_id"]

        load_res, load_code = self._execute_request("POST", "/api/samples/load", {
            "session_id": session_id,
            "pair_id": "PAIR-REAL-P0003-D1-1D-4D"
        })
        self.assertEqual(load_code, 200)
        self.assertEqual(load_res["session"]["dataset_mode"], "SAMPLE")
        self.assertEqual(load_res["session"]["sample_pair_id"], "PAIR-REAL-P0003-D1-1D-4D")


if __name__ == "__main__":
    unittest.main()
