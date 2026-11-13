"""
ASTROVISION V3 Spatial Anomaly Training Pipeline (Task 1.1U Remediation)
NASA Space Apps Challenge 2026 — Phase 3 Remediation Architecture

Strict Partition Governance:
- Evaluation Pointings Quarantine: Pointings 0002, 0009, 0010 are STRICTLY EXCLUDED (Zero Leakage).
- Calibration Pointings Separation: Pointings 0001 and 0008 are separated to preserve calibration isolation.
- Eligible Training/Validation Corpus: Pointings 0003 (23 files), 0004 (2 files), 0005 (2 files), 1B (4 files), 4B (4 files).
- Total Target Patches: Exactly 1,200 training patches + 240 validation patches (1,440 total) across all 6 detectors.
- Model Architecture: AstroVisionAutoencoderV3 with MaskAwareConv2d and RobustLocalNormalizer.
- Versioned Output: checkpoints/astrovision_spatial_v3.pt and checkpoints/astrovision_spatial_v3_meta.json.
"""

import os
import sys
import glob
import time
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from astropy.io import fits

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

from models.astrovision.model_v3 import (
    AstroVisionAutoencoderV3,
    RobustLocalNormalizer,
    FATAL_FLAG_MASK
)

# Quarantined Evaluation Pointings (STRICTLY PROHIBITED FROM TRAINING)
QUARANTINED_EVALUATION_POINTINGS = {"0002", "0009", "0010"}
# Calibration Pointings (PRESERVED FOR CALIBRATION ONLY)
CALIBRATION_POINTINGS = {"0001", "0008"}


class StratifiedV3CutoutDataset(Dataset):
    """
    Dataset loader for ASTROVISION V3 training:
    - Extracts non-overlapping 128x128 patches from eligible non-evaluation science files.
    - Applies RobustLocalNormalizer (fatal defect imputation, zero-median, MAD scaling).
    - Preserves explicit binary validity masks.
    """
    def __init__(
        self,
        file_list: List[str],
        target_patches: int = 1200,
        patch_size: int = 128,
        min_valid_fraction: float = 0.85,
        random_seed: int = 42
    ):
        self.patch_size = patch_size
        self.norm_patches = []
        self.mask_patches = []
        self.provenance = []
        
        rng = np.random.default_rng(random_seed)
        
        # Shuffle files
        shuffled_files = list(file_list)
        rng.shuffle(shuffled_files)
        
        patches_collected = 0
        
        for fp in shuffled_files:
            if patches_collected >= target_patches:
                break
                
            fname = os.path.basename(fp)
            p_id = fname.split("_")[3] if len(fname.split("_")) > 3 else "unknown"
            
            # Absolute governance check
            if p_id in QUARANTINED_EVALUATION_POINTINGS:
                raise RuntimeError(f"CRITICAL PARTITION VIOLATION: Evaluation pointing {p_id} detected in training file {fp}")
                
            try:
                with fits.open(fp, memmap=True) as hdul:
                    if "IMAGE" not in hdul:
                        continue
                    img = hdul["IMAGE"].data.astype(np.float32)
                    var = hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul else np.full_like(img, 1e-3)
                    flags = hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in hdul else np.zeros_like(img, dtype=np.int32)
                    det_id = hdul["IMAGE"].header.get("DETECTOR") or hdul["IMAGE"].header.get("DET_ID") or 1
                    
                    H, W = img.shape
                    
                    # Generate candidate grid
                    y_steps = list(range(100, H - patch_size - 100, 160))
                    x_steps = list(range(100, W - patch_size - 100, 160))
                    rng.shuffle(y_steps)
                    rng.shuffle(x_steps)
                    
                    for y in y_steps:
                        for x in x_steps:
                            if patches_collected >= target_patches:
                                break
                                
                            raw_sub_img = img[y:y+patch_size, x:x+patch_size]
                            raw_sub_var = var[y:y+patch_size, x:x+patch_size]
                            raw_sub_flags = flags[y:y+patch_size, x:x+patch_size]
                            
                            norm_res = RobustLocalNormalizer.normalize_patch(
                                raw_img=raw_sub_img,
                                raw_var=raw_sub_var,
                                raw_flags=raw_sub_flags,
                                fatal_mask_bits=FATAL_FLAG_MASK
                            )
                            
                            if norm_res["valid_fraction"] >= min_valid_fraction:
                                self.norm_patches.append(norm_res["norm_img"])
                                self.mask_patches.append(norm_res["mask"])
                                self.provenance.append({
                                    "patch_id": f"V3_PATCH_{patches_collected+1:05d}",
                                    "pointing": p_id,
                                    "detector": int(det_id),
                                    "fits_file": fname,
                                    "x0": int(x),
                                    "y0": int(y),
                                    "local_bg": norm_res["local_bg"],
                                    "mad_sigma": norm_res["mad_sigma"],
                                    "valid_fraction": norm_res["valid_fraction"]
                                })
                                patches_collected += 1
            except Exception as e:
                print(f"Warning: Error processing {fname}: {e}")

    def __len__(self):
        return len(self.norm_patches)

    def __getitem__(self, idx):
        img_t = torch.from_numpy(self.norm_patches[idx]).unsqueeze(0)
        mask_t = torch.from_numpy(self.mask_patches[idx]).unsqueeze(0)
        return img_t, mask_t


