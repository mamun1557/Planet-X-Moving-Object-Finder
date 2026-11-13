#!/usr/bin/env python3
"""
SPECTRA-X / F1 — Phase 4, Task 4.19B
Controlled External Catalog Acquisition, Exact-Footprint Crossmatch & Empirical Coverage Validation
Pipeline Build: l2b-v27-2026-222
"""

import os
import sys
import time
import json
import hashlib
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
from scipy.spatial import cKDTree

BASE_DIR = Path(".").resolve()
OUT_DIR = BASE_DIR / "reports" / "phase4" / "task_4_19B"
OUT_DIR.mkdir(parents=True, exist_ok=True)
RAW_CAT_DIR = BASE_DIR / "data" / "external_catalogs" / "task_4_19B"
RAW_CAT_DIR.mkdir(parents=True, exist_ok=True)
GAIA_BATCH_DIR = RAW_CAT_DIR / "gaia_batches"
GAIA_BATCH_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# CONSTANTS & PARAMETERS
# -----------------------------------------------------------------------------
SPHEREX_EPOCH = 2026.5496  # Week 30, 2026
GAIA_EPOCH = 2016.0
CATWISE_EPOCH = 2015.5
DT_GAIA = SPHEREX_EPOCH - GAIA_EPOCH       # 10.5496 years
DT_CATWISE = SPHEREX_EPOCH - CATWISE_EPOCH # 11.0496 years

CUTOUT_SIZE_PIXELS = 128
CUTOUT_RADIUS_ARCSEC = 565.0 # Enclosing circle radius for ingestion
CUTOUT_RADIUS_DEG = CUTOUT_RADIUS_ARCSEC / 3600.0 # ~0.1569 deg

# -----------------------------------------------------------------------------
# LOGGING & TRACKING CONTAINERS
# -----------------------------------------------------------------------------
acquisition_manifest = []
acquisition_failures = []

def record_manifest(service: str, endpoint: str, query: str, rows: int, latency: float, status: str, filename: Optional[str] = None):
    acquisition_manifest.append({
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": service,
        "endpoint": endpoint,
        "query": query.strip().replace("\n", " "),
        "returned_rows": rows,
        "latency_seconds": round(latency, 2),
        "status": status,
        "saved_filename": filename
    })

def record_failure(service: str, endpoint: str, query: str, error_type: str, error_message: str):
    acquisition_failures.append({
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "service": service,
        "endpoint": endpoint,
        "query": query.strip().replace("\n", " "),
        "error_type": error_type,
        "error_message": str(error_message)[:200]
    })

# Record historical exploratory failures
record_failure(
    "NASA_IPAC_IRSA_CatWISE",
    "https://irsa.ipac.caltech.edu/TAP/sync",
    "SELECT ... WHERE (CONTAINS(...)=1 OR CONTAINS(...)=1)",
    "UsageFault",
    "BAD_REQUEST: Invalid or unsupported ADQL query string. Multiple spatial CONTAINS joined by OR not supported by IRSA."
)
record_failure(
    "ESA_Gaia_TAP",
    "https://gea.esac.esa.int/tap-server/tap/sync",
    "SELECT TOP 1 source_id FROM gaiadr3.gaia_source",
    "TimeoutError",
    "The read operation timed out after 15.0s during pre-flight endpoint probe."
)

# -----------------------------------------------------------------------------
# 1. LOAD EVALUATION MANIFEST & FITS WCS
# -----------------------------------------------------------------------------
print("=== 1. Loading Evaluation Cohort & Level-2 FITS WCS Headers ===", flush=True)
df_spatial = pd.read_csv("reports/phase4/task_4_18_sky/spatial_source_positions.csv")
print(f"Loaded {len(df_spatial)} evaluation trials.", flush=True)

df_pilot = pd.read_csv("data/processed/pilot_results/astrovision_pilot_trial_results.csv")
eval_pilot = df_pilot[df_pilot["role"] == "EVALUATION"].copy().reset_index(drop=True)

# Cache WCS for all unique FITS files
wcs_cache = {}
for fpath in eval_pilot["fits_relpath"].unique():
    full_path = BASE_DIR / fpath
    if full_path.exists():
        with fits.open(full_path, memmap=True) as hdul:
            wcs_cache[fpath] = WCS(hdul[1].header)
    else:
        print(f"WARNING: Missing FITS file {fpath}", flush=True)

print(f"Cached WCS headers for {len(wcs_cache)} Level-2 FITS files.", flush=True)

# -----------------------------------------------------------------------------
# 2. PHASE B: CONTROLLED EXTERNAL CATALOG ACQUISITION
# -----------------------------------------------------------------------------
print("\n=== 2. Phase B: Controlled External Catalog Acquisition ===", flush=True)

# 2.1 GAIA DR3 ACQUISITION VIA HEIDELBERG TAP (BATCHES OF 15 CUTOUTS)
gaia_raw_file = RAW_CAT_DIR / "gaia_dr3_raw_acquired.csv"

if gaia_raw_file.exists():
    print(f"Loading existing consolidated Gaia DR3 records from {gaia_raw_file.name}...", flush=True)
    df_gaia_all = pd.read_csv(gaia_raw_file)
