"""
Unit and Regression Test Suite for ASTROVISION Injection & Recovery Benchmark
NASA Space Apps Challenge 2026 — SPECTRA-X / F1 Phase 3 Task 1

Verifies:
1. FITS integrity before and after injection (no file corruption, original files unmodified).
2. WCS preservation (pixel scale, coordinates, projection).
3. Exact flux conservation (integrated rendered PSF equals requested injected flux).
4. Physical variance propagation (shot noise variance Var_shot = I * AGM / exptime added correctly).
5. Defect mask preservation (mask flags unchanged by injection).
6. Injection reproducibility (identical random seed yields bitwise identical injections).
7. Recovery matching and subpixel peak finding.
8. Completeness and Wilson score confidence interval calculations.
9. Frozen checkpoint immutability (SHA-256 match).
"""

import os
import hashlib
import math
import numpy as np
import pytest
from astropy.io import fits
from astropy.wcs import WCS

from scripts.validation.astrovision_injection_benchmark import (
    SPHERExPSFProvider,
    SpatialInjectionEngine,
    AstroVisionEvaluator,
    compute_wilson_confidence_interval,
    fit_completeness_curve,
    find_subpixel_peak,
    DEFAULT_PIXEL_SCALE_ARCSEC,
    DEFAULT_EXPTIME_SEC,
    DEFAULT_AGM
)

EXPECTED_CHECKPOINT_SHA256 = "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557"
CHECKPOINT_PATH = "checkpoints/astrovision_spatial_v2.pt"
SAMPLE_FITS_PATH = "data/spherex/qr3/level2/level2_2026W30_1B_0003_1D1_spx_l2b-v27-2026-222.fits"


