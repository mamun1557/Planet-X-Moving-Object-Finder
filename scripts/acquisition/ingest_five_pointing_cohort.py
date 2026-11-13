"""
SPECTRA-X / F1 — Phase 3, Task 1.1M
Production Multi-Pointing Ingestion Engine for 5-Pointing Cohort (0001, 0002, 0008, 0009, 0010).

Acquires and validates:
- Group A: Qualified Replacements (P0008, P0009, P0010) - 72 products
- Group B: Previously Authorized Pending (P0001, P0002) - 40 products
Total: 112 remote acquisitions + 8 locally verified = 120 products.
"""

import os
import sys
import time
import json
import shutil
import hashlib
import urllib.request
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from scripts.acquisition.multipointing_pilot import (
    StorageSafetyGate,
    ScientificFITSValidator,
    AtomicFileHandler
)

S3_BASE_URL = "https://nasa-irsa-spherex.s3.amazonaws.com"
PERIOD = "2026W30_1B"
BUILD = "l2b-v27-2026-222"
BASE_DIR = Path("data/spherex/multipointing_pilot")
STAGING_DIR = BASE_DIR / "staging"
LEVEL2_DIR = BASE_DIR / "level2"

TARGET_POINTINGS = ["0001", "0002", "0008", "0009", "0010"]

def get_product_list():
    products = []
    for p in TARGET_POINTINGS:
        group = "Group B (Pending Ingestion)" if p in ["0001", "0002"] else "Group A (Qualified Replacement)"
        for det in range(1, 7):
            for dither in range(1, 5):
                fname = f"level2_{PERIOD}_{p}_{dither}D{det}_spx_{BUILD}.fits"
                url = f"{S3_BASE_URL}/qr3/level2/{PERIOD}/{BUILD}/{det}/{fname}"
                dest_path = LEVEL2_DIR / p / fname
                products.append({
                    "pointing": p,
                    "detector": f"D{det}",
                    "detector_num": det,
                    "dither": dither,
                    "filename": fname,
                    "group": group,
                    "url": url,
                    "dest_path": dest_path
                })
    return products

def acquire_and_validate_one(prod):
    fname = prod["filename"]
    dest_path = prod["dest_path"]
    staging_path = STAGING_DIR / f"{fname}.part"
    p = prod["pointing"]
    det = prod["detector_num"]

    result = {
        "pointing": p,
        "detector": prod["detector"],
        "dither": prod["dither"],
        "filename": fname,
        "group": prod["group"],
        "dest_path": str(dest_path),
        "status": "PENDING",
        "size_bytes": 0,
        "sha256": "",
        "download_elapsed_sec": 0.0,
        "fits_valid": False,
        "wcs_valid": False,
        "variance_valid": False,
        "epsf_bins": 0,
        "obs_id": "",
        "exptime_sec": 0.0,
        "errors": []
    }

    # 1. Check if already exists in destination
    if dest_path.exists():
        v_res = ScientificFITSValidator.validate_file(str(dest_path), expected_pointing=p, expected_detector=det)
        sha = AtomicFileHandler.compute_sha256(str(dest_path))
        result.update({
            "status": "REUSED_ALREADY_VERIFIED" if v_res["is_valid"] else "REUSED_CORRUPT",
            "size_bytes": dest_path.stat().st_size,
            "sha256": sha,
            "fits_valid": v_res["is_valid"],
            "wcs_valid": v_res["wcs_valid"],
            "variance_valid": v_res["variance_valid"],
            "epsf_bins": v_res["epsf_bins"],
            "obs_id": v_res["obs_id"],
            "exptime_sec": v_res["exptime_sec"],
            "errors": v_res["errors"]
        })
        return result

    # 2. Download to staging
    t0 = time.time()
    req = urllib.request.Request(prod["url"], headers={"User-Agent": "SPECTRA-X/1.0"})
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            content_len = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            with open(staging_path, "wb") as f_out:
                while chunk := resp.read(1024 * 1024):
                    f_out.write(chunk)
                    h.update(chunk)
                    downloaded += len(chunk)
            
            if content_len > 0 and downloaded != content_len:
                raise IOError(f"Incomplete download: {downloaded} != {content_len} bytes")
                
            result["download_elapsed_sec"] = round(time.time() - t0, 2)
            result["size_bytes"] = downloaded
            result["sha256"] = h.hexdigest()

        # 3. Scientific FITS Validation on Staging File
        v_res = ScientificFITSValidator.validate_file(str(staging_path), expected_pointing=p, expected_detector=det)
        result["fits_valid"] = v_res["is_valid"]
        result["wcs_valid"] = v_res["wcs_valid"]
        result["variance_valid"] = v_res["variance_valid"]
        result["epsf_bins"] = v_res["epsf_bins"]
        result["obs_id"] = v_res["obs_id"]
        result["exptime_sec"] = v_res["exptime_sec"]
        result["errors"] = v_res["errors"]

        if not v_res["is_valid"]:
            result["status"] = "QUARANTINED_INVALID_FITS"
            # Move to quarantine
            quarantine_path = BASE_DIR / "quarantine" / fname
            quarantine_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(staging_path, quarantine_path)
            return result

        # 4. Atomic Promotion to destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(staging_path, dest_path)
        result["status"] = "DOWNLOADED_AND_VERIFIED"

    except Exception as e:
        result["status"] = "DOWNLOAD_FAILED"
        result["errors"].append(str(e))
        if staging_path.exists():
            try: staging_path.unlink()
            except Exception: pass

    return result

