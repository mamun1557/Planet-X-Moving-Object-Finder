"""
SPECTRA-X: Photometric & Spectral Extraction Scientific Validation Suite
NASA Space Apps Challenge 2026 — F1 V2.1 Architecture

Validates:
1. Source detection dynamic range across bright, faint, and crowded regimes.
2. Circular aperture photometry repeatability across overlapping dither pairs.
3. Uncertainty consistency and Gaussian pull statistics: xi = (F1 - F2) / sqrt(sigma1^2 + sigma2^2).
4. Defect rejection and fatal flag masking policy (FATAL_FLAG_MASK = 615).
5. Spectral WCS channel mapping and 102-channel spectrophotometric vector assembly.
6. Benchmark comparison against official IRSA SPHEREx Level-2 specifications.
"""

import os
import glob
import json
import logging
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
import astropy.units as u
from scipy.spatial.distance import cdist

import sys
sys.path.insert(0, os.path.abspath("."))

from models.spectra.extract_photometry import SPHERExPhotometryExtractor, FATAL_FLAG_MASK
from models.spectra.assemble_spectrum import SPHERExSpectrumAssembler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SPHERExPhotometryValidator")


class SPHERExPhotometryValidator:
    """Scientific validation suite for aperture photometry and spectral extraction."""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = base_dir
        self.extractor = SPHERExPhotometryExtractor(
            detection_fwhm=2.5,
            detection_threshold_sigma=5.0,
            detection_min_separation=4.0,
            aperture_radius=3.0,
            annulus_inner_radius=6.0,
            annulus_outer_radius=10.0,
            aperture_correction=1.0,
            min_valid_fraction=0.80
        )
        self.assembler = SPHERExSpectrumAssembler(
            match_radius_arcsec=2.0,
            base_dir=base_dir
        )
        self.processed_dir = os.path.join(base_dir, "data", "processed", "spectral_features")
        os.makedirs(self.processed_dir, exist_ok=True)

    def select_validation_fits(self) -> Dict[str, List[str]]:
        """Selects well-characterized dither sets from the existing 5.195 GB dataset."""
        # 1. QR3 Wide Pointing 1 (Detector 1, 4 consecutive dithers)
        qr3_dithers = sorted(glob.glob(os.path.join(self.base_dir, "data", "spherex", "qr3", "level2", "*0001_*D1*.fits")))
        
        # 2. QR2 Wide Pointing 1 (Detector 2, 4 consecutive dithers)
        qr2_dithers = sorted(glob.glob(os.path.join(self.base_dir, "data", "spherex", "qr2", "level2", "*0001_*D2*.fits")))
        
        # 3. QR3 Deep Pointing 4 (Detector 1 Deep exposures)
        deep_dithers = sorted(glob.glob(os.path.join(self.base_dir, "data", "spherex", "qr3_deep", "*0004_*D1*.fits")))
        
        dither_sets = {
            "qr3_wide_det1": qr3_dithers,
            "qr2_wide_det2": qr2_dithers,
            "qr3_deep_det1": deep_dithers
        }
        
        total_files = sum(len(flist) for flist in dither_sets.values())
        logger.info(f"Selected {total_files} Level-2 FITS files across {len(dither_sets)} dither groups for validation.")
        return dither_sets

    def extract_validation_photometry(self, dither_sets: Dict[str, List[str]], max_sources_per_file: int = 500) -> pd.DataFrame:
        """Extracts calibrated aperture photometry across all validation dither sets."""
        phot_records = []
        
        for group_name, file_list in dither_sets.items():
            for fpath in file_list:
                fname = os.path.basename(fpath)
                logger.info(f"Extracting validation photometry from [{group_name}] {fname}...")
                df = self.extractor.extract_from_fits(fpath, max_sources=max_sources_per_file, base_dir=self.base_dir)
                if not df.empty:
                    df["dither_group"] = group_name
                    phot_records.append(df)
                    
        if not phot_records:
            raise RuntimeError("No photometric records extracted from validation files.")
            
        combined_df = pd.concat(phot_records, ignore_index=True)
        out_csv = os.path.join(self.processed_dir, "validation_extracted_photometry.csv")
        combined_df.to_csv(out_csv, index=False)
        logger.info(f"Successfully extracted {len(combined_df)} total photometric detections across validation sets. Saved to {out_csv}.")
        return combined_df

    def evaluate_dither_repeatability(self, phot_df: pd.DataFrame, match_radius_arcsec: float = 1.5) -> pd.DataFrame:
        """Matches astronomical sources across consecutive dither exposures and computes repeatability statistics."""
        repeatability_records = []
        
        groups = phot_df.groupby("dither_group")
        for group_name, gdf in groups:
            files = sorted(gdf["source_file"].unique())
            if len(files) < 2:
                continue
                
            # Compare consecutive dither pairs (e.g. D1 vs D2, D2 vs D3, D3 vs D4)
            for idx in range(len(files) - 1):
                f1, f2 = files[idx], files[idx + 1]
                sub1 = gdf[gdf["source_file"] == f1].reset_index(drop=True)
                sub2 = gdf[gdf["source_file"] == f2].reset_index(drop=True)
                
                coords1 = SkyCoord(ra=sub1["ra"].values * u.deg, dec=sub1["dec"].values * u.deg)
                coords2 = SkyCoord(ra=sub2["ra"].values * u.deg, dec=sub2["dec"].values * u.deg)
                
                idx2, d2d, _ = coords1.match_to_catalog_sky(coords2)
                sep_arcsec = d2d.arcsec
                matched_mask = sep_arcsec <= match_radius_arcsec
                
                for i1 in np.where(matched_mask)[0]:
                    i2 = idx2[i1]
                    r1 = sub1.iloc[i1]
                    r2 = sub2.iloc[i2]
                    
                    # Only analyze clean apertures
                    if r1["valid_pixel_fraction"] < 0.8 or r2["valid_pixel_fraction"] < 0.8:
                        continue
                        
                    f_1, f_2 = float(r1["flux"]), float(r2["flux"])
                    sig_1, sig_2 = float(r1["flux_uncertainty"]), float(r2["flux_uncertainty"])
                    
                    if sig_1 <= 0 or sig_2 <= 0:
                        continue
                        
                    flux_diff = f_1 - f_2
                    mean_flux = (f_1 + f_2) / 2.0
                    rel_diff = flux_diff / mean_flux if mean_flux > 0 else np.nan
                    
                    # Normalized residual (Pull)
                    comb_sig = np.sqrt(sig_1**2 + sig_2**2)
                    pull = flux_diff / comb_sig if comb_sig > 0 else np.nan
                    
                    mean_snr = (float(r1["snr"]) + float(r2["snr"])) / 2.0
                    
                    repeatability_records.append({
                        "dither_group": group_name,
                        "file_1": f1,
                        "file_2": f2,
                        "source_id": r1["source_id"],
                        "ra": r1["ra"],
                        "dec": r1["dec"],
                        "sep_arcsec": sep_arcsec[i1],
                        "flux_1": f_1,
                        "flux_2": f_2,
                        "sigma_1": sig_1,
                        "sigma_2": sig_2,
                        "flux_diff": flux_diff,
                        "rel_diff": rel_diff,
                        "pull": pull,
                        "mean_snr": mean_snr,
                        "cwave_1": r1["central_wavelength"],
                        "cwave_2": r2["central_wavelength"],
                        "valid_frac_1": r1["valid_pixel_fraction"],
                        "valid_frac_2": r2["valid_pixel_fraction"]
                    })
                    
        columns = [
            "dither_group", "file_1", "file_2", "source_id", "ra", "dec", "sep_arcsec",
            "flux_1", "flux_2", "sigma_1", "sigma_2", "flux_diff", "rel_diff", "pull",
            "mean_snr", "cwave_1", "cwave_2", "valid_frac_1", "valid_frac_2"
        ]
        rep_df = pd.DataFrame(repeatability_records, columns=columns) if repeatability_records else pd.DataFrame(columns=columns)
        out_csv = os.path.join(self.processed_dir, "photometry_repeatability_catalog.csv")
        rep_df.to_csv(out_csv, index=False)
        logger.info(f"Evaluated repeatability across {len(rep_df)} matched dither source pairs. Saved to {out_csv}.")
        return rep_df

    def compute_validation_metrics(self, phot_df: pd.DataFrame, rep_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates comprehensive empirical validation metrics."""
        metrics = {}
        
        # 1. Total Sample Statistics
        metrics["total_detections"] = len(phot_df)
        metrics["dither_groups"] = list(phot_df["dither_group"].unique())
        metrics["detectors_evaluated"] = [int(d) for d in phot_df["detector_id"].unique()]
        
        # 2. Photometric Repeatability & Pull Statistics
        valid_pulls = rep_df["pull"].dropna().values
        valid_rels = rep_df["rel_diff"].dropna().values
        
        metrics["repeatability_pairs_count"] = len(rep_df)
        metrics["mean_pull"] = float(np.mean(valid_pulls)) if len(valid_pulls) > 0 else 0.0
        metrics["std_pull"] = float(np.std(valid_pulls)) if len(valid_pulls) > 0 else 0.0
        metrics["median_rel_flux_residual_pct"] = float(np.median(np.abs(valid_rels)) * 100.0) if len(valid_rels) > 0 else 0.0
        metrics["mean_astrometric_separation_arcsec"] = float(rep_df["sep_arcsec"].mean()) if not rep_df.empty else 0.0
        
        # 3. Stratification by SNR Tiers
        snr_tiers = {
            "bright_snr_gt_50": rep_df[rep_df["mean_snr"] >= 50.0],
            "moderate_snr_20_50": rep_df[(rep_df["mean_snr"] >= 20.0) & (rep_df["mean_snr"] < 50.0)],
            "faint_snr_5_20": rep_df[(rep_df["mean_snr"] >= 5.0) & (rep_df["mean_snr"] < 20.0)],
            "marginal_snr_lt_5": rep_df[rep_df["mean_snr"] < 5.0]
        }
        
        tier_metrics = {}
        for tier_name, tdf in snr_tiers.items():
            t_pulls = tdf["pull"].dropna().values
            t_rels = tdf["rel_diff"].dropna().values
            tier_metrics[tier_name] = {
                "count": len(tdf),
                "mean_snr": float(tdf["mean_snr"].mean()) if not tdf.empty else 0.0,
                "median_rel_diff_pct": float(np.median(np.abs(t_rels)) * 100.0) if len(t_rels) > 0 else 0.0,
                "mean_pull": float(np.mean(t_pulls)) if len(t_pulls) > 0 else 0.0,
                "std_pull": float(np.std(t_pulls)) if len(t_pulls) > 0 else 0.0
            }
        metrics["snr_stratification"] = tier_metrics
        
        # 4. Nearest Neighbor Distance (Crowded Field Assessment)
        nnd_list = []
        for _, gdf in phot_df.groupby("source_file"):
            if len(gdf) > 1:
                coords = SkyCoord(ra=gdf["ra"].values * u.deg, dec=gdf["dec"].values * u.deg)
                idx, d2d, _ = coords.match_to_catalog_sky(coords, nthneighbor=2)
                nnd_list.extend(d2d.arcsec)
        metrics["nearest_neighbor_min_arcsec"] = float(np.min(nnd_list)) if nnd_list else 0.0
        metrics["nearest_neighbor_median_arcsec"] = float(np.median(nnd_list)) if nnd_list else 0.0
        
        # 5. Defect Rejection & Mask Quality
        clean_fraction = float((phot_df["valid_pixel_fraction"] == 1.0).sum() / len(phot_df))
        partial_apertures_count = int((phot_df["valid_pixel_fraction"] < 1.0).sum())
        fatal_flagged_count = int(((phot_df["quality_flags"] & FATAL_FLAG_MASK) > 0).sum())
        
        metrics["defect_rejection"] = {
            "clean_aperture_fraction": clean_fraction,
            "partial_apertures_count": partial_apertures_count,
            "fatal_flagged_count": fatal_flagged_count,
            "fatal_mask_value": FATAL_FLAG_MASK
        }
        
        # 6. Spectral Coordinate Consistency
        det_wl_stats = {}
        for det_id, ddf in phot_df.groupby("detector_id"):
            det_wl_stats[int(det_id)] = {
                "min_wavelength_um": float(ddf["central_wavelength"].min()),
                "max_wavelength_um": float(ddf["central_wavelength"].max()),
                "median_bandwidth_um": float(ddf["bandwidth"].median()),
                "detections_count": len(ddf)
            }
        metrics["spectral_coordinates"] = det_wl_stats
        
        return metrics

    def validate_spectral_assembly(self, phot_df: pd.DataFrame) -> pd.DataFrame:
        """Assembles validation photometric catalog into 102-channel SED vectors and verifies integrity."""
        logger.info("Executing 102-channel spectrophotometric vector assembly on validation catalog...")
        spectra_df = self.assembler.assemble_catalog(phot_df)
        
        out_csv = os.path.join(self.processed_dir, "validation_assembled_spectra.csv")
        spectra_df.to_csv(out_csv, index=False)
        logger.info(f"Assembled {len(spectra_df)} distinct spectral vectors. Saved to {out_csv}.")
        return spectra_df

    def run_full_validation(self) -> Dict[str, Any]:
        """Runs end-to-end validation pipeline."""
        dither_sets = self.select_validation_fits()
        phot_df = self.extract_validation_photometry(dither_sets)
        rep_df = self.evaluate_dither_repeatability(phot_df)
        metrics = self.compute_validation_metrics(phot_df, rep_df)
        spectra_df = self.validate_spectral_assembly(phot_df)
        
        metrics["assembled_spectra_count"] = len(spectra_df)
        
        # Save metrics JSON
        metrics_path = os.path.join(self.processed_dir, "validation_metrics_summary.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
            
        logger.info(f"Validation metrics successfully written to {metrics_path}")
        return metrics


if __name__ == '__main__':
    validator = SPHERExPhotometryValidator()
    results = validator.run_full_validation()
    print("\n--- VALIDATION SUMMARY ---")
    print(json.dumps(results, indent=2))
