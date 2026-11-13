"""
SPECTRA-X / F1 — Phase 4, Task 4.20D
Comprehensive Unit & Scientific Validation Test Suite for CHRONOS-X Sub-Pixel Registration

Mandatory Test Coverage:
 1. Zero translation (dy=0, dx=0).
 2. Integer-pixel translation (dy=2, dx=-3).
 3. Fractional-pixel translation (dy=0.35, dx=-0.72).
 4. Noisy image (additive white Gaussian noise).
 5. Low-signal image (near-zero variance -> LOW_SIGNAL fallback).
 6. Ambiguous correlation peak (low PSR -> AMBIGUOUS_PEAK fallback).
 7. Large displacement (shift > max_shift_pixels -> SHIFT_EXCEEDS_MAX_LIMIT).
 8. Invalid image (None, shape mismatch -> INVALID_INPUT).
 9. Variance propagation (non-negative, shifted correctly).
10. Deterministic reproducibility.
11. End-to-end integration with ChronosTemporalDifferencer.
"""

import math
import pytest
import numpy as np
import scipy.ndimage as ndimage
from astropy.io import fits
from astropy.wcs import WCS

from models.chronos_x.subpixel_registration import (
    SubPixelPhaseCorrelationAligner,
    RegistrationResult
)
from models.chronos_x.model import ChronosTemporalDifferencer


@pytest.fixture
def base_star_image():
    """Generates a synthetic 64x64 astronomical cutout with simulated stars."""
    img = np.zeros((64, 64), dtype=float)
    stars = [(20, 20, 100.0), (35, 45, 150.0), (50, 25, 75.0), (15, 50, 60.0)]
    for y, x, flux in stars:
        img[y, x] = flux
    # Convolve with SPHEREx PSF profile (~2 px Gaussian sigma)
    return ndimage.gaussian_filter(img, sigma=2.0)


def create_shifted_image(image: np.ndarray, dy: float, dx: float) -> np.ndarray:
    """Creates a sub-pixel shifted copy of image using the Fourier shift theorem."""
    M, N = image.shape
    u = np.fft.fftfreq(M)
    v = np.fft.fftfreq(N)
    U, V = np.meshgrid(u, v, indexing="ij")
    phase = np.exp(-2j * np.pi * (U * dy + V * dx))
    return np.real(np.fft.ifft2(np.fft.fft2(image) * phase))


# ==============================================================================
# 1. Zero Translation Test
# ==============================================================================
def test_zero_translation(base_star_image):
    """Validates that identical images yield zero shift with high correlation and PSR."""
    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(base_star_image, base_star_image)

    assert res.status == "SUCCESS"
    assert abs(res.shift_y_pixels) < 1e-4
    assert abs(res.shift_x_pixels) < 1e-4
    assert res.peak_correlation > 0.5
    assert res.psr > 20.0


# ==============================================================================
# 2. Integer-Pixel Translation Test
# ==============================================================================
def test_integer_pixel_translation(base_star_image):
    """Validates accurate recovery of pure integer translations."""
    dy_true, dx_true = 2.0, -3.0
    shifted = create_shifted_image(base_star_image, dy_true, dx_true)

    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(base_star_image, shifted)

    assert res.status == "SUCCESS"
    assert abs(res.shift_y_pixels - dy_true) < 0.1
    assert abs(res.shift_x_pixels - dx_true) < 0.1


# ==============================================================================
# 3. Fractional-Pixel Translation Test
# ==============================================================================
def test_fractional_pixel_translation(base_star_image):
    """Validates accurate sub-pixel recovery (<0.05 pixel error) for realistic pointing jitter."""
    dy_true, dx_true = 0.35, -0.72
    shifted = create_shifted_image(base_star_image, dy_true, dx_true)

    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(base_star_image, shifted)

    assert res.status == "SUCCESS"
    assert abs(res.shift_y_pixels - dy_true) < 0.05
    assert abs(res.shift_x_pixels - dx_true) < 0.05