else:
    batch_size = 15
    n_batches = int(np.ceil(len(df_spatial) / batch_size))
    print(f"Querying Heidelberg ARI TAP for Gaia DR3 across {len(df_spatial)} cutouts in {n_batches} batches...", flush=True)
    tap_url = "https://gaia.ari.uni-heidelberg.de/tap/sync"
    
    gaia_batches = []
    for b in range(n_batches):
        batch_csv = GAIA_BATCH_DIR / f"batch_{b:03d}.csv"
        if batch_csv.exists():
            df_res = pd.read_csv(batch_csv)
            gaia_batches.append(df_res)
            print(f"  [Gaia Batch {b+1:03d}/{n_batches}] Loaded cached {len(df_res)} rows.", flush=True)
            continue
            
        sub_batch = df_spatial.iloc[b * batch_size : (b + 1) * batch_size]
        conds = []
        for _, r in sub_batch.iterrows():
            conds.append(f"1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {r['center_ra_deg']:.5f}, {r['center_dec_deg']:.5f}, {CUTOUT_RADIUS_DEG:.4f}))")
        
        where_clause = " OR ".join(conds)
        adql = f"""
        SELECT
            source_id, ra, dec, ra_error, dec_error,
            phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag,
            pmra, pmdec, pmra_error, pmdec_error,
            parallax, parallax_error, ruwe
        FROM gaiadr3.gaia_source
        WHERE ({where_clause})
          AND phot_g_mean_mag <= 21.0
        """
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql}
        t0 = time.time()
        success = False
        for attempt in range(3):
            try:
                req = urllib.request.Request(f"{tap_url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "SPECTRA-X-Task4.19B/1.0"})
                with urllib.request.urlopen(req, timeout=35) as resp:
                    df_res = pd.read_csv(resp)
                    latency = time.time() - t0
                    df_res.to_csv(batch_csv, index=False)
                    gaia_batches.append(df_res)
                    record_manifest("Heidelberg_ARI_Gaia_TAP", tap_url, adql[:150], len(df_res), latency, "SUCCESS", batch_csv.name)
                    print(f"  [Gaia Batch {b+1:03d}/{n_batches}] Retrieved & saved {len(df_res)} rows in {latency:.2f}s", flush=True)
                    success = True
                    break
            except Exception as e:
                time.sleep(2.0 * (attempt + 1))
                if attempt == 2:
                    latency = time.time() - t0
                    record_failure("Heidelberg_ARI_Gaia_TAP", tap_url, adql[:150], type(e).__name__, str(e))
                    print(f"  [Gaia Batch {b+1:03d}/{n_batches}] FAILED after 3 attempts ({type(e).__name__}: {str(e)[:50]})", flush=True)
        
        time.sleep(0.3)
        
    df_gaia_all = pd.concat(gaia_batches, ignore_index=True).drop_duplicates(subset=["source_id"]).reset_index(drop=True)
    df_gaia_all.to_csv(gaia_raw_file, index=False)
    print(f"Consolidated and saved {len(df_gaia_all)} unique Gaia DR3 sources to {gaia_raw_file.name}", flush=True)

# Also load Task 4.17's 2MASS PSC table for baseline join & crossmatch
tmass_raw_file = BASE_DIR / "reports" / "phase4" / "task_4_17" / "twomass_psc_evaluation_catalog.csv"
if tmass_raw_file.exists():
    df_twomass_base = pd.read_csv(tmass_raw_file)
    print(f"Loaded {len(df_twomass_base)} historical 2MASS PSC records from Task 4.17.", flush=True)
else:
    df_twomass_base = pd.DataFrame(columns=["designation", "ra", "dec", "j_m", "h_m", "k_m", "ph_qual"])

# 2.2 CATWISE2020 ACQUISITION VIA NASA/IPAC IRSA TAP FOR 45 FALSE POSITIVES
catwise_raw_file = RAW_CAT_DIR / "catwise2020_raw_fps.csv"
fps_df = df_spatial[df_spatial["is_baseline_false_positive"] == True].copy().reset_index(drop=True)

if catwise_raw_file.exists():
    print(f"Loading existing CatWISE2020 records for False Positives from {catwise_raw_file.name}...", flush=True)
    df_catwise_all = pd.read_csv(catwise_raw_file)
else:
    print(f"Querying NASA/IPAC IRSA TAP for CatWISE2020 across {len(fps_df)} baseline false positives...", flush=True)
    irsa_tap_url = "https://irsa.ipac.caltech.edu/TAP/sync"
    catwise_sources_list = []
    
    for idx, r in fps_df.iterrows():
        t_id = r["trial_id"]
        c_ra = r["center_ra_deg"]
        c_dec = r["center_dec_deg"]
        adql = f"""
        SELECT source_id, ra, dec, sigra, sigdec, pmra, pmdec, sigpmra, sigpmdec,
               w1mpro, w1sigmpro, w2mpro, w2sigmpro, w1snr, w2snr
        FROM catwise_2020
        WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {c_ra:.5f}, {c_dec:.5f}, 0.16)) = 1
        """
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "CSV", "QUERY": adql}
        t0 = time.time()
        for attempt in range(3):
            try:
                req = urllib.request.Request(f"{irsa_tap_url}?{urllib.parse.urlencode(params)}", headers={"User-Agent": "SPECTRA-X-Task4.19B/1.0"})
                with urllib.request.urlopen(req, timeout=25) as resp:
                    df_res = pd.read_csv(resp)
                    latency = time.time() - t0
                    if len(df_res.columns) > 1 and "source_id" in df_res.columns:
                        catwise_sources_list.append(df_res)
                        record_manifest("NASA_IPAC_IRSA_CatWISE", irsa_tap_url, adql[:150], len(df_res), latency, "SUCCESS")
                        print(f"  [CatWISE FP {t_id}] Retrieved {len(df_res)} rows in {latency:.2f}s", flush=True)
                    else:
                        record_failure("NASA_IPAC_IRSA_CatWISE", irsa_tap_url, adql[:150], "VOTableError", "Invalid query response")
                    break
            except Exception as e:
                time.sleep(1.5 * (attempt + 1))
                if attempt == 2:
                    latency = time.time() - t0
                    record_failure("NASA_IPAC_IRSA_CatWISE", irsa_tap_url, adql[:150], type(e).__name__, str(e))
                    print(f"  [CatWISE FP {t_id}] FAILED ({type(e).__name__}: {str(e)[:50]})", flush=True)
        time.sleep(0.3)
        
    if catwise_sources_list:
        df_catwise_all = pd.concat(catwise_sources_list, ignore_index=True).drop_duplicates(subset=["source_id"]).reset_index(drop=True)
    else:
        df_catwise_all = pd.DataFrame(columns=["source_id", "ra", "dec", "w1mpro", "w2mpro", "pmra", "pmdec"])
    df_catwise_all.to_csv(catwise_raw_file, index=False)
    print(f"Saved {len(df_catwise_all)} unique CatWISE2020 sources to {catwise_raw_file.name}", flush=True)

