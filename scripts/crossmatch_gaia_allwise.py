"""
SPECTRA-X / F1 — Phase 2, Task 4
Data Retrieval & Spatial Cross-Matching Engine for Pointing 0003

Queries Gaia DR3 (Heidelberg ARI TAP) and AllWISE (NOIRLab Data Lab TAP)
for candidate counterparts within 4.0 arcsec of the 1,132 Pointing 0003 sources.
Performs proper-motion propagation to SPHEREx epoch (2026.5496).
Categorizes matches and computes astrophysical classification features.
"""

import os
import sys
import time
import math
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
import requests

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)

SPHEREx_EPOCH = 2026.5496  # Observation date: 2026-07-20T00:26:21 UTC (MJD 61241.018)
GAIA_EPOCH = 2016.0        # Gaia DR3 reference epoch J2016.0
ALLWISE_EPOCH = 2010.0     # AllWISE reference epoch J2010.0
DT_GAIA_SPHEREX = SPHEREx_EPOCH - GAIA_EPOCH  # 10.5496 years

SEARCH_RADIUS_ARCSEC = 4.0
SEARCH_RADIUS_DEG = SEARCH_RADIUS_ARCSEC / 3600.0

MATCH_DIR = os.path.join(BASE_DIR, "data", "processed", "crossmatch")
CLASS_DIR = os.path.join(BASE_DIR, "data", "processed", "classification")
GAIA_RAW_PATH = os.path.join(BASE_DIR, "data", "external", "gaia_dr3", "pointing_0003_gaia_dr3_candidates.csv")
ALLWISE_RAW_PATH = os.path.join(BASE_DIR, "data", "external", "allwise", "pointing_0003_allwise_candidates.csv")

os.makedirs(MATCH_DIR, exist_ok=True)
os.makedirs(CLASS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(GAIA_RAW_PATH), exist_ok=True)
os.makedirs(os.path.dirname(ALLWISE_RAW_PATH), exist_ok=True)


