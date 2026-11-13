"""
SPECTRA-X / F1 — Phase 3, Task 1
ASTROVISION: Scientific Spatial Injection & Recovery Benchmark Engine

Role: Senior Astronomical Image Processing Engineer, Scientific Validation Engineer,
      and Deep Learning Research Scientist.

Scientific Standards Enforced:
1. Genuine SPHEREx Level-2 FITS files exclusively (Pointing 0003 held-out test pointing).
2. Detector-aware effective PSF (ePSF) sampling using official 5x oversampled templates.
3. Extended morphologies (Gaussian / Sérsic profiles) with proper pixel scale conversion (6.1522 arcsec/pix).
4. Rigorous variance propagation: Var_new = Var_orig + dI * (AGM / EXPTIME).
5. Exact flux conservation: Sum of rendered PSF equals injected total flux density.
6. Subpixel interpolation via RegularGridInterpolator without arbitrary Gaussian substitution.
7. Wilson score 95% confidence intervals on binomial completeness metrics.
8. Model checkpoint frozen: checkpoints/astrovision_spatial_v2.pt. Zero retraining.
"""

import os
import glob
import math
import logging
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_scales
from scipy.interpolate import RegularGridInterpolator
from scipy.spatial import cKDTree
from scipy.optimize import curve_fit
import torch

from models.astrovision.model import AstroVisionAutoencoder

# Fatal defect flags bitmask per audited SPHEREx quality policy
FATAL_FLAG_MASK = 615

# Default physical constants and SPHEREx parameters
DEFAULT_PIXEL_SCALE_ARCSEC = 6.1522
DEFAULT_EXPTIME_SEC = 115.12
DEFAULT_AGM = 0.11683  # MJy * s / (electron * sr)

logger = logging.getLogger("AstroVisionBenchmark")


def find_subpixel_peak(grid_2d: np.ndarray, center_y: float, center_x: float) -> Tuple[float, float]:
    """
    Fits 2D quadratic parabolic polynomial to 3x3 neighborhood around integer peak
    to find continuous subpixel centroid (y_sub, x_sub).
    """
    H, W = grid_2d.shape
    iy = int(np.clip(round(center_y), 1, H - 2))
    ix = int(np.clip(round(center_x), 1, W - 2))

    patch = grid_2d[iy-1:iy+2, ix-1:ix+2]

    # Parabolic subpixel refinement in x
    denom_x = patch[1, 0] - 2.0 * patch[1, 1] + patch[1, 2]
    if abs(denom_x) > 1e-6:
        dx = 0.5 * (patch[1, 0] - patch[1, 2]) / denom_x
        dx = float(np.clip(dx, -0.6, 0.6))
    else:
        dx = 0.0

    # Parabolic subpixel refinement in y
    denom_y = patch[0, 1] - 2.0 * patch[1, 1] + patch[2, 1]
    if abs(denom_y) > 1e-6:
        dy = 0.5 * (patch[0, 1] - patch[2, 1]) / denom_y
        dy = float(np.clip(dy, -0.6, 0.6))
    else:
        dy = 0.0

    return float(iy + dy), float(ix + dx)


