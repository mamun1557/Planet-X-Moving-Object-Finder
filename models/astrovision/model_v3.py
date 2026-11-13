"""
SPECTRA-X Model 1: ASTROVISION V3
Remediated Mask-Aware, Background-Normalized Spatial Autoencoder for SPHEREx Anomaly Detection

Architecture Improvements:
1. Mask-Aware Partial Convolutions / Input Defect Filtering:
   - Prevents masked, fatal, and saturated pixels from bleeding into the latent representation.
2. Zero-Centered, Robust MAD-Normalized Preprocessing:
   - Normalizes input patches to zero-mean and unit robust dispersion (MAD).
   - Eliminates DC background bias across varying zodiacal regimes (ecliptic vs. NEP polar sky).
3. Aperture-Integrated Anomaly Scoring:
   - Spatially integrates normalized reconstruction residuals over matched apertures.
   - Uses nominal local sky variance to prevent Poisson shot-noise denominator damping.
"""

import math
from typing import Tuple, Dict, Any, Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

FATAL_FLAG_MASK = 615


class MaskAwareConv2d(nn.Module):
    """
    Partial Convolution layer that renormalizes convolutional output by valid pixel fraction.
    If receptive field contains masked/fatal pixels, their contribution is zeroed and
    the convolution is scaled by (k_w * k_h) / sum(mask) to prevent artifact bleed.
    """
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, stride: int = 1, padding: int = 1, bias: bool = False):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, stride=stride, padding=padding, bias=bias)
        self.kernel_size = kernel_size
        self.stride = stride
        self.padding = padding
        
        # Fixed kernel for calculating mask coverage ratio
        self.mask_kernel = nn.Parameter(
            torch.ones(1, 1, kernel_size, kernel_size),
            requires_grad=False
        )

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        # Zero out invalid/fatal pixels before convolution
        x_masked = x * mask
        raw_out = self.conv(x_masked)
        
        # Calculate mask sum over the sliding window
        with torch.no_grad():
            mask_sum = F.conv2d(mask, self.mask_kernel, stride=self.stride, padding=self.padding)
            # Mask ratio = (k*k) / sum(mask)
            k_area = float(self.kernel_size * self.kernel_size)
            ratio = k_area / torch.clamp(mask_sum, min=1.0)
            ratio = torch.clamp(ratio, max=10.0)
            new_mask = (mask_sum > 0).float()
            
        out = raw_out * ratio
        return out, new_mask


