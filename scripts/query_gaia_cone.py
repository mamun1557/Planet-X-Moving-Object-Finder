"""
SPECTRA-X: Gaia DR3 Cone Search Retrieval Script for Pointing 0003
NASA Space Apps Challenge 2026

Queries the official Gaia DR3 archive (via Astronomisches Rechen-Institut Heidelberg TAP)
for astrometric reference stars in the footprint of Pointing 0003.

Parameters:
- Center: RA = 165.6852 deg, Dec = -69.5651 deg
- Radius: 2.5 deg
- Magnitude: G <= 20.5 mag (or configurable top limit)
"""

import os
import requests
import time
import argparse
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GaiaConeRetriever")


def query_pointing_0003_gaia_cone(limit: int = 5000,
                                  ra: float = 165.6852,
                                  dec: float = -69.5651,
                                  radius_deg: float = 2.5,
                                  g_max: float = 20.5,
                                  out_csv: str = "data/external/gaia_dr3/gaia_pointing_0003_cone.csv"):
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    logger.info(f"Initiating Gaia DR3 cone search on Heidelberg TAP around ({ra}, {dec}) r={radius_deg} deg, limit={limit}...")

    # Fast indexed query syntax conforming to TAP ADQL standards
    adql_query = f"""
    SELECT TOP {limit} source_id, ra, dec, phot_g_mean_mag, pmra, pmdec, parallax, ruwe
    FROM gaiadr3.gaia_source
    WHERE 1=CONTAINS(POINT('ICRS', ra, dec), CIRCLE('ICRS', {ra}, {dec}, {radius_deg}))
      AND phot_g_mean_mag <= {g_max}
    """

    tap_endpoint = "https://gaia.ari.uni-heidelberg.de/tap/sync"
    params = {
        "REQUEST": "doQuery",
        "LANG": "ADQL",
        "FORMAT": "csv",
        "QUERY": adql_query
    }

    t0 = time.time()
    resp = requests.get(tap_endpoint, params=params, timeout=35)
    if resp.status_code == 200:
        lines = resp.text.strip().splitlines()
        rec_count = len(lines) - 1
        with open(out_csv, "w", encoding="utf-8") as f:
            f.write(resp.text)
        duration = time.time() - t0
        logger.info(f"Successfully retrieved {rec_count} Gaia DR3 reference stars in {duration:.2f}s -> {out_csv}")
        return out_csv
    else:
        logger.error(f"TAP query failed with HTTP {resp.status_code}: {resp.text[:200]}")
        return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5000, help="Maximum sources to retrieve")
    args = parser.parse_args()
    query_pointing_0003_gaia_cone(limit=args.limit)
