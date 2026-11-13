"""
CHRONOS-X Temporal Differencing Pipeline
Detects temporal changes, transients, and moving objects between verified multi-epoch pairs.
"""

import os
import sys
import glob
import pandas as pd
import numpy as np
from astropy.io import fits

sys.path.insert(0, os.path.abspath("scripts"))
sys.path.insert(0, os.path.abspath("models/chronos_x"))
import inspect_fits
from model import ChronosTemporalDifferencer


def execute_temporal_differencing():
    catalog_path = "manifests/fits_validation_catalog.csv"
    if not os.path.exists(catalog_path):
        print(f"Catalog {catalog_path} not found. Running inspect_fits...")
        inspect_fits.inspect_directory("data/spherex", catalog_path)

    df = pd.read_csv(catalog_path)
    pairs = inspect_fits.find_temporal_pairs(df)
    print(f"Found {len(pairs)} candidate multi-epoch temporal observation pairs. Processing first 5...")
    differencer = ChronosTemporalDifferencer(significance_threshold=5.0)

    out_dir = "data/processed/temporal_pairs"
    os.makedirs(out_dir, exist_ok=True)

    results = []
    for idx, p in enumerate(pairs[:5]):
        f1 = p["file_1"]
        f2 = p["file_2"]
        p1 = glob.glob(f"data/spherex/**/{f1}", recursive=True)
        p2 = glob.glob(f"data/spherex/**/{f2}", recursive=True)

        if p1 and p2:
            try:
                with fits.open(p1[0]) as h1, fits.open(p2[0]) as h2:
                    if "IMAGE" in h1 and "IMAGE" in h2:
                        res = differencer.align_and_difference(
                            img1=h1["IMAGE"].data,
                            hdr1=h1["IMAGE"].header,
                            var1=h1["VARIANCE"].data if "VARIANCE" in h1 else np.ones_like(h1["IMAGE"].data),
                            mask1=h1["FLAGS"].data if "FLAGS" in h1 else np.zeros_like(h1["IMAGE"].data, dtype=int),
                            img2=h2["IMAGE"].data,
                            hdr2=h2["IMAGE"].header,
                            var2=h2["VARIANCE"].data if "VARIANCE" in h2 else np.ones_like(h2["IMAGE"].data),
                            mask2=h2["FLAGS"].data if "FLAGS" in h2 else np.zeros_like(h2["IMAGE"].data, dtype=int)
                        )
                        p["max_significance"] = res["max_significance"]
                        p["candidate_pixels"] = res["candidate_pixels_count"]
                        p["monopolar_transients"] = res["monopolar_transients_count"]
                        p["dipole_artifacts"] = res["dipole_artifacts_count"]
                        p["bg_offset"] = res["background_offset"]
                        results.append(p)
                        print(f"Pair {idx+1}: {f1} vs {f2} (dt={p['dt_days']:.4f}d) -> Max Sig: {res['max_significance']:.2f} | Monopolar Transients: {res['monopolar_transients_count']} | Dipoles: {res['dipole_artifacts_count']}")
            except Exception as e:
                print(f"Error processing pair {idx+1}: {e}")

    df_out = pd.DataFrame(results if results else pairs)
    out_csv = os.path.join(out_dir, "temporal_candidates.csv")
    df_out.to_csv(out_csv, index=False)
    print(f"Saved temporal analysis report to {out_csv}")


if __name__ == "__main__":
    execute_temporal_differencing()
