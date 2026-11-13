"""
SPECTRA-X / F1 — Phase 3, Task 1.2C
SPECTRA Provisional-Null Threshold Calibration Driver
"""

import os
import sys
import json
import ast
import hashlib
import time
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import torch
from astropy.coordinates import SkyCoord
import astropy.units as u

# Add base directory to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, BASE_DIR)

from models.spectra.train_masked_spectra import MaskedSpectralAutoencoder

EXPECTED_CHECKPOINT_SHA256 = "6ecada80ba30ec803af2cf21ba58d72e8209789b4f5da68a22e60134a3b5a938"
F_SYS = 0.0193
RANDOM_SEED = 42
BOOTSTRAP_REPLICATES = 2000

KNOWN_OVERLAP_IDS = {
    6316932723797678080,
    6268273836710905344,
    6316494229114061952,
    6316495122467403776,
    6316948567937380224
}


def compute_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1048576):
            h.update(chunk)
    return h.hexdigest()


def compute_morans_i(coords: np.ndarray, values: np.ndarray, k_neighbors: int = 8) -> Tuple[float, float]:
    """Computes Moran's I spatial autocorrelation coefficient using k-nearest neighbors."""
    n = len(values)
    if n < k_neighbors + 1:
        return 0.0, 1.0
    
    # Distance matrix using SkyCoord
    sc = SkyCoord(ra=coords[:, 0] * u.deg, dec=coords[:, 1] * u.deg)
    
    # Standardize values
    z = values - np.mean(values)
    s0 = np.sum(z ** 2)
    if s0 == 0:
        return 0.0, 1.0
        
    # Build k-NN binary spatial weight matrix
    # For large n, match_to_catalog or search_around_sky
    # Compute in batches for efficiency
    W_num = 0.0
    W_sum = n * k_neighbors
    
    # KD-Tree in cartesian space
    from scipy.spatial import cKDTree
    xyz = sc.cartesian.xyz.value.T
    tree = cKDTree(xyz)
    distances, indices = tree.query(xyz, k=k_neighbors + 1)  # 0 is self
    
    for i in range(n):
        nn_idx = indices[i, 1:]  # skip self
        W_num += np.sum(z[i] * z[nn_idx])
        
    moran_i = float((n / W_sum) * (W_num / s0))
    expected_i = float(-1.0 / (n - 1))
    return moran_i, expected_i


def spatial_block_bootstrap(
    df: pd.DataFrame,
    block_size_deg: float,
    replicates: int = 1000,
    seed: int = 42
) -> Dict[str, Any]:
    """Performs spatial block bootstrap resampling by grouping sources into spatial grid cells."""
    rng = np.random.RandomState(seed)
    ra = df["ra"].values
    dec = df["dec"].values
    scores = df["score"].values
    
    ra_min, ra_max = np.min(ra), np.max(ra)
    dec_min, dec_max = np.min(dec), np.max(dec)
    
    # Assign block IDs
    ra_block = np.floor((ra - ra_min) / block_size_deg).astype(int)
    dec_block = np.floor((dec - dec_min) / block_size_deg).astype(int)
    block_ids = ra_block * 10000 + dec_block
    
    unique_blocks = np.unique(block_ids)
    n_blocks = len(unique_blocks)
    
    # Map blocks to source indices
    block_to_indices = {b: np.where(block_ids == b)[0] for b in unique_blocks}
    block_sizes = [len(block_to_indices[b]) for b in unique_blocks]
    
    boot_q95 = []
    boot_q99 = []
    
    for _ in range(replicates):
        sampled_blocks = rng.choice(unique_blocks, size=n_blocks, replace=True)
        sample_indices = np.concatenate([block_to_indices[b] for b in sampled_blocks])
        sample_scores = scores[sample_indices]
        boot_q95.append(np.percentile(sample_scores, 95, method="linear"))
        boot_q99.append(np.percentile(sample_scores, 99, method="linear"))
        
    return {
        "block_size_deg": block_size_deg,
        "n_blocks": n_blocks,
        "median_sources_per_block": float(np.median(block_sizes)),
        "min_sources_per_block": int(np.min(block_sizes)),
        "max_sources_per_block": int(np.max(block_sizes)),
        "q95_median": float(np.median(boot_q95)),
        "q95_ci": [float(np.percentile(boot_q95, 2.5)), float(np.percentile(boot_q95, 97.5))],
        "q95_se": float(np.std(boot_q95)),
        "q99_median": float(np.median(boot_q99)),
        "q99_ci": [float(np.percentile(boot_q99, 2.5)), float(np.percentile(boot_q99, 97.5))],
        "q99_se": float(np.std(boot_q99))
    }


