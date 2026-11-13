"""
SPECTRA-X: Scientific Aperture Photometry & Monochromatic Extraction Engine
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Performs:
1. Source detection with Photutils (DAOStarFinder / IRAFStarFinder) on unmasked background-subtracted images.
2. Circular aperture photometry with local annulus background estimation and sigma-clipping.
3. Rigorous uncertainty propagation from Level-2 VARIANCE HDU + background estimation error.
4. Exact pixel-to-wavelength mapping via standalone spectral_wcs_D*.fits (CWAVE and CBAND).
5. Defect masking adhering to the audited FATAL_FLAG_MASK = 615.
"""

import os
import glob
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.wcs import WCS
from astropy.stats import sigma_clipped_stats
from photutils.detection import DAOStarFinder
from photutils.aperture import CircularAperture, CircularAnnulus, ApertureStats

# SPHEREx Fatal Quality Flags Mask (MP_TRANSIENT, MP_OVERFLOW, MP_SUR_ERROR, MP_REFERENCE, MP_NONFUNC, MP_MISSING_DATA)
FATAL_FLAG_MASK = (1 << 0) | (1 << 1) | (1 << 2) | (1 << 5) | (1 << 6) | (1 << 9)  # 615

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SPHERExPhotometry")


class SPHERExPhotometryExtractor:
    """Scientific aperture photometry and spectral coordinate mapping engine."""
    
    def __init__(self,
                 detection_fwhm: float = 2.5,
                 detection_threshold_sigma: float = 5.0,
                 detection_min_separation: float = 4.0,
                 aperture_radius: float = 3.0,
                 annulus_inner_radius: float = 6.0,
                 annulus_outer_radius: float = 10.0,
                 aperture_correction: float = 1.0,
                 min_valid_fraction: float = 0.8,
                 processing_version: str = "v2.1-calibrated"):
        self.detection_fwhm = detection_fwhm
        self.detection_threshold_sigma = detection_threshold_sigma
        self.detection_min_separation = detection_min_separation
        self.aperture_radius = aperture_radius
        self.annulus_inner_radius = annulus_inner_radius
        self.annulus_outer_radius = annulus_outer_radius
        self.aperture_correction = aperture_correction
        self.min_valid_fraction = min_valid_fraction
        self.processing_version = processing_version
        
        # Cache for spectral WCS calibration maps: {(detector_id, release): (cwave_data, cband_data, cal_ver)}
        self._spectral_wcs_cache: Dict[Tuple[int, str], Tuple[np.ndarray, np.ndarray, str]] = {}

    def get_spectral_wcs(self, detector_id: int, release: str = "qr3", base_dir: str = ".") -> Tuple[np.ndarray, np.ndarray, str]:
        """Loads and caches CWAVE and CBAND calibration maps for a given detector."""
        key = (detector_id, release.lower())
        if key in self._spectral_wcs_cache:
            return self._spectral_wcs_cache[key]
            
        pattern = os.path.join(base_dir, "data", "spherex", release.lower(), "calibration", f"*spectral_wcs*D{detector_id}*.fits")
        files = sorted(glob.glob(pattern))
        if not files:
            # Fallback to any release calibration
            pattern_any = os.path.join(base_dir, "data", "spherex", "*", "calibration", f"*spectral_wcs*D{detector_id}*.fits")
            files = sorted(glob.glob(pattern_any))
            
        if not files:
            raise FileNotFoundError(f"No spectral_wcs calibration file found for Detector {detector_id} ({release})")
            
        cal_path = files[-1] # Pick latest version
        with fits.open(cal_path) as hdul:
            cwave = hdul["CWAVE"].data.astype(np.float32)
            cband = hdul["CBAND"].data.astype(np.float32)
            cal_ver = hdul[0].header.get("VERSION", hdul[0].header.get("CAL_VER", "UNKNOWN"))
            
        self._spectral_wcs_cache[key] = (cwave, cband, cal_ver)
        logger.info(f"Loaded Spectral WCS for Detector {detector_id} ({release}) from {os.path.basename(cal_path)} [Version {cal_ver}]")
        return cwave, cband, cal_ver

    def extract_from_fits(self, fits_path: str, max_sources: Optional[int] = None, base_dir: str = ".") -> pd.DataFrame:
        """Executes full detection, background estimation, aperture photometry, and wavelength mapping."""
        if not os.path.exists(fits_path):
            raise FileNotFoundError(f"Level-2 FITS file not found: {fits_path}")
            
        rel_path = os.path.relpath(fits_path, base_dir).replace('\\', '/')
        filename = os.path.basename(fits_path)
        release = "qr2" if "qr2" in rel_path.lower() else "qr3"
        
        with fits.open(fits_path, memmap=False) as hdul:
            # Metadata
            hdr0 = hdul[0].header
            hdr1 = hdul[1].header
            
            obsid = hdr1.get("OBSID", hdr0.get("OBSID", "UNKNOWN"))
            detector_id = int(hdr1.get("DETECTOR", hdr0.get("DETECTOR", 1)))
            date_obs = hdr1.get("DATE-OBS", "UNKNOWN")
            mjd_obs = float(hdr1.get("MJD-OBS", 0.0))
            cal_ver = hdr0.get("VERSION", hdr1.get("VERSION", "UNKNOWN"))
            
            img_data = hdul["IMAGE"].data.astype(np.float32)
            var_data = hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in hdul else np.full_like(img_data, 1e-3)
            flags_data = hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in hdul else np.zeros_like(img_data, dtype=np.int32)
            
            wcs = WCS(hdr1)

        # Load CWAVE and CBAND for this detector
        cwave_map, cband_map, swcs_ver = self.get_spectral_wcs(detector_id, release=release, base_dir=base_dir)

        # 1. Defect Masking
        fatal_mask = (flags_data & FATAL_FLAG_MASK) > 0
        nan_mask = np.isnan(img_data) | np.isnan(var_data)
        bad_mask = fatal_mask | nan_mask

        # 2. Global background estimation for detection
        # Use center region to avoid reference pixels and boundary effects
        H, W = img_data.shape
        center_slice = img_data[100:H-100, 100:W-100]
        center_bad = bad_mask[100:H-100, 100:W-100]
        valid_center = center_slice[~center_bad]
        
        if len(valid_center) == 0:
            logger.warning(f"No valid pixels in center slice of {filename}")
            return pd.DataFrame()
            
        bkg_mean, bkg_median, bkg_std = sigma_clipped_stats(valid_center, sigma=3.0, maxiters=5)
        
        # 3. Source Detection
        # Clean image for detection: set bad pixels to background median
        detection_img = img_data - bkg_median
        detection_img[bad_mask] = 0.0
        
        daofind = DAOStarFinder(fwhm=self.detection_fwhm,
                                threshold=self.detection_threshold_sigma * bkg_std,
                                min_separation=self.detection_min_separation)
        detected_sources = daofind(detection_img)
        
        if detected_sources is None or len(detected_sources) == 0:
            logger.info(f"Zero sources detected in {filename}")
            return pd.DataFrame()
            
        if max_sources is not None and len(detected_sources) > max_sources:
            if 'peak' in detected_sources.colnames:
                detected_sources.sort('peak', reverse=True)
            detected_sources = detected_sources[:max_sources]
            
        n_detected = len(detected_sources)
        logger.info(f"Detected {n_detected} source candidates in {filename} (Detector {detector_id}, MJD {mjd_obs:.4f})")

        # Extract coordinates
        x_col = 'x_centroid' if 'x_centroid' in detected_sources.colnames else 'xcentroid'
        y_col = 'y_centroid' if 'y_centroid' in detected_sources.colnames else 'ycentroid'
        x_coords = np.array(detected_sources[x_col])
        y_coords = np.array(detected_sources[y_col])
        positions = np.transpose((x_coords, y_coords))

        # 4. Circular Aperture Photometry
        apertures = CircularAperture(positions, r=self.aperture_radius)
        annuli = CircularAnnulus(positions, r_in=self.annulus_inner_radius, r_out=self.annulus_outer_radius)

        # Aperture and Annulus stats
        ap_stats = ApertureStats(img_data, apertures, mask=bad_mask)
        ann_stats = ApertureStats(img_data, annuli, mask=bad_mask)
        
        # Variance stats within aperture for uncertainty propagation
        ap_var_stats = ApertureStats(var_data, apertures, mask=bad_mask)

        # Compute celestial coordinates
        ra_coords, dec_coords = wcs.pixel_to_world_values(x_coords, y_coords)

        # 5. Assemble Photometric Records
        records = []
        nominal_ap_area = np.pi * (self.aperture_radius ** 2)
        nominal_ann_area = np.pi * (self.annulus_outer_radius ** 2 - self.annulus_inner_radius ** 2)

        for i in range(n_detected):
            xi, yi = x_coords[i], y_coords[i]
            ix, iy = int(np.clip(round(xi), 0, W - 1)), int(np.clip(round(yi), 0, H - 1))
            
            # Aperture unmasked pixel count and fraction
            ap_area_val = ap_stats.sum_aper_area[i]
            ap_npixels = float(ap_area_val.value if hasattr(ap_area_val, 'value') else ap_area_val)
            valid_frac = float(ap_npixels / nominal_ap_area)
            
            # Local background from annulus
            ann_median_bkg = float(ann_stats.median[i])
            ann_std_bkg = float(ann_stats.std[i])
            ann_area_val = ann_stats.sum_aper_area[i]
            ann_npixels = float(ann_area_val.value if hasattr(ann_area_val, 'value') else ann_area_val)
            
            # Fallback if annulus is mostly masked
            if np.isnan(ann_median_bkg) or ann_npixels < 5:
                ann_median_bkg = bkg_median
                ann_std_bkg = bkg_std
                ann_npixels = 5.0

            # Background-subtracted raw aperture flux
            raw_sum = float(ap_stats.sum[i])
            if np.isnan(raw_sum) or ap_npixels == 0:
                continue
                
            # Subtracted flux (surface brightness integrated over unmasked aperture)
            bkg_subtracted_flux = (raw_sum - (ann_median_bkg * ap_npixels)) * self.aperture_correction

            # Uncertainty propagation:
            # 1. Sum of per-pixel variances in aperture
            ap_var_sum = ap_var_stats.sum[i]
            if np.isnan(ap_var_sum) or ap_var_sum <= 0:
                ap_var_sum = ap_npixels * (bkg_std ** 2)
                
            # 2. Uncertainty in background estimation from annulus
            # sigma_bkg_mean^2 = sigma_annulus^2 / N_annulus
            bkg_var_est = (ann_std_bkg ** 2) / max(1, ann_npixels)
            
            # 3. Total propagated variance
            # Var(Flux) = Var(aperture_sum) + ap_npixels^2 * Var(background)
            total_flux_variance = (ap_var_sum + (ap_npixels ** 2) * bkg_var_est) * (self.aperture_correction ** 2)
            flux_uncertainty = float(np.sqrt(max(total_flux_variance, 1e-10)))
            snr = float(bkg_subtracted_flux / flux_uncertainty) if flux_uncertainty > 0 else 0.0

            # Spectral WCS mapping
            central_wave = float(cwave_map[iy, ix])
            bandwidth = float(cband_map[iy, ix])

            # Local quality flags at centroid
            q_flag = int(flags_data[iy, ix])

            # Source naming: SPX-DET-OBSID-INDEX
            source_id = f"SPX-J{ra_coords[i]:08.4f}{dec_coords[i]:+08.4f}"

            records.append({
                "source_id": source_id,
                "ra": float(ra_coords[i]),
                "dec": float(dec_coords[i]),
                "detector_id": detector_id,
                "observation_id": obsid,
                "mjd": mjd_obs,
                "x": float(xi),
                "y": float(yi),
                "aperture_radius": float(self.aperture_radius),
                "background": float(ann_median_bkg),
                "flux": float(bkg_subtracted_flux),
                "flux_uncertainty": flux_uncertainty,
                "snr": round(snr, 2),
                "central_wavelength": round(central_wave, 5),
                "bandwidth": round(bandwidth, 5),
                "quality_flags": q_flag,
                "valid_pixel_fraction": round(valid_frac, 3),
                "calibration_version": str(cal_ver),
                "source_file": filename,
                "processing_version": self.processing_version
            })

        df = pd.DataFrame(records)
        return df


