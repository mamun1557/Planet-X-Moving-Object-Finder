"""
SPECTRA-X / F1 — Phase 3, Task 1.1B
ASTROVISION Benchmark Engine v2: Physical Injection & Detector Calibration Remediation

Role: Senior Astronomical Image Simulation Engineer, Detector Calibration Specialist & Scientific ML Validation Engineer

Defect Remediations Enforced (per Independent Audit):
1. Verified FITS HDU Discovery & Schema Validation:
   - Validates HDU layout: HDU 0 (PRIMARY), HDU 1 (IMAGE), HDU 2 (FLAGS),
     HDU 3 (VARIANCE), HDU 4 (ZODI), HDU 5 (EPSF), HDU 6 (WCS-WAVE).
   - Safe fallback / robust discovery without blind index assumptions.
2. Detector-Aware Pixel-Level Absolute Gain Matrix (AGM) Calibration:
   - Full 2D pixel-level gain calibration from authoritative products:
     data/spherex/qr3/calibration/abs_gain_matrix_D{1..6}_*.fits.
   - Eliminates universal D1 median gain (0.11683) hardcoding; correctly calibrates
     D5 (~0.3373) and D6 (~0.4580) where 75.7% of trials reside.
3. In-File ePSF Priority & Provenance:
   - Queries in-file HDU 5 ('EPSF') by default to prevent template mismatch
     (such as D3 v1 441-bin vs v2 451-bin discrepancy).
   - Tracks ePSF provenance, nearest grid bin, and exact kernel peak fraction.
4. Physical Source Injection & Realistic Poisson Variance Propagation:
   - Injected flux units explicitly tracked: integrated flux in MJy/sr*pixel and Jansky.
   - Electron conversion: N_e = (I * Omega_pix * 1e6 / AGM) * t_exp.
   - Shot noise variance: Var_shot = I * (AGM / t_exp) [MJy^2/sr^2].
5. Non-Circular ASTROVISION Model Output Recovery:
   - Removes circular `injected_image - original_image` measurement entirely.
   - Injected image is processed through the frozen autoencoder.
   - True predictions are extracted from the model's normalized chi2 anomaly map and
     reconstruction residual: (I_injected - I_reconstructed).
   - Input injection ground truth is strictly isolated from model predictions.
6. Threshold Calibration & Evaluation Separation:
   - Explicit partition tagging: 'CALIBRATION_CONTROL' vs 'EVALUATION_CONTROL'.
   - Prevents in-sample threshold selection bias.
7. Stratified Detector Sampling:
   - Prevents raster-order scan bias and provides detector-stratified sampling across D1–D6.
"""

import os
import glob
import math
import hashlib
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Tuple, Optional, Union
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from astropy.time import Time
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import cKDTree
import torch

from models.astrovision.model import AstroVisionAutoencoder

# Fatal defect flags bitmask per audited SPHEREx quality policy
FATAL_FLAG_MASK = 615

# Physical constants and SPHEREx defaults
DEFAULT_PIXEL_SCALE_ARCSEC = 6.1522
STERADIANS_PER_SQ_DEG = (math.pi / 180.0) ** 2
SQ_DEG_PER_SQ_ARCSEC = 1.0 / (3600.0 ** 2)
NOMINAL_PIXEL_SOLID_ANGLE_SR = (DEFAULT_PIXEL_SCALE_ARCSEC ** 2) * SQ_DEG_PER_SQ_ARCSEC * STERADIANS_PER_SQ_DEG  # ~8.8963e-10 sr

logger = logging.getLogger("AstroVisionBenchmarkV2")


@dataclass
class FITSStructureVerification:
    """Stores verified HDU mapping and metadata from genuine SPHEREx FITS."""
    filename: str
    filepath: str
    is_valid: bool
    hdu_names: List[str]
    detector_id: int
    obs_id: str
    exptime_sec: float
    pixel_scale_arcsec: float
    pixel_solid_angle_sr: float
    has_image: bool
    has_variance: bool
    has_flags: bool
    has_epsf: bool
    epsf_num_bins: int
    error_message: Optional[str] = None


class SPHERExFITSValidatorV2:
    """
    Verifies and extracts authoritative HDU structures from SPHEREx Level-2 files.
    Does not assume blind indices; safely inspects headers and extensions.
    """

    REQUIRED_HDUS = ["IMAGE", "VARIANCE", "FLAGS"]

    @classmethod
    def verify_and_inspect(cls, fits_path: str) -> FITSStructureVerification:
        if not os.path.exists(fits_path):
            return FITSStructureVerification(
                filename=os.path.basename(fits_path),
                filepath=fits_path,
                is_valid=False,
                hdu_names=[],
                detector_id=-1,
                obs_id="UNKNOWN",
                exptime_sec=0.0,
                pixel_scale_arcsec=0.0,
                pixel_solid_angle_sr=0.0,
                has_image=False,
                has_variance=False,
                has_flags=False,
                has_epsf=False,
                epsf_num_bins=0,
                error_message=f"File not found: {fits_path}"
            )

        try:
            with fits.open(fits_path, memmap=True) as hdul:
                hdu_names = [h.name for h in hdul]
                has_img = "IMAGE" in hdul
                has_var = "VARIANCE" in hdul
                has_flg = "FLAGS" in hdul
                has_epsf = "EPSF" in hdul

                missing = [req for req in cls.REQUIRED_HDUS if req not in hdul]
                if missing:
                    return FITSStructureVerification(
                        filename=os.path.basename(fits_path),
                        filepath=fits_path,
                        is_valid=False,
                        hdu_names=hdu_names,
                        detector_id=-1,
                        obs_id="UNKNOWN",
                        exptime_sec=0.0,
                        pixel_scale_arcsec=0.0,
                        pixel_solid_angle_sr=0.0,
                        has_image=has_img,
                        has_variance=has_var,
                        has_flags=has_flg,
                        has_epsf=has_epsf,
                        epsf_num_bins=0,
                        error_message=f"Missing required HDUs: {missing}"
                    )

                h0 = hdul[0].header
                h_img = hdul["IMAGE"].header
                det_id = int(h_img.get("DETECTOR", h0.get("DETECTOR", -1)))
                obs_id = str(h_img.get("OBSID", h0.get("OBS_ID", os.path.basename(fits_path))))

                # Calculate accurate exposure duration from ISO-8601 timestamps if EXPTIME is absent
                exptime = float(h_img.get("EXPTIME", 0.0))
                if exptime <= 0.0:
                    t_beg = h_img.get("DATE-BEG", h0.get("DATE-BEG", None))
                    t_end = h_img.get("DATE-END", h0.get("DATE-END", None))
                    if t_beg and t_end:
                        try:
                            exptime = float((Time(t_end) - Time(t_beg)).sec)
                        except Exception:
                            exptime = 115.117
                    else:
                        exptime = 115.117

                # WCS pixel scale and solid angle
                w = WCS(h_img)
                scales = proj_plane_pixel_scales(w) * 3600.0
                pix_scale = float(np.mean(scales)) if len(scales) > 0 else DEFAULT_PIXEL_SCALE_ARCSEC
                solid_angle = (pix_scale ** 2) * SQ_DEG_PER_SQ_ARCSEC * STERADIANS_PER_SQ_DEG

                epsf_bins = 0
                if has_epsf and hdul["EPSF"].data is not None:
                    epsf_bins = len(hdul["EPSF"].data)

                return FITSStructureVerification(
                    filename=os.path.basename(fits_path),
                    filepath=fits_path,
                    is_valid=True,
                    hdu_names=hdu_names,
                    detector_id=det_id,
                    obs_id=obs_id,
                    exptime_sec=exptime,
                    pixel_scale_arcsec=pix_scale,
                    pixel_solid_angle_sr=solid_angle,
                    has_image=True,
                    has_variance=True,
                    has_flags=True,
                    has_epsf=has_epsf,
                    epsf_num_bins=epsf_bins,
                    error_message=None
                )
        except Exception as e:
            return FITSStructureVerification(
                filename=os.path.basename(fits_path),
                filepath=fits_path,
                is_valid=False,
                hdu_names=[],
                detector_id=-1,
                obs_id="UNKNOWN",
                exptime_sec=0.0,
                pixel_scale_arcsec=0.0,
                pixel_solid_angle_sr=0.0,
                has_image=False,
                has_variance=False,
                has_flags=False,
                has_epsf=False,
                epsf_num_bins=0,
                error_message=f"FITS read error: {str(e)}"
            )


