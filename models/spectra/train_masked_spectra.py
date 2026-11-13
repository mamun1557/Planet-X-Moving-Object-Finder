"""
SPECTRA Masked-Channel Training Pipeline (v2.1 Calibrated)
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Scientifically Rigorous Self-Supervised Spectral Anomaly Autoencoder:
1. Implements strictly masked reconstruction loss:
   L = sum(m_i * w_i * (x_hat_i - x_i)^2) / sum(m_i * w_i)
   where m_i is the valid_channel_mask and w_i is calibrated inverse-variance weight.
2. Incorporates empirical systematic error floor (f_sys = 1.93%) from Phase 4 calibration.
3. Completely isolates Pointing 0001 (Train: 2,416 sources), Pointing 0004 (Val: 1,249 sources),
   and Pointing 0003 (Independent Test: 1,392 sources) to eliminate spatial & source leakage.
4. Preserves unobserved channels as NaN/masked; never fills missing channels with zero in loss.
5. Saves versioned checkpoint 'checkpoints/spectra_masked_ae_v2.pt' without overwriting legacy checkpoints.
"""

import os
import sys
import json
import time
import ast
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MaskedSPECTRA")


class MaskedSpectralDataset(Dataset):
    """Dataset for 102-channel spectrophotometric vectors with per-channel masks and uncertainties."""
    
    def __init__(self, df: pd.DataFrame, f_sys: float = 0.0193):
        self.f_sys = f_sys
        self.samples = []
        
        for idx in range(len(df)):
            row = df.iloc[idx]
            
            # Parse lists stored as strings in CSV
            mask_raw = ast.literal_eval(row["valid_channel_mask"]) if isinstance(row["valid_channel_mask"], str) else row["valid_channel_mask"]
            flux_raw = ast.literal_eval(row["flux"]) if isinstance(row["flux"], str) else row["flux"]
            unc_raw = ast.literal_eval(row["uncertainty"]) if isinstance(row["uncertainty"], str) else row["uncertainty"]
            
            mask = np.array(mask_raw, dtype=bool)
            flux = np.array([f if f is not None and not np.isnan(f) else 0.0 for f in flux_raw], dtype=np.float32)
            unc = np.array([u if u is not None and not np.isnan(u) and u > 0 else 1.0 for u in unc_raw], dtype=np.float32)
            
            n_valid = int(np.sum(mask))
            if n_valid == 0:
                continue  # Skip all-invalid samples safely
                
            # Scientifically defensible normalization: scale by robust median of valid channels only
            valid_fluxes = flux[mask]
            scale = float(np.median(valid_fluxes))
            if scale <= 0 or np.isnan(scale):
                scale = float(np.mean(valid_fluxes)) if np.mean(valid_fluxes) > 0 else 1.0
                
            norm_flux = np.where(mask, flux / scale, 0.0).astype(np.float32)
            norm_unc = np.where(mask, unc / scale, 1.0).astype(np.float32)
            
            # Calibrated inverse variance weight incorporating 1.93% systematic floor
            # Var_tot = sigma_norm^2 + (f_sys * norm_flux)^2
            tot_var = (norm_unc ** 2) + ((self.f_sys * norm_flux) ** 2)
            tot_var = np.maximum(tot_var, 1e-4)
            weights = np.where(mask, 1.0 / tot_var, 0.0).astype(np.float32)
            
            # Clamp weights to prevent extreme leverage
            weights = np.clip(weights, 0.01, 100.0)
            
            self.samples.append({
                "source_id": row["source_id"],
                "flux": norm_flux,
                "mask": mask.astype(np.float32),
                "weight": weights,
                "scale": scale,
                "n_valid": n_valid
            })

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        return (
            torch.from_numpy(s["flux"]),
            torch.from_numpy(s["mask"]),
            torch.from_numpy(s["weight"]),
            torch.tensor(s["scale"], dtype=torch.float32)
        )


