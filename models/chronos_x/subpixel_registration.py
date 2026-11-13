"""
SPECTRA-X / F1 — Phase 4, Task 4.20D
Sub-Pixel Phase-Correlation Registration & Astrometric Jitter Remediation

Module: models.chronos_x.subpixel_registration
Package: CHRONOS-X

Scientific Context:
Task 4.20A identified that intra-visit SPHEREx dither observations suffer from
sub-pixel pointing jitter (Delta theta ~ 0.2 - 0.5 pixels) between frames.
When subtracting unaligned dither frames, pointing jitter produces high-significance
positive/negative dipole residuals that masquerade as false transient discoveries.

This module implements a production-grade 2D Fourier phase-correlation registration
engine that estimates sub-pixel translations (down to ~0.02 pixels) and aligns target
frames prior to differencing, suppressing false dipole alerts while preserving true
astrophysical transients.

Scientific Safeguards (Section 5 Governance):
1. Sub-pixel dither alignment is NOT genuine multi-epoch temporal validation.
2. Intra-visit dithers (cadence 2-6 min) must never be represented as secular variability.
3. QR2 vs QR3 release differences must not be interpreted as genuine temporal anomalies.
4. Preserves fail-closed behavior on low-signal, ambiguous, or out-of-bounds shifts.
5. Consistently propagates variance under unitary Fourier translation.
"""

import math
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, Tuple
import numpy as np


@dataclass(frozen=True)
class RegistrationResult:
    """Standardized result of sub-pixel phase-correlation registration."""
    shift_y_pixels: float
    shift_x_pixels: float
    peak_correlation: float
    psr: float                           # Peak-to-Sidelobe Ratio
    status: str                          # SUCCESS, LOW_SIGNAL, AMBIGUOUS_PEAK, SHIFT_EXCEEDS_MAX_LIMIT, INVALID_INPUT
    failure_reason: Optional[str]
    aligned_image: np.ndarray            # Registered target image
    aligned_variance: Optional[np.ndarray]  # Propagated variance map
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "shift_y_pixels": self.shift_y_pixels,
            "shift_x_pixels": self.shift_x_pixels,
            "peak_correlation": self.peak_correlation,
            "psr": self.psr,
            "status": self.status,
            "failure_reason": self.failure_reason,
            "provenance": self.provenance
        }
        return d