class AbsoluteGainProviderV2:
    """
    Manages authoritative 2D pixel-level and detector-level Absolute Gain Matrix (AGM) calibrations.
    Loads official QR3 calibration files:
    abs_gain_matrix_D{1..6}_spx_cal-agm-v8-2026-191.fits
    Units: MJy * s / (electron * sr)
    """

    def __init__(self, calib_dir: str = "data/spherex/qr3/calibration"):
        self.calib_dir = calib_dir
        self._agm_cache: Dict[int, Dict[str, Any]] = {}

    def get_agm_data(self, detector_id: int) -> Dict[str, Any]:
        """Loads and caches authoritative 2D pixel gain map for a specific detector."""
        if detector_id in self._agm_cache:
            return self._agm_cache[detector_id]

        pat = os.path.join(self.calib_dir, f"abs_gain_matrix_D{detector_id}_*.fits")
        files = sorted(glob.glob(pat))
        if not files:
            raise FileNotFoundError(
                f"Authoritative Absolute Gain Matrix for Detector {detector_id} not found matching {pat}"
            )

        agm_file = files[0]
        with fits.open(agm_file) as hdul:
            img_hdu = hdul["IMAGE"] if "IMAGE" in hdul else hdul[1]
            agm_map = img_hdu.data.astype(np.float32)
            header = img_hdu.header
            bunit = header.get("BUNIT", "MJy s / (electron sr)")

        pos_mask = np.isfinite(agm_map) & (agm_map > 0.0)
        med_val = float(np.nanmedian(agm_map[pos_mask])) if np.any(pos_mask) else 0.1168

        info = {
            "detector_id": detector_id,
            "filepath": agm_file,
            "filename": os.path.basename(agm_file),
            "agm_map": agm_map,
            "bunit": bunit,
            "median_gain": med_val,
            "min_valid_gain": float(np.nanmin(agm_map[pos_mask])) if np.any(pos_mask) else med_val,
            "max_valid_gain": float(np.nanmax(agm_map[pos_mask])) if np.any(pos_mask) else med_val
        }
        self._agm_cache[detector_id] = info
        return info

    def get_pixel_gain(self, detector_id: int, y_pix: int, x_pix: int) -> float:
        """Returns physical AGM gain value at exact detector coordinate (y_pix, x_pix)."""
        info = self.get_agm_data(detector_id)
        agm_map = info["agm_map"]
        H, W = agm_map.shape
        if 0 <= y_pix < H and 0 <= x_pix < W:
            val = float(agm_map[y_pix, x_pix])
            if np.isfinite(val) and val > 0.0:
                return val
        return info["median_gain"]

    def get_patch_gain(self, detector_id: int, y0: int, y1: int, x0: int, x1: int) -> np.ndarray:
        """Extracts 2D patch of AGM gains for spatial injection slice."""
        info = self.get_agm_data(detector_id)
        agm_map = info["agm_map"]
        sub_gain = agm_map[y0:y1, x0:x1].copy()
        bad = (~np.isfinite(sub_gain)) | (sub_gain <= 0.0)
        if np.any(bad):
            sub_gain[bad] = info["median_gain"]
        return sub_gain