class MaskedSpectralAutoencoder(nn.Module):
    """
    Mask-Aware 1D Autoencoder for SPHEREx 102-channel spectrophotometry.
    Takes normalized flux and valid-channel mask, preserves latent bottleneck (dim=16),
    and reconstructs SED vector across all channels.
    """
    def __init__(self, num_channels: int = 102, hidden_dim: int = 64, latent_dim: int = 16):
        super().__init__()
        self.num_channels = num_channels
        self.latent_dim = latent_dim
        
        # Concatenate normalized flux + mask (102 + 102 = 204)
        in_dim = num_channels * 2
        
        self.encoder = nn.Sequential(
            nn.Linear(in_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, latent_dim)
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, num_channels)
        )

    def forward(self, flux: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        # Combined input representation
        x_in = torch.cat([flux, mask], dim=-1)
        latent = self.encoder(x_in)
        recon = self.decoder(latent)
        return recon

    def compute_masked_loss(self, recon: torch.Tensor, target: torch.Tensor, mask: torch.Tensor, weight: torch.Tensor) -> torch.Tensor:
        """
        Calculates scientifically justified masked loss:
        L = sum(m_i * w_i * (x_hat_i - x_i)^2) / sum(m_i * w_i)
        """
        sq_err = (recon - target) ** 2
        weighted_sq_err = sq_err * weight * mask
        
        # Sum per sample
        num = torch.sum(weighted_sq_err, dim=-1)
        denom = torch.sum(weight * mask, dim=-1) + 1e-6
        
        sample_loss = num / denom
        return torch.mean(sample_loss)


def train_masked_spectra(
    train_csv: str = "data/processed/spectral_features/validation_assembled_spectra.csv",
    out_ckpt: str = "checkpoints/spectra_masked_ae_v2.pt",
    epochs: int = 25,
    batch_size: int = 32,
    lr: float = 1e-3,
    random_seed: int = 42
) -> Dict[str, Any]:
    
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training Masked SPECTRA on device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")
    
    # 1. Load dataset and partition by pointing
    df_raw = pd.read_csv(train_csv)
    logger.info(f"Loaded {len(df_raw)} total assembled spectra from {train_csv}")
    
    def extract_ptg(obs_prov):
        parts = str(obs_prov).split(",")
        ptgs = set()
        for p in parts:
            sub = p.strip().split("_")
            if len(sub) >= 3:
                ptgs.add(sub[2])
        return ",".join(sorted(ptgs)) if ptgs else "UNKNOWN"
        
    df_raw["pointing"] = df_raw["observation_provenance"].apply(extract_ptg)
    
    # Strict spatial partitioning:
    # Pointing 0001 (Train), Pointing 0004 (Validation)
    df_train = df_raw[df_raw["pointing"] == "0001"].reset_index(drop=True)
    df_val = df_raw[df_raw["pointing"] == "0004"].reset_index(drop=True)
    
    logger.info(f"Spatial Partitioning: Train (Pointing 0001) = {len(df_train)} sources | Val (Pointing 0004) = {len(df_val)} sources")
    
    train_dataset = MaskedSpectralDataset(df_train)
    val_dataset = MaskedSpectralDataset(df_val)
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # 2. Instantiate Model and Optimizer
    model = MaskedSpectralAutoencoder(num_channels=102, hidden_dim=64, latent_dim=16).to(device)
    total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    logger.info(f"Model initialized: MaskedSpectralAutoencoder (Parameters: {total_params:,})")
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    
    history = []
    best_val_loss = float("inf")
    best_epoch = 0
    start_time = time.time()
    
    # 3. Training Loop
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_total = 0.0
        
        for flux, mask, weight, scale in train_loader:
            flux, mask, weight = flux.to(device), mask.to(device), weight.to(device)
            optimizer.zero_grad()
            
            recon = model(flux, mask)
            loss = model.compute_masked_loss(recon, flux, mask, weight)
            loss.backward()
            
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            train_loss_total += loss.item()
            
        scheduler.step()
        train_loss_avg = train_loss_total / max(1, len(train_loader))
        
        # Validation evaluation
        model.eval()
        val_loss_total = 0.0
        with torch.no_grad():
            for flux, mask, weight, scale in val_loader:
                flux, mask, weight = flux.to(device), mask.to(device), weight.to(device)
                recon = model(flux, mask)
                v_loss = model.compute_masked_loss(recon, flux, mask, weight)
                val_loss_total += v_loss.item()
                
        val_loss_avg = val_loss_total / max(1, len(val_loader))
        
        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss_avg, 6),
            "val_loss": round(val_loss_avg, 6),
            "lr": float(scheduler.get_last_lr()[0])
        })
        
        logger.info(f"Epoch {epoch:02d}/{epochs:02d} | Train Masked Chi2 Loss: {train_loss_avg:.6f} | Val Loss: {val_loss_avg:.6f}")
        
        if val_loss_avg < best_val_loss:
            best_val_loss = val_loss_avg
            best_epoch = epoch
            os.makedirs(os.path.dirname(out_ckpt), exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "val_loss": val_loss_avg,
                "config": {
                    "num_channels": 102,
                    "hidden_dim": 64,
                    "latent_dim": 16,
                    "f_sys": 0.0193,
                    "train_samples": len(train_dataset),
                    "val_samples": len(val_dataset),
                    "architecture": "MaskedSpectralAutoencoder",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }, out_ckpt)
            
    total_time = time.time() - start_time
    logger.info(f"Training completed in {total_time:.2f}s. Best Epoch: {best_epoch} with Val Loss: {best_val_loss:.6f}")
    logger.info(f"Saved calibrated versioned checkpoint to: {out_ckpt}")
    
    # Save training metadata & history
    meta_path = os.path.splitext(out_ckpt)[0] + "_training_meta.json"
    meta_data = {
        "model_name": "SPECTRA_Masked_AE_v2",
        "checkpoint_path": out_ckpt,
        "timestamp_utc": datetime.utcnow().isoformat(),
        "hardware": {
            "device": str(device),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
        },
        "dataset_splits": {
            "train_pointing": "0001",
            "train_samples": len(train_dataset),
            "val_pointing": "0004",
            "val_samples": len(val_dataset),
            "random_seed": random_seed
        },
        "hyperparameters": {
            "epochs": epochs,
            "best_epoch": best_epoch,
            "batch_size": batch_size,
            "learning_rate": lr,
            "f_sys_calibrated": 0.0193,
            "latent_dim": 16,
            "hidden_dim": 64
        },
        "results": {
            "initial_train_loss": history[0]["train_loss"],
            "final_train_loss": history[-1]["train_loss"],
            "best_val_loss": round(best_val_loss, 6),
            "training_duration_sec": round(total_time, 2)
        },
        "history": history
    }
    with open(meta_path, "w") as f:
        json.dump(meta_data, f, indent=2)
    logger.info(f"Saved training metadata to: {meta_path}")
    
    return meta_data


if __name__ == "__main__":
    train_masked_spectra()
