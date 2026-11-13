"""
ASTROVISION Spatial Anomaly Training Pipeline (v2.1 Leakage-Free)
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Enforces strict pointing-level spatial partitioning:
- Train Set: Pointing 0001 & Pointing 0002 (16 files, 80 cutouts)
- Validation Set: Pointing 0004, 0005, 0006 (12 files, 60 cutouts)
- Untouched Test Set: Pointing 0003 (4 files, 20 cutouts) — completely excluded from training!
- Saves versioned checkpoint 'checkpoints/astrovision_spatial_v2.pt' without overwriting 'astrovision_latest.pt'.
"""

import os
import glob
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from astropy.io import fits

import sys
base_dir = os.path.abspath(".")
sys.path.insert(0, base_dir)

from models.astrovision.model import AstroVisionAutoencoder

# Fatal defects mask
FATAL_FLAG_MASK = 615


class SpatialPartitionedCutoutDataset(Dataset):
    """Extracts cutouts strictly from designated pointing files to eliminate spatial leakage."""
    
    def __init__(self, file_list: List[str], patch_size: int = 128, patches_per_file: int = 5, random_seed: int = 42):
        self.patch_size = patch_size
        self.patches = []
        self.var_patches = []
        self.mask_patches = []
        self.provenance = []
        
        np.random.seed(random_seed)
        
        for fp in file_list:
            fname = os.path.basename(fp)
            try:
                with fits.open(fp, memmap=True) as hdul:
                    if "IMAGE" not in hdul:
                        continue
                    img = hdul["IMAGE"].data.astype(np.float32)
                    var = hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul else np.full_like(img, 1e-3)
                    flags = hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in hdul else np.zeros_like(img, dtype=np.int32)
                    
                    H, W = img.shape
                    for p_idx in range(patches_per_file):
                        # Center region, avoid edges
                        y = np.random.randint(150, H - patch_size - 150)
                        x = np.random.randint(150, W - patch_size - 150)
                        
                        sub_img = img[y:y+patch_size, x:x+patch_size]
                        sub_var = var[y:y+patch_size, x:x+patch_size]
                        sub_flags = flags[y:y+patch_size, x:x+patch_size]
                        
                        # Replace NaNs
                        sub_img = np.nan_to_num(sub_img, nan=0.25)
                        sub_var = np.nan_to_num(sub_var, nan=0.01)
                        sub_var = np.maximum(sub_var, 1e-4)
                        
                        # Defect mask adhering to FATAL_FLAG_MASK = 615
                        mask = ((sub_flags & FATAL_FLAG_MASK) == 0).astype(np.float32)
                        
                        # Only accept patches with >= 75% unflagged pixels
                        if np.mean(mask) >= 0.75:
                            self.patches.append(sub_img)
                            self.var_patches.append(sub_var)
                            self.mask_patches.append(mask)
                            self.provenance.append(f"{fname}_p{p_idx}")
            except Exception as e:
                print(f"Error reading {fname}: {e}")

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        img = torch.from_numpy(self.patches[idx]).unsqueeze(0)
        var = torch.from_numpy(self.var_patches[idx]).unsqueeze(0)
        mask = torch.from_numpy(self.mask_patches[idx]).unsqueeze(0)
        return img, var, mask


def train_leakage_free_astrovision(
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 1e-3,
    out_ckpt: str = "checkpoints/astrovision_spatial_v2.pt",
    random_seed: int = 42
) -> Dict[str, Any]:
    
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training Leakage-Free ASTROVISION on device: {device}")
    
    l2_files = sorted(glob.glob(os.path.join(base_dir, "data", "spherex", "*", "level2", "*.fits")) +
                      glob.glob(os.path.join(base_dir, "data", "spherex", "*_deep", "*.fits")))
    
    # Partition files strictly by pointing
    train_files = [f for f in l2_files if "_0001_" in f or "_0002_" in f]
    val_files = [f for f in l2_files if "_0004_" in f or "_0005_" in f or "_0006_" in f]
    test_files = [f for f in l2_files if "_0003_" in f]
    
    print(f"Spatial Partitioning: Train={len(train_files)} files | Val={len(val_files)} files | Test={len(test_files)} files")
    
    train_ds = SpatialPartitionedCutoutDataset(train_files, patch_size=128, patches_per_file=5, random_seed=random_seed)
    val_ds = SpatialPartitionedCutoutDataset(val_files, patch_size=128, patches_per_file=5, random_seed=random_seed)
    
    print(f"Extracted Clean Cutouts: Train={len(train_ds)} patches | Val={len(val_ds)} patches")
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    model = AstroVisionAutoencoder().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    
    history = []
    best_val_loss = float("inf")
    best_epoch = 0
    start_time = time.time()
    
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for img, var, mask in train_loader:
            img, var, mask = img.to(device), var.to(device), mask.to(device)
            optimizer.zero_grad()
            recon = model(img)
            # Inverse variance weighted masked loss
            loss = torch.mean(((recon - img) ** 2 / var) * mask)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        scheduler.step()
        avg_train = train_loss / max(1, len(train_loader))
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for img, var, mask in val_loader:
                img, var, mask = img.to(device), var.to(device), mask.to(device)
                recon = model(img)
                loss = torch.mean(((recon - img) ** 2 / var) * mask)
                val_loss += loss.item()
                
        avg_val = val_loss / max(1, len(val_loader))
        
        history.append({
            "epoch": epoch,
            "train_loss": round(avg_train, 4),
            "val_loss": round(avg_val, 4)
        })
        print(f"Epoch {epoch:02d}/{epochs:02d} - Train Loss: {avg_train:.4f} | Val Loss: {avg_val:.4f}")
        
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            best_epoch = epoch
            os.makedirs(os.path.dirname(out_ckpt), exist_ok=True)
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": avg_val,
                "config": {
                    "patch_size": 128,
                    "train_patches": len(train_ds),
                    "val_patches": len(val_ds),
                    "pointing_train": ["0001", "0002"],
                    "pointing_val": ["0004", "0005", "0006"],
                    "pointing_test_excluded": ["0003"],
                    "timestamp": datetime.now().isoformat()
                }
            }, out_ckpt)
            
    total_time = time.time() - start_time
    print(f"Completed in {total_time:.2f}s. Saved versioned checkpoint: {out_ckpt} (Best Epoch {best_epoch}, Val Loss {best_val_loss:.4f})")
    
    meta_path = os.path.splitext(out_ckpt)[0] + "_meta.json"
    with open(meta_path, "w") as f:
        json.dump({
            "model_name": "AstroVision_Spatial_v2",
            "checkpoint_path": out_ckpt,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "duration_sec": total_time,
            "history": history
        }, f, indent=2)
        
    return {"best_val_loss": best_val_loss, "best_epoch": best_epoch}


if __name__ == "__main__":
    train_leakage_free_astrovision()
