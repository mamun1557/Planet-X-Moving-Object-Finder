"""
SPECTRA Training Pipeline
Unsupervised Infrared Spectral Anomaly Detection for SPHEREx 102-Channel Spectra
"""

import os
import glob
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from astropy.io import fits
from model import SpectralAnomalyDetector


class SyntheticAndExtractedSpectraDataset(Dataset):
    def __init__(self, num_samples: int = 500, num_channels: int = 102):
        self.num_channels = num_channels
        # Standard continuum + baseline emission templates
        wavelengths = np.linspace(0.75, 5.0, num_channels)
        self.spectra = []
        self.variances = []

        for _ in range(num_samples):
            # Simulated blackbody/power-law nominal stellar continuum
            temp = np.random.uniform(3000, 8000)
            # Planck approx
            c1, c2 = 1.191e8, 1.439e4
            bb = (c1 / (wavelengths**5)) / (np.exp(c2 / (wavelengths * temp)) - 1.0)
            bb_norm = bb / np.max(bb)

            # Noise
            sigma = np.random.uniform(0.01, 0.05, num_channels)
            noisy_spec = bb_norm + np.random.normal(0, sigma)

            self.spectra.append(noisy_spec.astype(np.float32))
            self.variances.append((sigma**2).astype(np.float32))

    def __len__(self):
        return len(self.spectra)

    def __getitem__(self, idx):
        return torch.from_numpy(self.spectra[idx]), torch.from_numpy(self.variances[idx])


def train_spectra(epochs: int = 5, batch_size: int = 32, lr: float = 1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training SPECTRA on device: {device}")

    dataset = SyntheticAndExtractedSpectraDataset()
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = SpectralAnomalyDetector(num_channels=102).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for spec, var in loader:
            spec, var = spec.to(device), var.to(device)
            optimizer.zero_grad()
            recon = model(spec)
            loss = torch.mean(((recon - spec) ** 2) / var)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / len(loader)
        print(f"Epoch {epoch}/{epochs} - Spectral Chi2 Loss: {avg_loss:.4f}")

    os.makedirs("checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "checkpoints/spectra_latest.pt")
    print("Saved checkpoint: checkpoints/spectra_latest.pt")


if __name__ == "__main__":
    train_spectra()