class AstroVisionAutoencoderV3(nn.Module):
    """
    Version 3: Mask-Aware Spatial Autoencoder for SPHEREx Anomaly Detection.
    Operates on zero-mean, unit-MAD normalized cutouts with input mask conditioning.
    """
    def __init__(self, in_channels: int = 1, latent_dim: int = 128):
        super().__init__()
        self.in_channels = in_channels
        self.latent_dim = latent_dim

        # Encoder with mask propagation
        self.enc1 = MaskAwareConv2d(in_channels, 32, kernel_size=4, stride=2, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.act1 = nn.LeakyReLU(0.2, inplace=True)

        self.enc2 = MaskAwareConv2d(32, 64, kernel_size=4, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.act2 = nn.LeakyReLU(0.2, inplace=True)

        self.enc3 = MaskAwareConv2d(64, 128, kernel_size=4, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.act3 = nn.LeakyReLU(0.2, inplace=True)

        self.enc4 = MaskAwareConv2d(128, latent_dim, kernel_size=4, stride=2, padding=1)
        self.act4 = nn.LeakyReLU(0.2, inplace=True)

        # Decoder
        self.dec1 = nn.ConvTranspose2d(latent_dim, 128, kernel_size=4, stride=2, padding=1)
        self.dec_bn1 = nn.BatchNorm2d(128)
        self.dec_act1 = nn.ReLU(inplace=True)

        self.dec2 = nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1)
        self.dec_bn2 = nn.BatchNorm2d(64)
        self.dec_act2 = nn.ReLU(inplace=True)

        self.dec3 = nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1)
        self.dec_bn3 = nn.BatchNorm2d(32)
        self.dec_act3 = nn.ReLU(inplace=True)

        self.dec4 = nn.ConvTranspose2d(32, in_channels, kernel_size=4, stride=2, padding=1)

    def forward(self, image: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass with mask-aware convolution in the encoder.
        If mask is None, assumes all pixels are valid.
        """
        if mask is None:
            mask = torch.ones_like(image[:, :1, :, :])

        x, m = self.enc1(image, mask)
        x = self.act1(self.bn1(x))

        x, m = self.enc2(x, m)
        x = self.act2(self.bn2(x))

        x, m = self.enc3(x, m)
        x = self.act3(self.bn3(x))

        x, m = self.enc4(x, m)
        x = self.act4(x)

        # Decoder
        d = self.dec_act1(self.dec_bn1(self.dec1(x)))
        d = self.dec_act2(self.dec_bn2(self.dec2(d)))
        d = self.dec_act3(self.dec_bn3(self.dec3(d)))
        recon = self.dec4(d)
        return recon

    def compute_anomaly_map(
        self,
        image_norm: torch.Tensor,
        mask: torch.Tensor,
        nominal_var_norm: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Computes normalized reconstruction residual map in normalized units.
        Residual: (I_norm - Recon)^2 / var_norm * mask.
        If nominal_var_norm is None, assumes unit variance (var_norm = 1.0).
        """
        with torch.no_grad():
            recon = self.forward(image_norm, mask)
            residual_sq = (image_norm - recon) ** 2
            if nominal_var_norm is not None:
                safe_var = torch.clamp(nominal_var_norm, min=1e-4)
                anom_map = (residual_sq / safe_var) * mask
            else:
                anom_map = residual_sq * mask
        return anom_map


class RobustLocalNormalizer:
    """
    Scientifically defensible local background and noise normalization.
    Calculates robust median background and MAD dispersion on unflagged pixels.
    """
    @staticmethod
    def normalize_patch(
        raw_img: np.ndarray,
        raw_var: np.ndarray,
        raw_flags: np.ndarray,
        fatal_mask_bits: int = FATAL_FLAG_MASK,
        saturation_flux_limit: float = 5000.0
    ) -> Dict[str, Any]:
        """
        Preprocesses a raw patch with:
        1. Fatal pixel identification & local median imputation.
        2. Robust median background subtraction.
        3. Robust MAD scaling.
        4. Nominal background variance propagation.
        """
        # Valid pixels: unflagged, finite, not saturated
        valid = (
            ((raw_flags & fatal_mask_bits) == 0) &
            np.isfinite(raw_img) &
            np.isfinite(raw_var) &
            (raw_img < saturation_flux_limit) &
            (raw_var > 0)
        )
        
        if np.sum(valid) < 16:
            # Fallback for degenerate cutouts
            med_bg = float(np.nanmedian(raw_img)) if np.any(np.isfinite(raw_img)) else 0.0
            mad_sigma = 1.0
            med_var = 1e-3
        else:
            med_bg = float(np.median(raw_img[valid]))
            # 1.4826 * MAD matches Gaussian sigma
            mad_sigma = float(1.4826 * np.median(np.abs(raw_img[valid] - med_bg)))
            mad_sigma = max(mad_sigma, 1e-4)
            med_var = float(np.median(raw_var[valid]))
            med_var = max(med_var, 1e-6)

        # Fatal pixel imputation: replace invalid pixels with local background
        imputed_img = raw_img.copy()
        imputed_img[~valid] = med_bg

        # Zero-centered, MAD-normalized image
        norm_img = (imputed_img - med_bg) / mad_sigma
        norm_var = raw_var / (mad_sigma ** 2)
        norm_nominal_sky_var = med_var / (mad_sigma ** 2)

        # Explicit validity mask
        defect_mask = valid.astype(np.float32)

        return {
            "norm_img": norm_img.astype(np.float32),
            "norm_var": norm_var.astype(np.float32),
            "norm_nominal_sky_var": float(norm_nominal_sky_var),
            "mask": defect_mask,
            "local_bg": med_bg,
            "mad_sigma": mad_sigma,
            "valid_fraction": float(np.mean(valid))
        }


class ApertureAnomalyScorer:
    """
    Aperture-integrated anomaly scoring engine.
    Supports point-source (tight) and extended-source (broad) apertures.
    Uses nominal sky variance to prevent Poisson shot variance dilution.
    """
    @staticmethod
    def compute_scores(
        anomaly_map: np.ndarray,
        mask: np.ndarray,
        center_x: float,
        center_y: float,
        point_aperture_radius: float = 2.5,
        extended_aperture_radius: float = 5.0
    ) -> Dict[str, float]:
        H, W = anomaly_map.shape
        yy, xx = np.ogrid[:H, :W]
        dist_sq = (xx - center_x)**2 + (yy - center_y)**2

        # 1. Historical Single Peak-Pixel Score
        match_mask = (dist_sq <= point_aperture_radius**2) & (mask > 0.5)
        if np.any(match_mask):
            peak_chi2 = float(np.max(anomaly_map[match_mask]))
        else:
            peak_chi2 = 0.0

        # 2. Point-Source Aperture Integrated Anomaly Score
        pt_ap_mask = (dist_sq <= point_aperture_radius**2) & (mask > 0.5)
        pt_valid_pixels = int(np.sum(pt_ap_mask))
        if pt_valid_pixels > 0:
            pt_integrated_chi2 = float(np.sum(anomaly_map[pt_ap_mask]))
            pt_mean_chi2 = float(np.mean(anomaly_map[pt_ap_mask]))
        else:
            pt_integrated_chi2 = 0.0
            pt_mean_chi2 = 0.0

        # 3. Extended-Source Aperture Integrated Anomaly Score
        ext_ap_mask = (dist_sq <= extended_aperture_radius**2) & (mask > 0.5)
        ext_valid_pixels = int(np.sum(ext_ap_mask))
        if ext_valid_pixels > 0:
            ext_integrated_chi2 = float(np.sum(anomaly_map[ext_ap_mask]))
            ext_mean_chi2 = float(np.mean(anomaly_map[ext_ap_mask]))
        else:
            ext_integrated_chi2 = 0.0
            ext_mean_chi2 = 0.0

        # 4. Multi-Scale Harmonic Score (Harmonic blend of peak and integrated)
        harmonic_score = float(math.sqrt(max(0.0, peak_chi2) * max(0.0, ext_mean_chi2)))

        return {
            "peak_chi2": peak_chi2,
            "pt_integrated_chi2": pt_integrated_chi2,
            "pt_mean_chi2": pt_mean_chi2,
            "pt_valid_pixels": pt_valid_pixels,
            "ext_integrated_chi2": ext_integrated_chi2,
            "ext_mean_chi2": ext_mean_chi2,
            "ext_valid_pixels": ext_valid_pixels,
            "harmonic_score": harmonic_score
        }

