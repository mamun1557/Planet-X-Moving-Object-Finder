"""
SPECTRA-X Download Verification Tool
NASA Space Apps 2026

Verifies:
- File presence and non-zero size
- Exact byte count match against remote Content-Length
- FITS file readability and header integrity using Astropy
- Checksum validation where available
- Manifest synchronization
"""

import os
import sys
import hashlib
import logging
from typing import Dict, Any, List
import pandas as pd
from astropy.io import fits

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("VerifyDownloads")


def calculate_md5(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    """Calculates MD5 hex digest of a local file."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file(file_path: str, expected_size: int = None, expected_etag: str = None) -> Dict[str, Any]:
    """Validates a single downloaded file."""
    res = {
        "file_path": file_path,
        "exists": False,
        "size_bytes": 0,
        "size_matches": True,
        "is_fits": file_path.lower().endswith(".fits"),
        "fits_valid": None,
        "md5_matches": None,
        "status": "MISSING",
        "error": None
    }

    if not os.path.exists(file_path):
        res["error"] = "File does not exist on disk"
        return res

    res["exists"] = True
    actual_size = os.path.getsize(file_path)
    res["size_bytes"] = actual_size

    if actual_size == 0:
        res["status"] = "ZERO_BYTES"
        res["error"] = "File is zero bytes"
        return res

    if expected_size is not None and expected_size > 0:
        if actual_size != expected_size:
            res["size_matches"] = False
            res["status"] = "SIZE_MISMATCH"
            res["error"] = f"Expected {expected_size} bytes, got {actual_size} bytes"
            return res

    # Check FITS validity
    if res["is_fits"]:
        try:
            with fits.open(file_path, mode="readonly", checksum=False) as hdul:
                hdul.verify("silentfix")
                res["fits_valid"] = True
        except Exception as exc:
            res["fits_valid"] = False
            res["status"] = "CORRUPTED_FITS"
            res["error"] = str(exc)
            return res

    # Check ETag / MD5 (if standard 32-char hex MD5)
    if expected_etag:
        clean_etag = expected_etag.strip('"')
        if len(clean_etag) == 32 and "-" not in clean_etag:
            actual_md5 = calculate_md5(file_path)
            res["md5_matches"] = (actual_md5.lower() == clean_etag.lower())
            if not res["md5_matches"]:
                res["status"] = "CHECKSUM_MISMATCH"
                res["error"] = f"Expected MD5 {clean_etag}, got {actual_md5}"
                return res

    res["status"] = "VALID"
    return res


def verify_manifest(manifest_path: str) -> pd.DataFrame:
    """Verifies all files listed in a given manifest CSV."""
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest not found: {manifest_path}")
        return pd.DataFrame()

    df = pd.read_csv(manifest_path)
    if df.empty:
        return df

    results = []
    path_col = "local_path" if "local_path" in df.columns else "file_path"
    size_col = "size_bytes" if "size_bytes" in df.columns else None
    etag_col = "etag" if "etag" in df.columns else None

    for _, row in df.iterrows():
        lp = row.get(path_col)
        sz = row.get(size_col) if size_col else None
        et = row.get(etag_col) if etag_col else None
        sz = int(sz) if pd.notna(sz) and str(sz).isdigit() else None
        et = str(et) if pd.notna(et) else None

        v = verify_file(lp, sz, et)
        results.append(v["status"])

    df["verification_result"] = results
    df.to_csv(manifest_path, index=False)
    return df


def verify_all():
    """Runs verification across all manifests."""
    manifests = [
        "manifests/qr2_manifest.csv",
        "manifests/qr3_manifest.csv",
        "manifests/calibration_manifest.csv",
        "manifests/external_manifest.csv"
    ]
    print("=" * 60)
    print(" SPECTRA-X VERIFICATION AUDIT")
    print("=" * 60)
    total_files = 0
    total_valid = 0
    total_failed = 0

    for m in manifests:
        if os.path.exists(m):
            df = verify_manifest(m)
            cnt = len(df)
            valid = (df["verification_result"] == "VALID").sum() if "verification_result" in df.columns else 0
            failed = cnt - valid
            total_files += cnt
            total_valid += valid
            total_failed += failed
            print(f"{os.path.basename(m):<28} | Files: {cnt:<5} | Valid: {valid:<5} | Issues: {failed:<5}")

    print("-" * 60)
    print(f"TOTAL AUDITED: {total_files} | VALID: {total_valid} | ISSUES: {total_failed}")
    print("=" * 60)


if __name__ == "__main__":
    verify_all()
