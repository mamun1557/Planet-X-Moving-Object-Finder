"""
ASTROVISION Training Pipeline
Self-Supervised Spatial Anomaly Detection on SPHEREx Infrared Images
"""

import os
import glob
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import numpy as np
from astropy.io import fits
from model import AstroVisionAutoencoder


class SPHERExCutoutDataset(Dataset):
    def __init__(self, fits_dir: str = "data/spherex", patch_size: int = 128, max_patches: int = 200):
        self.patch_size = patch_size
        self.patches = []
        self.var_patches = []
        self.mask_patches = []

        fits_files = glob.glob(os.path.join(fits_dir, "**", "*.fits"), recursive=True)
        # Filter Level-2 files
        l2_files = [f for f in fits_files if "level2" in f.lower() or "deep" in f.lower()]

        for fp in l2_files:
            try:
                with fits.open(fp) as hdul:
                    if "IMAGE" in hdul:
                        img = hdul["IMAGE"].data.astype(np.float32)
                        var = hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul else np.ones_like(img)
                        flags = hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in hdul else np.zeros_like(img, dtype=np.int32)

                        # Extract clean patches (center region, avoid edges)
                        H, W = img.shape
                        for _ in range(5):
                            if len(self.patches) >= max_patches:
                                break
                            y = np.random.randint(100, H - patch_size - 100)
                            x = np.random.randint(100, W - patch_size - 100)

                            sub_img = img[y:y+patch_size, x:x+patch_size]
                            sub_var = var[y:y+patch_size, x:x+patch_size]
                            sub_flags = flags[y:y+patch_size, x:x+patch_size]

                            # Replace NaNs
                            sub_img = np.nan_to_num(sub_img, nan=0.0)
                            sub_var = np.nan_to_num(sub_var, nan=1.0)
                            sub_var = np.maximum(sub_var, 1e-4)
                            mask = (sub_flags == 0).astype(np.float32)

                            self.patches.append(sub_img)
                            self.var_patches.append(sub_var)
                            self.mask_patches.append(mask)
            except Exception as e:
                pass

    def __len__(self):
        return len(self.patches)

    def __getitem__(self, idx):
        img = torch.from_numpy(self.patches[idx]).unsqueeze(0)
        var = torch.from_numpy(self.var_patches[idx]).unsqueeze(0)
        mask = torch.from_numpy(self.mask_patches[idx]).unsqueeze(0)
        return img, var, mask


def train_astrovision(epochs: int = 5, batch_size: int = 8, lr: float = 1e-3):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training ASTROVISION on device: {device}")

    dataset = SPHERExCutoutDataset()
    if len(dataset) == 0:
        print("No patches extracted yet. Ensure Level-2 FITS files are downloaded.")
        return

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)
    model = AstroVisionAutoencoder().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        for img, var, mask in loader:
            img, var, mask = img.to(device), var.to(device), mask.to(device)
            optimizer.zero_grad()
            recon = model(img)
            # Inverse variance weighted masked loss
            loss = torch.mean(((recon - img) ** 2 / var) * mask)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        avg_loss = total_loss / max(1, len(loader))
        print(f"Epoch {epoch}/{epochs} - Reconstruction Loss: {avg_loss:.4f}")

    os.makedirs("checkpoints", exist_ok=True)
    torch.save(model.state_dict(), "checkpoints/astrovision_latest.pt")
    print("Saved checkpoint: checkpoints/astrovision_latest.pt")


if __name__ == "__main__":
    train_astrovision()
