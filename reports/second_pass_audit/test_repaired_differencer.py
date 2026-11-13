import os
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from reproject import reproject_interp
from scipy.ndimage import binary_dilation, gaussian_filter

FATAL_FLAG_MASK = 615  # (1<<0) | (1<<1) | (1<<2) | (1<<5) | (1<<6) | (1<<9)

def test_differencing_repair():
    base_dir = os.path.abspath(".")
    f1 = os.path.join(base_dir, 'data', 'spherex', 'qr2', 'level2', 'level2_2025W17_4B_0001_2D2_spx_l2b-v20-2025-240.fits')
    f2 = os.path.join(base_dir, 'data', 'spherex', 'qr2', 'level2', 'level2_2025W17_4B_0001_3D2_spx_l2b-v20-2025-240.fits')

    with fits.open(f1) as h1, fits.open(f2) as h2:
        img1 = h1['IMAGE'].data.astype(np.float32)
        hdr1 = h1['IMAGE'].header
        var1 = h1['VARIANCE'].data.astype(np.float32)
        mask1 = h1['FLAGS'].data.astype(np.int32)

        img2 = h2['IMAGE'].data.astype(np.float32)
        hdr2 = h2['IMAGE'].header
        var2 = h2['VARIANCE'].data.astype(np.float32)
        mask2 = h2['FLAGS'].data.astype(np.int32)

    w1 = WCS(hdr1)
    w2 = WCS(hdr2)

    # 1. Fatal masks in raw frames
    fatal1 = (mask1 & FATAL_FLAG_MASK) > 0
    fatal2 = (mask2 & FATAL_FLAG_MASK) > 0

    # 2. Morphological dilation of defects in raw frame (radius 2)
    struct = np.ones((5, 5), dtype=bool)
    fatal1_dilated = binary_dilation(fatal1, structure=struct)
    fatal2_dilated = binary_dilation(fatal2, structure=struct)

    # 3. Reproject img2, var2, and fatal2_dilated onto wcs1
    print("Reprojecting img2 and dilated fatal mask...")
    img2_reproj, _ = reproject_interp((img2, w2), w1, shape_out=img1.shape)
    var2_reproj, _ = reproject_interp((var2, w2), w1, shape_out=img1.shape)
    fatal2_reproj, _ = reproject_interp((fatal2_dilated.astype(float), w2), w1, shape_out=img1.shape, order="nearest-neighbor")

    # Further dilate the reprojected mask by 1 pixel to seal any boundary interpolation leakage
    fatal2_reproj_dilated = binary_dilation(fatal2_reproj > 0.05, structure=np.ones((3, 3), dtype=bool))

    # Combined valid mask (clean pixels only)
    valid_mask = (~fatal1_dilated) & (~fatal2_reproj_dilated) & (~np.isnan(img1)) & (~np.isnan(img2_reproj))

    # Combined variance
    total_var = var1 + np.nan_to_num(var2_reproj, nan=1e6)
    total_sigma = np.sqrt(np.maximum(total_var, 1e-6))

    # Background-subtracted difference
    diff_raw = img2_reproj - img1
    bg_offset = np.nanmedian(diff_raw[valid_mask])
    diff = diff_raw - bg_offset

    # Significance map
    significance = np.where(valid_mask, np.abs(diff) / total_sigma, 0.0)

    # Check the exact defect pixel location from the audit (y=1894, x=1415)
    y_defect, x_defect = 1894, 1415
    print(f"\n--- Defect Location Check (y={y_defect}, x={x_defect}) ---")
    print(f"Is defect pixel valid in repaired mask? {valid_mask[y_defect, x_defect]} (Expected: False)")
    print(f"Significance at defect pixel: {significance[y_defect, x_defect]:.4f} (Expected: 0.0)")

    # Max significance across the entire array
    max_idx = np.unravel_index(np.argmax(significance), significance.shape)
    max_sig = significance[max_idx]
    print(f"\nRepaired Global Max Significance: {max_sig:.2f} at {max_idx}")
    print(f"Original un-repaired Max Significance was: 152.21")

    # Candidate pixel count above 5-sigma
    cands = np.sum(significance > 5.0)
    print(f"Pixels with significance > 5 sigma: {cands}")

if __name__ == '__main__':
    test_differencing_repair()
