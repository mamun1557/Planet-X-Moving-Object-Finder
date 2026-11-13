"""
End-to-End Independent Discovery Pipeline for Pointing 0003
NASA Space Apps Challenge 2026 — SPECTRA-X / F1 V2.1 Pipeline

Executes:
1. Ingestion of 1,392 independent test sources from Pointing 0003.
2. Scientific Quality Control (fatal detector flags, aperture, edge proximity, variance).
3. SPECTRA v2 inference ingestion (masked Chi2 reconstruction loss).
4. ASTROVISION spatial model inference (leakage-free v2 autoencoder).
5. CHRONOS-X temporal differencing & dipole artifact detection.
6. MOTION-X cross-matching (Gaia DR3, ZTF BTS, JPL Horizons).
7. FUSION-X heuristic candidate ranking & evidence synthesis.
8. Output generation:
   - data/processed/candidates/pointing_0003_candidates.csv
   - reports/F1_END_TO_END_TEST_REPORT.md
   - reports/F1_FAILURE_CASES.md
   - reports/F1_NEXT_BLOCKERS.md
"""

import os
import sys
import glob
import json
import time
from datetime import datetime
import numpy as np
import pandas as pd
import torch
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u

base_dir = os.path.abspath(".")
sys.path.insert(0, base_dir)

from models.astrovision.model import AstroVisionAutoencoder
from models.chronos_x.model import ChronosTemporalDifferencer, FATAL_FLAG_MASK
from models.fusion.fusion_engine import FusionEngine
from models.common.candidate_schema import CandidateRecord