def extract_batch_photometry(fits_pattern: str, output_csv: str, max_files: int = 10, max_sources_per_file: int = 200) -> pd.DataFrame:
    """Batch extraction across multiple SPHEREx Level-2 files."""
    extractor = SPHERExPhotometryExtractor()
    files = sorted(glob.glob(fits_pattern))
    
    if not files:
        print(f"No files matched pattern: {fits_pattern}")
        return pd.DataFrame()
        
    all_dfs = []
    for f in files[:max_files]:
        try:
            print(f"Extracting photometry from {os.path.basename(f)}...")
            df = extractor.extract_from_fits(f, max_sources=max_sources_per_file)
            if not df.empty:
                all_dfs.append(df)
        except Exception as e:
            print(f"Error processing {f}: {e}")
            
    if all_dfs:
        combined_df = pd.concat(all_dfs, ignore_index=True)
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        combined_df.to_csv(output_csv, index=False)
        print(f"Saved {len(combined_df)} photometric measurements to {output_csv}")
        return combined_df
    return pd.DataFrame()


if __name__ == '__main__':
    # Test execution on sample QR3 and QR2 Level-2 files
    sample_pattern = "data/spherex/qr3/level2/*.fits"
    out_path = "data/processed/spectral_features/sample_extracted_photometry.csv"
    extract_batch_photometry(sample_pattern, out_path, max_files=2, max_sources_per_file=50)
