"""
SPECTRA Independent Evaluation Suite
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Evaluates the retrained Masked SPECTRA Autoencoder strictly on the untouched
independent test set (Pointing 0003, 1,392 astronomical sources), completely
isolated from training and validation groups.
"""

import os
import sys
import json
import ast
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
import torch
import torch.nn as nn

base_dir = os.path.abspath(".")
sys.path.insert(0, base_dir)

from models.spectra.train_masked_spectra import MaskedSpectralAutoencoder, MaskedSpectralDataset


def evaluate_independent_spectra(
    test_csv: str = "data/processed/spectral_features/independent_test_assembled_spectra.csv",
    ckpt_path: str = "checkpoints/spectra_masked_ae_v2.pt",
    f_sys: float = 0.0193
) -> Dict[str, Any]:
    print("=" * 70)
    print("SPECTRA INDEPENDENT TEST EVALUATION (Pointing 0003)")
    print("=" * 70)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Evaluation device: {device}")
    
    if not os.path.exists(test_csv):
        raise FileNotFoundError(f"Independent test catalog not found: {test_csv}")
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Model checkpoint not found: {ckpt_path}")
        
    df_test = pd.read_csv(test_csv)
    print(f"Loaded {len(df_test)} independent test sources from Pointing 0003.")
    
    # Load model
    checkpoint = torch.load(ckpt_path, map_location=device)
    cfg = checkpoint.get("config", {})
    model = MaskedSpectralAutoencoder(
        num_channels=cfg.get("num_channels", 102),
        hidden_dim=cfg.get("hidden_dim", 64),
        latent_dim=cfg.get("latent_dim", 16)
    ).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    print(f"Loaded checkpoint from epoch {checkpoint.get('epoch', 'N/A')} with val loss {checkpoint.get('val_loss', 'N/A'):.6f}")

    dataset = MaskedSpectralDataset(df_test, f_sys=f_sys)
    print(f"Constructed test dataset: {len(dataset)} valid sources.")

    recon_losses = []
    per_channel_resids = []
    sample_records = []

    with torch.no_grad():
        for i in range(len(dataset)):
            flux, mask, weight, scale = dataset[i]
            t_flux = flux.unsqueeze(0).to(device)
            t_mask = mask.unsqueeze(0).to(device)
            t_weight = weight.unsqueeze(0).to(device)
            
            recon = model(t_flux, t_mask)
            
            # Loss on valid observed channels
            sq_err = ((recon - t_flux) ** 2) * t_weight * t_mask
            num = torch.sum(sq_err, dim=-1)
            denom = torch.sum(t_weight * t_mask, dim=-1) + 1e-6
            sample_loss = float((num / denom).item())
            
            recon_losses.append(sample_loss)
            
            # Record per-channel unweighted relative residual
            valid_idx = torch.where(t_mask[0] > 0)[0]
            unweighted_res = torch.abs(recon[0, valid_idx] - t_flux[0, valid_idx])
            mean_unw_res = float(torch.mean(unweighted_res).item()) if len(valid_idx) > 0 else 0.0
            
            sample_records.append({
                "source_id": dataset.samples[i]["source_id"],
                "n_valid": dataset.samples[i]["n_valid"],
                "scale": float(scale.item()),
                "masked_chi2": sample_loss,
                "mean_unweighted_res": mean_unw_res
            })

    df_res = pd.DataFrame(sample_records)
    
    # 1. Overall Error Distribution
    mean_err = float(np.mean(recon_losses))
    median_err = float(np.median(recon_losses))
    std_err = float(np.std(recon_losses))
    p90 = float(np.percentile(recon_losses, 90))
    p99 = float(np.percentile(recon_losses, 99))
    
    print("\n--- Independent Test Reconstruction Error Distribution ---")
    print(f"  Mean Masked Chi2 Loss:   {mean_err:.6f}")
    print(f"  Median Masked Chi2 Loss: {median_err:.6f}")
    print(f"  Std Masked Chi2 Loss:    {std_err:.6f}")
    print(f"  90th Percentile:         {p90:.6f}")
    print(f"  99th Percentile:         {p99:.6f}")

    # 2. Performance by Valid Channel Coverage
    print("\n--- Performance by Valid Channel Coverage ---")
    coverage_stats = {}
    for n_ch, gdf in df_res.groupby("n_valid"):
        coverage_stats[int(n_ch)] = {
            "count": len(gdf),
            "mean_loss": round(float(gdf["masked_chi2"].mean()), 6),
            "median_loss": round(float(gdf["masked_chi2"].median()), 6),
            "std_loss": round(float(gdf["masked_chi2"].std()), 6)
        }
    print(pd.DataFrame(coverage_stats).T.to_string())

    # 3. Performance by Source Brightness (Scale in MJy/sr)
    print("\n--- Performance by Flux Brightness Tier ---")
    df_res["flux_tier"] = pd.qcut(df_res["scale"], q=3, labels=["Faint", "Moderate", "Bright"])
    tier_stats = {}
    for tier, gdf in df_res.groupby("flux_tier", observed=False):
        tier_stats[str(tier)] = {
            "count": len(gdf),
            "scale_range": f"{gdf['scale'].min():.1f} - {gdf['scale'].max():.1f}",
            "mean_loss": round(float(gdf["masked_chi2"].mean()), 6),
            "median_loss": round(float(gdf["masked_chi2"].median()), 6)
        }
    print(pd.DataFrame(tier_stats).T.to_string())

    # 4. Negative-Control False Positive Behavior
    # In pure nominal stars, how many exceed 3-sigma or 5-sigma chi2 outlier thresholds?
    threshold_3sigma = median_err + 3.0 * std_err
    threshold_5sigma = median_err + 5.0 * std_err
    fp_3sig_count = int((df_res["masked_chi2"] > threshold_3sigma).sum())
    fp_5sig_count = int((df_res["masked_chi2"] > threshold_5sigma).sum())
    
    print("\n--- Negative Control False Positive Analysis ---")
    print(f"  3-Sigma Outlier Threshold: {threshold_3sigma:.6f} | False Positives: {fp_3sig_count} ({fp_3sig_count/len(df_res)*100:.2f}%)")
    print(f"  5-Sigma Outlier Threshold: {threshold_5sigma:.6f} | False Positives: {fp_5sig_count} ({fp_5sig_count/len(df_res)*100:.2f}%)")

    results = {
        "dataset": "Pointing_0003_Independent_Test",
        "total_sources_evaluated": len(df_res),
        "overall_recon_error": {
            "mean": mean_err,
            "median": median_err,
            "std": std_err,
            "p90": p90,
            "p99": p99
        },
        "coverage_stratification": coverage_stats,
        "brightness_stratification": tier_stats,
        "negative_control": {
            "3_sigma_threshold": threshold_3sigma,
            "3_sigma_fp_count": fp_3sig_count,
            "3_sigma_fp_rate": float(fp_3sig_count / len(df_res)),
            "5_sigma_threshold": threshold_5sigma,
            "5_sigma_fp_count": fp_5sig_count,
            "5_sigma_fp_rate": float(fp_5sig_count / len(df_res))
        },
        "real_world_discovery_labels": "NOT_AVAILABLE (No ground-truth labels for Pointing 0003)"
    }

    out_json = os.path.join(base_dir, "reports", "spectra_independent_eval_summary.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved independent evaluation summary to: {out_json}")
    
    return results


if __name__ == "__main__":
    evaluate_independent_spectra()