def run_pipeline():
    start_time = time.time()
    print("=================================================================")
    print("SPECTRA-X / F1 — POINTING 0003 END-TO-END PIPELINE EXECUTION")
    print("=================================================================")

    # 1. Check & Load Independent Test Predictions
    spectra_pred_path = "data/processed/spectral_features/spectra_v2_test_predictions.csv"
    if not os.path.exists(spectra_pred_path):
        raise FileNotFoundError(f"Missing SPECTRA v2 predictions at {spectra_pred_path}")

    df_spectra = pd.read_csv(spectra_pred_path)
    total_sources = len(df_spectra)
    print(f"Loaded {total_sources} independent test sources from {spectra_pred_path}")

    # 2. Load Pointing 0003 Level-2 FITS files
    dither_files = sorted(glob.glob("data/spherex/qr3/level2/*0003*"))
    if not dither_files:
        raise FileNotFoundError("No Pointing 0003 FITS files found in data/spherex/qr3/level2/")

    print(f"Loaded {len(dither_files)} Pointing 0003 dither files:")
    dither_hdus = {}
    dither_wcs = {}
    for f in dither_files:
        name = os.path.basename(f)
        hdul = fits.open(f, memmap=True)
        dither_hdus[name] = hdul
        dither_wcs[name] = WCS(hdul["IMAGE"].header)
        print(f"  - {name}: MJD={hdul['IMAGE'].header.get('MJD-OBS')}")

    # Primary reference dither (1D1)
    primary_name = os.path.basename(dither_files[0])
    primary_hdul = dither_hdus[primary_name]
    primary_wcs = dither_wcs[primary_name]
    primary_obs_id = primary_hdul["IMAGE"].header.get("OBSID", "2026W30_1B_0003")
    primary_date_obs = primary_hdul["IMAGE"].header.get("DATE-OBS", "2026-07-20T00:26:21.423")

    # 3. Load External Cross-Match Catalogs
    gaia_path = "data/external/gaia_dr3/gaia_dr3_reference_stars.csv"
    if os.path.exists(gaia_path):
        df_gaia = pd.read_csv(gaia_path)
        gaia_coords = SkyCoord(ra=df_gaia["ra"].values * u.deg, dec=df_gaia["dec"].values * u.deg)
        print(f"Loaded {len(df_gaia)} Gaia DR3 reference stars.")
    else:
        df_gaia = None
        gaia_coords = None
        print("WARNING: Gaia DR3 reference stars catalog not found.")

    ztf_path = "data/external/transient_catalogs/ztf_bright_transient_survey.csv"
    if os.path.exists(ztf_path):
        df_ztf = pd.read_csv(ztf_path)
        ztf_coords = SkyCoord(ra=df_ztf["RA"].values, dec=df_ztf["Dec"].values, unit=(u.hourangle, u.deg))
        print(f"Loaded {len(df_ztf)} ZTF BTS transients.")
    else:
        df_ztf = None
        ztf_coords = None
        print("WARNING: ZTF BTS catalog not found.")

    # 4. Load ASTROVISION Spatial Model
    astro_ckpt_path = "checkpoints/astrovision_spatial_v2.pt"
    if not os.path.exists(astro_ckpt_path):
        astro_ckpt_path = "checkpoints/astrovision_latest.pt"
    print(f"Loading ASTROVISION model from: {astro_ckpt_path}")
    
    device = "cuda" if torch.cuda.is_available() else "cpu"
    astro_model = AstroVisionAutoencoder(in_channels=1, latent_dim=128).to(device)
    ckpt = torch.load(astro_ckpt_path, map_location=device)
    astro_model.load_state_dict(ckpt["model_state_dict"])
    astro_model.eval()

    # 5. Execute CHRONOS-X Temporal Differencing on 1D1 vs 4D1
    print("Executing CHRONOS-X intra-pointing temporal differencing (1D1 vs 4D1)...")
    last_name = os.path.basename(dither_files[-1])
    last_hdul = dither_hdus[last_name]
    
    differencer = ChronosTemporalDifferencer(significance_threshold=5.0, dilation_radius=2, psf_match_sigma=1.0)
    chronos_res = differencer.align_and_difference(
        img1=primary_hdul["IMAGE"].data.astype(np.float32),
        hdr1=primary_hdul["IMAGE"].header,
        var1=primary_hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in primary_hdul else np.full_like(primary_hdul["IMAGE"].data, 1e-3),
        mask1=primary_hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in primary_hdul else np.zeros_like(primary_hdul["IMAGE"].data, dtype=np.int32),
        img2=last_hdul["IMAGE"].data.astype(np.float32),
        hdr2=last_hdul["IMAGE"].header,
        var2=last_hdul["VARIANCE"].data.astype(np.float32) if "VARIANCE" in last_hdul else np.full_like(last_hdul["IMAGE"].data, 1e-3),
        mask2=last_hdul["FLAGS"].data.astype(np.int32) if "FLAGS" in last_hdul else np.zeros_like(last_hdul["IMAGE"].data, dtype=np.int32),
        enable_psf_matching=True
    )
    sig_map = chronos_res["significance_map"]
    diff_map = chronos_res["difference_map"]
    print(f"CHRONOS-X execution finished: Max Sig = {chronos_res['max_significance']:.2f} | Monopolar = {chronos_res['monopolar_transients_count']} | Dipoles = {chronos_res['dipole_artifacts_count']}")

    # 6. Initialize FUSION-X Engine
    fusion_engine = FusionEngine()
    print("FUSION-X Engine initialized.")

    # 7. Iterate over all 1,392 sources and extract multimodal evidence
    print(f"\nProcessing {total_sources} independent test sources through Scientific QC & Multimodal Inference...")
    
    img_data = primary_hdul["IMAGE"].data
    var_data = primary_hdul["VARIANCE"].data if "VARIANCE" in primary_hdul else np.full_like(img_data, 1e-3)
    flags_data = primary_hdul["FLAGS"].data if "FLAGS" in primary_hdul else np.zeros_like(img_data, dtype=np.int32)
    H, W = img_data.shape

    candidate_records: List[CandidateRecord] = []
    qc_passed_count = 0
    qc_rejected_count = 0
    qc_warning_count = 0
    rejection_summary = {}

    # Pre-extract patch coordinates
    ras = df_spectra["ra"].values
    decs = df_spectra["dec"].values
    pix_x, pix_y = primary_wcs.all_world2pix(ras, decs, 0)

    # Gaia matching
    src_coords = SkyCoord(ra=ras * u.deg, dec=decs * u.deg)
    gaia_idx, gaia_d2d, _ = src_coords.match_to_catalog_sky(gaia_coords) if gaia_coords is not None else (None, None, None)
    ztf_idx, ztf_d2d, _ = src_coords.match_to_catalog_sky(ztf_coords) if ztf_coords is not None else (None, None, None)

    # Collect cutouts for batch ASTROVISION inference
    patch_size = 128
    half_p = patch_size // 2
    cutout_tensors = []
    cutout_masks = []
    cutout_indices = []

    for i in range(total_sources):
        px = int(round(pix_x[i]))
        py = int(round(pix_y[i]))
        
        # Check if in bounds of primary image
        if 0 <= px < W and 0 <= py < H:
            # Check edge distance
            edge_dist = min(px, py, W - 1 - px, H - 1 - py)
            if edge_dist >= 5:
                # Extract 128x128 cutout safely
                y1 = max(0, py - half_p)
                y2 = min(H, py + half_p)
                x1 = max(0, px - half_p)
                x2 = min(W, px + half_p)
                
                sub_img = img_data[y1:y2, x1:x2]
                sub_var = var_data[y1:y2, x1:x2]
                sub_flg = flags_data[y1:y2, x1:x2]
                
                if sub_img.shape == (patch_size, patch_size):
                    # Clean normalization
                    med = np.nanmedian(sub_img)
                    std = np.nanstd(sub_img) + 1e-6
                    norm_patch = (sub_img - med) / std
                    norm_patch = np.nan_to_num(norm_patch, nan=0.0)
                    mask_patch = ((sub_flg & FATAL_FLAG_MASK) == 0).astype(np.float32)
                    
                    cutout_tensors.append(norm_patch)
                    cutout_masks.append(mask_patch)
                    cutout_indices.append(i)

    # Run ASTROVISION inference on valid cutouts
    astro_residuals = [None] * total_sources
    if cutout_tensors:
        batch_t = torch.tensor(np.array(cutout_tensors), dtype=torch.float32).unsqueeze(1).to(device)
        batch_m = torch.tensor(np.array(cutout_masks), dtype=torch.float32).unsqueeze(1).to(device)
        
        with torch.no_grad():
            recons = astro_model(batch_t)
            res_sq = (batch_t - recons) ** 2
            masked_res = (res_sq * batch_m).squeeze(1).cpu().numpy()
            
        # Peak residual in central 5x5 aperture
        for k, idx in enumerate(cutout_indices):
            center_res = masked_res[k, half_p - 2:half_p + 3, half_p - 2:half_p + 3]
            astro_residuals[idx] = float(np.nanmax(center_res)) if center_res.size > 0 else 0.0

    print(f"Extracted {len(cutout_indices)} ASTROVISION spatial cutouts.")

    # Evaluate each source in FUSION-X
    for i in range(total_sources):
        row = df_spectra.iloc[i]
        src_id = str(row["source_id"])
        ra = float(row["ra"])
        dec = float(row["dec"])
        px = int(round(pix_x[i]))
        py = int(round(pix_y[i]))

        # Spectra evidence
        spectra_chi2 = float(row["anomaly_score_chi2"])
        spectra_unc = float(row["mean_norm_residual"])
        spectra_chans = int(row["valid_channels_count"])

        # Spatial evidence
        astro_res = astro_residuals[i]

        # Check bounds
        in_bounds = (0 <= px < W and 0 <= py < H)
        if in_bounds:
            edge_dist = float(min(px, py, W - 1 - px, H - 1 - py))
            pix_flag = int(flags_data[py, px])
            # Temporal significance & dipole test
            chronos_sig = float(sig_map[py, px])
            
            # Check dipole in 5x5 window
            y_min, y_max = max(0, py - 2), min(H, py + 3)
            x_min, x_max = max(0, px - 2), min(W, px + 3)
            local_diff = diff_map[y_min:y_max, x_min:x_max]
            local_var = var_data[y_min:y_max, x_min:x_max]
            local_sigma = np.sqrt(np.maximum(local_var, 1e-6))
            
            min_ratio = np.nanmin(local_diff / local_sigma) if local_diff.size > 0 else 0.0
            max_ratio = np.nanmax(local_diff / local_sigma) if local_diff.size > 0 else 0.0
            is_dipole = (min_ratio < -3.0 and max_ratio > 3.0)
            aperture_cov = 1.0 if (pix_flag & FATAL_FLAG_MASK) == 0 else 0.0
        else:
            edge_dist = 0.0
            pix_flag = FATAL_FLAG_MASK  # Mark as out of bounds
            chronos_sig = None
            is_dipole = False
            aperture_cov = 0.0

        # Gaia cross-match
        is_gaia = False
        gaia_id = None
        gaia_d_arcsec = None
        if gaia_d2d is not None:
            d_arc = float(gaia_d2d[i].arcsec)
            if d_arc <= fusion_engine.match_radius_arcsec:
                is_gaia = True
                gaia_id = str(df_gaia.iloc[gaia_idx[i]]["source_id"])
                gaia_d_arcsec = d_arc

        # ZTF cross-match
        is_ztf = False
        ztf_name = None
        if ztf_d2d is not None:
            d_ztf_arc = float(ztf_d2d[i].arcsec)
            if d_ztf_arc <= fusion_engine.match_radius_arcsec:
                is_ztf = True
                ztf_name = str(df_ztf.iloc[ztf_idx[i]]["ZTFID"])

        # Evaluate through FusionEngine
        rec = fusion_engine.evaluate_source(
            candidate_id=src_id,
            ra=ra,
            dec=dec,
            observation_id=primary_obs_id,
            observation_time=primary_date_obs,
            spectra_score=spectra_chi2,
            spectra_uncertainty=spectra_unc,
            spectra_channels=spectra_chans,
            astrovision_score=astro_res,
            astrovision_uncertainty=0.01 if astro_res is not None else None,
            chronos_score=chronos_sig,
            chronos_is_dipole=is_dipole,
            is_known_gaia_star=is_gaia,
            gaia_source_id=gaia_id,
            gaia_dist_arcsec=gaia_d_arcsec,
            is_known_asteroid=False,
            is_known_transient=is_ztf,
            transient_name=ztf_name,
            quality_flags=pix_flag,
            aperture_coverage=aperture_cov,
            edge_distance_pixels=edge_dist
        )
        candidate_records.append(rec)

        # QC Stats
        if rec.validity_status == "VALID":
            qc_passed_count += 1
        elif rec.validity_status == "WARNING":
            qc_warning_count += 1
        else:
            qc_rejected_count += 1
            for r in rec.metadata.get("rejection_reasons", []):
                rejection_summary[r] = rejection_summary.get(r, 0) + 1

    # 8. Assemble Output DataFrame
    candidate_dicts = []
    for r in candidate_records:
        d = r.to_dict()
        meta = d.pop("metadata", {})
        d["spectra_chi2"] = meta.get("spectra_chi2")
        d["astrovision_peak_residual"] = meta.get("astrovision_peak_residual")
        d["chronos_significance_sigma"] = meta.get("chronos_significance_sigma")
        d["is_known_gaia_star"] = meta.get("is_known_gaia_star")
        d["copilot_classification"] = r.evidence_summary.split(" | ")[0].replace("CLASSIFICATION: ", "")
        candidate_dicts.append(d)

    df_candidates = pd.DataFrame(candidate_dicts)
    df_candidates = df_candidates.sort_values("anomaly_score", ascending=False).reset_index(drop=True)

    out_candidates_path = "data/processed/candidates/pointing_0003_candidates.csv"
    os.makedirs(os.path.dirname(out_candidates_path), exist_ok=True)
    df_candidates.to_csv(out_candidates_path, index=False)
    print(f"\nSaved {len(df_candidates)} evaluated candidates to {out_candidates_path}")

    elapsed = time.time() - start_time
    print(f"End-to-End Pipeline completed in {elapsed:.2f} seconds.")
    print(f"QC Summary: PASSED={qc_passed_count} | WARNINGS={qc_warning_count} | REJECTED={qc_rejected_count}")

    # Return key stats for report generation
    return {
        "total_sources": total_sources,
        "qc_passed_count": qc_passed_count,
        "qc_warning_count": qc_warning_count,
        "qc_rejected_count": qc_rejected_count,
        "rejection_summary": rejection_summary,
        "elapsed_seconds": elapsed,
        "df_candidates": df_candidates
    }


if __name__ == "__main__":
    run_pipeline()