def main(max_workers: int = 8):
    print("=" * 70)
    print("SPECTRA-X / F1 — TASK 1.1M CONTROLLED MULTI-POINTING INGESTION")
    print(f"Target Cohort: {', '.join(TARGET_POINTINGS)} (120 files total)")
    print("=" * 70)

    # 1. Storage Safety Gate Check
    gate = StorageSafetyGate(target_path=".", min_margin_gb=5.0)
    allowed, free_gb, msg = gate.check_space(required_gb=7.5)
    print(f"Storage Gate: {msg}")
    if not allowed:
        print("ABORTING: Insufficient disk space.")
        sys.exit(1)

    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    for p in TARGET_POINTINGS:
        (LEVEL2_DIR / p).mkdir(parents=True, exist_ok=True)

    products = get_product_list()
    print(f"Total products to process: {len(products)}")

    # Execute concurrent ingestion
    results = []
    t_start = time.time()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(acquire_and_validate_one, prod): prod for prod in products}
        completed_count = 0
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            completed_count += 1
            status = res["status"]
            fname = res["filename"]
            sz_mb = res["size_bytes"] / (1024 * 1024)
            print(f"[{completed_count:3d}/120] {res['pointing']} {res['detector']} D{res['dither']}: {status} ({sz_mb:.1f} MB, {res['download_elapsed_sec']:.1f}s) - {fname}")

    total_elapsed = time.time() - t_start
    print(f"\nAll 120 products processed in {total_elapsed:.1f}s ({total_elapsed/60:.2f} min)")

    # Save validation matrix CSV
    df = pd.DataFrame(results)
    csv_out = Path("reports/ASTROVISION_TASK_1_1M_FITS_VALIDATION_MATRIX.csv")
    csv_out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_out, index=False)
    print(f"Saved validation matrix to {csv_out}")

    # Generate ingestion manifest JSON
    manifest = {
        "manifest_version": "1.0",
        "task_id": "SPECTRA-X_PHASE3_TASK_1.1M",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_cohort": TARGET_POINTINGS,
        "total_products": len(results),
        "summary_counts": {
            "REUSED_ALREADY_VERIFIED": sum(1 for r in results if r["status"] == "REUSED_ALREADY_VERIFIED"),
            "DOWNLOADED_AND_VERIFIED": sum(1 for r in results if r["status"] == "DOWNLOADED_AND_VERIFIED"),
            "QUARANTINED_INVALID_FITS": sum(1 for r in results if r["status"] == "QUARANTINED_INVALID_FITS"),
            "DOWNLOAD_FAILED": sum(1 for r in results if r["status"] == "DOWNLOAD_FAILED"),
        },
        "per_pointing_completeness": {},
        "products": results
    }

    for p in TARGET_POINTINGS:
        p_res = [r for r in results if r["pointing"] == p]
        verified_count = sum(1 for r in p_res if r["fits_valid"])
        manifest["per_pointing_completeness"][p] = {
            "total_expected": 24,
            "total_verified": verified_count,
            "complete": (verified_count == 24)
        }

    json_out = Path("reports/manifests/astrovision_multipointing_ingestion_manifest.json")
    with open(json_out, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"Saved manifest to {json_out}")

if __name__ == "__main__":
    main()