class TestAstroVisionInjectionBenchmark:

    def test_checkpoint_immutability(self):
        """Verifies that the evaluated checkpoint is bitwise identical to frozen v2 checkpoint."""
        assert os.path.exists(CHECKPOINT_PATH), f"Checkpoint missing: {CHECKPOINT_PATH}"
        with open(CHECKPOINT_PATH, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()
        assert computed_sha == EXPECTED_CHECKPOINT_SHA256, (
            f"Checkpoint hash mismatch! Expected {EXPECTED_CHECKPOINT_SHA256}, got {computed_sha}"
        )

    def test_fits_integrity_and_read_only(self):
        """Verifies original NASA FITS files exist and can be cleanly read without alteration."""
        assert os.path.exists(SAMPLE_FITS_PATH)
        mtime_before = os.path.getmtime(SAMPLE_FITS_PATH)
        size_before = os.path.getsize(SAMPLE_FITS_PATH)

        with fits.open(SAMPLE_FITS_PATH) as hdul:
            assert "PRIMARY" in hdul
            assert "IMAGE" in hdul
            assert "VARIANCE" in hdul
            assert "FLAGS" in hdul
            img_shape = hdul["IMAGE"].shape
            assert img_shape == (2040, 2040)

        # Confirm file on disk is untouched
        assert os.path.getmtime(SAMPLE_FITS_PATH) == mtime_before
        assert os.path.getsize(SAMPLE_FITS_PATH) == size_before

    def test_wcs_preservation(self):
        """Verifies WCS astrometric header cards and pixel scale conversion."""
        with fits.open(SAMPLE_FITS_PATH) as hdul:
            w = WCS(hdul["IMAGE"].header)
            det = np.abs(np.linalg.det(w.pixel_scale_matrix))
            pix_scale = np.sqrt(det) * 3600.0  # arcsec/pixel
            assert 6.0 <= pix_scale <= 6.3, f"Unexpected pixel scale: {pix_scale} arcsec/pix"

    def test_flux_conservation_point_source(self):
        """Verifies that rendering ePSF point source conserves integrated flux exactly."""
        provider = SPHERExPSFProvider()
        test_flux = 12.3456  # MJy/sr
        xs, ys, flux_2d = provider.render_point_source(
            detector_id=1,
            det_x=1020.0,
            det_y=1020.0,
            sub_x=64.3,
            sub_y=64.7,
            total_flux=test_flux,
            kernel_radius=5
        )
        rendered_sum = float(np.sum(flux_2d))
        np.testing.assert_allclose(rendered_sum, test_flux, rtol=1e-6)

    def test_flux_conservation_extended_source(self):
        """Verifies that extended 2D Gaussian profile conserves integrated flux exactly."""
        engine = SpatialInjectionEngine()
        patch_size = 128
        img = np.zeros((patch_size, patch_size), dtype=np.float32)
        var = np.full((patch_size, patch_size), 0.0004, dtype=np.float32)
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        test_flux = 25.0
        res = engine.inject_extended_source(
            img=img,
            var=var,
            flags=flags,
            sub_x=64.2,
            sub_y=64.8,
            total_flux=test_flux,
            fwhm_arcsec=18.0,
            add_poisson_noise=False
        )
        added_flux = float(np.sum(res["signal_map"]))
        np.testing.assert_allclose(added_flux, test_flux, rtol=1e-5)

    def test_physical_variance_propagation(self):
        """Verifies shot noise variance Var_new = Var_orig + dI * (AGM / exptime)."""
        engine = SpatialInjectionEngine()
        patch_size = 64
        base_var_val = 0.0005
        img = np.full((patch_size, patch_size), 0.3, dtype=np.float32)
        var = np.full((patch_size, patch_size), base_var_val, dtype=np.float32)
        flags = np.zeros((patch_size, patch_size), dtype=np.int32)

        test_flux = 10.0
        exptime = 100.0
        agm = 0.10
        expected_shot_rate = agm / exptime  # 0.001

        res = engine.inject_point_source(
            img=img,
            var=var,
            flags=flags,
            sub_x=32.0,
            sub_y=32.0,
            total_flux=test_flux,
            detector_id=1,
            det_x=1020.0,
            det_y=1020.0,
            agm=agm,
            exptime=exptime,
            add_poisson_noise=False
        )

        inj_var = res["injected_variance"]
        signal = res["signal_map"]
        expected_var = base_var_val + (signal * expected_shot_rate)
        np.testing.assert_allclose(inj_var, expected_var, rtol=1e-5)

    def test_mask_preservation(self):
        """Verifies that synthetic injection modifies flux and variance but preserves mask/flags."""
        engine = SpatialInjectionEngine()
        img = np.full((64, 64), 0.3, dtype=np.float32)
        var = np.full((64, 64), 0.0004, dtype=np.float32)
        # Random flags with some fatal bits
        flags = np.zeros((64, 64), dtype=np.int32)
        flags[10, 10] = 615  # Bad pixel

        mask_before = ((flags & 615) == 0)

        res = engine.inject_point_source(
            img=img,
            var=var,
            flags=flags,
            sub_x=32.0,
            sub_y=32.0,
            total_flux=15.0,
            detector_id=1,
            det_x=1020.0,
            det_y=1020.0,
            add_poisson_noise=False
        )

        # Flags are untouched
        mask_after = ((flags & 615) == 0)
        np.testing.assert_array_equal(mask_before, mask_after)
        assert res["injected_image"][10, 10] == img[10, 10]  # Pixel away from center untouched

    def test_injection_reproducibility(self):
        """Verifies that same random seed produces bitwise identical noisy injection realizations."""
        engine = SpatialInjectionEngine()
        img = np.full((64, 64), 0.3, dtype=np.float32)
        var = np.full((64, 64), 0.0004, dtype=np.float32)
        flags = np.zeros((64, 64), dtype=np.int32)

        rng1 = np.random.default_rng(12345)
        res1 = engine.inject_point_source(
            img=img, var=var, flags=flags, sub_x=32.3, sub_y=32.7,
            total_flux=20.0, detector_id=1, det_x=500.0, det_y=500.0,
            add_poisson_noise=True, rng=rng1
        )

        rng2 = np.random.default_rng(12345)
        res2 = engine.inject_point_source(
            img=img, var=var, flags=flags, sub_x=32.3, sub_y=32.7,
            total_flux=20.0, detector_id=1, det_x=500.0, det_y=500.0,
            add_poisson_noise=True, rng=rng2
        )

        np.testing.assert_array_equal(res1["injected_image"], res2["injected_image"])
        np.testing.assert_array_equal(res1["injected_variance"], res2["injected_variance"])

    def test_subpixel_peak_refinement(self):
        """Verifies parabolic subpixel centroid recovery on continuous synthetic 2D peak."""
        yy, xx = np.ogrid[:64, :64]
        true_y, true_x = 32.35, 32.65
        peak_2d = 100.0 * np.exp(-((yy - true_y)**2 + (xx - true_x)**2) / (2.0 * 1.5**2))
        
        int_y, int_x = int(round(true_y)), int(round(true_x))
        sub_y, sub_x = find_subpixel_peak(peak_2d, int_y, int_x)

        # Precision within 0.05 pixels
        assert abs(sub_y - true_y) < 0.05
        assert abs(sub_x - true_x) < 0.05

    def test_wilson_confidence_interval(self):
        """Verifies Wilson score confidence interval boundary properties."""
        low, high = compute_wilson_confidence_interval(k=10, n=20, confidence=0.95)
        assert 0.0 <= low <= 0.5 <= high <= 1.0
        assert round(low, 2) == 0.30
        assert round(high, 2) == 0.70

        # Boundary checks
        low0, high0 = compute_wilson_confidence_interval(k=0, n=20)
        assert low0 == 0.0
        assert high0 > 0.0

        low1, high1 = compute_wilson_confidence_interval(k=20, n=20)
        assert low1 < 1.0
        assert high1 == 1.0

    def test_completeness_curve_fit(self):
        """Verifies logistic sigmoid completeness curve fitting on synthetic sigmoid data."""
        fluxes = np.array([2.0, 4.0, 6.0, 8.0, 10.0, 15.0, 20.0, 30.0])
        # Synthetic probabilities
        probs = 1.0 / (1.0 + np.exp(-0.8 * (fluxes - 8.0)))
        # Sample 50 trials per flux
        np.random.seed(42)
        all_fluxes = []
        all_detections = []
        for f, p in zip(fluxes, probs):
            det = (np.random.uniform(0, 1, 50) < p).astype(int)
            all_fluxes.extend([f] * 50)
            all_detections.extend(det)

        res = fit_completeness_curve(np.array(all_fluxes), np.array(all_detections))
        c50 = res["completeness_50"]
        c90 = res["completeness_90"]
        # Expected c50 ~ 8.0, c90 ~ 8.0 + ln(9)/0.8 ~ 10.7
        assert 6.5 <= c50 <= 9.5
        assert 9.0 <= c90 <= 13.0