class InFilePSFProviderV2:
    """
    Detector-aware ePSF Provider with strict in-file priority.
    Uses the in-file HDU 5 'EPSF' table whenever present in genuine SPHEREx FITS.
    Falls back to external template only when explicitly requested.
    """

    def __init__(self, templates_dir: str = "data/spherex/qr3/templates"):
        self.templates_dir = templates_dir
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_psf_model_for_file(self, fits_path: str, detector_id: int) -> Dict[str, Any]:
        cache_key = f"{fits_path}_D{detector_id}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        provenance = "IN_FILE_HDU_EPSF"
        epsf_table_data = None
        ovsmp_x, ovsmp_y = 5.0, 5.0

        with fits.open(fits_path) as hdul:
            if "EPSF" in hdul and hdul["EPSF"].data is not None:
                epsf_table_data = hdul["EPSF"].data
                ovsmp_x = float(hdul["EPSF"].header.get("OVSMPX", 5.0))
                ovsmp_y = float(hdul["EPSF"].header.get("OVSMPY", 5.0))

        if epsf_table_data is None:
            # Fallback to templates dir matching detector
            provenance = "EXTERNAL_TEMPLATE_FALLBACK"
            pat = os.path.join(self.templates_dir, f"epsf_D{detector_id}_*.fits")
            files = sorted(glob.glob(pat))
            if not files:
                raise FileNotFoundError(f"No ePSF template found for Detector {detector_id} in {self.templates_dir}")
            # Ensure v2 priority for Detector 3
            if detector_id == 3:
                v2_files = [f for f in files if "cal-epsf-v2" in f]
                epsf_path = v2_files[0] if v2_files else files[0]
            else:
                epsf_path = files[0]

            with fits.open(epsf_path) as hdul_tpl:
                epsf_table_data = hdul_tpl[1].data
                ovsmp_x = float(hdul_tpl[1].header.get("OVSMPX", 5.0))
                ovsmp_y = float(hdul_tpl[1].header.get("OVSMPY", 5.0))

        x_centers = np.array(epsf_table_data["XCENTER"], dtype=np.float64)
        y_centers = np.array(epsf_table_data["YCENTER"], dtype=np.float64)
        psf_cubes = np.array(epsf_table_data["EPSF"], dtype=np.float64)

        if psf_cubes.ndim == 2:
            psf_cubes = psf_cubes.reshape((len(x_centers), 33, 33))

        n_sub = psf_cubes.shape[1]
        center_sub = (n_sub - 1.0) / 2.0
        native_coords = (np.arange(n_sub, dtype=np.float64) - center_sub) / ovsmp_x

        info = {
            "provenance": provenance,
            "ovsmp": (ovsmp_x, ovsmp_y),
            "native_coords": native_coords,
            "x_centers": x_centers,
            "y_centers": y_centers,
            "psf_cubes": psf_cubes,
            "tree": cKDTree(np.column_stack([x_centers, y_centers])),
            "num_bins": len(x_centers)
        }
        self._cache[cache_key] = info
        return info

    def render_point_source(
        self,
        fits_path: str,
        detector_id: int,
        det_x: float,
        det_y: float,
        sub_x: float,
        sub_y: float,
        total_flux_mjy_sr_pix: float,
        kernel_radius: int = 5
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
        """
        Renders a subpixel ePSF point source onto the local pixel grid.
        Returns:
            xs: column indices in local cutout
            ys: row indices in local cutout
            flux_2d: 2D array of added flux density [MJy / sr]
            meta: dictionary with exact kernel peak fraction, nearest bin, and provenance
        """
        psf_info = self.get_psf_model_for_file(fits_path, detector_id)
        _, nearest_idx = psf_info["tree"].query([det_x, det_y])
        psf_2d = psf_info["psf_cubes"][nearest_idx]

        coords = psf_info["native_coords"]
        interp = RegularGridInterpolator(
            (coords, coords),
            psf_2d,
            method="linear",
            bounds_error=False,
            fill_value=0.0
        )

        ix_min = int(np.floor(sub_x)) - kernel_radius
        ix_max = int(np.floor(sub_x)) + kernel_radius + 1
        iy_min = int(np.floor(sub_y)) - kernel_radius
        iy_max = int(np.floor(sub_y)) + kernel_radius + 1

        xs = np.arange(ix_min, ix_max)
        ys = np.arange(iy_min, iy_max)
        XX, YY = np.meshgrid(xs, ys)

        dx = XX - sub_x
        dy = YY - sub_y
        pts = np.column_stack([dy.ravel(), dx.ravel()])
        kernel = interp(pts).reshape(XX.shape)

        k_sum = float(kernel.sum())
        if k_sum <= 0.0:
            raise ValueError(f"Interpolated ePSF kernel sum non-positive ({k_sum}) at det ({det_x}, {det_y})")

        # Strictly normalize kernel sum to 1.0 (exact flux conservation)
        kernel_norm = kernel / k_sum
        flux_2d = (kernel_norm * total_flux_mjy_sr_pix).astype(np.float32)

        meta = {
            "epsf_provenance": psf_info["provenance"],
            "epsf_nearest_bin": int(nearest_idx),
            "epsf_total_bins": int(psf_info["num_bins"]),
            "actual_kernel_peak_fraction": float(np.max(kernel_norm)),
            "kernel_radius_pix": kernel_radius
        }
        return xs, ys, flux_2d, meta


@dataclass
class InjectionRecordV2:
    """Versioned injection manifest record with full physical provenance."""
    trial_id: str
    partition: str  # 'CALIBRATION_CONTROL', 'EVALUATION_CONTROL', 'POINT_SOURCE_INJECTION', 'EXTENDED_SOURCE_INJECTION'
    source_type: str
    filename: str
    detector_id: int
    obs_id: str
    det_x0: int
    det_y0: int
    det_cx: float
    det_cy: float
    sub_x_inj: float
    sub_y_inj: float
    exptime_sec: float
    pixel_scale_arcsec: float
    pixel_solid_angle_sr: float
    applied_agm_median: float
    applied_agm_bunit: str
    epsf_provenance: str
    epsf_nearest_bin: int
    actual_kernel_peak_fraction: float
    target_nominal_snr: float
    injected_flux_sum_mjy_sr_pix: float
    injected_flux_jy: float
    injected_peak_flux_mjy_sr: float
    fwhm_arcsec: float
    rejected_boundary_flag: bool
    rejection_reason: Optional[str] = None


class PhysicalSpatialInjectionEngineV2:
    """
    Benchmark Engine v2: Renders physical point-source and extended-source injections
    with pixel-level AGM calibration and Poisson variance propagation.
    """

    def __init__(
        self,
        gain_provider: Optional[AbsoluteGainProviderV2] = None,
        psf_provider: Optional[InFilePSFProviderV2] = None
    ):
        self.gain_provider = gain_provider or AbsoluteGainProviderV2()
        self.psf_provider = psf_provider or InFilePSFProviderV2()

    def inject_point_source(
        self,
        cutout_img: np.ndarray,
        cutout_var: np.ndarray,
        cutout_flags: np.ndarray,
        fits_path: str,
        detector_id: int,
        det_x0: int,
        det_y0: int,
        det_cx: float,
        det_cy: float,
        sub_x: float,
        sub_y: float,
        total_flux_mjy_sr_pix: float,
        exptime: float,
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Dict[str, Any]:
        """Injects physical ePSF point source with detector-specific AGM gain."""
        if rng is None:
            rng = np.random.default_rng()

        H, W = cutout_img.shape
        # Boundary protection check
        if sub_x < 6.0 or sub_x > (W - 7.0) or sub_y < 6.0 or sub_y > (H - 7.0):
            return {
                "rejected": True,
                "rejection_reason": f"Injection center ({sub_x:.1f}, {sub_y:.1f}) within boundary margin"
            }

        xs, ys, s_flux, psf_meta = self.psf_provider.render_point_source(
            fits_path=fits_path,
            detector_id=detector_id,
            det_x=det_cx,
            det_y=det_cy,
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux_mjy_sr_pix=total_flux_mjy_sr_pix,
            kernel_radius=5
        )

        valid_x = (xs >= 0) & (xs < W)
        valid_y = (ys >= 0) & (ys < H)
        sub_xs = xs[valid_x]
        sub_ys = ys[valid_y]
        sub_flux = s_flux[np.ix_(valid_y, valid_x)]

        # Extract localized 2D AGM gain for exact detector coordinate
        patch_agm = self.gain_provider.get_patch_gain(
            detector_id=detector_id,
            y0=det_y0 + int(sub_ys[0]),
            y1=det_y0 + int(sub_ys[-1]) + 1,
            x0=det_x0 + int(sub_xs[0]),
            x1=det_x0 + int(sub_xs[-1]) + 1
        )
        if patch_agm.shape != sub_flux.shape:
            # Fallback to local scalar gain if sub-slice shape differs
            scalar_agm = self.gain_provider.get_pixel_gain(detector_id, int(det_cy), int(det_cx))
            patch_agm = np.full_like(sub_flux, scalar_agm)

        # Variance propagation: Var_shot = I * (AGM / t_exp) [MJy^2 / sr^2]
        shot_rate_conversion = patch_agm / max(1e-3, exptime)
        shot_var = np.maximum(0.0, sub_flux * shot_rate_conversion)

        if add_poisson_noise:
            # Physical electron conversion: N_e = I * (t_exp / AGM)
            inv_rate = exptime / np.maximum(1e-6, patch_agm)
            expected_electrons = np.maximum(0.0, sub_flux * inv_rate)
            observed_electrons = rng.poisson(expected_electrons).astype(np.float64)
            noisy_flux = (observed_electrons * (patch_agm / exptime)).astype(np.float32)
            flux_to_add = noisy_flux
        else:
            flux_to_add = sub_flux

        inj_img = cutout_img.copy()
        inj_var = cutout_var.copy()
        signal_map = np.zeros_like(cutout_img, dtype=np.float32)

        inj_img[np.ix_(sub_ys, sub_xs)] += flux_to_add
        inj_var[np.ix_(sub_ys, sub_xs)] += shot_var.astype(np.float32)
        signal_map[np.ix_(sub_ys, sub_xs)] += sub_flux

        # Flux in Jansky: S [Jy] = S_tot [MJy/sr*pix] * 1e6 * Omega_pix
        flux_jy = total_flux_mjy_sr_pix * 1e6 * pixel_solid_angle_sr

        return {
            "rejected": False,
            "injected_image": inj_img,
            "injected_variance": inj_var,
            "signal_map": signal_map,
            "peak_flux_mjy_sr": float(np.max(sub_flux)),
            "actual_added_flux_sum": float(np.sum(sub_flux)),
            "flux_jy": flux_jy,
            "applied_agm_median": float(np.median(patch_agm)),
            "psf_meta": psf_meta
        }

    def inject_extended_source(
        self,
        cutout_img: np.ndarray,
        cutout_var: np.ndarray,
        cutout_flags: np.ndarray,
        detector_id: int,
        det_x0: int,
        det_y0: int,
        det_cx: float,
        det_cy: float,
        sub_x: float,
        sub_y: float,
        total_flux_mjy_sr_pix: float,
        fwhm_arcsec: float,
        pixel_scale_arcsec: float,
        exptime: float,
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Dict[str, Any]:
        """Injects physical 2D Gaussian extended source with pixel-level AGM gain."""
        if rng is None:
            rng = np.random.default_rng()

        fwhm_pix = fwhm_arcsec / max(1e-3, pixel_scale_arcsec)
        sigma_pix = fwhm_pix / (2.0 * math.sqrt(2.0 * math.log(2.0)))
        kernel_radius = int(math.ceil(4.0 * sigma_pix))

        H, W = cutout_img.shape
        if sub_x < (kernel_radius + 1) or sub_x > (W - kernel_radius - 2) or \
           sub_y < (kernel_radius + 1) or sub_y > (H - kernel_radius - 2):
            return {
                "rejected": True,
                "rejection_reason": f"Extended footprint radius {kernel_radius} exceeds cutout margin"
            }

        ix_min = int(np.floor(sub_x)) - kernel_radius
        ix_max = int(np.floor(sub_x)) + kernel_radius + 1
        iy_min = int(np.floor(sub_y)) - kernel_radius
        iy_max = int(np.floor(sub_y)) + kernel_radius + 1

        xs = np.arange(ix_min, ix_max)
        ys = np.arange(iy_min, iy_max)
        XX, YY = np.meshgrid(xs, ys)

        dx = XX - sub_x
        dy = YY - sub_y
        r_sq = dx**2 + dy**2

        raw_profile = np.exp(-r_sq / (2.0 * sigma_pix**2))
        prof_sum = float(raw_profile.sum())
        if prof_sum <= 0.0:
            raise ValueError("Extended Gaussian profile sum non-positive")

        norm_profile = raw_profile / prof_sum
        s_flux = (norm_profile * total_flux_mjy_sr_pix).astype(np.float32)

        valid_x = (xs >= 0) & (xs < W)
        valid_y = (ys >= 0) & (ys < H)
        sub_xs = xs[valid_x]
        sub_ys = ys[valid_y]
        sub_flux = s_flux[np.ix_(valid_y, valid_x)]

        patch_agm = self.gain_provider.get_patch_gain(
            detector_id=detector_id,
            y0=det_y0 + int(sub_ys[0]),
            y1=det_y0 + int(sub_ys[-1]) + 1,
            x0=det_x0 + int(sub_xs[0]),
            x1=det_x0 + int(sub_xs[-1]) + 1
        )
        if patch_agm.shape != sub_flux.shape:
            scalar_agm = self.gain_provider.get_pixel_gain(detector_id, int(det_cy), int(det_cx))
            patch_agm = np.full_like(sub_flux, scalar_agm)

        shot_rate_conversion = patch_agm / max(1e-3, exptime)
        shot_var = np.maximum(0.0, sub_flux * shot_rate_conversion)

        if add_poisson_noise:
            inv_rate = exptime / np.maximum(1e-6, patch_agm)
            expected_electrons = np.maximum(0.0, sub_flux * inv_rate)
            observed_electrons = rng.poisson(expected_electrons).astype(np.float64)
            noisy_flux = (observed_electrons * (patch_agm / exptime)).astype(np.float32)
            flux_to_add = noisy_flux
        else:
            flux_to_add = sub_flux

        inj_img = cutout_img.copy()
        inj_var = cutout_var.copy()
        signal_map = np.zeros_like(cutout_img, dtype=np.float32)

        inj_img[np.ix_(sub_ys, sub_xs)] += flux_to_add
        inj_var[np.ix_(sub_ys, sub_xs)] += shot_var.astype(np.float32)
        signal_map[np.ix_(sub_ys, sub_xs)] += sub_flux

        flux_jy = total_flux_mjy_sr_pix * 1e6 * pixel_solid_angle_sr

        return {
            "rejected": False,
            "injected_image": inj_img,
            "injected_variance": inj_var,
            "signal_map": signal_map,
            "peak_flux_mjy_sr": float(np.max(sub_flux)),
            "actual_added_flux_sum": float(np.sum(sub_flux)),
            "flux_jy": flux_jy,
            "applied_agm_median": float(np.median(patch_agm)),
            "fwhm_pix": fwhm_pix,
            "fwhm_arcsec": fwhm_arcsec
        }

    def create_matched_point_source_pair(
        self,
        cutout_img: np.ndarray,
        cutout_var: np.ndarray,
        cutout_flags: np.ndarray,
        fits_path: str,
        detector_id: int,
        det_x0: int,
        det_y0: int,
        det_cx: float,
        det_cy: float,
        sub_x: float,
        sub_y: float,
        total_flux_mjy_sr_pix: float,
        exptime: float,
        pair_id: str,
        control_trial_id: str,
        injected_trial_id: str,
        partition: str = "EVALUATION",
        obs_id: str = "UNKNOWN",
        filename: str = "",
        pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC,
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Tuple[Optional["MatchedCutoutPairV2"], Dict[str, Any]]:
        """
        Creates a matched cutout pair for point-source injection.
        Returns (MatchedCutoutPairV2, injection_dict) or (None, rejection_dict).
        """
        inj_res = self.inject_point_source(
            cutout_img=cutout_img,
            cutout_var=cutout_var,
            cutout_flags=cutout_flags,
            fits_path=fits_path,
            detector_id=detector_id,
            det_x0=det_x0,
            det_y0=det_y0,
            det_cx=det_cx,
            det_cy=det_cy,
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux_mjy_sr_pix=total_flux_mjy_sr_pix,
            exptime=exptime,
            pixel_solid_angle_sr=pixel_solid_angle_sr,
            add_poisson_noise=add_poisson_noise,
            rng=rng
        )

        if inj_res.get("rejected", False):
            return None, inj_res

        mask = ((cutout_flags & FATAL_FLAG_MASK) == 0).astype(np.float32)

        pair = MatchedCutoutPairV2(
            pair_id=pair_id,
            control_trial_id=control_trial_id,
            injected_trial_id=injected_trial_id,
            partition=partition,
            filename=filename or os.path.basename(fits_path),
            detector_id=detector_id,
            obs_id=obs_id,
            det_x0=det_x0,
            det_y0=det_y0,
            det_cx=det_cx,
            det_cy=det_cy,
            pixel_scale_arcsec=pixel_scale_arcsec,
            pixel_solid_angle_sr=pixel_solid_angle_sr,
            exptime_sec=exptime,
            applied_agm=inj_res["applied_agm_median"],
            control_image=cutout_img.copy(),
            control_variance=cutout_var.copy(),
            injected_image=inj_res["injected_image"],
            injected_variance=inj_res["injected_variance"],
            mask=mask,
            sub_x_inj=sub_x,
            sub_y_inj=sub_y,
            injected_flux_sum_mjy_sr_pix=total_flux_mjy_sr_pix,
            injected_flux_jy=inj_res["flux_jy"],
            source_type="POINT_SOURCE"
        )
        return pair, inj_res

    def create_matched_extended_source_pair(
        self,
        cutout_img: np.ndarray,
        cutout_var: np.ndarray,
        cutout_flags: np.ndarray,
        detector_id: int,
        det_x0: int,
        det_y0: int,
        det_cx: float,
        det_cy: float,
        sub_x: float,
        sub_y: float,
        total_flux_mjy_sr_pix: float,
        fwhm_arcsec: float,
        exptime: float,
        pair_id: str,
        control_trial_id: str,
        injected_trial_id: str,
        partition: str = "EVALUATION",
        obs_id: str = "UNKNOWN",
        filename: str = "",
        pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC,
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Tuple[Optional["MatchedCutoutPairV2"], Dict[str, Any]]:
        """
        Creates a matched cutout pair for extended-source injection.
        Returns (MatchedCutoutPairV2, injection_dict) or (None, rejection_dict).
        """
        inj_res = self.inject_extended_source(
            cutout_img=cutout_img,
            cutout_var=cutout_var,
            cutout_flags=cutout_flags,
            detector_id=detector_id,
            det_x0=det_x0,
            det_y0=det_y0,
            det_cx=det_cx,
            det_cy=det_cy,
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux_mjy_sr_pix=total_flux_mjy_sr_pix,
            fwhm_arcsec=fwhm_arcsec,
            pixel_scale_arcsec=pixel_scale_arcsec,
            exptime=exptime,
            pixel_solid_angle_sr=pixel_solid_angle_sr,
            add_poisson_noise=add_poisson_noise,
            rng=rng
        )

        if inj_res.get("rejected", False):
            return None, inj_res

        mask = ((cutout_flags & FATAL_FLAG_MASK) == 0).astype(np.float32)

        pair = MatchedCutoutPairV2(
            pair_id=pair_id,
            control_trial_id=control_trial_id,
            injected_trial_id=injected_trial_id,
            partition=partition,
            filename=filename,
            detector_id=detector_id,
            obs_id=obs_id,
            det_x0=det_x0,
            det_y0=det_y0,
            det_cx=det_cx,
            det_cy=det_cy,
            pixel_scale_arcsec=pixel_scale_arcsec,
            pixel_solid_angle_sr=pixel_solid_angle_sr,
            exptime_sec=exptime,
            applied_agm=inj_res["applied_agm_median"],
            control_image=cutout_img.copy(),
            control_variance=cutout_var.copy(),
            injected_image=inj_res["injected_image"],
            injected_variance=inj_res["injected_variance"],
            mask=mask,
            sub_x_inj=sub_x,
            sub_y_inj=sub_y,
            injected_flux_sum_mjy_sr_pix=total_flux_mjy_sr_pix,
            injected_flux_jy=inj_res["flux_jy"],
            source_type="EXTENDED_SOURCE"
        )
        return pair, inj_res

    def create_zero_injection_control_pair(
        self,
        cutout_img: np.ndarray,
        cutout_var: np.ndarray,
        cutout_flags: np.ndarray,
        detector_id: int,
        det_x0: int,
        det_y0: int,
        det_cx: float,
        det_cy: float,
        sub_x: float,
        sub_y: float,
        exptime: float,
        pair_id: str,
        control_trial_id: str,
        partition: str = "CALIBRATION",
        obs_id: str = "UNKNOWN",
        filename: str = "",
        pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC,
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR
    ) -> "MatchedCutoutPairV2":
        """
        Creates a matched zero-injection control pair (I_injected == I_control).
        Used for false positive rate calibration and baseline artifact cancellation.
        """
        mask = ((cutout_flags & FATAL_FLAG_MASK) == 0).astype(np.float32)
        scalar_agm = self.gain_provider.get_pixel_gain(detector_id, int(det_cy), int(det_cx))

        return MatchedCutoutPairV2(
            pair_id=pair_id,
            control_trial_id=control_trial_id,
            injected_trial_id=f"{control_trial_id}_EVAL",
            partition=partition,
            filename=filename,
            detector_id=detector_id,
            obs_id=obs_id,
            det_x0=det_x0,
            det_y0=det_y0,
            det_cx=det_cx,
            det_cy=det_cy,
            pixel_scale_arcsec=pixel_scale_arcsec,
            pixel_solid_angle_sr=pixel_solid_angle_sr,
            exptime_sec=exptime,
            applied_agm=scalar_agm,
            control_image=cutout_img.copy(),
            control_variance=cutout_var.copy(),
            injected_image=cutout_img.copy(),
            injected_variance=cutout_var.copy(),
            mask=mask,
            sub_x_inj=sub_x,
            sub_y_inj=sub_y,
            injected_flux_sum_mjy_sr_pix=0.0,
            injected_flux_jy=0.0,
            source_type="ZERO_INJECTION_CONTROL"
        )


@dataclass
class MatchedCutoutPairV2:
    """
    Matched Control and Injected Cutout Pair for Paired Residual Differencing.
    Both members share the identical background realization, detector metadata, and quality mask.
    The injected member adds the physical synthetic source profile and Poisson shot noise.
    """
    pair_id: str
    control_trial_id: str
    injected_trial_id: str
    partition: str  # 'CALIBRATION' or 'EVALUATION'
    filename: str
    detector_id: int
    obs_id: str
    det_x0: int
    det_y0: int
    det_cx: float
    det_cy: float
    pixel_scale_arcsec: float
    pixel_solid_angle_sr: float
    exptime_sec: float
    applied_agm: float
    control_image: np.ndarray
    control_variance: np.ndarray
    injected_image: np.ndarray
    injected_variance: np.ndarray
    mask: np.ndarray
    sub_x_inj: float
    sub_y_inj: float
    injected_flux_sum_mjy_sr_pix: float
    injected_flux_jy: float
    source_type: str = "POINT_SOURCE"

    def __post_init__(self):
        self.validate()

    def validate(self) -> None:
        """Enforces structural, dimensional, and physical consistency between pair members."""
        if self.control_image.shape != self.injected_image.shape:
            raise ValueError(
                f"Pair {self.pair_id}: Control image shape {self.control_image.shape} does not match injected image shape {self.injected_image.shape}"
            )
        if self.control_variance.shape != self.injected_variance.shape:
            raise ValueError(
                f"Pair {self.pair_id}: Control variance shape {self.control_variance.shape} does not match injected variance shape {self.injected_variance.shape}"
            )
        if self.mask.shape != self.control_image.shape:
            raise ValueError(
                f"Pair {self.pair_id}: Mask shape {self.mask.shape} does not match image shape {self.control_image.shape}"
            )
        if not (1 <= self.detector_id <= 6):
            raise ValueError(f"Pair {self.pair_id}: Invalid detector ID {self.detector_id}; must be between 1 and 6")
        if self.exptime_sec <= 0.0:
            raise ValueError(f"Pair {self.pair_id}: Non-positive exposure time {self.exptime_sec}")
        if self.pixel_scale_arcsec <= 0.0:
            raise ValueError(f"Pair {self.pair_id}: Non-positive pixel scale {self.pixel_scale_arcsec}")
        if self.pixel_solid_angle_sr <= 0.0:
            raise ValueError(f"Pair {self.pair_id}: Non-positive pixel solid angle {self.pixel_solid_angle_sr}")
        if self.applied_agm <= 0.0:
            raise ValueError(f"Pair {self.pair_id}: Non-positive applied AGM {self.applied_agm}")
        H, W = self.control_image.shape
        if not (0.0 <= self.sub_x_inj < W and 0.0 <= self.sub_y_inj < H):
            raise ValueError(
                f"Pair {self.pair_id}: Injection coordinates ({self.sub_x_inj}, {self.sub_y_inj}) outside bounds (0..{W}, 0..{H})"
            )


@dataclass
class ModelOutputRecoveryRecordV2:
    """
    Versioned record for actual ASTROVISION model output evaluation.
    Completely isolates ground truth injection from model predictions.
    Supports Paired Residual Differencing to eliminate baseline reconstruction bias.
    """
    trial_id: str
    partition: str
    target_true_x: float
    target_true_y: float
    injected_flux_sum: float
    # True ASTROVISION Model Output Metrics
    model_target_peak_chi2: float
    model_aperture_sum_chi2: float
    model_global_peak_chi2: float
    model_recovered_sub_x: float
    model_recovered_sub_y: float
    model_position_error_pix: float
    model_position_error_arcsec: float
    # Residual Flux Metrics
    model_residual_flux_mjy_sr: float  # Differential recovered flux (MJy / sr)
    is_detected_at_tau: bool
    tau_applied: float
    # Extended Paired Photometry Metrics (Task 1.1D Remediation)
    pair_id: str = "UNPAIRED"
    raw_injected_residual_flux: float = 0.0
    raw_control_residual_flux: float = 0.0
    differential_residual_flux: float = 0.0
    differential_residual_flux_jy: float = 0.0
    valid_aperture_pixels: int = 0
    masked_aperture_pixels: int = 0
    checkpoint_sha256: str = ""


class AstroVisionEvaluatorV2:
    """
    Non-Circular Evaluator for Frozen ASTROVISION Model.
    Evaluates actual model outputs (reconstruction residual and chi2 anomaly map).
    Implements Paired Residual Differencing (Task 1.1D Remediation) to cancel out
    autoencoder baseline reconstruction artifacts on blank and structured sky.
    """

    def __init__(self, checkpoint_path: str = "checkpoints/astrovision_spatial_v2.pt", device: Optional[str] = None):
        self.checkpoint_path = checkpoint_path
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))

        if torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"ASTROVISION checkpoint not found at {checkpoint_path}")

        # Compute SHA-256 hash for provenance
        with open(checkpoint_path, "rb") as f:
            self.checkpoint_sha256 = hashlib.sha256(f.read()).hexdigest()

        ckpt = torch.load(checkpoint_path, map_location=self.device, weights_only=False)
        self.model = AstroVisionAutoencoder().to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

    def _run_model_inference(
        self,
        image: np.ndarray,
        variance: np.ndarray,
        mask: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Runs model inference on a 2D cutout with variance and mask.
        Returns:
            reconstruction_2d: np.ndarray [H, W]
            anomaly_map_2d: np.ndarray [H, W]
        """
        t_img = torch.from_numpy(image.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)
        t_var = torch.from_numpy(variance.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)
        t_mask = torch.from_numpy(mask.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            reconstruction = self.model(t_img)
            anomaly_map = self.model.compute_anomaly_map(t_img, t_var, t_mask)

        anom_2d = anomaly_map.squeeze().cpu().numpy()
        recon_2d = reconstruction.squeeze().cpu().numpy()
        return recon_2d, anom_2d

    def evaluate_paired_model_output(
        self,
        pair: MatchedCutoutPairV2,
        threshold_tau: float = 169.10,
        match_radius_pix: float = 2.5,
        aperture_radius_pix: float = 3.5
    ) -> ModelOutputRecoveryRecordV2:
        """
        Runs paired model inference and computes Paired Residual Differencing.
        R_injected = max(0, I_inj - Recon(I_inj))
        R_control  = max(0, I_ctrl - Recon(I_ctrl))
        F_differential = sum_{aperture} (R_injected - R_control) * mask
        """
        pair.validate()

        # Check if pair is identical zero-injection control
        is_identical_control = (
            np.array_equal(pair.injected_image, pair.control_image) and
            np.array_equal(pair.injected_variance, pair.control_variance)
        )

        recon_inj, anom_inj = self._run_model_inference(
            pair.injected_image,
            pair.injected_variance,
            pair.mask
        )

        if is_identical_control:
            recon_ctrl = recon_inj
            anom_ctrl = anom_inj
        else:
            recon_ctrl, anom_ctrl = self._run_model_inference(
                pair.control_image,
                pair.control_variance,
                pair.mask
            )

        H, W = pair.injected_image.shape
        yy, xx = np.ogrid[:H, :W]
        dist_from_target = np.sqrt((xx - pair.sub_x_inj)**2 + (yy - pair.sub_y_inj)**2)
        match_mask = dist_from_target <= match_radius_pix

        if np.any(match_mask):
            target_peak_chi2 = float(np.max(anom_inj[match_mask]))
        else:
            target_peak_chi2 = 0.0

        ap_mask = dist_from_target <= aperture_radius_pix
        aperture_sum_chi2 = float(np.sum(anom_inj[ap_mask]))
        global_peak_chi2 = float(np.max(anom_inj[pair.mask > 0.5])) if np.any(pair.mask > 0.5) else 0.0

        # Subpixel centroid refinement on the injected anomaly map
        match_indices = np.where(match_mask)
        if len(match_indices[0]) > 0:
            window_vals = anom_inj[match_mask]
            best_idx = np.argmax(window_vals)
            int_y = float(match_indices[0][best_idx])
            int_x = float(match_indices[1][best_idx])

            from scripts.validation.astrovision_injection_benchmark import find_subpixel_peak
            sub_rec_y, sub_rec_x = find_subpixel_peak(anom_inj, int_y, int_x)
            pos_err_pix = float(math.sqrt((sub_rec_x - pair.sub_x_inj)**2 + (sub_rec_y - pair.sub_y_inj)**2))
            pos_err_arcsec = pos_err_pix * pair.pixel_scale_arcsec
        else:
            sub_rec_x, sub_rec_y = float("nan"), float("nan")
            pos_err_pix, pos_err_arcsec = float("nan"), float("nan")

        is_detected = bool((target_peak_chi2 >= threshold_tau) and (pos_err_pix <= match_radius_pix))

        valid_ap_mask = ap_mask & (pair.mask > 0.5)
        valid_pix_count = int(np.sum(valid_ap_mask))
        masked_pix_count = int(np.sum(ap_mask & (pair.mask <= 0.5)))

        # 1. Injected Residual Map: R_inj = max(0, I_inj - Recon(I_inj))
        r_inj = np.maximum(0.0, pair.injected_image.astype(np.float64) - recon_inj.astype(np.float64))

        # 2. Control Baseline Residual Map: R_ctrl = max(0, I_ctrl - Recon(I_ctrl))
        r_ctrl = np.maximum(0.0, pair.control_image.astype(np.float64) - recon_ctrl.astype(np.float64))

        mask_f64 = pair.mask.astype(np.float64)

        # Integrated raw aperture fluxes
        raw_inj_flux = float(np.sum(r_inj[ap_mask] * mask_f64[ap_mask]))
        raw_ctrl_flux = float(np.sum(r_ctrl[ap_mask] * mask_f64[ap_mask]))

        # 3. Differential Model Residual Flux:
        # Sum of (R_injected - R_control) * mask within aperture
        # CRUCIAL RULE: Preserve signed differential contributions;
        # do NOT apply a second max(0, .) clipping to the difference!
        if is_identical_control:
            diff_flux = 0.0
            diff_flux_jy = 0.0
        else:
            diff_residual_map = (r_inj - r_ctrl) * mask_f64
            diff_flux = float(np.sum(diff_residual_map[ap_mask]))
            diff_flux_jy = diff_flux * 1e6 * pair.pixel_solid_angle_sr

        return ModelOutputRecoveryRecordV2(
            trial_id=pair.injected_trial_id,
            partition=pair.partition,
            target_true_x=pair.sub_x_inj,
            target_true_y=pair.sub_y_inj,
            injected_flux_sum=pair.injected_flux_sum_mjy_sr_pix,
            model_target_peak_chi2=target_peak_chi2,
            model_aperture_sum_chi2=aperture_sum_chi2,
            model_global_peak_chi2=global_peak_chi2,
            model_recovered_sub_x=sub_rec_x,
            model_recovered_sub_y=sub_rec_y,
            model_position_error_pix=pos_err_pix,
            model_position_error_arcsec=pos_err_arcsec,
            model_residual_flux_mjy_sr=diff_flux,
            is_detected_at_tau=is_detected,
            tau_applied=threshold_tau,
            pair_id=pair.pair_id,
            raw_injected_residual_flux=raw_inj_flux,
            raw_control_residual_flux=raw_ctrl_flux,
            differential_residual_flux=diff_flux,
            differential_residual_flux_jy=diff_flux_jy,
            valid_aperture_pixels=valid_pix_count,
            masked_aperture_pixels=masked_pix_count,
            checkpoint_sha256=self.checkpoint_sha256
        )

    def evaluate_model_output(
        self,
        trial_id: str,
        partition: str,
        injected_image: np.ndarray,
        injected_variance: np.ndarray,
        mask: np.ndarray,
        target_true_x: float,
        target_true_y: float,
        injected_flux_sum: float,
        pixel_scale_arcsec: float,
        threshold_tau: float = 169.10,
        match_radius_pix: float = 2.5,
        aperture_radius_pix: float = 3.5,
        control_image: Optional[np.ndarray] = None,
        control_variance: Optional[np.ndarray] = None,
        pair_id: str = "UNPAIRED",
        pixel_solid_angle_sr: float = NOMINAL_PIXEL_SOLID_ANGLE_SR
    ) -> ModelOutputRecoveryRecordV2:
        """
        Runs model inference on the injected cutout and extracts genuine model outputs.
        If control_image and control_variance are provided, performs Paired Residual Differencing.
        Otherwise falls back to single-cutout evaluation.
        """
        if control_image is not None and control_variance is not None:
            pair = MatchedCutoutPairV2(
                pair_id=pair_id,
                control_trial_id=f"{trial_id}_CTRL",
                injected_trial_id=trial_id,
                partition=partition,
                filename="DIRECT_EVALUATION",
                detector_id=1,
                obs_id="DIRECT",
                det_x0=0,
                det_y0=0,
                det_cx=target_true_x,
                det_cy=target_true_y,
                pixel_scale_arcsec=pixel_scale_arcsec,
                pixel_solid_angle_sr=pixel_solid_angle_sr,
                exptime_sec=115.12,
                applied_agm=0.1168,
                control_image=control_image,
                control_variance=control_variance,
                injected_image=injected_image,
                injected_variance=injected_variance,
                mask=mask,
                sub_x_inj=target_true_x,
                sub_y_inj=target_true_y,
                injected_flux_sum_mjy_sr_pix=injected_flux_sum,
                injected_flux_jy=injected_flux_sum * 1e6 * pixel_solid_angle_sr
            )
            return self.evaluate_paired_model_output(
                pair=pair,
                threshold_tau=threshold_tau,
                match_radius_pix=match_radius_pix,
                aperture_radius_pix=aperture_radius_pix
            )

        # Standalone / Unpaired inference path
        recon_2d, anom_2d = self._run_model_inference(injected_image, injected_variance, mask)

        H, W = injected_image.shape
        yy, xx = np.ogrid[:H, :W]
        dist_from_target = np.sqrt((xx - target_true_x)**2 + (yy - target_true_y)**2)
        match_mask = dist_from_target <= match_radius_pix

        if np.any(match_mask):
            target_peak_chi2 = float(np.max(anom_2d[match_mask]))
        else:
            target_peak_chi2 = 0.0

        ap_mask = dist_from_target <= aperture_radius_pix
        aperture_sum_chi2 = float(np.sum(anom_2d[ap_mask]))
        global_peak_chi2 = float(np.max(anom_2d[mask > 0.5])) if np.any(mask > 0.5) else 0.0

        # Subpixel centroid refinement on the model's chi2 anomaly map
        match_indices = np.where(match_mask)
        if len(match_indices[0]) > 0:
            window_vals = anom_2d[match_mask]
            best_idx = np.argmax(window_vals)
            int_y = float(match_indices[0][best_idx])
            int_x = float(match_indices[1][best_idx])

            from scripts.validation.astrovision_injection_benchmark import find_subpixel_peak
            sub_rec_y, sub_rec_x = find_subpixel_peak(anom_2d, int_y, int_x)
            pos_err_pix = float(math.sqrt((sub_rec_x - target_true_x)**2 + (sub_rec_y - target_true_y)**2))
            pos_err_arcsec = pos_err_pix * pixel_scale_arcsec
        else:
            sub_rec_x, sub_rec_y = float("nan"), float("nan")
            pos_err_pix, pos_err_arcsec = float("nan"), float("nan")

        is_detected = bool((target_peak_chi2 >= threshold_tau) and (pos_err_pix <= match_radius_pix))

        valid_ap_mask = ap_mask & (mask > 0.5)
        valid_pix_count = int(np.sum(valid_ap_mask))
        masked_pix_count = int(np.sum(ap_mask & (mask <= 0.5)))

        model_residual = np.maximum(0.0, injected_image.astype(np.float64) - recon_2d.astype(np.float64)) * mask.astype(np.float64)
        model_residual_flux = float(np.sum(model_residual[ap_mask]))
        diff_flux_jy = model_residual_flux * 1e6 * pixel_solid_angle_sr

        return ModelOutputRecoveryRecordV2(
            trial_id=trial_id,
            partition=partition,
            target_true_x=target_true_x,
            target_true_y=target_true_y,
            injected_flux_sum=injected_flux_sum,
            model_target_peak_chi2=target_peak_chi2,
            model_aperture_sum_chi2=aperture_sum_chi2,
            model_global_peak_chi2=global_peak_chi2,
            model_recovered_sub_x=sub_rec_x,
            model_recovered_sub_y=sub_rec_y,
            model_position_error_pix=pos_err_pix,
            model_position_error_arcsec=pos_err_arcsec,
            model_residual_flux_mjy_sr=model_residual_flux,
            is_detected_at_tau=is_detected,
            tau_applied=threshold_tau,
            pair_id=pair_id,
            raw_injected_residual_flux=model_residual_flux,
            raw_control_residual_flux=0.0,
            differential_residual_flux=model_residual_flux,
            differential_residual_flux_jy=diff_flux_jy,
            valid_aperture_pixels=valid_pix_count,
            masked_aperture_pixels=masked_pix_count,
            checkpoint_sha256=self.checkpoint_sha256
        )


class StratifiedDetectorSamplerV2:
    """
    Provides reproducible, balanced detector-stratified cutout sampling across D1–D6.
    Avoids raster-order top-to-bottom scan bias.
    """

    def __init__(
        self,
        pointing_files: List[str],
        catalog_path: str = "data/processed/validation/pointing_0003_final_validated_catalogue.csv"
    ):
        self.pointing_files = pointing_files
        self.catalog_path = catalog_path
        self.cat_df = pd.read_csv(catalog_path)
        self.cat_ra = self.cat_df["spx_ra"].values
        self.cat_dec = self.cat_df["spx_dec"].values

    def harvest_stratified_safe_cutouts(
        self,
        cutouts_per_detector: int = 50,
        patch_size: int = 128,
        min_source_dist_pix: float = 8.0,
        random_seed: int = 42,
        num_probes_per_file: int = 600
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Samples safe background regions uniformly distributed across each detector array D1–D6.
        Applies detector-aware background estimation (std_eff = max(std_var, mad_bg))
        and exact Chebyshev / FootprintGeometryV2 non-overlap guards.
        """
        rng = np.random.default_rng(random_seed)
        detector_groups: Dict[int, List[str]] = {d: [] for d in range(1, 7)}

        for fp in self.pointing_files:
            v = SPHERExFITSValidatorV2.verify_and_inspect(fp)
            if v.is_valid and v.detector_id in detector_groups:
                detector_groups[v.detector_id].append(fp)

        harvested_by_det: Dict[int, List[Dict[str, Any]]] = {d: [] for d in range(1, 7)}

        for det_id, flist in detector_groups.items():
            if not flist:
                logger.warning(f"No valid Level-2 science files available for Detector {det_id}")
                continue

            # Randomize file examination
            flist_shuffled = flist.copy()
            rng.shuffle(flist_shuffled)
            target_per_file = max(1, int(math.ceil(cutouts_per_detector / len(flist_shuffled))))

            for pass_idx in (1, 2):
                if len(harvested_by_det[det_id]) >= cutouts_per_detector:
                    break

                for fp in flist_shuffled:
                    if len(harvested_by_det[det_id]) >= cutouts_per_detector:
                        break

                    count_in_file = sum(1 for it in harvested_by_det[det_id] if it["filename"] == os.path.basename(fp))
                    if pass_idx == 1 and count_in_file >= target_per_file:
                        continue

                    with fits.open(fp) as hdul:
                        img = hdul["IMAGE"].data.astype(np.float32)
                        var = hdul["VARIANCE"].data.astype(np.float32)
                        flags = hdul["FLAGS"].data.astype(np.int32)
                        wcs = WCS(hdul["IMAGE"].header)
                        v_meta = SPHERExFITSValidatorV2.verify_and_inspect(fp)

                    cat_x, cat_y = wcs.world_to_pixel_values(self.cat_ra, self.cat_dec)
                    source_tree = cKDTree(np.column_stack([cat_x, cat_y]))

                    H, W = img.shape
                    margin = 150
                    # Grid candidate points evenly across the entire 2040x2040 array
                    rand_xs = rng.integers(margin, W - margin - patch_size, size=num_probes_per_file)
                    rand_ys = rng.integers(margin, H - margin - patch_size, size=num_probes_per_file)

                    for x0, y0 in zip(rand_xs, rand_ys):
                        cx = x0 + patch_size // 2
                        cy = y0 + patch_size // 2

                        d_src, _ = source_tree.query([cx, cy])
                        if d_src < min_source_dist_pix:
                            continue

                        core_flags = flags[cy-2:cy+3, cx-2:cx+3]
                        if np.any((core_flags & FATAL_FLAG_MASK) != 0):
                            continue

                        core_img = img[cy-2:cy+3, cx-2:cx+3]
                        local_box = img[cy-8:cy+9, cx-8:cx+9]
                        local_var = var[cy-8:cy+9, cx-8:cx+9]

                        med_bg = np.nanmedian(local_box)
                        var_bg = np.nanmedian(local_var)
                        std_var = math.sqrt(max(1e-6, var_bg))
                        mad_bg = 1.4826 * np.nanmedian(np.abs(local_box - med_bg))
                        std_eff = max(std_var, float(mad_bg))

                        if np.nanmax(core_img) > med_bg + 2.5 * std_eff:
                            continue
                        if np.nanmax(local_box) > max(2.5, med_bg + 5.0 * std_eff):
                            continue

                        # Spatial overlap guard: prevent overlapping cutout footprints within the same file
                        # Uses exact Chebyshev / FootprintGeometryV2 non-overlap: max(|dx|, |dy|) >= patch_size
                        overlap = False
                        for prev in harvested_by_det[det_id]:
                            if prev["filename"] == os.path.basename(fp):
                                if max(abs(cx - prev["cx_det"]), abs(cy - prev["cy_det"])) < patch_size:
                                    overlap = True
                                    break
                        if overlap:
                            continue

                        sub_flags = flags[y0:y0+patch_size, x0:x0+patch_size]
                        full_mask = ((sub_flags & FATAL_FLAG_MASK) == 0).astype(np.float32)
                        if full_mask.mean() < 0.88:
                            continue

                        sub_img = np.nan_to_num(img[y0:y0+patch_size, x0:x0+patch_size], nan=float(med_bg))
                        sub_var = np.maximum(np.nan_to_num(var[y0:y0+patch_size, x0:x0+patch_size], nan=float(var_bg)), 1e-4)

                        harvested_by_det[det_id].append({
                            "fits_path": fp,
                            "filename": os.path.basename(fp),
                            "detector_id": det_id,
                            "obs_id": v_meta.obs_id,
                            "exptime": v_meta.exptime_sec,
                            "pixel_scale": v_meta.pixel_scale_arcsec,
                            "solid_angle": v_meta.pixel_solid_angle_sr,
                            "x0": int(x0),
                            "y0": int(y0),
                            "width": int(patch_size),
                            "height": int(patch_size),
                            "cx_det": float(cx),
                            "cy_det": float(cy),
                            "sub_img": sub_img,
                            "sub_var": sub_var,
                            "sub_mask": full_mask,
                            "bg_median": float(med_bg),
                            "bg_std": float(std_var),
                            "bg_mad": float(mad_bg),
                            "bg_std_eff": float(std_eff)
                        })

                        count_in_file += 1
                        if pass_idx == 1 and count_in_file >= target_per_file:
                            break
                        if len(harvested_by_det[det_id]) >= cutouts_per_detector:
                            break

        return harvested_by_det

    @staticmethod
    def assign_disjoint_partitions(
        harvested_by_det: Dict[int, List[Dict[str, Any]]],
        calibration_fraction: float = 0.5,
        seed: int = 42,
        strict_metadata: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group-aware disjoint partition assignment enforcing exposure-level independence.
        Resolves Audit F by ensuring no obs_id, filename, or overlapping region crosses partitions.
        """
        manager = GroupAwarePartitionManagerV2(strict_metadata=strict_metadata)
        res = manager.assign_partitions(
            harvested_items=harvested_by_det,
            calibration_fraction=calibration_fraction,
            seed=seed
        )
        return {
            "CALIBRATION": res.calibration_items,
            "EVALUATION": res.evaluation_items
        }


@dataclass(frozen=True)
class FootprintGeometryV2:
    """
    Exact spatial cutout footprint in detector pixel coordinates.
    Defines geometry using half-open intervals [x0, x0 + width) x [y0, y0 + height).
    Edge-touching convention: Touching boundaries share 0 interior pixels and are accepted.
    Overlaps occur if and only if two footprints share >= 1 interior pixel in the same file/detector.
    """
    x0: int
    y0: int
    width: int
    height: int
    filename: str
    detector_id: int
    obs_id: str = "UNKNOWN"

    @property
    def x1(self) -> int:
        return self.x0 + self.width

    @property
    def y1(self) -> int:
        return self.y0 + self.height

    @property
    def cx(self) -> float:
        return self.x0 + self.width / 2.0

    @property
    def cy(self) -> float:
        return self.y0 + self.height / 2.0

    def intersects(self, other: "FootprintGeometryV2") -> Tuple[bool, str]:
        """
        Determines whether two footprints overlap in physical detector space.
        Returns (is_overlapping, diagnostic_reason).
        Footprints from different FITS files or different detectors never collide.
        Overlaps in the same file/detector are evaluated via 2D half-open bounding box intersection:
          overlap = max(x0_a, x0_b) < min(x1_a, x1_b) and max(y0_a, y0_b) < min(y1_a, y1_b)
        """
        if self.filename != other.filename or self.detector_id != other.detector_id:
            return False, "DIFFERENT_FILES_OR_DETECTORS"

        x_overlap = max(self.x0, other.x0) < min(self.x1, other.x1)
        y_overlap = max(self.y0, other.y0) < min(self.y1, other.y1)

        if x_overlap and y_overlap:
            inter_w = min(self.x1, other.x1) - max(self.x0, other.x0)
            inter_h = min(self.y1, other.y1) - max(self.y0, other.y0)
            inter_area = inter_w * inter_h
            return True, f"SPATIAL_OVERLAP_{inter_w}x{inter_h}_AREA_{inter_area}_PIXELS"

        return False, "DISJOINT"

    @staticmethod
    def check_chebyshev_center_distance(
        cx1: float, cy1: float,
        cx2: float, cy2: float,
        patch_size: float
    ) -> bool:
        """
        Returns True if Chebyshev distance is strictly less than patch_size
        (indicating overlap for identical axis-aligned square cutouts of side patch_size).
        L_inf = max(|dx|, |dy|) < patch_size
        """
        return max(abs(cx1 - cx2), abs(cy1 - cy2)) < patch_size


@dataclass
class PartitionAssignmentResultV2:
    """Stores partitioned datasets along with audit metadata and leakage diagnostics."""
    calibration_items: List[Dict[str, Any]]
    evaluation_items: List[Dict[str, Any]]
    rejected_items: List[Dict[str, Any]]
    calibration_obs_ids: List[str]
    evaluation_obs_ids: List[str]
    calibration_filenames: List[str]
    evaluation_filenames: List[str]
    calibration_source_ids: List[str]
    evaluation_source_ids: List[str]
    detector_distribution: Dict[str, Dict[int, int]]
    num_independent_groups: int
    is_strictly_disjoint: bool
    diagnostics: Dict[str, Any]


class GroupAwarePartitionManagerV2:
    """
    Exposure-Level and Group-Aware Partitioning Architecture for ASTROVISION Benchmark v2.
    Remediates Audit F (cutout-level leakage) by enforcing a strict hierarchy of independence:
      1. Pointing Exposure / Observation Identity (obs_id):
         The same exposure NEVER appears in both calibration and evaluation partitions.
      2. FITS File Identity:
         All detector arrays and cutouts from a single FITS file belong to the same partition.
      3. Spatial Separation:
         Overlapping cutouts within the same file or sky region are detected and rejected.
      4. Source Identity:
         Repeated observations of the same physical target/source ID are strictly co-grouped.
    """

    def __init__(
        self,
        min_spatial_sep_pix: float = 128.0,
        strict_metadata: bool = True
    ):
        self.min_spatial_sep_pix = min_spatial_sep_pix
        self.strict_metadata = strict_metadata

    def assign_partitions(
        self,
        harvested_items: Union[List[Dict[str, Any]], Dict[int, List[Dict[str, Any]]]],
        calibration_fraction: float = 0.5,
        seed: int = 42
    ) -> PartitionAssignmentResultV2:
        """
        Deterministically assigns harvested cutouts to CALIBRATION and EVALUATION partitions
        while strictly preventing exposure, file, spatial, or source leakage.
        """
        from collections import defaultdict

        # Step 1: Normalize input to flat list
        if isinstance(harvested_items, dict):
            flat_items = []
            for det_id in sorted(harvested_items.keys()):
                flat_items.extend(harvested_items[det_id])
        else:
            flat_items = list(harvested_items)

        # Step 2: Validate metadata and filter out invalid/unresolved items
        valid_items: List[Dict[str, Any]] = []
        rejected_items: List[Dict[str, Any]] = []

        for idx, it in enumerate(flat_items):
            item = dict(it)
            item_id = item.get("id", f"CUTOUT_{idx}")
            item["id"] = item_id

            obs_id = item.get("obs_id")
            filename = item.get("filename")
            detector_id = item.get("detector_id")

            # Exposure metadata check
            if not obs_id or str(obs_id).strip() in ("", "UNKNOWN", "NONE", "NAN"):
                if self.strict_metadata:
                    raise ValueError(
                        f"Item {item_id}: Missing or invalid 'obs_id' metadata ({obs_id}). "
                        f"Physical exposure independence cannot be established."
                    )
                item["rejection_reason"] = "MISSING_OBS_ID"
                rejected_items.append(item)
                continue

            # FITS file identity check
            if not filename or str(filename).strip() in ("", "UNKNOWN", "NONE"):
                if self.strict_metadata:
                    raise ValueError(
                        f"Item {item_id}: Missing or invalid 'filename' metadata ({filename})."
                    )
                item["rejection_reason"] = "MISSING_FILENAME"
                rejected_items.append(item)
                continue

            # Detector ID check
            if detector_id is None or not (1 <= int(detector_id) <= 6):
                if self.strict_metadata:
                    raise ValueError(
                        f"Item {item_id}: Invalid detector ID ({detector_id}); must be in [1..6]."
                    )
                item["rejection_reason"] = "INVALID_DETECTOR_ID"
                rejected_items.append(item)
                continue

            valid_items.append(item)

        # Step 3: Spatial overlap detection within identical FITS files
        spatially_cleared_items: List[Dict[str, Any]] = []
        by_file: Dict[str, List[Dict[str, Any]]] = {}
        for it in valid_items:
            by_file.setdefault(it["filename"], []).append(it)

        for fn, f_items in by_file.items():
            accepted_in_file: List[Dict[str, Any]] = []
            accepted_fps_in_file: List[FootprintGeometryV2] = []
            for it in f_items:
                w = int(it.get("width", self.min_spatial_sep_pix))
                h = int(it.get("height", self.min_spatial_sep_pix))
                if "x0" in it and "y0" in it:
                    x0 = int(it["x0"])
                    y0 = int(it["y0"])
                else:
                    cx = float(it.get("cx_det", it.get("sub_x", 64.0)))
                    cy = float(it.get("cy_det", it.get("sub_y", 64.0)))
                    x0 = int(round(cx - w / 2.0))
                    y0 = int(round(cy - h / 2.0))

                fp = FootprintGeometryV2(
                    x0=x0,
                    y0=y0,
                    width=w,
                    height=h,
                    filename=fn,
                    detector_id=int(it.get("detector_id", 1)),
                    obs_id=str(it.get("obs_id", "UNKNOWN"))
                )

                has_overlap = False
                overlap_reason = ""
                for prev_fp in accepted_fps_in_file:
                    is_inter, reason = fp.intersects(prev_fp)
                    if is_inter:
                        has_overlap = True
                        overlap_reason = reason
                        break

                if has_overlap:
                    rej = dict(it)
                    rej["rejection_reason"] = f"SPATIAL_OVERLAP_WITH_PRIOR_CUTOUT_IN_FILE_{fn}: {overlap_reason}"
                    rejected_items.append(rej)
                else:
                    accepted_in_file.append(it)
                    accepted_fps_in_file.append(fp)
                    spatially_cleared_items.append(it)

        # Step 4: Disjoint Group Formation via Connected Components
        # Hierarchy: obs_id -> filename -> source_id
        obs_to_items = defaultdict(list)
        obs_to_sources = defaultdict(set)
        source_to_obs = defaultdict(set)

        for it in spatially_cleared_items:
            obs = it["obs_id"]
            obs_to_items[obs].append(it)
            src_id = it.get("source_id") or it.get("target_source_id")
            if src_id is not None and str(src_id).strip() not in ("", "NONE", "UNKNOWN"):
                obs_to_sources[obs].add(str(src_id))
                source_to_obs[str(src_id)].add(obs)

        # Disjoint set union (merging exposures sharing the same repeated source_ids)
        parent = {obs: obs for obs in obs_to_items}

        def find(u):
            while parent[u] != u:
                parent[u] = parent[parent[u]]
                u = parent[u]
            return u

        def union(u, v):
            root_u = find(u)
            root_v = find(v)
            if root_u != root_v:
                parent[root_v] = root_u

        for src_id, linked_obs in source_to_obs.items():
            obs_list = list(linked_obs)
            for i in range(1, len(obs_list)):
                union(obs_list[0], obs_list[i])

        clusters = defaultdict(list)
        for obs in obs_to_items:
            root = find(obs)
            clusters[root].append(obs)

        unique_clusters = list(clusters.keys())
        num_clusters = len(unique_clusters)

        # Step 5: Check for Insufficient Independent Groups
        if num_clusters < 2:
            raise ValueError(
                f"Insufficient independent exposure groups ({num_clusters} found; >= 2 required). "
                f"Cannot create disjoint calibration and evaluation partitions without exposure leakage."
            )

        # Step 6: Deterministic Group Assignment with Seed
        unique_clusters.sort()
        rng = np.random.default_rng(seed)
        rng.shuffle(unique_clusters)

        total_cutouts = len(spatially_cleared_items)
        target_cal_count = int(round(total_cutouts * calibration_fraction))

        cal_cluster_roots = set()
        eval_cluster_roots = set()
        current_cal_count = 0

        for root in unique_clusters:
            c_cutouts = sum(len(obs_to_items[obs]) for obs in clusters[root])
            if len(cal_cluster_roots) == 0:
                cal_cluster_roots.add(root)
                current_cal_count += c_cutouts
            elif len(eval_cluster_roots) == 0 and len(cal_cluster_roots) > 0 and len(unique_clusters) == 2:
                eval_cluster_roots.add(root)
            elif (current_cal_count + c_cutouts <= target_cal_count or len(eval_cluster_roots) == 0) and (current_cal_count < target_cal_count):
                cal_cluster_roots.add(root)
                current_cal_count += c_cutouts
            else:
                eval_cluster_roots.add(root)

        # Guarantee at least 1 cluster in each partition
        if len(eval_cluster_roots) == 0:
            moved_root = unique_clusters[-1]
            cal_cluster_roots.remove(moved_root)
            eval_cluster_roots.add(moved_root)

        # Step 7: Populate partition items
        calibration_items: List[Dict[str, Any]] = []
        evaluation_items: List[Dict[str, Any]] = []

        cal_obs_ids = set()
        eval_obs_ids = set()
        cal_filenames = set()
        eval_filenames = set()
        cal_sources = set()
        eval_sources = set()

        for root in cal_cluster_roots:
            for obs in clusters[root]:
                cal_obs_ids.add(obs)
                for it in obs_to_items[obs]:
                    it_copy = dict(it)
                    it_copy["partition"] = "CALIBRATION"
                    cal_filenames.add(it_copy["filename"])
                    src = it_copy.get("source_id")
                    if src:
                        cal_sources.add(str(src))
                    calibration_items.append(it_copy)

        for root in eval_cluster_roots:
            for obs in clusters[root]:
                eval_obs_ids.add(obs)
                for it in obs_to_items[obs]:
                    it_copy = dict(it)
                    it_copy["partition"] = "EVALUATION"
                    eval_filenames.add(it_copy["filename"])
                    src = it_copy.get("source_id")
                    if src:
                        eval_sources.add(str(src))
                    evaluation_items.append(it_copy)

        # Step 8: Strict Leakage Verification Guard (Assert zero leakage)
        assert cal_obs_ids.isdisjoint(eval_obs_ids), "CRITICAL LEAKAGE: Overlapping obs_id in CALIBRATION and EVALUATION"
        assert cal_filenames.isdisjoint(eval_filenames), "CRITICAL LEAKAGE: Overlapping filename in CALIBRATION and EVALUATION"
        if cal_sources and eval_sources:
            assert cal_sources.isdisjoint(eval_sources), "CRITICAL LEAKAGE: Overlapping source_id in CALIBRATION and EVALUATION"

        # Step 9: Detector distribution statistics
        det_dist: Dict[str, Dict[int, int]] = {
            "CALIBRATION": {d: 0 for d in range(1, 7)},
            "EVALUATION": {d: 0 for d in range(1, 7)}
        }
        for it in calibration_items:
            det_dist["CALIBRATION"][it["detector_id"]] += 1
        for it in evaluation_items:
            det_dist["EVALUATION"][it["detector_id"]] += 1

        diagnostics = {
            "total_harvested": len(flat_items),
            "valid_items": len(valid_items),
            "spatially_cleared": len(spatially_cleared_items),
            "rejected_spatial_overlaps": len(valid_items) - len(spatially_cleared_items),
            "num_clusters": num_clusters,
            "cal_clusters": len(cal_cluster_roots),
            "eval_clusters": len(eval_cluster_roots),
            "cal_cutouts": len(calibration_items),
            "eval_cutouts": len(evaluation_items),
            "detector_distribution": det_dist
        }

        return PartitionAssignmentResultV2(
            calibration_items=calibration_items,
            evaluation_items=evaluation_items,
            rejected_items=rejected_items,
            calibration_obs_ids=sorted(list(cal_obs_ids)),
            evaluation_obs_ids=sorted(list(eval_obs_ids)),
            calibration_filenames=sorted(list(cal_filenames)),
            evaluation_filenames=sorted(list(eval_filenames)),
            calibration_source_ids=sorted(list(cal_sources)),
            evaluation_source_ids=sorted(list(eval_sources)),
            detector_distribution=det_dist,
            num_independent_groups=num_clusters,
            is_strictly_disjoint=True,
            diagnostics=diagnostics
        )



