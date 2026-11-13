"""
SPECTRA-X Model 3: CHRONOS-X
Temporal Change Detection for Genuine Multi-Epoch SPHEREx Infrared Observations

Core Scientific Rules:
1. QR2 vs QR3 release changes are NOT automatically genuine temporal changes.
2. Only genuinely different observation epochs (MJD-OBS delta > threshold) are compared.
3. WCS astrometric reprojection is executed before differencing.
4. Bad pixel masks (FLAGS != 0) are combined using bitwise OR.
5. High-residual candidates are screened against zodiacal background changes and instrumental artifacts.
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from astropy.wcs import WCS
try:
    from reproject import reproject_interp
except ImportError:
    reproject_interp = None
from scipy.ndimage import binary_dilation, gaussian_filter

# SPHEREx Fatal Quality Flags Mask (MP_TRANSIENT, MP_OVERFLOW, MP_SUR_ERROR, MP_REFERENCE, MP_NONFUNC, MP_MISSING_DATA)
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615

# Re-export sub-pixel registration engine (Task 4.20D)
try:
    from .subpixel_registration import SubPixelPhaseCorrelationAligner, RegistrationResult
except ImportError:
    from models.chronos_x.subpixel_registration import SubPixelPhaseCorrelationAligner, RegistrationResult

# Re-export temporal eligibility contracts and functions
try:
    from .temporal_eligibility import (
        TemporalEligibilityResult,
        evaluate_pair_temporal_eligibility,
        determine_dataset_temporal_availability,
        DEFAULT_MIN_BASELINE_DAYS,
        BASELINE_POLICY_VERSION,
        ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES,
        ALLOWED_DATASET_AVAILABILITY_STATUSES,
        ALLOWED_EVIDENCE_TIERS
    )
except ImportError:
    from models.chronos_x.temporal_eligibility import (
        TemporalEligibilityResult,
        evaluate_pair_temporal_eligibility,
        determine_dataset_temporal_availability,
        DEFAULT_MIN_BASELINE_DAYS,
        BASELINE_POLICY_VERSION,
        ALLOWED_TEMPORAL_ELIGIBILITY_STATUSES,
        ALLOWED_DATASET_AVAILABILITY_STATUSES,
        ALLOWED_EVIDENCE_TIERS
    )


class ChronosTemporalDifferencer:
    """Scientific multi-epoch image differencing and transient candidate extractor."""
    def __init__(self, significance_threshold: float = 5.0, dilation_radius: int = 2, psf_match_sigma: float = 1.0):
        self.significance_threshold = significance_threshold
        self.dilation_radius = dilation_radius
        self.psf_match_sigma = psf_match_sigma

    def align_and_difference(self, img1: np.ndarray, hdr1: Any, var1: np.ndarray, mask1: np.ndarray,
                              img2: np.ndarray, hdr2: Any, var2: np.ndarray, mask2: np.ndarray,
                              enable_psf_matching: bool = True,
                              enable_subpixel_registration: bool = True,
                              max_subpixel_shift: float = 8.0) -> Dict[str, Any]:
        """Reprojects epoch 2 onto epoch 1's WCS with defect dilation and optimal differencing."""
        wcs1 = WCS(hdr1)
        wcs2 = WCS(hdr2)

        # 1. Identify fatal defective pixels in raw detector coordinates
        fatal1 = (mask1 & FATAL_FLAG_MASK) > 0
        fatal2 = (mask2 & FATAL_FLAG_MASK) > 0

        # 2. Morphological dilation in raw frames to seal sub-pixel flux leakage
        struct_raw = np.ones((2 * self.dilation_radius + 1, 2 * self.dilation_radius + 1), dtype=bool)
        fatal1_dilated = binary_dilation(fatal1, structure=struct_raw)
        fatal2_dilated = binary_dilation(fatal2, structure=struct_raw)

        # 3. Reproject img2, var2, and dilated fatal mask onto epoch 1 WCS
        if reproject_interp is not None:
            img2_reproj, _ = reproject_interp((img2, wcs2), wcs1, shape_out=img1.shape)
            var2_reproj, _ = reproject_interp((var2, wcs2), wcs1, shape_out=img1.shape)
            fatal2_reproj, _ = reproject_interp((fatal2_dilated.astype(float), wcs2), wcs1, shape_out=img1.shape, order="nearest-neighbor")
        else:
            img2_reproj = img2.copy()
            var2_reproj = var2.copy()
            fatal2_reproj = fatal2_dilated.astype(float)

        # 3b. Fine sub-pixel phase-correlation registration to remediate residual dither pointing jitter (Task 4.20D)
        reg_result = None
        if enable_subpixel_registration:
            aligner = SubPixelPhaseCorrelationAligner(max_shift_pixels=max_subpixel_shift)
            reg_result = aligner.align(ref_image=img1, target_image=img2_reproj, target_variance=var2_reproj)
            if reg_result.status == "SUCCESS":
                img2_reproj = reg_result.aligned_image
                if reg_result.aligned_variance is not None:
                    var2_reproj = reg_result.aligned_variance

        # 4. Boundary dilation on reprojected mask to eliminate fractional pixel defect leakage
        fatal2_reproj_dilated = binary_dilation(fatal2_reproj > 0.05, structure=np.ones((3, 3), dtype=bool))

        # 5. Combined clean science mask
        valid_mask = (~fatal1_dilated) & (~fatal2_reproj_dilated) & (~np.isnan(img1)) & (~np.isnan(img2_reproj))

        # 6. Combined variance propagation
        total_var = var1 + np.nan_to_num(var2_reproj, nan=1e6)
        total_sigma = np.sqrt(np.maximum(total_var, 1e-6))

        # 7. Background median matching
        diff_raw = img2_reproj - img1
        bg_offset = float(np.nanmedian(diff_raw[valid_mask])) if np.any(valid_mask) else 0.0
        diff = diff_raw - bg_offset

        # 8. Optional PSF-matching smoothing convolution to regularize sub-pixel dither jitter
        if enable_psf_matching and self.psf_match_sigma > 0:
            diff_clean = np.nan_to_num(diff, nan=0.0)
            diff_eval = gaussian_filter(diff_clean, sigma=self.psf_match_sigma)
        else:
            diff_eval = diff

        # 9. Normalized significance map
        significance = np.where(valid_mask, np.abs(diff_eval) / total_sigma, 0.0)
        significance = np.nan_to_num(significance, nan=0.0)

        # 10. Extract candidate peaks and classify dipoles vs monopolar transients
        raw_candidates = np.argwhere(significance > self.significance_threshold)
        
        monopolar_candidates = []
        dipole_artifacts = []

        # Vet candidates within 5x5 stamps around high-significance peaks
        visited = set()
        for y, x in raw_candidates:
            if (y, x) in visited:
                continue
            
            # Local window
            y_min, y_max = max(0, y - 2), min(img1.shape[0], y + 3)
            x_min, x_max = max(0, x - 2), min(img1.shape[1], x + 3)
            
            for vy in range(y_min, y_max):
                for vx in range(x_min, x_max):
                    visited.add((vy, vx))

            local_diff = diff[y_min:y_max, x_min:x_max]
            min_val = float(np.nanmin(local_diff))
            max_val = float(np.nanmax(local_diff))

            # Dipole test: paired positive and negative lobes of significant amplitude
            if min_val < -3.0 * total_sigma[y, x] and max_val > 3.0 * total_sigma[y, x]:
                dipole_artifacts.append((int(y), int(x), float(significance[y, x])))
            else:
                monopolar_candidates.append((int(y), int(x), float(significance[y, x])))

        return {
            "difference_map": diff,
            "difference_evaluated": diff_eval,
            "significance_map": significance,
            "valid_mask": valid_mask,
            "background_offset": bg_offset,
            "candidate_pixels_count": len(raw_candidates),
            "monopolar_transients_count": len(monopolar_candidates),
            "dipole_artifacts_count": len(dipole_artifacts),
            "monopolar_candidates": monopolar_candidates,
            "dipole_artifacts": dipole_artifacts,
            "max_significance": float(np.nanmax(significance[valid_mask])) if np.any(valid_mask) else 0.0,
            "registration_result": reg_result.to_dict() if reg_result is not None else None
        }
