"""
SPECTRA-X / F1 — Phase 3, Task 1.1K
Multi-Pointing SPHEREx Data Acquisition & Controlled Ingestion Pilot Engine

Implements Stages A-D:
- Stage A: Independent Archive Verification
- Storage Safety Gate: Disk space evaluation and safe abort
- Stage B: Atomic Download & Integrity Verification (.part staging, SHA-256)
- Stage C: Product Completeness Audit (classification of expected products)
- Stage D: Scientific FITS Validation (Astropy HDU, WCS, Variance, Flags, ePSF)
"""

import os
import sys
import json
import shutil
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

class StorageSafetyGate:
    """Enforces disk space headroom requirements before acquisition."""
    def __init__(self, target_path: str = ".", min_margin_gb: float = 5.0):
        self.target_path = target_path
        self.min_margin_gb = min_margin_gb

    def check_space(self, required_gb: float) -> Tuple[bool, float, str]:
        total, used, free = shutil.disk_usage(self.target_path)
        free_gb = free / (1024**3)
        needed_gb = required_gb + self.min_margin_gb
        if free_gb < needed_gb:
            msg = (f"ABORT: Insufficient disk space. Required: {required_gb:.2f} GB + "
                   f"{self.min_margin_gb:.2f} GB margin ({needed_gb:.2f} GB total), "
                   f"Available: {free_gb:.2f} GB.")
            return False, free_gb, msg
        return True, free_gb, f"OK: Available {free_gb:.2f} GB >= Needed {needed_gb:.2f} GB"


class ScientificFITSValidator:
    """Performs deep scientific inspection of Level-2 SPHEREx FITS products."""
    REQUIRED_HDUS = ["PRIMARY", "IMAGE", "FLAGS", "VARIANCE", "ZODI", "EPSF", "WCS-WAVE"]
    EXPECTED_SHAPE = (2040, 2040)
    EXPECTED_PIXEL_SCALE = 6.16  # arcsec/pixel

    @classmethod
    def validate_file(cls, filepath: str, expected_pointing: Optional[str] = None, expected_detector: Optional[int] = None) -> Dict[str, Any]:
        report = {
            "filepath": str(filepath),
            "filename": os.path.basename(filepath),
            "is_valid": False,
            "hdus_present": [],
            "missing_hdus": [],
            "obs_id": None,
            "detector_id": None,
            "exptime_sec": None,
            "wcs_valid": False,
            "variance_valid": False,
            "epsf_bins": 0,
            "errors": []
        }

        if not os.path.exists(filepath):
            report["errors"].append(f"File not found: {filepath}")
            return report

        try:
            with fits.open(filepath, memmap=True) as hdul:
                report["hdus_present"] = [h.name for h in hdul]
                for req in cls.REQUIRED_HDUS:
                    if req not in hdul:
                        report["missing_hdus"].append(req)

                if report["missing_hdus"]:
                    report["errors"].append(f"Missing required HDUs: {report['missing_hdus']}")

                # Primary Header
                pri_hdr = hdul[0].header

                # Image HDU
                if "IMAGE" in hdul:
                    img_hdu = hdul["IMAGE"]
                    img_hdr = img_hdu.header
                    img_data = img_hdu.data

                    # Dimensions
                    if img_data is not None:
                        if img_data.shape != cls.EXPECTED_SHAPE:
                            report["errors"].append(f"Unexpected image shape: {img_data.shape} != {cls.EXPECTED_SHAPE}")
                        if not np.isfinite(img_data).any():
                            report["errors"].append("Image array contains zero finite values.")

                    # Metadata
                    det = img_hdr.get("DETECTOR")
                    report["detector_id"] = det
                    obsid = img_hdr.get("OBSID", pri_hdr.get("OBSID", "UNKNOWN"))
                    report["obs_id"] = obsid
                    exptime = img_hdr.get("TSAMP", img_hdr.get("EXPTIME", pri_hdr.get("EXPTIME", 115.118)))
                    report["exptime_sec"] = float(exptime) if exptime is not None else None

                    # Expected checks
                    if expected_pointing and expected_pointing not in str(obsid):
                        report["errors"].append(f"Pointing mismatch: expected {expected_pointing} in OBSID {obsid}")
                    if expected_detector and det != expected_detector:
                        report["errors"].append(f"Detector mismatch: expected {expected_detector}, found {det}")

                    # WCS Validation
                    try:
                        w = WCS(img_hdr)
                        if w.is_celestial:
                            report["wcs_valid"] = True
                        else:
                            report["errors"].append("WCS is not celestial.")
                    except Exception as e:
                        report["errors"].append(f"WCS parsing error: {e}")

                # Variance HDU
                if "VARIANCE" in hdul:
                    var_data = hdul["VARIANCE"].data
                    if var_data is not None:
                        # Check finite and non-negative
                        finite_mask = np.isfinite(var_data)
                        if not finite_mask.any():
                            report["errors"].append("Variance array contains zero finite values.")
                        else:
                            finite_vals = var_data[finite_mask]
                            if np.any(finite_vals < 0):
                                report["errors"].append("Variance array contains negative values.")
                            else:
                                report["variance_valid"] = True
                    else:
                        report["errors"].append("Variance HDU data is None.")

                # EPSF HDU
                if "EPSF" in hdul:
                    epsf_data = hdul["EPSF"].data
                    if epsf_data is not None:
                        report["epsf_bins"] = epsf_data.shape[0] if len(epsf_data.shape) > 0 else 0
                    else:
                        report["errors"].append("EPSF data is None.")

                # Overall validity
                if not report["errors"] and not report["missing_hdus"] and report["wcs_valid"] and report["variance_valid"]:
                    report["is_valid"] = True

        except Exception as e:
            report["errors"].append(f"FITS file corruption/read failure: {e}")

        return report


class AtomicFileHandler:
    """Handles atomic staging, verification, and promotion of ingested files."""
    @staticmethod
    def compute_sha256(filepath: str) -> str:
        h = hashlib.sha256()
        with open(filepath, "rb") as f:
            while chunk := f.read(1024 * 1024):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def promote_from_staging(staging_path: str, dest_path: str, expected_sha256: Optional[str] = None) -> Tuple[bool, str, str]:
        if not os.path.exists(staging_path):
            return False, "", f"Staging file not found: {staging_path}"

        actual_sha = AtomicFileHandler.compute_sha256(staging_path)
        if expected_sha256 and actual_sha.lower() != expected_sha256.lower():
            os.remove(staging_path)
            return False, actual_sha, f"Checksum mismatch: expected {expected_sha256}, got {actual_sha}"

        # Prevent silent overwrite if dest already exists with different content
        if os.path.exists(dest_path):
            existing_sha = AtomicFileHandler.compute_sha256(dest_path)
            if existing_sha == actual_sha:
                os.remove(staging_path)
                return True, actual_sha, "File already exists and is identical (no overwrite needed)."
            else:
                return False, actual_sha, f"Destination {dest_path} exists with differing SHA {existing_sha}; overwrite blocked."

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(staging_path, dest_path)
        return True, actual_sha, "Promoted successfully."

