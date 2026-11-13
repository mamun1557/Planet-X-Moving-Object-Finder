"""
SPECTRA-X / F1 — Phase 3, Task 1.1O
Five-Partition Controlled Pilot Benchmark Allocation Engine:
Generates the deterministic frozen partition manifest across the 5-pointing cohort.

Allocation:
- Calibration: Pointing 0001, Pointing 0008 (48 FITS products)
- Evaluation: Pointing 0002, Pointing 0009, Pointing 0010 (72 FITS products)

Partitions:
1. CALIBRATION_CONTROL
2. CALIBRATION_INJECTION
3. EVALUATION_CONTROL
4. EVALUATION_POINT_SOURCE_INJECTION
5. EVALUATION_EXTENDED_SOURCE_INJECTION

Zero Cross-Boundary Leakage:
Calibration pointings/files strictly isolated from Evaluation pointings/files.
Deterministic RNG with locked seed (seed=42).
"""

import os
import sys
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

LEVEL2_DIR = BASE_DIR / "data" / "spherex" / "multipointing_pilot" / "level2"
CAT_DIR = BASE_DIR / "data" / "processed" / "pilot_catalogues"
MANIFEST_DIR = BASE_DIR / "reports" / "manifests"
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

MANIFEST_CSV = MANIFEST_DIR / "astrovision_five_partition_pilot_manifest.csv"

CALIBRATION_POINTINGS = ["0001", "0008"]
EVALUATION_POINTINGS = ["0002", "0009", "0010"]

# Target trials per partition
N_TRIALS_PER_PARTITION = 500  # Total = 2,500 trials

SNR_GRID_CALIBRATION = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0]
SNR_GRID_EVALUATION = [3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0, 25.0]

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def get_pointing_files(pointings: List[str]) -> List[Dict[str, Any]]:
    records = []
    for p in pointings:
        p_dir = LEVEL2_DIR / p
        files = sorted(list(p_dir.glob("*.fits")))
        for f in files:
            parts = f.name.split("_")
            dither_det = parts[4]
            dither = int(dither_det[0])
            det_num = int(dither_det[2])
            records.append({
                "pointing": p,
                "detector": f"D{det_num}",
                "detector_num": det_num,
                "dither": dither,
                "filename": f.name,
                "path": f
            })
    return records

