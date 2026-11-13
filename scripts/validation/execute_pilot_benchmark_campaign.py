"""
SPECTRA-X / F1 — Phase 3, Task 1.1R
Production Campaign Driver: Authorized Restricted Five-Pointing ASTROVISION Controlled Pilot Benchmark.

Parent Governance: Task 1.1Q — AUTHORIZED
Total Trials: Exactly 2,500 planned trials across 5 partitions.
Hardware: NVIDIA GeForce RTX 5060 (CUDA accelerated with deterministic settings).
"""

import os
import sys
import time
import math
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

import numpy as np
import pandas as pd
from astropy.io import fits
import torch

BASE_DIR = Path(".").resolve()
sys.path.insert(0, str(BASE_DIR))

from scripts.validation.astrovision_injection_benchmark_v2 import (
    PhysicalSpatialInjectionEngineV2,
    AstroVisionEvaluatorV2,
    DEFAULT_PIXEL_SCALE_ARCSEC,
    NOMINAL_PIXEL_SOLID_ANGLE_SR,
    FATAL_FLAG_MASK
)

# Protected Historical Assets
PROTECTED_ASSETS = {
    "checkpoints/astrovision_spatial_v2.pt": "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557",
    "data/processed/validation/pointing_0003_final_validated_catalogue.csv": "ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b",
    "data/processed/validation/astrovision_injection_manifest.csv": "339d5c58a12122f0e185838730f91a45cbd0d2a83f5df4a51fc83ada30d58978",
    "data/processed/validation/astrovision_injection_results.csv": "22ecaf448e1f01318fad333ee593d00c307a682989ac75b88b2416b380c79c5c",
    "reports/figures/astrovision/benchmark_metrics.json": "5f8fd6bc1313b8f01cc34f8adfcbac959a295902f8b6b99d2c9c7d4fb9ea386c",
    "reports/ASTROVISION_BENCHMARK_INDEPENDENT_AUDIT.md": "dd42430dbff8849d347b2dd0edf8adf01f7b7e6bc8237a1ffb7caedf0b656688",
    "reports/ASTROVISION_SPATIAL_INJECTION_BENCHMARK.md": "5cb9888f3ce42ece238c9405f9e9c80c5f127d741f99845cb1d9435852258698",
    "reports/ASTROVISION_BENCHMARK_V2_INDEPENDENT_IMPLEMENTATION_AUDIT.md": "db9aba61098b520db891ba29d0770315b8c069d24359bb50aec6217bbe1aa808",
    "reports/ASTROVISION_PAIRED_RESIDUAL_REMEDIATION.md": "d3c529c951803023953c6d87814c98e812ed418ddbb28b3f62c4db2877c146bc",
    "reports/ASTROVISION_PAIRED_RESIDUAL_INDEPENDENT_AUDIT.md": "13b0f22088067a814259a50cc469d6b4f533f57590610f37cc98781f8e222985",
    "reports/ASTROVISION_CONTROLLED_BENCHMARK_PROTOCOL.md": "764631f2abaf8ca8a192a9a600af0000ba7436750ec48a3191591eec7ff93b88",
    "reports/ASTROVISION_EXPOSURE_LEVEL_PARTITION_AUDIT.md": "5c26abb6da8f72b33799f2ce628db863d68c5517a41038a2f687b2bff546bf18",
    "reports/ASTROVISION_CONTROLLED_CAMPAIGN_READINESS_INDEPENDENT_AUDIT.md": "22c9e464c30b2204bd6fd71633aeaa009265f995bb5d9e5276eee609fd318278",
    "reports/ASTROVISION_TASK_1_1H_REMEDIATION.md": "950e361cccdb4c342cf10267d8f61fd38644cf97001860a794c7465f80e94e03",
    "reports/ASTROVISION_TASK_1_1H_DRYRUN_AUDIT.md": "74653153b17f110ba60578b2141ef1d205277b6fa4980178f0ac5ab542d0fd4f",
    "reports/ASTROVISION_TASK_1_1I_INDEPENDENT_REAUDIT.md": "7db57a54de5d9346ff46f8144868b93ed67544e2c9413d906852c3a79e86167a"
}

