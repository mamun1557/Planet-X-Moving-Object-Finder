"""
SPECTRA-X / F1 — Phase 3, Task 1.1O
Five-Pointing Controlled Pilot Benchmark Preparation:
Source Reference Catalogue Generation, Gaia DR3/2MASS Cross-Matching, and Mask Architecture.

Pointings: 0001, 0002, 0008, 0009, 0010
Total FITS products: 120 (24 per pointing, across 6 detectors and 4 dithers)
Epoch: SPHEREx Observation Epoch 2026.5496 (MJD 61241.018)
"""

import os
import sys
import time
import math
import json
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
from scipy.spatial import cKDTree

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

# Historical Protected Assets Hashes
PROTECTED_ASSETS = {
    "checkpoints/astrovision_spatial_v2.pt": "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557",
    "data/processed/validation/pointing_0003_final_validated_catalogue.csv": "ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b",
    "data/processed/validation/astrovision_injection_manifest.csv": "339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978",
    "data/processed/validation/astrovision_injection_results.csv": "22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c",
    "reports/figures/astrovision/benchmark_metrics.json": "5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c",
    "reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md": "dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688",
    "reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md": "5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698",
    "reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md": "db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808",
    "reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md": "d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc",
    "reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md": "13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985",
    "reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md": "764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88",
    "reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md": "5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18",
    "reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md": "22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278",
    "reports/ASTROVISION_TASK_1_1H_REMEDIATION.md": "950e361cccdb4c342cf10267d8f61fd38644cf97001860a794c7465f80e94e03",
    "reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md": "74653153b17f110ba60578b2141ef1d205277b6fa4980178f0ac5ab542d0fd4f",
    "reports/ASTROVISION_TASK_1_1I_INDEPENDENT_REAUDIT.md": "7db57a54de5d9346ff46f8144868b93ed67544e2c9413d906852c3a79e86167a"
}

SPHEREX_EPOCH = 2026.5496  # 2026-07-20T00:26:21 UTC (MJD 61241.018)
GAIA_EPOCH = 2016.0
DT_YEARS = SPHEREX_EPOCH - GAIA_EPOCH  # 10.5496 years

POINTINGS = ["0001", "0002", "0008", "0009", "0010"]
LEVEL2_DIR = BASE_DIR / "data" / "spherex" / "multipointing_pilot" / "level2"
RAW_GAIA_DIR = BASE_DIR / "data" / "external" / "gaia_dr3"
CAT_DIR = BASE_DIR / "data" / "processed" / "pilot_catalogues"
MASK_DIR = BASE_DIR / "data" / "processed" / "pilot_masks"

RAW_GAIA_DIR.mkdir(parents=True, exist_ok=True)
CAT_DIR.mkdir(parents=True, exist_ok=True)
MASK_DIR.mkdir(parents=True, exist_ok=True)