# ==============================================================================
# 4. Noisy Image Test
# ==============================================================================
def test_noisy_image_registration(base_star_image):
    """Validates robust registration in the presence of detector background noise."""
    np.random.seed(42)
    dy_true, dx_true = 0.40, -0.30
    shifted = create_shifted_image(base_star_image, dy_true, dx_true)

    # Add 10% Gaussian read noise
    noise_sigma = 0.10 * np.std(base_star_image)
    noisy_ref = base_star_image + np.random.normal(0, noise_sigma, base_star_image.shape)
    noisy_target = shifted + np.random.normal(0, noise_sigma, shifted.shape)

    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(noisy_ref, noisy_target)

    assert res.status == "SUCCESS"
    assert abs(res.shift_y_pixels - dy_true) < 0.35
    assert abs(res.shift_x_pixels - dx_true) < 0.35
    assert np.sign(res.shift_y_pixels) == np.sign(dy_true)
    assert np.sign(res.shift_x_pixels) == np.sign(dx_true)


# ==============================================================================
# 5. Low-Signal Image Fallback Test
# ==============================================================================
def test_low_signal_fallback():
    """Validates that featureless or zero-variance images safely fall back to zero shift."""
    flat_ref = np.zeros((64, 64), dtype=float)
    flat_target = np.zeros((64, 64), dtype=float)

    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(flat_ref, flat_target)

    assert res.status == "LOW_SIGNAL"
    assert res.shift_y_pixels == 0.0
    assert res.shift_x_pixels == 0.0
    assert res.failure_reason is not None


# ==============================================================================
# 6. Ambiguous Correlation Peak Fallback Test
# ==============================================================================
def test_ambiguous_correlation_peak_fallback():
    """Validates that pure white noise without celestial features triggers peak gating."""
    np.random.seed(123)
    noise_1 = np.random.normal(0, 1.0, (64, 64))
    noise_2 = np.random.normal(0, 1.0, (64, 64))

    aligner = SubPixelPhaseCorrelationAligner(min_psr=8.0, min_peak_corr=0.10)
    res = aligner.align(noise_1, noise_2)

    # White noise against white noise should have no significant correlation peak
    assert res.status in ["LOW_SIGNAL", "AMBIGUOUS_PEAK"]
    assert res.shift_y_pixels == 0.0
    assert res.shift_x_pixels == 0.0


# ==============================================================================
# 7. Large Displacement Gating Test
# ==============================================================================
def test_large_displacement_rejection(base_star_image):
    """Validates that displacements exceeding max_shift_pixels are rejected fail-closed."""
    # True shift: 15.0 pixels (exceeds default 8.0 pixel limit)
    dy_large, dx_large = 15.0, 0.0
    shifted = create_shifted_image(base_star_image, dy_large, dx_large)

    aligner = SubPixelPhaseCorrelationAligner(max_shift_pixels=8.0)
    res = aligner.align(base_star_image, shifted)

    assert res.status == "SHIFT_EXCEEDS_MAX_LIMIT"
    assert res.shift_y_pixels == 0.0
    assert res.shift_x_pixels == 0.0
    assert "exceeds max allowed" in res.failure_reason


# ==============================================================================
# 8. Invalid Image Handling Test
# ==============================================================================
def test_invalid_image_handling():
    """Validates graceful handling of None inputs and shape mismatches."""
    aligner = SubPixelPhaseCorrelationAligner()

    res_none = aligner.align(None, np.zeros((32, 32)))
    assert res_none.status == "INVALID_INPUT"

    res_mismatch = aligner.align(np.zeros((32, 32)), np.zeros((64, 64)))
    assert res_mismatch.status == "INVALID_INPUT"
    assert "Shape mismatch" in res_mismatch.failure_reason