class SPHERExPSFProvider:
    """
    Manages detector-aware effective PSF (ePSF) templates.
    Caches 5x oversampled ePSF spatial bins from official SPHEREx calibration products.
    """

    def __init__(self, templates_dir: str = "data/spherex/qr3/templates"):
        self.templates_dir = templates_dir
        self._cache: Dict[int, Dict[str, Any]] = {}

    def _load_detector_psf_table(self, detector_id: int) -> Dict[str, Any]:
        if detector_id in self._cache:
            return self._cache[detector_id]

        pat = os.path.join(self.templates_dir, f"epsf_D{detector_id}_*.fits")
        files = sorted(glob.glob(pat))
        if not files:
            raise FileNotFoundError(f"Official ePSF template for Detector {detector_id} not found in {self.templates_dir}")

        epsf_path = files[0]
        with fits.open(epsf_path) as hdul:
            hdr = hdul[1].header
            ovsmp_x = float(hdr.get("OVSMPX", 5.0))
            ovsmp_y = float(hdr.get("OVSMPY", 5.0))
            tb_data = hdul[1].data

            x_centers = np.array(tb_data["XCENTER"], dtype=np.float64)
            y_centers = np.array(tb_data["YCENTER"], dtype=np.float64)
            psf_cubes = np.array(tb_data["EPSF"], dtype=np.float64)  # (441, 33, 33)

        n_sub = psf_cubes.shape[1]
        center_sub = (n_sub - 1.0) / 2.0  # 16.0
        native_coords = (np.arange(n_sub, dtype=np.float64) - center_sub) / ovsmp_x

        info = {
            "path": epsf_path,
            "ovsmp": (ovsmp_x, ovsmp_y),
            "native_coords": native_coords,
            "x_centers": x_centers,
            "y_centers": y_centers,
            "psf_cubes": psf_cubes,
            "tree": cKDTree(np.column_stack([x_centers, y_centers]))
        }
        self._cache[detector_id] = info
        return info

    def get_interpolator(self, detector_id: int, det_x: float, det_y: float) -> RegularGridInterpolator:
        """Finds nearest spatial ePSF bin and returns 2D subpixel interpolator in native pixel units."""
        info = self._load_detector_psf_table(detector_id)
        _, nearest_idx = info["tree"].query([det_x, det_y])
        psf_2d = info["psf_cubes"][nearest_idx]

        coords = info["native_coords"]
        return RegularGridInterpolator(
            (coords, coords),
            psf_2d,
            method="linear",
            bounds_error=False,
            fill_value=0.0
        )

    def render_point_source(
        self,
        detector_id: int,
        det_x: float,
        det_y: float,
        sub_x: float,
        sub_y: float,
        total_flux: float,
        kernel_radius: int = 5
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Renders a point source onto an integer pixel grid around (sub_x, sub_y).
        Returns:
            xs: 1D array of column indices
            ys: 1D array of row indices
            flux_2d: 2D array of flux density in MJy/sr with exact flux conservation
        """
        interp = self.get_interpolator(detector_id, det_x, det_y)

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

        k_sum = kernel.sum()
        if k_sum <= 0:
            raise ValueError(f"Interpolated ePSF kernel sum is non-positive: {k_sum}")

        # Exact flux conservation normalization
        kernel_norm = kernel / k_sum
        flux_2d = kernel_norm * total_flux
        return xs, ys, flux_2d


class SpatialInjectionEngine:
    """
    Renders point-source and extended-source synthetic astronomical injections
    into genuine SPHEREx cutouts while preserving scientific and physical integrity.
    """

    def __init__(self, psf_provider: Optional[SPHERExPSFProvider] = None):
        self.psf_provider = psf_provider or SPHERExPSFProvider()

    def inject_point_source(
        self,
        img: np.ndarray,
        var: np.ndarray,
        flags: np.ndarray,
        sub_x: float,
        sub_y: float,
        total_flux: float,
        detector_id: int,
        det_x: float,
        det_y: float,
        agm: float = DEFAULT_AGM,
        exptime: float = DEFAULT_EXPTIME_SEC,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Dict[str, Any]:
        """Injects ePSF point source into a cutout."""
        if rng is None:
            rng = np.random.default_rng()

        xs, ys, s_flux = self.psf_provider.render_point_source(
            detector_id=detector_id,
            det_x=det_x,
            det_y=det_y,
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux=total_flux,
            kernel_radius=5
        )

        inj_img = img.copy()
        inj_var = var.copy()
        signal_map = np.zeros_like(img, dtype=np.float32)

        H, W = img.shape
        valid_x = (xs >= 0) & (xs < W)
        valid_y = (ys >= 0) & (ys < H)

        sub_xs = xs[valid_x]
        sub_ys = ys[valid_y]
        sub_flux = s_flux[np.ix_(valid_y, valid_x)]

        # Physical shot noise variance propagation: Var_shot = I_source * (AGM / exptime)
        shot_rate_conversion = agm / max(1e-3, exptime)
        shot_var = np.maximum(0.0, sub_flux * shot_rate_conversion)

        if add_poisson_noise:
            inv_rate = exptime / max(1e-6, agm)
            expected_electrons = np.maximum(0.0, sub_flux * inv_rate)
            observed_electrons = rng.poisson(expected_electrons).astype(np.float64)
            noisy_flux = observed_electrons * (agm / exptime)
            flux_to_add = noisy_flux
        else:
            flux_to_add = sub_flux

        inj_img[np.ix_(sub_ys, sub_xs)] += flux_to_add.astype(np.float32)
        inj_var[np.ix_(sub_ys, sub_xs)] += shot_var.astype(np.float32)
        signal_map[np.ix_(sub_ys, sub_xs)] += sub_flux.astype(np.float32)

        peak_injected = float(np.max(sub_flux))
        return {
            "injected_image": inj_img,
            "injected_variance": inj_var,
            "signal_map": signal_map,
            "peak_flux": peak_injected,
            "actual_added_flux": float(np.sum(sub_flux)),
            "source_type": "POINT_SOURCE_EPSF"
        }

    def inject_extended_source(
        self,
        img: np.ndarray,
        var: np.ndarray,
        flags: np.ndarray,
        sub_x: float,
        sub_y: float,
        total_flux: float,
        fwhm_arcsec: float,
        pixel_scale_arcsec: float = DEFAULT_PIXEL_SCALE_ARCSEC,
        agm: float = DEFAULT_AGM,
        exptime: float = DEFAULT_EXPTIME_SEC,
        add_poisson_noise: bool = True,
        rng: Optional[np.random.Generator] = None
    ) -> Dict[str, Any]:
        """Injects extended 2D Gaussian morphology source."""
        if rng is None:
            rng = np.random.default_rng()

        fwhm_pix = fwhm_arcsec / pixel_scale_arcsec
        sigma_pix = fwhm_pix / (2.0 * math.sqrt(2.0 * math.log(2.0)))

        kernel_radius = int(math.ceil(4.0 * sigma_pix))
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
        prof_sum = raw_profile.sum()
        if prof_sum <= 0:
            raise ValueError("Extended profile sum is non-positive")

        norm_profile = raw_profile / prof_sum
        s_flux = norm_profile * total_flux

        inj_img = img.copy()
        inj_var = var.copy()
        signal_map = np.zeros_like(img, dtype=np.float32)

        H, W = img.shape
        valid_x = (xs >= 0) & (xs < W)
        valid_y = (ys >= 0) & (ys < H)

        sub_xs = xs[valid_x]
        sub_ys = ys[valid_y]
        sub_flux = s_flux[np.ix_(valid_y, valid_x)]

        shot_rate_conversion = agm / max(1e-3, exptime)
        shot_var = np.maximum(0.0, sub_flux * shot_rate_conversion)

        if add_poisson_noise:
            inv_rate = exptime / max(1e-6, agm)
            expected_electrons = np.maximum(0.0, sub_flux * inv_rate)
            observed_electrons = rng.poisson(expected_electrons).astype(np.float64)
            noisy_flux = observed_electrons * (agm / exptime)
            flux_to_add = noisy_flux
        else:
            flux_to_add = sub_flux

        inj_img[np.ix_(sub_ys, sub_xs)] += flux_to_add.astype(np.float32)
        inj_var[np.ix_(sub_ys, sub_xs)] += shot_var.astype(np.float32)
        signal_map[np.ix_(sub_ys, sub_xs)] += sub_flux.astype(np.float32)

        peak_injected = float(np.max(sub_flux))
        return {
            "injected_image": inj_img,
            "injected_variance": inj_var,
            "signal_map": signal_map,
            "peak_flux": peak_injected,
            "actual_added_flux": float(np.sum(sub_flux)),
            "fwhm_arcsec": fwhm_arcsec,
            "fwhm_pix": fwhm_pix,
            "source_type": "EXTENDED_GAUSSIAN"
        }


class SafeRegionCatalogScanner:
    """
    Identifies safe, clean background regions on SPHEREx Level-2 images:
    - Zero known catalog sources within protective isolation radius.
    - Zero fatal quality flags in central injection core.
    - Quiescent, unflagged background conforming to verified noise levels.
    """

    def __init__(self, catalog_path: str = "data/processed/validation/pointing_0003_final_validated_catalogue.csv"):
        self.catalog_path = catalog_path
        self.cat_df = pd.read_csv(catalog_path)
        self.cat_ra = self.cat_df["spx_ra"].values
        self.cat_dec = self.cat_df["spx_dec"].values

    def scan_file_for_safe_cutouts(
        self,
        fits_path: str,
        patch_size: int = 128,
        stride: int = 48,
        min_source_dist_pix: float = 8.0,
        min_valid_fraction: float = 0.85,
        max_cutouts: int = 40
    ) -> List[Dict[str, Any]]:
        with fits.open(fits_path) as hdul:
            img = hdul["IMAGE"].data.astype(np.float32)
            var = hdul["VARIANCE"].data.astype(np.float32)
            flags = hdul["FLAGS"].data.astype(np.int32)
            wcs = WCS(hdul["IMAGE"].header)

            h0 = hdul[0].header
            h1 = hdul[1].header
            det_id = int(h0.get("DETECTOR", h1.get("DETECTOR", 1)))
            obs_id = str(h0.get("OBS_ID", h1.get("OBSID", os.path.basename(fits_path))))
            exptime = float(h1.get("EXPTIME", DEFAULT_EXPTIME_SEC))

            scales = proj_plane_pixel_scales(wcs) * 3600.0
            pix_scale = float(np.mean(scales)) if len(scales) > 0 else DEFAULT_PIXEL_SCALE_ARCSEC

        cat_x, cat_y = wcs.world_to_pixel_values(self.cat_ra, self.cat_dec)
        source_tree = cKDTree(np.column_stack([cat_x, cat_y]))

        H, W = img.shape
        safe_cutouts = []
        margin = 150

        for y0 in range(margin, H - margin - patch_size, stride):
            for x0 in range(margin, W - margin - patch_size, stride):
                cx = x0 + patch_size // 2
                cy = y0 + patch_size // 2

                # 1. Check isolation from known catalog sources
                d_src, _ = source_tree.query([cx, cy])
                if d_src < min_source_dist_pix:
                    continue

                # 2. Check that central 5x5 core has zero fatal flags
                core_flags = flags[cy-2:cy+3, cx-2:cx+3]
                if np.any((core_flags & FATAL_FLAG_MASK) != 0):
                    continue

                # 3. Check local background is clean (no uncataloged star in 17x17 neighborhood)
                core_img = img[cy-2:cy+3, cx-2:cx+3]
                local_box_img = img[cy-8:cy+9, cx-8:cx+9]
                local_box_var = var[cy-8:cy+9, cx-8:cx+9]

                med_bg = np.nanmedian(local_box_img)
                var_bg = np.nanmedian(local_box_var)
                std_bg = math.sqrt(max(1e-6, var_bg))

                # Core must not be a source
                if np.nanmax(core_img) > med_bg + 2.5 * std_bg:
                    continue

                # Avoid monster saturated stars in neighborhood
                if np.nanmax(local_box_img) > max(2.5, med_bg + 5.0 * std_bg):
                    continue

                # 4. Check entire cutout valid pixel fraction
                sub_flags = flags[y0:y0+patch_size, x0:x0+patch_size]
                full_mask = ((sub_flags & FATAL_FLAG_MASK) == 0)
                if full_mask.mean() < min_valid_fraction:
                    continue

                sub_img = np.nan_to_num(img[y0:y0+patch_size, x0:x0+patch_size], nan=float(med_bg))
                sub_var = np.maximum(np.nan_to_num(var[y0:y0+patch_size, x0:x0+patch_size], nan=float(var_bg)), 1e-4)

                safe_cutouts.append({
                    "fits_path": fits_path,
                    "filename": os.path.basename(fits_path),
                    "detector_id": det_id,
                    "obs_id": obs_id,
                    "exptime": exptime,
                    "pixel_scale": pix_scale,
                    "x0": x0,
                    "y0": y0,
                    "cx_det": cx,
                    "cy_det": cy,
                    "sub_img": sub_img,
                    "sub_var": sub_var,
                    "sub_mask": full_mask.astype(np.float32),
                    "bg_median": float(med_bg),
                    "bg_std": float(std_bg),
                    "dist_to_catalog_src_pix": float(d_src)
                })

                if len(safe_cutouts) >= max_cutouts:
                    return safe_cutouts

        return safe_cutouts


class AstroVisionEvaluator:
    """
    Evaluates ASTROVISION anomaly detection performance on cutouts:
    - Calculates chi2 normalized reconstruction anomaly map.
    - Measures peak anomaly score in aperture around injection.
    - Matches recovered source position and computes astrometric offset.
    - Measures recovered flux via aperture photometry.
    """

    def __init__(self, checkpoint_path: str = "checkpoints/astrovision_spatial_v2.pt", device: Optional[str] = None):
        self.checkpoint_path = checkpoint_path
        self.device = torch.device(device if device else ("cuda" if torch.cuda.is_available() else "cpu"))

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"ASTROVISION checkpoint not found at {checkpoint_path}")

        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.model = AstroVisionAutoencoder().to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        self.patch_size = 128
        yy, xx = np.ogrid[:self.patch_size, :self.patch_size]
        self.r_center = np.sqrt((xx - (self.patch_size // 2))**2 + (yy - (self.patch_size // 2))**2)

    def evaluate_cutout(
        self,
        img: np.ndarray,
        var: np.ndarray,
        mask: np.ndarray,
        target_sub_x: float = 64.0,
        target_sub_y: float = 64.0,
        match_radius_pix: float = 2.5,
        aperture_radius_pix: float = 3.0
    ) -> Dict[str, Any]:
        """
        Runs model inference on a 128x128 cutout.
        Returns:
            anomaly_map, peak_chi2, center_peak, recovered_x, recovered_y, pos_error_pix
        """
        t_img = torch.from_numpy(img.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)
        t_var = torch.from_numpy(var.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)
        t_mask = torch.from_numpy(mask.astype(np.float32)).unsqueeze(0).unsqueeze(0).to(self.device)

        with torch.no_grad():
            recon = self.model(t_img)
            anom = self.model.compute_anomaly_map(t_img, t_var, t_mask)

        anom_map = anom.squeeze().cpu().numpy()
        recon_map = recon.squeeze().cpu().numpy()

        H, W = img.shape
        yy, xx = np.ogrid[:H, :W]
        dist_from_target = np.sqrt((xx - target_sub_x)**2 + (yy - target_sub_y)**2)
        match_mask = dist_from_target <= match_radius_pix

        if np.any(match_mask):
            target_peak_chi2 = float(np.max(anom_map[match_mask]))
        else:
            target_peak_chi2 = 0.0

        ap_mask = dist_from_target <= aperture_radius_pix
        aperture_sum_chi2 = float(np.sum(anom_map[ap_mask]))

        valid_anom = anom_map[mask > 0.5]
        global_peak_chi2 = float(np.max(valid_anom)) if len(valid_anom) > 0 else 0.0

        # Subpixel peak refinement
        match_indices = np.where(match_mask)
        if len(match_indices[0]) > 0:
            window_vals = anom_map[match_mask]
            best_idx = np.argmax(window_vals)
            int_y = float(match_indices[0][best_idx])
            int_x = float(match_indices[1][best_idx])
            sub_rec_y, sub_rec_x = find_subpixel_peak(anom_map, int_y, int_x)
            pos_error = float(math.sqrt((sub_rec_x - target_sub_x)**2 + (sub_rec_y - target_sub_y)**2))
        else:
            sub_rec_x, sub_rec_y, pos_error = float("nan"), float("nan"), float("nan")

        return {
            "anomaly_map": anom_map,
            "reconstruction": recon_map,
            "target_peak_chi2": target_peak_chi2,
            "aperture_sum_chi2": aperture_sum_chi2,
            "global_peak_chi2": global_peak_chi2,
            "recovered_sub_x": sub_rec_x,
            "recovered_sub_y": sub_rec_y,
            "position_error_pix": pos_error
        }


def compute_wilson_confidence_interval(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    """Computes Wilson score binomial confidence interval [lower, upper]."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996
    p = k / n
    denom = 1.0 + (z**2) / n
    center = (p + (z**2) / (2.0 * n)) / denom
    spread = (z * math.sqrt((p * (1.0 - p) / n) + (z**2) / (4.0 * (n**2)))) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return lower, upper


def logistic_sigmoid(x: np.ndarray, x0: float, k: float) -> np.ndarray:
    """Logistic sigmoid function for completeness curve fitting: 1 / (1 + exp(-k * (x - x0)))."""
    return 1.0 / (1.0 + np.exp(-np.clip(k * (x - x0), -50.0, 50.0)))


def fit_completeness_curve(fluxes: np.ndarray, detections: np.ndarray) -> Dict[str, Any]:
    """
    Fits logistic curve to binary detection outcomes as a function of flux / SNR.
    Calculates 50% and 90% completeness thresholds.
    """
    unique_fluxes = np.unique(fluxes)
    binned_x = []
    binned_rate = []
    binned_n = []
    binned_k = []

    for uf in unique_fluxes:
        mask = (fluxes == uf)
        n = int(np.sum(mask))
        k = int(np.sum(detections[mask]))
        binned_x.append(uf)
        binned_rate.append(k / n)
        binned_n.append(n)
        binned_k.append(k)

    binned_x = np.array(binned_x, dtype=np.float64)
    binned_rate = np.array(binned_rate, dtype=np.float64)

    p0 = [float(np.median(binned_x)), 0.5]
    try:
        popt, _ = curve_fit(logistic_sigmoid, binned_x, binned_rate, p0=p0, maxfev=10000)
        x0_fit, k_fit = float(popt[0]), float(popt[1])
        if k_fit > 0:
            c50 = x0_fit
            c90 = x0_fit + (math.log(9.0) / k_fit)
        else:
            c50 = float("nan")
            c90 = float("nan")
    except Exception as e:
        logger.warning(f"Sigmoid fit failed: {e}. Falling back to empirical interpolation.")
        x0_fit, k_fit = float("nan"), float("nan")
        c50 = float(np.interp(0.50, binned_rate, binned_x))
        c90 = float(np.interp(0.90, binned_rate, binned_x))

    return {
        "binned_x": binned_x,
        "binned_rate": binned_rate,
        "binned_n": binned_n,
        "binned_k": binned_k,
        "x0_fit": x0_fit,
        "k_fit": k_fit,
        "completeness_50": c50,
        "completeness_90": c90
    }