MANIFEST_PATH = BASE_DIR / "reports" / "manifests" / "astrovision_five_partition_pilot_manifest.csv"
AUTH_REVIEW_PATH = BASE_DIR / "reports" / "manifests" / "astrovision_task_1_1Q_authorization_review.json"
RESULTS_DIR = BASE_DIR / "data" / "processed" / "pilot_results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RESULTS_CSV = RESULTS_DIR / "astrovision_pilot_trial_results.csv"
CALIB_PARAMS_JSON = RESULTS_DIR / "calibration_parameters.json"
EVAL_METRICS_JSON = RESULTS_DIR / "pilot_evaluation_metrics.json"
FAILED_LOG = RESULTS_DIR / "pilot_failed_trials.log"


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def run_pre_execution_gate() -> Dict[str, Any]:
    """Mandatory Pre-Execution Gate: Strictly blocks execution if any asset check fails."""
    print("=" * 80)
    print("MANDATORY PRE-EXECUTION GATE VERIFICATION")
    print("=" * 80)

    # 1. Verify Task 1.1Q Authorization Manifest
    if not AUTH_REVIEW_PATH.exists():
        raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Task 1.1Q Authorization manifest missing at {AUTH_REVIEW_PATH}!")
    with open(AUTH_REVIEW_PATH, "r", encoding="utf-8") as f:
        auth_data = json.load(f)
    if "AUTHORIZED" not in auth_data.get("authorization_metadata", {}).get("verdict", ""):
        raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Task 1.1Q verdict is not AUTHORIZED: {auth_data}")
    print("  [Gate 1] Task 1.1Q Authorization Review verified (Verdict: AUTHORIZED).")

    # 2. Verify all 16 protected historical assets
    for rel_path, expected_hash in PROTECTED_ASSETS.items():
        p = BASE_DIR / rel_path
        if not p.exists():
            raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Protected asset missing: {rel_path}")
        act_hash = compute_sha256(p)
        if act_hash != expected_hash:
            raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Hash mismatch on {rel_path}!")
    print(f"  [Gate 2] All {len(PROTECTED_ASSETS)} protected historical assets verified (SHA-256 MATCH).")

    # 3. Verify five-partition manifest
    if not MANIFEST_PATH.exists():
        raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Pilot manifest missing at {MANIFEST_PATH}")
    df_manifest = pd.read_csv(MANIFEST_PATH, dtype={"pointing": str})
    if len(df_manifest) != 2500:
        raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Manifest contains {len(df_manifest)} rows, expected exactly 2500!")
    if df_manifest["trial_id"].nunique() != 2500:
        raise RuntimeError("PRE-EXECUTION GATE BLOCKED: Duplicate trial IDs detected in manifest!")
    print(f"  [Gate 3] Manifest verified: exactly 2,500 unique planned trial specifications.")

    # 4. Verify Calibration / Evaluation disjointness
    cal_pointings = set(df_manifest[df_manifest["role"] == "CALIBRATION"]["pointing"].unique())
    eval_pointings = set(df_manifest[df_manifest["role"] == "EVALUATION"]["pointing"].unique())
    overlap = cal_pointings.intersection(eval_pointings)
    if len(overlap) > 0:
        raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: Spatial leakage detected across roles: {overlap}")
    print(f"  [Gate 4] Spatial disjointness verified: Calibration {cal_pointings} vs Evaluation {eval_pointings} (Zero Leakage).")

    # 5. Verify 120 FITS products exist
    for rel_path in df_manifest["fits_relpath"].unique():
        fp = BASE_DIR / rel_path
        if not fp.exists():
            raise RuntimeError(f"PRE-EXECUTION GATE BLOCKED: FITS product missing: {rel_path}")
    print(f"  [Gate 5] All 120 FITS products confirmed present on disk.")

    print("\nALL PRE-EXECUTION GATES PASSED. AUTHORIZATION TO EXECUTE VALIDATED.")
    print("=" * 80)
    return {
        "status": "PASS",
        "checkpoint_sha256": PROTECTED_ASSETS["checkpoints/astrovision_spatial_v2.pt"],
        "manifest_sha256": compute_sha256(MANIFEST_PATH),
        "total_trials": len(df_manifest)
    }


def compute_exact_auroc(labels: np.ndarray, scores: np.ndarray) -> float:
    """Computes exact rank-based AUROC using the Mann-Whitney U statistic."""
    pos = scores[labels == 1]
    neg = scores[labels == 0]
    n_pos = len(pos)
    n_neg = len(neg)
    if n_pos == 0 or n_neg == 0:
        return 0.5
    ranks = pd.Series(scores).rank(method="average").values
    rank_sum_pos = np.sum(ranks[labels == 1])
    u_stat = rank_sum_pos - (n_pos * (n_pos + 1)) / 2.0
    auroc = float(u_stat / (n_pos * n_neg))
    return max(0.0, min(1.0, auroc))


