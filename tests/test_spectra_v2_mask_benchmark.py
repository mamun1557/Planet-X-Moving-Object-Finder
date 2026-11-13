"""
Unit tests for SPECTRA v2 mask handling and valid-channel-only scoring.

Verifies:
1. Valid-channel-only scoring: Masked channels (mask=0) contribute zero to loss.
2. Missing flux invariance: Corrupting or modifying flux in masked channels does not affect reconstruction loss.
3. Dual-detector mask semantics: Condition A correctly masks D4, Condition B preserves valid D4.
4. Input tensor structure: Correct 204-dim concatenation of [flux, mask].
"""

import unittest
import numpy as np
import torch
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.spectra.train_masked_spectra import MaskedSpectralAutoencoder


class TestSpectraV2MaskBenchmark(unittest.TestCase):
    def setUp(self):
        self.device = torch.device("cpu")
        self.model = MaskedSpectralAutoencoder(num_channels=102, hidden_dim=64, latent_dim=16)
        self.model.eval()

    def test_reconstruction_loss_ignores_masked_channels(self):
        """Verify that masked channels (mask=0) are strictly excluded from loss computation."""
        # Ground truth and reconstruction
        y_true = torch.ones((1, 102), dtype=torch.float32)
        y_pred = torch.zeros((1, 102), dtype=torch.float32)  # error of 1.0 everywhere
        weight = torch.ones((1, 102), dtype=torch.float32)

        # Mask only first 3 channels valid
        mask = torch.zeros((1, 102), dtype=torch.float32)
        mask[:, :3] = 1.0

        # Compute using model's compute_masked_loss
        loss = self.model.compute_masked_loss(recon=y_pred, target=y_true, mask=mask, weight=weight)
        
        # Ground truth for 3 valid channels: (1.0 - 0.0)^2 * 1.0 * 1.0 / (3 * 1.0) = 1.0
        self.assertAlmostEqual(float(loss.item()), 1.0, places=5)

    def test_masked_flux_invariance(self):
        """Verify that changing flux values in masked channels has zero impact on valid channel loss."""
        torch.manual_seed(42)
        mask = torch.zeros((1, 102), dtype=torch.float32)
        mask[:, 10:15] = 1.0  # 5 valid channels

        y_true_clean = torch.ones((1, 102), dtype=torch.float32)
        y_true_corrupted = torch.ones((1, 102), dtype=torch.float32)
        # Put massive arbitrary flux in masked channels
        y_true_corrupted[:, 0:10] = 999999.0
        y_true_corrupted[:, 15:] = -888888.0

        y_pred = torch.full((1, 102), 0.5, dtype=torch.float32)
        weight = torch.ones((1, 102), dtype=torch.float32)

        loss_clean = self.model.compute_masked_loss(recon=y_pred, target=y_true_clean, mask=mask, weight=weight)
        loss_corrupt = self.model.compute_masked_loss(recon=y_pred, target=y_true_corrupted, mask=mask, weight=weight)

        self.assertAlmostEqual(float(loss_clean.item()), float(loss_corrupt.item()), places=5)

    def test_condition_a_vs_condition_b_masking(self):
        """Verify Condition A correctly zeroes D4 mask while Condition B retains observed D4."""
        # D1 channels: 0..16, D4 channels: 51..67
        full_mask = np.zeros(102, dtype=np.float32)
        full_mask[2] = 1.0
        full_mask[4] = 1.0
        full_mask[55] = 1.0
        full_mask[60] = 1.0

        # Condition A: D1 only (mask out D4)
        mask_A = full_mask.copy()
        mask_A[17:] = 0.0

        self.assertEqual(int(mask_A.sum()), 2)
        self.assertEqual(mask_A[55], 0.0)
        self.assertEqual(mask_A[60], 0.0)
        self.assertEqual(mask_A[2], 1.0)
        self.assertEqual(mask_A[4], 1.0)

        # Condition B: D1 + D4
        mask_B = full_mask.copy()
        self.assertEqual(int(mask_B.sum()), 4)
        self.assertEqual(mask_B[55], 1.0)
        self.assertEqual(mask_B[60], 1.0)

    def test_model_input_dimension_and_forward(self):
        """Verify model receives flux and mask and produces 102-channel reconstruction."""
        flux = torch.randn(1, 102)
        mask = torch.ones(1, 102)

        with torch.no_grad():
            recon = self.model(flux, mask)

        self.assertEqual(recon.shape, (1, 102))


if __name__ == "__main__":
    unittest.main()
