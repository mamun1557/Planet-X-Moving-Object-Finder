"""
SPECTRA-X Manifest Generator
NASA Space Apps 2026

Generates and updates standardized CSV manifests for all mission data:
- spherex_inventory.csv (comprehensive inventory of all discovered remote files)
- download_plan.csv (selected files prioritized for download within storage budget)
- qr2_manifest.csv (all downloaded QR2 data products)
- qr3_manifest.csv (all downloaded QR3 data products)
- calibration_manifest.csv (all calibration matrices, noise parameters, templates)
- external_manifest.csv (Gaia DR3, JPL Horizons, JPL SBDB, ZTF BTS transient data)
- download_log.csv (history of downloads, byte counts, checksums, statuses)
"""

import os
import sys
import csv
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ManifestGenerator")

MANIFEST_DIR = "manifests"


def init_manifests():
    """Initializes empty manifest CSV files with correct schema headers if not present."""
    os.makedirs(MANIFEST_DIR, exist_ok=True)

    manifest_schemas = {
        "spherex_inventory.csv": [
            "key", "filename", "release", "product_category", "planning_period",
            "detector", "size_bytes", "size_mb", "etag", "remote_url", "discovery_time"
        ],
        "download_plan.csv": [
            "key", "filename", "release", "priority", "product_category",
            "local_path", "size_bytes", "size_mb", "remote_url", "rationale"
        ],
        "qr2_manifest.csv": [
            "filename", "product_category", "local_path", "size_bytes",
            "etag", "download_timestamp", "status", "validation_status"
        ],
        "qr3_manifest.csv": [
            "filename", "product_category", "local_path", "size_bytes",
            "etag", "download_timestamp", "status", "validation_status"
        ],
        "calibration_manifest.csv": [
            "filename", "release", "calibration_type", "detector", "local_path",
            "size_bytes", "download_timestamp", "validation_status"
        ],
        "external_manifest.csv": [
            "dataset_name", "category", "target_object_or_field", "source_url",
            "local_path", "record_count", "size_bytes", "query_timestamp", "parameters"
        ],
        "download_log.csv": [
            "timestamp", "filename", "category", "remote_url", "local_path",
            "bytes_downloaded", "status", "duration_seconds", "error_message"
        ],
    }

    for fname, cols in manifest_schemas.items():
        path = os.path.join(MANIFEST_DIR, fname)
        if not os.path.exists(path):
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(cols)
            logger.info(f"Initialized manifest: {path}")


def append_to_manifest(manifest_name: str, rows: List[Dict[str, Any]]):
    """Appends records to a manifest CSV file."""
    path = os.path.join(MANIFEST_DIR, manifest_name)
    if not rows:
        return
    df_new = pd.DataFrame(rows)
    if os.path.exists(path):
        df_existing = pd.read_csv(path)
        combined = pd.concat([df_existing, df_new], ignore_index=True)
        # Deduplicate by key or filename if column exists
        dedup_col = "key" if "key" in combined.columns else ("filename" if "filename" in combined.columns else None)
        if dedup_col:
            combined = combined.drop_duplicates(subset=[dedup_col], keep="last")
        combined.to_csv(path, index=False)
    else:
        df_new.to_csv(path, index=False)


def log_download_event(filename: str, category: str, remote_url: str, local_path: str,
                       bytes_downloaded: int, status: str, duration_sec: float = 0.0,
                       error_msg: Optional[str] = None):
    """Appends an event to manifests/download_log.csv."""
    path = os.path.join(MANIFEST_DIR, "download_log.csv")
    row = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "filename": filename,
        "category": category,
        "remote_url": remote_url,
        "local_path": local_path,
        "bytes_downloaded": bytes_downloaded,
        "status": status,
        "duration_seconds": round(duration_sec, 2),
        "error_message": error_msg or ""
    }
    file_exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "timestamp", "filename", "category", "remote_url", "local_path",
            "bytes_downloaded", "status", "duration_seconds", "error_message"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


if __name__ == "__main__":
    init_manifests()
    print("Manifest initialization complete.")