def generate_five_partition_manifest(seed: int = 42) -> pd.DataFrame:
    print(f"Generating Five-Partition Pilot Manifest (seed={seed}, {N_TRIALS_PER_PARTITION} trials/partition)...")
    rng = np.random.default_rng(seed)

    cal_files = get_pointing_files(CALIBRATION_POINTINGS)
    eval_files = get_pointing_files(EVALUATION_POINTINGS)

    # Pre-cache WCS objects
    wcs_cache = {}
    for item in cal_files + eval_files:
        with fits.open(item["path"]) as hdul:
            wcs_cache[item["filename"]] = WCS(hdul["IMAGE"].header)

    all_trials = []
    trial_counter = 1

    # -------------------------------------------------------------
    # 1. CALIBRATION_CONTROL (500 trials from P0001, P0008)
    # -------------------------------------------------------------
    print("  Allocating CALIBRATION_CONTROL trials...")
    # Evenly distribute among the 48 calibration FITS files
    for i in range(N_TRIALS_PER_PARTITION):
        f_info = cal_files[i % len(cal_files)]
        w = wcs_cache[f_info["filename"]]
        # Sample coordinates in active area avoiding margins [100, 1940]
        px = rng.uniform(100.0, 1940.0)
        py = rng.uniform(100.0, 1940.0)
        ra, dec = w.pixel_to_world_values(px, py)

        all_trials.append({
            "trial_id": f"PILOT_{trial_counter:06d}",
            "partition": "CALIBRATION_CONTROL",
            "role": "CALIBRATION",
            "pointing": f_info["pointing"],
            "detector": f_info["detector"],
            "detector_num": f_info["detector_num"],
            "dither": f_info["dither"],
            "fits_filename": f_info["filename"],
            "fits_relpath": f"data/spherex/multipointing_pilot/level2/{f_info['pointing']}/{f_info['filename']}",
            "center_pixel_x": round(float(px), 2),
            "center_pixel_y": round(float(py), 2),
            "center_ra": round(float(ra), 6),
            "center_dec": round(float(dec), 6),
            "target_snr": 0.0,
            "injection_class": "NONE",
            "source_type": "NULL_BACKGROUND",
            "mask_status": "VALID_UNMASKED"
        })
        trial_counter += 1

    # -------------------------------------------------------------
    # 2. CALIBRATION_INJECTION (500 trials from P0001, P0008)
    # -------------------------------------------------------------
    print("  Allocating CALIBRATION_INJECTION trials...")
    for i in range(N_TRIALS_PER_PARTITION):
        f_info = cal_files[i % len(cal_files)]
        w = wcs_cache[f_info["filename"]]
        px = rng.uniform(100.0, 1940.0)
        py = rng.uniform(100.0, 1940.0)
        ra, dec = w.pixel_to_world_values(px, py)
        snr = float(rng.choice(SNR_GRID_CALIBRATION))

        all_trials.append({
            "trial_id": f"PILOT_{trial_counter:06d}",
            "partition": "CALIBRATION_INJECTION",
            "role": "CALIBRATION",
            "pointing": f_info["pointing"],
            "detector": f_info["detector"],
            "detector_num": f_info["detector_num"],
            "dither": f_info["dither"],
            "fits_filename": f_info["filename"],
            "fits_relpath": f"data/spherex/multipointing_pilot/level2/{f_info['pointing']}/{f_info['filename']}",
            "center_pixel_x": round(float(px), 2),
            "center_pixel_y": round(float(py), 2),
            "center_ra": round(float(ra), 6),
            "center_dec": round(float(dec), 6),
            "target_snr": snr,
            "injection_class": "POINT_SOURCE",
            "source_type": "SYNTHETIC_POINT_SOURCE",
            "mask_status": "VALID_UNMASKED"
        })
        trial_counter += 1

    # -------------------------------------------------------------
    # 3. EVALUATION_CONTROL (500 trials from P0002, P0009, P0010)
    # -------------------------------------------------------------
    print("  Allocating EVALUATION_CONTROL trials...")
    for i in range(N_TRIALS_PER_PARTITION):
        f_info = eval_files[i % len(eval_files)]
        w = wcs_cache[f_info["filename"]]
        px = rng.uniform(100.0, 1940.0)
        py = rng.uniform(100.0, 1940.0)
        ra, dec = w.pixel_to_world_values(px, py)

        all_trials.append({
            "trial_id": f"PILOT_{trial_counter:06d}",
            "partition": "EVALUATION_CONTROL",
            "role": "EVALUATION",
            "pointing": f_info["pointing"],
            "detector": f_info["detector"],
            "detector_num": f_info["detector_num"],
            "dither": f_info["dither"],
            "fits_filename": f_info["filename"],
            "fits_relpath": f"data/spherex/multipointing_pilot/level2/{f_info['pointing']}/{f_info['filename']}",
            "center_pixel_x": round(float(px), 2),
            "center_pixel_y": round(float(py), 2),
            "center_ra": round(float(ra), 6),
            "center_dec": round(float(dec), 6),
            "target_snr": 0.0,
            "injection_class": "NONE",
            "source_type": "NULL_BACKGROUND",
            "mask_status": "VALID_UNMASKED"
        })
        trial_counter += 1

    # -------------------------------------------------------------
    # 4. EVALUATION_POINT_SOURCE_INJECTION (500 trials from P0002, P0009, P0010)
    # -------------------------------------------------------------
    print("  Allocating EVALUATION_POINT_SOURCE_INJECTION trials...")
    for i in range(N_TRIALS_PER_PARTITION):
        f_info = eval_files[i % len(eval_files)]
        w = wcs_cache[f_info["filename"]]
        px = rng.uniform(100.0, 1940.0)
        py = rng.uniform(100.0, 1940.0)
        ra, dec = w.pixel_to_world_values(px, py)
        snr = float(rng.choice(SNR_GRID_EVALUATION))

        all_trials.append({
            "trial_id": f"PILOT_{trial_counter:06d}",
            "partition": "EVALUATION_POINT_SOURCE_INJECTION",
            "role": "EVALUATION",
            "pointing": f_info["pointing"],
            "detector": f_info["detector"],
            "detector_num": f_info["detector_num"],
            "dither": f_info["dither"],
            "fits_filename": f_info["filename"],
            "fits_relpath": f"data/spherex/multipointing_pilot/level2/{f_info['pointing']}/{f_info['filename']}",
            "center_pixel_x": round(float(px), 2),
            "center_pixel_y": round(float(py), 2),
            "center_ra": round(float(ra), 6),
            "center_dec": round(float(dec), 6),
            "target_snr": snr,
            "injection_class": "POINT_SOURCE",
            "source_type": "SYNTHETIC_POINT_SOURCE",
            "mask_status": "VALID_UNMASKED"
        })
        trial_counter += 1

    # -------------------------------------------------------------
    # 5. EVALUATION_EXTENDED_SOURCE_INJECTION (500 trials from P0002, P0009, P0010)
    # -------------------------------------------------------------
    print("  Allocating EVALUATION_EXTENDED_SOURCE_INJECTION trials...")
    for i in range(N_TRIALS_PER_PARTITION):
        f_info = eval_files[i % len(eval_files)]
        w = wcs_cache[f_info["filename"]]
        px = rng.uniform(100.0, 1940.0)
        py = rng.uniform(100.0, 1940.0)
        ra, dec = w.pixel_to_world_values(px, py)
        snr = float(rng.choice(SNR_GRID_EVALUATION))

        all_trials.append({
            "trial_id": f"PILOT_{trial_counter:06d}",
            "partition": "EVALUATION_EXTENDED_SOURCE_INJECTION",
            "role": "EVALUATION",
            "pointing": f_info["pointing"],
            "detector": f_info["detector"],
            "detector_num": f_info["detector_num"],
            "dither": f_info["dither"],
            "fits_filename": f_info["filename"],
            "fits_relpath": f"data/spherex/multipointing_pilot/level2/{f_info['pointing']}/{f_info['filename']}",
            "center_pixel_x": round(float(px), 2),
            "center_pixel_y": round(float(py), 2),
            "center_ra": round(float(ra), 6),
            "center_dec": round(float(dec), 6),
            "target_snr": snr,
            "injection_class": "EXTENDED_SOURCE",
            "source_type": "SYNTHETIC_EXTENDED_SOURCE",
            "mask_status": "VALID_UNMASKED"
        })
        trial_counter += 1

    df_manifest = pd.DataFrame(all_trials)
    df_manifest.to_csv(MANIFEST_CSV, index=False)
    manifest_sha = compute_sha256(MANIFEST_CSV)
    print(f"Manifest written -> {MANIFEST_CSV.name} ({len(df_manifest)} trials, SHA-256: {manifest_sha})")
    return df_manifest

if __name__ == "__main__":
    manifest = generate_five_partition_manifest(seed=42)
    print("\nPartition Counts:")
    print(manifest["partition"].value_counts())
    print("\nPointing by Partition Cross-tabulation:")
    print(pd.crosstab(manifest["partition"], manifest["pointing"]))