# Pointing field centers for the 3 focal-plane fields:
# Field 1: D1/D4, Field 2: D2/D5, Field 3: D3/D6
FIELD_CENTERS = {
    "0001": [
        {"field": 1, "detectors": [1, 4], "ra": 232.6636, "dec": -10.7213},
        {"field": 2, "detectors": [2, 5], "ra": 236.4941, "dec": -11.6087},
        {"field": 3, "detectors": [3, 6], "ra": 240.3274, "dec": -12.5569},
    ],
    "0002": [
        {"field": 1, "detectors": [1, 4], "ra": 222.1883, "dec": -28.8813},
        {"field": 2, "detectors": [2, 5], "ra": 226.4197, "dec": -30.0381},
        {"field": 3, "detectors": [3, 6], "ra": 230.7168, "dec": -31.1660},
    ],
    "0008": [
        {"field": 1, "detectors": [1, 4], "ra": 33.4396, "dec": 8.2925},
        {"field": 2, "detectors": [2, 5], "ra": 29.7763, "dec": 6.9761},
        {"field": 3, "detectors": [3, 6], "ra": 26.0913, "dec": 5.7351},
    ],
    "0009": [
        {"field": 1, "detectors": [1, 4], "ra": 17.6348, "dec": 47.9466},
        {"field": 2, "detectors": [2, 5], "ra": 12.5906, "dec": 46.1811},
        {"field": 3, "detectors": [3, 6], "ra": 7.7887, "dec": 44.3022},
    ],
    "0010": [
        {"field": 1, "detectors": [1, 4], "ra": 273.7222, "dec": 70.4402},
        {"field": 2, "detectors": [2, 5], "ra": 273.8088, "dec": 66.5786},
        {"field": 3, "detectors": [3, 6], "ra": 273.6277, "dec": 62.7125},
    ],
}

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def verify_authoritative_inputs() -> Dict[str, Any]:
    """Task A: Verify input dataset completeness and historical asset non-mutation."""
    print("=== TASK A: INDEPENDENT INPUT & PROVENANCE VERIFICATION ===")
    
    # 1. Verify protected assets
    asset_status = {}
    all_assets_pass = True
    for rel_path, expected_hash in PROTECTED_ASSETS.items():
        p = BASE_DIR / rel_path
        if not p.exists():
            asset_status[rel_path] = "MISSING"
            all_assets_pass = False
        else:
            actual = compute_sha256(p)
            match = (actual == expected_hash)
            asset_status[rel_path] = "MATCH" if match else f"MISMATCH ({actual})"
            if not match:
                all_assets_pass = False
    
    if not all_assets_pass:
        raise RuntimeError(f"CRITICAL: Protected asset hash mismatch detected: {asset_status}")
    print(f"  All {len(PROTECTED_ASSETS)} protected historical assets verified (SHA-256 MATCH).")

    # 2. Verify all 120 FITS files
    fits_counts = {}
    fits_files = []
    for p in POINTINGS:
        p_dir = LEVEL2_DIR / p
        files = sorted(list(p_dir.glob("*.fits")))
        fits_counts[p] = len(files)
        if len(files) != 24:
            raise RuntimeError(f"CRITICAL: Pointing {p} has {len(files)} files, expected exactly 24!")
        fits_files.extend(files)
    
    print(f"  All 5 pointings present: 120/120 FITS files verified (24 per pointing across 6 detectors x 4 dithers).")
    return {
        "status": "PASS",
        "protected_assets_verified": len(PROTECTED_ASSETS),
        "pointings": POINTINGS,
        "total_fits_files": len(fits_files),
        "fits_counts_per_pointing": fits_counts
    }