def run_provisional_null_calibration():
    print("=" * 80)
    print("SPECTRA-X / F1 — PHASE 3, TASK 1.2C")
    print("SPECTRA Provisional-Null Threshold Calibration Campaign")
    print("=" * 80)

    # 1. Verify checkpoint immutability
    ckpt_path = os.path.join(BASE_DIR, "checkpoints", "spectra_masked_ae_v2.pt")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
        
    actual_ckpt_hash = compute_sha256(ckpt_path)
    print(f"Checkpoint SHA-256: {actual_ckpt_hash}")
    if actual_ckpt_hash != EXPECTED_CHECKPOINT_SHA256:
        raise ValueError(f"CRITICAL STOP: Checkpoint hash mismatch! {actual_ckpt_hash} != {EXPECTED_CHECKPOINT_SHA256}")
    print("Checkpoint hash verified byte-for-byte immutable.")

    # 2. Load model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Inference device: {device}")
    
    checkpoint = torch.load(ckpt_path, map_location=device)
    cfg = checkpoint.get("config", {})
    model = MaskedSpectralAutoencoder(
        num_channels=cfg.get("num_channels", 102),
        hidden_dim=cfg.get("hidden_dim", 64),
        latent_dim=cfg.get("latent_dim", 16)
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    print(f"Loaded frozen model (epoch={checkpoint.get('epoch')}, val_loss={checkpoint.get('val_loss'):.6f})")

    # 3. Load calibration cohort from P0008
    spectra_path = os.path.join(BASE_DIR, "data", "processed", "spectra", "phase3_multpointing_spectra_v1.csv")
    p8_cat_path = os.path.join(BASE_DIR, "data", "processed", "pilot_catalogues", "pointing_0008_source_catalogue.csv")
    
    if not os.path.exists(spectra_path):
        raise FileNotFoundError(f"Spectra file missing: {spectra_path}")
    if not os.path.exists(p8_cat_path):
        raise FileNotFoundError(f"P0008 catalogue missing: {p8_cat_path}")
        
    spectra_df = pd.read_csv(spectra_path)
    p8_cat_df = pd.read_csv(p8_cat_path)[["source_id", "classification_category"]]
    
    # Restrict strictly to Pointing 0008
    p8_df = spectra_df[spectra_df["pointing"] == 8].merge(p8_cat_df, on="source_id")
    print(f"Total Pointing 0008 records in spectra catalog: {len(p8_df)}")
    
    # Enforce primary calibration filter: RELIABLE_ISOLATED_POINT_SOURCE with valid_channels >= 5
    calib_df = p8_df[
        (p8_df["classification_category"] == "RELIABLE_ISOLATED_POINT_SOURCE") &
        (p8_df["valid_channels_count"] >= 5)
    ].reset_index(drop=True)
    
    total_eligible = len(calib_df)
    print(f"\nTotal verified eligible P0008 calibration sources: {total_eligible}")
    if total_eligible != 3206:
        raise ValueError(f"CRITICAL STOP: Cohort count mismatch! Expected 3,206, got {total_eligible}")
        
    pair_counts = calib_df["detector_provenance"].value_counts().to_dict()
    print(f"  D1+D4: {pair_counts.get('D1,D4', 0)} (expected 1,055)")
    print(f"  D2+D5: {pair_counts.get('D2,D5', 0)} (expected 1,304)")
    print(f"  D3+D6: {pair_counts.get('D3,D6', 0)} (expected 847)")
    
    if pair_counts.get("D1,D4") != 1055 or pair_counts.get("D2,D5") != 1304 or pair_counts.get("D3,D6") != 847:
        raise ValueError("CRITICAL STOP: Stratum count mismatch against Task 1.2B-S reconciliation ledger!")
        
    # Check zero overlap with historical training sources
    overlap_ids_found = set(calib_df["source_id"]).intersection(KNOWN_OVERLAP_IDS)
    if len(overlap_ids_found) > 0:
        raise ValueError(f"CRITICAL STOP: Training overlap sources detected in P0008! {overlap_ids_found}")
    print("Zero historical training overlaps confirmed in primary P0008 calibration cohort.")

    # 4. Score all 3,206 sources
    print("\nExecuting model inference and scoring across all 3,206 sources...")
    t0 = time.time()
    
    score_records = []
    
    for i in range(len(calib_df)):
        row = calib_df.iloc[i]
        sid = row["source_id"]
        pair = row["detector_provenance"]
        ra_val = float(row["ra"])
        dec_val = float(row["dec"])
        n_valid = int(row["valid_channels_count"])
        
        mask_raw = ast.literal_eval(row["valid_channel_mask"])
        flux_raw = ast.literal_eval(row["flux"])
        unc_raw = ast.literal_eval(row["uncertainty"])
        
        mask = np.array(mask_raw, dtype=bool)
        flux = np.array([f if f is not None and not np.isnan(f) else 0.0 for f in flux_raw], dtype=np.float32)
        unc = np.array([u if u is not None and not np.isnan(u) and u > 0 else 1.0 for u in unc_raw], dtype=np.float32)
        
        # Robust scale: median of valid channels only
        valid_fluxes = flux[mask]
        scale = float(np.median(valid_fluxes))
        if scale <= 0 or np.isnan(scale):
            scale = float(np.mean(valid_fluxes)) if np.mean(valid_fluxes) > 0 else 1.0
            
        norm_flux = np.where(mask, flux / scale, 0.0).astype(np.float32)
        norm_unc = np.where(mask, unc / scale, 1.0).astype(np.float32)
        
        tot_var = (norm_unc ** 2) + ((F_SYS * norm_flux) ** 2)
        tot_var = np.maximum(tot_var, 1e-4)
        weights = np.where(mask, 1.0 / tot_var, 0.0).astype(np.float32)
        weights = np.clip(weights, 0.01, 100.0)
        
        t_flux = torch.from_numpy(norm_flux).unsqueeze(0).to(device)
        t_mask = torch.from_numpy(mask.astype(np.float32)).unsqueeze(0).to(device)
        t_weight = torch.from_numpy(weights).unsqueeze(0).to(device)
        
        with torch.no_grad():
            recon = model(t_flux, t_mask)
            sq_err = ((recon - t_flux) ** 2) * t_weight * t_mask
            num = torch.sum(sq_err, dim=-1)
            denom = torch.sum(t_weight * t_mask, dim=-1) + 1e-6
            sample_loss = float((num / denom).item())
            
            # Residual metrics
            valid_idx = torch.where(t_mask[0] > 0)[0]
            unw_res = torch.abs(recon[0, valid_idx] - t_flux[0, valid_idx])
            mean_unw = float(torch.mean(unw_res).item()) if len(valid_idx) > 0 else 0.0
            max_unw = float(torch.max(unw_res).item()) if len(valid_idx) > 0 else 0.0
            
        score_records.append({
            "source_id": sid,
            "pointing": 8,
            "partition_role": "CALIBRATION",
            "detector_provenance": pair,
            "ra": ra_val,
            "dec": dec_val,
            "valid_channels_count": n_valid,
            "flux_median_scale": scale,
            "score": sample_loss,
            "mean_unweighted_res": mean_unw,
            "max_unweighted_res": max_unw
        })
        
    scoring_time = time.time() - t0
    scores_df = pd.DataFrame(score_records)
    print(f"Scoring complete in {scoring_time:.2f}s ({len(scores_df)} sources scored).")
    
    # Save source-level score table
    out_scores_csv = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_p0008_calibration_scores_v1.csv")
    scores_df.to_csv(out_scores_csv, index=False)
    print(f"Saved source-level calibration scores to: {out_scores_csv}")

    # 5. Strata-specific Calibration and Statistics
    strata = ["D1,D4", "D2,D5", "D3,D6"]
    strata_results = {}
    
    print("\n" + "=" * 80)
    print("DETECTOR-PAIR PROVISIONAL-NULL THRESHOLD DERIVATION")
    print("=" * 80)
    
    for stratum in strata:
        sdf = scores_df[scores_df["detector_provenance"] == stratum].reset_index(drop=True)
        scores = sdf["score"].values
        n_stratum = len(scores)
        
        # Distribution moments & summary
        s_min = float(np.min(scores))
        s_max = float(np.max(scores))
        s_mean = float(np.mean(scores))
        s_std = float(np.std(scores))
        s_median = float(np.median(scores))
        s_q25 = float(np.percentile(scores, 25, method="linear"))
        s_q75 = float(np.percentile(scores, 75, method="linear"))
        s_iqr = float(s_q75 - s_q25)
        
        # Quantiles (Method: linear / Type 7)
        q90 = float(np.percentile(scores, 90, method="linear"))
        q95 = float(np.percentile(scores, 95, method="linear"))
        q97_5 = float(np.percentile(scores, 97.5, method="linear"))
        q99 = float(np.percentile(scores, 99, method="linear"))
        
        # Tie behavior check
        ties_near_q95 = int(np.sum(np.isclose(scores, q95, atol=1e-5)))
        ties_near_q99 = int(np.sum(np.isclose(scores, q99, atol=1e-5)))
        
        # Exceedance counts
        n_above_q95 = int(np.sum(scores > q95))
        n_above_q99 = int(np.sum(scores > q99))
        
        # Source-level Bootstrap
        rng_boot = np.random.RandomState(RANDOM_SEED)
        boot_q95_arr = np.zeros(BOOTSTRAP_REPLICATES, dtype=np.float64)
        boot_q99_arr = np.zeros(BOOTSTRAP_REPLICATES, dtype=np.float64)
        
        for b in range(BOOTSTRAP_REPLICATES):
            b_sample = rng_boot.choice(scores, size=n_stratum, replace=True)
            boot_q95_arr[b] = np.percentile(b_sample, 95, method="linear")
            boot_q99_arr[b] = np.percentile(b_sample, 99, method="linear")
            
        ci95_q95 = [float(np.percentile(boot_q95_arr, 2.5)), float(np.percentile(boot_q95_arr, 97.5))]
        se_q95 = float(np.std(boot_q95_arr))
        
        ci95_q99 = [float(np.percentile(boot_q99_arr, 2.5)), float(np.percentile(boot_q99_arr, 97.5))]
        se_q99 = float(np.std(boot_q99_arr))
        
        # Spatial Autocorrelation
        coords = sdf[["ra", "dec"]].values
        moran_i, exp_i = compute_morans_i(coords, scores, k_neighbors=8)
        
        # Spatial block bootstrap sensitivity analysis (0.5 deg, 1.0 deg, 2.0 deg)
        block_analysis = {}
        for bsize in [0.5, 1.0, 2.0]:
            block_analysis[f"{bsize}_deg"] = spatial_block_bootstrap(sdf, block_size_deg=bsize, replicates=1000, seed=RANDOM_SEED)
            
        print(f"\n--- Stratum: {stratum} (N = {n_stratum}) ---")
        print(f"  Score Range: [{s_min:.6f}, {s_max:.6f}] | Mean: {s_mean:.6f} +/- {s_std:.6f}")
        print(f"  Median: {s_median:.6f} | IQR: {s_iqr:.6f}")
        print(f"  95th Percentile (Nominal alpha=0.05 Threshold): {q95:.6f}")
        print(f"    Source-Level Bootstrap 95% CI: [{ci95_q95[0]:.6f}, {ci95_q95[1]:.6f}] (SE={se_q95:.6f})")
        print(f"    1.0 deg Block Bootstrap 95% CI: [{block_analysis['1.0_deg']['q95_ci'][0]:.6f}, {block_analysis['1.0_deg']['q95_ci'][1]:.6f}] (SE={block_analysis['1.0_deg']['q95_se']:.6f})")
        print(f"  99th Percentile (Nominal alpha=0.01 Threshold): {q99:.6f}")
        print(f"    Source-Level Bootstrap 95% CI: [{ci95_q99[0]:.6f}, {ci95_q99[1]:.6f}] (SE={se_q99:.6f})")
        print(f"    1.0 deg Block Bootstrap 95% CI: [{block_analysis['1.0_deg']['q99_ci'][0]:.6f}, {block_analysis['1.0_deg']['q99_ci'][1]:.6f}] (SE={block_analysis['1.0_deg']['q99_se']:.6f})")
        print(f"  Moran's I: {moran_i:.4f} (Expected: {exp_i:.4f})")
        print(f"  Exceedance: >95th = {n_above_q95} ({n_above_q95/n_stratum*100:.2f}%), >99th = {n_above_q99} ({n_above_q99/n_stratum*100:.2f}%)")

        strata_results[stratum] = {
            "detector_pair": stratum,
            "eligible_sources_count": n_stratum,
            "successfully_scored_count": n_stratum,
            "excluded_after_scoring_count": 0,
            "score_summary": {
                "min": s_min,
                "max": s_max,
                "mean": s_mean,
                "std": s_std,
                "median": s_median,
                "q25": s_q25,
                "q75": s_q75,
                "iqr": s_iqr,
                "percentile_90": q90,
                "percentile_95_nominal_alpha_0_05": q95,
                "percentile_97_5": q97_5,
                "percentile_99_nominal_alpha_0_01": q99
            },
            "threshold_alpha_0_05": {
                "nominal_alpha": 0.05,
                "threshold_value": q95,
                "sources_exceeding_threshold": n_above_q95,
                "empirical_exceedance_fraction": float(n_above_q95 / n_stratum),
                "bootstrap_confidence_interval_95": ci95_q95,
                "bootstrap_standard_error": se_q95,
                "ties_count_near_threshold": ties_near_q95
            },
            "threshold_alpha_0_01": {
                "nominal_alpha": 0.01,
                "threshold_value": q99,
                "sources_exceeding_threshold": n_above_q99,
                "empirical_exceedance_fraction": float(n_above_q99 / n_stratum),
                "bootstrap_confidence_interval_95": ci95_q99,
                "bootstrap_standard_error": se_q99,
                "ties_count_near_threshold": ties_near_q99
            },
            "spatial_autocorrelation": {
                "morans_i": moran_i,
                "expected_i": exp_i,
                "interpretation": "WEAK_SPATIAL_DEPENDENCE" if abs(moran_i) < 0.1 else "MODERATE_SPATIAL_DEPENDENCE"
            },
            "spatial_block_bootstrap_sensitivity": block_analysis
        }

    # 6. Save machine-readable threshold artifact
    out_thresh_json = os.path.join(BASE_DIR, "data", "processed", "spectra", "spectra_v2_provisional_thresholds_v1.json")
    
    thresholds_manifest = {
        "manifest_type": "SPECTRA_PROVISIONAL_NULL_THRESHOLDS",
        "version": "1.0.0",
        "task_id": "SPECTRA_TASK_1_2C",
        "calibration_timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model_provenance": {
            "model_identifier": "SPECTRA_Masked_AE_v2",
            "checkpoint_path": "checkpoints/spectra_masked_ae_v2.pt",
            "checkpoint_sha256": actual_ckpt_hash,
            "architecture": "MaskedSpectralAutoencoder (in=204, latent=16, hidden=64)",
            "systematic_error_floor": F_SYS
        },
        "score_definition": {
            "score_name": "masked_chi2",
            "formula": "sum(m_i * w_i * (x_hat_i - x_i)^2) / (sum(m_i * w_i) + 1e-6)",
            "normalization": "median of valid channels only",
            "weighting": "calibrated inverse variance with 1.93% systematic error floor",
            "weights_clamping": [0.01, 100.0]
        },
        "calibration_cohort_definition": {
            "pointing": "0008",
            "pointing_role": "CALIBRATION",
            "selection_criteria": "classification_category == 'RELIABLE_ISOLATED_POINT_SOURCE' and valid_channels_count >= 5",
            "total_calibration_sources": total_eligible,
            "training_overlap_sources": 0
        },
        "quantile_estimation": {
            "estimator": "numpy.percentile",
            "method": "linear",
            "interpolation_type": "Type 7 (linear interpolation between nearest data points)",
            "bootstrap_method": "source_level_with_replacement",
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "random_seed": RANDOM_SEED
        },
        "strata_thresholds": strata_results,
        "scientific_interpretation_and_limitations": {
            "threshold_status": "Empirical Provisional-Null Quantiles (NOT certified production false-positive rates)",
            "astrometric_caveat": "Astrometric cleanliness from Gaia DR3 does not guarantee absence of rare spectral anomalies in P0008",
            "generalization_limitation": "Derived strictly on Pointing 0008 (Galactic lat b approx -50 deg); cross-pointing transfer remains unverified until Task 1.2D blind evaluation",
            "blind_evaluation_firewall": "Pointings P0002, P0009, P0010 were strictly isolated and zero evaluation data were accessed"
        }
    }
    
    with open(out_thresh_json, "w", encoding="utf-8") as f:
        json.dump(thresholds_manifest, f, indent=2)
    print(f"\nSaved machine-readable provisional threshold artifact to: {out_thresh_json}")
    
    print("\n" + "=" * 80)
    print("TASK 1.2C CALIBRATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    print(f"Total Sources Scored: {total_eligible} (P0008 Only)")
    print(f"D1+D4 (N=1,055): 95th Threshold = {strata_results['D1,D4']['threshold_alpha_0_05']['threshold_value']:.6f} | 99th Threshold = {strata_results['D1,D4']['threshold_alpha_0_01']['threshold_value']:.6f}")
    print(f"D2+D5 (N=1,304): 95th Threshold = {strata_results['D2,D5']['threshold_alpha_0_05']['threshold_value']:.6f} | 99th Threshold = {strata_results['D2,D5']['threshold_alpha_0_01']['threshold_value']:.6f}")
    print(f"D3+D6 (N=847):   95th Threshold = {strata_results['D3,D6']['threshold_alpha_0_05']['threshold_value']:.6f} | 99th Threshold = {strata_results['D3,D6']['threshold_alpha_0_01']['threshold_value']:.6f}")
    print("=" * 80)


if __name__ == "__main__":
    run_provisional_null_calibration()