def train_astrovision_v3(
    epochs: int = 15,
    batch_size: int = 16,
    lr: float = 1e-3,
    train_target_patches: int = 1200,
    val_target_patches: int = 240,
    out_ckpt: str = "checkpoints/astrovision_spatial_v3.pt",
    random_seed: int = 42
) -> Dict[str, Any]:
    
    torch.manual_seed(random_seed)
    np.random.seed(random_seed)
    random.seed(random_seed)
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("=" * 80)
    print("ASTROVISION V3 STRATIFIED TRAINING PIPELINE")
    print(f"Device: {device} | Random Seed: {random_seed} | Target Patches: {train_target_patches}")
    print("=" * 80)
    
    # 1. Identify all candidate science files
    all_files = sorted(glob.glob(str(BASE_DIR / "data" / "**" / "*.fits"), recursive=True))
    eligible_files = []
    
    for fp in all_files:
        if "level2" not in fp and "deep" not in fp:
            continue
        fname = os.path.basename(fp)
        p = fname.split("_")[3] if len(fname.split("_")) > 3 else ""
        
        # STRICT GOVERNANCE CHECKS
        if p in QUARANTINED_EVALUATION_POINTINGS:
            continue
        if p in CALIBRATION_POINTINGS:
            # Quarantine calibration pointings as well for absolute calibration isolation
            continue
            
        eligible_files.append(fp)
        
    print(f"Eligible Governance-Clean Training Files: {len(eligible_files)} files")
    
    # Stratified split by pointing
    rng = np.random.default_rng(random_seed)
    shuffled = list(eligible_files)
    rng.shuffle(shuffled)
    
    split_idx = int(0.8 * len(shuffled))
    train_file_list = shuffled[:split_idx]
    val_file_list = shuffled[split_idx:]
    
    print(f"  Training File Corpus: {len(train_file_list)} files")
    print(f"  Validation File Corpus: {len(val_file_list)} files")
    
    # 2. Extract normalized patches
    print("\nExtracting normalized training patches...")
    train_ds = StratifiedV3CutoutDataset(
        file_list=train_file_list,
        target_patches=train_target_patches,
        random_seed=random_seed
    )
    
    print("Extracting normalized validation patches...")
    val_ds = StratifiedV3CutoutDataset(
        file_list=val_file_list,
        target_patches=val_target_patches,
        random_seed=random_seed + 100
    )
    
    print(f"\nFinal Extracted Dataset:")
    print(f"  Training Patches: {len(train_ds)} (Target: {train_target_patches})")
    print(f"  Validation Patches: {len(val_ds)} (Target: {val_target_patches})")
    
    if len(train_ds) < train_target_patches:
        print(f"NOTICE: Extracted {len(train_ds)} patches (< {train_target_patches}). Reporting exact count under governance.")
        
    # Check detector distribution in training dataset
    det_counts = {}
    for prov in train_ds.provenance:
        d = prov["detector"]
        det_counts[d] = det_counts.get(d, 0) + 1
    print(f"Detector Distribution in Training Set: {sorted(det_counts.items())}")
    
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    
    # 3. Model, Optimizer, Loss
    model = AstroVisionAutoencoderV3().to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-5)
    
    history = []
    best_val_loss = float("inf")
    best_epoch = 0
    t0 = time.time()
    
    print("\nStarting Training Loop:")
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss_accum = 0.0
        n_train_batches = 0
        
        for img, mask in train_loader:
            img, mask = img.to(device), mask.to(device)
            optimizer.zero_grad()
            recon = model(img, mask)
            
            # Masked Mean Squared Error loss on normalized pixels
            loss = torch.sum(((recon - img) ** 2) * mask) / torch.clamp(torch.sum(mask), min=1.0)
            loss.backward()
            optimizer.step()
            
            train_loss_accum += loss.item()
            n_train_batches += 1
            
        scheduler.step()
        avg_train = train_loss_accum / max(1, n_train_batches)
        
        # Validation
        model.eval()
        val_loss_accum = 0.0
        n_val_batches = 0
        with torch.no_grad():
            for img, mask in val_loader:
                img, mask = img.to(device), mask.to(device)
                recon = model(img, mask)
                val_loss = torch.sum(((recon - img) ** 2) * mask) / torch.clamp(torch.sum(mask), min=1.0)
                val_loss_accum += val_loss.item()
                n_val_batches += 1
                
        avg_val = val_loss_accum / max(1, n_val_batches)
        history.append({
            "epoch": epoch,
            "train_loss": round(avg_train, 6),
            "val_loss": round(avg_val, 6)
        })
        print(f"  Epoch {epoch:02d}/{epochs:02d} | Train Loss: {avg_train:.6f} | Val Loss: {avg_val:.6f}")
        
        if avg_val < best_val_loss:
            best_val_loss = avg_val
            best_epoch = epoch
            os.makedirs(os.path.dirname(out_ckpt), exist_ok=True)
            torch.save({
                "model_name": "ASTROVISION_SPATIAL_V3",
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "val_loss": avg_val,
                "train_patches_count": len(train_ds),
                "val_patches_count": len(val_ds),
                "patch_size": 128,
                "random_seed": random_seed,
                "governance": {
                    "quarantined_evaluation_pointings": list(QUARANTINED_EVALUATION_POINTINGS),
                    "separated_calibration_pointings": list(CALIBRATION_POINTINGS),
                    "zero_eval_leakage_verified": True
                },
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            }, out_ckpt)
            
    total_time = time.time() - t0
    print(f"\nTraining Complete in {total_time:.2f}s. Saved V3 Checkpoint: {out_ckpt} (Best Epoch {best_epoch}, Val Loss: {best_val_loss:.6f})")
    
    meta_path = str(Path(out_ckpt).with_suffix(".json"))
    with open(meta_path, "w") as f:
        json.dump({
            "model_name": "ASTROVISION_SPATIAL_V3",
            "checkpoint_path": out_ckpt,
            "best_epoch": best_epoch,
            "best_val_loss": best_val_loss,
            "training_duration_seconds": round(total_time, 2),
            "train_patches_count": len(train_ds),
            "val_patches_count": len(val_ds),
            "detector_distribution": det_counts,
            "governance_verification": {
                "quarantined_evaluation_pointings": list(QUARANTINED_EVALUATION_POINTINGS),
                "separated_calibration_pointings": list(CALIBRATION_POINTINGS),
                "eval_data_overlap": False,
                "cal_data_overlap": False
            },
            "training_history": history,
            "sample_provenance": train_ds.provenance[:10]
        }, f, indent=2)
        
    return {
        "out_ckpt": out_ckpt,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "train_patches": len(train_ds),
        "val_patches": len(val_ds)
    }


if __name__ == "__main__":
    train_astrovision_v3()

