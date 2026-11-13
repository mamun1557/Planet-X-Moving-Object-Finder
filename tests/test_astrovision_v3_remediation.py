"""
Unit Tests for ASTROVISION V3 Remediation (Task 1.1U)
Verifies:
1. Fatal-pixel masking and median imputation.
2. Saturated-star contamination rejection (PILOT_001118 scenario).
3. Robust local background and noise normalization (P0008 vs P0010).
4. Aperture-integrated anomaly scoring for point and extended sources.
5. Partition governance and checkpoint immutability.
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import numpy as np
import pytest
import torch

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from models.astrovision.model_v3 import (
    AstroVisionAutoencoderV3,
    RobustLocalNormalizer,
    ApertureAnomalyScorer,
    FATAL_FLAG_MASK
)


def test_fatal_pixel_masking_and_imputation():
    """Verifies that fatal flags, NaNs, and extreme saturated values are properly imputed and masked."""
    H, W = 128, 128
    rng = np.random.default_rng(42)
    
    # Nominal clean sky: median 0.20, noise sigma 0.01
    img = rng.normal(loc=0.20, scale=0.01, size=(H, W)).astype(np.float32)
    var = np.full((H, W), 1e-4, dtype=np.float32)
    flags = np.zeros((H, W), dtype=np.int32)
    
    # Inject fatal defects
    # 1. Dead/nonfunctional pixel (flag 64)
    img[10, 10] = 0.0
    flags[10, 10] = 64
    
    # 2. SUR regression error (flag 4) with NaN
    img[20, 20] = np.nan
    flags[20, 20] = 4
    
    # 3. Cosmic ray / transient (flag 1) with huge spike
    img[30, 30] = 50000.0
    flags[30, 30] = 1
    
    res = RobustLocalNormalizer.normalize_patch(img, var, flags, fatal_mask_bits=FATAL_FLAG_MASK)
    
    # Checks
    assert np.all(np.isfinite(res["norm_img"])), "Imputed normalized image must be completely finite!"
    assert res["mask"][10, 10] == 0.0, "Dead pixel must be masked out (0.0)!"
    assert res["mask"][20, 20] == 0.0, "NaN pixel must be masked out (0.0)!"
    assert res["mask"][30, 30] == 0.0, "Cosmic ray must be masked out (0.0)!"
    
    # Imputed pixel value should be close to 0.0 in zero-centered normalized space
    assert abs(res["norm_img"][10, 10]) < 0.1, "Imputed pixel must equal local median background!"
    assert abs(res["norm_img"][20, 20]) < 0.1, "Imputed NaN pixel must equal local median background!"
    assert abs(res["norm_img"][30, 30]) < 0.1, "Cosmic ray spike must be replaced with local median!"
    
    # Clean pixels must remain valid (mask = 1.0)
    assert res["mask"][64, 64] == 1.0, "Clean center pixel must remain valid (1.0)!"


def test_saturated_star_contamination_rejection():
    """
    Simulates the PILOT_001118 forensic failure:
    A 75,000 MJy/sr saturated star is present at (93, 53) in a 128x128 cutout.
    Verifies that MaskAwareConv2d and RobustLocalNormalizer reject convolutional bleed,
    preventing false anomaly explosion at the clean center (64, 64).
    """
    H, W = 128, 128
    rng = np.random.default_rng(101)
    
    # Clean sky: median = 0.10, noise = 0.005
    img = rng.normal(loc=0.10, scale=0.005, size=(H, W)).astype(np.float32)
    var = np.full((H, W), 2.5e-5, dtype=np.float32)
    flags = np.zeros((H, W), dtype=np.int32)
    
    # Place a 75,000 MJy/sr saturated star with fatal flag 2097217 at (93, 53)
    img[53, 93] = 75035.55
    flags[53, 93] = 2097217  # Fatal SUR error + Source flag
    
    # Preprocess with V3 normalizer
    norm_res = RobustLocalNormalizer.normalize_patch(img, var, flags)
    
    # Model inference
    model = AstroVisionAutoencoderV3()
    model.eval()
    
    t_img = torch.from_numpy(norm_res["norm_img"]).unsqueeze(0).unsqueeze(0)
    t_mask = torch.from_numpy(norm_res["mask"]).unsqueeze(0).unsqueeze(0)
    
    with torch.no_grad():
        recon = model(t_img, t_mask)
        anom_map = model.compute_anomaly_map(t_img, t_mask)
        
    anom_np = anom_map.squeeze().numpy()
    
    # Center pixel (64, 64) is clean sky
    center_anom = anom_np[64, 64]
    
    # In V2 without mask awareness, center anomaly exploded to 409,866!
    # In V3 with mask-aware preprocessing and PConv, it must remain well bounded (< 100).
    assert center_anom < 100.0, f"Contamination bleed detected! Center anomaly={center_anom:.2f} (expected < 100.0)"


def test_local_background_and_noise_normalization():
    """
    Verifies that RobustLocalNormalizer eliminates domain shift between high-zodi (P0008, 0.70 MJy/sr)
    and low-zodi (P0010 NEP, 0.08 MJy/sr) regimes.
    """
    H, W = 128, 128
    rng = np.random.default_rng(202)
    
    # High-zodiacal patch (Pointing 0008)
    img_high = rng.normal(loc=0.70, scale=0.04, size=(H, W)).astype(np.float32)
    var_high = np.full((H, W), 1.6e-3, dtype=np.float32)
    flags_high = np.zeros((H, W), dtype=np.int32)
    
    # Low-zodiacal patch (Pointing 0010 NEP)
    img_low = rng.normal(loc=0.08, scale=0.01, size=(H, W)).astype(np.float32)
    var_low = np.full((H, W), 1.0e-4, dtype=np.float32)
    flags_low = np.zeros((H, W), dtype=np.int32)
    
    res_high = RobustLocalNormalizer.normalize_patch(img_high, var_high, flags_high)
    res_low = RobustLocalNormalizer.normalize_patch(img_low, var_low, flags_low)
    
    # Both normalized images must be centered near 0.0
    assert abs(np.median(res_high["norm_img"])) < 0.05, "High-zodi normalized image must have ~0.0 median!"
    assert abs(np.median(res_low["norm_img"])) < 0.05, "Low-zodi normalized image must have ~0.0 median!"
    
    # Robust dispersion must be normalized to ~1.0
    mad_high = 1.4826 * np.median(np.abs(res_high["norm_img"]))
    mad_low = 1.4826 * np.median(np.abs(res_low["norm_img"]))
    assert abs(mad_high - 1.0) < 0.1, "High-zodi normalized image must have ~1.0 MAD!"
    assert abs(mad_low - 1.0) < 0.1, "Low-zodi normalized image must have ~1.0 MAD!"


def test_aperture_integrated_scoring():
    """Verifies aperture-integrated anomaly scoring on point vs extended source synthetic footprints."""
    H, W = 128, 128
    anom_map = np.zeros((H, W), dtype=np.float32)
    mask = np.ones((H, W), dtype=np.float32)
    
    cx, cy = 64.0, 64.0
    yy, xx = np.ogrid[:H, :W]
    r_sq = (xx - cx)**2 + (yy - cy)**2
    
    # Inject a diffuse extended Gaussian anomaly (sigma = 3.0 pix)
    anom_map += 20.0 * np.exp(-r_sq / (2 * 3.0**2))
    
    scores = ApertureAnomalyScorer.compute_scores(
        anomaly_map=anom_map,
        mask=mask,
        center_x=cx,
        center_y=cy,
        point_aperture_radius=2.5,
        extended_aperture_radius=5.0
    )
    
    # Extended integrated score should accumulate flux across the aperture
    assert scores["peak_chi2"] == pytest.approx(20.0, rel=1e-2)
    assert scores["ext_integrated_chi2"] > scores["pt_integrated_chi2"], "Extended aperture must capture more diffuse flux than point aperture!"
    assert scores["ext_valid_pixels"] > scores["pt_valid_pixels"]


def test_partition_governance_and_v2_immutability():
    """Verifies that V2 checkpoint hash is unchanged and V3 metadata confirms zero evaluation leakage."""
    # 1. Historical V2 Checkpoint Check
    v2_path = "checkpoints/astrovision_spatial_v2.pt"
    assert os.path.exists(v2_path), "Historical V2 checkpoint must exist!"
    
    h = hashlib.sha256()
    with open(v2_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    actual_v2_hash = h.hexdigest()
    expected_v2_hash = "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557"
    assert actual_v2_hash == expected_v2_hash, "CRITICAL: Historical V2 checkpoint has been mutated!"

    # 2. V3 Metadata Governance Check
    v3_meta_path = "checkpoints/astrovision_spatial_v3.json"
    assert os.path.exists(v3_meta_path), "V3 metadata JSON must exist!"
    with open(v3_meta_path) as f:
        meta = json.load(f)
        
    gov = meta["governance_verification"]
    assert gov["eval_data_overlap"] is False, "CRITICAL: V3 training must have ZERO evaluation overlap!"
    assert gov["cal_data_overlap"] is False, "CRITICAL: V3 training must have ZERO calibration overlap!"
    assert meta["train_patches_count"] == 1200, "V3 must train on exactly 1,200 patches!"
