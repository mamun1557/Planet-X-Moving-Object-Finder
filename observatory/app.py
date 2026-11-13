"""
SPECTRA-X Interactive Observatory — Single-Command Launch Entry Point
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline (l2b-v27-2026-222)

Usage:
    python observatory/app.py [--port PORT] [--host HOST] [--no-browser]

Launches the unified Python HTTP server which:
1. Serves the pre-compiled React + Vite interactive observatory frontend (HTML5/CSS/JS).
2. Serves the full REST API backend for candidates, FITS cutouts, SED spectra, and reviews.
3. Automatically opens the user's default browser to http://127.0.0.1:8050.
"""

import os
import sys
import argparse
import webbrowser
import threading
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.server import run_server


def main():
    parser = argparse.ArgumentParser(
        description="Launch the SPECTRA-X Interactive Observatory MVP (React + Vite + Python)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port to listen on (default: 8050)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically open the browser upon launch"
    )

    args = parser.parse_args()

    # Preflight check: Ensure frontend/dist exists
    dist_index = os.path.join(BASE_DIR, "frontend", "dist", "index.html")
    if not os.path.exists(dist_index):
        print(f"[WARNING] Compiled frontend not found at {dist_index}")
        print("Run 'npm --prefix frontend run build' before launching for production UI.")

    url = f"http://{args.host}:{args.port}/"

    def open_browser():
        time.sleep(1.2)
        print(f"\n[LAUNCH] Opening browser to: {url}")
        try:
            webbrowser.open(url)
        except Exception as e:
            print(f"[LAUNCH] Note: Could not launch browser automatically: {e}")

    if not args.no_browser:
        t = threading.Thread(target=open_browser, daemon=True)
        t.start()

    print("\n" + "=" * 70)
    print("  NASA SPACE APPS CHALLENGE 2026 — SPECTRA-X OBSERVATORY")
    print(f"  Pipeline Build:      l2b-v27-2026-222")
    print(f"  Interface URL:       {url}")
    print(f"  API Status:          {url}api/status")
    print(f"  Candidate Catalog:   {url}api/candidates")
    print(f"  Scientific Field:    SPHEREx Pointing 0003 (1,392 Candidates)")
    print("=" * 70 + "\n")

    run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()