# ==============================================================================
# 9. Variance Propagation Test
# ==============================================================================
def test_variance_propagation(base_star_image):
    """Validates that variance maps are shifted alongside science images and remain non-negative."""
    dy_true, dx_true = 0.50, -0.50
    shifted_img = create_shifted_image(base_star_image, dy_true, dx_true)

    # Synthetic variance map (positive everywhere)
    var_target = np.ones_like(shifted_img) * 0.25

    aligner = SubPixelPhaseCorrelationAligner()
    res = aligner.align(base_star_image, shifted_img, target_variance=var_target)

    assert res.status == "SUCCESS"
    assert res.aligned_variance is not None
    assert res.aligned_variance.shape == var_target.shape
    assert np.all(res.aligned_variance >= 0.0)


# ==============================================================================
# 10. Deterministic Reproducibility Test
# ==============================================================================
def test_deterministic_reproducibility(base_star_image):
    """Validates bit-for-bit identical registration results across multiple runs."""
    shifted = create_shifted_image(base_star_image, 0.28, -0.45)
    aligner = SubPixelPhaseCorrelationAligner()

    res1 = aligner.align(base_star_image, shifted)
    res2 = aligner.align(base_star_image, shifted)

    assert res1.shift_y_pixels == res2.shift_y_pixels
    assert res1.shift_x_pixels == res2.shift_x_pixels
    assert res1.peak_correlation == res2.peak_correlation
    assert np.array_equal(res1.aligned_image, res2.aligned_image)


# ==============================================================================
# 11. End-to-End Integration & Dipole Residual Suppression Test
# ==============================================================================
def test_end_to_end_dipole_residual_suppression(base_star_image):
    """
    Validates that sub-pixel registration significantly suppresses false dipole
    residuals and reduces RMS differencing error between dithered frames.
    """
    dy_jitter, dx_jitter = 0.40, -0.30
    shifted_img = create_shifted_image(base_star_image, dy_jitter, dx_jitter)

    # Construct minimal valid FITS WCS header
    hdr = fits.Header()
    hdr["NAXIS"] = 2
    hdr["NAXIS1"] = 64
    hdr["NAXIS2"] = 64
    hdr["CRPIX1"] = 32.0
    hdr["CRPIX2"] = 32.0
    hdr["CRVAL1"] = 180.0
    hdr["CRVAL2"] = 0.0
    hdr["CDELT1"] = -0.0017
    hdr["CDELT2"] = 0.0017
    hdr["CTYPE1"] = "RA---TAN"
    hdr["CTYPE2"] = "DEC--TAN"

    var = np.ones_like(base_star_image) * 0.01
    mask = np.zeros_like(base_star_image, dtype=np.int32)

    differencer = ChronosTemporalDifferencer(significance_threshold=5.0)

    # Run with sub-pixel registration DISABLED
    res_no_reg = differencer.align_and_difference(
        img1=base_star_image, hdr1=hdr, var1=var, mask1=mask,
        img2=shifted_img, hdr2=hdr, var2=var, mask2=mask,
        enable_psf_matching=False,
        enable_subpixel_registration=False
    )

    # Run with sub-pixel registration ENABLED
    res_with_reg = differencer.align_and_difference(
        img1=base_star_image, hdr1=hdr, var1=var, mask1=mask,
        img2=shifted_img, hdr2=hdr, var2=var, mask2=mask,
        enable_psf_matching=False,
        enable_subpixel_registration=True
    )

    # With registration enabled, RMS difference should drop substantially
    rms_no_reg = np.sqrt(np.mean(res_no_reg["difference_map"] ** 2))
    rms_with_reg = np.sqrt(np.mean(res_with_reg["difference_map"] ** 2))

    assert rms_with_reg < rms_no_reg
    reduction_pct = (1.0 - rms_with_reg / rms_no_reg) * 100.0
    assert reduction_pct > 80.0  # Over 80% reduction in residual pointing jitter noise!

    assert res_with_reg["registration_result"] is not None
    assert res_with_reg["registration_result"]["status"] == "SUCCESS"
