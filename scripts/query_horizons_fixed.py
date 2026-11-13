"""
SPECTRA-X: Fixed JPL Horizons Asteroid Ephemeris Retrieval Script
NASA Space Apps Challenge 2026

Fixes the major-planet target ID collision bug by enforcing small-body command syntax:
- 1; -> 1 Ceres (A801 AA)
- 2; -> 2 Pallas (A802 FA)
- 4; -> 4 Vesta (A807 FA)
- 433; -> 433 Eros (A898 PA)
- 99942; -> 99942 Apophis (2004 MN4)
"""

import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("HorizonsRetriever")


def retrieve_fixed_ephemerides():
    out_dir = "data/external/jpl_horizons"
    os.makedirs(out_dir, exist_ok=True)

    target_bodies = [
        ("1;", "ceres_1"),
        ("2;", "pallas_2"),
        ("4;", "vesta_4"),
        ("433;", "eros_433"),
        ("99942;", "apophis_99942")
    ]

    session = requests.Session()
    session.headers.update({"User-Agent": "SPECTRA-X-Scientific-Pipeline/1.0"})

    for cmd, fname in target_bodies:
        out_file = os.path.join(out_dir, f"horizons_ephem_{fname}.csv")
        logger.info(f"Querying JPL Horizons for command '{cmd}'...")

        params = {
            "format": "text",
            "COMMAND": f"'{cmd}'",
            "OBJ_DATA": "'YES'",
            "MAKE_EPHEM": "'YES'",
            "EPHEM_TYPE": "'OBSERVER'",
            "CENTER": "'500@399'",
            "START_TIME": "'2025-01-01'",
            "STOP_TIME": "'2026-12-31'",
            "STEP_SIZE": "'1d'",
            "QUANTITIES": "'1,3,9,20'"
        }

        try:
            resp = session.get("https://ssd.jpl.nasa.gov/api/horizons.api", params=params, timeout=25)
            if resp.status_code == 200:
                with open(out_file, "w", encoding="utf-8") as f:
                    f.write(resp.text)
                
                # Verify resolved target body
                resolved_name = "UNKNOWN"
                for line in resp.text.splitlines()[:25]:
                    if "Target body name:" in line or "JPL/HORIZONS" in line:
                        resolved_name = line.strip()
                        break
                logger.info(f"Successfully saved {out_file} -> {resolved_name}")
            else:
                logger.error(f"HTTP error {resp.status_code} querying {cmd}")
        except Exception as e:
            logger.error(f"Exception querying {cmd}: {e}")


if __name__ == "__main__":
    retrieve_fixed_ephemerides()