# 2.3 2MASS PSC & ALLWISE FOR 45 FALSE POSITIVES
twomass_raw_file = RAW_CAT_DIR / "twomass_raw_fps.csv"
allwise_raw_file = RAW_CAT_DIR / "allwise_raw_fps.csv"

if twomass_raw_file.exists():
    df_twomass_fps = pd.read_csv(twomass_raw_file)
else:
    print(f"Querying NASA/IPAC IRSA TAP for 2MASS PSC across 45 false positives...", flush=True)
    tm_list = []
    for idx, r in fps_df.iterrows():
        t_id = r["trial_id"]
        c_ra = r["center_ra_deg"]
        c_dec = r["center_dec_deg"]
        adql = f"""
        SELECT designation, ra, dec, j_m, h_m, k_m, ph_qual, rd_flg, cc_flg
        FROM fp_psc
        WHERE CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {c_ra:.5f}, {c_dec:.5f}, 0.16)) = 1
        """
        params = {"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "CSV", "QUERY": adql}
        t0 = time.time()
        try:
            req = urllib.request.Request(f"https://irsa.ipac.caltech.edu/TAP/sync?{urllib.parse.urlencode(params)}", headers={"User-Agent": "SPECTRA-X-Task4.19B/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                df_res = pd.read_csv(resp)
                if "designation" in df_res.columns:
                    tm_list.append(df_res)
                    record_manifest("NASA_IPAC_IRSA_2MASS", "https://irsa.ipac.caltech.edu/TAP/sync", adql[:150], len(df_res), time.time()-t0, "SUCCESS")
        except Exception as e:
            record_failure("NASA_IPAC_IRSA_2MASS", "https://irsa.ipac.caltech.edu/TAP/sync", adql[:150], type(e).__name__, str(e))
        time.sleep(0.3)
    if tm_list:
        df_twomass_fps = pd.concat(tm_list, ignore_index=True).drop_duplicates(subset=["designation"]).reset_index(drop=True)
    else:
        df_twomass_fps = pd.DataFrame(columns=["designation", "ra", "dec", "j_m", "h_m", "k_m", "ph_qual"])
    df_twomass_fps.to_csv(twomass_raw_file, index=False)
    print(f"Saved {len(df_twomass_fps)} 2MASS records for false positives.", flush=True)

df_twomass_all = pd.concat([df_twomass_base, df_twomass_fps], ignore_index=True).drop_duplicates(subset=["designation"]).reset_index(drop=True)

# Save Acquisition Manifest & Failures
with open(OUT_DIR / "catalog_acquisition_manifest.json", "w") as f:
    json.dump(acquisition_manifest, f, indent=2)

df_failures = pd.DataFrame(acquisition_failures)
df_failures.to_csv(OUT_DIR / "catalog_acquisition_failures.csv", index=False)
print(f"Saved acquisition manifest ({len(acquisition_manifest)} queries) and failures ({len(df_failures)} logs).", flush=True)

# -----------------------------------------------------------------------------
# 3. PHASE C: EXACT-FOOTPRINT WCS CROSSMATCH & EPOCH PROPAGATION
# -----------------------------------------------------------------------------
print("\n=== 3. Phase C: Exact-Footprint Crossmatch & Astrometric Epoch Propagation ===", flush=True)

# Propagate Gaia astrometry to SPHEREx observation epoch (2026.5496)
print(f"Propagating Gaia DR3 coordinates (J2016.0 -> {SPHEREX_EPOCH:.4f}, dt = {DT_GAIA:.4f} yr)...", flush=True)
g_ra = df_gaia_all["ra"].values.copy()
g_dec = df_gaia_all["dec"].values.copy()
has_g_pm = df_gaia_all["pmra"].notna() & df_gaia_all["pmdec"].notna()

cos_dec = np.cos(np.radians(g_dec[has_g_pm]))
g_dec[has_g_pm] += (df_gaia_all.loc[has_g_pm, "pmdec"].values * DT_GAIA) / (3600.0 * 1000.0)
g_ra[has_g_pm] += ((df_gaia_all.loc[has_g_pm, "pmra"].values * DT_GAIA) / (3600.0 * 1000.0)) / cos_dec

df_gaia_all["ra_epoch2026"] = g_ra
df_gaia_all["dec_epoch2026"] = g_dec

# Helper for 3D KD-Tree
def radec_to_xyz(ra_deg, dec_deg):
    ra_rad = np.radians(ra_deg)
    dec_rad = np.radians(dec_deg)
    return np.column_stack([
        np.cos(dec_rad) * np.cos(ra_rad),
        np.cos(dec_rad) * np.sin(ra_rad),
        np.sin(dec_rad)
    ])

print("Building KD-Trees on unit sphere for fast cutout candidate matching...", flush=True)
gaia_xyz = radec_to_xyz(df_gaia_all["ra_epoch2026"].values, df_gaia_all["dec_epoch2026"].values)
gaia_tree = cKDTree(gaia_xyz)

if len(df_catwise_all) > 0:
    cw_ra = df_catwise_all["ra"].values.copy()
    cw_dec = df_catwise_all["dec"].values.copy()
    has_cw_pm = df_catwise_all["pmra"].notna() & df_catwise_all["pmdec"].notna()
    cos_cw_dec = np.cos(np.radians(cw_dec[has_cw_pm]))
    cw_dec[has_cw_pm] += (df_catwise_all.loc[has_cw_pm, "pmdec"].values * DT_CATWISE) / (3600.0 * 1000.0)
    cw_ra[has_cw_pm] += ((df_catwise_all.loc[has_cw_pm, "pmra"].values * DT_CATWISE) / (3600.0 * 1000.0)) / cos_cw_dec
    df_catwise_all["ra_epoch2026"] = cw_ra
    df_catwise_all["dec_epoch2026"] = cw_dec
    catwise_xyz = radec_to_xyz(cw_ra, cw_dec)
    catwise_tree = cKDTree(catwise_xyz)
else:
    catwise_tree = None

if len(df_twomass_all) > 0:
    twomass_xyz = radec_to_xyz(df_twomass_all["ra"].values, df_twomass_all["dec"].values)
    twomass_tree = cKDTree(twomass_xyz)
else:
    twomass_tree = None

# Save Unified Catalog Source Records
unified_catalog_records = []
for idx, r in df_gaia_all.iterrows():
    unified_catalog_records.append({
        "catalog": "GAIA_DR3",
        "source_id": str(r["source_id"]),
        "ra_orig": r["ra"],
        "dec_orig": r["dec"],
        "ra_epoch2026": r["ra_epoch2026"],
        "dec_epoch2026": r["dec_epoch2026"],
        "phot_primary": r["phot_g_mean_mag"],
        "phot_primary_band": "G",
        "pmra": r["pmra"],
        "pmdec": r["pmdec"],
        "ruwe": r["ruwe"]
    })

if len(df_catwise_all) > 0:
    for idx, r in df_catwise_all.iterrows():
        unified_catalog_records.append({
            "catalog": "CATWISE2020",
            "source_id": str(r["source_id"]),
            "ra_orig": r["ra"],
            "dec_orig": r["dec"],
            "ra_epoch2026": r["ra_epoch2026"],
            "dec_epoch2026": r["dec_epoch2026"],
            "phot_primary": r["w1mpro"],
            "phot_primary_band": "W1",
            "pmra": r["pmra"],
            "pmdec": r["pmdec"],
            "ruwe": None
        })

df_unified_sources = pd.DataFrame(unified_catalog_records)
df_unified_sources.to_csv(OUT_DIR / "catalog_source_records.csv", index=False)
print(f"Saved {len(df_unified_sources)} unified catalog source records to catalog_source_records.csv", flush=True)

# -----------------------------------------------------------------------------
# 4. PERFORM EXACT-FOOTPRINT MATCHING ACROSS ALL 1,500 CUTOUTS
# -----------------------------------------------------------------------------
print("\n--- Evaluating Exact WCS Footprints for N = 1,500 Cutouts ---", flush=True)

r_cand_rad = np.deg2rad(CUTOUT_RADIUS_ARCSEC / 3600.0)
r_cand_euc = 2.0 * np.sin(r_cand_rad / 2.0)

cutout_coverage_rows = []
exact_crossmatch_rows = []

for idx, tr in eval_pilot.iterrows():
    t_id = tr["trial_id"]
    p_id = f"P{tr['pointing']:04d}"
    det_id = tr["detector"]
    part = tr["partition"]
    frel = tr["fits_relpath"]
    
    cx_full = float(tr["center_pixel_x"])
    cy_full = float(tr["center_pixel_y"])
    c_ra = float(tr["center_ra"])
    c_dec = float(tr["center_dec"])
    
    w = wcs_cache[frel]
    
    xmin = cx_full - 64.0
    xmax = cx_full + 64.0
    ymin = cy_full - 64.0
    ymax = cy_full + 64.0
    
    cut_xyz = radec_to_xyz(np.array([c_ra]), np.array([c_dec]))
    
    # 1. Gaia Sources in Cutout
    gaia_cand_idx = gaia_tree.query_ball_point(cut_xyz[0], r=r_cand_euc)
    exact_gaia_sources = []
    has_gaia_center = False
    
    if len(gaia_cand_idx) > 0:
        cand_gaia = df_gaia_all.iloc[gaia_cand_idx]
        pxs, pys = w.all_world2pix(cand_gaia["ra_epoch2026"].values, cand_gaia["dec_epoch2026"].values, 0)
        in_box = (pxs >= xmin) & (pxs < xmax) & (pys >= ymin) & (pys < ymax)
        
        for g_i, (is_in, px, py) in enumerate(zip(in_box, pxs, pys)):
            if is_in:
                g_row = cand_gaia.iloc[g_i]
                d_pix = np.sqrt((px - cx_full)**2 + (py - cy_full)**2)
                d_arcsec = d_pix * 6.2285
                exact_gaia_sources.append({
                    "source_id": str(g_row["source_id"]),
                    "dist_pix": d_pix,
                    "dist_arcsec": d_arcsec
                })
                if d_arcsec <= 2.0:
                    m_class = "CONFIRMED_QUALITY_MATCH"
                    has_gaia_center = True
                elif d_arcsec <= 3.0:
                    m_class = "PROBABLE_MATCH"
                    has_gaia_center = True
                else:
                    m_class = "IN_FOOTPRINT_OFFCENTER_SOURCE"
                    
                exact_crossmatch_rows.append({
                    "trial_id": t_id,
                    "pointing_id": p_id,
                    "detector_id": det_id,
                    "catalog": "GAIA_DR3",
                    "catalog_source_id": str(g_row["source_id"]),
                    "pixel_x_cutout": round(px - xmin, 2),
                    "pixel_y_cutout": round(py - ymin, 2),
                    "separation_pixels": round(d_pix, 2),
                    "separation_arcsec": round(d_arcsec, 2),
                    "photometry_primary": g_row["phot_g_mean_mag"],
                    "match_classification": m_class
                })
                
    exact_g_count = len(exact_gaia_sources)
    
    # 2. 2MASS Sources in Cutout
    exact_tm_count = 0
    if twomass_tree is not None:
        tm_cand_idx = twomass_tree.query_ball_point(cut_xyz[0], r=r_cand_euc)
        if len(tm_cand_idx) > 0:
            cand_tm = df_twomass_all.iloc[tm_cand_idx]
            pxs_tm, pys_tm = w.all_world2pix(cand_tm["ra"].values, cand_tm["dec"].values, 0)
            in_box_tm = (pxs_tm >= xmin) & (pxs_tm < xmax) & (pys_tm >= ymin) & (pys_tm < ymax)
            exact_tm_count = int(in_box_tm.sum())
            for tm_i, (is_in, px, py) in enumerate(zip(in_box_tm, pxs_tm, pys_tm)):
                if is_in:
                    tm_row = cand_tm.iloc[tm_i]
                    d_pix = np.sqrt((px - cx_full)**2 + (py - cy_full)**2)
                    d_arcsec = d_pix * 6.2285
                    m_class = "CONFIRMED_QUALITY_MATCH" if d_arcsec <= 2.0 else ("PROBABLE_MATCH" if d_arcsec <= 3.0 else "IN_FOOTPRINT_OFFCENTER_SOURCE")
                    exact_crossmatch_rows.append({
                        "trial_id": t_id,
                        "pointing_id": p_id,
                        "detector_id": det_id,
                        "catalog": "2MASS_PSC",
                        "catalog_source_id": str(tm_row["designation"]),
                        "pixel_x_cutout": round(px - xmin, 2),
                        "pixel_y_cutout": round(py - ymin, 2),
                        "separation_pixels": round(d_pix, 2),
                        "separation_arcsec": round(d_arcsec, 2),
                        "photometry_primary": tm_row.get("j_m", np.nan),
                        "match_classification": m_class
                    })

    # 3. CatWISE Sources in Cutout
    exact_cw_count = 0
    if catwise_tree is not None:
        cw_cand_idx = catwise_tree.query_ball_point(cut_xyz[0], r=r_cand_euc)
        if len(cw_cand_idx) > 0:
            cand_cw = df_catwise_all.iloc[cw_cand_idx]
            pxs_cw, pys_cw = w.all_world2pix(cand_cw["ra_epoch2026"].values, cand_cw["dec_epoch2026"].values, 0)
            in_box_cw = (pxs_cw >= xmin) & (pxs_cw < xmax) & (pys_cw >= ymin) & (pys_cw < ymax)
            exact_cw_count = int(in_box_cw.sum())
            for cw_i, (is_in, px, py) in enumerate(zip(in_box_cw, pxs_cw, pys_cw)):
                if is_in:
                    cw_row = cand_cw.iloc[cw_i]
                    d_pix = np.sqrt((px - cx_full)**2 + (py - cy_full)**2)
                    d_arcsec = d_pix * 6.2285
                    m_class = "CONFIRMED_QUALITY_MATCH" if d_arcsec <= 2.0 else ("PROBABLE_MATCH" if d_arcsec <= 3.0 else "IN_FOOTPRINT_OFFCENTER_SOURCE")
                    exact_crossmatch_rows.append({
                        "trial_id": t_id,
                        "pointing_id": p_id,
                        "detector_id": det_id,
                        "catalog": "CATWISE2020",
                        "catalog_source_id": str(cw_row["source_id"]),
                        "pixel_x_cutout": round(px - xmin, 2),
                        "pixel_y_cutout": round(py - ymin, 2),
                        "separation_pixels": round(d_pix, 2),
                        "separation_arcsec": round(d_arcsec, 2),
                        "photometry_primary": cw_row.get("w1mpro", np.nan),
                        "match_classification": m_class
                    })

    has_gaia = bool(exact_g_count > 0)
    has_tm = bool(exact_tm_count > 0)
    has_cw = bool(exact_cw_count > 0)
    has_any = bool(has_gaia or has_tm or has_cw)
    has_dual = bool(has_gaia and has_tm)
    
    if exact_g_count >= 5 and exact_tm_count >= 1:
        c_status = "CONFIRMED_EXACT_CATALOG_COVERAGE"
    elif has_any:
        c_status = "PARTIAL_EXACT_CATALOG_COVERAGE"
    else:
        c_status = "NO_LOCAL_CATALOG_COUNTERPART"

    if exact_g_count > 0:
        min_g_dist = min(s["dist_arcsec"] for s in exact_gaia_sources)
        nearest_g_id = [s["source_id"] for s in exact_gaia_sources if s["dist_arcsec"] == min_g_dist][0]
    else:
        min_g_dist = np.nan
        nearest_g_id = "NONE"

    cutout_coverage_rows.append({
        "trial_id": t_id,
        "pointing_id": p_id,
        "detector_id": det_id,
        "partition": part,
        "center_ra_deg": c_ra,
        "center_dec_deg": c_dec,
        "exact_footprint_shape": "128x128_pixels_box",
        "exact_gaia_source_count": exact_g_count,
        "exact_twomass_source_count": exact_tm_count,
        "exact_catwise_source_count": exact_cw_count,
        "total_external_sources_in_box": exact_g_count + exact_tm_count + exact_cw_count,
        "has_exact_gaia_coverage": has_gaia,
        "has_exact_twomass_coverage": has_tm,
        "has_exact_catwise_coverage": has_cw,
        "has_exact_any_coverage": has_any,
        "has_exact_dual_coverage": has_dual,
        "nearest_gaia_source_id": nearest_g_id,
        "nearest_gaia_dist_arcsec": round(min_g_dist, 2) if not np.isnan(min_g_dist) else None,
        "has_center_catalog_counterpart": has_gaia_center,
        "coverage_classification": c_status
    })

df_cutout_cov = pd.DataFrame(cutout_coverage_rows)
df_cutout_cov.to_csv(OUT_DIR / "cutout_coverage_summary.csv", index=False)
print(f"Saved {len(df_cutout_cov)} cutout coverage records to cutout_coverage_summary.csv", flush=True)

df_crossmatch = pd.DataFrame(exact_crossmatch_rows)
df_crossmatch.to_csv(OUT_DIR / "exact_footprint_crossmatch.csv", index=False)
print(f"Saved {len(df_crossmatch)} exact-footprint crossmatches to exact_footprint_crossmatch.csv", flush=True)

# -----------------------------------------------------------------------------
# 5. PHASE D: EMPIRICAL COVERAGE MEASUREMENT & STRATIFICATION
# -----------------------------------------------------------------------------
print("\n=== 4. Phase D: Empirical Coverage Measurement & Confidence Intervals ===", flush=True)

def wilson_score_interval(successes: int, trials: int, confidence: float = 0.95) -> Tuple[float, float]:
    if trials == 0:
        return 0.0, 0.0
    z = 1.95996
    p = successes / trials
    denom = 1.0 + (z**2) / trials
    center = (p + (z**2) / (2 * trials)) / denom
    margin = (z / denom) * np.sqrt((p * (1.0 - p) / trials) + ((z**2) / (4 * trials**2)))
    ci_lower = max(0.0, (center - margin) * 100.0)
    ci_upper = min(100.0, (center + margin) * 100.0)
    return round(ci_lower, 2), round(ci_upper, 2)

detector_summary_rows = []

def audit_stratum(sub: pd.DataFrame, name: str, s_type: str) -> Dict[str, Any]:
    n_tot = len(sub)
    n_g = int(sub["has_exact_gaia_coverage"].sum())
    n_tm = int(sub["has_exact_twomass_coverage"].sum())
    n_cw = int(sub["has_exact_catwise_coverage"].sum())
    n_any = int(sub["has_exact_any_coverage"].sum())
    n_dual = int(sub["has_exact_dual_coverage"].sum())
    
    pct_g = round(n_g / n_tot * 100.0, 2)
    pct_tm = round(n_tm / n_tot * 100.0, 2)
    pct_cw = round(n_cw / n_tot * 100.0, 2)
    pct_any = round(n_any / n_tot * 100.0, 2)
    pct_dual = round(n_dual / n_tot * 100.0, 2)
    
    ci_l, ci_u = wilson_score_interval(n_any, n_tot)
    
    return {
        "stratum_name": name,
        "stratum_type": s_type,
        "total_cutouts": n_tot,
        "gaia_covered_count": n_g,
        "gaia_coverage_pct": pct_g,
        "twomass_covered_count": n_tm,
        "twomass_coverage_pct": pct_tm,
        "catwise_covered_count": n_cw,
        "catwise_coverage_pct": pct_cw,
        "any_covered_count": n_any,
        "any_coverage_pct": pct_any,
        "dual_covered_count": n_dual,
        "dual_coverage_pct": pct_dual,
        "ci_95_wilson_lower": ci_l,
        "ci_95_wilson_upper": ci_u,
        "target_90pct_met": bool(pct_any >= 90.0)
    }

detector_summary_rows.append(audit_stratum(df_cutout_cov, "OVERALL_EVALUATION_COHORT", "COHORT_TOTAL"))
for part in ["EVALUATION_CONTROL", "EVALUATION_POINT_SOURCE_INJECTION", "EVALUATION_EXTENDED_SOURCE_INJECTION"]:
    detector_summary_rows.append(audit_stratum(df_cutout_cov[df_cutout_cov["partition"] == part], part, "PARTITION"))
for p in ["P0002", "P0009", "P0010"]:
    detector_summary_rows.append(audit_stratum(df_cutout_cov[df_cutout_cov["pointing_id"] == p], p, "POINTING"))
for d in ["D1", "D2", "D3", "D4", "D5", "D6"]:
    detector_summary_rows.append(audit_stratum(df_cutout_cov[df_cutout_cov["detector_id"] == d], f"DETECTOR_{d}", "DETECTOR"))

df_detector_cov = pd.DataFrame(detector_summary_rows)
df_detector_cov.to_csv(OUT_DIR / "detector_stratified_coverage.csv", index=False)
print(f"Saved detector stratified coverage to detector_stratified_coverage.csv", flush=True)

comb_rows = []
n_all = len(df_cutout_cov)
ctrls = df_cutout_cov[df_cutout_cov["partition"] == "EVALUATION_CONTROL"]
n_ctrl = len(ctrls)

comb_defs = [
    ("Gaia DR3 Only", df_cutout_cov["has_exact_gaia_coverage"], ctrls["has_exact_gaia_coverage"]),
    ("2MASS PSC Only", df_cutout_cov["has_exact_twomass_coverage"], ctrls["has_exact_twomass_coverage"]),
    ("CatWISE2020 Only", df_cutout_cov["has_exact_catwise_coverage"], ctrls["has_exact_catwise_coverage"]),
    ("Gaia + 2MASS PSC", df_cutout_cov["has_exact_gaia_coverage"] | df_cutout_cov["has_exact_twomass_coverage"],
                         ctrls["has_exact_gaia_coverage"] | ctrls["has_exact_twomass_coverage"]),
    ("Gaia + CatWISE2020", df_cutout_cov["has_exact_gaia_coverage"] | df_cutout_cov["has_exact_catwise_coverage"],
                           ctrls["has_exact_gaia_coverage"] | ctrls["has_exact_catwise_coverage"]),
    ("Gaia + CatWISE2020 + 2MASS (Tier 1)", df_cutout_cov["has_exact_any_coverage"], ctrls["has_exact_any_coverage"]),
    ("All Available External Catalogs", df_cutout_cov["has_exact_any_coverage"], ctrls["has_exact_any_coverage"])
]

for name, mask_all, mask_ctrl in comb_defs:
    c_all = int(mask_all.sum())
    c_ctrl = int(mask_ctrl.sum())
    pct_all = round(c_all / n_all * 100.0, 2)
    pct_ctrl = round(c_ctrl / n_ctrl * 100.0, 2)
    ci_l, ci_u = wilson_score_interval(c_ctrl, n_ctrl)
    comb_rows.append({
        "catalog_combination": name,
        "all_cutouts_covered_count": c_all,
        "all_cutouts_total": n_all,
        "all_cutouts_coverage_pct": pct_all,
        "control_covered_count": c_ctrl,
        "control_total": n_ctrl,
        "control_coverage_pct": pct_ctrl,
        "control_95_ci_lower": ci_l,
        "control_95_ci_upper": ci_u,
        "delta_pp_vs_task_4_17_baseline": round(pct_ctrl - 33.20, 2)
    })

df_comb_cov = pd.DataFrame(comb_rows)
df_comb_cov.to_csv(OUT_DIR / "catalog_combination_coverage.csv", index=False)
print(f"Saved catalog combination coverage to catalog_combination_coverage.csv", flush=True)

# -----------------------------------------------------------------------------
# 6. PHASE E: ASTROVISION FALSE-POSITIVE EXTERNAL EVIDENCE AUDIT (N = 45)
# -----------------------------------------------------------------------------
print("\n=== 5. Phase E: ASTROVISION False-Positive Evidence Audit (N = 45) ===", flush=True)

df_fp_4_18 = pd.read_csv("reports/phase4/task_4_18/false_positive_catalog_attribution.csv")
fp_audit_rows = []

for idx, r in df_fp_4_18.iterrows():
    t_id = r["trial_id"]
    p_id = r["pointing_id"]
    d_id = r["detector_id"]
    
    c_rec = df_cutout_cov[df_cutout_cov["trial_id"] == t_id].iloc[0]
    g_count = c_rec["exact_gaia_source_count"]
    tm_count = c_rec["exact_twomass_source_count"]
    cw_count = c_rec["exact_catwise_source_count"]
    tot_ext = c_rec["total_external_sources_in_box"]
    
    matches = [m for m in exact_crossmatch_rows if m["trial_id"] == t_id]
    
    if len(matches) > 0:
        matches_sorted = sorted(matches, key=lambda x: x["separation_arcsec"])
        best_m = matches_sorted[0]
        best_cat = best_m["catalog"]
        best_id = best_m["catalog_source_id"]
        best_sep_arcsec = best_m["separation_arcsec"]
        best_sep_pix = best_m["separation_pixels"]
        best_phot = best_m["photometry_primary"]
        
        if best_sep_arcsec <= 2.0:
            assoc_cat = "PLAUSIBLE_CATALOG_ASSOCIATION"
            causal_interp = "CENTRAL_BRIGHT_OR_NEAR_CENTER_STELLAR_SOURCE"
        elif best_sep_arcsec <= 15.0:
            assoc_cat = "POSSIBLE_ASSOCIATION"
            causal_interp = "OFF_CENTER_STELLAR_POINT_SPREAD_CONTAMINATION"
        elif tot_ext >= 1:
            assoc_cat = "AMBIGUOUS_ASSOCIATION"
            causal_interp = "DIFFUSE_OFF_CENTER_STELLAR_FIELD_CROWDING"
        else:
            assoc_cat = "UNVERIFIABLE"
            causal_interp = "UNRESOLVED_FAINT_OR_TRANSIENT_SYSTEMATIC"
    else:
        best_cat = "NONE"
        best_id = "NONE"
        best_sep_arcsec = np.nan
        best_sep_pix = np.nan
        best_phot = np.nan
        assoc_cat = "NO_LOCAL_CATALOG_COUNTERPART"
        causal_interp = "DETECTOR_SYSTEMATIC_OR_SUB_THRESHOLD_VOID"

    fp_audit_rows.append({
        "trial_id": t_id,
        "pointing_id": p_id,
        "detector_id": d_id,
        "baseline_peak_chi2": r["baseline_peak_chi2"],
        "detection_threshold_tau": r["detection_threshold_tau"],
        "shadow_suppressed": r["false_alarm_suppressed"],
        "exact_gaia_source_count": g_count,
        "exact_twomass_source_count": tm_count,
        "exact_catwise_source_count": cw_count,
        "total_external_sources_in_box": tot_ext,
        "nearest_catalog": best_cat,
        "nearest_catalog_source_id": best_id,
        "nearest_source_sep_arcsec": best_sep_arcsec,
        "nearest_source_sep_pixels": best_sep_pix,
        "nearest_source_photometry": best_phot,
        "evidence_association_category": assoc_cat,
        "causal_interpretation": causal_interp
    })

df_fp_audit = pd.DataFrame(fp_audit_rows)
df_fp_audit.to_csv(OUT_DIR / "false_positive_external_evidence_audit.csv", index=False)
print(f"Saved false positive evidence audit (N = {len(df_fp_audit)}) to false_positive_external_evidence_audit.csv", flush=True)

# -----------------------------------------------------------------------------
# 7. PHASE F: TASK 4.19A PROJECTION VERIFICATION
# -----------------------------------------------------------------------------
print("\n=== 6. Phase F: Task 4.19A Projection Verification ===", flush=True)

actual_gaia_ctrl = float(df_comb_cov[df_comb_cov["catalog_combination"] == "Gaia DR3 Only"]["control_coverage_pct"].iloc[0])
actual_tier1_ctrl = float(df_comb_cov[df_comb_cov["catalog_combination"] == "Gaia + CatWISE2020 + 2MASS (Tier 1)"]["control_coverage_pct"].iloc[0])
actual_fp_cov = round((df_fp_audit["total_external_sources_in_box"] > 0).mean() * 100.0, 2)

def verify_proj(claim_name: str, target_desc: str, proj_val: float, act_val: float, tol_pp: float = 3.0) -> Dict[str, Any]:
    diff = round(act_val - proj_val, 2)
    if abs(diff) <= tol_pp:
        status = "EMPIRICALLY_SUPPORTED"
    elif act_val >= proj_val * 0.85:
        status = "PARTIALLY_SUPPORTED"
    else:
        status = "NOT_SUPPORTED"
        
    return {
        "projection_claim": claim_name,
        "target_metric": target_desc,
        "projected_coverage_pct": proj_val,
        "empirically_measured_coverage_pct": act_val,
        "difference_percentage_points": diff,
        "verification_verdict": status
    }

proj_rows = [
    verify_proj("Tier 1A: Expanded Gaia DR3", "Control Cutout Coverage (N=500)", 82.40, actual_gaia_ctrl),
    verify_proj("Tier 1C: Gaia + CatWISE + 2MASS", "Control Cutout Coverage (N=500)", 92.40, actual_tier1_ctrl),
    verify_proj("Tier 1D: Expanded All-Catalog", "Control Cutout Coverage (N=500)", 93.60, actual_tier1_ctrl),
    verify_proj("Baseline False Positive Coverage", "False Positive External Sources (N=45)", 93.33, actual_fp_cov)
]

df_proj = pd.DataFrame(proj_rows)
df_proj.to_csv(OUT_DIR / "task_4_19A_projection_verification.csv", index=False)
print(f"Saved projection verification to task_4_19A_projection_verification.csv", flush=True)

# -----------------------------------------------------------------------------
# 8. PRINT SUMMARY TABLE
# -----------------------------------------------------------------------------
print("\n" + "="*80, flush=True)
print("TASK 4.19B FINAL EMPIRICAL SUMMARY", flush=True)
print("="*80, flush=True)
print(f"Total Cutouts Evaluated: {n_all}", flush=True)
print(f"Overall Catalog Coverage (All 1500): {(df_cutout_cov['has_exact_any_coverage']).sum()} / {n_all} ({(df_cutout_cov['has_exact_any_coverage']).mean()*100:.2f}%)", flush=True)
print(f"Null Controls Coverage (N = 500): {(ctrls['has_exact_any_coverage']).sum()} / {n_ctrl} ({(ctrls['has_exact_any_coverage']).mean()*100:.2f}%) [Task 4.17 baseline: 33.20%]", flush=True)
print(f"Baseline False Positives with External Counterparts (N = 45): {int((df_fp_audit['total_external_sources_in_box'] > 0).sum())} / 45 ({actual_fp_cov:.2f}%) [Task 4.17 baseline: 26.67%]", flush=True)
print(f"Plausible / Possible Associations on FPs: {int(((df_fp_audit['evidence_association_category'] == 'PLAUSIBLE_CATALOG_ASSOCIATION') | (df_fp_audit['evidence_association_category'] == 'POSSIBLE_ASSOCIATION')).sum())} / 45", flush=True)
print(f"Remaining FPs without External Counterparts: {int((df_fp_audit['evidence_association_category'] == 'NO_LOCAL_CATALOG_COUNTERPART').sum())} / 45", flush=True)
print("="*80, flush=True)
