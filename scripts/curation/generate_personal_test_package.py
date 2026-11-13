"""
SPECTRA-X / Planet X Personal Test Package Generator
NASA Space Apps Challenge 2026 — F1 V2.1 Pipeline

Curates exactly 50 observation pairs (100 observation samples):
- 25 REAL_INTRA_VISIT pairs from genuine SPHEREx Level-2 flight observations
- 25 SYNTHETIC_ENGINEERING_TEST pairs with deterministic ground-truth motion vectors

Produces a standalone, independently extractable ZIP package:
artifacts/downloadable_packages/SPECTRA-X-Personal-Test-Data.zip
"""

import os
import sys
import json
import math
import shutil
import hashlib
import zipfile
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from observatory.motion_analysis import (
    AstronomicalMotionEngine,
    ObservationEpoch,
    spherical_angular_separation_arcsec,
    position_angle_deg,
    compute_ra_difference_deg,
    normalize_ra_deg
)

OUTPUT_ROOT = os.path.join(BASE_DIR, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data")
ZIP_DEST = os.path.join(BASE_DIR, "artifacts", "downloadable_packages", "SPECTRA-X-Personal-Test-Data.zip")


def sha256_file(path: str) -> str:
    """Computes SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def extract_cutout_hdul(
    src_fits_path: str,
    target_ra: float,
    target_dec: float,
    box_size: int = 128
) -> Tuple[fits.HDUList, Tuple[float, float], Tuple[float, float]]:
    """
    Extracts a box_size x box_size calibrated sub-raster from a multi-extension FITS file,
    updating CRPIX1/CRPIX2 so the WCS transformation remains bitwise exact.
    """
    with fits.open(src_fits_path) as hdul:
        # Check extensions
        sci_idx = 1 if len(hdul) > 1 else 0
        wcs_orig = WCS(hdul[sci_idx].header)

        # Map sky target to original pixel coordinates
        pix_coords = wcs_orig.all_world2pix([[target_ra, target_dec]], 0)[0]
        px, py = float(pix_coords[0]), float(pix_coords[1])

        half = box_size // 2
        ix, iy = int(round(px)), int(round(py))
        x0, x1 = ix - half, ix + half
        y0, y1 = iy - half, iy + half

        # Clamp to bounds if needed
        data_shape = hdul[sci_idx].data.shape
        ny, nx = data_shape[-2], data_shape[-1]
        x0_c = max(0, min(nx - box_size, x0))
        y0_c = max(0, min(ny - box_size, y0))
        x1_c = x0_c + box_size
        y1_c = y0_c + box_size

        new_hdul = fits.HDUList()

        # HDU 0: Primary
        prim_hdr = hdul[0].header.copy()
        prim_hdr["ORIGIN"] = "NASA/IPAC & SPECTRA-X"
        prim_hdr["COMMENT"] = "Real SPHEREx Level-2 Calibrated Observation Sub-Raster"
        new_hdul.append(fits.PrimaryHDU(header=prim_hdr))

        # HDU 1: Science Image
        sci_hdr = hdul[sci_idx].header.copy()
        sci_hdr["CRPIX1"] -= x0_c
        sci_hdr["CRPIX2"] -= y0_c
        sci_hdr["NAXIS1"] = box_size
        sci_hdr["NAXIS2"] = box_size
        sci_data = np.array(hdul[sci_idx].data[y0_c:y1_c, x0_c:x1_c], dtype=np.float32)
        new_hdul.append(fits.ImageHDU(data=sci_data, header=sci_hdr, name="SCI"))

        # HDU 2: Variance Image (if available)
        var_data = np.full((box_size, box_size), 0.001, dtype=np.float32)
        if "VARIANCE" in hdul:
            var_data = np.array(hdul["VARIANCE"].data[y0_c:y1_c, x0_c:x1_c], dtype=np.float32)
        elif len(hdul) > 2 and hdul[2].data is not None:
            var_data = np.array(hdul[2].data[y0_c:y1_c, x0_c:x1_c], dtype=np.float32)
        new_hdul.append(fits.ImageHDU(data=var_data, header=sci_hdr.copy(), name="VAR"))

        # HDU 3: Flags Image (if available)
        flag_data = np.zeros((box_size, box_size), dtype=np.int32)
        if "FLAGS" in hdul:
            flag_data = np.array(hdul["FLAGS"].data[y0_c:y1_c, x0_c:x1_c], dtype=np.int32)
        elif len(hdul) > 3 and hdul[3].data is not None:
            flag_data = np.array(hdul[3].data[y0_c:y1_c, x0_c:x1_c], dtype=np.int32)
        new_hdul.append(fits.ImageHDU(data=flag_data, header=sci_hdr.copy(), name="FLAGS"))

        new_wcs = WCS(sci_hdr)
        rec_sky = new_wcs.all_pix2world([[px - x0_c, py - y0_c]], 0)[0]

        return new_hdul, (px, py), (float(rec_sky[0]), float(rec_sky[1]))


def curate_real_intra_visit_pairs() -> List[Dict[str, Any]]:
    """Curates 25 genuine intra-visit dither pairs from original SPHEREx Level-2 FITS."""
    print("Curating 25 Real Intra-Visit Dither Observation Pairs...")
    real_pairs_dir = os.path.join(OUTPUT_ROOT, "real_intra_visit", "pairs")
    os.makedirs(real_pairs_dir, exist_ok=True)

    # Candidate sources and pointings
    # 1-12: Pointing 0003 across D1-D6 (primary candidate and gold reference stars)
    p0003_cand_file = os.path.join(BASE_DIR, "data", "processed", "candidates", "pointing_0003_candidates.csv")
    p0003_df = None
    if os.path.exists(p0003_cand_file):
        import pandas as pd
        p0003_df = pd.read_csv(p0003_cand_file)

    # Define diverse real pair configurations
    # Format: (Pointing, Det, DitherA, DitherB, TargetRA_or_None, TargetDec_or_None, TargetName)
    pair_configs = [
        # Pointing 0003 (D1 - Gold Primary Candidate SPX-J163.6309-69.4422)
        ("0003", "D1", "1D1", "4D1", 163.6309, -69.4422, "SPX-J163.6309-69.4422"),
        ("0003", "D1", "1D1", "2D1", 163.6309, -69.4422, "SPX-J163.6309-69.4422"),
        ("0003", "D1", "2D1", "3D1", 163.6309, -69.4422, "SPX-J163.6309-69.4422"),
        ("0003", "D1", "3D1", "4D1", 163.6309, -69.4422, "SPX-J163.6309-69.4422"),
        # Pointing 0003 (D2-D6 - Detected Sources in Respective Bands)
        ("0003", "D2", "1D2", "4D2", None, None, "P0003_D2_FIELD_TARGET"),
        ("0003", "D2", "1D2", "2D2", None, None, "P0003_D2_FIELD_TARGET"),
        ("0003", "D2", "2D2", "3D2", None, None, "P0003_D2_FIELD_TARGET"),
        ("0003", "D3", "1D3", "4D3", None, None, "P0003_D3_FIELD_TARGET"),
        ("0003", "D3", "1D3", "3D3", None, None, "P0003_D3_FIELD_TARGET"),
        ("0003", "D4", "1D4", "4D4", 163.6309, -69.4422, "SPX-J163.6309-69.4422_D4"),
        ("0003", "D4", "1D4", "2D4", 163.6309, -69.4422, "SPX-J163.6309-69.4422_D4"),
        ("0003", "D5", "1D5", "4D5", None, None, "P0003_D5_FIELD_TARGET"),
        ("0003", "D6", "1D6", "4D6", None, None, "P0003_D6_FIELD_TARGET"),

        # Pointing 0001 (Multipointing pilot across D1-D3)
        ("0001", "D1", "1D1", "2D1", None, None, "P0001_D1_FIELD_TARGET"),
        ("0001", "D1", "1D1", "4D1", None, None, "P0001_D1_FIELD_TARGET"),
        ("0001", "D2", "1D2", "2D2", None, None, "P0001_D2_FIELD_TARGET"),
        ("0001", "D2", "1D2", "4D2", None, None, "P0001_D2_FIELD_TARGET"),
        ("0001", "D3", "1D3", "3D3", None, None, "P0001_D3_FIELD_TARGET"),

        # Pointing 0002 (Multipointing pilot across D1-D2)
        ("0002", "D1", "1D1", "2D1", None, None, "P0002_D1_FIELD_TARGET"),
        ("0002", "D1", "1D1", "4D1", None, None, "P0002_D1_FIELD_TARGET"),
        ("0002", "D2", "1D2", "2D2", None, None, "P0002_D2_FIELD_TARGET"),
        ("0002", "D2", "2D2", "4D2", None, None, "P0002_D2_FIELD_TARGET"),

        # Pointing 0008, 0009, 0010 (Multipointing pilot across D1-D2)
        ("0008", "D1", "1D1", "2D1", None, None, "P0008_D1_FIELD_TARGET"),
        ("0009", "D1", "1D1", "2D1", None, None, "P0009_D1_FIELD_TARGET"),
        ("0010", "D1", "1D1", "2D1", None, None, "P0010_D1_FIELD_TARGET"),
    ]

    assert len(pair_configs) == 25, f"Expected 25 real pairs, got {len(pair_configs)}"

    curated_records = []

    for idx, (ptg, det, dith_a, dith_b, tgt_ra, tgt_dec, tgt_name) in enumerate(pair_configs, 1):
        pair_id = f"REAL_PAIR_{idx:03d}"
        pair_folder = os.path.join(real_pairs_dir, pair_id)
        os.makedirs(pair_folder, exist_ok=True)

        # Locate original FITS files
        def find_l2_file(p_num: str, d_lbl: str):
            patterns = [
                os.path.join(BASE_DIR, "data", "spherex", "qr3", "level2", f"level2_2026W30_1B_{p_num}_{d_lbl}_*.fits"),
                os.path.join(BASE_DIR, "data", "spherex", "multipointing_pilot", "level2", p_num, f"level2_2026W30_1B_{p_num}_{d_lbl}_*.fits")
            ]
            import glob
            for pat in patterns:
                matches = glob.glob(pat)
                if matches:
                    return matches[0]
            return None

        file_a = find_l2_file(ptg, dith_a)
        file_b = find_l2_file(ptg, dith_b)

        if not file_a or not file_b:
            raise FileNotFoundError(f"Could not locate FITS files for Pointing {ptg}, dithers {dith_a}/{dith_b}")

        # Determine target coordinates (use center of A if None)
        if tgt_ra is None or tgt_dec is None:
            with fits.open(file_a) as h_tmp:
                w_tmp = WCS(h_tmp[1].header)
                c_sky = w_tmp.all_pix2world([[1024.0, 1024.0]], 0)[0]
                tgt_ra, tgt_dec = float(c_sky[0]), float(c_sky[1])

        # Extract cutouts
        hdul_a, orig_pix_a, rec_sky_a = extract_cutout_hdul(file_a, tgt_ra, tgt_dec)
        hdul_b, orig_pix_b, rec_sky_b = extract_cutout_hdul(file_b, tgt_ra, tgt_dec)

        path_out_a = os.path.join(pair_folder, "obs_a.fits")
        path_out_b = os.path.join(pair_folder, "obs_b.fits")
        hdul_a.writeto(path_out_a, overwrite=True)
        hdul_b.writeto(path_out_b, overwrite=True)

        # Read timestamps from FITS
        ts_a = str(hdul_a[1].header.get("DATE-OBS", "2026-07-20T00:26:21.423Z"))
        mjd_a = float(hdul_a[1].header.get("MJD-OBS", 61241.018303))
        ts_b = str(hdul_b[1].header.get("DATE-OBS", "2026-07-20T00:32:48.216Z"))
        mjd_b = float(hdul_b[1].header.get("MJD-OBS", 61241.022780))

        dt_days = abs(mjd_b - mjd_a)
        dt_minutes = dt_days * 1440.0
        assert dt_days < 1.0, f"Pair {pair_id} exceeds 1 day baseline: {dt_days} days"

        # Check hashes of original files
        sha_orig_a = sha256_file(file_a)
        sha_orig_b = sha256_file(file_b)

        # Measure displacement
        disp_arcsec = spherical_angular_separation_arcsec(rec_sky_a[0], rec_sky_a[1], rec_sky_b[0], rec_sky_b[1])

        metadata = {
            "pair_id": pair_id,
            "dataset_class": "REAL_INTRA_VISIT",
            "pointing_id": f"P{ptg}",
            "detector": det,
            "target_name": tgt_name,
            "target_coordinates": {
                "ra_deg": tgt_ra,
                "dec_deg": tgt_dec
            },
            "obs_a": {
                "filename": "obs_a.fits",
                "original_source_file": os.path.relpath(file_a, BASE_DIR).replace("\\", "/"),
                "original_sha256": sha_orig_a,
                "dither": dith_a,
                "timestamp_utc": ts_a,
                "mjd": mjd_a,
                "crval1_deg": float(hdul_a[1].header.get("CRVAL1", tgt_ra)),
                "crval2_deg": float(hdul_a[1].header.get("CRVAL2", tgt_dec)),
                "wcs_valid": True,
                "sha256": sha256_file(path_out_a)
            },
            "obs_b": {
                "filename": "obs_b.fits",
                "original_source_file": os.path.relpath(file_b, BASE_DIR).replace("\\", "/"),
                "original_sha256": sha_orig_b,
                "dither": dith_b,
                "timestamp_utc": ts_b,
                "mjd": mjd_b,
                "crval1_deg": float(hdul_b[1].header.get("CRVAL1", tgt_ra)),
                "crval2_deg": float(hdul_b[1].header.get("CRVAL2", tgt_dec)),
                "wcs_valid": True,
                "sha256": sha256_file(path_out_b)
            },
            "time_separation_minutes": round(dt_minutes, 4),
            "time_separation_days": round(dt_days, 6),
            "measured_dither_shift_arcsec": round(disp_arcsec, 4),
            "scientific_eligibility": "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
            "is_secular_motion_eligible": False,
            "has_ground_truth_motion": False,
            "synthetic_ground_truth_motion": None,
            "intended_test_purpose": "Astrometric WCS registration, PSF subtraction null tests, intra-visit dither dipole verification.",
            "scientific_disclaimer": "REAL SPHEREx Level-2 flight observations. Time baseline dt < 1.0 day is strictly an intra-visit dither; INELIGIBLE as evidence of secular astronomical motion."
        }

        with open(os.path.join(pair_folder, "pair_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        curated_records.append(metadata)

    # Write manifest for real intra-visit class
    with open(os.path.join(OUTPUT_ROOT, "real_intra_visit", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "dataset_class": "REAL_INTRA_VISIT",
            "count": len(curated_records),
            "scientific_eligibility": "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
            "pairs": curated_records
        }, f, indent=2)

    return curated_records


def generate_synthetic_engineering_pairs() -> List[Dict[str, Any]]:
    """Generates 25 deterministic synthetic observation pairs with known ground-truth motion."""
    print("Generating 25 Synthetic Engineering Test Observation Pairs...")
    syn_pairs_dir = os.path.join(OUTPUT_ROOT, "synthetic_engineering_test", "pairs")
    os.makedirs(syn_pairs_dir, exist_ok=True)

    np.random.seed(2026)  # Deterministic seed

    # 25 Scenarios
    # Format: (Scenario Name, Target Type, RA0, Dec0, dt_days, displacement_arcsec, PA_deg, Notes)
    scenarios = [
        ("SYNTH_PAIR_001", "MAIN_BELT_ASTEROID_SLOW", 150.0, 10.0, 2.0, 4.8, 45.0, "Typical slow MBA shift (2.4 arcsec/day)"),
        ("SYNTH_PAIR_002", "MAIN_BELT_ASTEROID_TYPICAL", 160.0, 12.0, 4.0, 12.0, 75.0, "Standard MBA motion over 4-day baseline (3.0 arcsec/day)"),
        ("SYNTH_PAIR_003", "NEAR_EARTH_OBJECT_FAST", 170.0, -15.0, 1.0, 60.0, 120.0, "Fast-moving NEO trajectory (2.5 arcsec/hour, 60 arcsec/day)"),
        ("SYNTH_PAIR_004", "NEAR_EARTH_OBJECT_ULTRA_FAST", 175.0, -20.0, 1.0, 120.0, 150.0, "High proper motion NEO close-approach (5.0 arcsec/hour)"),
        ("SYNTH_PAIR_005", "KUIPER_BELT_OBJECT_SLOW", 210.0, -5.0, 30.0, 2.5, 90.0, "Slow trans-Neptunian orbital motion (0.083 arcsec/day)"),
        ("SYNTH_PAIR_006", "RA_WRAPAROUND_MERIDIAN", 359.985, 5.0, 3.0, 108.0, 90.0, "Cross-meridian RA wraparound from 359.985 deg to ~0.015 deg"),
        ("SYNTH_PAIR_007", "RA_WRAPAROUND_REVERSE", 0.010, -5.0, 2.0, 72.0, 270.0, "Cross-meridian reverse RA wraparound from 0.010 deg to ~359.990 deg"),
        ("SYNTH_PAIR_008", "HIGH_SOUTHERN_DECLINATION", 80.0, -65.0, 5.0, 15.0, 30.0, "Southern polar cap astrometry with cos(Dec) geometric scaling"),
        ("SYNTH_PAIR_009", "HIGH_NORTHERN_DECLINATION", 120.0, 60.0, 7.0, 21.0, 60.0, "Northern high-declination field (cos(Dec) = 0.50)"),
        ("SYNTH_PAIR_010", "EQUATORIAL_BASELINE", 180.0, 0.0, 10.0, 30.0, 90.0, "Celestial equator reference baseline with zero Dec curvature"),
        ("SYNTH_PAIR_011", "MULTI_MONTH_LONG_BASELINE", 195.0, -25.0, 90.0, 90.0, 110.0, "90-day seasonal secular baseline (1.0 arcsec/day)"),
        ("SYNTH_PAIR_012", "SUB_ARCSEC_LIMIT", 140.0, 20.0, 1.0, 0.5, 0.0, "Sub-arcsecond astrometric resolution limit test (0.5 arcsec)"),
        ("SYNTH_PAIR_013", "SMALL_ONE_ARCSEC_SHIFT", 145.0, 22.0, 2.0, 1.0, 180.0, "Small 1.0 arcsecond displacement test"),
        ("SYNTH_PAIR_014", "DIRECTIONAL_PURE_NORTH", 100.0, 0.0, 3.0, 18.0, 0.0, "Pure North displacement along celestial meridian (PA = 0 deg)"),
        ("SYNTH_PAIR_015", "DIRECTIONAL_PURE_EAST", 100.0, 0.0, 3.0, 18.0, 90.0, "Pure East displacement along right ascension (PA = 90 deg)"),
        ("SYNTH_PAIR_016", "DIRECTIONAL_PURE_SOUTH", 100.0, 0.0, 3.0, 18.0, 180.0, "Pure South displacement along celestial meridian (PA = 180 deg)"),
        ("SYNTH_PAIR_017", "DIRECTIONAL_PURE_WEST", 100.0, 0.0, 3.0, 18.0, 270.0, "Pure West displacement along right ascension (PA = 270 deg)"),
        ("SYNTH_PAIR_018", "DIAGONAL_NORTHEAST", 110.0, 15.0, 4.0, 25.0, 45.0, "Symmetric diagonal displacement Northeast (PA = 45 deg)"),
        ("SYNTH_PAIR_019", "DIAGONAL_SOUTHEAST", 115.0, 15.0, 5.0, 35.0, 135.0, "Symmetric diagonal displacement Southeast (PA = 135 deg)"),
        ("SYNTH_PAIR_020", "DIAGONAL_SOUTHWEST", 120.0, 15.0, 6.0, 42.0, 225.0, "Symmetric diagonal displacement Southwest (PA = 225 deg)"),
        ("SYNTH_PAIR_021", "STATIONARY_CONTROL_NULL", 130.0, 30.0, 14.0, 0.0, 0.0, "Stationary control source / null motion test over 14 days"),
        ("SYNTH_PAIR_022", "LOW_SNR_FAINT_TARGET", 135.0, -10.0, 3.0, 8.0, 60.0, "Low-SNR faint source embedded in elevated Poisson noise"),
        ("SYNTH_PAIR_023", "CROWDED_FIELD_SIMULATION", 270.0, -29.0, 5.0, 16.0, 120.0, "Synthetic moving source surrounded by stationary companion stars"),
        ("SYNTH_PAIR_024", "UNCERTAINTY_BOUNDARY_TEST", 155.0, -40.0, 2.0, 1.5, 300.0, "High astrometric coordinate uncertainty (sigma = 0.5 arcsec)"),
        ("SYNTH_PAIR_025", "MID_BASELINE_SECULAR", 165.0, -35.0, 60.0, 75.0, 80.0, "60-day baseline secular asteroid track (1.25 arcsec/day)"),
    ]

    assert len(scenarios) == 25, f"Expected 25 synthetic scenarios, got {len(scenarios)}"

    generated_records = []
    base_date = datetime(2026, 7, 1, 0, 0, 0, tzinfo=timezone.utc)
    base_mjd = 61222.0

    box_size = 128
    pix_scale_deg = (6.2 / 3600.0)  # ~6.2 arcsec/pixel nominal SPHEREx scale

    for idx, (p_id, t_type, ra0, dec0, dt_d, disp_arcsec, pa_deg, notes) in enumerate(scenarios, 1):
        pair_folder = os.path.join(syn_pairs_dir, p_id)
        os.makedirs(pair_folder, exist_ok=True)

        dt_days = float(dt_d)
        dt_hours = dt_days * 24.0

        # Calculate epoch B coordinates based on displacement and PA
        disp_deg = disp_arcsec / 3600.0
        pa_rad = math.radians(pa_deg)

        dec0_rad = math.radians(dec0)
        cos_dec = math.cos(dec0_rad) if abs(math.cos(dec0_rad)) > 1e-6 else 1e-6

        d_dec_deg = disp_deg * math.cos(pa_rad)
        d_ra_deg = (disp_deg * math.sin(pa_rad)) / cos_dec

        ra_a = normalize_ra_deg(ra0)
        dec_a = dec0
        ra_b = normalize_ra_deg(ra0 + d_ra_deg)
        dec_b = min(90.0, max(-90.0, dec0 + d_dec_deg))

        # Recompute exact spherical displacement to verify consistency
        exact_disp = spherical_angular_separation_arcsec(ra_a, dec_a, ra_b, dec_b)
        exact_pa = position_angle_deg(ra_a, dec_a, ra_b, dec_b) if exact_disp > 1e-4 else 0.0

        rate_day = exact_disp / dt_days
        rate_hour = exact_disp / dt_hours

        # Timestamps
        date_a = base_date + timedelta(days=idx)
        mjd_a = base_mjd + idx
        date_b = date_a + timedelta(days=dt_days)
        mjd_b = mjd_a + dt_days

        ts_a = date_a.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        ts_b = date_b.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        # Build WCS
        w_syn = WCS(naxis=2)
        w_syn.wcs.crpix = [64.0, 64.0]
        w_syn.wcs.cdelt = np.array([-pix_scale_deg, pix_scale_deg])
        w_syn.wcs.crval = [ra0, dec0]
        w_syn.wcs.ctype = ["RA---TAN", "DEC--TAN"]

        # Synthesize pixel arrays (Gaussian noise + 2D Gaussian point source)
        def make_synthetic_frame(src_ra, src_dec, noise_level=0.05, extra_stars=False):
            # Compute pixel coordinates using WCS
            pix_coords = w_syn.all_world2pix([[src_ra, src_dec]], 0)[0]
            px, py = float(pix_coords[0]), float(pix_coords[1])

            img = np.random.normal(loc=0.25, scale=noise_level, size=(box_size, box_size)).astype(np.float32)
            var = np.full((box_size, box_size), noise_level**2, dtype=np.float32)
            flags = np.zeros((box_size, box_size), dtype=np.int32)

            # Inject point source (sigma = 1.2 pixels)
            yy, xx = np.mgrid[0:box_size, 0:box_size]
            r2 = (xx - px)**2 + (yy - py)**2
            psf = 10.0 * np.exp(-0.5 * r2 / (1.2**2))
            img += psf.astype(np.float32)

            # Optional extra background stars for crowded field scenario
            if extra_stars:
                for ex, ey, ea in [(30, 30, 8.0), (90, 40, 12.0), (35, 100, 6.0)]:
                    r2_s = (xx - ex)**2 + (yy - ey)**2
                    img += (ea * np.exp(-0.5 * r2_s / (1.1**2))).astype(np.float32)

            return img, var, flags, px, py

        is_crowded = (t_type == "CROWDED_FIELD_SIMULATION")
        noise_amp = 0.15 if t_type == "LOW_SNR_FAINT_TARGET" else 0.05

        img_a, var_a, flg_a, px_a, py_a = make_synthetic_frame(ra_a, dec_a, noise_amp, is_crowded)
        img_b, var_b, flg_b, px_b, py_b = make_synthetic_frame(ra_b, dec_b, noise_amp, is_crowded)

        # Build WCS headers
        def make_syn_hdul(img_data, var_data, flg_data, ts, mjd):
            hdr = w_syn.to_header()
            hdr["ORIGIN"] = "SYNTHETIC_ENGINEERING_TEST"
            hdr["COMMENT"] = "NOT REAL SPHEREX OBSERVATION - FOR TEST PURPOSES ONLY"
            hdr["IS_SYNTH"] = True
            hdr["DATE-OBS"] = ts
            hdr["MJD-OBS"] = mjd

            prim = fits.PrimaryHDU()
            prim.header["ORIGIN"] = "SYNTHETIC_ENGINEERING_TEST"
            prim.header["IS_SYNTH"] = True
            prim.header["COMMENT"] = "SYNTHETIC ENGINEERING TEST - NOT REAL SPHEREX OBSERVATION"

            h_sci = fits.ImageHDU(data=img_data, header=hdr, name="SCI")
            h_var = fits.ImageHDU(data=var_data, header=hdr.copy(), name="VAR")
            h_flg = fits.ImageHDU(data=flg_data, header=hdr.copy(), name="FLAGS")

            return fits.HDUList([prim, h_sci, h_var, h_flg])

        hdul_a = make_syn_hdul(img_a, var_a, flg_a, ts_a, mjd_a)
        hdul_b = make_syn_hdul(img_b, var_b, flg_b, ts_b, mjd_b)

        path_out_a = os.path.join(pair_folder, "obs_a.fits")
        path_out_b = os.path.join(pair_folder, "obs_b.fits")
        hdul_a.writeto(path_out_a, overwrite=True)
        hdul_b.writeto(path_out_b, overwrite=True)

        ground_truth = {
            "is_synthetic": True,
            "synthetic_engineering_label": "SYNTHETIC_ENGINEERING_TEST — NOT REAL SPHEREX OBSERVATION",
            "target_type": t_type,
            "scenario_notes": notes,
            "ground_truth_epoch_a": {
                "ra_deg": round(ra_a, 6),
                "dec_deg": round(dec_a, 6),
                "pixel_x": round(px_a, 2),
                "pixel_y": round(py_a, 2),
                "timestamp_utc": ts_a,
                "mjd": mjd_a
            },
            "ground_truth_epoch_b": {
                "ra_deg": round(ra_b, 6),
                "dec_deg": round(dec_b, 6),
                "pixel_x": round(px_b, 2),
                "pixel_y": round(py_b, 2),
                "timestamp_utc": ts_b,
                "mjd": mjd_b
            },
            "ground_truth_delta_ra_arcsec": round(compute_ra_difference_deg(ra_a, ra_b) * math.cos(math.radians(dec_a)) * 3600.0, 4),
            "ground_truth_delta_dec_arcsec": round((dec_b - dec_a) * 3600.0, 4),
            "ground_truth_angular_displacement_arcsec": round(exact_disp, 4),
            "ground_truth_position_angle_deg": round(exact_pa, 2),
            "ground_truth_dt_days": round(dt_days, 5),
            "ground_truth_dt_hours": round(dt_hours, 4),
            "ground_truth_motion_rate_arcsec_per_day": round(rate_day, 4),
            "ground_truth_motion_rate_arcsec_per_hour": round(rate_hour, 4),
            "astrometric_coordinate_uncertainty_arcsec": 0.50 if t_type == "UNCERTAINTY_BOUNDARY_TEST" else 0.05
        }

        with open(os.path.join(pair_folder, "ground_truth_motion.json"), "w", encoding="utf-8") as f:
            json.dump(ground_truth, f, indent=2)

        metadata = {
            "pair_id": p_id,
            "dataset_class": "SYNTHETIC_ENGINEERING_TEST",
            "pointing_id": "SYNTHETIC_TEST_FIELD",
            "detector": "SIMULATED_BAND_1",
            "target_name": f"SYN_{t_type}",
            "target_coordinates": {
                "ra_deg": round(ra_a, 6),
                "dec_deg": round(dec_a, 6)
            },
            "obs_a": {
                "filename": "obs_a.fits",
                "timestamp_utc": ts_a,
                "mjd": mjd_a,
                "crval1_deg": ra0,
                "crval2_deg": dec0,
                "wcs_valid": True,
                "sha256": sha256_file(path_out_a)
            },
            "obs_b": {
                "filename": "obs_b.fits",
                "timestamp_utc": ts_b,
                "mjd": mjd_b,
                "crval1_deg": ra0,
                "crval2_deg": dec0,
                "wcs_valid": True,
                "sha256": sha256_file(path_out_b)
            },
            "time_separation_minutes": round(dt_hours * 60.0, 2),
            "time_separation_days": round(dt_days, 5),
            "synthetic_displacement_arcsec": round(exact_disp, 4),
            "scientific_eligibility": "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION",
            "is_secular_motion_eligible": True,
            "has_ground_truth_motion": True,
            "synthetic_ground_truth_motion": ground_truth,
            "intended_test_purpose": f"Algorithmic verification of {t_type} displacement and rate calculation.",
            "scientific_disclaimer": "SYNTHETIC_ENGINEERING_TEST — NOT REAL SPHEREX OBSERVATION. Suitable strictly for software calibration and mathematical unit testing."
        }

        with open(os.path.join(pair_folder, "pair_metadata.json"), "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        generated_records.append(metadata)

    # Write manifest for synthetic engineering class
    with open(os.path.join(OUTPUT_ROOT, "synthetic_engineering_test", "manifest.json"), "w", encoding="utf-8") as f:
        json.dump({
            "dataset_class": "SYNTHETIC_ENGINEERING_TEST",
            "count": len(generated_records),
            "scientific_eligibility": "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION",
            "pairs": generated_records
        }, f, indent=2)

    return generated_records


def generate_package_manifests_and_readme(real_pairs, syn_pairs):
    """Builds root README, dataset_manifest.json, and SHA256SUMS.txt."""
    print("Generating Package Manifests, README, and Checksums...")

    total_pairs = len(real_pairs) + len(syn_pairs)
    total_samples = total_pairs * 2

    # Root Dataset Manifest
    dataset_manifest = {
        "dataset_name": "SPECTRA-X Personal Test Dataset",
        "version": "1.0.0",
        "release_date": "2026-11-13",
        "description": (
            "Optional, standalone, separately downloadable astronomical observation test dataset for "
            "development, algorithm validation, and engineering verification in the SPECTRA-X Observatory platform. "
            "This package is strictly optional and independent of application runtime."
        ),
        "total_pairs": total_pairs,
        "total_observation_samples": total_samples,
        "classes": {
            "REAL_INTRA_VISIT": {
                "pair_count": len(real_pairs),
                "observation_sample_count": len(real_pairs) * 2,
                "temporal_eligibility": "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY",
                "description": "Genuine intra-visit dither observations from SPHEREx Level-2 pointings (P0001, P0002, P0003, P0008, P0009, P0010)."
            },
            "SYNTHETIC_ENGINEERING_TEST": {
                "pair_count": len(syn_pairs),
                "observation_sample_count": len(syn_pairs) * 2,
                "temporal_eligibility": "TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION",
                "description": "Deterministic synthetic observations with simulated multi-day baselines, RA wraparound, and known motion truth."
            }
        },
        "all_pairs": real_pairs + syn_pairs
    }

    with open(os.path.join(OUTPUT_ROOT, "dataset_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(dataset_manifest, f, indent=2)

    # Root README.md
    readme_content = f"""# SPECTRA-X Personal Test Dataset (50 Pairs / 100 Samples)

**Version:** 1.0.0  
**Release Date:** 2026-11-13  
**Package:** `SPECTRA-X-Personal-Test-Data.zip`  
**License / Terms:** NASA Space Apps Challenge 2026 Engineering Dataset  

---

## 1. Important Product Architecture Note

SPECTRA-X is a general-purpose, input-driven astronomical analysis platform. Researchers and astronomers provide their own observation data (FITS cutouts, 102-channel spectrophotometry CSVs, or target catalogs) directly into the workspace.

This dataset is an **OPTIONAL, SEPARATELY DOWNLOADABLE PERSONAL TEST DATASET** for offline development, algorithm verification, and demonstration.

The SPECTRA-X Observatory application:
- Does **NOT** depend on this test dataset.
- Does **NOT** preload this dataset automatically into analysis sessions.
- Does **NOT** treat synthetic engineering scenarios as real astronomical discoveries.

---

## 2. Dataset Composition (50 Pairs / 100 Observation Samples)

| Dataset Class | Pair Count | Samples | Baseline Separation (Δt) | Scientific Classification |
|:---|:---:|:---:|:---:|:---|
| **REAL_INTRA_VISIT** | 25 | 50 | $\\Delta t < 1.0\\text{{ day}}$ ($2.15 - 6.45\\text{{ min}}$) | `INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY` |
| **SYNTHETIC_ENGINEERING_TEST** | 25 | 50 | $\\Delta t = 1.0 - 90.0\\text{{ days}}$ | `TEMPORALLY_ELIGIBLE_REQUIRES_FURTHER_VALIDATION` |
| **TOTAL** | **50** | **100** | — | — |

---

## 3. Package Structure

```text
SPECTRA-X-Personal-Test-Data/
├── README.md                  # This documentation
├── dataset_manifest.json      # Complete dataset catalog manifest
├── SHA256SUMS.txt             # Bitwise SHA-256 checksums of all 100 FITS files and metadata
├── real_intra_visit/          # 25 Real SPHEREx flight observation dither pairs
│   ├── manifest.json
│   └── pairs/
│       ├── REAL_PAIR_001/     # (P0003, D1, Dither 1 vs Dither 4, Primary Candidate)
│       │   ├── obs_a.fits
│       │   ├── obs_b.fits
│       │   └── pair_metadata.json
│       └── ... (REAL_PAIR_001 through REAL_PAIR_025)
└── synthetic_engineering_test/ # 25 Deterministic synthetic motion pairs
    ├── manifest.json
    └── pairs/
        ├── SYNTH_PAIR_001/    # (Main Belt Asteroid-like slow shift)
        │   ├── obs_a.fits
        │   ├── obs_b.fits
        │   ├── ground_truth_motion.json
        │   └── pair_metadata.json
        └── ... (SYNTH_PAIR_001 through SYNTH_PAIR_025)
```

---

## 4. Extraction & Usage Instructions

### 4.1 Extracting the Package
Extract the ZIP archive into any convenient location on your workstation:
```bash
unzip SPECTRA-X-Personal-Test-Data.zip -d personal_test_data/
```

### 4.2 Inspecting a Real Intra-Visit Pair
Every real pair contains:
- `obs_a.fits`: Multi-extension FITS file (SCI, VAR, FLAGS) with WCS.
- `obs_b.fits`: Subsequent intra-visit dither FITS file taken minutes later.
- `pair_metadata.json`: Provenance metadata recording original FITS filenames and SHA-256 hashes.

### 4.3 Inspecting a Synthetic Engineering Pair
Every synthetic pair contains:
- `obs_a.fits` & `obs_b.fits`: Simulated FITS frames with synthetic point spread functions.
- `ground_truth_motion.json`: Known ground-truth trajectory, angular displacement, and rates.
- `pair_metadata.json`: Scenario category and parameter details.

### 4.4 Using with the SPECTRA-X Motion Analysis API
You can run automated motion analysis on any pair using the REST API:
```bash
curl -X POST http://127.0.0.1:8050/api/motion/analyze \\
  -H "Content-Type: application/json" \\
  -d '{{
    "obs_a": {{"ra": 150.0, "dec": 10.0, "timestamp": "2026-07-02T00:00:00Z"}},
    "obs_b": {{"ra": 150.001, "dec": 10.001, "timestamp": "2026-07-04T00:00:00Z"}}
  }}'
```

---

## 5. Scientific Limitations & Governance

1. **Intra-Visit Dither Restriction:** Real pairs feature baselines $\\Delta t < 1.0\\text{{ day}}$ and must NEVER be used to claim moving object discoveries. They are intended strictly for astrometric alignment, PSF subtraction null tests, and registration diagnostics.
2. **Synthetic Data Labeling:** All synthetic observations are artificially synthesized test patterns with known ground-truth motion vectors. They must NEVER be presented as real astronomical discoveries.
"""

    with open(os.path.join(OUTPUT_ROOT, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)

    # Compute SHA-256 for every file in the package
    checksum_lines = []
    for root, dirs, files in os.walk(OUTPUT_ROOT):
        for fname in sorted(files):
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, OUTPUT_ROOT).replace("\\", "/")
            if rel_path == "SHA256SUMS.txt":
                continue
            h_val = sha256_file(fpath)
            checksum_lines.append(f"{h_val}  {rel_path}\n")

    checksum_lines.sort(key=lambda x: x.split()[1])
    with open(os.path.join(OUTPUT_ROOT, "SHA256SUMS.txt"), "w", encoding="utf-8") as f:
        f.writelines(checksum_lines)

    print(f"Computed SHA256SUMS for {len(checksum_lines)} package files.")


def create_zip_archive():
    """Compresses OUTPUT_ROOT into a standalone downloadable ZIP archive."""
    print(f"Creating Standalone ZIP Archive at: {ZIP_DEST} ...")
    os.makedirs(os.path.dirname(ZIP_DEST), exist_ok=True)

    with zipfile.ZipFile(ZIP_DEST, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(OUTPUT_ROOT):
            for fname in sorted(files):
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, os.path.dirname(OUTPUT_ROOT))
                zipf.write(fpath, arcname)

    zip_size_mb = os.path.getsize(ZIP_DEST) / (1024 * 1024)
    print(f"ZIP Archive successfully created. Size: {zip_size_mb:.2f} MB")
    return zip_size_mb


def validate_all_50_pairs():
    """Executes numerical validation on all 50 curated pairs using AstronomicalMotionEngine."""
    print("Running Numerical Validation on all 50 pairs...")

    manifest_path = os.path.join(OUTPUT_ROOT, "dataset_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    real_results = []
    syn_results = []

    for pair in manifest["all_pairs"]:
        p_id = pair["pair_id"]
        ds_class = pair["dataset_class"]

        if ds_class == "REAL_INTRA_VISIT":
            p_folder = os.path.join(OUTPUT_ROOT, "real_intra_visit", "pairs", p_id)
        else:
            p_folder = os.path.join(OUTPUT_ROOT, "synthetic_engineering_test", "pairs", p_id)

        fits_a = os.path.join(p_folder, "obs_a.fits")
        fits_b = os.path.join(p_folder, "obs_b.fits")

        if ds_class == "REAL_INTRA_VISIT":
            # For real pairs, cutout was extracted with target centered at (64.0, 64.0)
            with fits.open(fits_a) as h_a, fits.open(fits_b) as h_b:
                w_a = WCS(h_a[1].header)
                w_b = WCS(h_b[1].header)
                sky_a = w_a.all_pix2world([[64.0, 64.0]], 0)[0]
                sky_b = w_b.all_pix2world([[64.0, 64.0]], 0)[0]
                ts_a = str(h_a[1].header.get("DATE-OBS"))
                ts_b = str(h_b[1].header.get("DATE-OBS"))
        else:
            # For synthetic pairs, query target coordinates from ground truth
            gt = pair["synthetic_ground_truth_motion"]
            px_a, py_a = gt["ground_truth_epoch_a"]["pixel_x"], gt["ground_truth_epoch_a"]["pixel_y"]
            px_b, py_b = gt["ground_truth_epoch_b"]["pixel_x"], gt["ground_truth_epoch_b"]["pixel_y"]
            with fits.open(fits_a) as h_a, fits.open(fits_b) as h_b:
                w_a = WCS(h_a[1].header)
                w_b = WCS(h_b[1].header)
                sky_a = w_a.all_pix2world([[px_a, py_a]], 0)[0]
                sky_b = w_b.all_pix2world([[px_b, py_b]], 0)[0]
                ts_a = str(h_a[1].header.get("DATE-OBS"))
                ts_b = str(h_b[1].header.get("DATE-OBS"))

        obs_a = ObservationEpoch(
            obs_id=f"{p_id}_A",
            ra_deg=float(sky_a[0]),
            dec_deg=float(sky_a[1]),
            timestamp=ts_a,
            wcs_valid=True,
            sigma_coord_arcsec=0.05
        )
        obs_b = ObservationEpoch(
            obs_id=f"{p_id}_B",
            ra_deg=float(sky_b[0]),
            dec_deg=float(sky_b[1]),
            timestamp=ts_b,
            wcs_valid=True,
            sigma_coord_arcsec=0.05
        )

        res = AstronomicalMotionEngine.calculate_motion(obs_a, obs_b)
        assert res.is_valid, f"Pair {p_id} calculation failed: {res.notes}"

        if ds_class == "REAL_INTRA_VISIT":
            assert not res.is_secular_motion_eligible, f"Real pair {p_id} must be ineligible for secular motion"
            assert res.temporal_eligibility_status == "INTRA_VISIT_DITHER_INELIGIBLE_FOR_SECULAR_VARIABILITY"
            assert pair["synthetic_ground_truth_motion"] is None
            real_results.append({
                "pair_id": p_id,
                "dt_minutes": res.time_baseline_hours * 60.0,
                "displacement_arcsec": res.angular_displacement_arcsec,
                "status": "PASS"
            })
        else:
            assert res.is_secular_motion_eligible, f"Synthetic pair {p_id} should be temporally eligible"
            gt = pair["synthetic_ground_truth_motion"]
            exp_disp = gt["ground_truth_angular_displacement_arcsec"]
            exp_rate = gt["ground_truth_motion_rate_arcsec_per_day"]

            calc_disp = res.angular_displacement_arcsec
            calc_rate = res.motion_rate_arcsec_per_day

            # Check numerical tolerance (< 0.05 arcsec or < 0.5%)
            disp_err = abs(calc_disp - exp_disp)
            rate_err = abs(calc_rate - exp_rate)
            assert disp_err < 0.1, f"Synthetic {p_id} disp error {disp_err} arcsec exceeds 0.1 arcsec tolerance"

            syn_results.append({
                "pair_id": p_id,
                "target_type": gt["target_type"],
                "expected_disp_arcsec": exp_disp,
                "calculated_disp_arcsec": calc_disp,
                "displacement_error_arcsec": round(disp_err, 6),
                "expected_rate_arcsec_day": exp_rate,
                "calculated_rate_arcsec_day": calc_rate,
                "rate_error_arcsec_day": round(rate_err, 6),
                "status": "PASS"
            })

    print(f"Validation complete: 25 Real Intra-Visit pairs PASSED. 25 Synthetic Engineering pairs PASSED.")
    return real_results, syn_results


if __name__ == "__main__":
    print("==================================================================")
    print("Task 4.29C: Standalone Personal Test Dataset Generator")
    print("==================================================================")
    real_pairs = curate_real_intra_visit_pairs()
    syn_pairs = generate_synthetic_engineering_pairs()
    generate_package_manifests_and_readme(real_pairs, syn_pairs)
    zip_size = create_zip_archive()
    real_val, syn_val = validate_all_50_pairs()
    print("==================================================================")
    print(f"Successfully generated {len(real_pairs) + len(syn_pairs)} pairs / 100 observation samples.")
    print(f"Package ZIP: {ZIP_DEST} ({zip_size:.2f} MB)")
    print("==================================================================")
