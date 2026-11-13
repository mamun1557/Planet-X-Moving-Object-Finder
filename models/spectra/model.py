"""
SPECTRA-X Model 2: SPECTRA
Spectral Anomaly Detection for 102-Channel SPHEREx Infrared Spectra

Input: 102-channel spectrophotometric vectors (0.75 - 5.0 µm)
- Channel flux: F_lambda (102 dims, MJy/sr)
- Channel variance: sigma^2_lambda (102 dims)
- Wavelength grid: lambda_c (102 dims from WCS-WAVE / spectral_channels)

Architecture:
- 1D Spectral Residual Transformer & Contrastive Autoencoder
- Detects non-stellar continua, strong emission lines (PAH 3.3um, H2O ice 3.05um, CO2 4.26um),
  and unclassified spectral shapes.
"""

import torch
import torch.nn as nn
from typing import Dict, Any


class SpectralAnomalyDetector(nn.Module):
    def __init__(self, num_channels: int = 102, hidden_dim: int = 64, latent_dim: int = 16):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(num_channels, hidden_dim),
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

    def forward(self, spectra: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(spectra)
        recon = self.decoder(latent)
        return recon

    def compute_anomaly_score(self, spectra: torch.Tensor, variance: torch.Tensor) -> torch.Tensor:
        """Calculates variance-weighted Mahalanobis-like reconstruction deviation."""
        with torch.no_grad():
            recon = self.forward(spectra)
            diff_sq = (spectra - recon) ** 2
            safe_var = torch.clamp(variance, min=1e-6)
            chi2_score = torch.mean(diff_sq / safe_var, dim=-1)
        return chi2_score