def angular_separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Computes exact spherical angular separation in arcseconds using Haversine formula."""
    r1, d1, r2, d2 = map(math.radians, [ra1, dec1, ra2, dec2])
    d_ra = r2 - r1
    d_dec = d2 - d1
    a = math.sin(d_dec / 2.0) ** 2 + math.cos(d1) * math.cos(d2) * math.sin(d_ra / 2.0) ** 2
    a = min(1.0, max(0.0, a))
    dist_rad = 2.0 * math.asin(math.sqrt(a))
    return math.degrees(dist_rad) * 3600.0


def propagate_gaia_coords(
    ra_deg: float,
    dec_deg: float,
    pmra_mas_yr: Optional[float],
    pmdec_mas_yr: Optional[float],
    dt_years: float = DT_GAIA_SPHEREX
) -> Tuple[float, float, bool]:
    """
    Propagates Gaia DR3 coordinates from J2016.0 to target observation epoch using proper motion.
    pmra is pmra* = pmra * cos(dec) in mas/yr.
    """
    if pmra_mas_yr is None or pmdec_mas_yr is None or np.isnan(pmra_mas_yr) or np.isnan(pmdec_mas_yr):
        return ra_deg, dec_deg, False

    cos_dec = math.cos(math.radians(dec_deg))
    if abs(cos_dec) < 1e-6:
        return ra_deg, dec_deg, False

    delta_ra_deg = (pmra_mas_yr * 1e-3 * dt_years) / (3600.0 * cos_dec)
    delta_dec_deg = (pmdec_mas_yr * 1e-3 * dt_years) / 3600.0

    ra_prop = (ra_deg + delta_ra_deg) % 360.0
    dec_prop = dec_deg + delta_dec_deg
    return ra_prop, dec_prop, True


def fetch_gaia_dr3_candidates(sources_df: pd.DataFrame, batch_size: int = 30) -> pd.DataFrame:
    """Queries Heidelberg ARI TAP for Gaia DR3 candidates around each SPHEREx source."""
    if os.path.exists(GAIA_RAW_PATH):
        print(f"Loading cached Gaia DR3 candidates from {GAIA_RAW_PATH}...")
        return pd.read_csv(GAIA_RAW_PATH)

    print(f"Querying Heidelberg ARI TAP for Gaia DR3 candidates ({len(sources_df)} sources in batches of {batch_size})...")
    url = "https://gaia.ari.uni-heidelberg.de/tap/sync"
    all_rows = []

    num_batches = math.ceil(len(sources_df) / batch_size)
    for b_idx in range(num_batches):
        batch = sources_df.iloc[b_idx * batch_size : (b_idx + 1) * batch_size]
        clauses = [
            f"1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {row['ra']:.6f}, {row['dec']:.6f}, {SEARCH_RADIUS_DEG:.8f}))"
            for _, row in batch.iterrows()
        ]
        where_sql = " OR \n".join(clauses)

        adql = f"""
        SELECT source_id, ra, dec, ra_error, dec_error, pmra, pmdec, pmra_error, pmdec_error,
               parallax, parallax_error, parallax_over_error,
               phot_g_mean_mag, phot_bp_mean_mag, phot_rp_mean_mag, bp_rp, ruwe
        FROM gaiadr3.gaia_source
        WHERE {where_sql}
        """

        for attempt in range(3):
            try:
                resp = requests.post(
                    url,
                    data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql},
                    timeout=35
                )
                if resp.status_code == 200:
                    lines = resp.text.strip().splitlines()
                    if len(lines) > 1:
                        from io import StringIO
                        batch_df = pd.read_csv(StringIO(resp.text))
                        all_rows.append(batch_df)
                    break
                else:
                    time.sleep(1.0)
            except Exception as e:
                time.sleep(2.0)

        if (b_idx + 1) % 10 == 0 or b_idx == num_batches - 1:
            print(f"  Gaia batch {b_idx + 1}/{num_batches} complete...")

    if all_rows:
        gaia_df = pd.concat(all_rows, ignore_index=True).drop_duplicates(subset=["source_id"]).reset_index(drop=True)
    else:
        gaia_df = pd.DataFrame()

    gaia_df.to_csv(GAIA_RAW_PATH, index=False)
    print(f"Saved {len(gaia_df)} unique Gaia DR3 candidates to {GAIA_RAW_PATH}")
    return gaia_df


def fetch_allwise_candidates(sources_df: pd.DataFrame, batch_size: int = 25) -> pd.DataFrame:
    """Queries NOIRLab Astro Data Lab TAP for AllWISE candidates around each SPHEREx source."""
    if os.path.exists(ALLWISE_RAW_PATH):
        print(f"Loading cached AllWISE candidates from {ALLWISE_RAW_PATH}...")
        return pd.read_csv(ALLWISE_RAW_PATH)

    print(f"Querying NOIRLab Data Lab TAP for AllWISE candidates ({len(sources_df)} sources in batches of {batch_size})...")
    url = "https://datalab.noirlab.edu/tap/sync"
    all_rows = []

    num_batches = math.ceil(len(sources_df) / batch_size)
    for b_idx in range(num_batches):
        batch = sources_df.iloc[b_idx * batch_size : (b_idx + 1) * batch_size]
        clauses = []
        for _, row in batch.iterrows():
            ra = row["ra"]
            dec = row["dec"]
            dra = SEARCH_RADIUS_DEG / 0.35  # Account for cos(dec ~ -69.5 deg) ~ 0.35
            ddec = SEARCH_RADIUS_DEG
            clauses.append(f"(ra BETWEEN {ra-dra:.6f} AND {ra+dra:.6f} AND dec BETWEEN {dec-ddec:.6f} AND {dec+ddec:.6f})")

        where_sql = " OR \n".join(clauses)

        adql = f"""
        SELECT designation, ra, dec, sigra, sigdec, w1mpro, w1sigmpro, w1snr, w2mpro, w2sigmpro, w2snr, cc_flags, ext_flg, ph_qual
        FROM allwise.source
        WHERE {where_sql}
        """

        for attempt in range(3):
            try:
                resp = requests.post(
                    url,
                    data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql},
                    timeout=35
                )
                if resp.status_code == 200:
                    lines = resp.text.strip().splitlines()
                    if len(lines) > 1:
                        from io import StringIO
                        batch_df = pd.read_csv(StringIO(resp.text))
                        all_rows.append(batch_df)
                    break
                else:
                    time.sleep(1.0)
            except Exception as e:
                time.sleep(2.0)

        if (b_idx + 1) % 10 == 0 or b_idx == num_batches - 1:
            print(f"  AllWISE batch {b_idx + 1}/{num_batches} complete...")

    if all_rows:
        wise_df = pd.concat(all_rows, ignore_index=True).drop_duplicates(subset=["designation"]).reset_index(drop=True)
    else:
        wise_df = pd.DataFrame()

    wise_df.to_csv(ALLWISE_RAW_PATH, index=False)
    print(f"Saved {len(wise_df)} unique AllWISE candidates to {ALLWISE_RAW_PATH}")
    return wise_df


if __name__ == "__main__":
    spx_path = os.path.join(BASE_DIR, "data", "processed", "benchmarks", "spectra_v2_source_scores.csv")
    spx_df = pd.read_csv(spx_path)
    print(f"Loaded {len(spx_df)} SPHEREx Pointing 0003 matched sources.")

    t0 = time.time()
    gaia_cand = fetch_gaia_dr3_candidates(spx_df, batch_size=30)
    wise_cand = fetch_allwise_candidates(spx_df, batch_size=25)
    print(f"\nCompleted catalog candidate queries in {time.time()-t0:.2f}s.")
