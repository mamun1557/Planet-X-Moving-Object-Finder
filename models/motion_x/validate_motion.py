"""
MOTION-X Validation Pipeline
Validates proper motions and minor planet ephemerides against Gaia DR3 and JPL Horizons.
"""

import os
import glob
import pandas as pd
from model import MotionXValidator


def run_motion_validation():
    gaia_path = "data/external/gaia_dr3/gaia_dr3_reference_stars.csv"
    if os.path.exists(gaia_path):
        gaia_df = pd.read_csv(gaia_path)
        print(f"Loaded {len(gaia_df)} Gaia DR3 reference stars.")
    else:
        gaia_df = None
        print("Gaia DR3 catalog not found yet.")

    validator = MotionXValidator(gaia_df=gaia_df)

    # Check temporal candidates if available
    cand_path = "data/processed/temporal_pairs/temporal_candidates.csv"
    out_dir = "data/processed/motion_tracks"
    os.makedirs(out_dir, exist_ok=True)

    if os.path.exists(cand_path):
        df_cand = pd.read_csv(cand_path)
        matches = []
        for _, row in df_cand.iterrows():
            ra, dec = row["ra"], row["dec"]
            m = validator.crossmatch_gaia(ra, dec, match_radius_arcsec=3.0)
            if m:
                row_dict = row.to_dict()
                row_dict.update(m)
                matches.append(row_dict)

        df_matches = pd.DataFrame(matches)
        out_csv = os.path.join(out_dir, "gaia_matched_detections.csv")
        df_matches.to_csv(out_csv, index=False)
        print(f"Matched {len(matches)} detections against Gaia DR3 astrometric stars.")
    else:
        print("No temporal candidates found yet to match.")


if __name__ == "__main__":
    run_motion_validation()