def query_gaia_tap(ra: float, dec: float, radius_deg: float = 2.50, limit: int = 2500) -> pd.DataFrame:
    """
    Queries Heidelberg ARI TAP for Gaia DR3 stars with official 2MASS cross-match.
    Uses indexed spherical CIRCLE constraint for sub-second retrieval.
    """
    tap_url = "https://gaia.ari.uni-heidelberg.de/tap/sync"
    adql = f"""
    SELECT TOP {limit}
        g.source_id, g.ra, g.dec, g.pmra, g.pmdec, g.parallax,
        g.phot_g_mean_mag, g.phot_bp_mean_mag, g.phot_rp_mean_mag,
        g.ruwe, g.astrometric_excess_noise,
        x.original_ext_source_id as tmass_id, x.angular_distance as tmass_dist_arcsec
    FROM gaiadr3.gaia_source as g
    LEFT JOIN gaiadr3.tmass_psc_xsc_best_neighbour as x ON g.source_id = x.source_id
    WHERE 1=CONTAINS(POINT('ICRS', g.ra, g.dec), CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {radius_deg:.4f}))
      AND g.phot_g_mean_mag <= 19.5
    """
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": adql
    }
    encoded = urllib.parse.urlencode(params)
    req_url = f"{tap_url}?{encoded}"
    
    req = urllib.request.Request(req_url, headers={"User-Agent": "SPECTRA-X-PilotPreparation/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        df = pd.read_csv(resp)
    return df


def fetch_or_load_pointing_gaia(pointing: str) -> pd.DataFrame:
    """Retrieves or loads cached Gaia DR3 + 2MASS data for all 3 fields of a pointing."""
    dfs = []
    fields = FIELD_CENTERS[pointing]
    for f_info in fields:
        f_idx = f_info["field"]
        cache_path = RAW_GAIA_DIR / f"pilot_{pointing}_field{f_idx}_gaia_dr3.csv"
        if cache_path.exists():
            print(f"  [P{pointing} Field {f_idx}] Loading cached raw catalogue ({cache_path.name})...")
            df = pd.read_csv(cache_path)
        else:
            print(f"  [P{pointing} Field {f_idx}] Querying Heidelberg TAP at ({f_info['ra']}, {f_info['dec']})...")
            df = query_gaia_tap(f_info["ra"], f_info["dec"], radius_deg=2.50, limit=2500)
            df.to_csv(cache_path, index=False)
            print(f"  [P{pointing} Field {f_idx}] Saved {len(df)} sources -> {cache_path.name}")
        df["field_index"] = f_idx
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    # Deduplicate by source_id
    n_before = len(combined)
    combined = combined.drop_duplicates(subset=["source_id"]).reset_index(drop=True)
    n_after = len(combined)
    print(f"  [P{pointing}] Combined {n_before} raw records -> {n_after} unique Gaia DR3 sources.")
    return combined


def propagate_astrometry(df: pd.DataFrame) -> pd.DataFrame:
    """Propagates Gaia DR3 astrometry (J2016.0) to SPHEREx observation epoch (2026.5496)."""
    ras = df["ra"].values.astype(float)
    decs = df["dec"].values.astype(float)
    pmras = df["pmra"].values.astype(float)
    pmdecs = df["pmdec"].values.astype(float)

    has_pm = (~np.isnan(pmras)) & (~np.isnan(pmdecs))
    cos_dec = np.cos(np.radians(decs))
    # Protect against pole division
    cos_dec = np.where(np.abs(cos_dec) < 1e-6, 1e-6, cos_dec)

    delta_ra_deg = np.where(has_pm, (pmras * 1e-3 * DT_YEARS) / (3600.0 * cos_dec), 0.0)
    delta_dec_deg = np.where(has_pm, (pmdecs * 1e-3 * DT_YEARS) / 3600.0, 0.0)

    ra_prop = (ras + delta_ra_deg) % 360.0
    dec_prop = decs + delta_dec_deg

    df["ra_epoch"] = ra_prop
    df["dec_epoch"] = dec_prop
    df["pm_propagated"] = has_pm
    df["delta_ra_arcsec"] = delta_ra_deg * 3600.0 * cos_dec
    df["delta_dec_arcsec"] = delta_dec_deg * 3600.0
    return df


def classify_sources(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes spatial crowding and assigns rigorous astronomical categories:
    - RELIABLE_ISOLATED_POINT_SOURCE
    - BLENDED_CROWDED
    - SATURATED_OR_CONTAMINATED
    - EXTENDED
    - UNCERTAIN_OR_LOW_QUALITY
    """
    # 1. Compute 3D Cartesian coordinates on unit sphere for exact k-d tree spatial neighbor search
    ra_rad = np.radians(df["ra_epoch"].values)
    dec_rad = np.radians(df["dec_epoch"].values)
    x = np.cos(dec_rad) * np.cos(ra_rad)
    y = np.cos(dec_rad) * np.sin(ra_rad)
    z = np.sin(dec_rad)
    coords = np.column_stack([x, y, z])

    tree = cKDTree(coords)
    # Query 2 nearest neighbors (first neighbor is self, second is nearest)
    dists_euclid, indices = tree.query(coords, k=2)
    # Convert Euclidean chord distance d_c = 2 * sin(theta/2) to angular separation in arcseconds
    theta_rad = 2.0 * np.arcsin(np.clip(dists_euclid[:, 1] / 2.0, 0.0, 1.0))
    nn_arcsec = np.degrees(theta_rad) * 3600.0
    df["nn_dist_arcsec"] = nn_arcsec

    # 2. Check 2MASS match status
    # 2MASS cross-match threshold: 2.0 arcsec (SPHEREx pixel is 6.156 arcsec)
    tmass_dist = df["tmass_dist_arcsec"].fillna(999.0).values
    has_tmass = (df["tmass_id"].notna()) & (tmass_dist <= 2.0)
    df["has_tmass_match"] = has_tmass

    # 3. Categorization logic
    g_mags = df["phot_g_mean_mag"].values
    ruwes = df["ruwe"].fillna(99.0).values
    excess_noises = df["astrometric_excess_noise"].fillna(0.0).values

    # Find saturated / very bright stars (G < 11.5)
    is_saturated = (g_mags < 11.5)

    # Compute distance to nearest saturated star
    sat_indices = np.where(is_saturated)[0]
    if len(sat_indices) > 0:
        sat_tree = cKDTree(coords[sat_indices])
        sat_dists_euclid, _ = sat_tree.query(coords, k=1)
        sat_theta_rad = 2.0 * np.arcsin(np.clip(sat_dists_euclid / 2.0, 0.0, 1.0))
        dist_to_sat_arcsec = np.degrees(sat_theta_rad) * 3600.0
    else:
        dist_to_sat_arcsec = np.full(len(df), 99999.0)
    df["dist_to_sat_arcsec"] = dist_to_sat_arcsec

    categories = []
    for i in range(len(df)):
        g = g_mags[i]
        nn = nn_arcsec[i]
        ru = ruwes[i]
        en = excess_noises[i]
        d_sat = dist_to_sat_arcsec[i]

        if g < 11.5:
            cat = "SATURATED_OR_CONTAMINATED"
        elif en > 2.0:
            cat = "EXTENDED"
        elif nn <= 12.0:  # within 2 SPHEREx pixels (6.156" * 2 = 12.3")
            cat = "BLENDED_CROWDED"
        elif ru > 1.40 or np.isnan(g) or g > 19.5 or d_sat < 185.0:  # 185 arcsec = 30 px halo
            cat = "UNCERTAIN_OR_LOW_QUALITY"
        else:
            cat = "RELIABLE_ISOLATED_POINT_SOURCE"
        categories.append(cat)

    df["classification_category"] = categories
    return df


def compute_mask_diagnostics(pointing: str, df_cat: pd.DataFrame) -> Dict[str, Any]:
    """
    Projects catalogue sources into authentic detector coordinates (D1..D6, Dithers 1..4)
    using the verified FITS WCS headers, and computes usable unmasked areas and diagnostics.
    """
    p_dir = LEVEL2_DIR / pointing
    fits_files = sorted(list(p_dir.glob("*.fits")))
    
    det_diagnostics = {}
    total_sources_in_pointing = len(df_cat)
    
    # Pre-extract catalog coordinates
    ra_epoch = df_cat["ra_epoch"].values
    dec_epoch = df_cat["dec_epoch"].values
    categories = df_cat["classification_category"].values

    for fits_path in fits_files:
        fname = fits_path.name
        # Parse dither and detector from filename: level2_2026W30_1B_0001_1D1_spx_...
        parts = fname.split("_")
        dither_det = parts[4]  # e.g. '1D1'
        dither = int(dither_det[0])
        det_num = int(dither_det[2])
        det_name = f"D{det_num}"

        with fits.open(fits_path) as hdul:
            hdr = hdul["IMAGE"].header
            w = WCS(hdr)
            naxis1 = hdr.get("NAXIS1", 2040)
            naxis2 = hdr.get("NAXIS2", 2040)
            pixel_scale_arcsec = float(hdr.get("PLTSCALE", 6.156))

        # Project all catalog sources to detector pixel coordinates (x, y)
        px_x, px_y = w.world_to_pixel_values(ra_epoch, dec_epoch)
        
        # Check in-bounds condition (1 to 2040, 1-based FITS indexing)
        in_bounds = (px_x >= 1.0) & (px_x <= naxis1) & (px_y >= 1.0) & (px_y <= naxis2)
        in_margin = (px_x >= 51.0) & (px_x <= naxis1 - 50.0) & (px_y >= 51.0) & (px_y <= naxis2 - 50.0)

        n_on_array = int(np.sum(in_bounds))
        cats_on_array = categories[in_bounds]
        
        counts = {
            "RELIABLE_ISOLATED_POINT_SOURCE": int(np.sum(cats_on_array == "RELIABLE_ISOLATED_POINT_SOURCE")),
            "BLENDED_CROWDED": int(np.sum(cats_on_array == "BLENDED_CROWDED")),
            "SATURATED_OR_CONTAMINATED": int(np.sum(cats_on_array == "SATURATED_OR_CONTAMINATED")),
            "EXTENDED": int(np.sum(cats_on_array == "EXTENDED")),
            "UNCERTAIN_OR_LOW_QUALITY": int(np.sum(cats_on_array == "UNCERTAIN_OR_LOW_QUALITY")),
        }

        # Calculate geometric masked area on detector:
        # Array area: 2040 x 2040 = 4,161,600 pixels
        # 50-pixel margin: (2040 - 100) * (2040 - 100) = 3,763,600 pixels active
        # Exclusion zones:
        # - Point sources: R = 3 px -> Area = pi * 9 = 28.3 px^2
        # - Crowded: R = 6 px -> Area = pi * 36 = 113 px^2
        # - Extended: R = 15 px -> Area = pi * 225 = 707 px^2
        # - Saturated: R = 30 px -> Area = pi * 900 = 2827 px^2
        total_pixels = naxis1 * naxis2
        margin_pixels = total_pixels - (naxis1 - 100) * (naxis2 - 100)
        
        source_masked_pixels = (
            counts["RELIABLE_ISOLATED_POINT_SOURCE"] * (math.pi * 3.0**2) +
            counts["BLENDED_CROWDED"] * (math.pi * 6.0**2) +
            counts["EXTENDED"] * (math.pi * 15.0**2) +
            counts["SATURATED_OR_CONTAMINATED"] * (math.pi * 30.0**2)
        )
        # Bounded usable pixel estimate
        usable_pixels = max(0.0, total_pixels - margin_pixels - source_masked_pixels)
        usable_fraction = usable_pixels / float(total_pixels)
        fov_deg2 = (naxis1 * pixel_scale_arcsec / 3600.0) * (naxis2 * pixel_scale_arcsec / 3600.0)
        source_density_per_deg2 = n_on_array / fov_deg2

        key = f"{det_name}_dither{dither}"
        det_diagnostics[key] = {
            "fits_file": fname,
            "detector": det_name,
            "dither": dither,
            "n_sources_on_array": n_on_array,
            "n_sources_in_active_margin": int(np.sum(in_margin)),
            "category_counts": counts,
            "total_pixels": total_pixels,
            "margin_pixels": margin_pixels,
            "source_masked_pixels_approx": round(source_masked_pixels, 1),
            "usable_pixels_approx": round(usable_pixels, 1),
            "usable_fraction": round(usable_fraction, 4),
            "fov_deg2": round(fov_deg2, 4),
            "source_density_deg2": round(source_density_per_deg2, 2)
        }

    return {
        "pointing": pointing,
        "total_sources_in_catalogue": total_sources_in_pointing,
        "n_exposures_evaluated": len(fits_files),
        "detector_exposures": det_diagnostics
    }


def run_pilot_preparation() -> Dict[str, Any]:
    t0 = time.time()
    prov = verify_authoritative_inputs()
    
    catalogue_summaries = {}
    mask_summaries = {}
    
    print("\n=== TASK B & C: GAIA DR3/2MASS CROSS-MATCHING & MASK GENERATION ===")
    for p in POINTINGS:
        print(f"\nProcessing Pointing {p}...")
        df_raw = fetch_or_load_pointing_gaia(p)
        df_prop = propagate_astrometry(df_raw)
        df_classified = classify_sources(df_prop)
        
        # Save processed catalogue
        cat_file = CAT_DIR / f"pointing_{p}_source_catalogue.csv"
        df_classified.to_csv(cat_file, index=False)
        cat_sha256 = compute_sha256(cat_file)
        
        cat_summary = {
            "pointing": p,
            "catalogue_file": str(cat_file.relative_to(BASE_DIR)),
            "sha256": cat_sha256,
            "total_sources": len(df_classified),
            "pm_propagated_count": int(df_classified["pm_propagated"].sum()),
            "tmass_matched_count": int(df_classified["has_tmass_match"].sum()),
            "category_breakdown": df_classified["classification_category"].value_counts().to_dict(),
            "mean_g_mag": round(float(df_classified["phot_g_mean_mag"].mean()), 2),
            "median_nn_arcsec": round(float(df_classified["nn_dist_arcsec"].median()), 2)
        }
        catalogue_summaries[p] = cat_summary
        print(f"  [P{p}] Catalogue saved -> {cat_file.name} (SHA-256: {cat_sha256[:12]}...)")
        print(f"  [P{p}] Category counts: {cat_summary['category_breakdown']}")

        # Compute mask diagnostics
        mask_diag = compute_mask_diagnostics(p, df_classified)
        mask_diag_file = MASK_DIR / f"pointing_{p}_mask_diagnostics.json"
        with open(mask_diag_file, "w", encoding="utf-8") as f:
            json.dump(mask_diag, f, indent=2)
        mask_summaries[p] = {
            "diagnostics_file": str(mask_diag_file.relative_to(BASE_DIR)),
            "sha256": compute_sha256(mask_diag_file)
        }
        print(f"  [P{p}] Mask diagnostics saved -> {mask_diag_file.name}")

    elapsed = time.time() - t0
    print(f"\nAll 5 pointings processed successfully in {elapsed:.2f}s.")
    return {
        "provenance": prov,
        "catalogue_summaries": catalogue_summaries,
        "mask_summaries": mask_summaries,
        "elapsed_seconds": round(elapsed, 2)
    }


if __name__ == "__main__":
    results = run_pilot_preparation()
    print("\nPreparation script complete.")
