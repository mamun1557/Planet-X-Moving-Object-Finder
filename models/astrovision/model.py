"""
SPECTRA-X Model 1: ASTROVISION
Image Anomaly Detection for SPHEREx Infrared Observations

Input: SPHEREx Multi-Extension FITS (MEF) Level-2 products
- Primary Image: (2040 x 2040, float32, MJy/sr)
- Uncertainty / Variance: (2040 x 2040, float32, MJy2/sr2)
- Flag / Quality Mask: (2040 x 2040, int32)
- Calibration: Gain matrices, Dark current, Nonfunctional pixel maps

Architecture:
- Mask-aware Spatial Autoencoder / Anomaly Estimator
- Reconstruction loss weighted by inverse variance (1 / sigma^2)
- Ignores masked / bad pixels (FLAGS != 0)
"""

import torch
import torch.nn as nn
from typing import Tuple, Dict, Any


class MaskAwareConvBlock(nn.Module):
    """Convolution block with mask propagation to prevent artifact bleed."""
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn = nn.BatchNorm2d(out_channels)
        self.act = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x: torch.Tensor, mask: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        x_masked = x * mask
        out = self.conv(x_masked)
        out = self.bn(out)
        out = self.act(out)
        return out, mask


class AstroVisionAutoencoder(nn.Module):
    """
    Self-supervised spatial anomaly detector for SPHEREx infrared image cutouts.
    Trained on clean unflagged sky regions to reconstruct nominal backgrounds and point sources.
    Anomalies are detected via high normalized reconstruction error: (I - I_hat)^2 / Variance.
    """
    def __init__(self, in_channels: int = 1, latent_dim: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Conv2d(in_channels, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(32, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(64, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(128, latent_dim, kernel_size=4, stride=2, padding=1),
            nn.LeakyReLU(0.2, inplace=True)
        )

        self.decoder = nn.Sequential(
            nn.ConvTranspose2d(latent_dim, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, in_channels, kernel_size=4, stride=2, padding=1)
        )

    def forward(self, image: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(image)
        reconstruction = self.decoder(latent)
        return reconstruction

    def compute_anomaly_map(self, image: torch.Tensor, variance: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
        """Computes chi2-style normalized reconstruction residual map."""
        with torch.no_grad():
            recon = self.forward(image)
            residual_sq = (image - recon) ** 2
            safe_var = torch.clamp(variance, min=1e-6)
            norm_residual = (residual_sq / safe_var) * mask
        return norm_residual
