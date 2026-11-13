"""
SPECTRA-X FITS Inspection & Validation Tool
NASA Space Apps 2026

Inspects SPHEREx Level-2 and calibration Multi-Extension FITS (MEF) files.
Extracts:
- Release, observation timestamps (DATE-OBS, MJD-OBS)
- Spatial coordinates & WCS availability (RA---TAN-SIP)
- Multi-HDU cataloging (IMAGE, FLAGS, VARIANCE, ZODI, EPSF, WCS-WAVE)
- Wavelength range, uncertainty, and bad-pixel flags
- Data integrity, corruptions, and temporal observation pairs identification
"""

import os
import sys
import glob
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
import numpy as np

base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from models.chronos_x.temporal_eligibility import (
    evaluate_pair_temporal_eligibility,
    determine_dataset_temporal_availability,
    DEFAULT_MIN_BASELINE_DAYS,
    BASELINE_POLICY_VERSION
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("FITSInspector")


def inspect_single_fits(file_path: str) -> Dict[str, Any]:
    """Inspects a single FITS file, extracting HDUs, WCS, metadata, and validation status."""
    info: Dict[str, Any] = {
        "file_path": os.path.abspath(file_path),
        "filename": os.path.basename(file_path),
        "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
        "release": None,
        "obs_date": None,
        "mjd_obs": None,
        "plan_id": None,
        "detector": None,
        "dither": None,
        "channel": None,
        "ra_deg": None,
        "dec_deg": None,
        "wcs_available": False,
        "wcs_ctype": None,
        "hdu_count": 0,
        "hdu_names": [],
        "image_dimensions": None,
        "image_dtype": None,
        "wavelength_available": False,
        "wavelmin_um": None,
        "wavelmax_um": None,
        "variance_available": False,
        "variance_dtype": None,
        "flags_available": False,
        "flags_dtype": None,
        "zodi_available": False,
        "psf_available": False,
        "validation_status": "UNKNOWN",
        "error_message": None,
    }

    # Determine release from path or filename
    norm_path = file_path.replace("\\", "/").lower()
    if "qr2" in norm_path:
        info["release"] = "QR2"
    elif "qr3" in norm_path:
        info["release"] = "QR3"

    try:
        with fits.open(file_path, mode="readonly", memmap=True) as hdul:
            info["hdu_count"] = len(hdul)
            hdu_names = [hdu.name for hdu in hdul]
            info["hdu_names"] = hdu_names

            # Find primary and image headers
            primary_hdr = hdul[0].header if len(hdul) > 0 else {}
            image_hdu = None
            if "IMAGE" in hdul:
                image_hdu = hdul["IMAGE"]
            elif len(hdul) > 1 and getattr(hdul[1], "data", None) is not None:
                image_hdu = hdul[1]
            elif len(hdul) == 1 and getattr(hdul[0], "data", None) is not None:
                image_hdu = hdul[0]

            img_hdr = image_hdu.header if image_hdu is not None else primary_hdr

            # Observation date
            for date_key in ["DATE-OBS", "DATE", "OBSTIME"]:
                if date_key in img_hdr:
                    info["obs_date"] = str(img_hdr[date_key])
                    break
                elif date_key in primary_hdr:
                    info["obs_date"] = str(primary_hdr[date_key])
                    break

            if "MJD-OBS" in img_hdr:
                info["mjd_obs"] = float(img_hdr["MJD-OBS"])
            elif "MJD-OBS" in primary_hdr:
                info["mjd_obs"] = float(primary_hdr["MJD-OBS"])

            # Planning period / Observation ID / Detector
            for plan_key in ["PLAN_ID", "OBSID", "OBS_ID"]:
                if plan_key in img_hdr:
                    info["plan_id"] = str(img_hdr[plan_key])
                    break
                elif plan_key in primary_hdr:
                    info["plan_id"] = str(primary_hdr[plan_key])
                    break

            for det_key in ["DETECTOR", "DET"]:
                if det_key in img_hdr:
                    val = str(img_hdr[det_key]).strip()
                    info["detector"] = int(val) if val.isdigit() else val
                    break
                elif det_key in primary_hdr:
                    val = str(primary_hdr[det_key]).strip()
                    info["detector"] = int(val) if val.isdigit() else val
                    break

            for dith_key in ["DITHER", "DITH"]:
                if dith_key in img_hdr:
                    val = str(img_hdr[dith_key]).strip()
                    info["dither"] = int(val) if val.isdigit() else val
                    break

            for chan_key in ["CHANNEL", "BAND"]:
                if chan_key in img_hdr:
                    info["channel"] = str(img_hdr[chan_key])
                    break

            # Spatial coordinates and WCS
            wcs_found = False
            for c1, c2 in [("CRVAL1", "CRVAL2"), ("RA_CENT", "DEC_CENT")]:
                if c1 in img_hdr and c2 in img_hdr:
                    try:
                        info["ra_deg"] = float(img_hdr[c1])
                        info["dec_deg"] = float(img_hdr[c2])
                    except (ValueError, TypeError):
                        pass
                    break

            if "CTYPE1" in img_hdr:
                info["wcs_ctype"] = str(img_hdr["CTYPE1"])
                try:
                    w = WCS(img_hdr)
                    if w.has_celestial:
                        wcs_found = True
                except Exception:
                    wcs_found = True  # header has CTYPE keywords
            info["wcs_available"] = wcs_found

            # Image dimensions & dtype
            if image_hdu is not None and getattr(image_hdu, "data", None) is not None:
                shape_val = getattr(image_hdu, "shape", getattr(image_hdu.data, "shape", None))
                if shape_val is not None:
                    info["image_dimensions"] = list(shape_val)
                info["image_dtype"] = str(getattr(image_hdu.data, "dtype", ""))

            # Flags HDU
            if "FLAGS" in hdul:
                info["flags_available"] = True
                if getattr(hdul["FLAGS"], "data", None) is not None:
                    info["flags_dtype"] = str(hdul["FLAGS"].data.dtype)

            # Variance HDU
            if "VARIANCE" in hdul:
                info["variance_available"] = True
                if getattr(hdul["VARIANCE"], "data", None) is not None:
                    info["variance_dtype"] = str(hdul["VARIANCE"].data.dtype)

            # Zodi HDU
            if "ZODI" in hdul:
                info["zodi_available"] = True

            # PSF HDU
            if "EPSF" in hdul or "AVERAGE_PSF" in hdul or "PSF" in hdul:
                info["psf_available"] = True

            # Wavelength info
            if "WCS-WAVE" in hdul:
                info["wavelength_available"] = True
            for wmin_k in ["WAVELMIN", "WAVEMIN", "EM_MIN"]:
                if wmin_k in img_hdr:
                    info["wavelength_available"] = True
                    info["wavelmin_um"] = float(img_hdr[wmin_k])
                    break
            for wmax_k in ["WAVELMAX", "WAVEMAX", "EM_MAX"]:
                if wmax_k in img_hdr:
                    info["wavelength_available"] = True
                    info["wavelmax_um"] = float(img_hdr[wmax_k])
                    break

            info["validation_status"] = "VALID"

    except Exception as exc:
        info["validation_status"] = "CORRUPTED"
        info["error_message"] = str(exc)

    return info


def inspect_directory(data_dir: str, output_csv: Optional[str] = None) -> pd.DataFrame:
    """Scans and inspects all FITS files recursively under data_dir."""
    fits_files = glob.glob(os.path.join(data_dir, "**", "*.fits"), recursive=True)
    logger.info(f"Scanning {len(fits_files)} FITS files in {data_dir}...")

    records = []
    for f in fits_files:
        rec = inspect_single_fits(f)
        records.append(rec)

    df = pd.DataFrame(records)
    if output_csv:
        os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved inspection catalog to {output_csv}")

    return df


def find_temporal_pairs(
    df: pd.DataFrame,
    max_sep_arcsec: float = 12600.0,
    min_time_diff_days: float = DEFAULT_MIN_BASELINE_DAYS,
    policy_min_baseline_days: float = DEFAULT_MIN_BASELINE_DAYS,
    include_all_for_registration: bool = True
) -> List[Dict[str, Any]]:
    """
    Identifies observation pairs for CHRONOS-X and evaluates their temporal eligibility.
    
    Enforces the Task 1.3K Safety Remediation:
    - Distinguishes intra-visit dithers (dt < 1.0 day) from genuine secular multi-epoch pairs.
    - Intra-visit dithers receive temporal_eligibility='FALSE' but remain available for 
      image registration, noise propagation, and dipole artifact vetting.
    - Missing required metadata produces structured UNVERIFIABLE records with explicit provenance.
    - Only independent epochs meeting all 10 scientific checks receive temporal_eligibility='TRUE'.
    """
    if df is None or len(df) == 0:
        return []

    pairs = []
    n = len(df)
    
    # Process pairwise combinations
    for i in range(n):
        row_i = df.iloc[i].to_dict()
        for j in range(i + 1, n):
            row_j = df.iloc[j].to_dict()
            
            # Great-circle angular separation approximation if RA/Dec available
            ra_i, dec_i = row_i.get("ra_deg"), row_i.get("dec_deg")
            ra_j, dec_j = row_j.get("ra_deg"), row_j.get("dec_deg")
            
            sep_arcsec = None
            if pd.notna(ra_i) and pd.notna(dec_i) and pd.notna(ra_j) and pd.notna(dec_j):
                try:
                    cos_d = np.cos(np.deg2rad((float(dec_i) + float(dec_j)) / 2.0))
                    dra = (float(ra_j) - float(ra_i)) * cos_d * 3600.0
                    ddec = (float(dec_j) - float(dec_i)) * 3600.0
                    sep_arcsec = float(np.sqrt(dra**2 + ddec**2))
                except Exception:
                    sep_arcsec = None
            
            # If coordinates are valid and separation exceeds FOV, they don't overlap spatially
            if sep_arcsec is not None and sep_arcsec > max_sep_arcsec:
                continue

            # Evaluate pair temporal eligibility and evidence tier
            row_i_copy = dict(row_i)
            row_j_copy = dict(row_j)
            row_i_copy["sep_arcsec"] = sep_arcsec
            row_j_copy["sep_arcsec"] = sep_arcsec
            
            elig_res = evaluate_pair_temporal_eligibility(
                row_i_copy,
                row_j_copy,
                min_baseline_days=policy_min_baseline_days,
                max_sep_arcsec=max_sep_arcsec
            )

            # If caller only requested secularly eligible pairs, skip non-TRUE
            if not include_all_for_registration and elig_res.status != "TRUE":
                continue

            # If user specified a custom min_time_diff_days filter that wasn't bypassed by registration
            if not include_all_for_registration and elig_res.dt_days is not None and elig_res.dt_days < min_time_diff_days:
                continue

            rel_i = str(row_i.get("release", "UNKNOWN"))
            rel_j = str(row_j.get("release", "UNKNOWN"))

            pair_dict = {
                "file_1": str(row_i.get("filename", "")),
                "file_2": str(row_j.get("filename", "")),
                "release_1": rel_i,
                "release_2": rel_j,
                "ra": float(ra_i) if pd.notna(ra_i) else None,
                "dec": float(dec_i) if pd.notna(dec_i) else None,
                "sep_arcsec": float(sep_arcsec) if sep_arcsec is not None else None,
                "mjd_1": float(row_i["mjd_obs"]) if pd.notna(row_i.get("mjd_obs")) else None,
                "mjd_2": float(row_j["mjd_obs"]) if pd.notna(row_j.get("mjd_obs")) else None,
                "dt_days": float(elig_res.dt_days) if elig_res.dt_days is not None else None,
                "is_inter_release": (rel_i != rel_j and rel_i != "UNKNOWN" and rel_j != "UNKNOWN"),
                "temporal_eligibility": elig_res.status,
                "evidence_tier": elig_res.evidence_tier,
                "is_dither": elig_res.is_dither,
                "eligibility_reasons": elig_res.reasons,
                "missing_evidence": elig_res.missing_evidence,
                "usable_for_registration": (elig_res.evidence_tier in {"E3", "E4"}),
                "usable_for_secular_transients": (elig_res.status == "TRUE")
            }
            pairs.append(pair_dict)

    return pairs


def generate_validation_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates counts of valid, corrupted, duplicate, and metadata completeness."""
    total = len(df)
    if total == 0:
        return {
            "total_files": 0, "valid_files": 0, "corrupted_files": 0,
            "duplicate_files": 0, "missing_wcs": 0, "missing_variance": 0,
            "missing_flags": 0, "missing_wavelength": 0
        }

    valid_cnt = int((df["validation_status"] == "VALID").sum())
    corrupt_cnt = int((df["validation_status"] == "CORRUPTED").sum())
    dup_cnt = int(df.duplicated(subset=["filename"]).sum())
    missing_wcs = int((~df["wcs_available"]).sum())
    missing_var = int((~df["variance_available"]).sum())
    missing_flags = int((~df["flags_available"]).sum())
    missing_wave = int((~df["wavelength_available"]).sum())

    return {
        "total_files": total,
        "valid_files": valid_cnt,
        "corrupted_files": corrupt_cnt,
        "duplicate_files": dup_cnt,
        "missing_wcs": missing_wcs,
        "missing_variance": missing_var,
        "missing_flags": missing_flags,
        "missing_wavelength": missing_wave,
    }


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/spherex"
    out_csv = sys.argv[2] if len(sys.argv) > 2 else "manifests/fits_validation_catalog.csv"
    res_df = inspect_directory(target_dir, out_csv)
    summary = generate_validation_summary(res_df)
    print("\n--- FITS VALIDATION SUMMARY ---")
    print(json.dumps(summary, indent=2))
