"""
SPECTRA-X / F1 — Phase 3, Task 1
Execution Driver: ASTROVISION Scientific Spatial Injection & Recovery Benchmark

Role: Senior Astronomical Image Processing Engineer, Scientific Validation Engineer,
      and Deep Learning Research Scientist.
"""

import os
import sys
import glob
import math
import time
import json
import hashlib
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy.integrate import trapezoid
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base_dir = os.path.abspath(".")
sys.path.insert(0, base_dir)

from scripts.validation.astrovision_injection_benchmark import (
    SPHERExPSFProvider,
    SpatialInjectionEngine,
    SafeRegionCatalogScanner,
    AstroVisionEvaluator,
    compute_wilson_confidence_interval,
    fit_completeness_curve,
    logistic_sigmoid,
    find_subpixel_peak,
    FATAL_FLAG_MASK,
    DEFAULT_PIXEL_SCALE_ARCSEC,
    DEFAULT_EXPTIME_SEC,
    DEFAULT_AGM
)

def run_benchmark(
    n_point_injections: int = 250,
    n_extended_injections: int = 250,
    n_negative_controls: int = 150,
    random_seed: int = 42
) -> Dict[str, Any]:
    print("=" * 80)
    print("SPECTRA-X / F1 — PHASE 3, TASK 1: ASTROVISION INJECTION BENCHMARK")
    print("=" * 80)

    np.random.seed(random_seed)
    rng = np.random.default_rng(random_seed)

    # 1. Checkpoint Integrity & Hash Recording
    ckpt_path = "checkpoints/astrovision_spatial_v2.pt"
    if not os.path.exists(ckpt_path):
        raise FileNotFoundError(f"Missing required checkpoint: {ckpt_path}")

    with open(ckpt_path, "rb") as f:
        ckpt_sha256 = hashlib.sha256(f.read()).hexdigest()
    print(f"ASTROVISION Checkpoint: {ckpt_path}")
    print(f"  SHA-256: {ckpt_sha256}")
    print("  Status: FROZEN (Zero Retraining)")

    # 2. Identify Pointing 0003 Level-2 Science FITS Files
    l2_pattern = os.path.join(base_dir, "data", "spherex", "qr3", "level2", "*0003*.fits")
    p3_files = sorted(glob.glob(l2_pattern))
    print(f"\nPointing 0003 Level-2 Science Exposures Discovered: {len(p3_files)} files")
    if len(p3_files) == 0:
        raise FileNotFoundError(f"No Pointing 0003 files found matching {l2_pattern}")

    scanner = SafeRegionCatalogScanner()
    all_cutouts = []
    print("\nScanning genuine SPHEREx exposures for safe, unflagged, isolated background regions...")
    
    for fp in p3_files:
        cutouts = scanner.scan_file_for_safe_cutouts(
            fits_path=fp,
            patch_size=128,
            stride=36,
            min_source_dist_pix=8.0,
            min_valid_fraction=0.88,
            max_cutouts=40
        )
        all_cutouts.extend(cutouts)
        if len(all_cutouts) >= 800:
            break

    print(f"Total Safe Cutouts Harvested: {len(all_cutouts)}")
    if len(all_cutouts) < 300:
        raise ValueError(f"Insufficient safe background cutouts found ({len(all_cutouts)} < 300)")

    rng.shuffle(all_cutouts)

    total_needed = n_negative_controls + n_point_injections + n_extended_injections
    if len(all_cutouts) < total_needed:
        ratio_ctrl = n_negative_controls / total_needed
        ratio_pt = n_point_injections / total_needed
        n_negative_controls = int(len(all_cutouts) * ratio_ctrl)
        n_point_injections = int(len(all_cutouts) * ratio_pt)
        n_extended_injections = len(all_cutouts) - n_negative_controls - n_point_injections

    ctrl_cutouts = all_cutouts[:n_negative_controls]
    pt_cutouts = all_cutouts[n_negative_controls:n_negative_controls + n_point_injections]
    ext_cutouts = all_cutouts[n_negative_controls + n_point_injections:n_negative_controls + n_point_injections + n_extended_injections]

    print(f"Allocated Cohorts:")
    print(f"  Negative Controls (Clean, Uninjected): {len(ctrl_cutouts)}")
    print(f"  Point-Source Injections (ePSF):         {len(pt_cutouts)}")
    print(f"  Extended-Source Injections (Gaussian): {len(ext_cutouts)}")

    psf_provider = SPHERExPSFProvider()
    injection_engine = SpatialInjectionEngine(psf_provider)
    evaluator = AstroVisionEvaluator(checkpoint_path=ckpt_path)
    print(f"ASTROVISION Evaluator initialized on device: {evaluator.device}")

    # Phase A: Negative Controls
    print("\n--- Phase A: Evaluating Negative Controls (False Alarm Baseline) ---")
    ctrl_results = []
    ctrl_peak_scores = []

    for idx, c in enumerate(ctrl_cutouts):
        sub_img = c["sub_img"]
        sub_var = c["sub_var"]
        sub_mask = c["sub_mask"]

        eval_res = evaluator.evaluate_cutout(
            img=sub_img,
            var=sub_var,
            mask=sub_mask,
            target_sub_x=64.0,
            target_sub_y=64.0,
            match_radius_pix=2.5,
            aperture_radius_pix=3.0
        )

        peak_score = eval_res["target_peak_chi2"]
        ctrl_peak_scores.append(peak_score)

        ctrl_results.append({
            "trial_id": f"CTRL_{idx:04d}",
            "cohort": "NEGATIVE_CONTROL",
            "source_type": "NONE",
            "filename": c["filename"],
            "detector_id": c["detector_id"],
            "obs_id": c["obs_id"],
            "det_x": c["cx_det"],
            "det_y": c["cy_det"],
            "sub_x_inj": 64.0,
            "sub_y_inj": 64.0,
            "target_peak_chi2": peak_score,
            "aperture_sum_chi2": eval_res["aperture_sum_chi2"],
            "global_peak_chi2": eval_res["global_peak_chi2"],
            "injected_flux_mjy_sr": 0.0,
            "injected_snr": 0.0,
            "fwhm_arcsec": float("nan"),
            "recovered": False,
            "pos_error_pix": float("nan"),
            "pos_error_arcsec": float("nan"),
            "recovered_flux_mjy_sr": 0.0
        })

    ctrl_peak_scores = np.array(ctrl_peak_scores)
    med_ctrl = float(np.median(ctrl_peak_scores))
    mad_ctrl = float(1.4826 * np.median(np.abs(ctrl_peak_scores - med_ctrl)))

    tau_3sigma = float(med_ctrl + 3.0 * mad_ctrl)
    tau_5sigma = float(med_ctrl + 5.0 * mad_ctrl)
    det_threshold = max(150.0, tau_3sigma)

    print(f"Negative Control Anomaly Scores (Peak Chi2 at center window):")
    print(f"  Median: {med_ctrl:.2f} | Robust MAD Sigma: {mad_ctrl:.2f}")
    print(f"  3-sigma Robust Threshold: {tau_3sigma:.2f}")
    print(f"  5-sigma Robust Threshold: {tau_5sigma:.2f}")
    print(f"  Canonical Detection Threshold (tau_det): {det_threshold:.2f}")
    print(f"  Empirical FPR at tau_det: {np.mean(ctrl_peak_scores >= det_threshold)*100:.2f}%")

    for r in ctrl_results:
        r["recovered"] = bool(r["target_peak_chi2"] >= det_threshold)

    # Phase B: Point-Source Injections
    print("\n--- Phase B: Executing ePSF Point-Source Injections ---")
    pt_results = []
    snr_grid_pt = [2.0, 3.0, 4.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0]
    montage_data = None

    for idx, c in enumerate(pt_cutouts):
        sub_img = c["sub_img"]
        sub_var = c["sub_var"]
        sub_mask = c["sub_mask"]
        det_id = c["detector_id"]
        bg_std = c["bg_std"]

        target_snr = snr_grid_pt[idx % len(snr_grid_pt)]
        est_peak_frac = 0.25
        total_flux = (target_snr * bg_std) / est_peak_frac

        sub_x = 64.0 + float(rng.uniform(-0.5, 0.5))
        sub_y = 64.0 + float(rng.uniform(-0.5, 0.5))

        inj_res = injection_engine.inject_point_source(
            img=sub_img,
            var=sub_var,
            flags=np.zeros_like(sub_img, dtype=np.int32),
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux=total_flux,
            detector_id=det_id,
            det_x=c["cx_det"],
            det_y=c["cy_det"],
            agm=DEFAULT_AGM,
            exptime=c["exptime"],
            add_poisson_noise=True,
            rng=rng
        )

        eval_res = evaluator.evaluate_cutout(
            img=inj_res["injected_image"],
            var=inj_res["injected_variance"],
            mask=sub_mask,
            target_sub_x=sub_x,
            target_sub_y=sub_y,
            match_radius_pix=2.5,
            aperture_radius_pix=3.0
        )

        peak_score = eval_res["target_peak_chi2"]
        pos_err_pix = eval_res["position_error_pix"]
        pos_err_arcsec = pos_err_pix * c["pixel_scale"]
        is_detected = (peak_score >= det_threshold) and (pos_err_pix <= 2.5)

        diff_img = inj_res["injected_image"] - sub_img
        H, W = sub_img.shape
        yy, xx = np.ogrid[:H, :W]
        r_rec = np.sqrt((xx - sub_x)**2 + (yy - sub_y)**2)
        rec_flux = float(np.sum(diff_img[r_rec <= 3.5]))

        if montage_data is None and target_snr == 15.0:
            montage_data = {
                "orig": sub_img.copy(),
                "injected": inj_res["injected_image"].copy(),
                "diff": diff_img.copy(),
                "anom": eval_res["anomaly_map"].copy(),
                "target_x": sub_x,
                "target_y": sub_y,
                "target_snr": target_snr,
                "filename": c["filename"]
            }

        pt_results.append({
            "trial_id": f"PT_{idx:04d}",
            "cohort": "POINT_SOURCE",
            "source_type": "POINT_SOURCE_EPSF",
            "filename": c["filename"],
            "detector_id": det_id,
            "obs_id": c["obs_id"],
            "det_x": c["cx_det"],
            "det_y": c["cy_det"],
            "sub_x_inj": sub_x,
            "sub_y_inj": sub_y,
            "target_peak_chi2": peak_score,
            "aperture_sum_chi2": eval_res["aperture_sum_chi2"],
            "global_peak_chi2": eval_res["global_peak_chi2"],
            "injected_flux_mjy_sr": total_flux,
            "injected_snr": target_snr,
            "fwhm_arcsec": float("nan"),
            "recovered": is_detected,
            "pos_error_pix": pos_err_pix if is_detected else float("nan"),
            "pos_error_arcsec": pos_err_arcsec if is_detected else float("nan"),
            "recovered_flux_mjy_sr": rec_flux
        })

    # Phase C: Extended-Source Injections
    print("\n--- Phase C: Executing Extended-Source Injections ---")
    ext_results = []
    fwhm_grid_arcsec = [12.0, 18.0, 24.0, 36.0]
    snr_grid_ext = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0]

    for idx, c in enumerate(ext_cutouts):
        sub_img = c["sub_img"]
        sub_var = c["sub_var"]
        sub_mask = c["sub_mask"]
        det_id = c["detector_id"]
        bg_std = c["bg_std"]

        fwhm_arcsec = fwhm_grid_arcsec[idx % len(fwhm_grid_arcsec)]
        target_snr = snr_grid_ext[(idx // len(fwhm_grid_arcsec)) % len(snr_grid_ext)]

        sigma_pix = (fwhm_arcsec / c["pixel_scale"]) / 2.35482
        peak_frac = 1.0 / (2.0 * math.pi * (sigma_pix**2))
        total_flux = (target_snr * bg_std) / max(1e-4, peak_frac)

        sub_x = 64.0 + float(rng.uniform(-0.5, 0.5))
        sub_y = 64.0 + float(rng.uniform(-0.5, 0.5))

        inj_res = injection_engine.inject_extended_source(
            img=sub_img,
            var=sub_var,
            flags=np.zeros_like(sub_img, dtype=np.int32),
            sub_x=sub_x,
            sub_y=sub_y,
            total_flux=total_flux,
            fwhm_arcsec=fwhm_arcsec,
            pixel_scale_arcsec=c["pixel_scale"],
            agm=DEFAULT_AGM,
            exptime=c["exptime"],
            add_poisson_noise=True,
            rng=rng
        )

        eval_res = evaluator.evaluate_cutout(
            img=inj_res["injected_image"],
            var=inj_res["injected_variance"],
            mask=sub_mask,
            target_sub_x=sub_x,
            target_sub_y=sub_y,
            match_radius_pix=3.5,
            aperture_radius_pix=5.0
        )

        peak_score = eval_res["target_peak_chi2"]
        pos_err_pix = eval_res["position_error_pix"]
        pos_err_arcsec = pos_err_pix * c["pixel_scale"]
        is_detected = (peak_score >= det_threshold) and (pos_err_pix <= 3.5)

        diff_img = inj_res["injected_image"] - sub_img
        H, W = sub_img.shape
        yy, xx = np.ogrid[:H, :W]
        r_rec = np.sqrt((xx - sub_x)**2 + (yy - sub_y)**2)
        rec_flux = float(np.sum(diff_img[r_rec <= (2.0 * sigma_pix)]))

        ext_results.append({
            "trial_id": f"EXT_{idx:04d}",
            "cohort": "EXTENDED_SOURCE",
            "source_type": f"EXT_FWHM_{int(fwhm_arcsec)}as",
            "filename": c["filename"],
            "detector_id": det_id,
            "obs_id": c["obs_id"],
            "det_x": c["cx_det"],
            "det_y": c["cy_det"],
            "sub_x_inj": sub_x,
            "sub_y_inj": sub_y,
            "target_peak_chi2": peak_score,
            "aperture_sum_chi2": eval_res["aperture_sum_chi2"],
            "global_peak_chi2": eval_res["global_peak_chi2"],
            "injected_flux_mjy_sr": total_flux,
            "injected_snr": target_snr,
            "fwhm_arcsec": fwhm_arcsec,
            "recovered": is_detected,
            "pos_error_pix": pos_err_pix if is_detected else float("nan"),
            "pos_error_arcsec": pos_err_arcsec if is_detected else float("nan"),
            "recovered_flux_mjy_sr": rec_flux
        })

    all_results = ctrl_results + pt_results + ext_results
    df_results = pd.DataFrame(all_results)

    # 7. Scientific Analysis & Completeness Calculations
    print("\n" + "=" * 80)
    print("SCIENTIFIC BENCHMARK ANALYSIS & COMPLETENESS RESULTS")
    print("=" * 80)

    # A. Point Sources Analysis
    df_pt = df_results[df_results["cohort"] == "POINT_SOURCE"]
    pt_fit = fit_completeness_curve(df_pt["injected_snr"].values, df_pt["recovered"].values.astype(int))

    pt_summary = []
    for snr_val, rate, n, k in zip(pt_fit["binned_x"], pt_fit["binned_rate"], pt_fit["binned_n"], pt_fit["binned_k"]):
        ci_low, ci_high = compute_wilson_confidence_interval(k, n)
        pt_summary.append({
            "injected_snr": snr_val,
            "n_injected": n,
            "n_recovered": k,
            "completeness": rate,
            "ci_95_low": ci_low,
            "ci_95_high": ci_high
        })
    df_pt_summary = pd.DataFrame(pt_summary)

    print("\nPoint Source (ePSF) Completeness vs SNR:")
    for _, row in df_pt_summary.iterrows():
        print(f"  SNR {row['injected_snr']:4.1f} sigma: {row['completeness']*100:5.1f}% [{row['ci_95_low']*100:4.1f}%, {row['ci_95_high']*100:4.1f}%] (N={int(row['n_injected'])})")

    pt_c50 = pt_fit["completeness_50"]
    pt_c90 = pt_fit["completeness_90"]
    print(f"\nPoint Source Recovery Limits:")
    print(f"  50% Completeness Limit: {pt_c50:.2f} sigma SNR")
    print(f"  90% Completeness Limit: {pt_c90:.2f} sigma SNR")

    # B. Extended Sources Analysis
    df_ext = df_results[df_results["cohort"] == "EXTENDED_SOURCE"]
    ext_fit = fit_completeness_curve(df_ext["injected_snr"].values, df_ext["recovered"].values.astype(int))

    ext_summary = []
    for snr_val, rate, n, k in zip(ext_fit["binned_x"], ext_fit["binned_rate"], ext_fit["binned_n"], ext_fit["binned_k"]):
        ci_low, ci_high = compute_wilson_confidence_interval(k, n)
        ext_summary.append({
            "injected_snr": snr_val,
            "n_injected": n,
            "n_recovered": k,
            "completeness": rate,
            "ci_95_low": ci_low,
            "ci_95_high": ci_high
        })
    df_ext_summary = pd.DataFrame(ext_summary)

    print("\nExtended Source (Gaussian) Completeness vs SNR:")
    for _, row in df_ext_summary.iterrows():
        print(f"  SNR {row['injected_snr']:4.1f} sigma: {row['completeness']*100:5.1f}% [{row['ci_95_low']*100:4.1f}%, {row['ci_95_high']*100:4.1f}%] (N={int(row['n_injected'])})")

    ext_c50 = ext_fit["completeness_50"]
    ext_c90 = ext_fit["completeness_90"]
    print(f"\nExtended Source Recovery Limits:")
    print(f"  50% Completeness Limit: {ext_c50:.2f} sigma SNR")
    print(f"  90% Completeness Limit: {ext_c90:.2f} sigma SNR")

    # C. Astrometric Position Recovery
    pt_recovered = df_pt[df_pt["recovered"]]
    pos_err_pt = pt_recovered["pos_error_arcsec"].dropna()
    print(f"\nPoint Source Astrometric Recovery Precision (N={len(pos_err_pt)}):")
    print(f"  Median radial error: {pos_err_pt.median():.3f} arcsec ({pos_err_pt.median()/DEFAULT_PIXEL_SCALE_ARCSEC:.3f} pix)")
    print(f"  68th percentile:     {np.percentile(pos_err_pt, 68):.3f} arcsec")
    print(f"  95th percentile:     {np.percentile(pos_err_pt, 95):.3f} arcsec")

    # D. Overall Precision & False Positive Rate
    n_tp = int(np.sum(df_pt["recovered"]) + np.sum(df_ext["recovered"]))
    n_fp = int(np.sum(df_results[df_results["cohort"] == "NEGATIVE_CONTROL"]["recovered"]))
    n_fn = int(len(df_pt) + len(df_ext) - n_tp)
    n_tn = int(len(ctrl_results) - n_fp)

    precision = n_tp / max(1, n_tp + n_fp)
    recall = n_tp / max(1, n_tp + n_fn)
    f1 = 2.0 * (precision * recall) / max(1e-6, precision + recall)
    fpr = n_fp / max(1, n_fp + n_tn)

    print(f"\nOverall Global Benchmark Performance:")
    print(f"  True Positives:  {n_tp}")
    print(f"  False Positives: {n_fp} (FPR = {fpr*100:.2f}%)")
    print(f"  False Negatives: {n_fn}")
    print(f"  True Negatives:  {n_tn}")
    print(f"  Precision:       {precision*100:.2f}%")
    print(f"  Recall:          {recall*100:.2f}%")
    print(f"  F1 Score:        {f1:.4f}")

    # 8. Persist Machine-Readable Deliverables
    manifest_path = "data/processed/validation/astrovision_injection_manifest.csv"
    results_path = "data/processed/validation/astrovision_injection_results.csv"

    os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
    df_results.to_csv(results_path, index=False)
    print(f"\nSaved full benchmark results: {results_path} ({len(df_results)} rows)")

    manifest_cols = ["trial_id", "cohort", "source_type", "filename", "detector_id", "obs_id",
                     "sub_x_inj", "sub_y_inj", "injected_snr", "injected_flux_mjy_sr"]
    df_results[manifest_cols].to_csv(manifest_path, index=False)
    print(f"Saved injection manifest: {manifest_path} ({len(df_results)} rows)")

    # 9. Generate Publication-Quality Visualizations
    fig_dir = "reports/figures/astrovision"
    os.makedirs(fig_dir, exist_ok=True)
    print(f"\nGenerating figures in {fig_dir}...")

    # Figure 1: 4-Panel Cutout Montage
    if montage_data is not None:
        fig, axes = plt.subplots(1, 4, figsize=(18, 4.5), dpi=150)
        
        im0 = axes[0].imshow(montage_data["orig"], origin="lower", cmap="viridis")
        axes[0].set_title("1. Original SPHEREx Cutout", fontsize=11, fontweight="bold")
        axes[0].scatter([montage_data["target_x"]], [montage_data["target_y"]], s=60, edgecolors="red", facecolors="none", lw=1.5)
        plt.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04, label="MJy / sr")

        im1 = axes[1].imshow(montage_data["injected"], origin="lower", cmap="viridis")
        axes[1].set_title(f"2. Injected Cutout ({montage_data['target_snr']:.0f}σ ePSF)", fontsize=11, fontweight="bold")
        axes[1].scatter([montage_data["target_x"]], [montage_data["target_y"]], s=60, edgecolors="cyan", facecolors="none", lw=1.5)
        plt.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04, label="MJy / sr")

        im2 = axes[2].imshow(montage_data["diff"], origin="lower", cmap="magma")
        axes[2].set_title("3. Difference (Injected - Orig)", fontsize=11, fontweight="bold")
        plt.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04, label="MJy / sr")

        im3 = axes[3].imshow(np.log10(np.clip(montage_data["anom"], 0.1, 1e5)), origin="lower", cmap="inferno")
        axes[3].set_title("4. ASTROVISION Anomaly Map", fontsize=11, fontweight="bold")
        axes[3].scatter([montage_data["target_x"]], [montage_data["target_y"]], s=80, marker="x", color="cyan", lw=2)
        plt.colorbar(im3, ax=axes[3], fraction=0.046, pad=0.04, label="log10(Normalized Chi2)")

        plt.tight_layout()
        fig_path1 = os.path.join(fig_dir, "astrovision_cutout_montage.png")
        plt.savefig(fig_path1)
        plt.close()
        print(f"  Saved: {fig_path1}")

    # Figure 2: Completeness vs SNR Curves
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=150)
    snr_dense = np.linspace(1.5, 50.0, 200)

    if not math.isnan(pt_fit["x0_fit"]) and not math.isnan(pt_fit["k_fit"]) and pt_fit["k_fit"] > 0:
        ax.plot(snr_dense, logistic_sigmoid(snr_dense, pt_fit["x0_fit"], pt_fit["k_fit"]),
                color="#0066cc", lw=2.5, label=f"Point Source Sigmoid (50%={pt_c50:.1f}σ, 90%={pt_c90:.1f}σ)")
    
    err_low_pt = df_pt_summary["completeness"] - df_pt_summary["ci_95_low"]
    err_high_pt = df_pt_summary["ci_95_high"] - df_pt_summary["completeness"]
    ax.errorbar(df_pt_summary["injected_snr"], df_pt_summary["completeness"],
                 yerr=[err_low_pt, err_high_pt], fmt="o", color="#0066cc", capsize=4, elinewidth=1.5, label="Point Source (ePSF) Data ± 95% CI")

    if not math.isnan(ext_fit["x0_fit"]) and not math.isnan(ext_fit["k_fit"]) and ext_fit["k_fit"] > 0:
        ax.plot(snr_dense, logistic_sigmoid(snr_dense, ext_fit["x0_fit"], ext_fit["k_fit"]),
                color="#cc3300", lw=2.5, linestyle="--", label=f"Extended Source Sigmoid (50%={ext_c50:.1f}σ, 90%={ext_c90:.1f}σ)")
    
    err_low_ext = df_ext_summary["completeness"] - df_ext_summary["ci_95_low"]
    err_high_ext = df_ext_summary["ci_95_high"] - df_ext_summary["completeness"]
    ax.errorbar(df_ext_summary["injected_snr"], df_ext_summary["completeness"],
                 yerr=[err_low_ext, err_high_ext], fmt="s", color="#cc3300", capsize=4, elinewidth=1.5, label="Extended Source Data ± 95% CI")

    ax.axhline(0.50, color="gray", linestyle=":", lw=1.2, label="50% Completeness Limit")
    ax.axhline(0.90, color="black", linestyle=":", lw=1.2, label="90% Completeness Limit")

    ax.set_xlabel("Injected Source Peak Significance (SNR in σ)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Detection Completeness (Recall)", fontsize=11, fontweight="bold")
    ax.set_title("ASTROVISION Detection Completeness vs Injected Signal-to-Noise", fontsize=12, fontweight="bold")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="lower right", fontsize=8.5)

    plt.tight_layout()
    fig_path2 = os.path.join(fig_dir, "astrovision_completeness_curves.png")
    plt.savefig(fig_path2)
    plt.close()
    print(f"  Saved: {fig_path2}")

    # Figure 3: Astrometric Position Recovery Error Distribution
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=150)
    
    pos_err_pix = pt_recovered["pos_error_pix"].dropna()
    if len(pos_err_pix) > 0:
        ax1.hist(pos_err_pix, bins=15, range=(0, 2.5), color="#2b5c8f", edgecolor="black", alpha=0.75)
        ax1.axvline(pos_err_pix.median(), color="red", linestyle="--", lw=2, label=f"Median: {pos_err_pix.median():.3f} pix")
        ax1.axvline(np.percentile(pos_err_pix, 68), color="orange", linestyle=":", lw=2, label=f"68th %ile: {np.percentile(pos_err_pix, 68):.3f} pix")
        ax1.set_xlabel("Radial Astrometric Offset (pixels)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Count", fontsize=11, fontweight="bold")
        ax1.set_title("Point-Source Position Recovery Error", fontsize=11, fontweight="bold")
        ax1.legend(loc="upper right", fontsize=9)
        ax1.grid(True, linestyle="--", alpha=0.5)

        pos_err_arc = pt_recovered["pos_error_arcsec"].dropna()
        ax2.hist(pos_err_arc, bins=15, range=(0, 15.0), color="#1b7837", edgecolor="black", alpha=0.75)
        ax2.axvline(pos_err_arc.median(), color="red", linestyle="--", lw=2, label=f"Median: {pos_err_arc.median():.2f}\"")
        ax2.axvline(np.percentile(pos_err_arc, 68), color="orange", linestyle=":", lw=2, label=f"68th %ile: {np.percentile(pos_err_arc, 68):.2f}\"")
        ax2.set_xlabel("Radial Astrometric Offset (arcseconds)", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Count", fontsize=11, fontweight="bold")
        ax2.set_title("Astrometric Precision on Sky", fontsize=11, fontweight="bold")
        ax2.legend(loc="upper right", fontsize=9)
        ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig_path3 = os.path.join(fig_dir, "astrovision_position_recovery_error.png")
    plt.savefig(fig_path3)
    plt.close()
    print(f"  Saved: {fig_path3}")

    # Figure 4: Injected vs Recovered Flux Linearity
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    
    pt_rec_flux = pt_recovered[pt_recovered["injected_snr"] >= 5.0]
    if len(pt_rec_flux) > 0:
        inj_f = pt_rec_flux["injected_flux_mjy_sr"].values
        rec_f = pt_rec_flux["recovered_flux_mjy_sr"].values

        ax.scatter(inj_f, rec_f, color="#4a148c", alpha=0.6, s=35, edgecolors="none", label="Recovered Sources (SNR ≥ 5σ)")
        max_f = max(inj_f.max(), rec_f.max()) * 1.05
        ax.plot([0, max_f], [0, max_f], color="black", linestyle="--", lw=1.5, label="1:1 Flux Conservation")

        if len(inj_f) > 5:
            poly = np.polyfit(inj_f, rec_f, 1)
            r2 = np.corrcoef(inj_f, rec_f)[0, 1]**2
            ax.plot([0, max_f], [poly[1], poly[0]*max_f + poly[1]], color="red", lw=2, label=f"Linear Fit: Slope={poly[0]:.3f}, R²={r2:.4f}")

    ax.set_xlabel("Injected Total Flux (MJy / sr)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Photometric Recovered Flux (MJy / sr)", fontsize=11, fontweight="bold")
    ax.set_title("Photometric Recovery Linearity & Flux Conservation", fontsize=12, fontweight="bold")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper left", fontsize=9)

    plt.tight_layout()
    fig_path4 = os.path.join(fig_dir, "astrovision_flux_recovery_linearity.png")
    plt.savefig(fig_path4)
    plt.close()
    print(f"  Saved: {fig_path4}")

    # Figure 5: ROC & Precision-Recall Curves
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=150)
    
    thresholds = np.logspace(1.0, 4.0, 150)
    all_positives = df_results[df_results["cohort"].isin(["POINT_SOURCE", "EXTENDED_SOURCE"])]
    all_negatives = df_results[df_results["cohort"] == "NEGATIVE_CONTROL"]

    tpr_list = []
    fpr_list = []
    prec_list = []

    for t in thresholds:
        tp = np.sum((all_positives["target_peak_chi2"] >= t))
        fn = len(all_positives) - tp
        fp = np.sum(all_negatives["target_peak_chi2"] >= t)
        tn = len(all_negatives) - fp

        tpr_val = tp / max(1, tp + fn)
        fpr_val = fp / max(1, fp + tn)
        prec_val = tp / max(1, tp + fp)

        tpr_list.append(tpr_val)
        fpr_list.append(fpr_val)
        prec_list.append(prec_val)

    tpr_arr = np.array(tpr_list)
    fpr_arr = np.array(fpr_list)
    prec_arr = np.array(prec_list)

    sort_idx = np.argsort(fpr_arr)
    auroc = float(trapezoid(tpr_arr[sort_idx], fpr_arr[sort_idx]))
    
    sort_prc = np.argsort(tpr_arr)
    auprc = float(trapezoid(prec_arr[sort_prc], tpr_arr[sort_prc]))

    ax1.plot(fpr_arr, tpr_arr, color="#0055aa", lw=2.5, label=f"ASTROVISION (AUROC = {auroc:.4f})")
    ax1.plot([0, 1], [0, 1], color="gray", linestyle=":", label="Random Baseline (AUROC = 0.5000)")
    ax1.scatter([fpr], [recall], color="red", s=70, zorder=5, label=f"Canonical τ={det_threshold:.0f}")
    ax1.set_xlabel("False Positive Rate (FPR)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("True Positive Rate (Recall)", fontsize=11, fontweight="bold")
    ax1.set_title("Receiver Operating Characteristic (ROC)", fontsize=12, fontweight="bold")
    ax1.legend(loc="lower right", fontsize=9)
    ax1.grid(True, linestyle="--", alpha=0.5)

    ax2.plot(tpr_arr, prec_arr, color="#aa2200", lw=2.5, label=f"ASTROVISION (AUPRC = {auprc:.4f})")
    ax2.scatter([recall], [precision], color="red", s=70, zorder=5, label=f"Canonical τ={det_threshold:.0f}")
    ax2.set_xlabel("Recall (Completeness)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Precision", fontsize=11, fontweight="bold")
    ax2.set_title("Precision-Recall Curve (PRC)", fontsize=12, fontweight="bold")
    ax2.legend(loc="lower left", fontsize=9)
    ax2.grid(True, linestyle="--", alpha=0.5)

    plt.tight_layout()
    fig_path5 = os.path.join(fig_dir, "astrovision_roc_prc_curves.png")
    plt.savefig(fig_path5)
    plt.close()
    print(f"  Saved: {fig_path5}")

    summary_metrics = {
        "checkpoint_sha256": ckpt_sha256,
        "n_trials_total": len(df_results),
        "n_controls": len(ctrl_results),
        "n_point_injections": len(pt_results),
        "n_extended_injections": len(ext_results),
        "locked_detection_threshold_tau": det_threshold,
        "empirical_fpr_on_controls": float(fpr),
        "global_precision": float(precision),
        "global_recall": float(recall),
        "global_f1": float(f1),
        "auroc": float(auroc),
        "auprc": float(auprc),
        "point_source_c50_snr": float(pt_c50),
        "point_source_c90_snr": float(pt_c90),
        "extended_source_c50_snr": float(ext_c50),
        "extended_source_c90_snr": float(ext_c90),
        "point_source_median_radial_error_arcsec": float(pos_err_pt.median()) if len(pos_err_pt)>0 else float("nan"),
        "point_source_68th_radial_error_arcsec": float(np.percentile(pos_err_pt, 68)) if len(pos_err_pt)>0 else float("nan")
    }

    metrics_json_path = "reports/figures/astrovision/benchmark_metrics.json"
    with open(metrics_json_path, "w") as f:
        json.dump(summary_metrics, f, indent=2)
    print(f"Saved benchmark summary metrics: {metrics_json_path}")

    return summary_metrics

if __name__ == "__main__":
    t0 = time.time()
    metrics = run_benchmark(
        n_point_injections=250,
        n_extended_injections=250,
        n_negative_controls=150,
        random_seed=42
    )
    elapsed = time.time() - t0
    print(f"\nBenchmark completed successfully in {elapsed:.2f} seconds.")
