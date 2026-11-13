"""
SPECTRA-X Storage Utilization & Audit Report
NASA Space Apps 2026

Calculates:
- Drive capacity and free space
- Downloaded data by category and release
- Storage budget tracking against 180 GB default limit
- Detailed breakdown per model readiness
"""

import os
import sys
import shutil
import glob
from typing import Dict, Any
import pandas as pd


def get_disk_storage(path: str = ".") -> Dict[str, float]:
    """Returns total, used, and free disk space in GB for the partition containing path."""
    total, used, free = shutil.disk_usage(os.path.abspath(path))
    return {
        "total_gb": round(total / (1024**3), 2),
        "used_gb": round(used / (1024**3), 2),
        "free_gb": round(free / (1024**3), 2),
    }


def get_dir_size_and_count(dir_path: str) -> Dict[str, Any]:
    """Calculates total size in bytes, MB, GB, and file count for a directory."""
    if not os.path.exists(dir_path):
        return {"count": 0, "size_bytes": 0, "size_mb": 0.0, "size_gb": 0.0}

    total_bytes = 0
    file_count = 0
    for root, _, files in os.walk(dir_path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(fp)
                file_count += 1
            except OSError:
                pass

    return {
        "count": file_count,
        "size_bytes": total_bytes,
        "size_mb": round(total_bytes / (1024**2), 2),
        "size_gb": round(total_bytes / (1024**3), 3),
    }


def generate_storage_report(budget_gb: float = 180.0) -> Dict[str, Any]:
    """Generates a complete storage audit across the project directory."""
    disk = get_disk_storage(".")
    categories = {
        "QR2 Level-2": "data/spherex/qr2/level2",
        "QR2 Calibration": "data/spherex/qr2/calibration",
        "QR2 Templates": "data/spherex/qr2/templates",
        "QR3 Level-2": "data/spherex/qr3/level2",
        "QR3 Calibration": "data/spherex/qr3/calibration",
        "QR3 Templates": "data/spherex/qr3/templates",
        "QR2 Deep": "data/spherex/qr2_deep",
        "QR3 Deep": "data/spherex/qr3_deep",
        "Gaia DR3": "data/external/gaia_dr3",
        "Minor Planets": "data/external/minor_planets",
        "JPL Horizons": "data/external/jpl_horizons",
        "Transient Catalogs": "data/external/transient_catalogs",
        "Processed Data": "data/processed",
        "Manifests": "manifests",
    }

    report: Dict[str, Any] = {
        "disk": disk,
        "storage_budget_gb": budget_gb,
        "categories": {},
        "total_downloaded_gb": 0.0,
        "total_downloaded_bytes": 0,
        "total_files": 0,
        "budget_remaining_gb": budget_gb,
        "budget_utilization_pct": 0.0,
    }

    tot_bytes = 0
    tot_files = 0
    for cat_name, cat_path in categories.items():
        stat = get_dir_size_and_count(cat_path)
        report["categories"][cat_name] = stat
        tot_bytes += stat["size_bytes"]
        tot_files += stat["count"]

    report["total_downloaded_bytes"] = tot_bytes
    report["total_downloaded_gb"] = round(tot_bytes / (1024**3), 3)
    report["total_files"] = tot_files
    report["budget_remaining_gb"] = max(0.0, round(budget_gb - report["total_downloaded_gb"], 3))
    report["budget_utilization_pct"] = round((report["total_downloaded_gb"] / budget_gb) * 100.0, 2)

    return report


def print_storage_report(budget_gb: float = 180.0):
    rep = generate_storage_report(budget_gb)
    disk = rep["disk"]
    print("=" * 60)
    print(" SPECTRA-X STORAGE AUDIT & BUDGET REPORT")
    print("=" * 60)
    print(f"Drive Free Space      : {disk['free_gb']} GB (out of {disk['total_gb']} GB total)")
    print(f"Configured Budget     : {rep['storage_budget_gb']} GB")
    print(f"Total Downloaded Data : {rep['total_downloaded_gb']} GB ({rep['total_files']} files)")
    print(f"Remaining Budget Space: {rep['budget_remaining_gb']} GB")
    print(f"Budget Utilization    : {rep['budget_utilization_pct']} %")
    print("-" * 60)
    print(f"{'Category':<22} | {'Files':<6} | {'Size (MB)':<12} | {'Size (GB)':<10}")
    print("-" * 60)
    for cat, stat in rep["categories"].items():
        print(f"{cat:<22} | {stat['count']:<6} | {stat['size_mb']:<12.2f} | {stat['size_gb']:<10.3f}")
    print("=" * 60)


if __name__ == "__main__":
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 180.0
    print_storage_report(budget)
