"""
ASTROVISION Controlled Benchmark Campaign Driver (Preparation & Dry-Run Mode)
NASA Space Apps Challenge 2026 — SPECTRA-X / F1 Phase 3 Task 1.1H

Role: Principal Scientific Data Engineer & ML Validation Architect

MANDATORY SCIENTIFIC GOVERNANCE:
- BENCHMARK EXECUTION IS STRICTLY PROHIBITED IN TASK 1.1H.
- This driver prepares the complete dataset, grouping manifests, trial configurations,
  and threshold-calibration procedures.
- It operates strictly in DRY-RUN / PREPARATION mode with zero model inference.
- Does not modify frozen checkpoints, catalogues, or authoritative FITS files.
"""

import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import glob
import json
import math
import hashlib
import logging
import argparse
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from scripts.validation.astrovision_injection_benchmark_v2 import (
    SPHERExFITSValidatorV2,
    AbsoluteGainProviderV2,
    InFilePSFProviderV2,
    PhysicalSpatialInjectionEngineV2,
    AstroVisionEvaluatorV2,
    StratifiedDetectorSamplerV2,
    MatchedCutoutPairV2,
    FootprintGeometryV2,
    GroupAwarePartitionManagerV2,
    PartitionAssignmentResultV2,
    DEFAULT_PIXEL_SCALE_ARCSEC,
    NOMINAL_PIXEL_SOLID_ANGLE_SR,
    FATAL_FLAG_MASK
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AstroVisionCampaignDriver")

# Authoritative Immutability References
FROZEN_CHECKPOINT = "checkpoints/astrovision_spatial_v2.pt"
EXPECTED_CHECKPOINT_SHA256 = "f65c0f139a5e1fa5073707eb006145d6a380637a42599d7ea061724f64080557"
FROZEN_CATALOGUE = "data/processed/validation/pointing_0003_final_validated_catalogue.csv"
EXPECTED_CATALOGUE_SHA256 = "ce1416bb0d5fcffe6fbc7a3115cb0e90e76dc0cf40fb04d87ba1ab5f3ebb8f2b"

# Execution Governance Safety Lock
CAMPAIGN_EXECUTION_LOCKED = True


class AstroVisionControlledCampaignDriver:
    """
    Orchestrates the preparation, group-aware partitioning, and manifest generation
    for the ASTROVISION spatial recovery benchmark campaign without executing inference.
    """

    def __init__(
        self,
        pointing_files_pattern: str = "data/spherex/qr3/level2/*0003*.fits",
        catalog_path: str = FROZEN_CATALOGUE,
        checkpoint_path: str = FROZEN_CHECKPOINT,
        templates_dir: str = "data/spherex/qr3/templates",
        seed: int = 42
    ):
        self.pointing_files_pattern = pointing_files_pattern
        self.catalog_path = catalog_path
        self.checkpoint_path = checkpoint_path
        self.templates_dir = templates_dir
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def verify_governance_and_assets(self) -> Dict[str, str]:
        """Validates that all authoritative assets match their frozen cryptographic signatures."""
        logger.info("Verifying authoritative asset immutability...")
        if not os.path.exists(self.checkpoint_path):
            raise FileNotFoundError(f"Checkpoint not found at {self.checkpoint_path}")
        with open(self.checkpoint_path, "rb") as f:
            ckpt_hash = hashlib.sha256(f.read()).hexdigest()
        if ckpt_hash != EXPECTED_CHECKPOINT_SHA256:
            raise ValueError(f"CRITICAL: Checkpoint hash mismatch! Expected {EXPECTED_CHECKPOINT_SHA256}, got {ckpt_hash}")

        if not os.path.exists(self.catalog_path):
            raise FileNotFoundError(f"Catalogue not found at {self.catalog_path}")
        with open(self.catalog_path, "rb") as f:
            cat_hash = hashlib.sha256(f.read()).hexdigest()
        if cat_hash != EXPECTED_CATALOGUE_SHA256:
            raise ValueError(f"CRITICAL: Catalogue hash mismatch! Expected {EXPECTED_CATALOGUE_SHA256}, got {cat_hash}")

        logger.info("Asset verification PASSED. Checkpoint and catalogue are cryptographically locked.")
        return {
            "checkpoint_sha256": ckpt_hash,
            "catalogue_sha256": cat_hash
        }

    def prepare_campaign_manifest(
        self,
        cutouts_per_detector: int = 50,
        calibration_fraction: float = 0.5,
        min_spatial_sep_pix: float = 128.0
    ) -> Dict[str, Any]:
        """
        Executes complete dry-run dataset harvesting, exposure grouping,
        and trial configuration generation without model inference.
        """
        # Step 1: Asset check
        asset_info = self.verify_governance_and_assets()

        # Step 2: Discover pointing FITS files
        fits_files = sorted(glob.glob(self.pointing_files_pattern))
        if not fits_files:
            raise FileNotFoundError(f"No FITS files found matching {self.pointing_files_pattern}")
        logger.info(f"Discovered {len(fits_files)} Level-2 science files for Pointing 0003.")

        # Step 3: Harvest safe stratified cutouts with spatial overlap avoidance
        logger.info(f"Harvesting up to {cutouts_per_detector} cutouts per detector array (D1-D6)...")
        sampler = StratifiedDetectorSamplerV2(
            pointing_files=fits_files,
            catalog_path=self.catalog_path
        )
        harvested_by_det = sampler.harvest_stratified_safe_cutouts(
            cutouts_per_detector=cutouts_per_detector,
            patch_size=128,
            min_source_dist_pix=8.0,
            random_seed=self.seed,
            num_probes_per_file=600
        )

        total_harvested = sum(len(items) for items in harvested_by_det.values())
        logger.info(f"Successfully harvested {total_harvested} spatially safe cutouts across D1-D6.")

        # Step 4: Apply Group-Aware Exposure-Level Partitioning (Remediating Audit F & 1.1H)
        logger.info("Executing exposure-level group-aware partition assignment...")
        partition_manager = GroupAwarePartitionManagerV2(
            min_spatial_sep_pix=min_spatial_sep_pix,
            strict_metadata=True
        )
        partition_result = partition_manager.assign_partitions(
            harvested_items=harvested_by_det,
            calibration_fraction=calibration_fraction,
            seed=self.seed
        )

        logger.info(
            f"Partitioning complete: "
            f"{len(partition_result.calibration_items)} CALIBRATION cutouts, "
            f"{len(partition_result.evaluation_items)} EVALUATION cutouts, "
            f"{len(partition_result.rejected_items)} rejected spatial overlaps. "
            f"Strictly disjoint: {partition_result.is_strictly_disjoint}"
        )

        # Step 5: Define Trial Configurations (Grid Design across 5 Partitions)
        snr_grid = [3.0, 5.0, 7.0, 10.0, 15.0, 20.0, 30.0, 50.0]
        fwhm_grid_arcsec = [12.0, 18.0, 24.0, 36.0]

        trials_manifest = []

        # A. CALIBRATION_CONTROL (Zero-injection on calibration exposures)
        for idx, item in enumerate(partition_result.calibration_items):
            ctrl_id = f"CAL_CTRL_{idx:04d}"
            cutout_id = item.get("id", f"CAL_CUTOUT_{idx:04d}")
            trials_manifest.append({
                "trial_id": ctrl_id,
                "parent_cutout_id": cutout_id,
                "matched_control_id": ctrl_id,
                "partition": "CALIBRATION_CONTROL",
                "source_type": "ZERO_INJECTION_CONTROL",
                "obs_id": item["obs_id"],
                "filename": item["filename"],
                "detector_id": item["detector_id"],
                "det_cx": item["cx_det"],
                "det_cy": item["cy_det"],
                "target_snr": 0.0,
                "target_flux_mjy_sr_pix": 0.0,
                "fwhm_arcsec": 0.0
            })

        # B. CALIBRATION_INJECTION (Calibration exposures for out-of-sample transfer curve fitting)
        cal_inj_count = 0
        for idx, item in enumerate(partition_result.calibration_items):
            ctrl_id = f"CAL_CTRL_{idx:04d}"
            cutout_id = item.get("id", f"CAL_CUTOUT_{idx:04d}")
            target_snr = snr_grid[idx % len(snr_grid)]
            bg_sigma = max(1e-3, float(item.get("bg_std_eff", item.get("bg_std", 1e-2))))
            flux_mjy_sr_pix = target_snr * bg_sigma * 5.0
            trials_manifest.append({
                "trial_id": f"CAL_INJ_{idx:04d}",
                "parent_cutout_id": cutout_id,
                "matched_control_id": ctrl_id,
                "partition": "CALIBRATION_INJECTION",
                "source_type": "POINT_SOURCE",
                "obs_id": item["obs_id"],
                "filename": item["filename"],
                "detector_id": item["detector_id"],
                "det_cx": item["cx_det"],
                "det_cy": item["cy_det"],
                "target_snr": target_snr,
                "target_flux_mjy_sr_pix": flux_mjy_sr_pix,
                "fwhm_arcsec": 0.0
            })
            cal_inj_count += 1

        # C. EVALUATION_CONTROL (Zero-injection on evaluation exposures for empirical FPR)
        for idx, item in enumerate(partition_result.evaluation_items):
            ctrl_id = f"EVAL_CTRL_{idx:04d}"
            cutout_id = item.get("id", f"EVAL_CUTOUT_{idx:04d}")
            trials_manifest.append({
                "trial_id": ctrl_id,
                "parent_cutout_id": cutout_id,
                "matched_control_id": ctrl_id,
                "partition": "EVALUATION_CONTROL",
                "source_type": "ZERO_INJECTION_CONTROL",
                "obs_id": item["obs_id"],
                "filename": item["filename"],
                "detector_id": item["detector_id"],
                "det_cx": item["cx_det"],
                "det_cy": item["cy_det"],
                "target_snr": 0.0,
                "target_flux_mjy_sr_pix": 0.0,
                "fwhm_arcsec": 0.0
            })

        # D. EVALUATION_POINT_SOURCE_INJECTION (Evaluation exposures, ePSF profiles across SNR grid)
        eval_items = partition_result.evaluation_items
        pt_idx = 0
        for idx, item in enumerate(eval_items):
            ctrl_id = f"EVAL_CTRL_{idx:04d}"
            cutout_id = item.get("id", f"EVAL_CUTOUT_{idx:04d}")
            target_snr = snr_grid[pt_idx % len(snr_grid)]
            bg_sigma = max(1e-3, float(item.get("bg_std_eff", item.get("bg_std", 1e-2))))
            flux_mjy_sr_pix = target_snr * bg_sigma * 5.0
            trials_manifest.append({
                "trial_id": f"EVAL_INJ_POINT_{pt_idx:04d}",
                "parent_cutout_id": cutout_id,
                "matched_control_id": ctrl_id,
                "partition": "EVALUATION_POINT_SOURCE_INJECTION",
                "source_type": "POINT_SOURCE",
                "obs_id": item["obs_id"],
                "filename": item["filename"],
                "detector_id": item["detector_id"],
                "det_cx": item["cx_det"],
                "det_cy": item["cy_det"],
                "target_snr": target_snr,
                "target_flux_mjy_sr_pix": flux_mjy_sr_pix,
                "fwhm_arcsec": 0.0
            })
            pt_idx += 1

        # E. EVALUATION_EXTENDED_SOURCE_INJECTION (Evaluation exposures, 2D Gaussian profiles across FWHM grid)
        ext_idx = 0
        for idx, item in enumerate(eval_items):
            ctrl_id = f"EVAL_CTRL_{idx:04d}"
            cutout_id = item.get("id", f"EVAL_CUTOUT_{idx:04d}")
            target_fwhm = fwhm_grid_arcsec[ext_idx % len(fwhm_grid_arcsec)]
            target_snr = snr_grid[ext_idx % len(snr_grid)]
            bg_sigma = max(1e-3, float(item.get("bg_std_eff", item.get("bg_std", 1e-2))))
            flux_mjy_sr_pix = target_snr * bg_sigma * 10.0
            trials_manifest.append({
                "trial_id": f"EVAL_INJ_EXT_{ext_idx:04d}",
                "parent_cutout_id": cutout_id,
                "matched_control_id": ctrl_id,
                "partition": "EVALUATION_EXTENDED_SOURCE_INJECTION",
                "source_type": "EXTENDED_SOURCE",
                "obs_id": item["obs_id"],
                "filename": item["filename"],
                "detector_id": item["detector_id"],
                "det_cx": item["cx_det"],
                "det_cy": item["cy_det"],
                "target_snr": target_snr,
                "target_flux_mjy_sr_pix": flux_mjy_sr_pix,
                "fwhm_arcsec": target_fwhm
            })
            ext_idx += 1

        campaign_package = {
            "governance": {
                "campaign_status": "PREPARED_LOCKED",
                "execution_permitted": False,
                "task_governance": "Phase 3, Task 1.1H",
                "asset_verification": asset_info
            },
            "partition_summary": {
                "total_harvested_cutouts": total_harvested,
                "num_independent_exposure_groups": partition_result.num_independent_groups,
                "calibration_obs_ids": partition_result.calibration_obs_ids,
                "evaluation_obs_ids": partition_result.evaluation_obs_ids,
                "calibration_cutouts": len(partition_result.calibration_items),
                "evaluation_cutouts": len(partition_result.evaluation_items),
                "rejected_spatial_overlaps": len(partition_result.rejected_items),
                "detector_distribution": partition_result.detector_distribution,
                "is_strictly_disjoint": partition_result.is_strictly_disjoint
            },
            "experimental_design": {
                "snr_grid": snr_grid,
                "fwhm_grid_arcsec": fwhm_grid_arcsec,
                "total_trials": len(trials_manifest),
                "trials_by_partition": {
                    "CALIBRATION_CONTROL": len(partition_result.calibration_items),
                    "CALIBRATION_INJECTION": cal_inj_count,
                    "EVALUATION_CONTROL": len(partition_result.evaluation_items),
                    "EVALUATION_POINT_SOURCE_INJECTION": pt_idx,
                    "EVALUATION_EXTENDED_SOURCE_INJECTION": ext_idx
                }
            },
            "trials_manifest": trials_manifest
        }

        return campaign_package

    def execute_campaign(self) -> None:
        """
        Execution Gate: Strictly blocks execution under Task 1.1H governance.
        """
        if CAMPAIGN_EXECUTION_LOCKED:
            raise RuntimeError(
                "CRITICAL GOVERNANCE BLOCKER: Benchmark Campaign Execution is STRICTLY PROHIBITED "
                "under Phase 3 Task 1.1H governance. Only remediation, regression testing, "
                "and dry-run manifest compilation are authorized. No model inference may be executed."
            )


def main():
    parser = argparse.ArgumentParser(description="ASTROVISION Controlled Benchmark Campaign Driver")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run dry-run manifest preparation without model inference")
    parser.add_argument("--execute", action="store_true", help="Attempt execution (BLOCKED by governance)")
    parser.add_argument("--cutouts-per-detector", type=int, default=50, help="Target cutouts per detector array")
    parser.add_argument("--output-manifest", type=str, default="reports/manifests/astrovision_controlled_campaign_manifest_dryrun.json")
    args = parser.parse_args()

    driver = AstroVisionControlledCampaignDriver()

    if args.execute:
        logger.error("Campaign execution requested, checking governance lock...")
        driver.execute_campaign()
        return

    logger.info("Executing Controlled Benchmark Campaign Preparation (DRY-RUN)...")
    package = driver.prepare_campaign_manifest(cutouts_per_detector=args.cutouts_per_detector)

    os.makedirs(os.path.dirname(args.output_manifest), exist_ok=True)
    with open(args.output_manifest, "w") as f:
        json.dump(package, f, indent=2)

    logger.info(f"Campaign package compiled successfully to {args.output_manifest}")
    logger.info(f"Total Trials Prepared: {package['experimental_design']['total_trials']}")
    logger.info("DRY-RUN COMPLETE. Zero model inferences executed.")


if __name__ == "__main__":
    main()