class SubPixelPhaseCorrelationAligner:
    """
    Sub-pixel image registration engine using Fourier phase correlation
    with 2D windowing, centroid sub-pixel estimation, and variance propagation.
    """

    def __init__(
        self,
        max_shift_pixels: float = 8.0,
        min_psr: float = 3.0,
        min_peak_corr: float = 0.05,
        window_type: str = "hann"
    ):
        self.max_shift_pixels = float(max_shift_pixels)
        self.min_psr = float(min_psr)
        self.min_peak_corr = float(min_peak_corr)
        self.window_type = window_type.lower()

    def _generate_window(self, shape: Tuple[int, int]) -> np.ndarray:
        """Generates a separable 2D apodization window to suppress periodic boundary artifacts."""
        M, N = shape
        if self.window_type == "hann":
            wy = np.hanning(M) if M > 1 else np.ones(M)
            wx = np.hanning(N) if N > 1 else np.ones(N)
        elif self.window_type == "hamming":
            wy = np.hamming(M) if M > 1 else np.ones(M)
            wx = np.hamming(N) if N > 1 else np.ones(N)
        else:
            wy = np.ones(M)
            wx = np.ones(N)
        return np.outer(wy, wx)

    @staticmethod
    def apply_subpixel_shift(image: np.ndarray, shift_y: float, shift_x: float) -> np.ndarray:
        """
        Shifts a 2D image by sub-pixel translation (shift_y, shift_x)
        using the Fourier Phase Shift Theorem:
            F{f(y - dy, x - dx)} = F(u, v) * exp(-i 2pi (u dy + v dx))
        Preserves total flux and sharpness without spatial interpolation blur.
        """
        if abs(shift_y) < 1e-6 and abs(shift_x) < 1e-6:
            return image.copy()

        M, N = image.shape
        u = np.fft.fftfreq(M)
        v = np.fft.fftfreq(N)
        U, V = np.meshgrid(u, v, indexing="ij")

        phase_shift = np.exp(-2j * np.pi * (U * shift_y + V * shift_x))
        F = np.fft.fft2(image)
        shifted = np.real(np.fft.ifft2(F * phase_shift))
        return shifted

    def align(
        self,
        ref_image: np.ndarray,
        target_image: np.ndarray,
        target_variance: Optional[np.ndarray] = None
    ) -> RegistrationResult:
        """
        Measures sub-pixel translation between ref_image and target_image,
        and shifts target_image (and target_variance) to align with ref_image.
        """
        # 1. Input sanity check
        if ref_image is None or target_image is None:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=0.0,
                psr=0.0,
                status="INVALID_INPUT",
                failure_reason="Input image is None",
                aligned_image=target_image if target_image is not None else np.zeros((1, 1)),
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        if ref_image.shape != target_image.shape:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=0.0,
                psr=0.0,
                status="INVALID_INPUT",
                failure_reason=f"Shape mismatch: ref={ref_image.shape} vs target={target_image.shape}",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        M, N = ref_image.shape
        if M < 4 or N < 4:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=0.0,
                psr=0.0,
                status="INVALID_INPUT",
                failure_reason=f"Image dimensions too small ({M}x{N}) for phase correlation",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        # Handle NaNs
        clean_ref = np.nan_to_num(ref_image, nan=0.0)
        clean_target = np.nan_to_num(target_image, nan=0.0)

        # Check for zero or uniform signal
        std_ref = float(np.std(clean_ref))
        std_target = float(np.std(clean_target))
        if std_ref < 1e-12 or std_target < 1e-12:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=0.0,
                psr=0.0,
                status="LOW_SIGNAL",
                failure_reason="Zero or near-zero variance in input frames (uniform background)",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        # 2. Windowing and cross-power spectrum
        W = self._generate_window((M, N))
        i1 = (clean_ref - np.mean(clean_ref)) * W
        i2 = (clean_target - np.mean(clean_target)) * W

        F1 = np.fft.fft2(i1)
        F2 = np.fft.fft2(i2)

        cross = F2 * np.conj(F1)
        norm = np.abs(cross) + 1e-12
        R = cross / norm

        # Phase correlation map
        r = np.real(np.fft.ifft2(R))
        r_shift = np.fft.fftshift(r)

        cy, cx = M // 2, N // 2
        py, px = np.unravel_index(np.argmax(r_shift), r_shift.shape)
        peak_val = float(r_shift[py, px])

        # 3. Peak-to-Sidelobe Ratio (PSR)
        sidelobe_mask = np.ones_like(r_shift, dtype=bool)
        sidelobe_mask[max(0, py - 2):min(M, py + 3), max(0, px - 2):min(N, px + 3)] = False
        sidelobes = r_shift[sidelobe_mask]
        std_side = float(np.std(sidelobes)) if sidelobes.size > 0 else 1.0
        mean_side = float(np.mean(sidelobes)) if sidelobes.size > 0 else 0.0
        psr = float((peak_val - mean_side) / (std_side + 1e-12))

        # 4. Signal & Peak Validation Gating
        if peak_val < self.min_peak_corr:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=peak_val,
                psr=psr,
                status="LOW_SIGNAL",
                failure_reason=f"Peak correlation ({peak_val:.4f}) below minimum threshold ({self.min_peak_corr})",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        if psr < self.min_psr:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=peak_val,
                psr=psr,
                status="AMBIGUOUS_PEAK",
                failure_reason=f"Peak-to-sidelobe ratio ({psr:.2f}) below confidence threshold ({self.min_psr})",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        # 5. Centroid Sub-Pixel Interpolation in 3x3 Window
        win_y = slice(max(0, py - 1), min(M, py + 2))
        win_x = slice(max(0, px - 1), min(N, px + 2))
        patch = np.maximum(r_shift[win_y, win_x], 0.0)
        psum = float(np.sum(patch))

        if psum > 0:
            gy, gx = np.mgrid[win_y, win_x]
            cent_y = float(np.sum(gy * patch) / psum)
            cent_x = float(np.sum(gx * patch) / psum)
            raw_dy = cent_y - cy
            raw_dx = cent_x - cx
        else:
            raw_dy = float(py - cy)
            raw_dx = float(px - cx)

        # 6. Maximum Shift Gating
        if abs(raw_dy) > self.max_shift_pixels or abs(raw_dx) > self.max_shift_pixels:
            return RegistrationResult(
                shift_y_pixels=0.0,
                shift_x_pixels=0.0,
                peak_correlation=peak_val,
                psr=psr,
                status="SHIFT_EXCEEDS_MAX_LIMIT",
                failure_reason=f"Estimated shift ({raw_dy:.2f}, {raw_dx:.2f}) exceeds max allowed ({self.max_shift_pixels} px)",
                aligned_image=target_image,
                aligned_variance=target_variance,
                provenance={"method": "PHASE_CORRELATION_SUBPIXEL"}
            )

        # 7. Apply Shift to Target Image: target is shifted by -raw_dy, -raw_dx to align with ref
        aligned_img = self.apply_subpixel_shift(target_image, -raw_dy, -raw_dx)

        # 8. Variance Propagation under Unitary Shift
        if target_variance is not None:
            aligned_var = np.maximum(
                self.apply_subpixel_shift(np.nan_to_num(target_variance, nan=0.0), -raw_dy, -raw_dx),
                0.0
            )
        else:
            aligned_var = None

        return RegistrationResult(
            shift_y_pixels=float(raw_dy),
            shift_x_pixels=float(raw_dx),
            peak_correlation=peak_val,
            psr=psr,
            status="SUCCESS",
            failure_reason=None,
            aligned_image=aligned_img,
            aligned_variance=aligned_var,
            provenance={
                "method": "PHASE_CORRELATION_SUBPIXEL",
                "window": self.window_type,
                "max_shift_pixels": self.max_shift_pixels,
                "peak_correlation": peak_val,
                "psr": psr
            }
        )


__all__ = [
    "RegistrationResult",
    "SubPixelPhaseCorrelationAligner"
]