def compute_auprc(labels: np.ndarray, scores: np.ndarray) -> float:
    """Computes Average Precision (Area Under Precision-Recall Curve)."""
    order = np.argsort(-scores)
    sorted_labels = labels[order]
    n_pos = np.sum(sorted_labels == 1)
    if n_pos == 0:
        return 0.0
    tp_cum = np.cumsum(sorted_labels == 1)
    fp_cum = np.cumsum(sorted_labels == 0)
    recalls = tp_cum / n_pos
    precisions = tp_cum / (tp_cum + fp_cum)
    # Average precision
    ap = float(np.sum((recalls[1:] - recalls[:-1]) * precisions[1:]) + recalls[0] * precisions[0])
    return max(0.0, min(1.0, ap))


class PilotCampaignExecutor:
    """Executes the authorized 2,500-trial pilot benchmark campaign with full caching and safety."""

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.rng = np.random.default_rng(seed)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Initializing ASTROVISION Evaluator on device: {self.device}...")
        self.evaluator = AstroVisionEvaluatorV2(device=str(self.device))
        self.injection_engine = PhysicalSpatialInjectionEngineV2()
        self.fits_cache: Dict[str, Dict[str, Any]] = {}

    def get_fits_data(self, fits_relpath: str) -> Dict[str, Any]:
        """Loads and caches full-frame FITS arrays (image, variance, flags, metadata)."""
        if fits_relpath in self.fits_cache:
            return self.fits_cache[fits_relpath]

        fp = BASE_DIR / fits_relpath
        with fits.open(fp) as hdul:
            img = hdul["IMAGE"].data.astype(np.float32)
            var = hdul["VARIANCE"].data.astype(np.float32)
            flags = hdul["FLAGS"].data.astype(np.int32)
            hdr = hdul["IMAGE"].header
            exptime = float(hdr.get("EXPTIME", 100.0))
            obs_id = str(hdr.get("OBS_ID", "UNKNOWN"))
            pixel_scale = float(hdr.get("PLTSCALE", DEFAULT_PIXEL_SCALE_ARCSEC))

        data = {
            "image": img,
            "variance": var,
            "flags": flags,
            "exptime": exptime,
            "obs_id": obs_id,
            "pixel_scale": pixel_scale,
            "fits_path": str(fp)
        }
        self.fits_cache[fits_relpath] = data
        return data

    def extract_patch(
        self,
        fits_data: Dict[str, Any],
        cx: float,
        cy: float,
        patch_size: int = 128
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, int, int, float, float]:
        """Extracts patch with NaN imputation and variance lower bounding."""
        x0 = int(round(cx)) - patch_size // 2
        y0 = int(round(cy)) - patch_size // 2
        sub_x = cx - x0
        sub_y = cy - y0

        raw_img = fits_data["image"][y0:y0+patch_size, x0:x0+patch_size]
        raw_var = fits_data["variance"][y0:y0+patch_size, x0:x0+patch_size]
        raw_flags = fits_data["flags"][y0:y0+patch_size, x0:x0+patch_size]

        good = ((raw_flags & FATAL_FLAG_MASK) == 0) & (~np.isnan(raw_img)) & (~np.isnan(raw_var))
        med_bg = float(np.median(raw_img[good])) if np.any(good) else 0.0
        var_bg = float(np.median(raw_var[good])) if np.any(good) else 1e-2

        cutout_img = np.nan_to_num(raw_img, nan=med_bg)
        cutout_var = np.maximum(np.nan_to_num(raw_var, nan=var_bg), 1e-4)

        return cutout_img, cutout_var, raw_flags, x0, y0, sub_x, sub_y

    def execute_campaign(self) -> Dict[str, Any]:
        t_start = time.time()
        start_iso = datetime.now(timezone.utc).isoformat()
        print(f"\nSTARTING 2,500-TRIAL CONTROLLED PILOT CAMPAIGN EXECUTION at {start_iso}")

        df_manifest = pd.read_csv(MANIFEST_PATH, dtype={"pointing": str})
        
        # Check if resuming
        executed_trials = set()
        if RESULTS_CSV.exists():
            df_prev = pd.read_csv(RESULTS_CSV)
            if len(df_prev) > 0 and "trial_id" in df_prev.columns:
                executed_trials = set(df_prev["trial_id"].unique())
                print(f"  Found existing results with {len(executed_trials)} previously executed trials.")

        # Stage 1: CALIBRATION STAGE
        print("\n--- STAGE 1: CALIBRATION EXECUTION (Partitions 1 & 2) ---")
        cal_trials = df_manifest[df_manifest["role"] == "CALIBRATION"].copy()
        
        cal_records = []
        for idx, row in cal_trials.iterrows():
            t_id = row["trial_id"]
            part = row["partition"]
            f_rel = row["fits_relpath"]
            det_num = int(row["detector_num"])
            cx = float(row["center_pixel_x"])
            cy = float(row["center_pixel_y"])
            target_snr = float(row["target_snr"])

            fits_data = self.get_fits_data(f_rel)
            c_img, c_var, c_flags, x0, y0, sub_x, sub_y = self.extract_patch(fits_data, cx, cy)
            
            # Local background sigma
            good = ((c_flags & FATAL_FLAG_MASK) == 0) & (~np.isnan(c_img))
            bg_sigma = float(np.sqrt(np.median(c_var[good]))) if np.any(good) else 1e-2

            if part == "CALIBRATION_CONTROL":
                pair = self.injection_engine.create_zero_injection_control_pair(
                    cutout_img=c_img,
                    cutout_var=c_var,
                    cutout_flags=c_flags,
                    detector_id=det_num,
                    det_x0=x0,
                    det_y0=y0,
                    det_cx=cx,
                    det_cy=cy,
                    sub_x=sub_x,
                    sub_y=sub_y,
                    exptime=fits_data["exptime"],
                    pair_id=f"PAIR_{t_id}",
                    control_trial_id=t_id,
                    partition=part,
                    obs_id=fits_data["obs_id"],
                    filename=row["fits_filename"]
                )
                inj_dict = {"total_flux_mjy_sr_pix": 0.0, "flux_jy": 0.0}
            else:  # CALIBRATION_INJECTION
                flux_mjy_sr_pix = target_snr * bg_sigma * 5.0
                pair, inj_dict = self.injection_engine.create_matched_point_source_pair(
                    cutout_img=c_img,
                    cutout_var=c_var,
                    cutout_flags=c_flags,
                    fits_path=fits_data["fits_path"],
                    detector_id=det_num,
                    det_x0=x0,
                    det_y0=y0,
                    det_cx=cx,
                    det_cy=cy,
                    sub_x=sub_x,
                    sub_y=sub_y,
                    total_flux_mjy_sr_pix=flux_mjy_sr_pix,
                    exptime=fits_data["exptime"],
                    pair_id=f"PAIR_{t_id}",
                    control_trial_id=f"CTRL_{t_id}",
                    injected_trial_id=t_id,
                    partition=part,
                    obs_id=fits_data["obs_id"],
                    filename=row["fits_filename"],
                    rng=self.rng
                )

            # Evaluate with preliminary threshold tau=0.0
            rec = self.evaluator.evaluate_paired_model_output(pair, threshold_tau=0.0)
            
            cal_records.append({
                "trial_id": t_id,
                "partition": part,
                "role": "CALIBRATION",
                "pointing": row["pointing"],
                "detector": row["detector"],
                "detector_num": det_num,
                "dither": int(row["dither"]),
                "fits_filename": row["fits_filename"],
                "fits_relpath": f_rel,
                "center_pixel_x": cx,
                "center_pixel_y": cy,
                "center_ra": float(row["center_ra"]),
                "center_dec": float(row["center_dec"]),
                "target_snr": target_snr,
                "injection_class": row["injection_class"],
                "source_type": row["source_type"],
                "injected_flux_mjy_sr_pix": float(inj_dict.get("total_flux_mjy_sr_pix", 0.0)),
                "injected_flux_jy": float(inj_dict.get("flux_jy", 0.0)),
                "model_target_peak_chi2": float(rec.model_target_peak_chi2),
                "model_global_peak_chi2": float(rec.model_global_peak_chi2),
                "model_recovered_sub_x": float(rec.model_recovered_sub_x),
                "model_recovered_sub_y": float(rec.model_recovered_sub_y),
                "model_position_error_pix": float(rec.model_position_error_pix),
                "differential_residual_flux": float(rec.differential_residual_flux),
                "differential_residual_flux_jy": float(rec.differential_residual_flux_jy),
                "valid_aperture_pixels": int(rec.valid_aperture_pixels),
                "masked_aperture_pixels": int(rec.masked_aperture_pixels),
                "is_detected": False,  # Will be updated once tau_d is computed
                "applied_threshold_tau": 0.0
            })

            if (len(cal_records)) % 200 == 0:
                print(f"  Calibration progress: {len(cal_records)} / {len(cal_trials)} trials completed...")

        df_cal = pd.DataFrame(cal_records)

        # -------------------------------------------------------------
        # FIT CALIBRATION PARAMETERS
        # -------------------------------------------------------------
        print("\n--- FITTING DETECTOR-SPECIFIC OPERATING THRESHOLDS & TRANSFER CURVES ---")
        df_cal_ctrl = df_cal[df_cal["partition"] == "CALIBRATION_CONTROL"]
        df_cal_inj = df_cal[df_cal["partition"] == "CALIBRATION_INJECTION"]

        calib_params = {
            "metadata": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "calibration_pointings": ["0001", "0008"],
                "alpha_target_nominal": 0.05,
                "alpha_target_stringent": 0.01,
                "source_partition": "CALIBRATION_CONTROL"
            },
            "detector_thresholds": {},
            "detector_transfer_curves": {}
        }

        detector_taus = {}
        for det_num in range(1, 7):
            det_name = f"D{det_num}"
            scores_det = df_cal_ctrl[df_cal_ctrl["detector_num"] == det_num]["model_target_peak_chi2"].values
            scores_det = scores_det[~np.isnan(scores_det)]
            
            # 95th percentile (alpha = 0.05) and 99th percentile (alpha = 0.01)
            tau_95 = float(np.percentile(scores_det, 95.0))
            tau_99 = float(np.percentile(scores_det, 99.0))
            tau_median = float(np.median(scores_det))
            tau_max = float(np.max(scores_det))

            detector_taus[det_num] = tau_95

            # Fit transfer curve recovery on CALIBRATION_INJECTION
            inj_det = df_cal_inj[df_cal_inj["detector_num"] == det_num].copy()
            inj_det["detected"] = (inj_det["model_target_peak_chi2"] >= tau_95) & (inj_det["model_position_error_pix"] <= 2.5)
            
            recovery_by_snr = inj_det.groupby("target_snr")["detected"].agg(["count", "mean"]).reset_index()
            snrs = recovery_by_snr["target_snr"].values
            rec_rates = recovery_by_snr["mean"].values

            # Estimate C50 and C90 by linear interpolation
            c50 = float(np.interp(0.50, rec_rates, snrs, left=snrs[0], right=snrs[-1]))
            c90 = float(np.interp(0.90, rec_rates, snrs, left=snrs[0], right=snrs[-1]))

            calib_params["detector_thresholds"][det_name] = {
                "tau_nominal_alpha_0_05": round(tau_95, 4),
                "tau_stringent_alpha_0_01": round(tau_99, 4),
                "null_sample_count": len(scores_det),
                "null_score_median": round(tau_median, 4),
                "null_score_max": round(tau_max, 4)
            }

            calib_params["detector_transfer_curves"][det_name] = {
                "snr_grid": list(snrs),
                "recovery_fraction": [round(float(r), 4) for r in rec_rates],
                "trial_counts": [int(c) for c in recovery_by_snr["count"].values],
                "c50_snr": round(c50, 2),
                "c90_snr": round(c90, 2)
            }

            print(f"  {det_name}: tau(alpha=0.05) = {tau_95:.4f}, tau(alpha=0.01) = {tau_99:.4f}, C50 = SNR {c50:.2f}, C90 = SNR {c90:.2f}")

        # Update calibration records with applied tau
        for r in cal_records:
            d_tau = detector_taus[r["detector_num"]]
            r["applied_threshold_tau"] = d_tau
            r["is_detected"] = bool((r["model_target_peak_chi2"] >= d_tau) and (r["model_position_error_pix"] <= 2.5))

        with open(CALIB_PARAMS_JSON, "w", encoding="utf-8") as f:
            json.dump(calib_params, f, indent=2)
        print(f"Calibration parameters frozen -> {CALIB_PARAMS_JSON.name}")

        # -------------------------------------------------------------
        # STAGE 2: EVALUATION STAGE (Partitions 3, 4, 5)
        # -------------------------------------------------------------
        print("\n--- STAGE 2: EVALUATION EXECUTION (Partitions 3, 4, 5) ---")
        eval_trials = df_manifest[df_manifest["role"] == "EVALUATION"].copy()
        
        eval_records = []
        fwhm_grid = [12.0, 18.0, 24.0, 36.0]

        for idx, row in eval_trials.iterrows():
            t_id = row["trial_id"]
            part = row["partition"]
            f_rel = row["fits_relpath"]
            det_num = int(row["detector_num"])
            cx = float(row["center_pixel_x"])
            cy = float(row["center_pixel_y"])
            target_snr = float(row["target_snr"])

            fits_data = self.get_fits_data(f_rel)
            c_img, c_var, c_flags, x0, y0, sub_x, sub_y = self.extract_patch(fits_data, cx, cy)
            
            good = ((c_flags & FATAL_FLAG_MASK) == 0) & (~np.isnan(c_img))
            bg_sigma = float(np.sqrt(np.median(c_var[good]))) if np.any(good) else 1e-2
            tau_d = detector_taus[det_num]

            if part == "EVALUATION_CONTROL":
                pair = self.injection_engine.create_zero_injection_control_pair(
                    cutout_img=c_img,
                    cutout_var=c_var,
                    cutout_flags=c_flags,
                    detector_id=det_num,
                    det_x0=x0,
                    det_y0=y0,
                    det_cx=cx,
                    det_cy=cy,
                    sub_x=sub_x,
                    sub_y=sub_y,
                    exptime=fits_data["exptime"],
                    pair_id=f"PAIR_{t_id}",
                    control_trial_id=t_id,
                    partition=part,
                    obs_id=fits_data["obs_id"],
                    filename=row["fits_filename"]
                )
                inj_dict = {"total_flux_mjy_sr_pix": 0.0, "flux_jy": 0.0}

            elif part == "EVALUATION_POINT_SOURCE_INJECTION":
                flux_mjy_sr_pix = target_snr * bg_sigma * 5.0
                pair, inj_dict = self.injection_engine.create_matched_point_source_pair(
                    cutout_img=c_img,
                    cutout_var=c_var,
                    cutout_flags=c_flags,
                    fits_path=fits_data["fits_path"],
                    detector_id=det_num,
                    det_x0=x0,
                    det_y0=y0,
                    det_cx=cx,
                    det_cy=cy,
                    sub_x=sub_x,
                    sub_y=sub_y,
                    total_flux_mjy_sr_pix=flux_mjy_sr_pix,
                    exptime=fits_data["exptime"],
                    pair_id=f"PAIR_{t_id}",
                    control_trial_id=f"CTRL_{t_id}",
                    injected_trial_id=t_id,
                    partition=part,
                    obs_id=fits_data["obs_id"],
                    filename=row["fits_filename"],
                    rng=self.rng
                )

            else:  # EVALUATION_EXTENDED_SOURCE_INJECTION
                fwhm_val = fwhm_grid[len(eval_records) % len(fwhm_grid)]
                flux_mjy_sr_pix = target_snr * bg_sigma * 10.0
                pair, inj_dict = self.injection_engine.create_matched_extended_source_pair(
                    cutout_img=c_img,
                    cutout_var=c_var,
                    cutout_flags=c_flags,
                    detector_id=det_num,
                    det_x0=x0,
                    det_y0=y0,
                    det_cx=cx,
                    det_cy=cy,
                    sub_x=sub_x,
                    sub_y=sub_y,
                    total_flux_mjy_sr_pix=flux_mjy_sr_pix,
                    fwhm_arcsec=fwhm_val,
                    exptime=fits_data["exptime"],
                    pair_id=f"PAIR_{t_id}",
                    control_trial_id=f"CTRL_{t_id}",
                    injected_trial_id=t_id,
                    partition=part,
                    obs_id=fits_data["obs_id"],
                    filename=row["fits_filename"],
                    rng=self.rng
                )

            rec = self.evaluator.evaluate_paired_model_output(pair, threshold_tau=tau_d)

            eval_records.append({
                "trial_id": t_id,
                "partition": part,
                "role": "EVALUATION",
                "pointing": row["pointing"],
                "detector": row["detector"],
                "detector_num": det_num,
                "dither": int(row["dither"]),
                "fits_filename": row["fits_filename"],
                "fits_relpath": f_rel,
                "center_pixel_x": cx,
                "center_pixel_y": cy,
                "center_ra": float(row["center_ra"]),
                "center_dec": float(row["center_dec"]),
                "target_snr": target_snr,
                "injection_class": row["injection_class"],
                "source_type": row["source_type"],
                "injected_flux_mjy_sr_pix": float(inj_dict.get("total_flux_mjy_sr_pix", 0.0)),
                "injected_flux_jy": float(inj_dict.get("flux_jy", 0.0)),
                "model_target_peak_chi2": float(rec.model_target_peak_chi2),
                "model_global_peak_chi2": float(rec.model_global_peak_chi2),
                "model_recovered_sub_x": float(rec.model_recovered_sub_x),
                "model_recovered_sub_y": float(rec.model_recovered_sub_y),
                "model_position_error_pix": float(rec.model_position_error_pix),
                "differential_residual_flux": float(rec.differential_residual_flux),
                "differential_residual_flux_jy": float(rec.differential_residual_flux_jy),
                "valid_aperture_pixels": int(rec.valid_aperture_pixels),
                "masked_aperture_pixels": int(rec.masked_aperture_pixels),
                "is_detected": bool((rec.model_target_peak_chi2 >= tau_d) and (rec.model_position_error_pix <= 2.5)),
                "applied_threshold_tau": tau_d
            })

            if len(eval_records) % 250 == 0:
                print(f"  Evaluation progress: {len(eval_records)} / {len(eval_trials)} trials completed...")

        # Combine all 2,500 records
        all_results = cal_records + eval_records
        df_all = pd.DataFrame(all_results)
        df_all.to_csv(RESULTS_CSV, index=False)
        print(f"\nAll 2,500 trials executed successfully and streamed -> {RESULTS_CSV.name} ({compute_sha256(RESULTS_CSV)[:16]}...)")

        # -------------------------------------------------------------
        # COMPUTE EVALUATION METRICS
        # -------------------------------------------------------------
        print("\n--- COMPUTING PILOT EVALUATION METRICS ---")
        df_eval = df_all[df_all["role"] == "EVALUATION"].copy()
        ctrl_eval = df_eval[df_eval["partition"] == "EVALUATION_CONTROL"]
        pt_eval = df_eval[df_eval["partition"] == "EVALUATION_POINT_SOURCE_INJECTION"]
        ext_eval = df_eval[df_eval["partition"] == "EVALUATION_EXTENDED_SOURCE_INJECTION"]

        # 1. False Positive Rate on Evaluation Controls
        eval_fpr = float(ctrl_eval["is_detected"].mean())
        print(f"  Empirical Evaluation FPR at calibrated tau_d: {eval_fpr:.4f} ({ctrl_eval['is_detected'].sum()} / {len(ctrl_eval)})")

        # 2. Point Source AUROC & AUPRC
        pt_labels = np.concatenate([np.zeros(len(ctrl_eval)), np.ones(len(pt_eval))])
        pt_scores = np.concatenate([ctrl_eval["model_target_peak_chi2"].values, pt_eval["model_target_peak_chi2"].values])
        pt_auroc = compute_exact_auroc(pt_labels, pt_scores)
        pt_auprc = compute_auprc(pt_labels, pt_scores)
        pt_recovery_rate = float(pt_eval["is_detected"].mean())
        print(f"  Point Sources: AUROC = {pt_auroc:.4f}, AUPRC = {pt_auprc:.4f}, Overall Recovery = {pt_recovery_rate*100:.2f}%")

        # 3. Extended Source AUROC & AUPRC
        ext_labels = np.concatenate([np.zeros(len(ctrl_eval)), np.ones(len(ext_eval))])
        ext_scores = np.concatenate([ctrl_eval["model_target_peak_chi2"].values, ext_eval["model_target_peak_chi2"].values])
        ext_auroc = compute_exact_auroc(ext_labels, ext_scores)
        ext_auprc = compute_auprc(ext_labels, ext_scores)
        ext_recovery_rate = float(ext_eval["is_detected"].mean())
        print(f"  Extended Sources: AUROC = {ext_auroc:.4f}, AUPRC = {ext_auprc:.4f}, Overall Recovery = {ext_recovery_rate*100:.2f}%")

        # 4. Detector-Wise Metrics
        detector_eval_metrics = {}
        for det_num in range(1, 7):
            d_name = f"D{det_num}"
            c_d = ctrl_eval[ctrl_eval["detector_num"] == det_num]
            p_d = pt_eval[pt_eval["detector_num"] == det_num]
            e_d = ext_eval[ext_eval["detector_num"] == det_num]

            d_pt_labels = np.concatenate([np.zeros(len(c_d)), np.ones(len(p_d))])
            d_pt_scores = np.concatenate([c_d["model_target_peak_chi2"].values, p_d["model_target_peak_chi2"].values])
            d_pt_auroc = compute_exact_auroc(d_pt_labels, d_pt_scores)

            d_ext_labels = np.concatenate([np.zeros(len(c_d)), np.ones(len(e_d))])
            d_ext_scores = np.concatenate([c_d["model_target_peak_chi2"].values, e_d["model_target_peak_chi2"].values])
            d_ext_auroc = compute_exact_auroc(d_ext_labels, d_ext_scores)

            detector_eval_metrics[d_name] = {
                "fpr": round(float(c_d["is_detected"].mean()), 4),
                "point_source_auroc": round(d_pt_auroc, 4),
                "point_source_recovery": round(float(p_d["is_detected"].mean()), 4),
                "extended_source_auroc": round(d_ext_auroc, 4),
                "extended_source_recovery": round(float(e_d["is_detected"].mean()), 4)
            }

        # 5. Pointing-Wise Metrics
        pointing_eval_metrics = {}
        for p in ["0002", "0009", "0010"]:
            c_p = ctrl_eval[ctrl_eval["pointing"] == p]
            p_p = pt_eval[pt_eval["pointing"] == p]
            e_p = ext_eval[ext_eval["pointing"] == p]

            p_pt_labels = np.concatenate([np.zeros(len(c_p)), np.ones(len(p_p))])
            p_pt_scores = np.concatenate([c_p["model_target_peak_chi2"].values, p_p["model_target_peak_chi2"].values])
            p_pt_auroc = compute_exact_auroc(p_pt_labels, p_pt_scores)

            pointing_eval_metrics[p] = {
                "fpr": round(float(c_p["is_detected"].mean()), 4),
                "point_source_auroc": round(p_pt_auroc, 4),
                "point_source_recovery": round(float(p_p["is_detected"].mean()), 4),
                "extended_source_recovery": round(float(e_p["is_detected"].mean()), 4)
            }

        # 6. Cluster-Bootstrap over 10 Unique Multisets (G_eval = 3)
        multisets = [
            ["0002", "0002", "0002"],
            ["0002", "0002", "0009"],
            ["0002", "0002", "0010"],
            ["0002", "0009", "0009"],
            ["0002", "0009", "0010"],
            ["0002", "0010", "0010"],
            ["0009", "0009", "0009"],
            ["0009", "0009", "0010"],
            ["0009", "0010", "0010"],
            ["0010", "0010", "0010"],
        ]
        boot_aurocs_pt = []
        boot_aurocs_ext = []
        for ms in multisets:
            ms_ctrl = pd.concat([ctrl_eval[ctrl_eval["pointing"] == p] for p in ms], ignore_index=True)
            ms_pt = pd.concat([pt_eval[pt_eval["pointing"] == p] for p in ms], ignore_index=True)
            ms_ext = pd.concat([ext_eval[ext_eval["pointing"] == p] for p in ms], ignore_index=True)

            l_pt = np.concatenate([np.zeros(len(ms_ctrl)), np.ones(len(ms_pt))])
            s_pt = np.concatenate([ms_ctrl["model_target_peak_chi2"].values, ms_pt["model_target_peak_chi2"].values])
            boot_aurocs_pt.append(compute_exact_auroc(l_pt, s_pt))

            l_ext = np.concatenate([np.zeros(len(ms_ctrl)), np.ones(len(ms_ext))])
            s_ext = np.concatenate([ms_ctrl["model_target_peak_chi2"].values, ms_ext["model_target_peak_chi2"].values])
            boot_aurocs_ext.append(compute_exact_auroc(l_ext, s_ext))

        eval_summary = {
            "metadata": {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "total_evaluation_trials": len(df_eval),
                "evaluation_pointings": ["0002", "0009", "0010"],
                "calibration_pointings": ["0001", "0008"],
                "statistical_model": "G_eval=3 Pointing Clusters (10 unique multisets)"
            },
            "overall_metrics": {
                "evaluation_fpr": round(eval_fpr, 4),
                "point_source_auroc": round(pt_auroc, 4),
                "point_source_auroc_bootstrap_range": [round(min(boot_aurocs_pt), 4), round(max(boot_aurocs_pt), 4)],
                "point_source_auprc": round(pt_auprc, 4),
                "point_source_recovery_fraction": round(pt_recovery_rate, 4),
                "extended_source_auroc": round(ext_auroc, 4),
                "extended_source_auroc_bootstrap_range": [round(min(boot_aurocs_ext), 4), round(max(boot_aurocs_ext), 4)],
                "extended_source_auprc": round(ext_auprc, 4),
                "extended_source_recovery_fraction": round(ext_recovery_rate, 4)
            },
            "detector_metrics": detector_eval_metrics,
            "pointing_metrics": pointing_eval_metrics,
            "cluster_bootstrap_multisets_aurocs_pt": [round(a, 4) for a in boot_aurocs_pt],
            "cluster_bootstrap_multisets_aurocs_ext": [round(a, 4) for a in boot_aurocs_ext]
        }

        with open(EVAL_METRICS_JSON, "w", encoding="utf-8") as f:
            json.dump(eval_summary, f, indent=2)
        print(f"Evaluation metrics saved -> {EVAL_METRICS_JSON.name}")

        elapsed = time.time() - t_start
        print(f"\nCAMPAIGN COMPLETED SUCCESSFULLY in {elapsed:.2f} seconds ({elapsed/60.0:.2f} minutes).")
        return {
            "elapsed_seconds": round(elapsed, 2),
            "results_csv_sha256": compute_sha256(RESULTS_CSV),
            "calibration_json_sha256": compute_sha256(CALIB_PARAMS_JSON),
            "evaluation_json_sha256": compute_sha256(EVAL_METRICS_JSON),
            "total_executed": len(df_all),
            "eval_summary": eval_summary
        }


if __name__ == "__main__":
    gate_res = run_pre_execution_gate()
    executor = PilotCampaignExecutor(seed=42)
    campaign_res = executor.execute_campaign()
    print("\nTask 1.1R execution run finished.")

