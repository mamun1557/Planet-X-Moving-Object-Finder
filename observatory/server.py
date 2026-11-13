"""
SPECTRA-X Interactive Observatory — Web Server
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Lightweight, robust Python multi-threaded HTTP server providing:
1. Versioned REST API endpoints for candidate discovery, FITS cutouts, and SEDs.
2. Cryptographically secure, isolated session management (SessionManager).
3. Standalone astronomical motion analysis engine (AstronomicalMotionEngine).
4. Sample observation library registry and query API.
5. Production static file server hosting the compiled React + Vite frontend.
6. CORS support with X-Session-ID header support.
"""

import os
import sys
import json
import mimetypes
from urllib.parse import urlparse, parse_qs
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.data_provider import ObservatoryDataProvider
from observatory.session_manager import SessionManager
from observatory.motion_analysis import (
    AstronomicalMotionEngine,
    ObservationEpoch,
    validate_coordinates
)
from observatory.sample_library import SampleLibraryCatalog


class ObservatoryHTTPRequestHandler(BaseHTTPRequestHandler):
    data_provider = ObservatoryDataProvider()
    session_manager = SessionManager()
    sample_catalog = SampleLibraryCatalog()
    frontend_dist_dir = os.path.join(BASE_DIR, "frontend", "dist")

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Session-ID")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.end_headers()

    def do_OPTIONS(self):
        """Handle CORS pre-flight requests."""
        self._set_headers(204, "text/plain")

    def _send_json(self, data: Any, status_code: int = 200):
        self._set_headers(status_code, "application/json; charset=utf-8")
        payload = json.dumps(data, indent=2, default=str).encode("utf-8")
        self.wfile.write(payload)

    def _send_error(self, message: str, status_code: int = 400, extra: Optional[Dict[str, Any]] = None):
        err = {"status": "ERROR", "message": message}
        if extra:
            err.update(extra)
        self._send_json(err, status_code)

    def _extract_session_id(self, query: Optional[Dict[str, Any]] = None, body_json: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Extracts session_id from X-Session-ID header, query parameters, or request JSON body."""
        hdr_sid = self.headers.get("X-Session-ID")
        if hdr_sid and hdr_sid.strip():
            return hdr_sid.strip()

        if query and "session_id" in query:
            sid_val = query.get("session_id", [None])[0]
            if sid_val and sid_val.strip():
                return sid_val.strip()

        if body_json and "session_id" in body_json:
            sid_val = body_json.get("session_id")
            if sid_val and isinstance(sid_val, str) and sid_val.strip():
                return sid_val.strip()

        return None

    def do_GET(self):
        """Routes GET requests to API handlers or static frontend files."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        session_id = self._extract_session_id(query=query)

        # -------------------------------------------------------------
        # Session Management Routes
        # -------------------------------------------------------------
        if path == "/api/session/info" or path == "/api/session/info/":
            if not session_id:
                return self._send_error("Missing required session_id parameter or X-Session-ID header", 400)
            session = self.session_manager.get_session(session_id, auto_touch=True)
            if not session:
                return self._send_error("Session not found or expired", 404, {"error_code": "SESSION_EXPIRED_OR_NOT_FOUND"})
            return self._send_json({"status": "SUCCESS", "session": session.to_dict()})

        # -------------------------------------------------------------
        # Sample Library Routes
        # -------------------------------------------------------------
        elif path == "/api/samples/list" or path == "/api/samples/list/":
            ds_class = query.get("class", [None])[0]
            samples = self.sample_catalog.list_samples(dataset_class=ds_class)
            return self._send_json({
                "status": "SUCCESS",
                "count": len(samples),
                "filter_class": ds_class,
                "samples": samples
            })

        elif path == "/api/samples/get" or path == "/api/samples/get/":
            pair_id = query.get("pair_id", [None])[0]
            if not pair_id:
                return self._send_error("Missing pair_id query parameter", 400)
            sample = self.sample_catalog.get_sample(pair_id)
            if not sample:
                return self._send_error(f"Sample pair '{pair_id}' not found", 404)
            return self._send_json({"status": "SUCCESS", "sample": sample})

        # -------------------------------------------------------------
        # REST API Routes (Observatory Baseline)
        # -------------------------------------------------------------
        elif path == "/api/status" or path == "/api/status/":
            status = self.data_provider.get_system_status()
            status["active_sessions_count"] = self.session_manager.get_active_session_count()
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    status["session"] = session.to_dict()
            return self._send_json(status)

        elif path == "/api/candidates" or path == "/api/candidates/":
            # Check if this request belongs to an isolated session
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session and session.dataset_mode == "EMPTY":
                    # Input-driven session starts with zero candidates
                    return self._send_json({
                        "status": "SUCCESS",
                        "dataset_id": "EMPTY_WORKSPACE",
                        "total": 0,
                        "page": 1,
                        "page_size": 25,
                        "items": [],
                        "data": []
                    })
                elif session and session.dataset_mode == "USER_UPLOAD":
                    # Return session-scoped candidates
                    return self._send_json({
                        "status": "SUCCESS",
                        "dataset_id": f"SESSION_{session_id[:8]}",
                        "total": len(session.candidates),
                        "page": 1,
                        "page_size": max(1, len(session.candidates)),
                        "items": session.candidates,
                        "data": session.candidates
                    })

            # Default backward compatibility fallback (P0003 built-in)
            page = int(query.get("page", [1])[0])
            page_size = int(query.get("page_size", [25])[0])
            search = query.get("search", [""])[0]
            validity = query.get("validity", ["ALL"])[0]
            sort_by = query.get("sort_by", ["anomaly_score"])[0]
            sort_order = query.get("sort_order", ["desc"])[0]
            res = self.data_provider.list_candidates(
                page=page,
                page_size=page_size,
                search=search,
                validity=validity,
                sort_by=sort_by,
                sort_order=sort_order
            )
            return self._send_json(res)

        elif path.startswith("/api/candidate/"):
            cand_id = path.replace("/api/candidate/", "").strip()
            # If session-scoped, search session candidates first
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    match = next((c for c in session.candidates if c.get("candidate_id") == cand_id), None)
                    if match:
                        return self._send_json({"status": "SUCCESS", "candidate": match})

            cand = self.data_provider.get_candidate(cand_id)
            if cand:
                return self._send_json({"status": "SUCCESS", "candidate": cand})
            return self._send_error(f"Candidate '{cand_id}' not found", 404)

        elif path.startswith("/api/cutout/"):
            cand_id = path.replace("/api/cutout/", "").strip()
            res = self.data_provider.get_cutout(cand_id)
            status_code = 200 if res.get("status") == "SUCCESS" else 404
            return self._send_json(res, status_code)

        elif path.startswith("/api/spectrum/"):
            cand_id = path.replace("/api/spectrum/", "").strip()
            res = self.data_provider.get_spectrum(cand_id)
            status_code = 200 if res.get("status") == "SUCCESS" else 404
            return self._send_json(res, status_code)

        elif path == "/api/reviews" or path == "/api/reviews/":
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    return self._send_json({
                        "status": "SUCCESS",
                        "total_reviews": len(session.reviews),
                        "reviews": session.reviews
                    })
            return self._send_json(self.data_provider.get_reviews())

        elif path == "/api/dataset/info" or path == "/api/dataset/info/":
            return self._send_json(self.data_provider.get_dataset_info())

        # -------------------------------------------------------------
        # Static Frontend Serving (Compiled Vite App)
        # -------------------------------------------------------------
        if not os.path.exists(self.frontend_dist_dir):
            html = """<!DOCTYPE html>
            <html>
            <head><title>SPECTRA-X Observatory</title></head>
            <body style="background:#0b0e14;color:#e2e8f0;font-family:sans-serif;padding:40px;text-align:center;">
                <h2>SPECTRA-X Interactive Observatory — Backend Online</h2>
                <p>Pipeline Build: <code>l2b-v27-2026-222</code> | REST API Active</p>
                <p>SessionManager &amp; AstronomicalMotionEngine Online.</p>
                <p><a href="/api/status" style="color:#60a5fa;">View /api/status</a> | <a href="/api/samples/list" style="color:#60a5fa;">View /api/samples/list</a></p>
            </body>
            </html>"""
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(html.encode("utf-8"))
            return

        clean_path = path.lstrip("/")
        if not clean_path:
            clean_path = "index.html"

        file_path = os.path.join(self.frontend_dist_dir, clean_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/octet-stream"
            self._set_headers(200, mime_type)
            with open(file_path, "rb") as f:
                self.wfile.write(f.read())
            return
        else:
            index_path = os.path.join(self.frontend_dist_dir, "index.html")
            if os.path.exists(index_path):
                self._set_headers(200, "text/html; charset=utf-8")
                with open(index_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        return self._send_error(f"Asset '{path}' not found", 404)

    def do_POST(self):
        """Routes POST requests for sessions, motion analysis, targets, validation, and uploads."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        content_length = int(self.headers.get("Content-Length", 0))

        body_json = {}
        if content_length > 0:
            try:
                raw_body = self.rfile.read(content_length).decode("utf-8")
                body_json = json.loads(raw_body)
            except Exception as e:
                return self._send_error(f"Malformed JSON request body: {str(e)}", 400)

        session_id = self._extract_session_id(body_json=body_json)

        # -------------------------------------------------------------
        # Session Management Routes
        # -------------------------------------------------------------
        if path == "/api/session/create" or path == "/api/session/create/":
            session = self.session_manager.create_session()
            return self._send_json({"status": "SUCCESS", "session": session.to_dict()}, 201)

        elif path == "/api/session/reset" or path == "/api/session/reset/":
            if not session_id:
                return self._send_error("Missing required session_id parameter or header", 400)
            success = self.session_manager.reset_session(session_id)
            if not success:
                return self._send_error("Session not found or expired", 404)
            return self._send_json({"status": "SUCCESS", "message": f"Session {session_id} reset to EMPTY state."})

        # -------------------------------------------------------------
        # Astronomical Motion Analysis Route
        # -------------------------------------------------------------
        elif path == "/api/motion/analyze" or path == "/api/motion/analyze/":
            obs_a_raw = body_json.get("obs_a")
            obs_b_raw = body_json.get("obs_b")

            obs_a = None
            if obs_a_raw and isinstance(obs_a_raw, dict):
                obs_a = ObservationEpoch(
                    obs_id=str(obs_a_raw.get("obs_id", "OBS_A")),
                    ra_deg=float(obs_a_raw.get("ra", obs_a_raw.get("ra_deg", 0.0))),
                    dec_deg=float(obs_a_raw.get("dec", obs_a_raw.get("dec_deg", 0.0))),
                    timestamp=obs_a_raw.get("timestamp", obs_a_raw.get("date_obs", "")),
                    wcs_valid=bool(obs_a_raw.get("wcs_valid", True)),
                    sigma_coord_arcsec=float(obs_a_raw.get("sigma_arcsec", obs_a_raw.get("sigma_coord_arcsec", 0.05))),
                    mjd=float(obs_a_raw["mjd"]) if "mjd" in obs_a_raw and obs_a_raw["mjd"] is not None else None
                )

            obs_b = None
            if obs_b_raw and isinstance(obs_b_raw, dict):
                obs_b = ObservationEpoch(
                    obs_id=str(obs_b_raw.get("obs_id", "OBS_B")),
                    ra_deg=float(obs_b_raw.get("ra", obs_b_raw.get("ra_deg", 0.0))),
                    dec_deg=float(obs_b_raw.get("dec", obs_b_raw.get("dec_deg", 0.0))),
                    timestamp=obs_b_raw.get("timestamp", obs_b_raw.get("date_obs", "")),
                    wcs_valid=bool(obs_b_raw.get("wcs_valid", True)),
                    sigma_coord_arcsec=float(obs_b_raw.get("sigma_arcsec", obs_b_raw.get("sigma_coord_arcsec", 0.05))),
                    mjd=float(obs_b_raw["mjd"]) if "mjd" in obs_b_raw and obs_b_raw["mjd"] is not None else None
                )

            sigma_a_override = body_json.get("sigma_a_arcsec")
            sigma_b_override = body_json.get("sigma_b_arcsec")

            motion_res = AstronomicalMotionEngine.calculate_motion(
                obs_a=obs_a,
                obs_b=obs_b,
                sigma_a_override=float(sigma_a_override) if sigma_a_override is not None else None,
                sigma_b_override=float(sigma_b_override) if sigma_b_override is not None else None
            )

            status_code = 200 if motion_res.is_valid else 422
            return self._send_json(motion_res.to_dict(), status_code)

        # -------------------------------------------------------------
        # Sample Library Loading Route
        # -------------------------------------------------------------
        elif path == "/api/samples/load" or path == "/api/samples/load/":
            if not session_id:
                return self._send_error("Missing required session_id parameter or header", 400)
            pair_id = body_json.get("pair_id")
            if not pair_id:
                return self._send_error("Missing required pair_id in body", 400)

            session = self.session_manager.get_session(session_id, auto_touch=True)
            if not session:
                return self._send_error("Session not found or expired", 404)

            sample = self.sample_catalog.get_sample(pair_id)
            if not sample:
                return self._send_error(f"Sample pair '{pair_id}' not found", 404)

            session.dataset_mode = "SAMPLE"
            session.sample_pair_id = pair_id
            return self._send_json({
                "status": "SUCCESS",
                "message": f"Sample pair '{pair_id}' loaded into session {session_id}.",
                "session": session.to_dict(),
                "sample": sample
            })

        # -------------------------------------------------------------
        # Target Search & Reviews (Session-Aware)
        # -------------------------------------------------------------
        elif path == "/api/review" or path == "/api/review/":
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    review_record = dict(body_json)
                    review_record["session_id"] = session_id
                    session.reviews.append(review_record)
                    return self._send_json({
                        "status": "SUCCESS",
                        "message": "Review recorded in active session.",
                        "session_id": session_id,
                        "review": review_record
                    })

            res = self.data_provider.save_review(body_json)
            status_code = 200 if res.get("status") == "SUCCESS" else 400
            return self._send_json(res, status_code)

        elif path == "/api/target/search" or path == "/api/target/search/":
            ra = body_json.get("ra")
            dec = body_json.get("dec")
            radius = body_json.get("radius_arcsec", 30.0)
            res = self.data_provider.search_target_by_coordinates(ra, dec, radius)
            status_code = 200 if res.get("status") in ["SUCCESS", "NO_SOURCES_FOUND", "OUT_OF_FIELD_OF_VIEW"] else 400
            return self._send_json(res, status_code)

        elif path == "/api/data/validate" or path == "/api/data/validate/":
            filename = body_json.get("filename", "uploaded_file.dat")
            content = body_json.get("content") or body_json.get("content_base64") or body_json.get("content_text", "")
            file_type = body_json.get("file_type")
            res = self.data_provider.validate_astronomical_file(filename, content, file_type)
            return self._send_json(res, 200)

        elif path == "/api/data/upload" or path == "/api/data/upload/":
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    # Isolate upload inside session
                    session.dataset_mode = "USER_UPLOAD"
                    candidates = body_json.get("candidates", [])
                    session.candidates = candidates
                    session.uploaded_files.append({
                        "filename": body_json.get("filename", "custom_catalog.csv"),
                        "candidates_count": len(candidates)
                    })
                    return self._send_json({
                        "status": "SUCCESS",
                        "session_id": session_id,
                        "message": f"Successfully loaded {len(candidates)} candidates into isolated session.",
                        "candidates_loaded": len(candidates)
                    })

            res = self.data_provider.upload_custom_dataset(body_json)
            status_code = 200 if res.get("status") == "SUCCESS" else 400
            return self._send_json(res, status_code)

        return self._send_error(f"Endpoint '{path}' not found", 404)

    def do_DELETE(self):
        """Routes DELETE requests for clearing session or uploaded data."""
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query = parse_qs(parsed_url.query)
        session_id = self._extract_session_id(query=query)

        if path == "/api/session" or path == "/api/session/":
            if not session_id:
                return self._send_error("Missing required session_id parameter or header", 400)
            deleted = self.session_manager.delete_session(session_id)
            if not deleted:
                return self._send_error("Session not found or already deleted", 404)
            return self._send_json({"status": "SUCCESS", "message": f"Session {session_id} terminated and purged."})

        elif path == "/api/data/upload" or path == "/api/data/upload/":
            if session_id:
                session = self.session_manager.get_session(session_id, auto_touch=True)
                if session:
                    session.candidates.clear()
                    session.uploaded_files.clear()
                    session.dataset_mode = "EMPTY"
                    return self._send_json({
                        "status": "SUCCESS",
                        "session_id": session_id,
                        "message": "Custom session dataset cleared."
                    })
            res = self.data_provider.clear_custom_dataset()
            return self._send_json(res, 200)

        return self._send_error(f"Endpoint '{path}' not found", 404)


def run_server(host: str = "127.0.0.1", port: int = 8050):
    """Launches the threaded HTTP server."""
    server_address = (host, port)
    httpd = ThreadingHTTPServer(server_address, ObservatoryHTTPRequestHandler)
    print(f"=================================================================")
    print(f"SPECTRA-X Interactive Observatory Server")
    print(f"Pipeline Build: l2b-v27-2026-222")
    print(f"SessionManager: Active (TTL = 7200s, Ephemeral Scratch Storage)")
    print(f"Motion Engine:  AstronomicalMotionEngine Active")
    print(f"Sample Library: SampleLibraryCatalog Active")
    print(f"Local Server running at: http://{host}:{port}/")
    print(f"REST API Endpoints:      http://{host}:{port}/api/status")
    print(f"                         http://{host}:{port}/api/session/create")
    print(f"                         http://{host}:{port}/api/motion/analyze")
    print(f"                         http://{host}:{port}/api/samples/list")
    print(f"Press Ctrl+C to stop.")
    print(f"=================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping Observatory Server...")
        httpd.server_close()


if __name__ == "__main__":
    port = 8050
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port=port)
